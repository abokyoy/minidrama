# -*- coding: utf-8 -*-
"""生成流水线巡检：每 10 分钟看一次，把异常报出来。

用户要求「不要停下来，持续生成视频，监控生成过程」——
生成器自己会跑，但**卡住没人知道**。这个脚本负责盯：
  1. ComfyUI 是否还活着
  2. 当前段是否在正常时长内（超过 2 倍正常耗时 = 疑似卡死）
  3. 亮度是否达标（_grade.py 的阈值）
  4. 队列是否推进（有没有卡在同一段反复重跑）
发现异常立刻打出来，并可自动重启 ComfyUI 链。

用法：
  python _watch_gen.py              # 巡检一次，打印报告
  python _watch_gen.py --loop       # 常驻，每 10 分钟巡检一次
  python _watch_gen.py --loop --heal  # 常驻 + 发现卡死自动重启 ComfyUI
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
LOG = os.path.join(BASE, "logs", "gen_worker.log")
# 与生成器保持一致：可用 MINIDRAMA_OUT 覆盖。2026-10-04 换到 D:\output\new 后，
# 巡检还盯 D:\output，报"95 个 mp4"全是旧片 → 误以为在正常跑。
OUT = os.environ.get("MINIDRAMA_OUT", r"D:\output").replace("\\", "/")
SERVER = "http://127.0.0.1:8188"
EPISODES = ["ep001", "ep002", "ep003", "ep004", "ep005"]

# 单段正常耗时 10.8–16.7 分钟，超过 25 分钟视为疑似卡死
STUCK_MIN = 25.0
LOOP_MIN = 10.0
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def read_log():
    try:
        raw = io.open(LOG, "rb").read().decode("utf-8", errors="ignore")
        return ANSI.sub("", raw)
    except Exception as e:
        return ""


# 本轮起点（clean-log 时写入）：日志是 append 的，亮度统计必须只算
# 这一轮产出的段，否则换目录重跑后会一直报旧片的数字。
MARK = os.path.join(BASE, "logs", ".watch_mark")


def log_mark():
    try:
        with open(MARK) as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0


def mark_log():
    try:
        n = os.path.getsize(LOG)
        with open(MARK, "w") as f:
            f.write(str(n))
        print(" 已重置亮度统计起点 → %d 字节" % n)
    except Exception as e:
        print(" 标记起点失败：%s" % str(e)[:80])


def comfy_alive():
    try:
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
                  "ALL_PROXY", "all_proxy"):
            os.environ.pop(k, None)
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with op.open(SERVER + "/system_stats", timeout=6) as r:
            return r.status == 200
    except Exception:
        return False


def progress():
    """返回 [(集, 已完成段数, 总段数, 最新段id), ...]"""
    out = []
    for ep in EPISODES:
        segs = os.path.join(BASE, ep + "_segs")
        man_p = os.path.join(segs, "manifest.json")
        st_p = os.path.join(segs, "state.json")
        if not os.path.exists(man_p):
            continue
        try:
            man = json.load(io.open(man_p, encoding="utf-8"))
            total = len(man)
        except Exception:
            total = 0
        done, last = 0, "—"
        if os.path.exists(st_p):
            try:
                d = json.load(io.open(st_p, encoding="utf-8"))
                done = len(d)
                if done:
                    last = sorted(d.keys())[-1]
            except Exception:
                pass
        out.append((ep, done, total, last))
    return out


def cur_segment():
    """当前正在跑的段与其开始时间（分钟）。"""
    log = read_log()
    pending = re.findall(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] --- (\S+)\s+scene\s+(\S+)\s+(.*?)\s+\[", log)
    if not pending:
        return None
    ts, sid, scene, title = pending[-1]
    # 日志时间是本机本地时间，strptime 得到的是 naive 结构时间，直接减 epoch 即可
    t = time.mktime(time.strptime(ts, "%Y-%m-%d %H:%M:%S"))
    return sid, scene, title.strip(), (time.time() - t) / 60.0


def brightness():
    """从生成器日志里读亮度记录。

    ⚠️ 只统计**本轮**：日志是 append 的，改输出目录重跑后旧记录还在，
    直接统计会一直报"已测 70 段"（全是旧目录的片），看着像在正常跑。
    用 _mark() 在重启时记下日志字节偏移，之后只解析偏移之后的内容。
    """
    log = read_log()
    start = log_mark()
    if start and start < len(log):
        log = log[start:]
    rows = re.findall(r"亮度\s+(\S+)\s+mean=([\d.]+)\s+med=(\d+)\s+p05=(\d+)\s+p90=(\d+)\s+(\S+)", log)
    bad = [r for r in rows if r[5] != "OK"]
    means = [float(r[1]) for r in rows]
    trend = None
    if len(means) >= 20:
        h = len(means) // 2
        trend = sum(means[h:]) / len(means[h:]) - sum(means[:h]) / len(means[:h])
    return rows, bad, trend


def report():
    now = time.strftime("%H:%M:%S")
    print("=" * 62)
    print(" 巡检 %s" % now)
    print("=" * 62)

    alive = comfy_alive()
    print(" ComfyUI     : %s" % ("存活" if alive else "*** 无响应 ***"))

    pr = progress()
    tot_done = tot_all = 0
    for ep, done, total, last in pr:
        pct = (done / total * 100) if total else 0
        bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
        print(" %-8s %s %3d/%-3d %5.1f%%  最新 %s" % (ep, bar, done, total, pct, last))
        tot_done += done
        tot_all += total
    if tot_all:
        print(" 合计       : %d/%d 段（%.1f%%）" % (tot_done, tot_all, tot_done / tot_all * 100))

    seg = cur_segment()
    if seg:
        sid, scene, title, mins = seg
        flag = ""
        if mins > STUCK_MIN:
            flag = "  *** 超过 %.0f 分钟，疑似卡死 ***" % STUCK_MIN
        if not alive:
            flag = "  *** ComfyUI 没了 ***"
        print(" 当前段     : %s  scene %s  %s  已跑 %.1f 分钟%s"
              % (sid, scene, title[:22], mins, flag))
    else:
        print(" 当前段     : （无在跑任务，可能在链组间隙或已全部完成）")

    rows, bad, trend = brightness()
    if rows:
        t = "  无明显变暗趋势" if trend is None or trend > -8 else "  *** 疑似越接越暗 %+.1f ***" % trend
        print(" 亮度       : 已测 %d 段，达标 %d，非达标 %d%s"
              % (len(rows), len(rows) - len(bad), len(bad), t))
        for b in bad[-4:]:
            print("   ! %s mean=%s p05=%s -> %s" % (b[0], b[1], b[3], b[5]))
    else:
        print(" 亮度       : 暂无记录")

    n_mp4 = len([f for f in os.listdir(OUT) if f.endswith(".mp4")]) if os.path.isdir(OUT) else 0
    print(" D:\\output   : %d 个 mp4" % n_mp4)
    print()
    return alive, seg


def main():
    import functools
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    # 无论日志怎么重定向都保证实时落盘
    _p = functools.partial(print, flush=True)
    globals()["print"] = _p

    if "--clean-log" in sys.argv:
        mark_log()
        return
    if "--mark" in sys.argv:
        print("亮度统计起点 = %d" % log_mark())
        return

    loop = "--loop" in sys.argv
    heal = "--heal" in sys.argv
    # 常驻启动时重置亮度统计起点：日志是 append 的，不重置就会一直
    # 报换目录之前那批旧片的数字（看着像"已测 70 段 达标 69"，其实全是旧的）。
    if loop:
        mark_log()

    while True:
        alive, seg = report()
        stuck = (not alive) or (seg and seg[3] > STUCK_MIN)
        if heal and stuck:
            # ⚠️ 只重启 ComfyUI，**绝不能 taskkill 全部 python** ——
            #    那会把生成器（gen_worker）一起杀掉，等于自己把流水线掐了。
            print(">>> 卡死 detected（alive=%s）→ 只重启 ComfyUI，不动生成器" % alive)
            try:
                subprocess.run([sys.executable,
                                os.path.join(BASE, "_comfy_task.py"), "start"],
                               capture_output=True, timeout=420, errors="replace")
            except Exception as e:
                print("   重启调用失败：%s" % str(e)[:100])
        if not loop:
            return
        print("（%.0f 分钟后再次巡检）" % LOOP_MIN, flush=True)
        time.sleep(LOOP_MIN * 60)


if __name__ == "__main__":
    main()
