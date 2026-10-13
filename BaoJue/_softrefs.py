# -*- coding: utf-8 -*-
"""把参考图调成 Seedance 的色调，输出到 assets_soft/。

═══════════════════════════════════════════════════════════════════════
为什么必须改参考图，而不是事后调色（2026-10-04 实测的决定性证据）
═══════════════════════════════════════════════════════════════════════
H3 是 **ref2v** —— 它会连同**色调**一起复制参考图。实测 4 张参考图：

  参考图                p50     p95     p99     饱和
  char_suxiaoman       214.9   255.0   255.0   51.8
  char_qianjingli      216.0   251.2   253.2   36.2
  char_xiaotang        218.1   254.0   255.0   22.6
  sc_office_pano       155.1   237.3   251.7   17.2
  ────────────────────────────────────────────────────
  Seedance 目标         112.5   188.8   212.6   61.7

三张角色图的中位调就已经顶到 215（接近死白），高光 100% 顶满 255。
把它们喂给模型，H3 学到的就是「中间调极亮 + 高光死白」→ 输出必然
「对比度巨大、高光硬、饱和艳」（实测成片 p99=236、局部对比 16.1、饱和 85.6）。

**所以修在输入端，不是输出端。** 这是「一次生成就等于 Seedance」的唯一正路：
  · 事后调色 = 补救，画面已经硬了，只能靠 gblur 糊回来（会损失清晰度）
  · 改参考图 = 从源头让 H3 走「柔和高调」这条路，输出天生就柔

调的是这 4 项（与 Seedance 实测值对齐）：
  · 曲线：p50 216→112、p95 255→189、p99 255→213  （高光 roll-off，白不刺眼）
  · 饱和：按各图原值往 61.7 靠（人物图略降，场景图提）
  · 局部对比：往 9.24 靠（轻微柔化）
  · 保留人脸/构图/道具 —— 只动像素值，不动内容

用法：
  python _softrefs.py              # 生成全部
  python _softrefs.py --one assets/char_suxiaoman.png   # 只生成一张看效果
"""
import glob
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
DST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_soft")
TMP = r"C:\Users\86134\.workbuddy\tmp\softrefs"

# Seedance 实测目标 —— 由 `_seedance_target.py` 从**全部 4 支**样片算出
# （2026-10-04 21:05）。⚠️ 不要用单支的值：之前的 TARGET 是从 (2) 号一支抄的，
# 样本太窄，会把另外 3 支误判成不合格。
T_P50, T_P95, T_P99, T_SAT, T_LOCAL = 117.8, 195.0, 223.6, 53.8, 10.5
T_P05 = 28.5          # 暗部目标（t01 实测只有 12.5，这是「对比大」的另一半原因）

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _softgrade as SG          # noqa: E402  复用测量逻辑


def build_curve(cur, sigma_max=0.9):
    """把参考图映射到 Seedance 色调。

    ⚠️ 2026-10-04 20:30 修正 1：第一版用「全 7 点直方图匹配」把 p01 也压到 9.6，
       结果**白背景被一起拉成灰底**（对比图右半张：人物变暗、背景发灰、失去通透感）。
       参考图是**设定图**，白背景是内容的一部分，不是需要压暗的暗部。

    ⚠️ 2026-10-04 20:47 修正 2（实测驱动）：把参考图压到 Seedance 分布后，
       **输出的高光反而更亮了**（p99 236→243，Seedance 只要 213）。
       原因：H3 ref2v 会**重建**高光，不完全照抄参考图 —— 参考图的高光压得不够，
       模型就按自己的高对比倾向补回来。
       → 对策：参考图的高光**过压**（比目标再低一档），让模型重建时也起不来。
         目标 p95 189 → 压到 170；p99 213 → 压到 190。
         暗部/中间调仍保通透（p50 128、p01≥16），不动内容。
    """
    tgt = {
        # ⚠️ 2026-10-04 21:10 决定性修正（_isolate_soft.py 隔离实验）。
        #   逐项开关测出来的结论：
        #     仅曲线            → 肤色 S 69→92（+23.3），脸明显发红发橙
        #     仅 gblur 柔化     → S 69→69（+0.1），**完全无关**
        #     仅 eq=saturation 0.78 → S 69→61（-8.1），正常变淡
        #   → **元凶是曲线本身**，不是饱和、不是柔化。
        #   根因：曲线整体上抬像素值，人脸本来就亮，抬后 S/V 比例失衡 → 显艳显红。
        #   对策：曲线**只压高光（roll-off），中间调以下基本不动**。
        #   p25/p50/p75 全部保持原值 → 肤色不变；只治「硬白」和「饱和艳」。
        "p01": cur["p01"],
        "p05": cur["p05"],
        "p25": cur["p25"],
        "p50": cur["p50"],
        "p75": min(cur["p75"], 200.0),
        "p95": 170.0,                       # 过压：治 H3 重建高光
        "p99": 190.0,                       # 过压：治死白
    }
    # ══════════════════════════════════════════════════════════════
    # 第七版（21:30）：参数由 `_grid_soft.py` **网格搜索**得出，不再靠手调。
    #
    # 手调失败 6 轮的原因：V 和 S 是耦合的 —— 压高光让白背景 V 降，
    # 肤色 V 没降 → 相对差异拉大 → 肤色 S 上升 → 脸发红。
    # 推理调不出来，只能穷举。
    #
    # 网格结果（char_suxiaoman，11 档全跑）：
    #   压白=0.890 饱和=0.85 → p99 255→235.8、肤色S 69.1→**69.2**（零变化）
    #   局部对比 10.72→10.37（目标 10.5）  综合误差 1.30（最优）
    # 对比手调的 v6（压白 0.845 饱和 0.72）：肤色 S 69→77.5，明显变艳。
    #
    # 关键点：压白量必须落在 **0.89** 这个窄区间。
    #   0.845/0.870 → 压不动（p99 仍 253），且肤色 S 涨到 71~82
    #   0.925       → 压过头（p99 243 但局部对比掉到 9.1），肤色 S 涨到 81
    TOP_OUT = 0.890
    SAT_RATIO = 0.85
    pts = [
        (0.000, 0.000),
        (0.925, 0.925),              # 236/255 以下完全不动（人脸区）
        (0.945, TOP_OUT + 0.030),
        (0.980, TOP_OUT + 0.015),
        (1.000, TOP_OUT),             # 255 → 227
    ]
    cs = " ".join("%s/%.4f" % (x, y) for x, y in pts)

    # ⚠️ 饱和度：**只降不升，而且主动压一档**。
    #   实测（_skinchk.py，2026-10-04 21:00）：
    #     char_suxiaoman  原图 S=69.1 → 调后 S=92.5（艳了 34%，肉眼「发红发橙」）
    #     char_qianjingli 原图 S=91.2 → 调后 S=103.6（H 掉到 10.9，判为偏红）
    #   根因：`eq=saturation=ratio` 是**乘法**，而 ratio>1 时会把已经很艳的图推得更艳。
    #   正确做法：饱和度按**倍数直接下调**，不用「往目标靠」那个方向 ——
    #   参考图本来就常比目标艳，往目标靠 = 提艳 = 出事。
    # 饱和度倍数同样来自网格搜索（0.85 最优，肤色 S 零变化）
    ratio = SAT_RATIO
    need = cur.get("local", 10.0) / T_LOCAL * 1.35
    sigma = max(0.0, min(sigma_max, (need - 1.0) * 9.0))
    soft = (",gblur=sigma=%.2f" % sigma) if sigma >= 0.35 else ""
    vf = ("curves=all='" + cs + "'"
          ",unsharp=5:5:0.40:5:5:0.0"
          ",eq=saturation=" + ("%.3f" % ratio) + soft)
    # ⚠️ 不加 colorbalance 红偏移。参考图是**人物设定图**，肤色必须准 ——
    #   任何 rs>0 的红偏移都会让脸发红。2026-10-04 21:00 移除。
    return vf


def measure_still(path):
    """量一张静态 PNG 的色调分布。

    ⚠️ 不能用 _softgrade.measure —— 那个走 ffmpeg 抽帧（fps=N），
       对单张图片会抽不出帧，直接 SystemExit("抽帧失败")。
    """
    import numpy as np
    import cv2

    ascii_p = os.path.join(TMP, os.path.basename(path))
    if os.path.abspath(ascii_p) != os.path.abspath(path):
        shutil.copy2(path, ascii_p)
    im = cv2.imread(ascii_p, cv2.IMREAD_COLOR)
    if im is None:
        raise SystemExit("读不出图片: " + path)
    b, g, r = im[:, :, 0].astype("f4"), im[:, :, 1].astype("f4"), im[:, :, 2].astype("f4")
    y = 0.114 * b + 0.587 * g + 0.299 * r
    q = np.percentile(y, [1, 5, 25, 50, 75, 95, 99])
    out = dict(zip(SG.KEYS, [float(v) for v in q]))
    out["sat"] = float(cv2.cvtColor(im, cv2.COLOR_BGR2HSV)[:, :, 1].mean())
    h, w = y.shape
    bh, bw = h // 16 * 16, w // 16 * 16
    bl = y[:bh, :bw].reshape(bh // 16, 16, bw // 16, 16).transpose(0, 2, 1, 3)
    out["local"] = float(bl.reshape(-1, 256).std(axis=1).mean())
    out["contrast"] = out["p95"] - out["p05"]
    out["dyn"] = out["p99"] - out["p01"]
    return out


def one(src, dst, tag):
    os.makedirs(TMP, exist_ok=True)
    ascii_src = os.path.join(TMP, tag + "_in.png")
    shutil.copy2(src, ascii_src)

    cur = measure_still(ascii_src)
    vf = build_curve(cur)

    r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", ascii_src,
                        "-vf", vf, "-frames:v", "1", dst],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if r.returncode != 0 or not os.path.exists(dst):
        raise SystemExit("ffmpeg 失败 %s\n%s" % (src, r.stderr[:400]))

    # 自动把关：肤色不能比原图更艳、更红（肉眼判断已经骗过三轮了）
    #
    # ⚠️ 只对**人物图**生效。场景图里被判成"肤色"的是墙面/木纹/地砖，
    #    它们的 H 本来就偏黄（H≈37~47），压高光后 H 掉到 23~30 会被误报偏红。
    #    → 用文件名判断：char_*.png 才是人物设定图。
    import _skinchk
    warn = ""
    if os.path.basename(src).startswith("char_"):
        a, b = _skinchk.skin_stats(src), _skinchk.skin_stats(dst)
        if a and b and a["H"] > 0 and b["H"] > 0:
            if b["S"] > a["S"] * 1.06:
                warn = "  ★饱和升了 %.0f%%（%s→%s）" % ((b["S"] / a["S"] - 1) * 100,
                                                       round(a["S"]), round(b["S"]))
            if b["H"] < a["H"] - 2.5:
                warn += "  ★偏红 H %.1f→%.1f" % (a["H"], b["H"])
    print("  %-26s p50 %6.1f→%6.1f  p95 %6.1f→%6.1f  饱和 %5.1f→%5.1f  局部 %5.2f→%5.2f%s"
          % (os.path.basename(src), cur["p50"], T_P50, cur["p95"], T_P95,
             cur["sat"], T_SAT, cur.get("local", 0), T_LOCAL, warn))
    return cur


def main():
    args = sys.argv[1:]
    if "--one" in args:
        src = os.path.abspath(args[args.index("--one") + 1])
        os.makedirs(DST_DIR, exist_ok=True)
        dst = os.path.join(DST_DIR, os.path.basename(src))
        one(src, dst, os.path.splitext(os.path.basename(src))[0])
        print("  →", dst)
        return

    os.makedirs(DST_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(SRC_DIR, "*.png")))
    print("处理 %d 张参考图 → %s\n" % (len(files), DST_DIR))
    for f in files:
        tag = os.path.splitext(os.path.basename(f))[0]
        one(f, os.path.join(DST_DIR, os.path.basename(f)), tag)
    print("\n完成 %d 张。改 jobNN.json 的 ref_dir 指向本目录即可生效。" % len(files))


if __name__ == "__main__":
    main()
