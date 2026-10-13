# -*- coding: utf-8 -*-
"""建立 Seedance 的客观指标基线 —— 让「接近 Seedance」变成可验证的数字。

问题：用户要求「确保效果和 Seedance 一样」。这句话没法靠肉眼保证，
必须先知道 Seedance 在**同一套指标**下是多少，才能判断本地 H3 差在哪、差多少。

指标（与 _matrix_result.py 完全一致，保证可比）：
  亮度 YAVG / 动态范围 YDIF / **帧间抖动**（越低越好，对应人物跳跃、镜头不连续）
  锐度（拉普拉斯方差，越高越锐）/ 4–8kHz 高频能量（人声清晰度）
  分辨率 / 码率 / 音频采样率

用法：
  python _seedance_base.py           # 测 Seedance 4 支
  python _seedance_base.py --cmp     # 同时测本地 H3，做成对比表
"""
import glob
import io
import json
import os
import re
import subprocess
import sys

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"E:\Program Files\ffmpeg\bin\ffprobe.exe"
SEED = "D:/output/Seedance"
LOCAL = "D:/output"


def _grab(stderr, key):
    m = re.search(key + r"=([\d.]+)", stderr or "")
    return float(m.group(1)) if m else None


def metrics(p, tmpdir):
    """与 _matrix_result.py 同口径的指标。"""
    m = {}
    os.makedirs(tmpdir, exist_ok=True)
    one = os.path.join(tmpdir, "f.png")
    # 锐度 + 亮度 + 动态：取第 4 秒一帧
    subprocess.run([FFMPEG, "-v", "error", "-ss", "4", "-i", p, "-frames:v", "1",
                    "-vf", "format=gray", "-f", "image2", "-y", one],
                   capture_output=True, timeout=90)
    if os.path.exists(one):
        for key, ck in (("lap", None), ("bright", "YAVG"), ("range", "YDIF")):
            vf = "format=gray"
            if key == "lap":
                vf = ("convolution=0:1:1:1:0:-1:1:0:-1:0:1:0:-1:1:0:0,"
                      "signalstats,metadata=print:key=lavfi.signalstats.YAVG")
            else:
                vf = "signalstats,metadata=print:key=lavfi.signalstats.%s" % ck
            r = subprocess.run([FFMPEG, "-v", "error", "-i", one, "-vf", vf,
                                "-f", "null", "-"],
                               capture_output=True, text=True, errors="replace", timeout=90)
            m[key] = _grab(r.stderr, "YAVG")
    # 帧间抖动：越高越跳
    r4 = subprocess.run([FFMPEG, "-v", "error", "-i", p, "-vf",
                         "tblend=all_mode=difference,signalstats,"
                         "metadata=print:key=lavfi.signalstats.YAVG",
                         "-f", "null", "-"], capture_output=True, text=True,
                        errors="replace", timeout=240)
    vals = [float(x) for x in re.findall(r"YAVG=([\d.]+)", r4.stderr or "")]
    if vals:
        m["jitter"] = sum(vals) / len(vals)
        m["jitter_max"] = max(vals)
    # 人声高频
    r5 = subprocess.run([FFMPEG, "-v", "error", "-i", p, "-t", "8",
                         "-af", "highpass=f=4000,astats=metadata=1:reset=0",
                         "-f", "null", "-"], capture_output=True, text=True,
                        errors="replace", timeout=150)
    mm = re.search(r"RMS level dB:\s*(-?[\d.]+|-inf)", r5.stderr or "")
    if mm and mm.group(1) != "-inf":
        m["hf_db"] = float(mm.group(1))
    # 容器信息
    pr = subprocess.run([FFPROBE, "-v", "error", "-show_entries",
                         "stream=codec_type,width,height,sample_rate,bit_rate",
                         "-show_entries", "format=duration,bit_rate",
                         "-of", "json", p], capture_output=True, text=True,
                        errors="replace", timeout=60)
    try:
        d = json.loads(pr.stdout)
    except Exception:
        d = {}
    a = [s for s in d.get("streams", []) if s.get("codec_type") == "audio"]
    v = [s for s in d.get("streams", []) if s.get("codec_type") == "video"]
    if v:
        m["res"] = "%sx%s" % (v[0].get("width"), v[0].get("height"))
    m["sr"] = a[0].get("sample_rate") if a else None
    m["kbps"] = int(d.get("format", {}).get("bit_rate", 0) or 0) // 1000
    m["dur"] = round(float(d.get("format", {}).get("duration", 0) or 0), 1)
    return m


def main():
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    cmp_mode = "--cmp" in sys.argv
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_cmp", "tmp")
    rows = []

    print("测 Seedance 基准…", flush=True)
    for f in sorted(glob.glob(os.path.join(SEED, "*.mp4"))):
        name = os.path.basename(f).replace("清洁女工与富客走廊冲突", "Seedance")
        print("  %s …" % name, flush=True)
        m = metrics(f, tmp)
        m["name"] = name[:26]
        rows.append(m)

    if cmp_mode:
        for f in sorted(glob.glob(os.path.join(LOCAL, "ep01_t6*_00001-audio.mp4")))[:2]:
            print("  本地 %s …" % os.path.basename(f), flush=True)
            m = metrics(f, tmp)
            m["name"] = "本地 " + os.path.basename(f)[:18]
            rows.append(m)

    print()
    print("=" * 104)
    print(" Seedance 客观指标基线（同一套指标，可直接与本地 H3 对比）")
    print("=" * 104)
    print(" %-28s %-10s %6s %6s %7s %7s %6s %7s %6s" %
          ("片", "分辨率", "亮度", "动态", "帧抖动", "抖动峰", "高频dB", "音频kbps", "采样率"))
    print(" " + "-" * 100)
    for m in rows:
        print(" %-28s %-10s %6s %6s %7s %7s %6s %7s %6s" % (
            m["name"][:28], m.get("res", "?"), _f(m.get("bright")), _f(m.get("range")),
            _f(m.get("jitter"), 2), _f(m.get("jitter_max"), 2),
            _f(m.get("hf_db"), 1), m.get("kbps", "?"), m.get("sr", "?")))
    print()
    print("帧抖动越低越好（对应「人物跳跃 / 镜头不连续」）")
    print("高频dB  越高人声越清（对应「对白不清楚」）")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "Seedance客观指标基线.json")
    io.open(out, "w", encoding="utf-8").write(
        json.dumps(rows, ensure_ascii=False, indent=1))
    print("已保存：%s" % os.path.basename(out))


def _f(x, nd=1):
    return ("%." + str(nd) + "f") % x if isinstance(x, (int, float)) else "-"


if __name__ == "__main__":
    main()
