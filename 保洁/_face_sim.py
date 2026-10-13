# -*- coding: utf-8 -*-
"""人脸身份一致性检测 —— 量化用户抱怨的「好几个人都是一张脸」。

为什么需要（2026-10-04）：
  帧间抖动/亮度**测不出身份混乱**。用户抱怨的是「前一秒一个人，
  后一秒钟又是另一个人」「好几个人都是一张脸」，这是 identity consistency，
  必须单独量化。本地 H3 是 4 步 + int8 量化，最容易在这上面翻车。

用 OpenCV 5 官方人脸模型（纯 CPU，不占显存，几秒一段）：
  检测：YuNet  face_detection_yunet_2023mar.onnx
  识别：SFace face_recognition_sface_2021dec.onnx
  SFace 输出 128 维人脸特征，用**余弦相似度**比对身份。

判定（SFace 官方口径：同一人 COS ≥ 0.363，不同人 < 0.363）：
  正常情况下一段里**不同角色**的相似度应远低于 0.363。
  如果「本该是不同人的几张脸」相似度 ≥ 0.363 → 就是用户说的「多人同脸」。

⚠️ OpenCV 5 移除了 `cv2.CascadeClassifier`（Haar 级联），
   别再写 `cv2.CascadeClassifier` —— 实测会 AttributeError。

用法：
  python _face_sim.py --seed            # Seedance 基线
  python _face_sim.py --local           # 本地已生成段
  python _face_sim.py --cmp             # 两边对比
  python _face_sim.py --dir "D:/output/new"
"""
import glob
import os
import subprocess
import sys

import cv2
import numpy as np

FFMPEG = r"E:\Program Files\ffmpeg\bin\ffmpeg.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "..", "_cmp", "models")
TMP = os.path.join(HERE, "..", "_cmp", "face")
SEED_DIR = "D:/output/Seedance"
LOCAL_DIR = "D:/output"

DET = os.path.join(MODELS, "face_detection_yunet_2023mar.onnx")
REC = os.path.join(MODELS, "face_recognition_sface_2021dec.onnx")
SAME_TH = 0.363          # SFace 官方：同一人 COS 阈值
IDENTITY_LEAK = 0.50     # 明显是同一人（比官方阈值严，防误判）


def _models():
    for p in (DET, REC):
        if not os.path.exists(p):
            print("缺少模型：%s" % p)
            print("下载：https://github.com/opencv/opencv_zoo/tree/main/models")
            sys.exit(1)


def frames_of(video, n=10):
    os.makedirs(TMP, exist_ok=True)
    for f in glob.glob(os.path.join(TMP, "*.png")):
        try:
            os.remove(f)
        except OSError:
            pass
    subprocess.run([FFMPEG, "-v", "error", "-i", video, "-vf", "fps=1",
                    "-frames:v", str(n), "-y", os.path.join(TMP, "f%02d.png")],
                   capture_output=True, timeout=240)
    return sorted(glob.glob(os.path.join(TMP, "*.png")))


def analyze(video, det, rec):
    """返回 (每帧人脸数, [(特征, 面积)])"""
    counts, feats = [], []
    for p in frames_of(video):
        img = cv2.imread(p)
        if img is None:
            continue
        h, w = img.shape[:2]
        # ⚠️ OpenCV 5 的 `detect` 返回 **(张数:int, ndarray[N,15])**，
        #    与旧版 OpenCV 的 `(faces, num)` **顺序相反**。
        #    按旧版写 `faces, _ = det.detect(img)` 会拿到 int → `len(int)` 报
        #    "object of type 'int' has no len()"。这里按新签名取。
        #    另外 YuNet 每次 detect 前必须 setInputSize 成实际图像尺寸。
        det.setInputSize((w, h))
        n, faces = det.detect(img)
        n = int(n)
        counts.append(n)
        if not n or faces is None:
            continue
        for f in faces:
            try:
                aligned = rec.alignCrop(img, f)
                feat = rec.feature(aligned)
                feats.append((feat.reshape(-1), float(f[2] * f[3])))
            except Exception:
                continue
    return counts, feats


def score(feats):
    """段内两两余弦相似度统计。

    ⚠️ 第一版把「相似度高」直接判成身份混乱，**这是错的**：
    同一个人在不同帧的 SFace 相似度本来就该高（0.85+），
    Seedance 实测也有 9 对「疑似同脸」，但它明显没有多人同脸问题。
    → 段内相似度只能看**离散度**（不同角色是否被拉成同一张脸），
      真正的身份一致性必须**跨段**比：同一角色在不同段是否还是那张脸。
    这里只返回统计量，判定交给跨段逻辑。
    """
    if len(feats) < 2:
        return None, None, 0
    a = np.array([f[0] for f in feats])
    a = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-8)
    sim = a @ a.T
    n = len(a)
    iu = np.triu_indices(n, k=1)
    vals = sim[iu]
    leak = int((vals >= IDENTITY_LEAK).sum())
    return float(vals.mean()), float(vals.max()), leak


def dominant_ratio(feats):
    """段内「疑似同一个身份」的占比：把每个特征与它的**质心**比。

    真正的判据：如果一段里**所有脸都互相像同一个身份**（含不同角色），
    说明身份被抹平了。做法：算全体质心，看多少比例的特征与质心相似度
    ≥ 阈值。多人同脸时这个比例会接近 1（全都一张脸）；
    正常多角色时质心居中，各角色分散，比例明显更低。
    """
    if len(feats) < 3:
        return None
    a = np.array([f[0] for f in feats])
    a = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-8)
    c = a.mean(axis=0)
    c /= (np.linalg.norm(c) + 1e-8)
    sims = a @ c
    return float((sims >= 0.55).mean())


def cross_seg(groups):
    """跨段身份一致性：每段取质心，两两比。

    groups: [(段名, feats)]
    同一角色跨段应该相似度高；如果**所有段**的质心都互相高度相似，
    说明不同段的角色被生成成同一张脸。
    返回 [(a, b, sim)]
    """
    cents = []
    for name, feats in groups:
        if len(feats) < 2:
            continue
        a = np.array([f[0] for f in feats])
        a = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-8)
        c = a.mean(axis=0)
        c /= (np.linalg.norm(c) + 1e-8)
        cents.append((name, c))
    out = []
    for i in range(len(cents)):
        for j in range(i + 1, len(cents)):
            out.append((cents[i][0], cents[j][0], float(cents[i][1] @ cents[j][1])))
    return out


def report(name, path, det, rec, groups=None):
    counts, feats = analyze(path, det, rec)
    mean, mx, leak = score(feats)
    dom = dominant_ratio(feats)
    med = sorted(counts)[len(counts) // 2] if counts else 0
    mxct = max(counts) if counts else 0
    if groups is not None:
        groups.append((name, feats))
    print(" %-26s 脸数中位=%d 最多=%d ｜ 特征%3d ｜ 段内均值%s 最大%s ｜ 同一身份占比%s" % (
        name[:26], med, mxct, len(feats),
        ("%.3f" % mean) if mean is not None else "-",
        ("%.3f" % mx) if mx is not None else "-",
        ("%.2f" % dom) if dom is not None else "-"), flush=True)
    return dict(name=name, face_median=med, face_max=mxct,
                sim_mean=mean, sim_max=mx, dominant=dom)


def main():
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    _models()
    det = cv2.FaceDetectorYN_create(DET, "", (320, 320), 0.6, 0.3, 5000)
    rec = cv2.FaceRecognizerSF.create(REC, "")

    d = LOCAL_DIR
    if "--dir" in sys.argv:
        d = sys.argv[sys.argv.index("--dir") + 1]
    want_seed = "--seed" in sys.argv or "--cmp" in sys.argv
    want_local = "--local" in sys.argv or "--cmp" in sys.argv

    if want_seed:
        print("Seedance 基准：", flush=True)
        g = []
        for f in sorted(glob.glob(os.path.join(SEED_DIR, "*.mp4"))):
            report("SD" + os.path.basename(f).split("冲突")[-1], f, det, rec, g)
        cs = cross_seg(g)
        if cs:
            print("\n  Seedance 跨段质心相似度：", flush=True)
            for a, b, s in cs:
                print("    %-14s ↔ %-14s %.3f" % (a[:14], b[:14], s))
    if want_local:
        print("\n本地成片：", flush=True)
        g = []
        for f in sorted(glob.glob(os.path.join(d, "ep01_t*_00001-audio.mp4")))[:3]:
            report(os.path.basename(f), f, det, rec, g)
        cs = cross_seg(g)
        if cs:
            print("\n  本地跨段质心相似度：", flush=True)
            for a, b, s in cs:
                print("    %-14s ↔ %-14s %.3f" % (a[:14], b[:14], s))
    print()
    print("怎么看：")
    print("  段内最大相似度高是**正常的**（同一个人跨帧本就该像）")
    print("  「同一身份占比」高 → 一段里所有人都长成同一张脸（身份被抹平）")
    print("  跨段质心相似度：不同段的角色若都高度相似 → 跨段身份漂移")


if __name__ == "__main__":
    main()
