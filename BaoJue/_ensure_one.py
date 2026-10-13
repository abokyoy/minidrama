# -*- coding: utf-8 -*-
"""只保留**一个** ComfyUI，并把生成器固定到 D:\\output\\new。

为什么需要这个脚本（本会话踩了 3 次）：
  · 反复出现**两个 ComfyUI 同时在跑** —— 一个 venv(3.13)、一个系统 Python310。
    两个都占显存 → H3 采样 OOM / 超时 → driver 报「后台任务失败」。
  · 出现的原因：注册计划任务时 ComfyUI 任务**没被先停掉**，于是旧的还活着、
    新的又被拉起来；`MultipleInstances IgnoreNew` 只拦「同名任务」，
    拦不住「上一个任务的残留进程」。
  · `_task.py start` 不带参数、OUT_DIR 走环境变量默认值 D:\\output，
    于是片子又落回旧目录（用户 2026-10-04 要求新片进 D:\\output\\new）。

所以这里做三件事，顺序不能反：
  1. 停所有计划任务（生成器 + ComfyUI + 兜底重启）
  2. 杀所有 ComfyUI / h3_driver / _run_gen 进程，杀到干净为止（最多 6 轮）
  3. 只重启**一个** ComfyUI，输出目录写死 D:\\output\\new

用法：
  python _ensure_one.py --status     # 只看现状
  python _ensure_one.py --fix        # 清理 + 单实例重启（生成器不动）
  python _ensure_one.py --fix --with-gen xs001   # 连生成器一起重启
"""
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = r"D:\output\new"
COMFY = "minidrama_comfyui"
TASKS = ["minidrama_comfyui", "minidrama_gen001", "minidrama_genwatch",
         "minidrama_fixaudio"]


def ps(cmd):
    r = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", cmd],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return (r.stdout or "") + (("ERR:" + r.stderr) if r.stderr else "")


def procs():
    out = ps("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "ForEach-Object { Write-Output ($_.ProcessId.ToString() + '|' + $_.CommandLine) }")
    rows = []
    for line in out.splitlines():
        if "|" not in line:
            continue
        pid, _, cl = line.partition("|")
        pid = pid.strip()
        if pid.isdigit():
            rows.append((int(pid), cl.strip()))
    return rows


def is_comfy(cl):
    return "main.py" in cl and "--output-directory" in cl


def is_gen(cl):
    return any(k in cl for k in ("_run_gen.py", "h3_driver.py", "gen_worker.py"))


def show():
    print("== 计划任务 ==")
    print(ps("Get-ScheduledTask -TaskName 'minidrama*' -ErrorAction SilentlyContinue | "
             "ForEach-Object { Write-Output ($_.TaskName + ' | ' + $_.State) }").strip() or "(none)")
    print("== 进程 ==")
    nc = ng = 0
    for pid, cl in procs():
        if is_comfy(cl):
            nc += 1
            tag = "COMFY "
        elif is_gen(cl):
            ng += 1
            tag = "GEN   "
        else:
            continue
        print("  %s %6d  %s" % (tag, pid, cl[:95]))
    print("  ComfyUI=%d  生成相关=%d" % (nc, ng))
    if nc > 1:
        print("  ⚠️ 多个 ComfyUI 并存 → 抢显存 → 必超时。用 --fix 收拾。")
    return nc


def stop_tasks():
    for t in TASKS:
        ps("Stop-ScheduledTask -TaskName '%s' -ErrorAction SilentlyContinue" % t)
    ps("Disable-ScheduledTask -TaskName '%s' -ErrorAction SilentlyContinue" % COMFY)
    print("已停全部任务")


def kill_all():
    for rnd in range(1, 7):
        n = 0
        for pid, cl in procs():
            if is_comfy(cl) or is_gen(cl):
                subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                               capture_output=True)
                n += 1
        if n == 0:
            print("第 %d 轮：已干净" % rnd)
            return True
        print("第 %d 轮：杀掉 %d 个" % (rnd, n))
        time.sleep(3)
    return False


def start_one_comfy():
    """直接起一个，不走计划任务（计划任务的启动会带上旧参数）。"""
    cmd = (r'"E:\ComfyUI\ComfyUI-master\ComfyUI-master\venv\Scripts\python.exe" main.py '
           r'--lowvram --enable-triton-backend --output-directory "%s" '
           r'--temp-directory "D:\ComfyUI_out\ComfyUI-master\temp"' % OUT)
    subprocess.Popen(["cmd", "/c", "start", "", "/min", cmd],
                     cwd=r"E:\ComfyUI\ComfyUI-master\ComfyUI-master")
    print("已拉起单个 ComfyUI → %s" % OUT)
    time.sleep(25)
    # 若又冒出第二个（守护在拉），杀掉多出来的
    cs = [(p, c) for p, c in procs() if is_comfy(c)]
    if len(cs) > 1:
        for p, _ in sorted(cs, key=lambda x: x[0])[:-1]:
            subprocess.run(["taskkill", "/F", "/PID", str(p)], capture_output=True)
            print("  多余 ComfyUI 已杀: %d" % p)
    for p, c in procs():
        if is_comfy(c):
            print("  保留 ComfyUI %d" % p)
    return len([1 for p, c in procs() if is_comfy(c)]) == 1


def main():
    args = sys.argv[1:]
    if "--status" in args:
        show()
        return
    if "--fix" not in args:
        show()
        print("\n用法: --status | --fix [--with-gen xs001]")
        return

    stop_tasks()
    kill_all()
    ok = start_one_comfy()
    print("单实例 ComfyUI: %s" % ("OK" if ok else "仍有多实例"))

    if "--with-gen" in args:
        i = args.index("--with-gen")
        eps = args[i + 1] if i + 1 < len(args) else "xs001"
        env = dict(os.environ, MINIDRAMA_OUT=OUT)
        r = subprocess.run([sys.executable, "_task.py", "register"] + eps.split(),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=env)
        print((r.stdout or "").strip()[:200])
        time.sleep(15)
    show()


if __name__ == "__main__":
    main()
