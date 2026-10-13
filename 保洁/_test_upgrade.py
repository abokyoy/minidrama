# -*- coding: utf-8 -*-
"""画质升级验证：用同一段提示词，对比「现行 4 步」与「升级参数」的实际效果。

为什么需要它：
  用户实测 Seedance 出的片子明显比本地好（质感、连续性、人声）。
  根因不是提示词，而是我为了「跑得动」做的三处降级：
    ① 视频 VAE 是 int8 量化
    ② 扩散模型是 w4a8 4bit 量化
    ③ 采样只有 4 步（res_multistep 快速采样器）
  但直接全量重跑风险太大（ep001 已跑 70+ 段），必须先拿数据。

本脚本做的事：
  读现有 jobNN.json → 只改上面几个参数 → 另存成 test_*.json →
  提交给 ComfyUI 排队（ComfyUI 是串行队列，不会打断正在跑的主线段）。

用法：
  python _test_upgrade.py ep001 62      # 拿 t62 的提示词跑升级参数
  python _test_upgrade.py ep001 62 --steps 8 --refsize max
"""
import io
import json
import os
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = "D:/output"
SERVER = "http://127.0.0.1:8188"
# 扩散模型只有这两种 H3 权重可选（都是量化版，本机没有 bf16 原版）
H3_MODELS = [
    "minimax_h3_fused_refdelta_r1024_turbo8_mystic07_int8_convrot.safetensors",
    "minimax_h3_fl2va_pruned_w4a8_mixed.safetensors",
]
H3_VAE = "minimax_h3_video_vae_int8_convrot.safetensors"


def _noproxy():
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
              "ALL_PROXY", "all_proxy"):
        os.environ.pop(k, None)
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


OP = _noproxy()


def get(path):
    return json.load(OP.open(SERVER + path, timeout=30))


def post(path, body):
    req = urllib.request.Request(
        SERVER + path,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    return json.loads(OP.open(req, timeout=60).read().decode("utf-8"))


def load_api():
    p = os.path.join(BASE, "ep001_segs", "_last_api.json")
    if not os.path.exists(p):
        raise SystemExit("找不到 _last_api.json —— 先让主线跑完一段再试")
    return json.load(io.open(p, encoding="utf-8"))


def tweak(api, steps=None, refsize=None, model=None, megapixels=None, shift_v=None):
    api = json.loads(json.dumps(api))          # 深拷贝，别污染原件
    changed = []
    for nid, nd in api.items():
        if not isinstance(nd, dict):
            continue
        ct = nd.get("class_type")
        if ct == "BasicScheduler" and steps:
            nd["inputs"]["steps"] = int(steps)
            changed.append("steps=%d" % steps)
        elif ct == "MiniMaxH3ReferenceToVideo" and refsize:
            nd["inputs"]["ref_image_size"] = refsize
            changed.append("ref_image_size=%s" % refsize)
        elif ct == "UNETLoader" and model:
            nd["inputs"]["unet_name"] = model
            changed.append("unet=%s" % model.split("_")[2])
        elif ct == "ResolutionSelector" and megapixels:
            if "megapixels" in nd.get("inputs", {}):
                nd["inputs"]["megapixels"] = float(megapixels)
                changed.append("megapixels=%.2f" % megapixels)
        elif ct == "MiniMaxH3SigmaShift" and shift_v:
            nd["inputs"]["shift_video"] = float(shift_v)
            changed.append("shift_video=%.1f" % shift_v)
    return api, changed


def queue_wait(pid, timeout_min=90):
    t0 = time.time()
    while time.time() - t0 < timeout_min * 60:
        time.sleep(10)
        h = get("/history/" + pid)
        if pid in h:
            return h[pid]
    raise SystemExit("超时 %d 分钟仍未完成" % timeout_min)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ep = sys.argv[1] if len(sys.argv) > 1 else "ep001"
    seg = sys.argv[2] if len(sys.argv) > 2 else "62"

    def opt(name, default):
        if name in sys.argv:
            i = sys.argv.index(name)
            return sys.argv[i + 1]
        return default

    steps = int(opt("--steps", 8))
    refsize = opt("--refsize", "max")
    megapixels = float(opt("--megapixels", 0)) or None
    model = opt("--model", H3_MODELS[0])
    tag = opt("--tag", "8step_max")

    api = load_api()
    api, changed = tweak(api, steps=steps, refsize=refsize,
                         model=model, megapixels=megapixels)
    api["142"]["inputs"]["shift_video"] = 12.0
    prefix = "TEST_%s_t%s_%s" % (ep, seg, tag)
    for nid, nd in api.items():
        if isinstance(nd, dict) and nd.get("class_type") == "VHS_VideoCombine":
            nd["inputs"]["filename_prefix"] = prefix

    print("=" * 60)
    print(" 画质升级验证  %s  段=%s" % (ep, seg))
    print(" 改动：%s" % ("、".join(changed) or "（无）"))
    print(" 产出前缀：%s" % prefix)
    print("=" * 60)
    print(" 提交（ComfyUI 串行排队，不会打断正在跑的主线段）…")

    pid = post("/prompt", {"prompt": api, "client_id": "upg_test"})["prompt_id"]
    print(" prompt_id = %s" % pid)
    print(" 预计 8 步比 4 步慢 2~3 倍，请耐心等它排到。")

    h = queue_wait(pid, timeout_min=120)
    outs = h.get("outputs", {})
    print(" 完成。")
    for nid, o in outs.items():
        for k in ("gifs", "videos", "images"):
            for it in o.get(k, []) or []:
                fn = it.get("filename", "")
                sub = it.get("subfolder", "")
                print("   → %s" % os.path.join(OUT, sub, fn) if sub else "   → %s" % os.path.join(OUT, fn))
    print("\n抽帧对比：")
    print("  ffprobe 对比码率/分辨率，或直接看 D:\\output\\%s*.mp4" % prefix)


if __name__ == "__main__":
    main()
