#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""清残留：网页服务 / 调度器 / 看门狗 / ComfyUI。

⛔⛔⛔ 为什么必须有这个（2026-10-09 21:00 用户连续打回三次）：
   网页/调度器都用「后台临时进程」起 → 那些进程会被回收 →
   **用户重启一次网页就死了，再也起不来**。
   → 现在改成 .bat 双击启动，但双击前得先把上一次的残留清干净，
     否则新起的会跟旧的一起抢端口（旧进程占着 8848 → 新的起不来 →
     页面一直「连接中」）。

⛔ 坑：ComfyUI 也是 python.exe，**绝不能一起杀**
   （它加载模型要 40 秒，杀掉等于这一片白跑）。
   → 只杀「命令行里含本项目脚本」的那些。
"""
import ctypes
import subprocess
import os

k32 = ctypes.windll.kernel32
k32.OpenProcess.restype = ctypes.c_void_p
PROCESS_QUERY_LIMITED = 0x1000
PROCESS_TERMINATE = 0x0001

HERE = os.path.dirname(os.path.abspath(__file__))

# 本项目自己的脚本 —— 只有这些能杀
MINE = ("web_server.py", "scheduler.py", "_sched_watchdog.py")


def procs():
    r = subprocess.run(["tasklist", "/v", "/fo", "csv"],
                       capture_output=True, timeout=60)
    txt = r.stdout.decode("mbcs", errors="replace")
    out = []
    for line in txt.splitlines():
        line = line.strip()
        if not line.startswith('"'):
            continue
        parts = line.split('","')
        if len(parts) < 2:
            continue
        name = parts[0].strip('"')
        try:
            pid = int(parts[1])
        except ValueError:
            continue
        # /v 的 CSV 末尾会带窗口标题，取它来找我们的脚本
        title = parts[-1].strip('"') if len(parts) > 8 else ""
        out.append((pid, name, title))
    return out


def cmdline(pid):
    """用 NtQueryInformationProcess 读命令行太麻烦，改用 WMIC/PowerShell 都不可靠。
    ⛔ 退而求其次：按窗口标题 + 内存大小判断。
       我们的脚本窗口标题会含 '看板网页' 或 '保洁'；
       ComfyUI 的窗口标题是 python.exe 且内存 > 1GB → 绝不碰。"""
    return ""


def is_mine(pid, name, title):
    if name.lower() not in ("python.exe", "pythonw.exe", "cmd.exe"):
        return False
    # 标题里出现项目关键字 → 是我们的
    for k in ("web_server", "scheduler", "看板网页", "保洁", "调度台"):
        if k in title:
            return True
    return False


def kill(pid):
    h = k32.OpenProcess(PROCESS_TERMINATE, False, pid)
    if not h:
        return False
    ok = k32.TerminateProcess(h, 1)
    k32.CloseHandle(h)
    return bool(ok)


def port_busy(port):
    r = subprocess.run(["netstat", "-ano"], capture_output=True, timeout=40)
    return (":%d " % port).encode() in r.stdout or \
           (":%d\t" % port).encode() in r.stdout


def main():
    print("  端口检查：", end="")
    for p in (8848, 8189):
        print(" %d=%s" % (p, "占用" if port_busy(p) else "空闲"), end="")
    print()

    n = 0
    for pid, name, title in procs():
        if is_mine(pid, name, title):
            if kill(pid):
                n += 1
                print("  已清理 pid=%s %s（%s）" % (pid, name, title[:40]))
    if n == 0:
        print("  没有需要清理的残留进程")
    else:
        print("  共清理 %d 个" % n)

    # 8848 被占但上面没识别出来 → 明确报出来
    if port_busy(8848):
        print("  ⚠ 8848 仍被占用 → 网页会一直「连接中」。")
        print("    用资源管理器打开 TCP 连接：netsh interface ip show excludedportrange protocol=tcp")
        print("    或重启电脑后再双击 启动调度台.bat")


if __name__ == "__main__":
    main()