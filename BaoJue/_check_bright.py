# -*- coding: utf-8 -*-
r"""
成片亮度验收：把用户「偏黑 / 阴影过重 / 不柔和」这条反馈变成可量化的数字。

为什么需要它：H3 是照参考图打光的，改完提示词或参考图之后，
必须用**成片的实际灰度分布**来验收，而不是靠"看起来应该好了"。

指标含义
  mean   全画面平均亮度（目标 ≥ 120）
  med    中位灰度（目标 ≥ 130）—— 比 mean 更能反映"大面积是不是黑的"
  p05    第 5 百分位（目标 ≥ 45）—— **这条最关键**，代表暗部有没有被压死；
         用户说的"阴影过重"就是 p05 太低
  p90    第 90 百分位（目标 200~250）—— 亮部别过曝

用法
  python _check_bright.py              # 看成片目录 D:\output
  python _check_bright.py --stale      # 看 D:\output\_stale（改之前的老片，作对照）
  python _check_bright.py --cmp        # 成片 vs _stale 同段对照，直接看提亮了多少
"""
import os
import re
import sys
import subprocess

sys.stdout.reconfigure(encoding="utf-8")

PY_IMG = r"E:\ComfyUI\ComfyUI-master\ComfyUI-master\venv\Scripts\python.exe"
OUT = r"D:\output"
STALE = os.path.join(OUT, "_stale")

MEAN_MIN, MED_MIN, P05_MIN = 120.0, 130, 45

MEASURE = r'''
import os, sys, glob, json
from PIL import Image
def stat(p):
    h = Image.open(p).convert("L").histogram()
    tot = sum(h); c = 0; g = {}
    for i, v in enumerate(h):
        c += v
        if "p05" not in g and c >= tot * 0.05: g["p05"] = i
        if "med" not in g and c >= tot * 0.5:  g["med"] = i
        if "p90" not in g and c >= tot * 0.90: g["p90"] = i
    g["mean"] = round(sum(i * v for i, v in enumerate(h)) / tot, 1)
    return g
out = {}
for p in sys.argv[1:]:
    try:
        out[os.path.basename(p)] = stat(p)
    except Exception as e:
        out[os.path.basename(p)] = {"err": str(e)}
print(json.dumps(out))
'''


def measure(paths):
    if not paths:
        return {}
    import json
    r = subprocess.run([PY_IMG, "-c", MEASURE] + paths, capture_output=True, text=True)
    if r.returncode != 0:
        print("测量失败:", (r.stderr or "")[-500:])
        return {}
    return json.loads(r.stdout.strip().splitlines()[-1])


def newest_pngs(d, limit=99):
    if not os.path.isdir(d):
        return []
    fs = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".png")]
    fs.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return fs[:limit]


def verdict(s):
    bad = []
    if s["mean"] < MEAN_MIN:
        bad.append("平均亮度偏低")
    if s["med"] < MED_MIN:
        bad.append("大面积偏黑")
    if s["p05"] < P05_MIN:
        bad.append("暗部压死（阴影过重）")
    if s["p90"] > 250:
        bad.append("亮部接近过曝")
    return "OK" if not bad else " / ".join(bad)


def main():
    mode = "--stale" if "--stale" in sys.argv else ("--cmp" if "--cmp" in sys.argv else "cur")
    if mode == "--cmp":
        cur = {os.path.basename(p): p for p in newest_pngs(OUT)}
        old = {}
        for p in newest_pngs(STALE, 200):
            # _stale 里的名字形如 20261003_201416.ep01_t01_00001.png
            m = re.match(r"\d{8}_\d{6}\.(.+)$", os.path.basename(p))
            if m:
                old.setdefault(m.group(1), p)
        keys = sorted(set(cur) & set(old))
        if not keys:
            print("还没有可对照的段（成片目录里暂时没有和 _stale 同名的 PNG）。")
            return
        a = measure([old[k] for k in keys])
        b = measure([cur[k] for k in keys])
        print("%-26s %-22s %-22s %s" % ("seg", "改前 mean/med/p05", "改后 mean/med/p05", "结论"))
        for k in keys:
            o, n = a.get(k, {}), b.get(k, {})
            if "mean" not in o or "mean" not in n:
                continue
            print("%-26s %-22s %-22s %s" % (
                k,
                "%5.1f/%4d/%4d" % (o["mean"], o["med"], o["p05"]),
                "%5.1f/%4d/%4d" % (n["mean"], n["med"], n["p05"]),
                verdict(n)))
        return

    d = STALE if mode == "--stale" else OUT
    ps = newest_pngs(d)
    if not ps:
        print("目录里没有 PNG：%s" % d)
        return
    res = measure(ps)
    print("== %s（共 %d 张）==" % (d, len(ps)))
    print("%-32s %6s %5s %5s %5s  %s" % ("file", "mean", "med", "p05", "p90", "结论"))
    for p in ps:
        k = os.path.basename(p)
        s = res.get(k, {})
        if "mean" not in s:
            print("%-32s  %s" % (k, s.get("err", "?")))
            continue
        print("%-32s %6.1f %5d %5d %5d  %s" % (k, s["mean"], s["med"], s["p05"], s["p90"], verdict(s)))


if __name__ == "__main__":
    main()
