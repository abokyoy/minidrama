# -*- coding: utf-8 -*-
"""用计划任务跑音频批量修复（后台常驻，不受沙箱回收影响）。

为什么不用 nohup：实测 `nohup python ... &` 在本会话里会被父 shell 退出时
连带回收（日志停在第 2 段，进程消失）。跟 ComfyUI 一样，走计划任务才稳。

用法：
  python _audio_task.py start [ep001]   # 开始（默认 ep001）
  python _audio_task.py status
  python _audio_task.py stop
"""
import os
import subprocess
import sys

TASK = "minidrama_fixaudio"
PY = r"C:\Users\86134\.workbuddy\binaries\python\versions\3.13.12\python.exe"
SCRIPT = r"E:\LLM\try\minidrama\保洁\_fix_audio.py"
LOG = r"E:\LLM\try\minidrama\保洁\logs\fixaudio_task.log"


def ps(cmd, timeout=120):
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                       capture_output=True, timeout=timeout)
    return (r.stdout or b"").decode("utf-8", "replace").strip(), \
           (r.stderr or b"").decode("utf-8", "replace").strip()


def args_for(ep):
    # 包 cmd /c 才能重定向（New-ScheduledTaskAction 不经过 shell）
    return ('/c ""%s" -u "%s" --batch %s > "%s" 2>&1"'
            % (PY, SCRIPT, ep, LOG))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    ep = "ep001"
    for a in sys.argv[2:]:
        if a.startswith("ep"):
            ep = a

    if mode == "start":
        out, err = ps(
            "$a = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '%s'; "
            "$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries "
            "-DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) "
            "-RestartCount 0 -MultipleInstances IgnoreNew; "
            "Register-ScheduledTask -TaskName %s -Action $a -Settings $s -Force | Out-Null; "
            "Start-ScheduledTask -TaskName %s; Write-Output 'started %s'"
            % (args_for(ep), TASK, TASK, ep))
        print(out or err[:400])
    elif mode == "status":
        out, _ = ps("$t = Get-ScheduledTask -TaskName %s -ErrorAction SilentlyContinue; "
                    "if ($t) { $t | ForEach-Object { Write-Output $_.State } } "
                    "else { Write-Output 'none' }" % TASK)
        print("TASK:", out)
        if os.path.exists(LOG):
            n = 0
            try:
                with open(LOG, encoding="utf-8", errors="replace") as f:
                    n = sum(1 for l in f if "完成：" in l)
            except Exception:
                pass
            print("已修复 %d 段（日志 %s）" % (n, os.path.basename(LOG)))
    elif mode in ("stop", "remove"):
        out, _ = ps("Stop-ScheduledTask -TaskName %s -ErrorAction SilentlyContinue; %s"
                    "Write-Output '%s'"
                    % (TASK,
                       "Unregister-ScheduledTask -TaskName %s -Confirm:$false "
                       "-ErrorAction SilentlyContinue; " % TASK if mode == "remove" else "",
                       mode))
        print(out)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
