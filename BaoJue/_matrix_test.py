# -*- coding: utf-8 -*-
"""画质参数矩阵测试 v2 —— 按显存预算重新设计。

⚠️ 关键实测（2026-10-04 14:25，nvidia-smi 连续采样）：
    ComfyUI 跑 1 段 H3 时显存稳定占用 **15.6 GB / 16 GB，只剩 561 MB**。
    也就是说**现在的 4 步 + 0.75MP 已经把显存吃满了**。

→ 之前想的「8 步」很可能直接 OOM；「1.0MP 分辨率」也一样会 OOM。
   **必须先找出哪些参数不增显存就能提升质量。**

不增显存的项（可以放心测）：
    ① ref_image_size : match → max
       官方 tooltip：max 走参考管线的 2048px 短边，身份保真最好。
       代价是慢（每步都要重跑参考图编码），但**峰值显存不变**。
    ② scheduler     : simple → sgm_uniform
       纯调度器换法，不改张量形状，显存不变。
    ③ KSamplerSelect : res_multistep → uni_pc / dpmpp_2m
       同样不增显存。
    ④ 音频          : 后期重采样到 48kHz（不影响画面）

可能增显存的项（谨慎，逐个单独试）：
    ⑤ steps 4→8      采样器缓存不随步数增长，理论上峰值不变，但要实测
    ⑥ megapixels 0.75→1.0   一定 OOM，暂不测

测试顺序（每组只改一项，串行提交，共用同一份 t62 提示词）：
    A  基线        steps=4  simple  res_multistep  match  0.75MP
    B  身份锚定    steps=4  simple  res_multistep  max    0.75MP   ← 重点
    C  采样器      steps=4  simple  uni_pc         match  0.75MP
    D  调度器      steps=4  sgm_uni res_multistep  match  0.75MP
    E  步数        steps=8  simple  res_multistep  max    0.75MP   ← 重点
    F  组合        steps=6  sgm_uni uni_pc         max    0.75MP

用法：
  python _matrix_test.py            # 只生成配置
  python _matrix_test.py --run      # 提交
  python _matrix_test.py --run --only B
"""
import copy
import io
import json
import os
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
SRC_API = os.path.join(BASE, "ep001_segs", "_last_api.json")
OUTDIR = os.path.join(BASE, "ep001_segs", "matrix")
SERVER = "http://127.0.0.1:8188"

MATRIX = {
    "A": dict(steps=4, sch="simple",      smp="res_multistep", ref="match", mp=0.75, tag="base"),
    "B": dict(steps=4, sch="simple",      smp="res_multistep", ref="max",   mp=0.75, tag="refmax"),
    "C": dict(steps=4, sch="simple",      smp="uni_pc",        ref="match", mp=0.75, tag="unipc"),
    "D": dict(steps=4, sch="sgm_uniform", smp="res_multistep", ref="match", mp=0.75, tag="sgmuni"),
    "E": dict(steps=8, sch="simple",      smp="res_multistep", ref="max",   mp=0.75, tag="8step_refmax"),
    "F": dict(steps=6, sch="sgm_uniform", smp="uni_pc",        ref="max",   mp=0.75, tag="combo"),
}

ORDER = ["A", "B", "C", "D", "E", "F"]


def op_():
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
              "ALL_PROXY", "all_proxy"):
        os.environ.pop(k, None)
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def build(cfg):
    api = copy.deepcopy(json.load(io.open(SRC_API, encoding="utf-8")))
    prefix = "MT2_%s" % cfg["tag"]
    log = []
    for nid, nd in api.items():
        if not isinstance(nd, dict):
            continue
        ct, ins = nd.get("class_type"), nd.get("inputs", {})
        if ct == "BasicScheduler":
            ins["steps"] = cfg["steps"];      ins["scheduler"] = cfg["sch"]
            log.append("steps=%d" % cfg["steps"]); log.append("sch=%s" % cfg["sch"])
        elif ct == "KSamplerSelect":
            ins["sampler_name"] = cfg["smp"]; log.append("smp=%s" % cfg["smp"])
        elif ct == "MiniMaxH3ReferenceToVideo":
            ins["ref_image_size"] = cfg["ref"]; log.append("ref=%s" % cfg["ref"])
        elif ct == "ResolutionSelector" and "megapixels" in ins:
            ins["megapixels"] = cfg["mp"];    log.append("mp=%.2f" % cfg["mp"])
        elif ct == "VHS_VideoCombine":
            ins["filename_prefix"] = prefix
    return api, prefix, log


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    run = "--run" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].upper()

    os.makedirs(OUTDIR, exist_ok=True)
    ids = [only] if only else ORDER
    print("=" * 70)
    print(" 画质参数矩阵 v2（显存预算版）")
    print(" 实测：现设置已占 15.6/16GB，剩 561MB → 升分辨率必 OOM，只测不增显存的项")
    print("=" * 70)
    for k in ids:
        cfg = MATRIX[k]
        api, prefix, log = build(cfg)
        json.dump(api, io.open(os.path.join(OUTDIR, "api_%s.json" % k), "w",
                               encoding="utf-8"), ensure_ascii=False, indent=1)
        print(" [%s] %-14s %s" % (k, cfg["tag"], " ".join(log)))
    if not run:
        print("\n（只生成配置了。加 --run 提交）")
        return

    print("\n提交中…")
    for k in ids:
        cfg = MATRIX[k]
        api, prefix, _ = build(cfg)
        try:
            req = urllib.request.Request(
                SERVER + "/prompt",
                data=json.dumps({"prompt": api, "client_id": "mt2"}).encode("utf-8"),
                headers={"Content-Type": "application/json"})
            pid = json.loads(op_().open(req, timeout=180).read().decode("utf-8"))["prompt_id"]
            io.open(os.path.join(OUTDIR, "pid_%s.txt" % k), "w",
                    encoding="utf-8").write(pid)
            print(" [%s] %-14s pid=%s" % (k, cfg["tag"], pid))
        except Exception as e:
            print(" [%s] 失败：%s" % (k, str(e)[:200]))
            return
        time.sleep(2)
    print("\n提交完毕。结果：python _matrix_result.py")


if __name__ == "__main__":
    main()
