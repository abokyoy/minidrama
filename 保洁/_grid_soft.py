# -*- coding: utf-8 -*-
"""参考图调色参数的**网格搜索**：一次生成多档，量完再挑。

为什么需要这个（2026-10-04 21:25）：
  「压高光 → 肤色变艳」这件事，我手调了 5 轮（v1~v6）全都没同时满足两个条件：
    · 高光压下去（治「对比大 / 硬白」）
    · 肤色 S 不涨（防「脸发红发橙」）
  靠推理调不出来 —— 因为 V 和 S 是耦合的，改一边必然影响另一边。
  → 只能**穷举**：一次生成 N 档，每档量高光 + 肤色，挑那个两头都对的。

产出：<out>/ 下一组 png，终端打印一张对照表（按「高光误差 + 肤色误差」排序）。

用法：
  python _grid_soft.py assets/char_suxiaoman.png          # 只测不落地
  python _grid_soft.py assets/char_suxiaoman.png --apply  # 把最优档写进 assets_soft
"""
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
TMP = r"C:\Users\86134\.workbuddy\tmp\gridsoft"
ASCII = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")

# Seedance 4 支联合目标
T_P99, T_SAT, T_P95 = 223.6, 53.8, 195.0
T_LOCAL = 10.5


def safe(t):
    return "".join(c if c in ASCII else "_" for c in t)[:20] or "x"


def hi_roll(top_out):
    """高光 roll-off 曲线族：x 起点固定 0.925（肤色上限 236/255=0.925），
    top_out = 纯白 255 被压到多少（0-1）。"""
    return [(0.000, 0.000), (0.925, 0.925), (0.945, top_out + 0.03),
            (0.980, top_out + 0.015), (1.000, top_out)]


def stats(path, tag):
    import _skinchk
    im = _skinchk.read_any(path)
    if im is None:
        return None
    y = 0.114 * im[:, :, 0] + 0.587 * im[:, :, 1] + 0.299 * im[:, :, 2]
    q = np.percentile(y, [5, 50, 95, 99])
    h, w = y.shape
    bh, bw = h // 16 * 16, w // 16 * 16
    bl = y[:bh, :bw].reshape(bh // 16, 16, bw // 16, 16).transpose(0, 2, 1, 3)
    local = float(bl.reshape(-1, 256).std(axis=1).mean())
    sat = float(cv2.cvtColor(im, cv2.COLOR_BGR2HSV)[:, :, 1].mean())
    sk = _skinchk.skin_stats(path)
    return dict(p05=q[0], p50=q[1], p95=q[2], p99=q[3], local=local, sat=sat,
                skS=(sk["S"] if sk and sk["S"] > 0 else -1),
                skH=(sk["H"] if sk and sk["H"] > 0 else -1))


def main():
    src = sys.argv[1]
    apply_it = "--apply" in sys.argv
    os.makedirs(TMP, exist_ok=True)
    tag = safe(os.path.splitext(os.path.basename(src))[0])
    a = os.path.join(TMP, tag + "_in.png")
    shutil.copy2(src, a)

    base = stats(a, tag)
    print("原图: p95=%.1f p99=%.1f 饱和=%.1f 局部=%.2f 肤色S=%.1f"
          % (base["p95"], base["p99"], base["sat"], base["local"], base["skS"]))
    print("\n%-6s %-7s %-6s %7s %7s %7s %7s %7s  %s"
          % ("档", "压白", "饱和", "p95", "p99", "饱和", "局部", "肤色S", "综合误差"))

    rows = []
    for i, (top, sat_r) in enumerate([
            (0.845, 0.72), (0.845, 0.85), (0.845, 1.00),
            (0.870, 0.72), (0.870, 0.85), (0.870, 1.00),
            (0.890, 0.72), (0.890, 0.85), (0.890, 1.00),
            (0.925, 0.85), (0.925, 1.00)]):
        pts = hi_roll(top)
        cs = " ".join("%s/%.4f" % (x, y) for x, y in pts)
        need = base["local"] / T_LOCAL * 1.35
        sigma = max(0.0, min(0.9, (need - 1.0) * 9.0))
        vf = ("curves=all='" + cs + "',unsharp=5:5:0.40:5:5:0.0,eq=saturation=" +
              ("%.2f" % sat_r) + (",gblur=sigma=%.2f" % sigma if sigma >= 0.35 else ""))
        dst = os.path.join(TMP, "%s_g%02d.png" % (tag, i))
        r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", a,
                            "-vf", vf, "-frames:v", "1", dst],
                           capture_output=True, text=True, errors="replace")
        if r.returncode != 0 or not os.path.exists(dst):
            print("%-6d 生成失败" % i)
            continue
        s = stats(dst, tag)
        # 综合误差：高光压到位（p99→223.6）+ 肤色不涨（skS ≈ 原图）权重相当
        e_hi = abs(s["p99"] - T_P99) / 10.0
        e_sk = abs(s["skS"] - base["skS"]) / 8.0
        e_loc = abs(s["local"] - T_LOCAL) / 2.0
        err = e_hi + e_sk + e_loc
        rows.append((err, i, top, sat_r, s, dst))
        print("%-6d %-7.3f %-6.2f %7.1f %7.1f %7.1f %7.2f %7.1f  %.2f"
              % (i, top, sat_r, s["p95"], s["p99"], s["sat"], s["local"], s["skS"], err))

    if not rows:
        return
    rows.sort(key=lambda r: r[0])
    best = rows[0]
    print("\n★ 最优档 #%d  压白=%.3f 饱和=%.2f  误差=%.2f"
          % (best[1], best[2], best[3], best[0]))
    print("  p99 %.1f→%.1f（目标 %.1f）  肤色S %.1f→%.1f（原图）  局部 %.2f→%.2f（目标 %.2f）"
          % (base["p99"], best[4]["p99"], T_P99, base["skS"], best[4]["skS"],
             base["local"], best[4]["local"], T_LOCAL))

    if apply_it:
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_soft")
        os.makedirs(out_dir, exist_ok=True)
        shutil.copy2(best[5], os.path.join(out_dir, os.path.basename(src)))
        print("  已写入 " + out_dir)


if __name__ == "__main__":
    main()
