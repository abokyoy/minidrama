# -*- coding: utf-8 -*-
"""列出 / 结束本流水线相关进程。避免 Bash 直接调 powershell。"""
import subprocess, sys, json

PS_LIST = (
    "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
    "ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }"
)
PS_TASK = "Get-ScheduledTask -TaskName 'minidrama*' -ErrorAction SilentlyContinue | ForEach-Object { \"$($_.TaskName)`t$($_.State)\" }"


def ps(cmd, timeout=60):
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                       capture_output=True, timeout=timeout)
    out = r.stdout.decode("utf-8", "replace") if isinstance(r.stdout, bytes) else (r.stdout or "")
    err = r.stderr.decode("utf-8", "replace") if isinstance(r.stderr, bytes) else (r.stderr or "")
    return out, err


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "list"
    if mode == "list":
        out, err = ps(PS_TASK)
        print("== TASKS ==")
        print(out.strip() or "(none)")
        out, err = ps(PS_LIST)
        print("== PYTHON PROCS ==")
        for line in out.splitlines():
            line = line.strip()
            if line:
                print(line[:230])
        if err.strip():
            print("ERR:", err.strip()[:300])
    elif mode == "stop":
        # 只杀 autopilot/_run.py 与 ComfyUI main.py
        killer = (
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
            "Where-Object { $_.CommandLine -like '*autopilot.py*' -or $_.CommandLine -like '*_run.py*' } | "
            "ForEach-Object { Write-Output \"KILL $($_.ProcessId)\"; Stop-Process -Id $_.ProcessId -Force }"
        )
        out, err = ps(killer)
        print(out.strip() or "(nothing killed)")
        if err.strip():
            print("ERR:", err.strip()[:300])
    elif mode == "stopall":
        killer = (
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
            "Where-Object { $_.CommandLine -like '*h3_driver.py*' -or $_.CommandLine -like '*autopilot.py*'"
            " -or $_.CommandLine -like '*_run.py*' } | "
            "ForEach-Object { Write-Output \"KILL $($_.ProcessId)\"; Stop-Process -Id $_.ProcessId -Force }"
        )
        out, err = ps(killer)
        print("== killed procs ==")
        print(out.strip() or "(nothing)")
        task = ("Stop-ScheduledTask -TaskName minidrama_ep001 -ErrorAction SilentlyContinue; "
                "Unregister-ScheduledTask -TaskName minidrama_ep001 -Confirm:$false -ErrorAction SilentlyContinue; "
                "Write-Output 'task removed'")
        out, err = ps(task)
        print("== task ==")
        print(out.strip() or "(nothing)")
        if err.strip():
            print("ERR:", err.strip()[:400])
    elif mode == "killcomfy":
        killer = (
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
            "Where-Object { $_.CommandLine -like '*main.py*' -and $_.CommandLine -like '*ComfyUI*' } | "
            "ForEach-Object { Write-Output \"KILL $($_.ProcessId)\"; Stop-Process -Id $_.ProcessId -Force }"
        )
        out, err = ps(killer)
        print(out.strip() or "(nothing killed)")


if __name__ == "__main__":
    main()
