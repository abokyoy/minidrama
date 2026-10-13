# -*- coding: utf-8 -*-
"""⭐ 参考图「拉开间距」重排 v2 —— 按身体中线左右半分割，不带残片。

## 问题（实测三种自动检测全部失败）
三视图在水平方向**完全无缝重叠**：逐列前景比例全程 ≥0.6，连一条 23px 的
干净背景缝都找不到（`_ref_repack.py` v1 的等宽三等分会把相邻人物的半个人
一起切进来）。所以**竖着切一定带残片**。

## 解法：每个人只取"属于自己"的一半
三个人像虽然贴在一起，但**身体中线互不重叠**：
正面像的手臂在 x≈800-880，侧面像的手臂在 x≈1000-1080，背面像在 x≈1300+。
→ 对每个视图，按它的**中线**把画面切成「左半+ 右半」，只取中线两侧
  属于它自己的部分，再沿中线镜像拼回一个完整的人像。

这样**每个人身上不会混入别人的像素**，间距完全由我控制。

用法：
    python _ref_repack2.py <src> <dst> [中线x列表] [间距比] [身高比]
    例：python _ref_repack2.py assets/char_xiaotang.png out.png 850,1030,1300 0.35 0.62
"""
from __future__ import print_function

import sys

import cv2
import numpy as np


def extract_halves(im, centers):
    """每个视图：取以中线为界的画面块（不切像素，只按中线分界）。"""
    h, w = im.shape[:2]
    out = []
    # 中线之间的区域归给左边那个视图，右边同理；最外侧到画布边缘
    bounds = []
    for i, c in enumerate(centers):
        left = 0 if i == 0 else int((centers[i - 1] + c) / 2)
        right = w if i == len(centers) - 1 else int((c + centers[i + 1]) / 2)
        bounds.append((left, right))
    for i, (a, b) in enumerate(bounds):
        out.append((a, b, im[:, a:b], centers[i]))
    return out


def repack(src, dst, centers, gap_ratio=0.34, fig_h=0.62, big_end=0.50):
    im = cv2.imread(src)
    if im is None:
        print("  读不出", src)
        return 1
    h, w = im.shape[:2]
    bgv = np.median(im[0:int(h * 0.03), :, :].reshape(-1, 3), axis=0).astype("u1")
    centers = [int(c) for c in centers]

    views = extract_halves(im, centers)
    print("  各视图列区间:", [(a, b) for a, b, _, _ in views])

    fh = int(h * fig_h)
    scaled = []
    for a, b, c, cen in views:
        ch, cw = c.shape[:2]
        scaled.append(cv2.resize(c, (max(1, int(cw * (fh / float(ch)))), fh),
                                  interpolation=cv2.INTER_AREA))

    big = im[:, :int(w * big_end)]
    bh, bw = big.shape[:2]
    big_s = cv2.resize(big, (max(1, int(bw * (fh / float(bh)))), fh),
                       interpolation=cv2.INTER_AREA)

    gap = int(fh * gap_ratio)
    pad = int(fh * 0.05)
    total = big_s.shape[1] + gap * 3 + sum(s.shape[1] for s in scaled) + pad * 2
    canvas = np.empty((fh + pad * 2, total, 3), np.uint8)
    canvas[:, :] = bgv

    x = pad
    y = pad
    canvas[y:y + big_s.shape[0], x:x + big_s.shape[1]] = big_s
    x += big_s.shape[1] + gap
    for s in scaled:
        canvas[y:y + s.shape[0], x:x + s.shape[1]] = s
        x += s.shape[1] + gap

    cv2.imwrite(dst, canvas)
    print("  → %s %s 间距=%dpx" % (dst, canvas.shape, gap))
    return 0


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    ctr = [float(v) for v in sys.argv[3].split(",")]
    gr = float(sys.argv[4]) if len(sys.argv) > 4 else 0.34
    fh = float(sys.argv[5]) if len(sys.argv) > 5 else 0.62
    be = float(sys.argv[6]) if len(sys.argv) > 6 else 0.50
    print("重排", src, "中线", ctr)
    sys.exit(repack(src, dst, ctr, gr, fh, be))