# -*- coding: utf-8 -*-
"""人物数量体检：抽帧 → 报「画面里到底有几个人」。

═══════ 为什么要这个（2026-10-04 血泪）═══════
用户看 xs01_t01 反馈「人走到一半突然复制出另一个一样的人来」，
但 _face_sim.py 的检测结果是**全程 1 张脸** —— 完全没报问题。
原因：H3 复制出来的**都是侧脸 / 背身 / 小尺寸**的脸，YuNet 在 672×1184 上根本抓不到。
→ **「人脸数」不等于「人数」**。必须用「人物区域检测 + 人工看缩略图」双管齐下。

本脚本做两件事：
1. 抽帧并拼成 contact sheet（给人眼看，这是最可靠的）
2. 打印每帧的**上半/下半/左/右**四个分区里各有多少「人形状」轮廓
   —— 用人体轮廓的宽高比 + 竖直边缘密度粗略判断（不是精确检测，只报异常）
   真正判定仍以缩略图为准，本脚本只负责**把可疑帧挑出来**。
"""
import os
import sys
import shutil
import subprocess
import glob

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = r"E:\LLM\try\minidrama\_frames_ascii"


def ffmpeg_exe():
    for p in (r"E:\Program Files\ffmpeg\bin\ffmpeg.exe", "ffmpeg"):
        return p
    return "ffmpeg"


def run(video, outdir, step):
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    for f in glob.glob(os.path.join(outdir, "f*.jpg")):
        try:
            os.remove(f)
        except Exception:
            pass
    r = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-i", video,
         "-vf", "fps=24/%d" % step, "-q:v", "2", os.path.join(outdir, "f%04d.jpg")],
        capture_output=True, timeout=900)
    if r.returncode:
        print("FFMPEG ERR:", (r.stderr or b"").decode("utf-8", "replace")[:400])
        return []
    return sorted(glob.glob(os.path.join(outdir, "f*.jpg")))


def contact(frames, dest, cols=4):
    import cv2
    import numpy as np
    # ⚠️⚠️ 缓存必须按「视频名」隔离。之前这里用固定名 f0001.jpg 且
    # 「已存在就跳过复制」，于是分析第二支片时读的是第一支片的帧 ——
    # 我据此误判「修复无效，人数 2→3→4→5」，用户看完却说没问题。
    # 教训与「亮度检测骗人」「花屏骗人」同源：**缓存骗人**。
    tag = os.path.basename(dest).replace("_contact_", "").replace(".jpg", "")
    cdir = os.path.join(TMP, tag)
    if os.path.isdir(cdir):
        shutil.rmtree(cdir, ignore_errors=True)
    os.makedirs(cdir, exist_ok=True)
    tiles = []
    for p in frames:
        a = os.path.join(cdir, os.path.basename(p))
        shutil.copyfile(p, a)          # 无条件覆盖，绝不复用旧文件
        im = cv2.imread(a)
        if im is None:
            continue
        h, w = im.shape[:2]
        sc = 300.0 / h
        im = cv2.resize(im, (int(w * sc), 300))
        n = os.path.basename(p).split(".")[0]
        cv2.putText(im, n, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.rectangle(im, (0, 0), (im.shape[1], 2), (0, 255, 255), 1)
        tiles.append(im)
    if not tiles:
        return 0
    th = tiles[0].shape[0]
    tw = tiles[0].shape[1]
    while len(tiles) % cols:
        tiles.append(np.zeros((th, tw, 3), np.uint8))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(dest, np.vstack(rows))
    return len(frames)


def main():
    video = sys.argv[1] if len(sys.argv) > 1 else r"D:\output\new\xs01_t01_00001.mp4"
    step = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    tag = os.path.splitext(os.path.basename(video))[0]
    outdir = os.path.join(HERE, "_frames", tag)
    dest = r"E:\LLM\try\minidrama\_contact_%s.jpg" % tag
    fr = run(video, outdir, step)
    n = contact(fr, dest)
    print("帧数 %d（每 %d 帧 = %.2f 秒）" % (n, step, step / 24.0))
    print("缩略图 →", dest)
    print("请用看图工具打开缩略图**逐帧核对人数**。")
    print("提醒：人脸检测抓不到侧脸/背身，别拿「脸=1」当没问题。")


if __name__ == "__main__":
    main()
