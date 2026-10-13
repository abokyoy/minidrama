# -*- coding: utf-8 -*-
r"""
成片后期调色：解决「偏黑 / 人物阴影过重 / 没有柔和感」。

为什么走后期而不是继续调提示词：
  实测过三轮，提示词写满 "BRIGHT / NOT dark / LOW shadow density"、
  场景参考图也从中位 77 提到 155，t02 的 mean 只从 99.6 动到 101.4 ——
  **H3 这条工作流本身就往高对比暗调走**，提示词推不动它。
  与其和模型较劲，不如做一次确定性的调色：立竿见影，而且能**直接救回已经生成的片段**。

调色曲线（一段式，无二次测量）：
  黑位  0.00 → 0.16   （把 p05 从 ~6 抬到 ~47，暗部不再压死 = 用户说的"阴影过重"）
  四分之一 0.25 → 0.42
  中间调 0.50 → 0.62  （med 从 ~99 抬到 ~136）
  亮部 0.75 → 0.83
  白点 1.00 → 1.00    （保留最高光，不做成一片灰）
  再叠一点暖色偏移，去掉画面里那层偏冷/偏青的调子。

产物：原片先备份到 D:\output\_raw\，然后在**原地**输出调色后的 mp4（含音轨的那份是交付件，
同时也是链式生成的参考视频 —— 所以调色后的片子会把"越接越黑"一起压住）。
PNG 预览用调色后视频的首帧重新生成，保证"量到的亮度 = 成片的亮度"。

用法：
  python _grade.py <mp4 或 -audio.mp4> [...]
  python _grade.py --dir D:\output          # 处理目录下所有成片
  python _grade.py --no-backup <mp4>        # 不备份（已经在 _raw 里了）
"""
import glob
import os
import shutil
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
# 与 gen_worker 保持一致：可用 MINIDRAMA_OUT 覆盖。两处不同步会调错文件。
OUT_DIR = os.environ.get("MINIDRAMA_OUT", r"D:\output")
RAW_DIR = os.path.join(OUT_DIR, "_raw")

# ══════════════════════════════════════════════════════════════════════
# 2026-10-04 18:35 用户反馈：「本地颜色总是像蒙了一层灰，Seedance 有种高清清亮的感觉」
#
# ⭐ 我用 _grade_cmp.py 量了三方数据，结论是**我自己的调色就是元凶**：
#
#              原片      旧调色后   Seedance
#   黑位 p01   13.0   →   49.8      10.9
#   对比度    187.4   →  156.7     171.2
#   动态范围  227.0   →  191.9     210.6
#
# 旧曲线 CURVE="0/0.16 ..." 把**纯黑抬到 16% 灰**（实测 p01 从 13 抬到 50）。
# 这在摄影术语里就叫「抬黑位 / lifted blacks」，观感正是「蒙了一层灰」——
# 阴影里全是灰雾，黑不下去，所以整体发闷。
#
# 而且 H3 **原片其实比 Seedance 更通透**（对比度 187 vs 171，动态范围 227 vs 211）。
# 早上我把「偏暗、阴影重」误判成需要提黑位，实际那是**该保住的对比**，
# 提黑位只会把「偏暗」变成「蒙灰」，越修越糟。
#
# → 新曲线：**不抬黑位**，只做轻微 S 形对比拉伸 + 提中调 + 补一点饱和度。
#   目标值：对齐 Seedance（黑位 ~11、对比度 ~171），而不是"越亮越好"。
# ══════════════════════════════════════════════════════════════════════

# 档位：clean = 当前上线（去灰、通透）；legacy = 旧曲线（留作对照，别用）
GRADE_PROFILES = {
    "clean": {
        # 0.0→0.02  黑位基本不动（Seedance p01=10.9，16 灰是蒙灰主因）
        # 0.25→0.235 轻微压一点，制造 S 形
        # 0.5→0.55  中调提亮（原片 p50=113.6，Seedance 119.2）
        # 0.75→0.80  亮部跟进
        # 1.0→1.0    白点保留
        "curve": "0/0.02 0.25/0.235 0.5/0.55 0.75/0.80 1/1",
        # 饱和度补到 1.12：H3 直出偏淡，补一点让肤色/木色/"清亮感"回来
        "sat": "1.12",
        # 轻微锐化（unsharp 是"高清感"的一半来源）
        "sharp": "5:5:0.6:5:5:0.0",
    },
    "legacy": {
        "curve": "0/0.16 0.25/0.42 0.5/0.62 0.75/0.83 1/1",
        "sat": "1.05",
        "sharp": None,
    },
}
GRADE = GRADE_PROFILES["clean"]


def build_vf(profile):
    vf = "curves=all='%s'" % profile["curve"]
    if profile.get("sharp"):
        vf += ",unsharp=%s" % profile["sharp"]
    vf += ",eq=saturation=%s" % profile["sat"]
    # 极轻微的暖色偏移，去掉画面偏冷/偏青的调子（不清灰）
    vf += ",colorbalance=rs=0.03:bs=-0.03"
    return vf


VF = build_vf(GRADE)
# 兼容旧调用点（旧代码直接 import CURVE）
CURVE = GRADE["curve"]

# 音轨那份就是交付件
AUDIO_SUFFIX = "-audio.mp4"


def ffmpeg(args, timeout=1800):
    r = subprocess.run([FFMPEG, "-y", "-v", "error"] + args,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    return r.returncode, (r.stderr or "").strip()


def grade_one(path, backup=True):
    """调色一个 mp4（原地替换）。"""
    if not os.path.exists(path):
        return "缺失"
    name = os.path.basename(path)
    if backup:
        os.makedirs(RAW_DIR, exist_ok=True)
        dst = os.path.join(RAW_DIR, name)
        if not os.path.exists(dst):
            shutil.copy2(path, dst)
    tmp = path + ".graded.mp4"
    has_audio = name.endswith(AUDIO_SUFFIX)
    args = ["-i", path, "-vf", VF, "-c:v", "libx264", "-crf", "16",
            "-preset", "veryfast", "-pix_fmt", "yuv420p"]
    args += ["-c:a", "copy"] if has_audio else ["-an"]
    args += ["-movflags", "+faststart", tmp]
    rc, err = ffmpeg(args)
    if rc != 0 or not os.path.exists(tmp) or os.path.getsize(tmp) < 10000:
        return "失败: %s" % err[-200:]
    os.replace(tmp, path)
    return "OK"


def refresh_png(audio_mp4):
    """用调色后视频的首帧重建预览 PNG，保证"量到的亮度 = 成片的亮度"。"""
    png = audio_mp4.replace(AUDIO_SUFFIX, ".png")
    tmp = png + ".tmp.png"
    rc, err = ffmpeg(["-i", audio_mp4, "-frames:v", "1", tmp], timeout=300)
    if rc == 0 and os.path.exists(tmp):
        os.replace(tmp, png)
        return "OK"
    return "失败: %s" % err[-120:]


def targets(d):
    fs = [p for p in glob.glob(os.path.join(d, "*.mp4"))
          if not p.endswith("-audio.mp4") and ".graded." not in p
          and os.path.dirname(p) == d]
    return sorted(fs)


def main():
    raw = sys.argv[1:]
    backup = "--no-backup" not in raw
    pos = [a for a in raw if not a.startswith("--")]
    if "--dir" in raw:
        d = pos[0] if pos else OUT_DIR
        vids = targets(d)
    elif pos and os.path.isdir(pos[0]):
        vids = targets(pos[0])
    elif pos:
        vids = pos
    else:
        vids = targets(OUT_DIR)

    if not vids:
        print("没有要处理的 mp4")
        return 0
    t0 = time.time()
    ok = bad = 0
    for v in vids:
        a = v.replace(".mp4", AUDIO_SUFFIX)
        r1 = grade_one(v, backup)
        r2 = grade_one(a, backup) if os.path.exists(a) else "跳过"
        r3 = refresh_png(a) if os.path.exists(a) else "跳过"
        flag = "OK" if (r1 == "OK" and r2 in ("OK", "跳过")) else "!!"
        if flag == "OK":
            ok += 1
        else:
            bad += 1
        print("%s %-34s video=%s audio=%s png=%s"
              % (flag, os.path.basename(v), r1, r2, r3))
    print("\n处理 %d 个文件，成功 %d，失败 %d，用时 %.1f 秒" % (len(vids), ok, bad, time.time() - t0))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
