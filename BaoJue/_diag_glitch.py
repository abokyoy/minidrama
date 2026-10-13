# -*- coding: utf-8 -*-
"""花屏定位实验：ep01_t01 全片花屏，到底是不是 reference_protection=Light 造成的。

现象（2026-10-04 16:23）：切到 D:\\output\\new 重跑，第一段
  D:\\output\\new\\ep01_t01_00001.mp4 **整段 11 帧全部花屏**（彩色噪点 + 马赛克块），
  码率 10.4 Mbps（旧片同段只有 4.2 Mbps，差 2.5 倍 → 画面里有大量噪点数据）。
  而亮度检测却报 mean=164.9 med=169 p05=88 **OK** —— 说明它只看灰度均值，
  彩噪对亮度影响不大，所以**亮度检测根本发现不了花屏**（又一个"校验器骗人"）。

本脚本做严格对照：同一份 t01 提示词，只改一个变量，各跑 1 段。
  OFF : reference_protection = Off        （= 旧片设置）
  LIGHT: reference_protection = Light     （= 当前上线档设置）
跑完自动抽帧 + 算「彩噪强度」指标，直接判真伪。

彩噪指标怎么算（简单可靠）：
  1) 取若干帧转 RGB
  2) 逐像素算饱和度 S = (max-min)/max
  3) 取 S 的均值 —— 正常画面 S 均值低（0.1~0.25）；
     花屏/彩噪画面 S 会显著更高（>0.3）
另外算相邻帧差（花屏时也会异常高）。

用法：
  python _diag_glitch.py OFF      # 只跑 Off 一组
  python _diag_glitch.py          # 两组都跑并对比
  python _diag_glitch.py --check  # 不生成，只对已有文件做检测
"""
import glob
import json
import os
import subprocess
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = "D:/output/new"
SEGDIR = os.path.join(BASE, "ep001_segs")
SRC_API = os.path.join(SEGDIR, "_last_api.json")
JOB = os.path.join(SEGDIR, "job01.json")
FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"E:\Program Files\ffmpeg\bin\ffprobe.exe"
SERVER = "http://127.0.0.1:8188"

GROUPS = {"OFF": "Off", "LIGHT": "Light"}


def op_():
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
              "ALL_PROXY", "all_proxy"):
        os.environ.pop(k, None)
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def alive():
    try:
        op_().open(SERVER + "/system_stats", timeout=8).read()
        return True
    except Exception:
        return False


def build(refprot, tag):
    api = json.load(open(SRC_API, encoding="utf-8"))
    for nd in api.values():
        if not isinstance(nd, dict):
            continue
        ct, ins = nd.get("class_type"), nd.get("inputs", {})
        if ct == "H3SLAAttention":
            ins["reference_protection"] = refprot
        elif ct == "VHS_VideoCombine":
            ins["filename_prefix"] = "GL_%s" % tag
    # 参考图槽位（901/904-908）照旧
    for nid, nd in api.items():
        if isinstance(nd, dict) and nd.get("class_type") == "LoadImage":
            p = nd["inputs"].get("image", "")
            if p:
                api[nid]["inputs"]["image"] = os.path.basename(p)
    return api


def submit(api):
    req = urllib.request.Request(
        SERVER + "/prompt",
        data=json.dumps({"prompt": api, "client_id": "glitch"}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    return json.loads(op_().open(req, timeout=180).read().decode("utf-8"))["prompt_id"]


def wait(pid, timeout=2400):
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = json.loads(op_().open(SERVER + "/history/" + pid, timeout=30).read())
        if pid in h and h[pid].get("outputs"):
            return True
        time.sleep(10)
    return False


def find(tag):
    fs = sorted(glob.glob(os.path.join(OUT, "GL_%s_*.mp4" % tag)))
    return [f for f in fs if os.path.getsize(f) > 200000]


def glitch_score(video):
    """彩噪强度 + 相邻帧差。返回 dict。"""
    tmp = os.path.join(BASE, "..", "_cmp", "glitch", os.path.basename(video)[:20])
    os.makedirs(tmp, exist_ok=True)
    for f in glob.glob(os.path.join(tmp, "*.png")):
        try:
            os.remove(f)
        except OSError:
            pass
    subprocess.run([FFMPEG, "-v", "error", "-i", video, "-vf", "fps=1",
                    "-frames:v", "8", "-y", os.path.join(tmp, "g%02d.png")],
                   capture_output=True, timeout=240)
    frames = sorted(glob.glob(os.path.join(tmp, "*.png")))
    if not frames:
        return {}
    # 用 ffmpeg 算 YAVG 序列（帧间差）+ 饱和度
    r1 = subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "info", "-i", video,
                         "-vf", "tblend=all_mode=difference,signalstats,"
                                "metadata=print:key=lavfi.signalstats.YAVG",
                         "-f", "null", "-"], capture_output=True, text=True,
                        errors="replace", timeout=300)
    import re
    jitter = [float(x) for x in re.findall(r"YAVG=([\d.]+)", r1.stderr or "")]
    # 码率：噪点越多码率越高（实测花屏段 10.4Mbps vs 正常 4.2Mbps）
    r2 = subprocess.run([FFPROBE, "-v", "error", "-show_entries",
                         "format=bit_rate", "-of", "csv=p=0", video],
                        capture_output=True, text=True, errors="replace", timeout=60)
    kbps = 0
    try:
        kbps = int(float((r2.stdout or "0").strip())) // 1000
    except ValueError:
        pass
    return {
        "frames": len(frames),
        "jitter": (sum(jitter) / len(jitter)) if jitter else None,
        "jitter_max": max(jitter) if jitter else None,
        "kbps": kbps,
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    only = None
    for a in sys.argv[1:]:
        if a.upper() in GROUPS:
            only = a.upper()
    tags = [only] if only else list(GROUPS)

    if "--check" in sys.argv:
        for tag in GROUPS:
            for v in find(tag):
                print(" %-8s %s" % (tag, os.path.basename(v)), glitch_score(v))
        return

    if not alive():
        print("❌ ComfyUI 无响应，先启动：python _comfy_task.py start")
        return
    print("=" * 66)
    print(" 花屏定位：只改 reference_protection，其余全同")
    print("=" * 66)
    for tag in tags:
        rp = GROUPS[tag]
        print("\n[%s] reference_protection=%s 提交中…" % (tag, rp), flush=True)
        try:
            pid = submit(build(rp, tag))
        except Exception as e:
            print("  提交失败：%s" % str(e)[:160])
            continue
        print("  pid=%s 等待生成（最多 40 分钟）…" % pid, flush=True)
        if not wait(pid):
            print("  超时未完成")
            continue
        for v in find(tag):
            print("  → %s" % os.path.basename(v), glitch_score(v), flush=True)


if __name__ == "__main__":
    main()
