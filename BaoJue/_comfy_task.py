# -*- coding: utf-8 -*-
"""
用 Windows 计划任务启动 / 管理 ComfyUI。

为什么必须用计划任务（2026-10-04 实测踩坑）：
  · `nohup ... &` 配 `run_in_background` → 父 shell 退出时子进程被回收，
    表现为「日志停在中途、显存一直是 0、8188 拒连」。
  · `cmd /c start "" /min python.exe ...` → 直接 SIGTERM，同样起不来。
  · 只有**计划任务**能真正脱离会话常驻（AGENTS.md 里也是这个结论）。

注意：主生成器那边的启动走的是 venv 里的 python，
这里必须用**同一个** venv python，否则自定义节点（H3SLAAttention 等）
会因解释器不一致而加载失败。

用法：
  python _comfy_task.py start     # 注册并启动
  python _comfy_task.py status    # 看状态
  python _comfy_task.py stop      # 停
  python _comfy_task.py restart   # 重启（改了节点参数后常用）
  python _comfy_task.py remove    # 注销
"""
import os
import json
import subprocess
import sys
import time

TASK = "minidrama_comfyui"
PY = r"E:\ComfyUI\ComfyUI-master\ComfyUI-master\venv\Scripts\python.exe"
MAIN = r"E:\ComfyUI\ComfyUI-master\ComfyUI-master\main.py"
# 计划任务的进程没有控制台，stdout/stderr 会丢失 → 崩了都看不到原因。
# 必须包一层 cmd /c 才能做重定向（直接写 > xxx 在 -Argument 里不生效，
# 因为 New-ScheduledTaskAction 自己 CreateProcess，不经过 shell 解析）。
LOG = r"E:\LLM\try\minidrama\保洁\logs\comfyui_task.log"
# 输出目录必须与 gen_worker / h3_driver / _grade 的 MINIDRAMA_OUT 一致，
# 否则 ComfyUI 写到 A、生成器去 B 找文件，表现为「跑完但找不到成片」。
#
# ⚠️ 关键坑：计划任务**不继承启动它那条命令的环境变量**。
#    实测 `MINIDRAMA_OUT="D:/output/new" python _comfy_task.py restart`
#    之后日志里仍然是 "Setting output directory to: D:\output"。
#    → 所以输出目录必须**在注册任务时写进 -Argument**，
#      用下面 args_for() 按当前环境变量现算，而不是模块级算一次。
DEFAULT_OUT = r"D:\output"


def args_for(outdir):
    return ('/c ""%s" "%s" --lowvram --enable-triton-backend '
            '--output-directory "%s" '
            '--temp-directory "D:\\ComfyUI_out\\ComfyUI-master\\temp" > "%s" 2>&1"'
            % (PY, MAIN, outdir, LOG))


EXEC = "cmd.exe"

# 队列守护（同样必须走计划任务，nohup 会被回收）
WATCH_TASK = "minidrama_queuewatch"
WATCH_PY = r"C:\Users\86134\.workbuddy\binaries\python\versions\3.13.12\python.exe"
WATCH_SCRIPT = r"E:\LLM\try\minidrama\保洁\_queue_watch.py"
WATCH_LOG = r"E:\LLM\try\minidrama\保洁\logs\queue_watch.log"
WATCH_ARGS = ('/c ""%s" -u "%s" --heal > "%s" 2>&1"'
              % (WATCH_PY, WATCH_SCRIPT, WATCH_LOG))

# 生成巡检（同样走计划任务常驻）
GENWATCH_TASK = "minidrama_genwatch"
GENWATCH_SCRIPT = r"E:\LLM\try\minidrama\保洁\_watch_gen.py"
GENWATCH_LOG = r"E:\LLM\try\minidrama\保洁\logs\watch_gen.log"


def ps(cmd, timeout=180):
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                       capture_output=True, timeout=timeout)
    return (r.stdout or b"").decode("utf-8", "replace").strip(), \
           (r.stderr or b"").decode("utf-8", "replace").strip()


def wait_ready(timeout=300):
    """等 ComfyUI 的 8188 真正就绪。加载 custom_nodes 通常要 1–2 分钟。"""
    import json
    import urllib.request
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
              "ALL_PROXY", "all_proxy"):
        os.environ.pop(k, None)
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            op.open("http://127.0.0.1:8188/system_stats", timeout=8).read()
            return int(time.time() - t0)
        except Exception:
            time.sleep(5)
    return -1


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"

    if mode == "start":
        outdir = os.environ.get("MINIDRAMA_OUT", DEFAULT_OUT)
        out, err = ps(
            "$a = New-ScheduledTaskAction -Execute '%s' -Argument '%s'; "
            "$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries "
            "-DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) "
            "-RestartCount 0 -MultipleInstances IgnoreNew; "
            "Register-ScheduledTask -TaskName %s -Action $a -Settings $s -Force | Out-Null; "
            "Start-ScheduledTask -TaskName %s; Write-Output 'started out=%s'"
            % (EXEC, args_for(outdir), TASK, TASK, outdir))
        print(out or err[:400])
        print("等待 ComfyUI 就绪…")
        sec = wait_ready()
        print(("✅ 就绪，用了 %d 秒" % sec) if sec > 0 else "❌ 超时未就绪")

    elif mode == "status":
        out, _ = ps("$t = Get-ScheduledTask -TaskName %s -ErrorAction SilentlyContinue; "
                    "if ($t) { $t | ForEach-Object { Write-Output $_.State } } "
                    "else { Write-Output 'none' }" % TASK)
        print("TASK:", out)
        # 只 import urllib.request：os / json 是模块级导入的。
        # 在这里 import os 会把 os 变成 main() 的**局部**变量，
        # 上面 os.environ.get("MINIDRAMA_OUT") 就会 UnboundLocalError（踩过）。
        import urllib.request
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
                  "ALL_PROXY", "all_proxy"):
            os.environ.pop(k, None)
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            q = json.loads(op.open("http://127.0.0.1:8188/queue", timeout=10).read())
            print("队列 运行=%d 排队=%d" % (len(q.get("queue_running", [])),
                                            len(q.get("queue_pending", []))))
        except Exception as e:
            print("服务未响应:", str(e)[:80])

    elif mode in ("stop", "restart"):
        if mode == "restart":
            out, err = ps("Stop-ScheduledTask -TaskName %s -ErrorAction SilentlyContinue; "
                          "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                          "Where-Object { $_.CommandLine -like '*ComfyUI-master*main.py*' } | "
                          "ForEach-Object { Stop-Process -Id $_.ProcessId -Force; "
                          "Write-Output ('KILL ' + $_.ProcessId) }" % TASK)
            print(out.strip() or "(no proc killed)")
            time.sleep(5)
        out, err = ps("%s-ScheduledTask -TaskName %s -ErrorAction SilentlyContinue; "
                      "Start-ScheduledTask -TaskName %s; Write-Output '%s'"
                      % ("Start-" if mode == "restart" else "Stop-", TASK, TASK, mode))
        print(out or err[:300])
        if mode == "restart":
            print("等待就绪…")
            sec = wait_ready()
            print(("✅ 就绪，用了 %d 秒" % sec) if sec > 0 else "❌ 超时未就绪")

    elif mode == "watch":
        # 队列守护也走计划任务常驻（nohup 会被沙箱回收，已实测）
        out, err = ps(
            "$a = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '%s'; "
            "$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries "
            "-DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) "
            "-RestartCount 0 -MultipleInstances IgnoreNew; "
            "Register-ScheduledTask -TaskName %s -Action $a -Settings $s -Force | Out-Null; "
            "Start-ScheduledTask -TaskName %s; Write-Output 'watch started'"
            % (WATCH_ARGS, WATCH_TASK, WATCH_TASK))
        print(out or err[:400])

    elif mode == "unwatch":
        out, _ = ps("Stop-ScheduledTask -TaskName %s -ErrorAction SilentlyContinue; "
                    "Unregister-ScheduledTask -TaskName %s -Confirm:$false "
                    "-ErrorAction SilentlyContinue; Write-Output 'unwatched'"
                    % (WATCH_TASK, WATCH_TASK))
        print(out)

    elif mode == "checkarg":
        # 诊断：计划任务里到底存了哪个输出目录。
        # 症状是"明明注册了 new，日志里仍是 D:\output"——需要看任务定义本身。
        out, _ = ps("(Get-ScheduledTask -TaskName %s).Actions | "
                    "ForEach-Object { Write-Output $_.Arguments }" % TASK)
        import re as _re
        m = _re.search(r"--output-directory\s+\"?([^\"\s]+)", out or "")
        print("任务定义里的输出目录：%s" % (m.group(1) if m else "未找到"))
        print("环境变量 MINIDRAMA_OUT：%s" % os.environ.get("MINIDRAMA_OUT", "(未设)"))
        log = LOG
        if os.path.exists(log):
            with open(log, "rb") as f:
                f.seek(max(0, os.path.getsize(log) - 60000))
                tail = f.read().decode("utf-8", "replace")
            got = _re.findall(r"output directory to: (.+)", tail)
            print("日志里最后实际生效的：%s" % (got[-1] if got else "未找到"))
        def _norm(x):
            # 计划任务里是 D:/output/new，日志里是 D:\output\new ——
            # 斜杠方向不同但**是同一个目录**，不归一化会误报"不一致"。
            return (x or "").strip().strip('"').replace("/", "\\").rstrip("\\").lower()
        if m and got and _norm(m.group(1)) != _norm(got[-1]):
            print("\n⚠️ 不一致：任务定义是 %s，但实际生效是 %s" % (m.group(1), got[-1]))
            print("   → 多半是旧实例还占着 8188（MultipleInstances IgnoreNew 会让")
            print("     新实例直接退出）。用：python _comfy_task.py restart")
        elif m and got:
            print("✅ 一致：%s" % got[-1])

    elif mode == "genwatch":
        # 生成巡检常驻（同样必须走计划任务，nohup 会被回收）
        outdir = os.environ.get("MINIDRAMA_OUT", DEFAULT_OUT)
        args = ('/c "set MINIDRAMA_OUT=%s&& "%s" -u "%s" --loop --heal > "%s" 2>&1"'
                % (outdir, WATCH_PY, GENWATCH_SCRIPT, GENWATCH_LOG))
        out, err = ps(
            "$a = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '%s'; "
            "$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries "
            "-DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) "
            "-RestartCount 0 -MultipleInstances IgnoreNew; "
            "Register-ScheduledTask -TaskName %s -Action $a -Settings $s -Force | Out-Null; "
            "Start-ScheduledTask -TaskName %s; Write-Output 'genwatch started out=%s'"
            % (args.replace("'", "''"), GENWATCH_TASK, GENWATCH_TASK, outdir))
        print(out or err[:400])

    elif mode == "ungenwatch":
        out, _ = ps("Stop-ScheduledTask -TaskName %s -ErrorAction SilentlyContinue; "
                    "Unregister-ScheduledTask -TaskName %s -Confirm:$false "
                    "-ErrorAction SilentlyContinue; Write-Output 'ungenwatched'"
                    % (GENWATCH_TASK, GENWATCH_TASK))
        print(out)

    elif mode == "remove":
        out, _ = ps("Stop-ScheduledTask -TaskName %s -ErrorAction SilentlyContinue; "
                    "Unregister-ScheduledTask -TaskName %s -Confirm:$false "
                    "-ErrorAction SilentlyContinue; Write-Output 'removed'" % (TASK, TASK))
        print(out)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
