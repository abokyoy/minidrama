# -*- coding: utf-8 -*-
"""调色 A/B 对照：同一条原片，套不同调色档，量出各自的画风数字 + 并排出图。

用途：改 _grade.py 之后先在这里验证，不要直接拿去跑全片。
做法：拿同一支原片，分别套 GRADE_PROFILES 里每个档，输出到 _gradetest/，
      然后跟 Seedance 的目标值（黑位~11、对比度~171、动态范围~211）比对。

用法：
  python _grade_ab.py            # 全部档位
  python _grade_ab.py clean      # 只跑某一档
"""
import json
import os
import shutil
import subprocess
import sys

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)

import numpy as np
import cv2

FF = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_gradetest")
SRC = r"D:\output\new\_raw\xs01_t01_00001.mp4"
SEED = r"D:\output\Seedance\清洁女工与富客走廊冲突 (1).mp4"

sys.path.insert(0, HERE)
import _grade  # noqa: E402  复用它的档位定义

# Seedance 实测基线（_grade_cmp.py 3 支片均值）
TARGET = {"p01": 10.9, "p05": 25.0, "p50": 119.2, "p95": 196.2,
          "p99": 221.5, "contrast": 171.2, "spread": 210.6}


def run_grade(src, dst, vf):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    r = subprocess.run([FF, "-y", "-v", "error", "-i", src, "-vf", vf,
                        "-c:v", "libx264", "-crf", "16", "-preset", "veryfast",
                        "-pix_fmt", "yuv420p", "-an", dst],
                       capture_output=True, timeout=1800)
    if r.returncode:
        print("FFMPEG ERR:", (r.stderr or b"").decode("utf-8", "replace")[:300])
        return False
    return True


def measure(video, tag):
    # ⚠️ OpenCV 5 的 imread/imwrite 读不了含中文的路径（静默返回 None）。
    # 本项目路径全是中文（E:\LLM\try\minidrama\保洁\...），
    # 所以**所有抽帧/读图都必须先拷到纯 ASCII 目录**。
    # 之前 `_dup_check.py` 已经在同一个坑上栽过一次，这里统一处理。
    root = r"E:\LLM\try\minidrama\_ab_ascii"
    d = os.path.join(root, tag)
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    subprocess.run([FF, "-y", "-v", "error", "-i", video,
                    "-vf", "fps=2/5,scale=480:-1", os.path.join(d, "g%02d.png")],
                   capture_output=True, timeout=600)
    fs = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    allp = []
    for f in fs:
        im = cv2.imread(os.path.join(d, f))
        if im is None:
            continue
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        allp.append(np.percentile(g, [1, 5, 50, 95, 99]))
    if not allp:
        return None
    m = np.array(allp).mean(axis=0)
    return {"p01": m[0], "p05": m[1], "p50": m[2], "p95": m[3], "p99": m[4],
            "contrast": m[3] - m[1], "spread": m[4] - m[0]}


def strip(video, tag, label):
    d = os.path.join(r"E:\LLM\try\minidrama\_ab_ascii", tag)
    fs = sorted(f for f in os.listdir(d) if f.endswith(".png"))[:3]
    ims = []
    for f in fs:
        im = cv2.imread(os.path.join(d, f))
        if im is None:
            continue
        cv2.putText(im, label, (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.rectangle(im, (0, 0), (im.shape[1] - 1, 2), (0, 255, 255), 1)
        ims.append(im)
    return np.vstack(ims) if ims else None


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    os.makedirs(OUT, exist_ok=True)
    jobs = [("RAW", None)]                       # 原片（不调色）
    for name in _grade.GRADE_PROFILES:
        if only and name != only:
            continue
        jobs.append((name, _grade.GRADE_PROFILES[name]))
    jobs.append(("SEEDANCE", None))

    rows, strips = [], []
    for tag, prof in jobs:
        if tag == "SEEDANCE":
            vid = SEED
        elif prof is None:
            vid = os.path.join(OUT, "raw.mp4")
            if not os.path.exists(vid):
                shutil.copyfile(SRC, vid)
        else:
            vid = os.path.join(OUT, "%s.mp4" % tag)
            if not run_grade(SRC, vid, _grade.build_vf(prof)):
                continue
        m = measure(vid, tag)
        if not m:
            print("量不到:", tag)
            continue
        rows.append((tag, m))
        strips.append(strip(vid, tag, tag))
        print("%-10s p01=%5.1f p05=%5.1f p50=%5.1f p95=%5.1f p99=%5.1f  对比=%5.1f 动态=%5.1f"
              % (tag, m["p01"], m["p05"], m["p50"], m["p95"], m["p99"],
                 m["contrast"], m["spread"]))

    print()
    print("目标（Seedance）：p01=%.1f 对比=%.1f 动态=%.1f" %
          (TARGET["p01"], TARGET["contrast"], TARGET["spread"]))
    print()
    print("与 Seedance 目标的差距（0 = 完全对齐）")
    print("%-10s %8s %8s %8s" % ("档位", "Δ黑位", "Δ对比", "Δ动态"))
    for tag, m in rows:
        print("%-10s %+8.1f %+8.1f %+8.1f"
              % (tag, m["p01"] - TARGET["p01"],
                 m["contrast"] - TARGET["contrast"],
                 m["spread"] - TARGET["spread"]))

    if strips:
        h = max(s.shape[0] for s in strips)
        norm = [cv2.copyMakeBorder(
            s if s.shape[0] == h else np.vstack(
                [s, np.zeros((h - s.shape[0], s.shape[1], 3), np.uint8)]),
            0, 0, 6, 6, cv2.BORDER_CONSTANT, value=(40, 40, 40)) for s in strips]
        # imwrite 也读不了中文路径 → 输出到纯 ASCII 目录
        dest = r"E:\LLM\try\minidrama\_grade_ab.jpg"
        cv2.imwrite(dest, np.hstack(norm))
        print()
        print("对照图 →", dest)
        print("从左到右：", " / ".join(t for t, _ in rows))


if __name__ == "__main__":
    main()
