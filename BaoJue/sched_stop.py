# -*- coding: utf-8 -*-
"""打断指令通道 —— 让「用户否定某片」能立刻改变正在跑的调度。

⛔⛔⛔ 2026-10-09 用户定义的打断语义（调度器必须照做）：

  · 「如果当前 GPU 在运行的任务不是这一个片所在的链，那你就不用管，
     就等 GPU 把当前这一次任务运行完，运行完了以后，然后再插队。」
  · 「如果当前的任务刚好又是这个片所在的这个链，那么就**停止当前的这个
     生成的任务**，直接跳到下一个链的第一个片去做，
     同时你开始分析问题……然后你再插队。」

做法：一个 JSON 停机文件当信箱。
  · `scheduler.py reject 5` 会 **自己判断**：
      - 当前正在跑的片 == 链2  → 写 "kill" 信箱，调度器 20 秒内察觉 → 放弃当前片
      - 当前正在跑的片 != 链2  → 只把链2 打回 pending（自然会在链2 轮到时重跑）
  · 调度器不轮询数据库文件，只看这个信箱 → 简单、跨进程安全。
"""

import io
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STOPFILE = os.path.join(HERE, "sched_stop.json")


def put_kill(sid, reason=""):
    """给正在跑的那片发「放弃」信号。"""
    d = {}
    if os.path.exists(STOPFILE):
        try:
            d = json.load(io.open(STOPFILE, encoding="utf-8"))
        except Exception:
            d = {}
    d[str(sid)] = {"kill": True, "why": reason, "t": time.strftime("%H:%M:%S")}
    tmp = STOPFILE + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False))
    os.replace(tmp, STOPFILE)
    return STOPFILE


def take(sid):
    """调度器轮询：这片有没有被要求放弃。"""
    if not os.path.exists(STOPFILE):
        return None
    try:
        d = json.load(io.open(STOPFILE, encoding="utf-8"))
    except Exception:
        return None
    return d.get(str(sid))


def clear(sid):
    if not os.path.exists(STOPFILE):
        return
    try:
        d = json.load(io.open(STOPFILE, encoding="utf-8"))
    except Exception:
        return
    if str(sid) in d:
        d.pop(str(sid))
        with io.open(STOPFILE, "w", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False))


def current_running(led):
    """台账里当前**真正在跑**的那一片。

    ⛔ 必须取**最近启动**的那片，不能简单取第一个 status==running：
      异常残留（上一片没回写成 done）会同时留两条 running，
      「取第一个」会把信号发给一片没在跑的 → 打断失效。
      → 用 started_at 时间戳选最新的那条；没有时间戳的排在最后。
    """
    best, best_t = None, ""
    for k, sg in led["segments"].items():
        if sg["status"] != "running":
            continue
        t = sg.get("started_at") or ""
        if best is None or t > best_t:
            best, best_t = int(k), t
    return best
