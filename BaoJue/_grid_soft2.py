# -*- coding: utf-8 -*-
"""网格搜索：找「压中间调 + 抬暗部」的参考图调色参数。

═══ 为什么这轮和上一轮不同 ═══════════════════════════════════════════
上一轮（`_grid_soft.py`）只搜了「压高光」，结果：
  参考图 p50 仍然是 207~228（目标 117.8）—— **中间调压根没动**
  → 输出 p50=83.9（目标 117.8），画面偏暗、对比大

关键认识（这一轮才想明白）：
  · **高调 ≠ 柔和**。压高光只治"硬白"，不治"对比大"。
  · 「柔和 / 通透 / 高清」的真正含义是**反差低**：
      中间调往下压（别冲到 200+）+ 暗部往上抬（别压到 0）
    → 直方图被**压缩到中间**，两端都不顶死 → 视觉上就是柔和通透。
  · 这与「蒙灰」是两件事：
      蒙灰 = 抬**黑位**（p01 从 13 抬到 50）→ 灰底、失去黑
      柔和 = **压中间调 + 抬 p05 到 28** → 黑还在，但暗部有细节
    区别在 p01 要**保持低**（≤14），只抬 p05。

═══ 本轮搜索维度 ═══════════════════════════════════════════════════
  mid  : 中间映射点（0.50 → mid），压低中间调
  lift : 暗部抬升（0.0 → lift，0.10 对应 p05≈26）
  top  : 纯白压到多少
  sat  : 饱和倍数

评价误差 = 高光(p99) + 肤色S + 局部对比 + **中间调 p50** 四项加权
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
TMP = r"C:\Users\86134\.workbuddy\tmp\gridsoft2"
ASCII = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")

T_P50, T_P95, T_P99, T_SAT, T_LOCAL, T_P05 = 117.8, 195.0, 223.6, 53.8, 10.5, 28.5


def safe(t):
    return "".join(c if c in ASCII else "_" for c in t)[:20] or "x"


def curve(mid, lift, top):
    """8 点曲线。关键：lift 只抬最暗端，mid 压中间，top 压纯白。
    肤色安全区（<0.925）在本曲线里**会跟着 mid 一起降** —— 这是本轮
    与上一轮的根本区别：为了让画面柔和，**必须**让人脸也暗一点。
    肤色安全性改由「不升饱和」+ 网格搜索的肤色误差项来保证。
    """
    return [
        (0.000, 0.000),
        (0.047, lift),        # 12/255  → 抬到 lift*255（≈26）
        (0.157, lift + 0.045),
        (0.350, mid * 0.86),  # 89/255
        (0.500, mid),         # ★中间调核心
        (0.700, mid + (0.93 - mid) * 0.42),
        (0.925, mid + (0.93 - mid) * 0.80),
        (0.960, top + 0.02),
        (1.000, top),
    ]


def stats(path):
    import _skinchk
    im = _skinchk.read_any(path)
    if im is None:
        return None
    y = 0.114 * im[:, :, 0] + 0.587 * im[:, :, 1] + 0.299 * im[:, :, 2]
    q = np.percentile(y, [1, 5, 50, 95, 99])
    h, w = y.shape
    bh, bw = h // 16 * 16, w // 16 * 16
    bl = y[:bh, :bw].reshape(bh // 16, 16, bw // 16, 16).transpose(0, 2, 1, 3)
    local = float(bl.reshape(-1, 256).std(axis=1).mean())
    sat = float(cv2.cvtColor(im, cv2.COLOR_BGR2HSV)[:, :, 1].mean())
    sk = _skinchk.skin_stats(path)
    return dict(p01=q[0], p05=q[1], p50=q[2], p95=q[3], p99=q[4], local=local,
                sat=sat, skS=(sk["S"] if sk and sk["S"] > 0 else -1))


def main():
    src = sys.argv[1]
    apply_it = "--apply" in sys.argv
    os.makedirs(TMP, exist_ok=True)
    tag = safe(os.path.splitext(os.path.basename(src))[0])
    a = os.path.join(TMP, tag + "_in.png")
    shutil.copy2(src, a)
    base = stats(a)
    print("原图 p05=%.1f p50=%.1f p95=%.1f p99=%.1f 饱和=%.1f 局部=%.2f 肤色S=%.1f"
          % (base["p05"], base["p50"], base["p95"], base["p99"], base["sat"],
             base["local"], base["skS"]))
    print("\n%-4s %-6s %-6s %-6s %-5s | %6s %6s %6s %6s %6s %6s  %s"
          % ("档", "mid", "lift", "top", "sat", "p05", "p50", "p95", "p99", "饱和", "局部", "肤色S"))
    print("-" * 96)

    rows = []
    combos = []
    for mid in (0.50, 0.56, 0.62):
        for lift in (0.06, 0.10):
            for sat in (0.72, 0.85):
                combos.append((mid, lift, 0.885, sat))

    for i, (mid, lift, top, sat) in enumerate(combos):
        pts = curve(mid, lift, top)
        cs = " ".join("%s/%.4f" % (x, y) for x, y in pts)
        need = base["local"] / T_LOCAL * 1.3
        sigma = max(0.0, min(0.9, (need - 1.0) * 9.0))
        vf = ("curves=all='" + cs + "',unsharp=5:5:0.35:5:5:0.0,eq=saturation=" +
              ("%.2f" % sat) + (",gblur=sigma=%.2f" % sigma if sigma >= 0.35 else ""))
        dst = os.path.join(TMP, "%s_g%02d.png" % (tag, i))
        r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", a, "-vf", vf,
                            "-frames:v", "1", dst], capture_output=True, text=True,
                           errors="replace")
        if r.returncode != 0 or not os.path.exists(dst):
            print("%-4d 生成失败" % i)
            continue
        s = stats(dst)
        # 误差：p50 是本轮主角（权重大），p99/肤色S/局部 各一份
        e = (abs(s["p50"] - T_P50) / 9.0 + abs(s["p99"] - T_P99) / 10.0
             + abs(s["skS"] - base["skS"]) / 10.0 + abs(s["local"] - T_LOCAL) / 2.0
             + abs(s["p05"] - T_P05) / 6.0)
        rows.append((e, i, mid, lift, top, sat, s, dst))
        print("%-4d %-6.2f %-6.2f %-6.3f %-5.2f | %6.1f %6.1f %6.1f %6.1f %6.1f %6.2f  %.1f"
              % (i, mid, lift, top, sat, s["p05"], s["p50"], s["p95"], s["p99"],
                 s["sat"], s["local"], s["skS"]))

    if not rows:
        return
    rows.sort(key=lambda r: r[0])
    b = rows[0]
    print("\n目标                | %6.1f %6.1f %6.1f %6.1f %6.1f %6.2f  (p05/p50/p95/p99/饱和/局部)"
          % (T_P05, T_P50, T_P95, T_P99, T_SAT, T_LOCAL))
    print("\n★ 最优 #%d  mid=%.2f lift=%.2f top=%.3f sat=%.2f  误差=%.2f"
          % (b[1], b[2], b[3], b[4], b[5], b[0]))
    print("  p50 %.1f→%.1f（目标 %.1f）  肤色S %.1f→%.1f  局部 %.2f→%.2f  p05 %.1f→%.1f"
          % (base["p50"], b[6]["p50"], T_P50, base["skS"], b[6]["skS"],
             base["local"], b[6]["local"], base["p05"], b[6]["p05"]))

    if apply_it:
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_soft")
        os.makedirs(out_dir, exist_ok=True)
        shutil.copy2(b[7], os.path.join(out_dir, os.path.basename(src)))
        print("  已写入 " + out_dir)


if __name__ == "__main__":
    main()
