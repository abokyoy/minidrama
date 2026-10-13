# -*- coding: utf-8 -*-
"""抽帧 + 拼接成「胸口特写放大图」，用来肉眼检查胸前有没有工牌/文字。

用法：
    python _chest_check.py <mp4> [out目录] [帧数]

为什么必须肉眼看（铁律：工具会骗人）：
    人脸检测抓不到侧脸/背身/胸前小物件 → 「人脸=1 个」并不代表没有复制的人，
    也不代表胸前干净。**胸前有没有挂东西只能靠眼睛看。**

输出：
    <out>/frame_XX.png        原始帧
    <out>/chest_grid.png      3xN 拼接的胸口放大图（每帧裁上半身并放大 2.5 倍）
    <out>/full_grid.png       3xN 拼接的整帧图（看构图/人数）
"""
from __future__ import print_function

import glob
import os
import shutil
import subprocess
import sys

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
# ⛔ 必须纯 ASCII 且不在受管目录（软删除钩子会拦 ~/.workbuddy/tmp）
AB = r"D:\_abtmp"

ASCII = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")


def safe(s):
    return "".join(c if c in ASCII else "_" for c in s)[:40] or "x"


def grab(mp4, tag, n=12):
    d = os.path.join(AB, "chest_" + safe(tag))
    os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "src.mp4")
    # ⚠️ 用 shutil 不用 shell copy —— 静默失败会导致「抽不出帧」，
    #    症状和「片是黑的」一模一样
    shutil.copy2(mp4, src)
    # 不删旧帧：独立子目录 + 覆盖写（ffmpeg -y 覆盖同名的 f*.png）
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", src,
                    "-vf", "fps=%g" % (n / 10.0),
                    os.path.join(d, "f%02d.png")], capture_output=True)
    fs = sorted(glob.glob(os.path.join(d, "f*.png")))
    # 去掉上一次可能残留的（帧数变了会留旧的）
    keep = set(fs[-n:])
    return d, sorted(keep)


def grid(files, cols, crop, out, scale=2.5, tilew=520):
    """把 frames 拼成一张大图。crop=None 表示整帧。"""
    import cv2
    import numpy as np
    ims = []
    for f in files:
        im = cv2.imread(f, cv2.IMREAD_COLOR)
        if im is None:
            continue
        if crop:
            h, w = im.shape[:2]
            # 上半身：横向取中间 62%，纵向取 0~62%（胸口在这块）
            cw = int(w * 0.62)
            x0 = (w - cw) // 2
            ch = int(h * 0.62)
            im = im[0:ch, x0:x0 + cw]
        h, w = im.shape[:2]
        tw = tilew
        th = int(h * (tw / float(w)))
        im = cv2.resize(im, (tw, th), interpolation=cv2.INTER_CUBIC)
        # 标号
        cv2.rectangle(im, (0, 0), (tw, 26), (0, 0, 0), -1)
        cv2.putText(im, os.path.basename(f)[:-4], (6, 19),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        ims.append(im)
    if not ims:
        print("没有可用帧")
        return None
    th = max(i.shape[0] for i in ims)
    tw = ims[0].shape[1]
    rows = (len(ims) + cols - 1) // cols
    canvas = np.zeros((rows * th, cols * tw, 3), np.uint8)
    for k, im in enumerate(ims):
        r, c = divmod(k, cols)
        canvas[r * th:r * th + im.shape[0], c * tw:c * tw + im.shape[1]] = im
    p = os.path.join(os.path.dirname(files[0]), out)
    cv2.imwrite(p, canvas)
    print("  →", p, canvas.shape)
    return p


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    mp4 = sys.argv[1]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    tag = os.path.splitext(os.path.basename(mp4))[0]
    print("检查:", mp4)
    d, files = grab(mp4, tag, n)
    print("抽到 %d 帧 @ %s" % (len(files), d))
    if not files:
        return 2
    grid(files, 4, True, "chest_grid.png")
    grid(files, 4, None, "full_grid.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())