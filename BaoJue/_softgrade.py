# -*- coding: utf-8 -*-
r"""把成片调成 Seedance 的质感：柔和 + 一点点滤镜的美感。

═══════════════════════════════════════════════════════════════════════
这一版和 _grade.py 的区别（_grade.py 已成历史，别再用）
═══════════════════════════════════════════════════════════════════════
_grade.py 用一条**手写**曲线 `0/0.16 0.25/0.42 ...`，靠"猜"来调。
结果两个坏毛病：
  · 抬的是**黑位**（p05 → 47），画面蒙灰，用户骂"蒙了一层灰"
  · 局部对比 14.5（Seedance 只有 9.2），画面又硬又艳，没质感

本版三步走，全自动，先测后调再验：

  ① MEASURE  抽 12 帧，量 5 个分位数（p01/p05/p25/p50/p75/p95/p99）+ 饱和度
  ② SOLVE    把这 7 个点当锚点，用**保序单调三次插值**拟合出一条曲线，
             端点固定 (0, 目标 p01) 和 (255, 目标 p99)。
             锚点目标全部来自 Seedance 实测值，不是拍脑袋。
  ③ VERIFY   调完再量一次，对比 Seedance，输出偏差表；超差就再迭代一轮。

为什么能在**不重新生成**的前提下改出 Seedance 质感：
  画面明暗关系是可逆的映射。lean 原片的问题是「中间调压太狠、高光顶太狠、
  饱和度过高」—— 这三样都是**像素值层面的**，后期能全部拉回来。
  后期改不了的只有「构图乱 / 剧情看不懂 / 人物复制」这类语义问题。

滤镜感从哪来（Seedance 的实际做法，也是本版复刻的）：
  · **降饱和**到 61.7（lean 是 80.6，艳得发假）
  · **高光 roll-off**：p99 压到 212（Seedance 212.6），让白色是柔白不是死白
  · **中间调抬起**：p25 抬到 71.7（lean 只有 34.5–49），这是"柔和"的关键
  · **暗部不死**：p05 停在 20（不回到 0，也不抬到 47 的蒙灰区）
  → 合起来就是「中间调饱满 + 暗部通透 + 高光柔白 + 色彩收敛」的胶片感

用法：
  python _softgrade.py --dir D:\output\new          # 整个目录
  python _softgrade.py a.mp4 b.mp4                  # 指定文件
  python _softgrade.py --dry a.mp4                   # 只测量不改
  python _softgrade.py --iter 3 --dir D:\output\new # 迭代收敛（默认 2）
"""
import glob
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"E:\Program Files\ffmpeg\bin\ffprobe.exe"
TMP = r"C:\Users\86134\.workbuddy\tmp\softgrade"
PY = sys.executable

# ══════════════════════════════════════════════════════════════════
# Seedance 实测目标值（2026-10-04，_soft_cmp.py 从 4 支样片量出来）
# 亮度是 Rec.601 灰度，0-255
# ══════════════════════════════════════════════════════════════════
TARGET = dict(p01=9.6, p05=20.1, p25=71.7, p50=112.5,
              p75=150.4, p95=188.8, p99=212.6, sat=61.7,
              local=9.24, contrast=168.7, dyn=203.0)

KEYS = ["p01", "p05", "p25", "p50", "p75", "p95", "p99"]

NF = 12          # 抽帧数
ITER = 2         # 迭代轮数


# ─────────────────────────── ① 测量 ───────────────────────────
def probe_size(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", path],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    try:
        w, h = r.stdout.strip().split(",")[:2]
        return int(w), int(h)
    except Exception:
        return 672, 1184


def measure(path, tag):
    """抽 NF 帧量分位数 + 饱和度。中文路径先拷成 ASCII 名（OpenCV 5 坑）。"""
    import numpy as np
    import cv2

    # ⚠️ tag 必须是**纯 ASCII**。OpenCV 读不出中文路径、ffmpeg 输出模板带非 ASCII
    #    也会静默抽不出帧 → acc 为空 → `ZeroDivisionError: division by zero`。
    #    踩过两次：① tag 由文件名切片拼出来含 "()" 和中文
    #              ② 用 `c.isalnum()` 过滤 —— ⚠️ 它对**中文返回 True**，滤不掉！
    ASCII = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    tag = "".join(c if c in ASCII else "_" for c in tag)[:28] or "x"

    os.makedirs(TMP, exist_ok=True)
    ascii_mp4 = os.path.join(TMP, tag + ".mp4")
    shutil.copy2(path, ascii_mp4)
    for p in glob.glob(os.path.join(TMP, tag + "_f*.png")):
        try:
            os.remove(p)
        except OSError:
            pass
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", ascii_mp4,
                    "-vf", "fps=%d" % NF,
                    os.path.join(TMP, tag + "_f%03d.png")], check=False)

    frames = sorted(glob.glob(os.path.join(TMP, tag + "_f*.png")))
    if not frames:
        raise SystemExit("抽帧失败: " + path)

    acc = []
    for f in frames:
        im = cv2.imread(f, cv2.IMREAD_COLOR)
        if im is None:
            continue
        b, g, r = im[:, :, 0].astype("f4"), im[:, :, 1].astype("f4"), im[:, :, 2].astype("f4")
        y = 0.114 * b + 0.587 * g + 0.299 * r
        sat = float(cv2.cvtColor(im, cv2.COLOR_BGR2HSV)[:, :, 1].mean())

        # ★ 局部对比：16x16 块内标准差的均值 —— 这才是「硬邦邦」的量化指标。
        #   全局对比(p95-p05)大但局部小 = 通透；两个都大 = 又黑又硬。
        #   Seedance 实测 9.24，lean 原片 13.9~16.1。
        h, w = y.shape
        bh, bw = h // 16 * 16, w // 16 * 16
        blocks = y[:bh, :bw].reshape(bh // 16, 16, bw // 16, 16).transpose(0, 2, 1, 3)
        local = float(blocks.reshape(-1, 256).std(axis=1).mean())

        acc.append((np.percentile(y, [1, 5, 25, 50, 75, 95, 99]), sat, local))

    n = len(acc)
    if n == 0:
        # 静默崩掉（ZeroDivisionError）会让人以为是数据问题，实际是抽帧失败
        raise SystemExit("抽到 0 帧，tag=%s  path=%s" % (tag, path))
    q = [sum(a[0][i] for a in acc) / n for i in range(7)]
    out = dict(zip(KEYS, q))
    out["sat"] = sum(a[1] for a in acc) / n
    out["local"] = sum(a[2] for a in acc) / n
    out["contrast"] = out["p95"] - out["p05"]
    out["dyn"] = out["p99"] - out["p01"]
    return out


# ─────────────────────── ② 求解曲线 ───────────────────────
def solve_curve(cur, it=0):
    """按当前测量值 → Seedance 目标，生成 33 点单调曲线（直方图匹配）。

    ⚠️ 两次踩坑，都写在这里防止重蹈：
      ① 控制点的 **x 必须是「当前实测的像素值」**，不是 p50 的序号位置 0.5。
         误用序号位置 → 整条曲线压暗 17%（实测 p99 被压到 179，目标 212）。
      ② 只用 7 个锚点不够准：ffmpeg 的 curves 在锚点之间是**样条插值**，
         p25(49→72) 和 p50(91→113) 之间的实际映射会"鼓"出去。
         → 改用 33 个锚点（每 8 个灰阶一个），并对每个 x 做线性查找求 y。

    it>0 表示已迭代若干轮，按剩余差值的 80% 修正（留余量，防过冲）。
    """
    # 33 个输入点：0, 8, 16, ... 248, 255
    xs = [i * 255.0 / 32.0 for i in range(33)]

    # 锚点：(当前分位值, 目标分位值)
    anchors = []
    for k in KEYS:
        want, have = TARGET[k], cur[k]
        goal = want if it == 0 else have + (want - have) * 0.85
        anchors.append((max(0.0, min(255.0, have)), goal))

    # 两端：0 → p01 目标；255 → p99 目标（高光 roll-off，这是"柔和"的关键）
    anchors = [(0.0, TARGET["p01"])] + anchors + [(255.0, TARGET["p99"])]
    # 保序（分位值本身单调，但修正后会破序）
    fixed = [anchors[0]]
    for x, y in anchors[1:]:
        if y < fixed[-1][1] + 0.3:
            y = fixed[-1][1] + 0.3
        fixed.append((x, min(255.0, y)))
    anchors = fixed

    # 逐点线性插值出 33 点曲线
    ys = []
    for x in xs:
        if x <= anchors[0][0]:
            ys.append(anchors[0][1]); continue
        if x >= anchors[-1][0]:
            ys.append(anchors[-1][1]); continue
        for i in range(1, len(anchors)):
            x0, y0 = anchors[i - 1]
            x1, y1 = anchors[i]
            if x0 <= x <= x1:
                t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
                ys.append(y0 + (y1 - y0) * t)
                break

    cs = " ".join("%s/%.4f" % (x / 255.0, y / 255.0) for x, y in zip(xs, ys))
    return cs, ys


def build_vf(curve, cur_sat, local=None, it=0):
    """调色滤镜链：曲线（定调子） + 降饱和（收敛色彩）+ 柔化（降局部对比）+ 轻微暖偏移。

    ★ 局部对比是「硬邦邦」的主因，而**全局曲线降不了它**（曲线只管整体分布，
      块内明暗差原样保留）。实测 t02：曲线调完后局部对比仍 13.9（目标 9.2）。
      对策是叠一层**轻微高斯柔化** —— 只削细节反差，不糊画面：
      gblur sigma 取 (local/11.5) 附近，sigma=0 时自动跳过。
    """
    want_sat = TARGET["sat"]
    ratio = (want_sat / cur_sat) if cur_sat > 1 else 1.0
    if it > 0:
        ratio = 1.0 + (ratio - 1.0) * 0.85
    ratio = max(0.55, min(1.30, ratio))

    # 柔化：局部对比 / 目标 → 需要多少 sigma。经验值 sigma≈(比值-1)*11.5
    soft = ""
    if local:
        need = local / TARGET["local"]
        sigma = max(0.0, (need - 1.0) * 11.5)
        if sigma >= 0.4:
            soft = ",gblur=sigma=%.2f" % min(sigma, 4.0)

    # ⚠️ 曲线串含 % 必须用 + 拼接。用 % 格式化会把整条链里的 %s 吃掉，
    #    curves 拿不到控制点 → ffmpeg 报错或输出全黑（分位数全是 0.6 就是这个症状）。
    return ("curves=all='" + curve + "'"
            ",unsharp=5:5:0.45:5:5:0.0"
            ",eq=saturation=" + ("%.3f" % ratio) + soft +
            ",colorbalance=rs=0.020:bs=-0.020")


# ─────────────────────── ③ 应用 + 验证 ───────────────────────
def apply_grade(src, dst, vf, audio_only=False):
    """对 src 施加滤镜链 → dst。有音轨就 copy 音轨。

    audio_only=True 时**不重新编码视频**，直接把视频流 copy 过去
    （用于「音轨版只换调色、不重编码」的场景，省一半时间）。
    """
    has_audio = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=codec_type", "-of", "csv=p=0", src],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    ).stdout.strip() != ""

    cmd = [FFMPEG, "-y", "-loglevel", "error", "-i", src]
    if audio_only:
        cmd += ["-c:v", "copy"]
    else:
        cmd += ["-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                "-pix_fmt", "yuv420p"]
    if has_audio:
        cmd += ["-c:a", "copy"]
    cmd += [dst]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0 or not os.path.exists(dst):
        raise SystemExit("ffmpeg 失败: %s\n%s" % (r.stderr[:600], vf))


def report(tag, before, after, n):
    print("\n" + "=" * 68)
    print("  %s   第 %d 轮调完" % (tag, n))
    print("=" * 68)
    print("  %-8s %8s %8s %8s %8s" % ("指标", "调前", "调后", "目标", "偏差"))
    print("  " + "-" * 44)
    worst = 0.0
    for k in KEYS:
        d = after[k] - TARGET[k]
        worst = max(worst, abs(d))
        print("  %-8s %8.1f %8.1f %8.1f %+8.1f" % (k, before[k], after[k], TARGET[k], d))
    ds = after["sat"] - TARGET["sat"]
    worst = max(worst, abs(ds))
    print("  %-8s %8.1f %8.1f %8.1f %+8.1f" % ("饱和度", before["sat"],
          after["sat"], TARGET["sat"], ds))
    dl = after["local"] - TARGET["local"]
    worst = max(worst, abs(dl) * 1.2)
    print("  %-8s %8.2f %8.2f %8.2f %+8.2f  ★" % ("局部对比", before["local"],
          after["local"], TARGET["local"], dl))
    print("  %-8s %8.1f %8.1f %8.1f %+8.1f" % ("全局对比", before["contrast"],
          after["contrast"], TARGET["contrast"], after["contrast"] - TARGET["contrast"]))
    print("  " + "-" * 44)
    print("  最大偏差 %.1f  →  %s" % (worst, "达标" if worst <= 8 else "偏差偏大，再迭代"))
    return worst


def do_one(path, iters=ITER, dry=False):
    tag = os.path.splitext(os.path.basename(path))[0]
    tag = "".join(c if c.isalnum() or c in "-_" else "_" for c in tag)[-28:]
    print("\n▶ %s" % os.path.basename(path))

    # ⚠️ 必须先把原片备份下来再动手。本会话已踩坏过一次：
    #    调色结果直接写回原路径，脚本中途报错就再也拿不回未调色的版本。
    raw_dir = os.path.join(os.path.dirname(os.path.dirname(path)), "_raw")
    base = os.path.basename(path)
    for suf in ("", "-audio"):
        src_f = path[:-4] + suf + ".mp4" if path.endswith(".mp4") else None
        if not src_f or not os.path.exists(src_f):
            continue
        dst_f = os.path.join(raw_dir, os.path.basename(src_f))
        # 只在「备份还没有」或「备份比现文件新」时才复制，避免用已调色片盖掉原片
        if not os.path.exists(dst_f) or os.path.getmtime(dst_f) < os.path.getmtime(src_f):
            os.makedirs(raw_dir, exist_ok=True)
            shutil.copy2(src_f, dst_f)

    cur = measure(path, tag)
    before = dict(cur)
    print("  调前 p05=%.1f p25=%.1f p50=%.1f p95=%.1f p99=%.1f sat=%.1f 局部对比≈%.1f"
          % (cur["p05"], cur["p25"], cur["p50"], cur["p95"], cur["p99"],
             cur["sat"], cur["local"] if "local" in cur else -1))
    if dry:
        return

    tmp_out = os.path.join(TMP, tag + "_graded.mp4")
    for n in range(1, iters + 1):
        cs, _ = solve_curve(cur, it=n - 1)
        vf = build_vf(cs, cur["sat"], local=cur.get("local"), it=n - 1)
        apply_grade(path, tmp_out, vf)
        after = measure(tmp_out, tag + "_g")
        worst = report(tag, before, after, n)
        if worst <= 8.0:
            # ⚠️ 达标即停。直方图匹配在**第 1 轮就是精确解**（t02 实测最大偏差 5.6，
            #    7 个分位全中）。再叠一轮会把饱和度二次调整（85.6→58.8→92.9）、
            #    曲线重复收窄（p25 从 66.8 掉回 35.4）—— 越调越差。
            print("  → 已达标（最大偏差 %.1f ≤ 8），停止迭代" % worst)
            cur = after
            break
        cur = after

    # 正式落地：把调色结果写回原路径（含音轨的交付件也是它）
    shutil.copy2(tmp_out, path)
    a_out = path[:-4] + "-audio.mp4"
    a_in = os.path.join(os.path.dirname(path),
                        os.path.basename(tmp_out)[:-4] + "-audio.mp4")
    if os.path.exists(a_in):
        shutil.copy2(a_in, a_out)
    elif os.path.exists(path[:-4] + "-audio.mp4"):
        # 音轨版单独处理：只换视频流，音频直接 copy
        va = os.path.join(TMP, tag + "_g_audio.mp4")
        apply_grade(path[:-4] + "-audio.mp4", va, build_vf(cs, before["sat"],
                                local=before.get("local"), it=0), audio_only=False)
        shutil.copy2(va, a_out)
    print("  ✔ 已写回 %s" % path)


def main():
    args = sys.argv[1:]
    dry = "--dry" in args
    iters = ITER
    if "--iter" in args:
        iters = int(args[args.index("--iter") + 1])
    files = []
    if "--dir" in args:
        d = args[args.index("--dir") + 1]
        files = sorted(glob.glob(os.path.join(d, "*.mp4")))
    else:
        files = [a for a in args if not a.startswith("--") and a.endswith(".mp4")
                 and not a.endswith("-audio.mp4")]

    if not files:
        raise SystemExit("没找到要处理的 mp4")
    print("待处理 %d 个文件，迭代 %d 轮" % (len(files), iters))
    for f in files:
        do_one(f, iters, dry)


if __name__ == "__main__":
    main()
