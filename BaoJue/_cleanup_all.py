# -*- coding: utf-8 -*-
"""彻底清理：所有生成器进程 + ComfyUI 进程。

为什么需要这个（2026-10-04 19:15 踩到）：
`register` 会重注册计划任务，但**已经跑起来的 `_run_gen.py` 不会被带走**。
多次 register 之后会出现：
  · 两个 `_run_gen.py` 主进程同时往队列塞任务
  · 两个 `h3_driver.py` 孤儿（父进程已死，还在等一个已清空的队列）
  · 两个 ComfyUI 同时启动（`gen_worker` 自己的重启 + 手动 restart 撞车）
结果 = 抢显存 → ComfyUI 超时 → 整条链卡死。

`_kill_old.py` 只能按「集名」保留，不能全清；这里提供「全清」。

用法：python _cleanup_all.py
"""
import os
import subprocess
import sys

PS = (
    "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
    "Where-Object { ($_.CommandLine -like '*_run_gen.py*') -or "
    "($_.CommandLine -like '*h3_driver.py*') -or "
    "($_.CommandLine -like '*gen_worker.py*') -or "
    "($_.CommandLine -like '*_watch_xs001.py*') -or "
    "($_.CommandLine -like '*_queue_watch.py*') -or "
    "($_.CommandLine -like '*_watch_gen.py*') -or "
    "($_.CommandLine -like '*ComfyUI*main.py*') } | "
    "ForEach-Object { Write-Output ($_.ProcessId.ToString() + '|' + $_.CommandLine) }"
)


def main():
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", PS],
                       capture_output=True, timeout=120)
    out = (r.stdout or b"").decode("utf-8", "replace")
    rows = []
    for line in out.splitlines():
        if "|" not in line:
            continue
        pid, cmd = line.split("|", 1)
        pid = pid.strip()
        if pid.isdigit():
            rows.append((pid, cmd.strip()))

    if not rows:
        print("没有残留进程")
        return 0
    for pid, cmd in rows:
        subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=60)
        tag = "ComfyUI" if "main.py" in cmd else "生成器"
        print("KILL %-8s [%s] %s" % (pid, tag, cmd[:90]))
    print("\n共清理 %d 个进程" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
