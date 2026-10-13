# -*- coding: utf-8 -*-
"""⭐ 参考图「拉开间距」重排 —— 按等宽切分，不做人物检测。

## 为什么这么粗暴反而可靠
试过三种自动检测（列投影 / 形态学闭运算 / 横线扫缝隙），
**全部失败** —— 因为三视图挨得太近，衣服在水平投影上互相重叠，
连一条干净的背景缝都扫不出来（实测最宽缝仅 23px）。
→ 与其写一个脆detector，不如用**已知版式**直接切：
参考图是标准三视图 sheet，右侧三个全身像各占约 1/3 宽度，位置稳定。

## 做法
把右侧区域按**等宽三等分**切开，每块含一个全身像；
每块缩到统一身高，再按**指定的宽间距**重新排到新画布。
人物像素零改动 —— 只是变小了、挪位置了。

用法：
    python _ref_repack.py <src.png> <dst.png> [间距比] [身高比]
    例：python _ref_repack.py assets/char_xiaotang.png out.png 0.32 0.60
"""
from __future__ import print_function

import sys

import cv2
import numpy as np


def repack(src, dst, gap_ratio=0.30, fig_h=0.62, right_start=0.50):
    im = cv2.imread(src)
    if im is None:
        print("  读不出", src)
        return 1
    h, w = im.shape[:2]
    bgv = np.median(im[0:int(h * 0.03), :, :].reshape(-1, 3), axis=0).astype("u1")

    # 右侧三等分
    x_start = int(w * right_start)
    seg_w = (w - x_start) / 3.0
    cuts = [(int(x_start + i * seg_w), int(x_start + (i + 1) * seg_w))
            for i in range(3)]
    print("  切分:", cuts)

    crops = [im[:, a:b] for a, b in cuts]

    # 统一缩放到同一身高
    fh = int(h * fig_h)
    scaled = []
    for c in crops:
        ch, cw = c.shape[:2]
        scaled.append(cv2.resize(c, (max(1, int(cw * (fh / float(ch)))), fh),
                                  interpolation=cv2.INTER_AREA))

    # 左侧大头照：切到 x_start
    big = im[:, :x_start]
    bh, bw = big.shape[:2]
    big_s = cv2.resize(big, (max(1, int(bw * (fh / float(bh)))), fh),
                       interpolation=cv2.INTER_AREA)

    # 新画布：大头照 + 三个小图，每个之间 gap 宽
    gap = int(fh * gap_ratio)
    pad = int(fh * 0.04)
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
    print("  → %s %s  间距=%dpx (原图最宽缝仅 23px)" % (dst, canvas.shape, gap))
    return 0


if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2]
    gr = float(sys.argv[3]) if len(sys.argv) > 3 else 0.30
    fh = float(sys.argv[4]) if len(sys.argv) > 4 else 0.62
    rs = float(sys.argv[5]) if len(sys.argv) > 5 else 0.50
    print("重排 %s间距比=%.2f 身高比=%.2f 右起点=%.2f" % (src, gr, fh, rs))
    sys.exit(repack(src, dst, gr, fh, rs))