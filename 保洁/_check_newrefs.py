# -*- coding: utf-8 -*-
"""验收 ImageGen 新生成的参考图：逐张量色调 + 肤色，并和 Seedance 目标比对。

为什么必须量（2026-10-04 22:15）：
  上轮我凭肉眼觉得"新场景图不错"，结果量出来才看到 p99=233.9 仍偏高。
  → 参考图的每一次改动都要**用数字验收**，不能靠看。
  → 人物图还多一项：肤色必须健康（`_skinchk.py` 判 H 在 11~20）。

用法：
  python _check_newrefs.py a.png b.png ...
  python _check_newrefs.py --dir assets_new
"""
import glob
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np

import _skinchk
import _softrefs as SR

TXT = r"C:\Users\86134\.workbuddy\tmp\newref"
TARGET = dict(p05=28.5, p25=71.8, p50=117.8, p75=148.0, p95=195.0,
              p99=223.6, sat=53.8, local=10.5)
TOL = dict(p05=8.4, p25=10.4, p50=7.1, p75=3.4, p95=5.3, p99=7.3,
           sat=6.9, local=0.9)


def one(path):
    ASCII = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    tag = "".join(c if c in ASCII else "_"
                  for c in os.path.splitext(os.path.basename(path))[0])[:20]
    os.makedirs(TXT, exist_ok=True)
    d = os.path.join(TXT, tag + ".png")
    if os.path.exists(d):
        os.remove(d)
    shutil.copy2(path, d)
    m = SR.measure_still(d)
    sk = _skinchk.skin_stats(d)
    return m, sk


def main():
    args = [a for a in sys.argv[1:]]
    if "--dir" in args:
        files = sorted(glob.glob(os.path.join(args[args.index("--dir") + 1], "*.png")))
    else:
        files = [a for a in args if not a.startswith("--")]
    if not files:
        raise SystemExit("没给文件")

    print("目标：" + "  ".join("%s=%.1f" % (k, TARGET[k]) for k in
                             ("p05", "p25", "p50", "p95", "p99", "sat", "local")))
    print()
    for f in files:
        if not os.path.exists(f):
            print("%-34s 缺失" % os.path.basename(f))
            continue
        m, sk = one(f)
        name = os.path.basename(f)[:32]
        bad = []
        for k, t in TARGET.items():
            v = m[k]
            if abs(v - t) > TOL[k]:
                bad.append("%s %.0f→%.0f(目标%.0f)" % (k, v, t, v - t))
        # ⚠️ _skinchk.skin_stats 返回的键是 n / H / S（不是 skH / skS），
        #    写错会直接 KeyError。
        sktxt = ("肤色S=%.0f H=%.0f %s" % (sk["S"], sk["H"], _skinchk.verdict(sk["H"]))
                 if sk and sk["H"] > 0 else "无肤色数据")
        print("── %s" % name)
        print("   p05=%5.1f p25=%5.1f p50=%5.1f p75=%5.1f p95=%5.1f p99=%5.1f 饱和=%5.1f 局部=%5.2f"
              % (m["p05"], m["p25"], m["p50"], m["p75"], m["p95"], m["p99"],
                 m["sat"], m["local"]))
        print("   " + sktxt)
        if bad:
            print("   ⚠️ 偏离：" + "；".join(bad))
        else:
            print("   ✔ 全部在容差内")
        print()


if __name__ == "__main__":
    main()
