# -*- coding: utf-8 -*-
"""追踪画质升级测试段的结果，并与同提示词的 4 步基线做对比。

用法：
  python _test_result.py            # 看测试段跑到哪了
  python _test_result.py --compare  # 完成后做客观指标对比
"""
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = "D:/output"
PID_FILE = os.path.join(BASE, "ep001_segs", "_test_pid.txt")
FF = r"E:\Program Files\ffmpeg\bin\ffprobe.exe"

TEST_PREFIX = "TEST_upg_8step_max"
# 基线：t62 的现行 4 步版本
BASE_CLIP = os.path.join(OUT, "ep01_t62_00001-audio.mp4")


def op_():
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
              "ALL_PROXY", "all_proxy"):
        os.environ.pop(k, None)
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def find_test():
    if not os.path.isdir(OUT):
        return None
    for f in os.listdir(OUT):
        if f.startswith(TEST_PREFIX) and f.endswith(".mp4"):
            p = os.path.join(OUT, f)
            if os.path.getsize(p) > 100000:
                return p
    return None


def probe(path):
    try:
        r = subprocess.run([FF, "-v", "error", "-show_entries",
                            "stream=width,height,nb_frames,bit_rate",
                            "-show_entries", "format=duration,bit_rate,size",
                            "-of", "json", path],
                           capture_output=True, text=True, timeout=30)
        return json.loads(r.stdout)
    except Exception as e:
        return {"err": str(e)}


def status():
    pid = None
    if os.path.exists(PID_FILE):
        pid = io.open(PID_FILE, encoding="utf-8").read().strip()
    clip = find_test()
    print("=" * 60)
    print(" 画质升级测试 状态  %s" % time.strftime("%H:%M:%S"))
    print("=" * 60)
    if clip:
        print(" 已产出：%s" % os.path.basename(clip))
        print(" 大小  ：%.1f MB" % (os.path.getsize(clip) / 1e6))
        return clip
    print(" 还没产出。ComfyUI 是串行队列，排在主线当前段之后。")
    if pid:
        try:
            o = op_()
            h = json.load(o.open("http://127.0.0.1:8188/history/" + pid, timeout=20))
            print(" history 里有结果：%s" % ("是" if pid in h else "否（还在跑）"))
        except Exception as e:
            print(" 查询失败：%s" % str(e)[:80])
    return None


def sharpness(path, tag):
    """用拉普拉斯方差量测锐度（越高越锐），并抽帧存盘供肉眼看。"""
    tmp = os.path.join(BASE, "_cmp", "sharp_%s.png" % tag)
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    ffmpeg = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
    # 抽第 4 秒一帧，算清晰度
    cmd = [ffmpeg, "-v", "error", "-ss", "4", "-i", path, "-frames:v", "1",
           "-vf", "format=gray,convolution=0:1:1:1:0:-1:1:0:-1:0:1:0:-1:1:0:0",
           "-f", "image2", "-y", tmp]
    subprocess.run(cmd, capture_output=True, timeout=60)
    if not os.path.exists(tmp):
        return None
    # 用 ffmpeg 的 signalstats 拿标准差近似对比度
    r = subprocess.run([ffmpeg, "-v", "error", "-ss", "4", "-i", path,
                        "-frames:v", "1", "-vf",
                        "signalstats,metadata=print:key=lavfi.signalstats.YAVG",
                        "-f", "null", "-"], capture_output=True, text=True, timeout=60)
    m = re.search(r"YAVG=([\d.]+)", r.stderr or "")
    avg = float(m.group(1)) if m else None
    return avg


def compare():
    test = find_test()
    if not test:
        print("测试段还没产出，无法对比")
        return
    print("=" * 60)
    print(" 对比：4 步基线  vs  8 步 + max 参考图")
    print("=" * 60)
    a = probe(BASE_CLIP)
    b = probe(test)
    for name, d in (("4 步基线 (" + os.path.basename(BASE_CLIP) + ")", a),
                    ("8 步+max (" + os.path.basename(test) + ")", b)):
        if "err" in d:
            print(" %-34s 读取失败" % name)
            continue
        v = [s for s in d.get("streams", []) if s.get("width")][0]
        f = d.get("format", {})
        print(" %s" % name)
        print("   分辨率 %sx%s   帧数 %s   时长 %.1fs" %
              (v.get("width"), v.get("height"), v.get("nb_frames"),
               float(f.get("duration", 0))))
    sa = sharpness(BASE_CLIP, "base")
    sb = sharpness(test, "upg")
    if sa and sb:
        print(" 平均亮度(YAVG)：基线 %.1f  升级 %.1f" % (sa, sb))
    print()
    print(" 抽帧已存到 _cmp/sharp_base.png 与 _cmp/sharp_upg.png，请肉眼对比")
    print(" 文件在：%s" % test)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--compare" in sys.argv:
        compare()
    else:
        status()
