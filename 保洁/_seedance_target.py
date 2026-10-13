# -*- coding: utf-8 -*-
"""从**全部 4 支** Seedance 样片算出权威目标分布，写入 _seedance_target.json。

⚠️ 为什么必须重算（2026-10-04 21:05 发现的错）：
  我之前硬编码的 TARGET 是从**其中一支**（(2) 号）抄的，所以它恰好等于 (2) 的数值。
  单支样本 → 目标值偏窄，会把其它 3 支误判成"不合格"。
  → 4 支全是 720x1280 竖屏 24fps 10.04s（ffprobe 实测，四支完全一致），
    联合平均才是可信目标。

用法：python _seedance_target.py
"""
import glob
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import _softgrade as SG

SRC = r"D:\output\Seedance"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_seedance_target.json")


def main():
    files = sorted(glob.glob(os.path.join(SRC, "*.mp4")))
    print("共 %d 支样片\n" % len(files))
    rows = {}
    for i, f in enumerate(files):
        tag = "sd%02d" % i
        m = SG.measure(f, tag)
        rows[f] = m
        print("  [%d] p50=%5.1f p95=%5.1f p99=%5.1f 饱和=%5.1f 局部=%5.2f"
              % (i, m["p50"], m["p95"], m["p99"], m["sat"], m["local"]))

    keys = SG.KEYS + ["sat", "local", "contrast", "dyn"]
    T = {k: float(np.mean([m[k] for m in rows.values()])) for k in keys}
    sd = {k: float(np.std([m[k] for m in rows.values()])) for k in keys}

    print("\n=== Seedance 4 支联合目标（均值 ± 标准差）===")
    for k in keys:
        print("  %-8s %7.2f  ± %.2f" % (k, T[k], sd[k]))

    # 验收阈值用「均值 ± 1.5σ」，避免把正常波动判成不合格
    TOL = {k: max(2.0, 1.5 * sd[k]) for k in keys}
    payload = dict(target=T, stdev=sd, tol=TOL, n=len(files))
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, indent=1))
    print("\n已写入 " + OUT)


if __name__ == "__main__":
    main()
