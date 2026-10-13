# -*- coding: utf-8 -*-
"""做「脸部特写」参考图 —— 给换装测试用。

为什么要单独做：
  用户要测修仙打斗，**服装是古装**，但参考图是现代制服
  （藏青工作衬衫+灰围裙 / 白衬衫+灰马甲）。
  送整身图进去 → 模型会把制服一起带出来，古装穿不上。
  → 只裁**头肩范围**的脸部特写，五官和发型保留，衣服完全不进画面。
  → 服装完全由提示词描述决定。

按之前踩过的坑：
  ⛔ 必须单人正面 —— 参考图里有几个人，模型就画几个人
  ⛔ 边界看图手工标定 —— 自动检测不可靠
  ⛔ 裁完必须肉眼验证
"""
import os
import shutil
import cv2

SRC = "assets_single"
OUT = "assets_face"
PAIRS = [("assets_single", "assets_face"), ("assets_soft_single", "assets_face")]

# 头部在上半部。按 1280 高的单人图，裁到 y 30..330 —— 只留头+颈，
# **不能到锁骨以下**（那里是现代制服的领口，会把衣服带进画面）。
# 衣服完全交给提示词描述（用户要古装）。
FACE_BOX = {
    # 名字: (y0, y1)  —— 头颈范围
    "suxiaoman":    (30, 285),
    "qianjingli":   (30, 285),
}


def cut_face(src, dst, y0, y1):
    im = cv2.imread(src)
    if im is None:
        print("   读不了%s" % src)
        return False
    h, w = im.shape[:2]
    # 左右向内收一点，去掉伸出来的手臂/围裙
    cx0, cx1 = int(w * 0.22), int(w * 0.78)
    yy0, yy1 = int(h * y0 / 1280.0), int(h * y1 / 1280.0)
    face = im[yy0:yy1, cx0:cx1]
    fh, fw = face.shape[:2]
    # 放大到高768（脸特写要够清晰）
    s = 768.0 / fh
    face = cv2.resize(face, (int(fw * s), 768), interpolation=cv2.INTER_AREA)
    cv2.imwrite(dst, face, [cv2.IMWRITE_PNG_COMPRESSION, 6])
    print("   %dx%d -> %dx%d" % (w, h, face.shape[1], face.shape[0]))
    return True


def main():
    for sd in (SRC, "assets_soft_single"):
        if not os.path.isdir(sd):
            continue
        os.makedirs(OUT, exist_ok=True)
        print("=== %s ===" % sd)
        for name, (y0, y1) in FACE_BOX.items():
            s = os.path.join(sd, "char_%s.png" % name)
            d = os.path.join(OUT, "char_%s.png" % name)
            if not os.path.exists(s):
                print("   %-12s 源图不存在" % name)
                continue
            print("   %-12s" % name)
            cut_face(s, d, y0, y1)
    print("\n-> %s/" % OUT)


if __name__ == "__main__":
    main()