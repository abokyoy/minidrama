# -*- coding: utf-8 -*-
"""网格搜索：把「太暗」的新人物参考图调到 Seedance 的明度分布。

═══ 背景 ═══════════════════════════════════════════════════════════
2026-10-04 22:15 用 ImageGen 重做了 3 张人物设定图（22:16），结果：
  · **人物形象对**（苏小满/钱经理/小唐 都符合设定）✔
  · **肤色健康**（H=15~20，全部"健康肤色"）✔
  · **但整体太暗**：p50 只有 31~50，Seedance 目标是 118；饱和 66~72 偏高
  → 不需要重新生成（形象是对的），**只要把明度调对**。
    这一步就是调色，和场景图那条路一样用网格搜索找参数。

═══ 为什么这次必然成功 ═════════════════════════════════════════════
场景图那轮一次命中，是因为目标明确（p50 118）。
人物图是**同一个目标的另一个样本**，参数可以复用：
  · 提亮（S 曲线抬中间调）—— 上一轮 `_grid_soft2.py` 已证明能把 p50 从 207 压下，
    这轮是反过来从 40 抬上，方向相反、同样可控
  · 降饱和 0.72~0.78 —— 唯一安全的操作（不碰 V，不影响肤色）
  · 柔化 —— 局部对比 6.7~11 已接近目标，只需微调

═══ 关键约束 ═══════════════════════════════════════════════════════
**不能抬得太狠**。ImageGen 这批图的 p50 只有 31，要抬到 118 是 3.8 倍 ——
按之前总结的机理「抬像素值会让肤色 S 上升 → 脸发红」，
所以必须把**肤色 S 变化量**作为一项硬指标放进误差函数。

用法：
  python _grid_bright.py assets_new/x.png [更多图…] --apply
"""
import glob
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
TMP = r"C:\Users\86134\.workbuddy\tmp\gridbright"
ASCII = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")

T_P05, T_P25, T_P50 = 28.5, 71.8, 117.8
T_P75, T_P95, T_P99 = 148.0, 195.0, 223.6
T_SAT, T_LOCAL = 53.8, 10.5


def safe(t):
    return "".join(c if c in ASCII else "_" for c in t)[:20] or "x"


def curve(mid, lift, top):
    """三点式：黑 →(lift) 暗部 →(mid) 中间调 →(top) 高光。
    保留 S 形，避免线性抬升导致发灰。

    ⚠️ 2026-10-04 22:20 修正：
      第一版用 `mid = 0.5*gain`，gain 1.8/2.2/2.6/3.0 算出来是 0.90/1.10/1.30/1.50
      —— 全部 ≥0.9 或超过 1.0，被 ffmpeg 钳位后**四档结果完全一样**
      （实测 p50 都是 60~64，误差 38~41，看起来像"调不动"）。
      → 改为**直接把 mid 当搜索维度**，范围 0.42~0.62（对应 p50 约 107~158）。
    """
    return [
        (0.000, 0.000),
        (0.080, lift),
        (0.250, lift + (mid - lift) * 0.62),
        (0.500, mid),
        (0.750, mid + (top - mid) * 0.70),
        (0.925, mid + (top - mid) * 0.93),
        (1.000, top),
    ]


def stats(path):
    import _skinchk
    im = _skinchk.read_any(path)
    if im is None:
        return None
    y = 0.114 * im[:, :, 0] + 0.587 * im[:, :, 1] + 0.299 * im[:, :, 2]
    q = np.percentile(y, [5, 25, 50, 75, 95, 99])
    h, w = y.shape
    bh, bw = h // 16 * 16, w // 16 * 16
    bl = y[:bh, :bw].reshape(bh // 16, 16, bw // 16, 16).transpose(0, 2, 1, 3)
    local = float(bl.reshape(-1, 256).std(axis=1).mean())
    sat = float(cv2.cvtColor(im, cv2.COLOR_BGR2HSV)[:, :, 1].mean())
    sk = _skinchk.skin_stats(path)
    return dict(p05=q[0], p25=q[1], p50=q[2], p75=q[3], p95=q[4], p99=q[5],
                local=local, sat=sat,
                skS=(sk["S"] if sk and sk["S"] > 0 else -1),
                skH=(sk["H"] if sk and sk["H"] > 0 else -1))


def search(src, apply_it=False, out_name=None):
    os.makedirs(TMP, exist_ok=True)
    tag = safe(os.path.splitext(os.path.basename(src))[0])
    a = os.path.join(TMP, tag + "_in.png")
    shutil.copy2(src, a)
    base = stats(a)
    print("\n══ %s" % os.path.basename(src))
    print("   原图 p05=%.1f p25=%.1f p50=%.1f p95=%.1f p99=%.1f 饱和=%.1f 局部=%.2f 肤色S=%.0f"
          % (base["p05"], base["p25"], base["p50"], base["p95"], base["p99"],
             base["sat"], base["local"], base["skS"]))

    combos = []
    for mid in (0.42, 0.48, 0.54, 0.60):
        for lift in (0.06, 0.11):
            for sat in (0.55, 0.65, 0.75):
                combos.append((mid, lift, sat))

    best = None
    for i, (gain, lift, sat) in enumerate(combos):
        pts = curve(gain, lift, 0.90)
        cs = " ".join("%s/%.4f" % (x, y) for x, y in pts)
        need = base["local"] / T_LOCAL
        sigma = max(0.0, min(1.0, (need - 1.0) * 6.0)) if need > 1 else 0.0
        vf = ("curves=all='" + cs + "',unsharp=5:5:0.35:5:5:0.0,eq=saturation=" +
              ("%.2f" % sat) + (",gblur=sigma=%.2f" % sigma if sigma >= 0.35 else ""))
        dst = os.path.join(TMP, "%s_g%02d.png" % (tag, i))
        r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", a, "-vf", vf,
                            "-frames:v", "1", dst], capture_output=True, text=True,
                           errors="replace")
        if r.returncode != 0 or not os.path.exists(dst):
            continue
        s = stats(dst)
        # 误差：明度三项为主，肤色 S/H 涨幅**权重加倍**
        # （机理已知：抬 V 会让 HSL 的 S 相对变高 → 脸发红，所以要压着降饱和）
        e = (abs(s["p50"] - T_P50) / 8.0
             + abs(s["p25"] - T_P25) / 9.0
             + abs(s["p05"] - T_P05) / 7.0
             + abs(s["p99"] - T_P99) / 9.0
             + abs(s["sat"] - T_SAT) / 5.0
             + abs(s["skS"] - base["skS"]) / 5.0
             + abs(s["skH"] - base["skH"]) / 3.0
             + abs(s["local"] - T_LOCAL) / 2.0)
        if best is None or e < best[0]:
            best = (e, i, gain, lift, sat, s, dst)
        print("   mid=%.2f lift=%.2f sat=%.2f → p05=%5.1f p25=%5.1f p50=%5.1f p99=%5.1f "
              "饱和=%5.1f 肤色S=%3.0f H=%2.0f 误差=%.2f"
              % (gain, lift, sat, s["p05"], s["p25"], s["p50"], s["p99"],
                 s["sat"], s["skS"], s["skH"], e))

    if not best:
        print("   全部失败")
        return
    b = best
    print("   ★最优 gain=%.1f lift=%.2f sat=%.2f 误差=%.2f"
          % (b[2], b[3], b[4], b[0]))
    print("   ★  p50 %.1f→%.1f(目标%.1f)  p25 %.1f→%.1f(%.1f)  饱和 %.1f→%.1f(%.1f)  "
          "肤色S %.0f→%.0f  H %.0f→%.0f"
          % (base["p50"], b[5]["p50"], T_P50, base["p25"], b[5]["p25"], T_P25,
             base["sat"], b[5]["sat"], T_SAT, base["skS"], b[5]["skS"],
             base["skH"], b[5]["skH"]))

    if apply_it:
        d = os.path.join(TMP, "best_" + (out_name or os.path.basename(src)))
        shutil.copy2(b[6], d)
        print("   → " + d)
    return b


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply_it = "--apply" in sys.argv
    if "--dir" in sys.argv:
        d = sys.argv[sys.argv.index("--dir") + 1]
        files = sorted(glob.glob(os.path.join(d, "*.png")))
    else:
        files = [os.path.abspath(a) for a in args]
    for f in files:
        if os.path.exists(f):
            search(f, apply_it)
        else:
            print("缺失", f)


if __name__ == "__main__":
    main()
