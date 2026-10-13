# -*- coding: utf-8 -*-
"""
注册 / 注销"并发流水线"计划任务。

为什么用计划任务：Start-Process 启的子进程会在会话结束时被沙箱回收，
计划任务才能真正脱离会话常驻（见 AGENTS.md）。

用法：
  python _task.py register              # 注册 minidrama_gen001 并立即启动（旧剧本 ep001–ep005）
  python _task.py register xs001        # 注册并只跑新剧本 X003 的 xs001
  python _task.py status
  python _task.py stop        # 停止任务（不注销）
  python _task.py remove      # 停止并注销
"""
import subprocess
import sys

TASK = "minidrama_gen001"
PY = r"C:\Users\86134\.workbuddy\binaries\python\versions\3.13.12\python.exe"
LAUNCHER = r"E:\LLM\try\minidrama\_run_gen.py"
# 全集队列：ep001 跑完自动接 ep002……（没有 manifest 的集会跳过，等分镜做好后自动接上）
EP_ARGS = "ep001 ep002 ep003 ep004 ep005 --watch"
# 输出目录。2026-10-04 用户要求「新生成的放 D:\output\new，从第一幕重新生成」。
#
# ⚠️ 必须**写进计划任务定义**，不能只靠环境变量：
#    计划任务不继承启动它那条命令的环境变量（实测：命令行带
#    MINIDRAMA_OUT 启动生成器，任务里读到的仍是 D:\output）。
#    在 -Argument 里用 cmd /c "set VAR=... && python ..." 显式注入。
import os
DEFAULT_OUT = r"D:\output"
OUT_DIR = os.environ.get("MINIDRAMA_OUT", DEFAULT_OUT)
ARGS = ('/c "set MINIDRAMA_OUT=%s&& "%s" "%s" %s"'
        % (OUT_DIR, PY, LAUNCHER, EP_ARGS))


def set_eps(eps):
    """运行时切集：python _task.py register xs001  →  只跑 X003 的 xs001。
    必须先 set 再 register：ARGS 是模块级常量，register 时才被拼进 -Argument。"""
    global EP_ARGS, ARGS, TASK
    if eps:
        EP_ARGS = " ".join(eps) + " --watch"
        ARGS = ('/c "set MINIDRAMA_OUT=%s&& "%s" "%s" %s"'
                % (OUT_DIR, PY, LAUNCHER, EP_ARGS))
        print("集队列 =", EP_ARGS)


def ps(cmd, timeout=180):
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                       capture_output=True, timeout=timeout)
    out = (r.stdout or b"").decode("utf-8", "replace")
    err = (r.stderr or b"").decode("utf-8", "replace")
    return out.strip(), err.strip()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    eps = [a for a in sys.argv[2:] if not a.startswith("-")]

    if mode == "register":
        set_eps(eps)
        # 走 cmd /c 显式注入 MINIDRAMA_OUT（计划任务不继承外部环境变量）
        action = ("New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '%s'"
                  % ARGS.replace("'", "''"))
        settings = ("New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries "
                    "-ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 0 -MultipleInstances IgnoreNew")
        cmd = ("$a = %s; $s = %s; "
               "Register-ScheduledTask -TaskName %s -Action $a -Settings $s -Force | Out-Null; "
               "Start-ScheduledTask -TaskName %s; Write-Output ('registered+started out=%s')"
               % (action, settings, TASK, TASK, OUT_DIR))
        out, err = ps(cmd)
        print(out or "(no out)")
        if err:
            print("ERR:", err[:600])

    elif mode == "status":
        out, err = ps("$t = Get-ScheduledTask -TaskName %s -ErrorAction SilentlyContinue; "
                      "if ($t) { $t | ForEach-Object { Write-Output ($_.TaskName + ' | ' + $_.State) } } "
                      "else { Write-Output 'none' }" % TASK)
        print("TASK:", out or "(none)")
        out, err = ps("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                      "ForEach-Object { Write-Output ($_.ProcessId.ToString() + ' | ' + $_.CommandLine) }")
        for line in out.splitlines():
            if "_run_gen" in line or "gen_worker" in line or "h3_driver" in line:
                print("PROC:", line[:200])
        if err:
            print("ERR:", err[:400])

    elif mode == "stop":
        out, err = ps("Stop-ScheduledTask -TaskName %s -ErrorAction SilentlyContinue; Write-Output 'stopped'" % TASK)
        print(out or "(no out)")

    elif mode == "remove":
        out, err = ps("Stop-ScheduledTask -TaskName %s -ErrorAction SilentlyContinue; "
                      "Unregister-ScheduledTask -TaskName %s -Confirm:$false -ErrorAction SilentlyContinue; "
                      "Write-Output 'removed'" % (TASK, TASK))
        print(out or "(no out)")

    elif mode == "restart":
        # 先停任务，再杀掉真正在跑的 python（计划任务只停"实例"，不一定带走子进程）
        ps("Stop-ScheduledTask -TaskName %s -ErrorAction SilentlyContinue" % TASK)
        out, err = ps("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                      "Where-Object { $_.CommandLine -like '*_run_gen.py*' -or "
                      "$_.CommandLine -like '*gen_worker.py*' -or "
                      "$_.CommandLine -like '*h3_driver.py*' } | "
                      "ForEach-Object { Write-Output ('KILL ' + $_.ProcessId); "
                      "Stop-Process -Id $_.ProcessId -Force }")
        print(out.strip() or "(nothing killed)")
        if err.strip():
            print("ERR:", err[:400])
        out, err = ps("Start-ScheduledTask -TaskName %s; Write-Output 'started'" % TASK)
        print(out.strip() or "(no out)")


if __name__ == "__main__":
    main()
