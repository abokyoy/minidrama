# -*- coding: utf-8 -*-
"""画质对比：本地成片 vs Seedance —— 量化「蒙了一层灰」。

用户反馈：「本地做的视频颜色总是像蒙了一层灰，而 Seedance 有种高清清亮的感觉」。

要查的三个量化指标（都能直接对应观感）：
  1. **黑位抬高**（lifted blacks）：p01/p05 越高 = 蒙灰越重。胶片感"雾"就是黑不下去。
  2. **对比度**：p95 - p05。差值小 = 发灰发雾；差值大 = 通透清晰。
  3. **动态范围利用率**：画面用到的最暗到最亮占了整个 0-255 的多少比例。
     Seedance 通常又黑又亮（用满），低对比但**分布拉开**；
     本地如果 p05=46 p95=206，看起来"灰"其实是**整段被抬到中间调**。

另外查 **色相分布**（有没有整体偏色/偏青）—— 「蒙灰」也可能是色彩被压成同一种。

用法：python _grade_cmp.py
"""
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"

# ⭐ 关键：同时量「原片」和「调色后」，直接看 _grade.py 到底做了什么
RAW = [   # _grade.py 处理前的原始输出
    r"D:\output\new\_raw\xs01_t01_00001.mp4",
    r"D:\output\new\_raw\xs01_t02_00001.mp4",
]
LOCAL = [ # _grade.py 处理后（= 交付件）
    r"D:\output\new\xs01_t01_00001.mp4",
    r"D:\output\new\xs01_t02_00001.mp4",
    r"D:\output\new\xs01_t03_00001.mp4",
]
SEED = [
    r"D:\output\Seedance\清洁女工与富客走廊冲突 (1).mp4",
    r"D:\output\Seedance\清洁女工与富客走廊冲突 (2).mp4",
    r"D:\output\Seedance\清洁女工与富客走廊冲突 (3).mp4",
]


def stats(path, label):
    """用 ffmpeg 抽 12 帧，各帧算 YAVG + 直方图分位。"""
    if not os.path.exists(path):
        print("缺失:", path)
        return None
    tmp = r"E:\LLM\try\minidrama\_cmp_tmp"
    os.makedirs(tmp, exist_ok=True)
    pf = os.path.join(tmp, "g%03d.png")
    for f in os.listdir(tmp):
        try:
            os.remove(os.path.join(tmp, f))
        except Exception:
            pass
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", path,
                    "-vf", "fps=2/5,scale=480:-1", pf],
                   capture_output=True, timeout=600)
    imgs = sorted(f for f in os.listdir(tmp) if f.endswith(".png"))
    if not imgs:
        print("抽帧失败:", path)
        return None

    vals = []
    for f in imgs:
        p = os.path.join(tmp, f)
        r = subprocess.run([FFMPEG, "-hide_banner", "-i", p,
                            "-vf", "signalstats,metadata=print:file=-", "-f", "null", "-"],
                           capture_output=True, timeout=180)
        txt = (r.stderr or b"").decode("utf-8", "replace")
        m = re.findall(r"lavfi\.signalstats\.YAVG=([\d.]+)", txt)
        if m:
            vals.append(float(m[0]))
    if not vals:
        return None
    vals.sort()
    n = len(vals)
    return {
        "label": label,
        "n": n,
        "ymin": vals[0],
        "ymed": vals[n // 2],
        "ymax": vals[-1],
    }


def pct_of_frame(png):
    """单帧的亮度分位（用 PIL 直方图，能拿到 p01/p05/p95）。"""
    try:
        from PIL import Image
        import numpy as np
        im = Image.open(png).convert("L")
        a = np.asarray(im)
        return np.percentile(a, [1, 5, 25, 50, 75, 95, 99])
    except Exception:
        return None


def deep(path, label):
    if not os.path.exists(path):
        return None
    tmp = r"E:\LLM\try\minidrama\_cmp_tmp2"
    os.makedirs(tmp, exist_ok=True)
    for f in os.listdir(tmp):
        try:
            os.remove(os.path.join(tmp, f))
        except Exception:
            pass
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", path,
                    "-vf", "fps=2/5,scale=480:-1", os.path.join(tmp, "q%03d.png")],
                   capture_output=True, timeout=600)
    imgs = sorted(os.listdir(tmp))
    allp = []
    for f in imgs:
        p = pct_of_frame(os.path.join(tmp, f))
        if p is not None:
            allp.append(p)
    if not allp:
        return None
    import numpy as np
    a = np.array(allp)          # (帧数, 7)
    m = a.mean(axis=0)
    return {
        "label": label,
        "p01": m[0], "p05": m[1], "p25": m[2],
        "p50": m[3], "p75": m[4], "p95": m[5], "p99": m[6],
        "spread": m[6] - m[0],
        "contrast": m[5] - m[1],
    }


def show(d):
    if not d:
        return
    print("── %s" % d["label"])
    print("   p01=%5.1f  p05=%5.1f  p25=%5.1f  p50=%5.1f  p75=%5.1f  p95=%5.1f  p99=%5.1f"
          % (d["p01"], d["p05"], d["p25"], d["p50"], d["p75"], d["p95"], d["p99"]))
    print("   全动态范围 p99-p01 = %5.1f / 255  (用满 = 通透, 偏小 = 蒙灰)"
          % d["spread"])
    print("   局部对比 p95-p05   = %5.1f / 255  (大 = 层次清楚)" % d["contrast"])


def main():
    print("=" * 72)
    print("① 本地原片（H3 直接输出，_grade.py 之前）")
    print("=" * 72)
    R = [deep(p, os.path.basename(p)) for p in RAW]
    for d in R:
        show(d)
    print()
    print("=" * 72)
    print("② 本地成片（经 _grade.py 调色，= 交付件）")
    print("=" * 72)
    L = [deep(p, os.path.basename(p)) for p in LOCAL]
    for d in L:
        show(d)
    print()
    print("=" * 72)
    print("③ Seedance（无后期，原生）")
    print("=" * 72)
    S = [deep(p, os.path.basename(p)) for p in SEED]
    for d in S:
        show(d)

    print()
    print("=" * 72)
    print("结论")
    print("=" * 72)
    Rv = [d for d in R if d]
    Lv = [d for d in L if d]
    Sv = [d for d in S if d]
    if not (Rv and Lv and Sv):
        print("数据不足：原片 %d / 成片 %d / Seedance %d" % (len(Rv), len(Lv), len(Sv)))
        return

    def avg(ds, k):
        return sum(d[k] for d in ds) / len(ds)

    print("                     原片      调色后    Seedance")
    for k, name in [("p01", "黑位 p01  "), ("p05", "      p05  "), ("p50", "中位 p50  "),
                    ("p95", "亮部 p95  "), ("p99", "白位 p99  "),
                    ("spread", "动态范围  "), ("contrast", "对比度    ")]:
        print("  %s  %8.1f   %8.1f   %8.1f"
              % (name, avg(Rv, k), avg(Lv, k), avg(Sv, k)))
    print()
    d1 = avg(Lv, "p01") - avg(Rv, "p01")
    d2 = avg(Lv, "contrast") - avg(Rv, "contrast")
    d3 = avg(Lv, "spread") - avg(Rv, "spread")
    print("调色造成的净变化：黑位 %+.1f，对比度 %+.1f，动态范围 %+.1f" % (d1, d2, d3))
    gap = avg(Lv, "contrast") - avg(Sv, "contrast")
    print("与 Seedance 的对比度差距：%+.1f （负数=我们更灰）" % gap)


if __name__ == "__main__":
    main()
