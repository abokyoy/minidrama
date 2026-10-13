# -*- coding: utf-8 -*-
r"""
整段视频的亮度曲线：只看首帧会骗人。

之前只量了 ComfyUI 出的那一张预览 PNG（= 首帧），结果和用户的实际观感对不上。
本脚本用 ffmpeg 沿时间轴均匀抽 N 帧，逐帧量灰度，可以看出：
  · 这一段的整体明暗；
  · **段内有没有越走越黑**（链式掉色的真身）；
  · 首帧是不是恰好偏亮、掩盖了后面的暗。

用法：
  python _scan_video.py                       # 扫 D:\output 里最新的 3 段
  python _scan_video.py <mp4> [<mp4> ...]     # 扫指定文件
  python _scan_video.py --stale               # 扫 _stale 里最新的 3 段（作对照）
"""
import glob
import os
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
PY_IMG = r"E:\ComfyUI\ComfyUI-master\ComfyUI-master\venv\Scripts\python.exe"
OUT = r"D:\output"
STALE = os.path.join(OUT, "_stale")
N = 8

MEASURE = ("import sys,json;from PIL import Image\n"
           "o=[]\n"
           "for p in sys.argv[1:]:\n"
           "    h=Image.open(p).convert('L').histogram();t=sum(h);c=0;g={}\n"
           "    for i,v in enumerate(h):\n"
           "        c+=v\n"
           "        if 'p05' not in g and c>=t*.05: g['p05']=i\n"
           "        if 'med' not in g and c>=t*.5: g['med']=i\n"
           "        if 'p90' not in g and c>=t*.9: g['p90']=i\n"
           "    g['mean']=round(sum(i*v for i,v in enumerate(h))/t,1)\n"
           "    o.append(g)\n"
           "print(json.dumps(o))")


def newest(d, pat="*.mp4", limit=3):
    fs = [p for p in glob.glob(os.path.join(d, pat)) if not p.endswith("-audio.mp4")]
    fs.sort(key=os.path.getmtime, reverse=True)
    return fs[:limit]


def dur(mp4):
    r = subprocess.run([FFMPEG, "-i", mp4], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    t = 0.0
    for line in (r.stderr or "").splitlines():
        if "Duration:" in line:
            h, m, s = line.split("Duration:")[1].split(",")[0].strip().split(":")
            t = int(h) * 3600 + int(m) * 60 + float(s)
    return t or 10.0


def scan(mp4, tmp):
    d = dur(mp4)
    # 均匀抽 N 帧，缩到 1/4 尺寸够算亮度了，快很多
    vf = "fps=%d/%f,scale=168:296" % (N, max(d, 0.1))
    out = os.path.join(tmp, "f_%03d.png")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", mp4, "-vf", vf,
                    "-frames:v", str(N), out], capture_output=True)
    fs = sorted(glob.glob(os.path.join(tmp, "f_*.png")))
    if not fs:
        return []
    r = subprocess.run([PY_IMG, "-c", MEASURE] + fs, capture_output=True,
                       text=True, encoding="utf-8")
    import json
    return json.loads(r.stdout.strip().splitlines()[-1])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        vids = args
    elif "--stale" in sys.argv:
        vids = newest(STALE, "*.mp4", 3)
    else:
        vids = newest(OUT, "*.mp4", 3)
    if not vids:
        print("没找到 mp4")
        return
    tmp = tempfile.mkdtemp(prefix="bright_", dir=os.path.dirname(os.path.abspath(__file__)))
    for v in vids:
        stats = scan(v, tmp)
        if not stats:
            print("%s  抽帧失败" % os.path.basename(v))
            continue
        tag = "⚠️ 段内越走越黑" if (stats[0]["med"] - stats[-1]["med"]) > 25 else "段内稳定"
        print("== %s  （沿时间轴抽 %d 帧）==" % (os.path.basename(v), len(stats)))
        print("   " + "  ".join("mean/med/p05" for _ in stats[:1]) + "")
        for i, s in enumerate(stats):
            print("   第%d帧  mean=%5.1f  med=%3d  p05=%3d  p90=%3d"
                  % (i + 1, s["mean"], s["med"], s["p05"], s["p90"]))
        av = {k: round(sum(s[k] for s in stats) / len(stats), 1) for k in ("mean", "med", "p05", "p90")}
        bad = []
        if av["p05"] < 45:
            bad.append("暗部压死")
        if av["med"] < 130:
            bad.append("大面积偏黑")
        if av["mean"] < 120:
            bad.append("平均亮度偏低")
        print("   平均  mean=%.1f  med=%.0f  p05=%.0f  p90=%.0f   → %s | %s"
              % (av["mean"], av["med"], av["p05"], av["p90"],
                 " / ".join(bad) if bad else "OK", tag))
        print()


if __name__ == "__main__":
    main()
