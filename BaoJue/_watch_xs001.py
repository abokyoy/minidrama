# -*- coding: utf-8 -*-
"""xs001 出片监控：每 45 秒查一次目录 + ComfyUI 队列，5 段全出齐就退出。
同时做两道体检（都是本轮踩过的坑）：
  · 花屏：ffprobe 码率 > 8000 kbps（亮度检测对彩噪不敏感，发现不了花屏）
  · 亮度：signalstats 前后半均值差，防「越接越暗」
用法：python _watch_xs001.py [超时秒]
"""
import os
import re
import sys
import json
import glob
import time
import subprocess
import urllib.request

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)
os.environ["no_proxy"] = "127.0.0.1,localhost"

OUT = r"D:\output\new"
EP = "xs001"
N = 5
GLITCH_KBPS = 8000
DEADLINE = time.time() + float(sys.argv[1] if len(sys.argv) > 1 else 7200)


LOGF = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "xs001", "logs", "watch.log")


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOGF), exist_ok=True)
        with open(LOGF, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def queue():
    try:
        d = json.load(urllib.request.urlopen("http://127.0.0.1:8188/queue", timeout=8))
        return len(d.get("queue_running", [])), len(d.get("queue_pending", []))
    except Exception:
        return -1, -1


def kbps(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=bit_rate", "-of", "csv=p=0", path],
        capture_output=True, timeout=90)
    s = (r.stdout or b"").decode("utf-8", "replace").strip().splitlines()
    try:
        return int(s[0]) // 1000
    except Exception:
        return -1


def bright(path):
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "info", "-i", path,
         "-vf", "signalstats,metadata=print:file=-", "-f", "null", "-"],
        capture_output=True, timeout=300)
    txt = (r.stderr or b"").decode("utf-8", "replace")
    vals = [float(m) for m in re.findall(r"lavfi\.signalstats\.YAVG=([\d.]+)", txt)]
    if len(vals) < 8:
        return None
    h = len(vals) // 2
    return sum(vals[:h]) / h, sum(vals[h:]) / h


def main():
    log("监控 %s，%d 段，输出 %s" % (EP, N, OUT))
    seen = {}
    while time.time() < DEADLINE:
        run, pend = queue()
        # ⚠️ 原来用 glob("xs01_t*_00001*.mp4")，把 `-audio.mp4` 也数进去，
        # 于是「已出 6/5」被误判成全部出齐、监控提前退出。
        # 现在只认无后缀的主文件：xs01_tNN_00001.mp4
        files = sorted(glob.glob(os.path.join(OUT, "xs01_t*_00001.mp4")))
        for f in files:
            name = os.path.basename(f)
            if name in seen:
                continue
            kb = kbps(f)
            seen[name] = kb
            flag = ""
            if kb > GLITCH_KBPS:
                flag = "  ❗花屏嫌疑(码率%d kbps)" % kb
            log("出片 %s  %.1f MB  码率=%d kbps%s"
                % (name, os.path.getsize(f) / 1048576.0, kb, flag))
        log("队列 运行=%d 排队=%d  已出 %d/%d" % (run, pend, len(seen), N))
        if len(seen) >= N:
            log("=== 5 段全部出齐 ===")
            for name in sorted(seen):
                f = os.path.join(OUT, name)
                b = bright(f)
                if b:
                    log("  %s  亮度 前半%.1f 后半%.1f 差%+.1f  %s"
                        % (name, b[0], b[1], b[1] - b[0],
                           "OK" if abs(b[1] - b[0]) < 12 else "⚠️偏暗"))
            return 0
        time.sleep(45)
    log("超时退出")
    return 1


if __name__ == "__main__":
    sys.exit(main())
