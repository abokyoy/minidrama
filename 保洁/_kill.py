# -*- coding: utf-8 -*-
"""⛔ 唯一可靠的杀进程方式：ctypes 直接调 kernel32。
   taskkill /F 在这个环境里静默返回空（杀了但拿不到输出），
   PowerShell 也静默返回空（记忆里已记）。
   → OpenProcess(PROCESS_TERMINATE) + TerminateProcess。
"""
import ctypes
import subprocess
import sys
from ctypes import wintypes

k32 = ctypes.windll.kernel32
PROCESS_TERMINATE = 0x0001
PROCESS_QUERY_LIMITED = 0x1000


def all_pids():
    r = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True)
    txt = r.stdout.decode("mbcs", errors="replace")
    out = []
    for l in txt.splitlines():
        l = l.strip()
        if not l.startswith('"'):
            continue
        try:
            name = l.split('","')[0].strip('"')
            pid = int(l.split('","')[1])
        except Exception:
            continue
        out.append((pid, name))
    return out


def kill_pid(pid):
    h = k32.OpenProcess(PROCESS_TERMINATE, False, pid)
    if not h:
        return False, "OpenProcess failed"
    ok = k32.TerminateProcess(h, 1)
    k32.CloseHandle(h)
    return bool(ok), ("killed" if ok else "TerminateProcess failed")


def kill_matching(pred, label=""):
    n = 0
    for pid, name in all_pids():
        try:
            if pred(pid, name):
                ok, why = kill_pid(pid)
                if ok:
                    n += 1
                    print("  杀 %s pid=%s" % (name, pid))
        except Exception as e:
            print("  杀 pid=%s 异常 %r" % (pid, e))
    print("共杀 %d 个 %s" % (n, label))
    return n


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "sched"
    if what == "sched":
        # 调度器 / 看门狗 / 启动器 / 看板 —— 都跑在 _run_one.py 之外的脚本上，
        # ⛔ 不能杀 ComfyUI（它也是 python.exe，名字一样）→ 只杀我们自己的。
        MINE = ("_sched_watchdog.py", "web_server.py", "_launch_detached.py",
                "_kill_old.py", "_dup_check.py", "_snap.py", "_fix_")
        # 先按命令行找：tasklist 拿不到命令行，改用 pid 记录
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        pidfile = os.path.join(here, "_sched.pid")
        if os.path.exists(pidfile):
            try:
                pid = int(open(pidfile).read().strip())
                ok, why = kill_pid(pid)
                print("按 pid 文件杀 %s: %s" % (pid, why))
                os.remove(pidfile)
            except Exception as e:
                print("pid 文件处理失败", e)
        # 剩下的按内存大小筛：调度器 40MB+，ComfyUI 起步 2GB+
        killed = 0
        for pid, name in all_pids():
            if name.lower() != "python.exe":
                continue
            import ctypes.wintypes as wt
            PH = ctypes.create_string_buffer(1024)
            cnt = wt.DWORD()
            h = k32.OpenProcess(PROCESS_QUERY_LIMITED, False, pid)
            if not h:
                continue
            try:
                psapi = ctypes.windll.psapi
                cbs = ctypes.c_size_t(1024)
                psapi.GetModuleFileNameExW(h, None, PH, cbs)
            except Exception:
                pass
            k32.CloseHandle(h)
            path = PH.value.decode("utf-16-le", errors="ignore") if PH.value else ""
            # ComfyUI 的命令行含 main.py → 绝不碰
            print("  pid=%s path=%s" % (pid, path))