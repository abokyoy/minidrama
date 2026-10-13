# -*- coding: utf-8 -*-
"""把「三视图 + 大头像」角色设定图裁成单人正面全身图。

⭐⭐ 这就是人物复制（第2段三个苏小满、第3轮两个苏小满）的真病根：
参考图本身画了同一个人 4 次（大头像 + 正面 + 侧面 + 背面）。
模型看到「四个人」，于是照着画出两个人 —— 它是在忠实执行参考图，
不是提示词写错。前面三轮都在改提示词、砍参考图，方向全错了。

缝位置逐张看图手工标定（自动检测不可靠：缝常是低密度平台，
阈值一变位置就飘，裁出的图会带进侧脸或切到人）。
每张的区间都经过肉眼核对。
"""

import os
import shutil
import cv2

# 逐张标定：角色 -> (正面全身左界, 右界)  单位=原图像素（2730x1536 版式）
# 左界取「大头像右边界」（前景密度最低的谷），右界 = 左界 + 一个身位宽
CUTS = {
    "suxiaoman":    (1175, 1690),
    "qianjingli":   (1085, 1620),
    "xiaotang":     (1320, 1800),
    "afang":        (1250, 1700),
    "zhouzongjian": (1400, 1880),
    "nvguibin":     (1160, 1650),
}

PAIRS = [("assets", "assets_single"),
         ("assets_soft", "assets_soft_single")]

OUT_H = 1280


def assert_one_person(dst, label):
    """裁完的图必须只有一个人 —— 用「居中度」判断，不看左侧有没有前景。

    ⚠️ 曾经的错判：去查「左侧 40% 有没有前景」→ 全红。
       但人像的手臂/裙摆本来就在左侧，前景占比从边缘平滑爬升是正常的。
    那张图左边多出来的东西，是大头像的头发残影，属于「另一个人的碎片」。

    正确判据（对照真凶的特征）：
      真凶 = 有一条竖直边界，左边一块独立碎影（头发/肩膀），中间有明显白缝，
             右边才是完整人像。
      正常 = 左右留白大致对称，人像从中间往两侧渐变，没有孤立碎块。
    所以查：是否存在「前景 → 白缝 → 前景」的三段结构。
    """
    im = cv2.imread(dst)
    h, w = im.shape[:2]
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    col = (gray < 225).mean(axis=0)
    solid = col > 0.06          # 认定「有实体」的阈值
    xs = [x for x in range(w) if solid[x]]
    if not xs:
        return False, "整张图空"
    left, right = xs[0], xs[-1]
    # 人像左右两侧留白应大致对称；不对称说明一边混进了别人的碎片
    lp, rp = left, w - 1 - right
    skew = abs(lp - rp) / float(max(lp, rp) + 1)
    # 中间必须连续（人像是一整块），不能有白缝把它切成两段
    mid_empty = any(not solid[x] for x in range(left, right + 1))
    if mid_empty:
        return False, "人像中间有白缝（混入了别人的碎片）"
    if skew > 0.55:
        return False, "左右留白偏斜 %.0f%%（左%d 右%d）" % (skew * 100, lp, rp)
    return True, "居中 左%d 右%d" % (lp, rp)


def cut_one(src, dst):
    im = cv2.imread(src)
    if im is None:
        print("    读不了: %s" % src)
        return False
    h, w = im.shape[:2]
    if w != 2730:
        print("    宽度 %d 不是新版式 2730，跳过" % w)
        return False

    crop = im[:, 1175:1690] if False else None  # 占位，实际用下面传入的区间
    return True


def cut_range(im, x0, x1, dst):
    crop = im[:, x0:x1]
    # 去掉这一格里人物外侧的空白，留14px 边距
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    col = (gray < 236).mean(axis=0)
    nz = [x for x in range(col.shape[0]) if col[x] > 0.006]
    if not nz:
        print("    这一格是空的")
        return False
    pad = 14
    a = max(0, nz[0] - pad)
    b = min(crop.shape[1], nz[-1] + 1 + pad)
    crop = crop[:, a:b]

    ch, cw = crop.shape[:2]
    s = float(OUT_H) / ch
    crop = cv2.resize(crop, (int(cw * s), OUT_H), interpolation=cv2.INTER_AREA)
    cv2.imwrite(dst, crop, [cv2.IMWRITE_PNG_COMPRESSION, 6])
    return True


def main():
    for src_dir, out_dir in PAIRS:
        if not os.path.isdir(src_dir):
            print("跳过（无目录）%s" % src_dir)
            continue
        os.makedirs(out_dir, exist_ok=True)
        print("\n=== %s -> %s ===" % (src_dir, out_dir))

        for name, (x0, x1) in CUTS.items():
            src = os.path.join(src_dir, "char_%s.png" % name)
            dst = os.path.join(out_dir, "char_%s.png" % name)
            if not os.path.exists(src):
                print("  %-12s 源图不存在" % name)
                continue
            im = cv2.imread(src)
            if im is None or im.shape[1] != 2730:
                print("  %-12s 不是新版式 2730 宽，跳过" % name)
                continue
            if cut_range(im, x0, x1, dst):
                got = cv2.imread(dst)
                ok, why = assert_one_person(dst, name)
                print("  %-12s x=%d..%d -> %dx%d  %s"
                      % (name, x0, x1, got.shape[1], got.shape[0],
                         ("✅ " + why) if ok else ("❌ " + why)))

        # 场景图原样同步（场景图本来只有环境，不含人）
        n = 0
        for f in os.listdir(src_dir):
            if f.startswith("sc_"):
                s = os.path.join(src_dir, f)
                d = os.path.join(out_dir, f)
                if os.path.exists(s) and not os.path.exists(d):
                    shutil.copy2(s, d)
                n += 1
        print("  场景图 %d 张已就位" % n)


if __name__ == "__main__":
    main()