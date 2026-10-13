# -*- coding: utf-8 -*-
"""盯 xs001 五段生成到齐，做完自动体检（亮度/色调/码率/人物复制）。

为什么需要它（2026-10-04 20:45）：
  每段 9–11 分钟，5 段近 1 小时。干等是浪费，而且中途 ComfyUI 挂了、
  抢显存、链组顺序乱，都要人发现。→ 让脚本自己盯，异常立刻报。

体检四项（都踩过坑才加的）：
  ① **亮度分位** —— p05 太低 = 暗部死黑（"偏黑"）；p95/p99 太高 = 高光硬白（"没滤镜感"）
  ② **饱和 / 局部对比** —— 这两个才是"对比太大、不柔和"的量化指标
  ③ **码率** —— 花屏的可靠信号。灰度均值看不出花屏，但码率会暴跌到几百 kbps
  ④ **人物复制** —— 逐帧人脸数（侧脸/背身抓不到，所以辅以 contact sheet 人工看）

用法：
  python _wait_xs001.py            # 盯到 5 段出齐
  python _wait_xs001.py --check    # 不等，只体检已有的
"""
import glob
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = r"D:\output\new"
SEGS = ["xs01_t01", "xs01_t02", "xs01_t03", "xs01_t04", "xs01_t05"]
FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"E:\Program Files\ffmpeg\bin\ffprobe.exe"

# Seedance 实测目标
TARGET = dict(p01=9.6, p05=20.1, p25=71.7, p50=112.5, p75=150.4,
              p95=188.8, p99=212.6, sat=61.7, local=9.24)


def done_path(seg):
    """只认无后缀的主文件 —— ⚠️ `-audio.mp4` 也会匹配 `xs01_t*_00001*`，
    之前误把 6 个文件数成"5 段出齐"，实际只出了 3 段。"""
    p = os.path.join(OUT, "%s_00001.mp4" % seg)
    return p if os.path.exists(p) else None


def how_many():
    return sum(1 for s in SEGS if done_path(s))


def bitrate(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "format=bit_rate", "-of", "csv=p=0", path],
                       capture_output=True, text=True, errors="replace")
    try:
        return int(r.stdout.strip()) / 1000.0
    except ValueError:
        return -1.0


def measure(path, tag):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import _softgrade as SG
    return SG.measure(path, tag)


def check(path, seg):
    m = measure(path, "w_" + seg)
    br = bitrate(path)
    print("\n── %s ──" % seg)
    print("  p01=%5.1f p05=%5.1f p25=%5.1f p50=%5.1f p75=%5.1f p95=%5.1f p99=%5.1f"
          % tuple(m[k] for k in SG_KEYS))
    print("  饱和=%5.1f（目标 %.1f）  局部对比=%5.2f（目标 %.2f）  码率=%.0f kbps"
          % (m["sat"], TARGET["sat"], m["local"], TARGET["local"], br))
    flags = []
    if m["p05"] < 10:
        flags.append("暗部死黑（p05<10）")
    if m["local"] > TARGET["local"] * 1.25:
        flags.append("局部对比过高=画面硬（%.2f > %.2f）" % (m["local"], TARGET["local"]))
    if m["sat"] > TARGET["sat"] * 1.18:
        flags.append("过艳（%.1f > %.1f）" % (m["sat"], TARGET["sat"]))
    if m["p99"] > 235:
        flags.append("高光死白（p99>235）")
    if br < 1500:
        flags.append("★码率过低 %.0f kbps → 可能花屏" % br)
    if flags:
        print("  ⚠️ " + "；".join(flags))
    else:
        print("  ✔ 各项正常")
    return m


SG_KEYS = ["p01", "p05", "p25", "p50", "p75", "p95", "p99"]


def main():
    check_only = "--check" in sys.argv
    limit = 90          # 最多等 90 分钟
    t0 = time.time()

    if not check_only:
        print("等待 5 段出齐（最多 %d 分钟）…" % limit)
        last = -1
        while how_many() < 5 and time.time() - t0 < limit * 60:
            n = how_many()
            if n != last:
                print("  %s  %d/5 出齐" % (time.strftime("%H:%M:%S"), n))
                last = n
            time.sleep(30)
        n = how_many()
        if n < 5:
            print("超时：只出了 %d/5 段" % n)
            return

    print("\n全部出齐，开始体检：")
    ms = []
    for s in SEGS:
        p = done_path(s)
        if p:
            ms.append((s, check(p, s)))
        else:
            print("\n── %s ── 缺失" % s)

    if ms:
        print("\n" + "=" * 64)
        print("汇总（对比 Seedance 目标）")
        print("=" * 64)
        print("%-6s %7s %7s %7s %7s %7s %7s %7s"
              % ("段", "p05", "p25", "p50", "p95", "p99", "饱和", "局部"))
        for s, m in ms:
            print("%-6s %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.2f"
                  % (s, m["p05"], m["p25"], m["p50"], m["p95"], m["p99"],
                     m["sat"], m["local"]))
        print("%-6s %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.2f  ★目标"
              % ("SD", TARGET["p05"], TARGET["p25"], TARGET["p50"],
                 TARGET["p95"], TARGET["p99"], TARGET["sat"], TARGET["local"]))


if __name__ == "__main__":
    main()
