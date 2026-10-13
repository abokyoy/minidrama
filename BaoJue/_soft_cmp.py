# -*- coding: utf-8 -*-
"""量化「对比度太大 / 没有柔和滤镜感」这两个主观感受。

主观感受拆成 3 个可测量的东西：
  1. 全局对比 p95-p05  —— 用户说的「对比度大」主要指这个
  2. 局部对比（8x8 块内标准差均值）—— 这才是人眼感到「硬」「硬邦邦」的东西
     全局对比大但局部柔 = 通透；全局和局部都大 = 又黑又硬
  3. 高光溢出比例（>=250 的像素）—— 硬白就是「没滤镜感」的主因
     胶片/滤镜的柔和高光会 roll off，不会顶到 255

OpenCV 5 坑：中文路径 imread/imwrite 静默返回 None → 先拷到纯 ASCII 目录。
"""
import os
import shutil
import subprocess
import sys

SRC = {
    "seedance": r"D:\output\Seedance\清洁女工与富客走廊冲突 (2).mp4",
    "lean_t01": r"D:\output\new\_lean_v1\xs01_t01_00001.mp4",
    "lean_t02": r"D:\output\new\_lean_v1\xs01_t02_00001.mp4",
    "legacy":  r"D:\output\new\ep01_t01_00001.mp4",
}
TMP = r"C:\Users\86134\.workbuddy\tmp\gradecmp"
N = 12  # 每支片抽帧数


def extract(path, tag):
    os.makedirs(TMP, exist_ok=True)
    for p in os.listdir(TMP):
        if p.startswith(tag + "_"):
            try:
                os.remove(os.path.join(TMP, p))
            except OSError:
                pass
    dst = os.path.join(TMP, tag + ".mp4")
    shutil.copy2(path, dst)          # 先拷成纯 ASCII 名
    pat = os.path.join(TMP, tag + "_f%03d.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", dst,
                    "-vf", "fps=%d" % N, pat], check=False)
    return sorted(os.path.join(TMP, f) for f in os.listdir(TMP)
                  if f.startswith(tag + "_") and f.endswith(".png"))


def stats(frames):
    import numpy as np
    import cv2
    acc = []
    for f in frames:
        im = cv2.imread(f, cv2.IMREAD_COLOR)
        if im is None:
            print("  !! 读不出", f)
            continue
        b, g, r = im[:, :, 0].astype("f4"), im[:, :, 1].astype("f4"), im[:, :, 2].astype("f4")
        y = 0.114 * b + 0.587 * g + 0.299 * r          # Rec.601 亮度
        hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
        sat = float(hsv[:, :, 1].mean())

        p = np.percentile(y, [1, 5, 25, 50, 75, 95, 99])
        clip_hi = float((y >= 250).mean() * 100)
        clip_lo = float((y <= 2).mean() * 100)

        # 局部对比：16x16 块的标准差均值（越大越硬）
        h, w = y.shape
        bh, bw = h // 16 * 16, w // 16 * 16
        blocks = y[:bh, :bw].reshape(bh // 16, 16, bw // 16, 16).transpose(0, 2, 1, 3)
        local_std = float(blocks.reshape(-1, 256).std(axis=1).mean())

        acc.append(dict(p=p, contrast=p[5] - p[1], dyn=p[6] - p[0],
                        local=local_std, hi=clip_hi, lo=clip_lo, sat=sat,
                        mean=float(y.mean())))
    n = len(acc)
    def avg(fn):
        return sum(fn(a) for a in acc) / n
    return dict(
        p01=avg(lambda a: a["p"][0]), p05=avg(lambda a: a["p"][1]),
        p25=avg(lambda a: a["p"][2]), p50=avg(lambda a: a["p"][3]),
        p75=avg(lambda a: a["p"][4]), p95=avg(lambda a: a["p"][5]),
        p99=avg(lambda a: a["p"][6]),
        contrast=avg(lambda a: a["contrast"]), dyn=avg(lambda a: a["dyn"]),
        local=avg(lambda a: a["local"]), hi=avg(lambda a: a["hi"]),
        lo=avg(lambda a: a["lo"]), sat=avg(lambda a: a["sat"]),
        mean=avg(lambda a: a["mean"]),
        n=n,
    )


def main():
    keys = sys.argv[1:] or list(SRC)
    res = {}
    for k in keys:
        p = SRC.get(k)
        if not p or not os.path.exists(p):
            print("跳过", k, p)
            continue
        fr = extract(p, k)
        if not fr:
            print("抽帧失败", k)
            continue
        res[k] = stats(fr)
        print("抽帧完成", k, len(fr))

    hdr = ("指标",) + tuple(res)
    print()
    print(" | ".join("%-12s" % h for h in hdr))
    for key, label, fmt in [
        ("p01", "黑位 p01", "%6.1f"), ("p05", "暗部 p05", "%6.1f"),
        ("p25", "p25", "%6.1f"), ("p50", "中位 p50", "%6.1f"),
        ("p75", "p75", "%6.1f"), ("p95", "亮部 p95", "%6.1f"),
        ("p99", "白位 p99", "%6.1f"),
        ("contrast", "全局对比", "%6.1f"), ("dyn", "动态范围", "%6.1f"),
        ("local", "★局部对比", "%6.2f"), ("hi", "★硬白占比%", "%6.2f"),
        ("lo", "死黑占比%", "%6.2f"), ("sat", "饱和度", "%6.2f"),
        ("mean", "平均亮度", "%6.1f"),
    ]:
        row = [label]
        for k in hdr[1:]:
            row.append(fmt % res[k][key])
        print(" | ".join("%-12s" % c for c in row))


if __name__ == "__main__":
    main()
