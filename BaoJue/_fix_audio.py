# -*- coding: utf-8 -*-
"""人声清晰度后期修复（不占显存、不需要重跑）。

问题根因：H3 音频 VAE 输出是 32000 Hz，语音清晰度主要在 3–8kHz，
32k 采样率（Nyquist 16kHz）把这一段砍掉一半 → 人声发闷、齿音丢失。
Seedance 是 44100 Hz。

本脚本做四件事（都是无损重采样 + 温和增强，不改画面）：
  ① 重采样到 48000 Hz（SoX 高质量算法）
  ② 轻度降噪（只压静态底噪，不伤人声）
  ③ 齿音/清晰度带提升（3–8kHz 提升 2dB，Q=1.2，温和）
  ④ 响度归一到 -16 LUFS（短剧平台的通用标准）

用法：
  python _fix_audio.py ep01_t62_00001.mp4          # 处理单个
  python _fix_audio.py --batch ep001               # 批量处理已完成的段
  python _fix_audio.py --batch ep001 --dry        # 只看会处理哪些
"""
import glob
import os
import re
import shutil
import subprocess
import sys

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"E:\Program Files\ffmpeg\bin\ffprobe.exe"
OUT = "D:/output"
TMP_SUFFIX = "_afix"


def build_filter():
    """人声清晰度滤镜链。参数都是温和值，宁可少做也不要做坏。"""
    parts = [
        # ① 高质量重采样到 48kHz
        "aresample=48000:resampler=soxr:precision=28",
        # ② 温和降噪：只压窄带静态底噪，n=-18dB 属于轻处理
        "afftdn=nr=12:nf=-30:tn=1",
        # ③ 清晰度带：3-8kHz 提升，人声的关键频段
        "equalizer=f=5200:t=q:w=1.4:g=2.2",
        # ④ 一点点高频空气感
        "equalizer=f=9000:t=q:w=1.2:g=1.2",
        # ⑤ 响度归一 -16 LUFS（短剧平台通用）
        "loudnorm=I=-16:TP=-1.5:LRA=11",
    ]
    return ",".join(parts)


def fix_one(src, dry=False):
    # 输入通常是 "<seg>_00001-audio.mp4"；成片沿用同样的命名规则，
    # 不能变成 "...-audio-audio.mp4"（踩过一次）
    stem = re.sub(r"-audio$", "", os.path.splitext(src)[0])
    dst = stem + TMP_SUFFIX + ".mp4"
    if dry:
        print("  将处理：%s  →  %s-audio.mp4"
              % (os.path.basename(src), os.path.basename(stem)))
        return stem + "-audio.mp4"
    vf = build_filter()
    # 画面直接 copy（不重编码，画面零损失），只重做音频
    cmd = [FFMPEG, "-v", "error", "-y", "-i", src,
           "-map", "0:v:0", "-c:v", "copy",
           "-map", "0:a:0", "-af", vf,
           "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
           "-movflags", "+faststart", dst]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or not os.path.exists(dst):
        print("  失败：%s\n    %s" % (os.path.basename(src), (r.stderr or "")[:200]))
        return None
    new_audio = stem + "-audio.mp4"
    if os.path.exists(new_audio):
        os.remove(new_audio)
    shutil.move(dst, new_audio)
    print("  完成：%s  %.1f MB" % (os.path.basename(new_audio),
                                  os.path.getsize(new_audio) / 1e6))
    return new_audio


def _sample_rate(path):
    """读文件的音频采样率；读不到返回 0。"""
    r = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate", "-of", "csv=p=0", path],
        capture_output=True, text=True, timeout=60)
    try:
        return int((r.stdout or "0").strip().split("\n")[0])
    except (ValueError, IndexError):
        return 0


def collect(ep):
    """收集待修复的成片。

    两个坑（都踩过）：
      ① 输出文件前缀是 `ep01_t*`，不是 `ep001_t*`——按集号直接拼前缀会一个都匹配不到。
      ② 生成器会把历史段挪进 `_raw/`，只扫根目录会漏掉大部分已完成的段。
    所以这里两个目录都扫，再按段号去重（同一段在两边都有时优先根目录，那是当前版本）。
    """
    pat = "ep%s_t*_00001-audio.mp4" % re.sub(r"\D", "", ep)[-2:]
    picked = {}
    for sub in ("", "_raw"):
        for f in glob.glob(os.path.join(OUT, sub, pat)):
            m = re.search(r"_t(\d+)_", os.path.basename(f))
            if not m:
                continue
            n = int(m.group(1))
            if n not in picked or sub == "":
                picked[n] = f
    return [picked[k] for k in sorted(picked)]


def batch(ep, dry=False, force=False):
    files = collect(ep)
    print("=" * 60)
    print(" 音频修复 %s：%d 段待查" % (ep, len(files)))
    print("=" * 60)
    if not files:
        print("（没有找到已完成的段）")
        return
    ok = 0
    skip = 0
    for i, f in enumerate(files, 1):
        if os.path.getsize(f) < 200000:
            continue
        # 幂等：已经是 48kHz 的跳过，重复跑不会二次降质（二次 loudnorm 会再压一次动态）
        if not force and _sample_rate(f) >= 48000:
            skip += 1
            continue
        print(" [%d/%d] %s" % (i, len(files), os.path.basename(f)))
        if fix_one(f, dry):
            ok += 1
    print("\n成功 %d 段，跳过（已是 48kHz）%d 段" % (ok, skip))
    if not dry:
        print("提示：原始无音轨的 ep*_t*_00001.mp4 保持不动，成片请用 -audio 那条")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--batch" in sys.argv:
        ep = sys.argv[sys.argv.index("--batch") + 1]
        batch(ep, "--dry" in sys.argv, "--force" in sys.argv)
    else:
        for a in sys.argv[1:]:
            if a.endswith(".mp4"):
                fix_one(a, "--dry" in sys.argv)
