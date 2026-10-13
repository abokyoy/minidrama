# -*- coding: utf-8 -*-
"""抽帧 + 人脸计数：定位「人物复制」出现在第几秒、复制出几张脸。

为什么要脚本：肉眼拖进度条会漏掉只出现 0.5 秒的复制帧。
本项目已装 OpenCV 5 + FaceDetectorYN（见 _face_sim.py），纯 CPU。
用法：python _frame_dump.py D:\\output\\new\\xs01_t01_00001.mp4 [步长帧]
"""
import os
import sys
import shutil
import subprocess

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)

VIDEO = sys.argv[1] if len(sys.argv) > 1 else r"D:\output\new\xs01_t01_00001.mp4"
STEP = int(sys.argv[2]) if len(sys.argv) > 2 else 12
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_frames", "t01")
TMP = r"E:\LLM\try\minidrama\_frames_ascii"
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

base = os.path.splitext(os.path.basename(VIDEO))[0]
print("抽帧 →", OUT)

# 1) ffmpeg 抽帧（比逐帧解码快得多）
r = subprocess.run(
    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", VIDEO,
     "-vf", "fps=24/%d" % STEP, "-q:v", "2", os.path.join(OUT, "f%04d.jpg")],
    capture_output=True, timeout=600)
if r.returncode:
    print("FFMPEG ERR:", (r.stderr or b"").decode("utf-8", "replace")[:400])
fr = sorted(f for f in os.listdir(OUT) if f.startswith("f") and f.endswith(".jpg"))
print("共 %d 帧（每 %d 帧 = %.2f 秒）" % (len(fr), STEP, STEP / 24.0))

# 2) 逐帧数脸
try:
    import cv2
    DET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_cmp", "models",
                       "face_detection_yunet_2023mar.onnx")
    det = cv2.FaceDetectorYN.create(DET, "", (320, 320), 0.6, 0.3, 5000)
except Exception as e:
    print("人脸检测不可用（%s），只抽帧" % e)
    det = None

for f in fr:
    idx = int(f[1:5])
    sec = idx * STEP / 24.0
    if det is None:
        print("  f%04d  %5.1fs" % (idx, sec))
        continue
    # ⚠️ OpenCV 5 的 imread 读不了含中文的路径（会静默返回 None），
    # 所以先拷到纯 ASCII 临时目录再读。ffmpeg 反而能正常处理中文路径。
    src = os.path.join(OUT, f)
    tmp = os.path.join(TMP, f)
    if not os.path.exists(tmp):
        shutil.copyfile(src, tmp)
    img = cv2.imread(tmp)
    if img is None:
        print("  f%04d  %5.1fs  读取失败" % (idx, sec))
        continue
    h, w = img.shape[:2]
    det.setInputSize((w, h))
    n, faces = det.detect(img)
    n = int(n)
    flag = "  ❗❗ 多脸!" if n >= 3 else ("  ⚠️" if n == 2 else "")
    print("  f%04d  %5.1fs  %dx%d  脸=%d%s" % (idx, sec, w, h, n, flag))
    if n >= 2:
        for i, fc in enumerate(faces):
            x, y, fw, fh = fc[:4]
            print("        #%d  x=%.0f y=%.0f w=%.0f h=%.0f  score=%.2f"
                  % (i, x, y, fw, fh, fc[-1]))
