# -*- coding: utf-8 -*-
"""⛔ 停掉所有残留生成进程 + 清空 ComfyUI 队列。

为什么需要：driver 被取消/杀掉后，ComfyUI **不会自己停** —— 它会继续把
已经提交的 prompt 跑完（约 16 分钟），产出用的是旧提示词 = 白跑，
而且显存被占住导致新任务起不来（铁律：两实例不能同时跑，会抢显存崩）。

用法：
    python _stop_all.py            # 杀ComfyUI + 清队列
    python _stop_all.py --port 8189
"""
from __future__ import print_function

import json
import os
import subprocess
import sys
import time
import urllib.request


def kill_tree(pid):
    """连带杀子进程（ComfyUI 会 fork 出采样进程）。"""
    r = subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                       capture_output=True)
    return (r.stdout or b"").decode("gbk", "replace")


def port_pid(port):
    r = subprocess.run(["netstat", "-ano"], capture_output=True, text=True,
                       encoding="gbk", errors="replace")
    for line in (r.stdout or "").splitlines():
        if (":%d " % port) in line and "LISTENING" in line:
            parts = line.split()
            if len(parts) >= 2:
                return parts[-1]
    return None


def get(port, path):
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        return op.open("http://127.0.0.1:%d%s" % (port, path), timeout=6).read()
    except Exception:
        return None


def main():
    port = 8189
    for i, a in enumerate(sys.argv):
        if a == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    # 1) 先清队列（如果还能连上）
    if get(port, "/queue"):
        try:
            op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            req = urllib.request.Request(
                "http://127.0.0.1:%d/queue" % port, method="DELETE",
                data=b"{}")
            op.open(req, timeout=6).read()
            print("队列已清空")
        except Exception as e:
            print("清队列失败（可能本来就没东西）: %s" % e)

    # 2) 杀监听该端口的进程
    pid = port_pid(port)
    if pid:
        print("杀端口 %d 的进程 pid=%s" % (port, pid))
        print("  " + kill_tree(pid).strip().splitlines()[-1])
        time.sleep(6)
    else:
        print("端口 %d 没人监听" % port)

    print("存活检查: %s" % ("还在" if get(port, "/system_stats") else "已停"))


if __name__ == "__main__":
    main()