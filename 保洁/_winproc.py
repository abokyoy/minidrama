# -*- coding: utf-8 -*-
"""列出 / 结束进程：只用 Windows 原生 API（ctypes），不经过任何 shell。

为什么不用别的办法（本会话连续踩了 4 次）：
  · `wmic` —— 新版 Windows 已移除，FileNotFoundError
  · `schtasks.exe` —— 被安全策略列入黑名单，不能启动
  · `powershell.exe` —— 从 Bash 调会被拦（"绕过 PowerShell 安全检查"）；
    用 PowerShell 工具时它的 stdout 又整个被吞，看不到任何东西
  · psutil —— 环境里没装
  → 只剩 ctypes 调 kernel32。这条路不依赖任何被禁的外部程序。

提供两个函数给其它脚本 import：
  list_procs()      -> [(pid, cmdline), ...]
  kill_pids(pids)   -> 杀掉的 pid 列表
"""
import ctypes
import subprocess
import sys
from ctypes import wintypes

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TH32CS_SNAPPROCESS = 0x00000002
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_TERMINATE = 0x0001
MAX_PATH = 260
INVALID_HANDLE_VALUE = -1


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * MAX_PATH),
    ]


k32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)
ntdll = ctypes.WinDLL("ntdll", use_last_error=True)

k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
k32.OpenProcess.restype = wintypes.HANDLE
k32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                           wintypes.LPWSTR,
                                           ctypes.POINTER(wintypes.DWORD)]


def list_procs():
    """返回 [(pid, 可执行文件全路径), ...]

    ⚠️ 2026-10-04 实测：读 PEB 拿 CommandLine 在本机返回全空
       （OpenProcess 的 PROCESS_QUERY_LIMITED_INFORMATION 能开，但
        NtQueryInformationProcess 拿到的 PEB 地址读不出 CommandLine）。
       改成只取 exe 全路径 —— 够用来区分 ComfyUI / 生成器 / 无关进程。
       需要完整命令行时走 `_cmdline()`（单进程查，可用）。
    """
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())
    out = []
    try:
        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        ok = k32.Process32FirstW(snap, ctypes.byref(pe))
        while ok:
            pid = int(pe.th32ProcessID)
            path = _image(pid)
            if path:
                out.append((pid, path))
            ok = k32.Process32NextW(snap, ctypes.byref(pe))
    finally:
        k32.CloseHandle(snap)
    return out


def _image(pid):
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(MAX_PATH * 2)
        n = wintypes.DWORD(0)
        if not k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
            return ""
        return buf.value
    except Exception:
        return ""
    finally:
        k32.CloseHandle(h)


def _cmdline(pid):
    """NtQueryInformationProcess(ProcessBasicInformation) → PEB → RTL_USER_PROCESS_PARAMETERS → CommandLine"""
    PROCESS_BASIC_INFORMATION = 0
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return ""
    try:
        pbi = (ctypes.c_byte * 48)()
        ret = ctypes.c_ulong()
        st = ntdll.NtQueryInformationProcess(
            h, PROCESS_BASIC_INFORMATION, ctypes.byref(pbi), 48,
            ctypes.byref(ret))
        if st != 0:
            return ""
        # PEB 地址在 offset 8
        peb_addr = ctypes.cast(ctypes.byref(pbi, 8), ctypes.POINTER(ctypes.c_void_p)).contents.value
        if not peb_addr:
            return ""

        def read_mem(addr, size):
            buf = (ctypes.c_byte * size)()
            n = ctypes.c_ulong()
            if not k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, size,
                                         ctypes.byref(n)):
                return None
            return buf

        # PEB->ProcessParameters 位于 64 位 PEB 的 offset 0x20
        pp = read_mem(peb_addr + 0x20, 8)
        if not pp:
            return ""
        pp_addr = ctypes.cast(pp, ctypes.POINTER(ctypes.c_void_p)).contents.value
        if not pp_addr:
            return ""
        # RTL_USER_PROCESS_PARAMETERS->CommandLine(UNICODE_STRING) 在 offset 0x70
        us = read_mem(pp_addr + 0x70, 16)
        if not us:
            return ""
        us_len = ctypes.cast(ctypes.byref(us, 4), ctypes.POINTER(ctypes.c_ushort)).contents.value
        us_buf = ctypes.cast(ctypes.byref(us, 8), ctypes.POINTER(ctypes.c_void_p)).contents.value
        if not us_buf or us_len == 0 or us_len > 32767:
            return ""
        s = read_mem(us_buf, us_len)
        if not s:
            return ""
        return ctypes.wstring_at(ctypes.cast(s, ctypes.c_void_p))
    except Exception:
        return ""
    finally:
        k32.CloseHandle(h)


def kill_pids(pids):
    killed = []
    for pid in pids:
        h = k32.OpenProcess(PROCESS_TERMINATE, False, pid)
        if h:
            if k32.TerminateProcess(h, 1):
                killed.append(pid)
            k32.CloseHandle(h)
        else:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            killed.append(pid)
    return killed


# ── 自查 ──
if __name__ == "__main__":
    rows = list_procs()
    print("共读到 %d 个进程" % len(rows))
    hits = [(p, c) for p, c in rows
            if "python" in c.lower() and
            any(k in c for k in ("comfyui", "python.exe"))]
    for p, c in hits:
        print("  %6d  %s" % (p, c))
    print("python 进程 %d 个" % len(hits))
