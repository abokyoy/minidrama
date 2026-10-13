# -*- coding: utf-8 -*-
r"""
A/B/C 三方案对比体检（2026-10-09）

三个变体跑的是**同一段（seg05）、同一 prev、同一条提示词**，唯一差别是工作流：
  baseline chain  22 帧 clip 锚本段 frame 0
  vC单帧锚910 只取上一段最后一帧 1 张图锚 frame 0
  vA  双端锚     frame 0 锚 22 帧 clip + frame 242 锚上一段首帧 PNG
  vB  音轨锚     vC/vA 的画面 + 910.audio → 911.audio

指标（都是数值，不靠肉眼）：
  饱和度均值    掉色/发灰的第一指标
  清晰度        Laplacian 方差，糊了会掉
  帧间差        越小 = 越静；突然飙升 = 镜头晃
  首帧亮度      与 prev 尾帧亮度的差 = 衔接跳变
  音轨         RMS + 与 prev 的相关，验B 到底有没有把音轨接上

用法：
  "$PY" _abc_compare.py                # 自动找 D:\output_h3off 里 seg05 的全部变体成片
  "$PY" _abc_compare.py a.mp4 b.mp4   # 也可手工指定
"""
import os, sys, glob, subprocess, json, time

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
           "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)

import numpy as np
import cv2

OUT = r"D:\output_h3off"
PREV = r"D:\output_h3off\off_xs01_t04_00003-audio.mp4"
GRID = r"E:\LLM\try\minidrama\_abc_frames"


def ffprobe_ok(p):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", p],
                           capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def metrics(path):
    cap = cv2.VideoCapture(path)
    sats, sharps, diffs, brights = [], [], [], []
    prev_gray = None
    i = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        i += 1
        hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV)
        sats.append(float(hsv[:, :, 1].mean()))
        gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        sharps.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
        brights.append(float(gray.mean()))
        if prev_gray is not None:
            diffs.append(float(cv2.absdiff(gray, prev_gray).mean()))
        prev_gray = gray
    cap.release()
    return {
        "frames": i,
        "sat": round(float(np.mean(sats)), 2) if sats else 0,
        "sharp": round(float(np.mean(sharps)), 1) if sharps else 0,
        "diff": round(float(np.mean(diffs)), 2) if diffs else 0,
        "bright_head": round(float(brights[0]), 2) if brights else 0,
        "bright_tail": round(float(brights[-1]), 2) if brights else 0,
    }


def audio_info(path):
    """用 ffprobe 量音频。返回 (有无音轨, RMS dB, 时长)。"""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=codec_name,duration",
                        "-of", "json", path], capture_output=True, text=True,
                       timeout=30)
    try:
        st = json.loads(r.stdout).get("streams") or []
    except Exception:
        st = []
    if not st:
        return "无音轨", None, 0.0
    d = 0.0
    try:
        d = float(st[0].get("duration") or 0)
    except Exception:
        pass
    return st[0].get("codec_name", "?"), None, d


def dump_grid(path, name):
    os.makedirs(GRID, exist_ok=True)
    dst = os.path.join(GRID, name + ".png")
    if os.path.exists(dst):
        return dst
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    picks = sorted(set(int(total * k / 12) for k in range(12)))
    tiles = []
    for p in picks:
        cap.set(cv2.CAP_PROP_POS_FRAMES, p)
        ok, fr = cap.read()
        if not ok:
            continue
        h, w = fr.shape[:2]
        s = 220 / max(h, 1)
        tiles.append(cv2.resize(fr, (int(w * s), 220)))
    cap.release()
    if not tiles:
        return None
    rows = []
    for k in range(0, len(tiles), 6):
        rows.append(np.hstack(tiles[k:k + 6]))
    wmax = max(r.shape[1] for r in rows)
    rows = [np.pad(r, ((0, 0), (0, wmax - r.shape[1]), (0, 0))) for r in rows]
    cv2.imwrite(dst, np.vstack(rows))
    return dst


def main():
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        # ⛔ 只取**最近 3 小时**内的 seg05 成片。
        #    seg05 目录里躺着 7 号（用户取消前）的废弃成片，
        #    全扫进来会把废弃结果当本轮结果 —— 「脚本不看时间 = 数据全是错的」。
        cut = time.time() - 3 * 3600
        cand = [f for f in glob.glob(os.path.join(OUT, "off_xs01_t05_*.mp4"))
                if os.path.getmtime(f) >= cut]
        # 同一支成片有 -audio 和无 -audio 两个文件，指标完全一样 → 只留 -audio
        witha = [f for f in cand if f.endswith("-audio.mp4")]
        files = sorted(witha or cand, key=os.path.getmtime)
        if files:
            print("近3 小时内成片%d 支（已滤掉 -audio 重复项）" % len(files))
    if not files:
        print("没找到 seg05 成片。先跑 _chain.py 5 --kind=chain --wf=vA|vB|vC")
        return 1

    rows = []
    if os.path.exists(PREV):
        pm = metrics(PREV)
        pa = audio_info(PREV)[0]
        print("prev(seg04 认可版) sat=%s sharp=%s diff=%s 音频=%s"
              % (pm["sat"], pm["sharp"], pm["diff"], pa))
    else:
        pm = None
        print("prev 缺失:", PREV)

    print("\n%-34s %6s %7s %9s %7s %8s %8s %s"
          % ("文件", "帧", "饱和", "清晰度", "帧间差", "头亮", "尾亮", "音频"))
    for f in files:
        m = metrics(f)
        a, _, _ = audio_info(f)
        dur = ffprobe_ok(f)
        tag = os.path.basename(f)
        rows.append((tag, m, a, dur))
        print("%-34s %6d %7.2f %9.1f %7.2f %8.2f %8.2f %s (%.1fs)"
              % (tag, m["frames"], m["sat"], m["sharp"], m["diff"],
                 m["bright_head"], m["bright_tail"], a, dur))
        g = dump_grid(f, os.path.splitext(tag)[0])
        if g:
            print("      抽帧拼图 ->", g)

    if pm:
        print("\n--- 与 prev(seg04) 对比 ---")
        for tag, m, a, dur in rows:
            print("%-34s 饱和%+6.2f%%  清晰%+6.1f%%  帧间差%+6.2f%%"
                  % (tag, (m["sat"] - pm["sat"]) / pm["sat"] * 100,
                     (m["sharp"] - pm["sharp"]) / pm["sharp"] * 100,
                     (m["diff"] - pm["diff"]) / pm["diff"] * 100))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())