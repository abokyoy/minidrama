#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""调度器看门狗。

⛔⛔⛔ 它存在的原因（2026-10-09 20:00 事故）：
   17:18 ComfyUI 自己崩了 → 调度器进程跟着消失 → GPU 空转 2h42m 无人发现。
   光把调度器改成 detached **不够**：它自己崩了照样没人管。
   → 必须有一个更小的、极不容易崩的进程盯着它。

判据（每 60 秒一轮，三条任意一条成立就拉起调度器）：
   ① 调度器进程不存在            → 直接起
   ② 调度器在，但台账里所有片都
      不是 pending/running       → 说明它跑了没片了，正常待命，**不起**
      （待命是正常的，resume 一叫它就回来；这里只管"该跑却没跑"）
   ③ 有一片 status=running 且
      started_at 超过 90 分钟     → 调度器卡死 → 杀掉重启
   ④ 连续 3 轮检测到 GPU 利用率 0%
      且台账还有 pending          → 肯定没人在生成 → 起

⛔ 起之前先杀干净旧的 `_kill_old.py`，否则显存抢爆。
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
           "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)

PY = sys.executable
LEDGER = os.path.join(HERE, "show_ledger.json")
INTERVAL = 60
RUNNING_TIMEOUT = 90 * 60      # 一片正常 13-15 分钟，90 分钟还不落盘 = 卡死
GPU_ZERO_ROUNDS = 3            # 连续 3 分钟 GPU 空 → 判定没人干活


def log(*a):
    print("[%s]" % time.strftime("%H:%M:%S"), *a, flush=True)


def sched_alive():
    """调度器进程在不在。用 tasklist 找命令行含 scheduler.py 的 python。"""
    try:
        out = subprocess.run(["tasklist", "/v", "/fo", "csv"],
                             capture_output=True, text=True,
                             encoding="utf-8", errors="replace",
                             timeout=40).stdout
    except Exception as e:
        log("tasklist 失败", e)
        return False
    # tasklist 不带命令行 → 退而求其次：查 pid 文件
    pf = os.path.join(HERE, "_sched.pid")
    if os.path.exists(pf):
        try:
            pid = int(open(pf).read().strip())
            r = subprocess.run(["tasklist", "/fi", "PID eq %d" % pid],
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               timeout=30).stdout
            if str(pid) in r and "python" in r.lower():
                return True
        except Exception:
            pass
    del out
    return False


def read_led():
    try:
        return json.load(open(LEDGER, encoding="utf-8"))
    except Exception:
        return None


def pending_count(led):
    sg = led.get("segments", {})
    return sum(1 for v in sg.values()
               if v.get("status") in ("pending", "running"))


def gpu_util():
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20)
        return int(r.stdout.strip().splitlines()[0])
    except Exception:
        return -1


def running_stuck(led):
    sg = led.get("segments", {})
    for k, v in sg.items():
        if v.get("status") != "running":
            continue
        ep = v.get("run_epoch")
        if not ep:
            continue
        age = time.time() - float(ep)
        if age > RUNNING_TIMEOUT:
            return k, int(age / 60)
    return None


def start_sched():
    log("▶ 拉起调度器")
    lf = open(os.path.join(HERE, "_sched_run.log"), "a",
              encoding="utf-8", buffering=1)
    p = subprocess.Popen([PY, "-u", "scheduler.py", "run"], cwd=HERE,
                         env=dict(os.environ), stdout=lf,
                         stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         creationflags=0x00000008 | 0x00000200)
    try:
        open(os.path.join(HERE, "_sched.pid"), "w").write(str(p.pid))
    except Exception:
        pass
    log("  pid=%s" % p.pid)


def kill_sched():
    pf = os.path.join(HERE, "_sched.pid")
    if not os.path.exists(pf):
        return
    try:
        pid = int(open(pf).read().strip())
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                       capture_output=True, timeout=60)
        log("  已杀调度器 pid=%s" % pid)
        os.remove(pf)
    except Exception as e:
        log("  杀调度器失败", e)


def kill_comfy():
    try:
        subprocess.run([PY, os.path.join(HERE, "_kill_old.py")],
                       capture_output=True, timeout=240, cwd=HERE,
                       env=dict(os.environ))
        log("  已清场（ComfyUI + 吃内存的进程）")
    except Exception as e:
        log("  清场失败", e)


def main():
    log("看门狗启动，每 %d 秒巡一轮" % INTERVAL)
    zero = 0
    while True:
        try:
            led = read_led()
            alive = sched_alive()
            np_pend = pending_count(led) if led else 0
            u = gpu_util()

            # ① 调度器不在 → 起（除非压根没片可跑）
            if not alive:
                if np_pend == 0:
                    zero = 0
                    log("调度器不在，但没有待跑的片 → 待命（resume 可叫醒）")
                else:
                    start_sched()
                    zero = 0
                time.sleep(INTERVAL)
                continue

            # ③ 在跑但超 90 分钟 → 卡死，重启
            if led:
                st = running_stuck(led)
                if st:
                    sid, mins = st
                    log("‼ 片%s 已标 running 但 %d 分钟没落盘 → 判定卡死"
                        % (sid, mins))
                    kill_sched()
                    kill_comfy()
                    led = read_led()
                    if led:
                        v = led["segments"][sid]
                        v["status"] = "pending"
                        v["out"] = None
                        v["run_epoch"] = None
                        v["started_at"] = None
                        json.dump(led, open(LEDGER + ".tmp", "w",
                                  encoding="utf-8"),
                                  ensure_ascii=False, indent=2)
                        os.replace(LEDGER + ".tmp", LEDGER)
                        log("  片%s 已回退 pending" % sid)
                    start_sched()
                    zero = 0
                    time.sleep(INTERVAL)
                    continue

            # ④ 连续 GPU 空转
            if u == 0 and np_pend > 0:
                zero += 1
                if zero >= GPU_ZERO_ROUNDS:
                    log("‼ GPU 连续 %d 分钟 0%%，但还有 %d 片待跑 → 重启调度器"
                        % (zero, np_pend))
                    kill_sched()
                    kill_comfy()
                    start_sched()
                    zero = 0
            else:
                if zero:
                    log("  GPU 恢复 %d%%，撤销空转计数" % u)
                zero = 0

        except Exception as e:
            log("巡检异常（忽略继续）:", repr(e))
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()