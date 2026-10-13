# -*- coding: utf-8 -*-
"""列出占内存最多的进程 + 生成前的清场报告。

不用 psutil（本机 pip 源不通），改用 Windows 自带的 typeperf 性能计数器。

用法：
  python _mem_report.py            只看当前占用
  python _mem_report.py --reclaim  关掉可关的应用腾内存（默认只报告，不动手）
"""
import ctypes
import ctypes.wintypes as wt
import subprocess
import sys

K32 = ctypes.windll.kernel32


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD),
        ("cntUsage", wt.DWORD),
        ("th32ProcessID", wt.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wt.DWORD),
        ("cntThreads", wt.DWORD),
        ("th32ParentProcessID", wt.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wt.DWORD),
        ("szExeFile", ctypes.c_char * 260),
    ]


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wt.DWORD),
        ("PageFaultCount", wt.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


TH32CS_SNAPPROCESS = 0x00000002
INVALID = ctypes.c_void_p(-1).value
PSAPI = ctypes.windll.psapi
KERNEL = ctypes.windll.kernel32


def snapshot():
    """返回 [(pid, 进程名, RSS MB)]，纯 ctypes，不依赖性能计数器/psutil。"""
    snap = KERNEL.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == INVALID:
        return []
    e = PROCESSENTRY32()
    e.dwSize = ctypes.sizeof(PROCESSENTRY32)
    out = []
    ok = KERNEL.Process32First(snap, ctypes.byref(e))
    while ok:
        name = e.szExeFile.decode("utf-8", "replace")
        pid = e.th32ProcessID
        if pid != 0:
            c = PROCESS_MEMORY_COUNTERS()
            c.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            if PSAPI.GetProcessMemoryInfo(
                    KERNEL.OpenProcess(0x0400 | 0x0010, False, pid),
                    ctypes.byref(c), c.cb):
                out.append((pid, name,
                            c.WorkingSetSize / 1024 / 1024))
        ok = KERNEL.Process32Next(snap, ctypes.byref(e))
    KERNEL.CloseHandle(snap)
    return out


def phys():
    class MS(ctypes.Structure):
        _fields_ = [
            ("dwLength", wt.DWORD), ("dwMemoryLoad", wt.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]
    m = MS()
    m.dwLength = ctypes.sizeof(MS)
    KERNEL.GlobalMemoryStatusEx(ctypes.byref(m))
    return m


def procs_with_rss():
    return [(n, mb) for _pid, n, mb in snapshot()]


# ── 可安全关闭的进程（用户 2026-10-07 授权）─────────────────────────
# 保留白名单：WorkBuddy / v2rayN / mstsc(远程桌面) / 网易UU远程
KEEP = {
    # 必须留 —— 远程控制通道，断了就联系不上
    "mstsc.exe", "gameviewerserver.exe", "gamviewer.exe", "uu.exe",
    "neteaseuu.exe", "uuclient.exe", "remotedesktop.exe",
    # 必须留 —— 代理，断了下载不了东西
    "v2rayn.exe", "v2rayn-service.exe", "xray.exe", "sing-box.exe",
    # 必须留 —— 我们自己
    "workbuddy.exe", "codebuddy.exe", "code.exe", "node.exe",
    "python.exe", "bash.exe", "git.exe",
    # 必须留 —— 系统骨架
    "system", "system idle process", "[system process]",
    "registry", "memory compression", "smss.exe", "csrss.exe",
    "wininit.exe", "winlogon.exe", "services.exe", "lsass.exe",
    "svchost.exe", "fontdrvhost.exe", "dwm.exe", "sihost.exe",
    "ctfmon.exe", "conhost.exe", "powershell.exe", "cmd.exe",
    # 必须留 —— 显卡/外设驱动服务
    "nvcontainer.exe", "nvdisplay.container.exe", "armourycrate.service.exe",
    "armourycrate.usersessionhelper.exe", "asussystemcontrol.exe",
    "asus_framework.exe", "rogthrustv2service.exe", "asusservice.exe",
    "logibolt.exe", "logioptionsmgr.exe", "logioptionsmanager.exe",
    "logioptionsservice.exe", "logioverlay.exe",
    "audioaccessoryservice.exe", "nahimicservice.exe",
    # 必须留 —— 输入法/安全软件
    "ime_service.exe", "imeservice.exe", "hipstrust.exe", "hipsdaemon.exe",
    "hipsmain.exe", "hipsclient.exe", "wetype_server.exe", "wetype_renderer.exe",
    "kemonmain.exe", "kemon.exe", "usblink.exe", "usbkey.exe",
    "windowsdefender.exe", "msmpeng.exe", "nissrv.exe",
}

# 高优先级清理对象：常驻吃内存的第三方
BIG_TARGETS = [
    ("msedge.exe", "Edge 浏览器"),
    ("msedgewebview2.exe", "Edge WebView"),
    ("chrome.exe", "Chrome"),
    ("wps.exe", "WPS 文字"),
    ("wpscloudsvr.exe", "WPS 云服务"),
    ("QQ.exe", "QQ"),
    ("wechat.exe", "微信"),
    ("WXWork.exe", "企业微信"),
    ("neteasemusic.exe", "网易云音乐"),
    ("Spotify.exe", "Spotify"),
    ("steam.exe", "Steam"),
    ("EpicGamesLauncher.exe", "Epic 启动器"),
    ("battle.net.exe", "战网"),
    ("NVIDIA app.exe", "NVIDIA App"),
    ("NVIDIA Share.exe", "NVIDIA 覆盖层"),
    ("ArmouryCrate.UserSessionHelper.exe", "华硕 Armoury Crate"),
    ("ROGLiveService.exe", "ROG 实时服务"),
    ("wetype_update.exe", "Wetype 更新器"),
]


def kill_targets():
    """按白名单杀进程，返回被杀的清单。"""
    killed = []
    try:
        out = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                             capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=60)
    except Exception as e:
        print("tasklist 失败: %s" % e)
        return killed
    for line in out.stdout.splitlines():
        parts = [p.strip().strip('"') for p in line.split('","')]
        if len(parts) < 2:
            continue
        name = parts[0]
        if name.lower() in KEEP:
            continue
        if not any(name.lower() == t.lower() for t, _ in BIG_TARGETS):
            continue
        subprocess.run(["taskkill", "/im", name, "/f"],
                       capture_output=True, timeout=60)
        killed.append(name)
    return killed


def main():
    if "--reclaim" in sys.argv:
        print("=== 关闭可关应用 ===")
        killed = kill_targets()
        if killed:
            for k in killed:
                print("  已关 %s" % k)
        else:
            print("  没有可关的目标进程（或已在运行状态干净）")
        import time
        print("等 5 秒让内存归还…")
        time.sleep(5)

    rows = procs_with_rss()
    m = phys()
    tot = m.ullTotalPhys / 1024 ** 3
    av = m.ullAvailPhys / 1024 ** 3
    print()
    print("物理内存总 %.1f GB / 空闲 %.1f GB / 已用 %.1f GB (%.0f%%)"
          % (tot, av, tot - av, (tot - av) / tot * 100))
    print("提交内存 可用 %.1f GB / 总 %.1f GB"
          % (m.ullAvailPageFile / 1024 ** 3, m.ullTotalPageFile / 1024 ** 3))
    if not rows:
        print("\n(typeperf 没取到)")
        return
    agg = {}
    for n, mb in rows:
        agg[n] = agg.get(n, 0) + mb
    print("进程数 %d，合计 %.1f GB" % (len(rows), sum(agg.values()) / 1024))
    print("-" * 52)
    for n, mb in sorted(agg.items(), key=lambda r: -r[1])[:25]:
        mark = " [可关]" if any(n.lower() == t.lower()
                                for t, _ in BIG_TARGETS) else ""
        print("  %-34s %8.0f MB%s" % (n, mb, mark))


if __name__ == "__main__":
    main()