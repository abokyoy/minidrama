# -*- coding: utf-8 -*-
"""杀掉旧剧本（ep001–ep005）的僵尸生成进程，只留当前集。

为什么需要：计划任务 stop 只会停"实例"，正在跑的 h3_driver.py 子进程不一定带走；
两个生成器同时往 ComfyUI 队列里塞任务会抢显存 → OOM。

用法：python _kill_old.py            # 杀掉除 keep 之外的所有生成进程
      python _kill_old.py xs001      # 只保留含 xs001 的
"""
import os
import subprocess
import sys

KEEP = sys.argv[1] if len(sys.argv) > 1 else "xs001"

PS = (
    "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
    "Where-Object { ($_.CommandLine -like '*_run_gen.py*') -or "
    "($_.CommandLine -like '*gen_worker.py*') -or "
    "($_.CommandLine -like '*h3_driver.py*') } | "
    "ForEach-Object { Write-Output ($_.ProcessId.ToString() + '|' + $_.CommandLine) }"
)


def main():
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", PS],
                       capture_output=True, timeout=120)
    out = (r.stdout or b"").decode("utf-8", "replace")
    victims = []
    for line in out.splitlines():
        if "|" not in line:
            continue
        pid, cmd = line.split("|", 1)
        if KEEP in cmd:
            print("KEEP %s  %s" % (pid, cmd[:110]))
            continue
        victims.append((pid.strip(), cmd.strip()))

    for pid, cmd in victims:
        subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=60)
        print("KILL %s  %s" % (pid, cmd[:110]))

    print("杀掉 %d 个，保留目标=%s" % (len(victims), KEEP))


if __name__ == "__main__":
    main()
