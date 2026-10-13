# -*- coding: utf-8 -*-
"""量参考图调色前后的**肤色**，防止调出「发红/发橙」。

为什么需要这个（2026-10-04 20:55 踩坑）：
  肉眼看对比图觉得「脸发红」，但说不清是哪一步造成的 —— 猜了三轮参数都改不对。
  → 必须直接量。肤色在 HSV 里落在 H∈[0,30]∪[160,180]、S∈[40,140]、V>90，
    统计这些像素的平均 H：
      H 越小越红（0=纯红，15=健康肤色，25=偏黄）
      S 越大越艳
  实测原图 H=14.9 是健康肤色；调坏之后 H 会掉到 8 以下 → 一眼看出来。

踩过的坑：
  · OpenCV 5 读中文路径静默返回 None（第 3 次栽）→ 一律先拷到纯 ASCII 目录
  · 肤色像素可能不足 500（参考图里人物占比小）→ 返回 -1 让调用方跳过
"""
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
TMP = r"C:\Users\86134\.workbuddy\tmp\skinchk"


def read_any(path):
    """读图；中文路径读不出时用 ffmpeg 转码绕开。"""
    os.makedirs(TMP, exist_ok=True)
    tag = os.path.splitext(os.path.basename(path))[0][:20]
    dst = os.path.join(TMP, tag + ".png")
    try:
        if os.path.exists(dst):
            os.remove(dst)
    except OSError:
        pass
    shutil.copy2(path, dst)
    im = cv2.imread(dst, cv2.IMREAD_COLOR)
    if im is None:
        alt = os.path.join(TMP, tag + "_x.png")
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", dst, alt],
                       capture_output=True)
        im = cv2.imread(alt, cv2.IMREAD_COLOR)
    return im


def skin_stats(path):
    im = read_any(path)
    if im is None:
        return None
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[:, :, 0].astype(int), hsv[:, :, 1].astype(int), hsv[:, :, 2].astype(int)
    m = ((H <= 30) | (H >= 160)) & (S >= 40) & (S <= 140) & (V > 90)
    n = int(m.sum())
    if n < 500:
        return dict(n=n, H=-1, S=-1)
    return dict(n=n, H=float(H[m].mean()), S=float(S[m].mean()))


def verdict(h):
    """H < 11 → 明显偏红；11~20 → 健康；> 20 → 偏黄/偏暗。"""
    if h < 0:
        return "无肤色数据"
    if h < 11:
        return "★偏红（发红/发橙）"
    if h <= 20:
        return "健康肤色"
    return "偏黄"


if __name__ == "__main__":
    pairs = []
    for a in sys.argv[1:]:
        if "=" in a:
            k, p = a.split("=", 1)
            pairs.append((k, p))
        else:
            pairs.append((os.path.basename(a), a))
    print("%-18s %10s %8s %8s  %s" % ("图", "肤色像素", "平均H", "平均S", "判定"))
    print("-" * 60)
    for k, p in pairs:
        if not os.path.exists(p):
            print("%-18s  缺失" % k)
            continue
        r = skin_stats(p)
        if r is None:
            print("%-18s  读取失败" % k)
        else:
            print("%-18s %10d %8.1f %8.1f  %s"
                  % (k, r["n"], r["H"], r["S"], verdict(r["H"])))
