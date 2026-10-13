# -*- coding: utf-8 -*-
"""并排对比 Seedance 样片与本地成片（不同画幅也能比）。

⚠️ 坑：Seedance 是 720x1280（竖）、本地是 672x1184（竖），但样片里也有横屏的。
   直接 hstack 会因高度不一致报
   `all the input array dimensions except for the concatenation axis must match`。
   → 统一缩放到同一高度再拼。

用法：python _cmp_final.py seedance=/path/a.mp4 t01=/path/b.mp4 [out.png]
"""
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
TMP = r"C:\Users\86134\.workbuddy\tmp\final"
H = 760          # 每帧统一高度
PER = 4          # 每支片取几帧


ASCII = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")


def safe_tag(tag):
    """只保留 ASCII 字母数字。

    ⚠️ 踩坑：`c.isalnum()` 对**中文返回 True**，所以用它过滤不掉中文！
       结果 ffmpeg 吐出 `本地t01_f03.png`，OpenCV 5 读不了中文路径 →
       静默返回 None → 「抽到 0 帧」→ np.hstack 报 need at least one array。
    """
    return "".join(c if c in ASCII else "_" for c in tag)[:24] or "x"


def frames(tag, path, per=PER):
    # ⚠️ tag 必须纯 ASCII（中文路径要先拷成 ASCII 文件名）。
    #    症状是「某支 frames=0」，见 safe_tag 的说明。
    safe = safe_tag(tag)
    os.makedirs(TMP, exist_ok=True)
    d = os.path.join(TMP, safe + ".mp4")
    shutil.copy2(path, d)
    for f in os.listdir(TMP):
        if f.startswith(safe + "_f") and f.endswith(".png"):
            try:
                os.remove(os.path.join(TMP, f))
            except OSError:
                pass
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", d,
                    "-vf", "fps=%d/10" % per,
                    os.path.join(TMP, safe + "_f%02d.png")], capture_output=True)
    fs = sorted(f for f in os.listdir(TMP)
                if f.startswith(safe + "_f") and f.endswith(".png"))
    out = []
    for f in fs[:per]:
        im = cv2.imread(os.path.join(TMP, f), cv2.IMREAD_COLOR)
        if im is not None:
            w = int(im.shape[1] * H / im.shape[0])
            out.append(cv2.resize(im, (w, H)))
    return out


def row_w(row):
    return sum(im.shape[1] for im in row) + 10 * (len(row) - 1)


def fit_row(imgs, width):
    """把若干帧补白到同一宽度（画幅不同 → 宽度不同）。"""
    parts = []
    for i, im in enumerate(imgs):
        if i:
            parts.append(np.full((H, 10, 3), 50, np.uint8))
        parts.append(im)
        if im.shape[1] < width:
            parts.append(np.full((H, width - im.shape[1], 3), 50, np.uint8))
    return np.hstack(parts)


def main():
    argv = sys.argv[1:]
    out = os.path.join(TMP, "final_cmp.png")
    if "--out" in argv:
        i = argv.index("--out")
        out = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]        # ⚠️ 必须把 --out 及其值一起剔掉，
                                              #    否则输出路径会被当成 k=p 参数拆开报错
    items = []
    for a in argv:
        if "=" not in a:
            continue
        k, p = a.split("=", 1)
        items.append((k, frames(k, p)))

    # ⚠️ 每行宽度和**行数**都要各自归一：
    #   · 宽度：不同画幅缩放到同高后宽度不同
    #   · 行数：fps=per/10 对时长 10.04s 的片子会抽出 4 或 5 帧（进位差异），
    #     行数不等 → vstack 报 `dimension 1, index 0 has size 6982, index 7 has size 7046`
    #     （后者其实是多出来的那一行）
    PER_ROW = PER
    fixed = []
    for k, row in items:
        if not row:
            # ⚠️ 某支片抽不到帧（文件被移动/占用/已删）→ 直接报错更有用，
            #    不要在后面 `row[0]` 处才炸出 IndexError，看不出是哪支的问题。
            raise SystemExit("「%s」抽不到帧，文件可能已移动或被占用：%s"
                             % (k, dict(items).get(k)))
        r = row[:PER_ROW] + [np.zeros_like(row[0])] * max(0, PER_ROW - len(row))
        fixed.append(r)
    W = max(row_w(r) for r in fixed)
    blocks = [fit_row(r, W) for r in fixed]
    stack = []
    for i, b in enumerate(blocks):
        if i:
            stack.append(np.full((14, b.shape[1], 3), 50, np.uint8))
        stack.append(b)
    cv2.imwrite(out, np.vstack(stack))
    print("对比图: " + out)
    for k, row in items:
        print("  %-10s %d 帧" % (k, len(row)))


if __name__ == "__main__":
    main()
