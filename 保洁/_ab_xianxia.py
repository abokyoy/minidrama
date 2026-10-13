# -*- coding: utf-8 -*-
"""修仙段 v1 vs v2 对比：同一套指标，量化「提示词瘦身+补运镜」到底有没有用。

用法：
    "C:/Users/86134/.workbuddy/binaries/python/envs/default/Scripts/python.exe" \
        _ab_xianxia.py "D:/output_h3off/off_xs90_t01_00001-audio.mp4" \
                       "D:/output_h3off/off_xs90_t01_00002-audio.mp4"

⚠️ 必须抽帧拼图**人眼看**人数与动作，指标只给客观量。
指标说明：
  清晰度   = 拉普拉斯方差，越高越锐（提示词变短后动作细节是否更实）
  运动量   = 帧间差分均值，越高动作越猛（打斗是否真的动起来）
  色彩数   = 独特色数，越高特效层次越丰富
  亮度/饱和 = 基础观感
"""
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

# OpenCV 读不了中文路径 → 全部拷到纯 ASCII 临时目录
TMP = r"C:\Users\86134\AppData\Local\Temp\h3ab"
os.makedirs(TMP, exist_ok=True)


def probe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", path],
        capture_output=True, text=True)
    import json
    j = json.loads(r.stdout)
    v = j["streams"][0]
    return (float(j["format"]["duration"]),
            int(v["width"]), int(v["height"]),
            int(j["format"]["size"]))


def metrics(path, tag):
    """抽 20 帧算指标 + 出缩略图拼图。"""
    ascii_mp4 = os.path.join(TMP, tag + ".mp4")
    shutil.copy2(path, ascii_mp4)

    cap = cv2.VideoCapture(ascii_mp4)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    step = max(1, n // 20)
    frames, idx = [], []
    i = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i % step == 0 and len(frames) < 20:
            frames.append(f)
            idx.append(i)
        i += 1
    cap.release()

    sharp, motion = [], []
    for k in range(1, len(frames)):
        g1 = cv2.cvtColor(frames[k - 1], cv2.COLOR_BGR2GRAY)
        g2 = cv2.cvtColor(frames[k], cv2.COLOR_BGR2GRAY)
        sharp.append(cv2.Laplacian(g2, cv2.CV_64F).var())
        motion.append(np.abs(g2.astype(np.float32) - g1.astype(np.float32)).mean())
    hsv = [cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in frames]
    bright = [h[:, :, 2].mean() for h in hsv]
    sat = [h[:, :, 1].mean() for h in hsv]
    colors = len(set(
        tuple(frames[k][::7, ::7].reshape(-1, 3)[c].tolist())
        for k in range(len(frames)) for c in range(0, 40, 3)))

    dur, w, h, size = probe(path)

    # 缩略图拼图：5 列 x 4 行
    th = []
    for f in frames:
        t = cv2.resize(f, (w // 3, h // 3))
        cv2.putText(t, "f%02d" % len(th), (6, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
        cv2.putText(t, "f%02d" % len(th), (6, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        th.append(t)
    cols, rows = 5, (len(th) + 4) // 5
    sheet = np.zeros((rows * th[0].shape[0], cols * th[0].shape[1], 3),
                     np.uint8)
    for k, t in enumerate(th):
        r, c = divmod(k, cols)
        sheet[r * t.shape[0]:(r + 1) * t.shape[0],
              c * t.shape[1]:(c + 1) * t.shape[1]] = t
    sheet_path = os.path.join(TMP, tag + "_sheet.jpg")
    cv2.imwrite(sheet_path, sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])

    return {
        "文件": os.path.basename(path),
        "大小": "%.2f MB" % (size / 1048576),
        "时长": "%.1fs" % dur,
        "分辨率": "%dx%d" % (w, h),
        "帧数": n,
        "清晰度": np.mean(sharp),
        "运动量": np.mean(motion),
        "运动峰值": np.max(motion),
        "独特色数": colors,
        "亮度": np.mean(bright),
        "饱和": np.mean(sat),
        "拼图": sheet_path,
    }


def main():
    paths = [p for p in sys.argv[1:] if p.lower().endswith(".mp4")]
    if not paths:
        print("用法: _ab_xianxia.py v1.mp4 [v2.mp4]")
        return
    rows = []
    for k, p in enumerate(paths):
        if not os.path.exists(p):
            print("跳过（不存在）: %s" % p)
            continue
        rows.append(metrics(p, "v%d" % (k + 1)))
    if len(rows) < 1:
        return
    keys = list(rows[0].keys())
    print("=" * 78)
    print(" 修仙段 v1 vs v2 对比")
    print("=" * 78)
    print("%-10s %26s %26s %14s" % ("指标", rows[0]["文件"][:24],
                                     rows[1]["文件"][:24] if len(rows) > 1 else "-",
                                     "变化"))
    print("-" * 78)
    for k in keys:
        if k == "拼图":
            continue
        a = rows[0][k]
        if len(rows) > 1:
            b = rows[1][k]
            d = ""
            if isinstance(a, float) and isinstance(b, float):
                if a:
                    d = "%+.1f%%" % ((b - a) / a * 100)
            elif a != b:
                d = "变化"
            print("%-10s %26s %26s %14s" % (k, a, b, d))
        else:
            print("%-10s %26s" % (k, a))
    print("-" * 78)
    for r in rows:
        print("拼图: %s" % r["拼图"])
    print("\n⛔ 指标只给客观量。**必须打开拼图人眼看**：")
    print("   ① 剑雨/御剑术有没有真的画出来  ② 有没有人物复制")
    print("   ③ 动作是不是有起手-交锋-收势（还是每帧都在糊）")


if __name__ == "__main__":
    main()
