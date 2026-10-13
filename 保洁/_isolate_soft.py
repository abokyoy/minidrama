# -*- coding: utf-8 -*-
"""隔离实验：参考图调色链路里，到底哪一步让脸「发红」。

背景（2026-10-04 21:05）：`_softrefs.py` 产出的软调参考图肉眼「脸发红」，
但已排除两个嫌疑：
  · eq=saturation —— 已改成 0.78 反而更红？（反常）
  · colorbalance=rs  —— 已经删掉
剩下两个嫌疑，一次性隔离验证：
  ① curves 曲线本身（抬中间调 → 抬 V → 视觉更艳）
  ② gblur 柔化（把肤色边界和背景混在一起 → 糊红）

做法：同一条曲线，逐项开关滤镜，各存一张，逐张量肤色 + 出对比图。
肉眼猜已经骗了三轮（v1 猜饱和、v2 猜饱和、v3 猜 colorbalance，全错），必须隔离。

用法：python _isolate_soft.py assets/char_suxiaoman.png
"""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cv2
import numpy as np

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
TMP = r"C:\Users\86134\.workbuddy\tmp\isolate"


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else r"E:\LLM\try\minidrama\保洁\assets\char_suxiaoman.png"
    os.makedirs(TMP, exist_ok=True)
    a = os.path.join(TMP, "in.png")
    shutil.copy2(src, a)

    sys.path.insert(0, r"E:\LLM\try\minidrama\保洁")
    import _softrefs as SR
    import _softgrade as SG
    import _skinchk

    cur = SR.measure_still(a)
    # 复刻当前曲线（不带滤镜）
    tgt = {"p01": max(cur["p01"], 16.0), "p05": max(cur["p05"], 24.0),
           "p25": 78.0, "p50": 128.0, "p75": 160.0, "p95": 170.0, "p99": 190.0}
    fake = dict(cur); fake.update(tgt)
    cs, _ = SG.solve_curve(fake, it=0)
    need = cur.get("local", 10.0) / SR.T_LOCAL * 1.45
    sigma = max(0.0, min(0.9, (need - 1.0) * 9.0))

    cases = [
        ("0_原图", None),
        ("1_仅曲线", "curves=all='%s'" % cs),
        ("2_曲线+降饱和", "curves=all='%s',eq=saturation=0.78" % cs),
        ("3_曲线+柔化", "curves=all='%s',gblur=sigma=%.2f" % (cs, sigma)),
        ("4_全上(当前)", "curves=all='%s',gblur=sigma=%.2f,eq=saturation=0.78" % (cs, sigma)),
        ("5_仅降饱和", "eq=saturation=0.78"),
        ("6_仅柔化", "gblur=sigma=%.2f" % sigma),
    ]
    print("sigma = %.2f" % sigma)
    print("%-14s %8s %8s  %s" % ("变体", "平均H", "平均S", "判定"))
    print("-" * 52)
    ims = []
    h = 620
    for name, vf in cases:
        dst = os.path.join(TMP, "c_%s.png" % name.split("_")[0])
        if vf is None:
            shutil.copy2(a, dst)
        else:
            r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", a,
                                "-vf", vf, "-frames:v", "1", dst],
                               capture_output=True, text=True, errors="replace")
            if r.returncode != 0 or not os.path.exists(dst):
                print("%-14s 生成失败" % name)
                continue
        s = _skinchk.skin_stats(dst)
        base = _skinchk.skin_stats(a)
        if s and base:
            dS = s["S"] - base["S"]
            dH = s["H"] - base["H"]
            print("%-14s %8.1f %8.1f  ΔH%+5.1f ΔS%+5.1f  %s"
                  % (name, s["H"], s["S"], dH, dS, _skinchk.verdict(s["H"])))
        im = cv2.imread(dst, cv2.IMREAD_COLOR)
        if im is not None:
            w = int(im.shape[1] * h / im.shape[0])
            ims.append(cv2.resize(im, (w, h)))

    if len(ims) >= 2:
        sep = np.full((h, 8, 3), 40, np.uint8)
        rows = []
        for i in range(0, len(ims), 3):
            chunk = ims[i:i + 3]
            while len(chunk) < 3:
                chunk.append(np.zeros_like(ims[0]))
            r1 = np.hstack([chunk[0], sep, chunk[1], sep, chunk[2]])
            rows.append(r1)
        wmax = max(r.shape[1] for r in rows)
        rows = [np.pad(r, ((0, 0), (0, wmax - r.shape[1]), (0, 0))) for r in rows]
        vsep = np.full((8, wmax, 3), 40, np.uint8)
        grid = []
        for r in rows:
            grid.append(r)
            grid.append(vsep)
        cv2.imwrite(os.path.join(TMP, "grid.png"), np.vstack(grid[:-1]))
        print("\n对比图: " + os.path.join(TMP, "grid.png"))
        print("顺序: 0原图 1仅曲线 2曲线+降饱和 | 3曲线+柔化 4全上 5仅降饱和 | 6仅柔化")


if __name__ == "__main__":
    main()
