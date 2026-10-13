# -*- coding: utf-8 -*-
"""把一支片子和 Seedance 目标逐项对照，打「过 / 不过」表。

用法：
    python _ab_seedance.py "D:\\output_h3off\\off_xs01_t01_00001-audio.mp4"
    python _ab_seedance.py a.mp4 b.mp4 c.mp4     # 一次比多支

判定标准：偏差在 ±1.5σ 容差内算「过」（`_seedance_target.json` 的 tol）。
只看数字不看结论生成 —— 但**最终验收必须人眼看片**。
"""
import json
import os
import sys

import _softgrade as SG

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "_seedance_target.json"), encoding="utf-8") as f:
    T = json.load(f)

TGT, TOL = T["target"], T["tol"]

ROWS = [
    ("p50", "中间调", 1),
    ("p95", "亮部", 1),
    ("p05", "暗部", 1),
    ("p01", "最黑点", 1),
    ("p25", "中暗", 1),
    ("p75", "中亮", 1),
    ("p99", "最亮点", 1),
    ("local", "局部对比", 1),
    ("contrast", "全局对比", 1),
    ("sat", "饱和度", 1),
    ("dyn", "动态范围", 1),
]


def one(path):
    tag = os.path.splitext(os.path.basename(path))[0]
    print("=" * 74)
    print("  %s" % tag)
    print("=" * 74)
    m = SG.measure(path, tag)
    w, h = SG.probe_size(path)
    print("  尺寸 %dx%d= %.2f MP    抽帧 %d" % (w, h, w * h / 1e6, SG.NF))
    print("")
    print("  %-10s %8s %8s %8s %9s  %s" % ("指标", "本片", "目标", "偏差", "容差±", "判定"))
    print("  " + "-" * 62)
    npass = 0
    for k, name, _ in ROWS:
        v, g, tol = m[k], TGT[k], TOL[k]
        d = v - g
        ok = abs(d) <= tol
        npass += 1 if ok else 0
        print("  %-10s %8.2f %8.2f %+8.2f %9.2f  %s"
              % (name, v, g, d, tol, "过" if ok else "★不过"))
    print("")
    print("  → %d / %d 项在容差内" % (npass, len(ROWS)))
    return m, npass


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        print(__doc__)
        sys.exit(1)
    for p in args:
        if not os.path.isfile(p):
            print("找不到文件: " + p)
            continue
        one(p)
        print("")


if __name__ == "__main__":
    main()