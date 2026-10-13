# -*- coding: utf-8 -*-
"""把参考图的直方图**精确匹配**到 Seedance 目标分布（33 点曲线）。

═══ 为什么前两种手写曲线都失败 ═════════════════════════════════════
1. `_grid_bright.py`（提亮）: p50 40 → 53，抬不上去
2. `_grid_soft2.py`（压中间）: p50 190 → 178，压不下来
3. 根因：两者的控制点**输入位置都写死在 0.50**（即"原图的中间调"），
   但原图 98% 的像素挤在 0.72~0.85，0.50 附近几乎没像素。
   → 曲线在"像素真正所在的地方"几乎是平的，怎么调都没用。

═══ 本脚本的做法（复用已验证的 `_softgrade.solve_curve`）════════════
控制点的 **x = 该图实测的分位值**，**y = 目标分位值**。
即"现在 p50 落在 190，我要它落在 118" → 控制点 (190/255, 118/255)。
因为 x 就是像素真正聚集的位置，映射才真正生效（t02 实测一轮最大偏差 5.6）。

额外安全项：
  · 肤色保护 —— 反复验证过「改像素值会影响肤色」，所以把肤色 S/H 的
    变化量**放进验收**：调完必须肤色仍在 11~20 健康区间、S 不显著上涨。
  · 达标即停 —— 第 2 轮会重复调色、越调越差。

用法：
  python _match_hist.py a.png b.png --apply
"""
import io
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import _softgrade as SG   # noqa: E402

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
TMP = r"C:\Users\86134\.workbuddy\tmp\matchhist"
ASCII = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")


def safe(t):
    return "".join(c if c in ASCII else "_" for c in t)[:20] or "x"


def measure_still(path):
    """量静态 PNG。

    ⚠️ 不能用 `_softgrade.measure` —— 它走 `ffmpeg -vf fps=N` 抽帧，
       对单张图片会抽不出帧，直接 `SystemExit("抽帧失败")`。
       （同一个坑在 `_softrefs.py` 已踩过一次，这里不重复踩。）
    """
    import cv2
    import numpy as np

    d = path
    if not os.path.exists(d) or os.path.abspath(d) != os.path.abspath(path):
        pass
    im = cv2.imread(d, cv2.IMREAD_COLOR)
    if im is None:
        raise SystemExit("读不出图片（中文路径？): " + path)
    b, g, r = im[:, :, 0].astype("f4"), im[:, :, 1].astype("f4"), im[:, :, 2].astype("f4")
    y = 0.114 * b + 0.587 * g + 0.299 * r
    q = np.percentile(y, [1, 5, 25, 50, 75, 95, 99])
    out = dict(zip(SG.KEYS, [float(v) for v in q]))
    out["sat"] = float(cv2.cvtColor(im, cv2.COLOR_BGR2HSV)[:, :, 1].mean())
    h, w = y.shape
    bh, bw = h // 16 * 16, w // 16 * 16
    bl = y[:bh, :bw].reshape(bh // 16, 16, bw // 16, 16).transpose(0, 2, 1, 3)
    out["local"] = float(bl.reshape(-1, 256).std(axis=1).mean())
    out["contrast"] = out["p95"] - out["p05"]
    out["dyn"] = out["p99"] - out["p01"]
    return out


def one(src, apply_it=False):
    import _skinchk

    os.makedirs(TMP, exist_ok=True)
    tag = safe(os.path.splitext(os.path.basename(src))[0])
    a = os.path.join(TMP, tag + "_in.png")
    shutil.copy2(src, a)

    cur = measure_still(a)          # 静态图专用
    sk0 = _skinchk.skin_stats(a)

    tj = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "_seedance_target.json")
    T = json.load(io.open(tj, encoding="utf-8"))["target"]
    SG.TARGET.update({k: T[k] for k in SG.KEYS})
    SG.TARGET["sat"] = T["sat"]
    SG.TARGET["local"] = T["local"]

    print("\n══ %s" % os.path.basename(src))
    print("   原图 p05=%.1f p25=%.1f p50=%.1f p95=%.1f p99=%.1f 饱和=%.1f 局部=%.2f 肤色S=%.0f H=%.0f"
          % (cur["p05"], cur["p25"], cur["p50"], cur["p95"], cur["p99"],
             cur["sat"], cur["local"], sk0["S"], sk0["H"]))

    cs, _ = SG.solve_curve(cur, it=0)
    # 饱和度：只降不升（乘法；提亮后 S 相对会涨）
    ratio = 0.80 if cur["sat"] >= T["sat"] else 1.0
    need = cur.get("local", 10.0) / T["local"]
    sigma = max(0.0, min(1.0, (need - 1.0) * 6.0)) if need > 1 else 0.0
    vf = ("curves=all='" + cs + "',unsharp=5:5:0.35:5:5:0.0,eq=saturation=" +
          ("%.2f" % ratio) + (",gblur=sigma=%.2f" % sigma if sigma >= 0.35 else ""))

    dst = os.path.join(TMP, tag + "_out.png")
    r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", a, "-vf", vf,
                        "-frames:v", "1", dst], capture_output=True, text=True,
                       errors="replace")
    if r.returncode != 0 or not os.path.exists(dst):
        raise SystemExit("ffmpeg 失败: " + (r.stderr or "")[:300])

    new = measure_still(dst)
    sk1 = _skinchk.skin_stats(dst)
    print("   调后 p05=%.1f p25=%.1f p50=%.1f p95=%.1f p99=%.1f 饱和=%.1f 局部=%.2f 肤色S=%.0f H=%.0f"
          % (new["p05"], new["p25"], new["p50"], new["p95"], new["p99"],
             new["sat"], new["local"], sk1["S"], sk1["H"]))
    print("   目标 p05=%.1f p25=%.1f p50=%.1f p95=%.1f p99=%.1f 饱和=%.1f 局部=%.2f"
          % (T["p05"], T["p25"], T["p50"], T["p95"], T["p99"], T["sat"], T["local"]))

    bad = []
    for k in SG.KEYS:
        if abs(new[k] - T[k]) > 8.0:
            bad.append("%s %.0f→%.0f(目标%.0f)" % (k, new[k], T[k], new[k] - T[k]))
    if sk1["H"] < 11 or sk1["H"] > 20:
        bad.append("肤色 H=%.0f 越界（健康 11~20）" % sk1["H"])
    if sk1["S"] > sk0["S"] * 1.10:
        bad.append("肤色 S 涨了 %.0f%%（%.0f→%.0f）"
                   % ((sk1["S"] / max(sk0["S"], 1) - 1) * 100, sk0["S"], sk1["S"]))
    print("   " + ("✔ 达标" if not bad else "⚠️ " + "；".join(bad)))

    if apply_it:
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "assets_new_sc")
        os.makedirs(out_dir, exist_ok=True)
        d = os.path.join(out_dir, os.path.basename(src))
        shutil.copy2(dst, d)
        print("   → " + d)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply_it = "--apply" in sys.argv
    for f in args:
        p = os.path.abspath(f)
        if os.path.exists(p):
            one(p, apply_it)
        else:
            print("缺失", p)


if __name__ == "__main__":
    main()
