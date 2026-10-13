# -*- coding: utf-8 -*-
"""⭐ 整集驱动 —— 用官方原版档（hd_turbo8）从第1 段跑到最后一段。

为什么不直接用 `_run_one.py`：它只支持单段，跑完就退出。
本文件**只import 复用**它的函数（start_comfy / build_job / stage_refs），
不改它一行 → 单段路径零风险。

每满 3 段重启一次 ComfyUI（防越接越黑，这是本项目的老规矩）。
每段出片立刻做两件事：
  1. 抽帧亮度体检（**查全黑** —— fp16 VAE 栽过，int8 才正常）
  2. 码率体检（查花屏：正常 ~4.0M，花屏 ~10.4M，阈值 8000 kbps）

用法：
    python _run_ep.py 1                 # 第 1 集，官方实例 8189
    python _run_ep.py 1 --old           # 走老实例 8188
    python _run_ep.py 1 --start 2       # 从第 2 段开始（续跑）
"""
from __future__ import print_function

import glob
import io
import json
import os
import shutil
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import _run_one as RO          # noqa: E402  复用单段驱动的函数
from _quality import PROFILE   # noqa: E402

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"E:\Program Files\ffmpeg\bin\ffprobe.exe"
# 抽帧/分析目录必须纯 ASCII 且不在受管目录内（软删除钩子会拦~/.workbuddy/tmp）
AB_DIR = r"D:\_abtmp"

# ⛔⛔ 不要用 `os.remove` 删抽帧文件（2026-10-07 栽过）
#每次 check() 抽 16 帧、删 16 个，累计到第 4 段就触发
#   SAFE_DELETE_BULK_CONFIRM_REQUIRED {"count":50,"threshold":50}
# → driver 直接被拦死，整集跑到一半停掉。
# **正确做法：每次体检用独立子目录，事后不删**（临时目录本来就是该被清空的，
#   让用户按目录整体删一次，远比每 50 个文件触发一次拦截安全）。
def _workdir(tag):
    d = os.path.join(AB_DIR, "chk_" + tag)
    os.makedirs(d, exist_ok=True)
    return d

RESTART_EVERY = 3     # 每 3 段重启 ComfyUI
BLACK_MEAN = 8.0      # 帧均值低于此值 = 全黑，判失败
BITRATE_MAX = 8000    # kbps，超过 = 花屏

# 本进程启的 ComfyUI pid（自己记，不去猜系统里哪个 python 是 ComfyUI ——
# 猜错会杀掉无关进程。AGENTS.md 铁律：重启权只属于生成器。）
_PID = {"v": None}


def kill_comfy(port):
    """只杀**自己启的**那个 pid。宁可重启失败也不能误杀用户进程。"""
    pid = _PID.get("v")
    if not pid:
        print("  （没记录 pid，跳过 kill；start_comfy 会复用已在跑的实例）")
        return
    print("  kill pid=%d" % pid)
    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    _PID["v"] = None
    time.sleep(10)


def ensure_comfy(port, official):
    """确保实例在跑，并记住 pid（方便后面重启）。"""
    if RO.comfy_alive(port):
        print("  ComfyUI 已在运行（端口 %d）" % port)
        return
    if official:
        p = RO.start_comfy(RO.OFFICIAL_PORT, RO.OFFICIAL_DIR, RO.OFFICIAL_OUT,
                           RO.OFFICIAL_TEMP, "official")
    else:
        p = RO.start_comfy(port)
    _PID["v"] = p.pid if p else None


# ─────────────────────────── 体检 ───────────────────────────
def probe(path):
    """返回 (均值, 码率kbps, 宽, 高, 秒)。任一项读不到返回 None。"""
    try:
        r = subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries",
             "stream=width,height,bit_rate:format=duration,bit_rate",
             "-of", "json", path],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        d = json.loads(r.stdout or "{}")
        st = (d.get("streams") or [{}])[0]
        fmt = d.get("format") or {}
        br = st.get("bit_rate") or fmt.get("bit_rate") or "0"
        return (int(br) / 1000.0, st.get("width"), st.get("height"),
                float(fmt.get("duration") or 0))
    except Exception as e:
        print("     probe 失败: %s" % e)
        return None


def mean_of_frames(mp4, tag):
    """抽 8 帧算平均亮度。中文路径先拷成 ASCII（OpenCV5 坑）。"""
    import numpy as np
    import cv2
    ASCII = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    tag = "".join(c if c in ASCII else "_" for c in tag)[:28] or "x"
    os.makedirs(AB_DIR, exist_ok=True)
    src = os.path.join(AB_DIR, tag + ".mp4")
    # ⚠️ 用 shutil 不用 `copy` 命令 —— shell 的 copy 在本机对
    #    「含-的tag + 长路径」组合会静默失败（抽帧拿不到→亮度算成-1）。
    #    症状和「片是黑的」一模一样，会误判，必须用可靠写法。
    shutil.copy2(mp4, src)
    # 不删旧帧：改用带序号的独立子目录（见 _workdir 注释 —— 删文件会触发批量删除拦截）
    wd = _workdir(tag)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", src,
                    "-vf", "fps=2", os.path.join(wd, "f%03d.png")],
                   capture_output=True)
    fs = sorted(glob.glob(os.path.join(wd, "f*.png")))
    if not fs:
        return -1.0
    acc = []
    for f in fs:
        im = cv2.imread(f, cv2.IMREAD_COLOR)
        if im is None:
            continue
        b, g, r = (im[:, :, i].astype("f4") for i in range(3))
        acc.append(float((0.114 * b + 0.587 * g + 0.299 * r).mean()))
    return sum(acc) / len(acc) if acc else -1.0


def latest_mp4(out_dir, prefix):
    """取该段**最新**的一条成片（ComfyUI 输出编号会递增，不能写死 _00001）。"""
    pats = [os.path.join(out_dir, prefix + "_0000*-audio.mp4"),
            os.path.join(out_dir, prefix + "_0000*.mp4")]
    cands = []
    for pat in pats:
        cands += glob.glob(pat)
    if not cands:
        return None
    return max(cands, key=os.path.getmtime)


def check(tag, mp4):
    """全黑 / 花屏 / 尺寸 三项体检。返回 (是否通过, 说明)。"""
    if not os.path.exists(mp4):
        return False, "文件不存在"
    size = os.path.getsize(mp4)
    if size < 100000:
        return False, "文件太小 %.0f KB（多半是全黑）" % (size / 1024.0)
    pr = probe(mp4)
    if not pr:
        return False, "probe 读不出"
    br, w, h, dur = pr
    mean = mean_of_frames(mp4, tag)
    msg = "%dx%d %.1fs %.1fMB 码率%.0fk 亮度%.1f" % (w, h, dur, size / 1048576.0, br, mean)
    if mean >= 0 and mean < BLACK_MEAN:
        return False, "★全黑（帧均值 %.1f）  %s" % (mean, msg)
    if br > BITRATE_MAX:
        return False, "★疑似花屏（码率 %.0fk 超过 %d）  %s" % (br, BITRATE_MAX, msg)
    if mean < 0:
        return False, "抽不出帧  " + msg
    return True, "OK  " + msg


# ─────────────────────────── 主流程 ───────────────────────────
def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    idx = int(args[0]) if args else 1
    official = "--old" not in sys.argv
    start = 1
    for i, a in enumerate(sys.argv):
        if a == "--start" and i + 1 < len(sys.argv):
            start = int(sys.argv[i + 1])

    RO.pop_proxy()

    # ⛔ 生成前清场（用户 2026-10-07 要求）：关ComfyUI + 关占内存应用。
    #    必须在起 ComfyUI 之前做 —— 起来之后内存就抢不动了。
    RO.reclaim_before_gen()

    os.environ["MINIDRAMA_PORT"] = str(
        RO.OFFICIAL_PORT if official else 8188)
    out_dir = RO.OFFICIAL_OUT if official else RO.OUT
    wf = RO.OFFICIAL_WF if official else (
        r"E:\ComfyUI\ComfyUI_new\user\default\workflows"
        r"\04_ref2v_4step_sla_ganloss_fixed.json")

    prof = json.load(io.open(RO.PROFILE, encoding="utf-8")) \
        if hasattr(RO, "PROFILE") else json.load(
            io.open(os.path.join(BASE, "_quality_profile.json"), encoding="utf-8"))
    print("=" * 70)
    print(" 整集生成  第%d 集  段%d → 末段" % (idx, start))
    print(" 档位: %s" % prof.get("name"))
    p = prof.get("p", {})
    print("   steps=%s unet=%s" % (p.get("steps"), p.get("unet")))
    print("   vae=%s" % p.get("vae"))
    if p.get("lora"):
        print("   lora=%s (%.2f)" % (p["lora"], p.get("lora_s", 1.0)))
    print(" 实例: %s  输出: %s" % ("8189 官方版" if official else "8188 旧版", out_dir))
    print("=" * 70)

    # 段数从 manifest 读（权威），比 ls 提示词文件可靠
    mf = os.path.join(RO.SEGS, "manifest.json")
    total = 5
    if os.path.exists(mf):
        d = json.load(io.open(mf, encoding="utf-8"))
        items = d if isinstance(d, list) else d.get("segments", [])
        total = len(items)
    print(" 共%d 段，本次跑 %d → %d\n" % (total, start, total))

    ensure_comfy(RO.OFFICIAL_PORT if official else 8188, official)

    todo = list(range(start, total + 1))
    ok_list, bad_list = [], []
    done_since_restart = 0

    for k, i in enumerate(todo):
        print("─" * 70)
        print("【段 %d / %d】(第 %d/%d 段)" % (i, total, k + 1, len(todo)))
        rf, job = RO.build_job(i, official=official)
        print("  %s" % job["out_prefix"])
        print("  参考图 %d 张  提示词 %d 词"
              % (len(job["refs"]),
                 len(io.open(job["prompt_file"], encoding="utf-8").read().split())))

        env = dict(os.environ)
        env["MINIDRAMA_PORT"] = str(RO.OFFICIAL_PORT if official else 8188)
        t0 = time.time()
        try:
            r = subprocess.run([sys.executable, os.path.join(BASE, "h3_driver.py"), rf],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=env)
            for l in ((r.stdout or "") + (r.stderr or "")).strip().splitlines()[-6:]:
                print("   " + l)
            rc = r.returncode
        except Exception as e:
            rc, print("   driver 异常: %s" % e)

        # ⚠️ ComfyUI 的输出编号**会递增**（同名文件已存在就编下一个号），
        #   写死 `_00001` 会把正常成片报成「文件不存在」（2026-10-07 踩过：
        #   第 1 段明明 DONE 了却报失败）。→ glob 取**最新**那条。
        mp4 = latest_mp4(out_dir, job["out_prefix"])
        passed, why = check("ep%d_%02d" % (idx, i), mp4) if mp4 \
            else (False, "没找到任何输出文件")
        print("  用时 %.1f 分钟  →  %s" % ((time.time() - t0) / 60.0, why))
        (ok_list if passed else bad_list).append(i)

        if not passed:
            print("  ★ 本段失败，先继续跑下一段，最后统一处理")
        done_since_restart += 1

        # 每满 3 段重启 ComfyUI（防越接越黑）
        if done_since_restart >= RESTART_EVERY and k < len(todo) - 1:
            print("\n⟳ 已跑 %d 段，重启 ComfyUI 防掉色…" % done_since_restart)
            kill_comfy(RO.OFFICIAL_PORT if official else 8188)
            ensure_comfy(RO.OFFICIAL_PORT if official else 8188, official)
            done_since_restart = 0
            print()

    print("\n" + "=" * 70)
    print(" 完成：成功 %d 段 %s｜失败 %d 段 %s"
          % (len(ok_list), ok_list, len(bad_list), bad_list))
    print(" 输出目录: %s" % out_dir)
    print("=" * 70)
    return 1 if bad_list else 0


if __name__ == "__main__":
    sys.exit(main())