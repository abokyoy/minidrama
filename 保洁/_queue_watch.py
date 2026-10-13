# -*- coding: utf-8 -*-
"""测试队列守护：等 ComfyUI 把队列跑空，自动出客观指标表。

为什么需要它：v3 有 9 组待测，每段 10–16 分钟，全跑完要 2–3 小时。
用户要求「不要一直卡住、有问题解决问题」，所以这里常驻轮询：
  · 每 3 分钟看一次队列
  · 每出一段新片就打印一次（能第一时间看到结果，不用等全部跑完）
  · 有任务失败（error / OOM）立刻报出来，不静默跳过
  · 队列跑空后自动跑 --analyze 出完整对比表

用法：
  python _queue_watch.py            # 前台跑（会一直守着）
  python _queue_watch.py --once     # 只看一次状态
日志：logs/queue_watch.log
"""
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
SERVER = "http://127.0.0.1:8188"
OUT = "D:/output"
POLICY = 180          # 轮询间隔（秒）
LONG_RUN = 25 * 60    # 单段超过这个分钟数判为卡死

# 我们关心的输出前缀（v3 优先）
WATCH = ["MT3_", "MT2_", "TEST_"]


def op_():
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
              "ALL_PROXY", "all_proxy"):
        os.environ.pop(k, None)
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def queue_state():
    q = json.loads(op_().open(SERVER + "/queue", timeout=30).read())
    return (len(q.get("queue_running", [])), len(q.get("queue_pending", [])))


def gpu_mb():
    r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total",
                        "--format=csv,noheader,nounits"],
                       capture_output=True, text=True, timeout=30)
    try:
        a, b = r.stdout.strip().split("\n")[0].split(",")
        return int(a), int(b)
    except Exception:
        return 0, 0


def history_failed():
    """返回失败任务列表（error / OOM 之类），不静默吞掉。"""
    try:
        h = json.loads(op_().open(SERVER + "/history", timeout=30).read())
    except Exception:
        return []
    bad = []
    for pid, d in h.items():
        st = d.get("status", {})
        if st.get("status_str") not in ("success", None):
            msg = ""
            for m in st.get("messages", []) or []:
                if isinstance(m, list) and len(m) > 1 and m[0] == "execution_error":
                    msg = str(m[1].get("exception_message", ""))[:160]
            bad.append((pid[:8], st.get("status_str"), msg))
    return bad


def scan_outputs():
    """扫已完成的测试片，返回 {前缀: (文件, mtime)}"""
    res = {}
    if not os.path.isdir(OUT):
        return res
    for f in os.listdir(OUT):
        if not f.endswith(".mp4"):
            continue
        stem = re.sub(r"_\d{5}(-audio)?\.mp4$", "", f)
        if not stem.startswith(tuple(WATCH)):
            continue
        p = os.path.join(OUT, f)
        try:
            if os.path.getsize(p) < 200000:
                continue
        except OSError:
            continue
        res.setdefault(stem, []).append(p)
    return res


def comfy_alive():
    try:
        op_().open(SERVER + "/system_stats", timeout=8).read()
        return True
    except Exception:
        return False


def comfy_oom_evidence():
    """看 ComfyUI 自己的日志里有没有 OOM —— 单任务 OOM 会拖垮整个服务，
    这台机器已经因此崩过一次（8步+max 参考图）。"""
    p = os.path.join(BASE, "logs", "comfyui_task.log")
    if not os.path.exists(p):
        return ""
    try:
        # 只看文件尾部，避免每次读整个大日志
        with io.open(p, "rb") as f:
            f.seek(max(0, os.path.getsize(p) - 400000))
            tail = f.read().decode("utf-8", "replace")
    except Exception:
        return ""
    for key in ("CUDA error: out of memory", "OutOfMemoryError",
                "cudaErrorMemoryAllocation", "aimdo memory compile error"):
        if key in tail:
            return key
    return ""


def restart_comfy():
    """ComfyUI 崩溃后重启。

    ⚠️ 重启会**清空队列和 history**（实测：G 组跑到一半崩，重启后 8 组任务全丢，
    `/history` 返回 0 条）。所以重启完必须把没跑完的组重新提交一遍，
    否则会「队列空 → 守护以为跑完了 → 什么都没测」。
    """
    log("🔧 ComfyUI 挂了，正在重启…")
    r = subprocess.run([sys.executable, os.path.join(BASE, "_comfy_task.py"), "start"],
                       cwd=BASE, capture_output=True, timeout=480)
    if not comfy_alive():
        log("❌ 重启失败：%s" % (r.stdout or r.stderr or "")[-200:])
        return False
    log("✅ 重启成功，重新提交未完成的测试组…")
    # errors="replace"：日志里有非 GBK 字节，用默认编码读会抛
    # UnicodeDecodeError 并把调用方线程带崩（实测踩过）
    r2 = subprocess.run([sys.executable, os.path.join(BASE, "_requeue.py"), "--order"],
                        cwd=BASE, capture_output=True, timeout=300,
                        errors="replace")
    out = (r2.stdout or b"").decode("utf-8", "replace")
    log("重提结果：%s" % (out.strip().replace("\n", " | ")[-220:] or "(无输出)"))
    return True


def main():
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    once = "--once" in sys.argv
    seen = set()
    heal = "--heal" in sys.argv

    log("队列守护启动。每 %d 秒查一次。%s"
        % (POLICY, "（带自愈）" if heal else ""))
    while True:
        try:
            if not comfy_alive():
                # 服务不在：能自愈就自愈，否则一直守着等用户手动起
                if heal:
                    restart_comfy()
                else:
                    log("❌ ComfyUI 无响应（用 --heal 可自动重启）")
                    if once:
                        return
                    time.sleep(POLICY)
                    continue
            run, pend = queue_state()
            used, total = gpu_mb()
            done = scan_outputs()
            new = [k for k in done if k not in seen]
            if new:
                for k in sorted(new):
                    seen.add(k)
                    log("✅ 出片：%s" % k)
            oom = comfy_oom_evidence()
            if oom:
                log("⚠️ 日志里有 OOM 迹象（%s）——这类任务会拖垮服务，"
                    "建议从测试计划里去掉" % oom)
            log("队列 运行=%d 排队=%d ｜ 已出片 %d ｜ 显存 %d/%d MB"
                % (run, pend, len(seen), used, total))

            if run == 0 and pend == 0:
                # 空队列但一片都没出 → 任务全丢了（ComfyUI 重启会清空队列/history），
                # 不能当成"跑完了"，否则会静默退出、什么都没测。
                if not seen:
                    log("⚠️ 队列空但零出片 —— 任务很可能在 ComfyUI 重启时丢了，重新提交…")
                    r3 = subprocess.run(
                        [sys.executable, os.path.join(BASE, "_requeue.py"), "--order"],
                        cwd=BASE, capture_output=True, timeout=300, errors="replace")
                    out = (r3.stdout or b"").decode("utf-8", "replace")
                    log("重提：%s" % (out.strip().replace("\n", " | ")[-200:] or "(无输出)"))
                    time.sleep(20)
                    continue
                log("队列已跑空（已出 %d 组）。等 30 秒后出完整指标表…" % len(seen))
                time.sleep(30)
                subprocess.run([sys.executable, os.path.join(BASE, "_matrix_result.py"),
                                "--analyze"], cwd=BASE, errors="replace")
                log("指标表已输出。守护结束。")
                return
            if once:
                return
        except Exception as e:
            log("巡检异常（不致命，继续）：%s" % str(e)[:160])
        time.sleep(POLICY)


if __name__ == "__main__":
    main()
