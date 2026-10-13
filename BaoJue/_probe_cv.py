# -*- coding: utf-8 -*-
import cv2, os, subprocess
DET = os.path.abspath('../_cmp/models/face_detection_yunet_2023mar.onnx')
det = cv2.FaceDetectorYN_create(DET, '', (320, 320), 0.6, 0.3, 5000)
p = os.path.abspath('../_cmp/face/t.png')
os.makedirs(os.path.dirname(p), exist_ok=True)
subprocess.run([r'E:/Program Files\ffmpeg\bin\ffmpeg.exe', '-v', 'error', '-ss', '2',
                '-i', 'D:/output/Seedance/清洁女工与富客走廊冲突 (1).mp4',
                '-frames:v', '1', '-y', p], capture_output=True, timeout=120)
im = cv2.imread(p)
h, w = im.shape[:2]
det.setInputSize((w, h))
r = det.detect(im)
print('返回:', type(r).__name__, '长度', len(r))
for i, x in enumerate(r):
    sh = getattr(x, 'shape', None)
    print('  [%d] %-10s shape=%s' % (i, type(x).__name__, sh))
