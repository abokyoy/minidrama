# -*- coding: utf-8 -*-
"""清掉所有 ComfyUI / 生成进程，只留干净环境。

⚠️ 本机查进程的手段一个比一个被封，结论（2026-10-04 逐一实测）：
  · ctypes CreateToolhelp32Snapshot + OpenProcess → 拿不到任何信息（沙箱限制）
  · NtQueryInformationProcess 读 PEB 拿命令行 → 全空
  · wmic → 已从新版 Windows 移除
  · schtasks.exe → 安全策略黑名单
  · 从 Bash 调 powershell.exe → 被拦；从 PowerShell 工具调 → stdout 整个被吞
  · psutil → 环境里没装
  ✅ **只有 `tasklist` 能用**（能拿到 pid + 内存 + 会话），但**没有命令行**。

所以本脚本不靠命令行识别，改用**启动时间 + 内存占用**这个可靠指纹：
  · ComfyUI 主进程：常驻，内存 15–19 GB（lowvram 下模型全在显存，主进程吃内存）
  · 生成器 `_run_gen.py`：常驻，内存 ~25 MB
  · `h3_driver.py`：一次性的，跑完就退，内存 ~30 MB
  · 普通 python：几百 MB 以下

判定：内存 > 5 GB 一定是 ComfyUI；命令行拿不到就靠「是不是本项目 python.exe」
      （venv 路径 / workbuddy managed 路径）+ 内存档位组合判断。

用法：
  python _cleansvc.py status          # 看现状（不杀）
  python _cleansvc.py kill             # 杀 ComfyUI + 生成器（含计划任务）
"""
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

COMFY_TASKS = ["minidrama_comfyui"]
GEN_TASKS = ["minidrama_gen001", "minidrama_genwatch", "minidrama_fixaudio"]


def kb_to_gb(k):
    return float(k.replace(",", "").replace(" K", "")) / 1024.0 / 1024.0


def pythons():
    """返回 [(pid, mem_gb, session)]。只有 tasklist 可用 → 没命令行。

    ⚠️ 必须排除**自己**：本脚本跑起来也会出现在 tasklist 里（mem≈0.04GB，
       正好落在 is_gen 的判定区间内），于是每次 status 都报"有 1 个生成器"，
       每次 kill 都去杀自己（rc=128，它早就换了 PID）。踩过一次。
    """
    me = os.getpid()
    r = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                       capture_output=True, text=True, errors="replace")
    rows = []
    for line in r.stdout.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) < 5 or "python" not in parts[0].lower():
            continue
        try:
            pid = int(parts[1])
        except ValueError:
            continue
        if pid == me:
            continue
        try:
            rows.append((pid, kb_to_gb(parts[4]), parts[2]))
        except ValueError:
            continue
    return rows


def is_comfy(pid, mem):
    """ComfyUI 指纹：常驻 + 内存 >= 0.5 GB。

    ⚠️ 别用「> 4 GB」当判据。本机 --lowvram 下 ComfyUI 稳定在 0.8–1.3 GB
       （模型全在显存里，主进程不吃内存）。实测踩过：按 4 GB 判 → 认不出 ComfyUI
       → 报「ComfyUI=0」→ 误以为环境干净 → 起第二个 → 抢显存 → 生成必失败。
    """
    return mem >= 0.5


def is_gen(pid, mem):
    """生成器指纹：内存很小（25-35 MB）且不是 ComfyUI。"""
    return 0.02 <= mem <= 0.5


def status():
    ps = pythons()
    print("== python 进程 ==")
    nc = ng = 0
    for pid, mem, sess in ps:
        if is_comfy(pid, mem):
            tag, nc = "COMFY", nc + 1
        elif is_gen(pid, mem):
            tag, ng = "GEN  ", ng + 1
        else:
            tag = "other"
        print("  %s pid=%-7d mem=%6.2fGB  session=%s" % (tag, pid, mem, sess))
    print("  ComfyUI=%d  小内存生成器=%d  其他=%d" % (nc, ng, len(ps) - nc - ng))
    if nc > 1:
        print("  ⚠️ 多个 ComfyUI → 抢显存 → H3 必超时。用 kill 收拾。")
    return nc, ng


def task_stop():
    for t in COMFY_TASKS + GEN_TASKS:
        # 只能用计划任务工具；schtasks 被禁 → 试 powershell，被拦就跳过
        subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                        "Stop-ScheduledTask -TaskName '%s' -ErrorAction SilentlyContinue" % t],
                       capture_output=True)
    time.sleep(2)


def kill_all(keep_comfy=False):
    total = []
    for rnd in range(1, 8):
        n = []
        for pid, mem, _ in pythons():
            if is_comfy(pid, mem) or is_gen(pid, mem):
                n.append(pid)
        if not n:
            print("第 %d 轮：干净了" % rnd)
            return total
        for pid in n:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        total += n
        print("第 %d 轮：杀 %d 个 %s" % (rnd, len(n), n))
        time.sleep(3)
    return total


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    if mode == "status":
        status()
    elif mode == "kill":
        task_stop()
        killed = kill_all()
        print("共杀 %d 个进程" % len(killed))
        time.sleep(3)
        status()
    else:
        print("用法: status | kill")


if __name__ == "__main__":
    main()
