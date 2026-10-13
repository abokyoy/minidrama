# -*- coding: utf-8 -*-
"""三方画面对比图：本地原片 / 本地调色后 / Seedance。

为什么原片也摆进来：
用户说「本地像蒙了一层灰，Seedance 清亮」。直觉是「H3 直出不如 Seedance」，
但 _grade_cmp.py 的数据说反了 —— **H3 原片对比度 187 / 动态范围 227，
反而高于 Seedance 的 171 / 211**。是 _grade.py 的调色把画面弄灰的。
所以这张图必须三方摆一起看，否则会得出「原片也灰」的错误结论。

用法：python _grade_view.py [输出jpg]
"""
import os
import shutil
import subprocess
import sys

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)

import numpy as np
import cv2

FF = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
TMP = r"E:\LLM\try\minidrama\_grade_tmp"
DEST = sys.argv[1] if len(sys.argv) > 1 else r"E:\LLM\try\minidrama\_grade_compare.jpg"

# (标签, 视频, 该视频抽第几帧做代表)
PAIRS = [
    ("LOCAL_RAW", r"D:\output\new\_raw\xs01_t01_00001.mp4", 1),
    ("LOCAL_GRADED", r"D:\output\new\xs01_t01_00001.mp4", 1),
    ("SEEDANCE", r"D:\output\Seedance\清洁女工与富客走廊冲突 (1).mp4", 1),
]


def grab(tag, src, n=3):
    d = os.path.join(TMP, tag)
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        try:
            os.remove(os.path.join(d, f))
        except Exception:
            pass
    r = subprocess.run([FF, "-y", "-v", "error", "-i", src,
                        "-vf", "fps=2/5,scale=300:-1", "-frames:v", str(n),
                        os.path.join(d, "g%02d.png")],
                       capture_output=True, timeout=600)
    fs = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    if not fs:
        print("抽帧失败:", tag, (r.stderr or b"").decode("utf-8", "replace")[:200])
    return fs


def strip(files, tag):
    """竖拼一个视频的 3 帧，做成一条。"""
    ims = []
    for f in files:
        p = os.path.join(TMP, tag, f)
        im = cv2.imread(p)
        if im is None:
            continue
        cv2.putText(im, tag, (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
        cv2.rectangle(im, (0, 0), (im.shape[1] - 1, 2), (0, 255, 255), 1)
        ims.append(im)
    return np.vstack(ims) if ims else None


def main():
    strips = []
    for tag, src, _ in PAIRS:
        if not os.path.exists(src):
            print("缺失:", src)
            continue
        fs = grab(tag, src)
        s = strip(fs, tag)
        if s is not None:
            strips.append(s)
    if not strips:
        print("无可用画面")
        return
    h = max(s.shape[0] for s in strips)
    norm = []
    for s in strips:
        if s.shape[0] < h:
            s = np.vstack([s, np.zeros((h - s.shape[0], s.shape[1], 3), np.uint8)])
        s = cv2.copyMakeBorder(s, 0, 0, 6, 6, cv2.BORDER_CONSTANT, value=(40, 40, 40))
        norm.append(s)
    out = np.hstack(norm)
    cv2.imwrite(DEST, out)
    print("对比图 →", DEST, "尺寸", out.shape)
    print("从左到右：LOCAL_RAW（H3原片） / LOCAL_GRADED（现交付件） / SEEDANCE")


if __name__ == "__main__":
    main()
