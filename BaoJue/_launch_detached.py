#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""完全脱离当前会话的启动器。

⛔⛔⛔ 2026-10-09 20:00 血泪教训：
   调度器用 Bash(run_in_background=true) 起的，17:18 ComfyUI 崩溃后
   调度器进程**跟着消失了**，GPU 空转近 3 小时没人管。
   根因：run_in_background 的进程是当前会话的子进程，会话一收/一重连就被回收。

   → 必须用 DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP 起，
     让它彻底脱离进程树。会话结束、WorkBuddy 重启都不影响它。
   → 再配 _sched_watchdog.py 兜底：调度器死了自动拉起。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

# ⛔⛔ 2026-10-09 20:02 实测：DETACHED_PROCESS(0x8) 在这台机器上**进程一起来就被杀**
#    （pid 报得出来，1 秒后 tasklist 里就没了，日志 0 字节）。
#    → 改用 CREATE_NEW_PROCESS_GROUP(0x200) | CREATE_NO_WINDOW(0x08000000)，
#      同样能脱离会话，但不会因为脱离控制台被杀。
DETACHED = 0x00000200 | 0x08000000   # CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW

# ⛔ 一定要清掉代理环境变量，否则 ComfyUI 内部访问 127.0.0.1 会走死代理 502
env = dict(os.environ)
for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
          "ALL_PROXY", "all_proxy"):
    env.pop(k, None)

def spawn(args, logname, cwd=HERE):
    logp = os.path.join(HERE, logname)
    lf = open(logp, "a", encoding="utf-8", buffering=1)
    p = subprocess.Popen(
        args, cwd=cwd, env=env, stdout=lf, stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        creationflags=DETACHED,
    )
    lf.close()
    return p.pid

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "run":
        pid = spawn([PY, "-u", "scheduler.py", "run"], "_sched_run.log")
        print("调度器已脱离启动 pid=%s 日志=_sched_run.log" % pid)
    elif mode == "watchdog":
        pid = spawn([PY, "-u", "_sched_watchdog.py"], "_watchdog.log")
        print("看门狗已脱离启动 pid=%s 日志=_watchdog.log" % pid)
    elif mode == "web":
        pid = spawn([PY, "-u", "web_server.py"], "_web.log")
        print("看板已脱离启动 pid=%s 端口=8848" % pid)
    elif mode == "all":
        for m, lg in (("watchdog", "_watchdog.log"),
                      ("web", "_web.log"),
                      ("run", "_sched_run.log")):
            print(spawn([PY, "-u", {"watchdog": "_sched_watchdog.py",
                                    "web": "web_server.py",
                                    "run": "scheduler.py"}[m], *(
                                       [] if m != "run" else ["run"])],
                        lg))