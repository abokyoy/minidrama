# -*- coding: utf-8 -*-
"""对比 I 组(参考保护=Light) 与 4 步基线 的身份一致性。"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("fs", "_face_sim.py")
fs = importlib.util.module_from_spec(spec); spec.loader.exec_module(fs)
fs._models()
det = __import__("cv2").FaceDetectorYN_create(fs.DET, "", (320, 320), 0.6, 0.3, 5000)
rec = __import__("cv2").FaceRecognizerSF.create(fs.REC, "")
groups = []
rows = []
print("本组对比（同 t62 提示词）：")
for tag, p in [("4步基线",   r"D:/output/ep01_t62_00001-audio.mp4"),
               ("G 6步",     r"D:/output/MT3_G_00001-audio.mp4"),
               ("H 末步全注意力", r"D:/output/MT3_H_00001-audio.mp4"),
               ("I 参考保护Light", r"D:/output/MT3_I_00001-audio.mp4")]:
    if not os.path.exists(p):
        print("  缺 %s" % p); continue
    rows.append(fs.report(tag, p, det, rec, groups))
print()
print("跨段质心相似度（越低说明不同角色越能区分）：")
for a, b, s in fs.cross_seg(groups):
    print("  %-16s ↔ %-16s %.3f" % (a[:16], b[:16], s))
