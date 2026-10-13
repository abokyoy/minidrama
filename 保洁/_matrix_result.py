# -*- coding: utf-8 -*-
"""矩阵测试结果对比：用客观指标评画质，不靠肉眼猜。

指标定义（都用 ffmpeg/ffprobe，自动化、可复现）：
  ① 锐度     ：拉普拉斯卷积后的方差 → 越高越锐利（能反映 int8 VAE 的糊）
  ② 亮度     ：YAVG 平均亮度（过低=发灰发暗）
  ③ 对比度   ：YAVG 与 YDIF（动态范围）
  ④ 帧间抖动 ：相邻帧差分的均值 → **越低越好**。
     这一项直接对应用户说的「镜头不连续、人物跳跃」——
     跳变会让相邻帧差异暴涨。
  ⑤ 音频     ：采样率 / 码率，以及响度（LUFS）与人声清晰度相关的
               高频能量占比（4–8kHz），这是「对白不清」的量化指标。

用法：
  python _matrix_result.py            # 列出已完成
  python _matrix_result.py --analyze  # 跑完整指标分析
"""
import glob
import io
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = "D:/output"
CMP = os.path.join(BASE, "..", "_cmp")
FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"E:\Program Files\ffmpeg\bin\ffprobe.exe"

GROUPS = {
    # ── v3：依据 SLA 官方 tooltip 的关键项（当前优先级最高）──
    # 注意键是**组号**（_requeue.py 提交时把 filename_prefix 改成了 "MT3_<组号>"），
    # 不是 tag。第一版按 tag 写（MT3_6step）→ 一片都扫不到，误以为"没出片"。
    "MT3_G": "G 6步 ★官方推荐",
    "MT3_H": "H 末步全注意力",
    "MT3_I": "I 参考保护Light",
    "MT3_J": "J 尾部修正",
    "MT3_L": "L 组合6步",
    "MT3_K": "K 运动稳定",
    "MT3_A": "A 基线",
    # ── v2：分辨率/采样器维度 ──
    "MT2_base": "A2 基线（现行设置）",
    "MT2_refmax": "B2 身份锚定 max",
    "MT2_unipc": "C2 采样器 uni_pc",
    "MT2_sgmuni": "D2 调度器 sgm_uniform",
    "MT2_8step_refmax": "E2 8步+max",
    "MT2_combo": "F2 组合",
    "MT_base4step": "A' 旧基线",
    "MT_8step": "B' 旧8步",
    "MT_maxref": "C' 旧max",
    "MT_1mp": "D' 旧1MP",
    "MT_8step_max_1mp": "E' 旧组合",
    "TEST_upg_8step_max": "T 单测 8步+max",
    "TEST_8step": "T 单测 8步",
    "TEST_8step_max": "T 单测 8步+max",
}
# 参考基线：主线的真实成片
LINE_CLIPS = {
    "4步 t62": os.path.join(OUT, "ep01_t62_00001-audio.mp4"),
    "4步 t67": os.path.join(OUT, "ep01_t67_00001-audio.mp4"),
}


def clips():
    """扫出所有已完成的测试片（体积 >200KB 视为完成）。"""
    found = {}
    if not os.path.isdir(OUT):
        return found
    for f in os.listdir(OUT):
        if not f.endswith(".mp4"):
            continue
        stem = re.sub(r"_\d{5}(-audio)?\.mp4$", "", f)
        p = os.path.join(OUT, f)
        if os.path.getsize(p) > 200000 and stem in GROUPS:
            # 优先带音轨的
            if stem not in found or "-audio" in f:
                found[stem] = p
    return found


def probe(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries",
                        "stream=codec_type,width,height,nb_frames,sample_rate,channels,bit_rate",
                        "-show_entries", "format=duration,bit_rate",
                        "-of", "json", p], capture_output=True, text=True, timeout=40)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def metrics(p, tag):
    """返回 {锐度, 亮度, 对比, 帧抖动, 高频占比}"""
    m = {}
    # ⚠️ 这里必须用 `-loglevel info`，**不能用 `-v error`**。
    # `metadata=print` / `astats` 把结果打在 **info 级**，而 `-v error` 只显示
    # error 及以上 → 之前所有 YAVG/YDIF/帧抖动/高频 指标全是 None，
    # 而表里那一列 "-" 我**误当成"正常但没测到"**，实际是采集失败。
    # 教训：看到指标全是空，先怀疑采集端，不要直接下"画质没差异"的结论。
    LVL = ["-hide_banner", "-loglevel", "info"]
    # 抽 6 帧到 gray，算拉普拉斯方差当锐度
    os.makedirs(CMP, exist_ok=True)
    one = os.path.join(CMP, "m_%s.png" % tag)
    r = subprocess.run([FFMPEG, "-v", "error", "-ss", "4", "-i", p, "-frames:v", "1",
                        "-vf", "format=gray", "-f", "image2", "-y", one],
                       capture_output=True, timeout=90)
    if os.path.exists(one):
        r2 = subprocess.run([FFMPEG] + LVL + ["-i", one,
                             "-vf", "convolution=0:1:1:1:0:-1:1:0:-1:0:1:0:-1:1:0:0,"
                                    "signalstats,metadata=print:key=lavfi.signalstats.YAVG",
                             "-f", "null", "-"], capture_output=True, text=True,
                            errors="replace", timeout=60)
        m["lap"] = _grab(r2.stderr, "YAVG")   # 卷积后均值 = 锐度代理
        # 亮度/动态要**未经卷积**的原图值，另跑一次（卷积会改写像素）
        r3 = subprocess.run([FFMPEG] + LVL + ["-i", one, "-vf",
                             "signalstats,metadata=print:key=lavfi.signalstats.YAVG",
                             "-f", "null", "-"], capture_output=True, text=True,
                            errors="replace", timeout=60)
        m["bright"] = _grab(r3.stderr, "YAVG")
        r3b = subprocess.run([FFMPEG] + LVL + ["-i", one, "-vf",
                             "signalstats,metadata=print:key=lavfi.signalstats.YDIF",
                             "-f", "null", "-"], capture_output=True, text=True,
                            errors="replace", timeout=60)
        m["range"] = _grab(r3b.stderr, "YDIF")
    # 帧间抖动：相邻帧差分均值（越高=越跳）
    r4 = subprocess.run([FFMPEG] + LVL + ["-i", p, "-vf",
                         "tblend=all_mode=difference,signalstats,"
                         "metadata=print:key=lavfi.signalstats.YAVG",
                         "-f", "null", "-"], capture_output=True, text=True,
                        errors="replace", timeout=240)
    vals = [float(x) for x in re.findall(r"YAVG=([\d.]+)", r4.stderr or "")]
    if vals:
        m["jitter"] = sum(vals) / len(vals)
        m["jitter_max"] = max(vals)
    # 高频能量占比 4–8kHz（人声清晰度相关）
    r5 = subprocess.run([FFMPEG] + LVL + ["-i", p, "-t", "8",
                         "-af", "highpass=f=4000,astats=metadata=1:reset=0",
                         "-f", "null", "-"], capture_output=True, text=True,
                        errors="replace", timeout=150)
    mm = re.search(r"RMS level dB:\s*(-?[\d.]+|-inf)", r5.stderr or "")
    if mm and mm.group(1) != "-inf":
        m["hf_db"] = float(mm.group(1))
    pr = probe(p)
    a = [s for s in pr.get("streams", []) if s.get("codec_type") == "audio"]
    v = [s for s in pr.get("streams", []) if s.get("codec_type") == "video"]
    if a:
        m["sr"] = a[0].get("sample_rate")
    if v:
        m["res"] = "%sx%s" % (v[0].get("width"), v[0].get("height"))
    m["dur"] = float(pr.get("format", {}).get("duration", 0))
    m["kbps"] = int(pr.get("format", {}).get("bit_rate", 0)) // 1000
    return m


def _grab(stderr, key):
    mm = re.search(key + r"=([\d.]+)", stderr or "")
    return float(mm.group(1)) if mm else None


def list_done():
    f = clips()
    print("=" * 76)
    print(" 已完成的测试片")
    print("=" * 76)
    for stem, p in sorted(f.items()):
        print("  %-22s %s" % (GROUPS.get(stem, stem), os.path.basename(p)))
    if not f:
        print("  （还没有。等 ComfyUI 跑完队列）")
    print()
    print("主线真实成片（对照基线）：")
    for k, p in LINE_CLIPS.items():
        if os.path.exists(p):
            print("  %-22s %s" % (k, os.path.basename(p)))
    return f


def analyze():
    f = clips()
    rows = []
    for stem, p in sorted(f.items()):
        tag = re.sub(r"[^A-Za-z0-9]", "_", stem)
        m = metrics(p, tag)
        m["name"] = GROUPS.get(stem, stem)
        m["file"] = os.path.basename(p)
        rows.append(m)
    for k, p in LINE_CLIPS.items():
        if os.path.exists(p):
            m = metrics(p, re.sub(r"[^A-Za-z0-9]", "_", k))
            m["name"] = "★主线 " + k
            m["file"] = os.path.basename(p)
            rows.append(m)

    print("=" * 96)
    print(" 客观指标对比（★ = 主线现行成片，作基线）")
    print("=" * 96)
    print(" %-22s %-10s %6s %6s %7s %7s %6s %7s" %
          ("组", "分辨率", "亮度", "动态", "帧抖动", "抖动峰", "高频dB", "音频kbps"))
    print(" " + "-" * 92)
    for m in sorted(rows, key=lambda x: (x["name"].startswith("★") is False, x["name"])):
        print(" %-22s %-10s %6s %6s %7s %7s %6s %7s" % (
            m["name"][:22], m.get("res", "?"),
            _f(m.get("bright")), _f(m.get("range")),
            _f(m.get("jitter"), 2), _f(m.get("jitter_max"), 2),
            _f(m.get("hf_db"), 1), m.get("kbps", "?")))
    print()
    print("怎么看：")
    print("  帧抖动/抖动峰  越低越好 ← 直接对应「人物跳跃、镜头不连续」")
    print("  动态范围(YDIF)  越高越好 ← 对应「画面有质感、不灰」")
    print("  亮度(YAVG)     90~160 最佳")
    print("  高频dB         越高人声越清（对应「对白不清楚」）")


def _f(x, nd=1):
    return ("%." + str(nd) + "f") % x if isinstance(x, (int, float)) else "-"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--analyze" in sys.argv:
        analyze()
    else:
        list_done()
