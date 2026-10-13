# -*- coding: utf-8 -*-
"""画质参数矩阵测试 v3 —— 依据 SLA 节点官方 tooltip 重新设计。

⭐ 本轮关键发现（读 `sla_node.py` 的 tooltip 得出，不是猜的）：

  ① **步数才是主因，不是稀疏采样**
     官方原话：Sparsity did NOT turn out to drive the speech artefacts on
     H3 — step count did, so use 6 steps rather than lowering this.
     → 我们现在是 **4 步**，官方建议 **6 步**。这是最大的一处失配。

  ② **dense_steps 当前是 "0"（不是关掉！）**
     查 `patch.py` 第 993 行确认：
         to["_h3sla_dense"] = (dense_last_steps>0 and step>n_steps-dense_last_steps)
                             or step0 in dense_steps
     我们工作流里 dense_steps="0" → 第 0 步**已经**走全注意力。
     ⚠️ 我一度误判成"等于没开"，看了实现才确认，这里记下来别再搞错。
     真正没开的是 **dense_last_steps=0**（最后一步没有全注意力）。
     官方对它的说明是：「the final step's error is the one you actually
     see，1 步的成本能换回细节」→ 这是独立于 dense_steps 的第二个杠杆。

  ③ **reference_protection = "Off"** → 参考图/参考视频走普通 top-k，
     身份信息可能被采样丢掉 → **好几个人都是一张脸**。
     "Light" 只用固定 0.85 参考稀疏率，代价极小。
     ⚠️ "Heavy Enforcement" 官方明说在 **max 参考图尺寸下基本不可用**，
        所以只在 match 尺寸下考虑 heavy。

  ④ **stabilize_motion = False** → 官方说明：快动作时相邻两步的块选择
     会无理由翻转，表现为**淡淡的重复曝光/重影**。这正是"人物跳跃、
     动作不连续"。注意：源码注释提到它会多占几 GB 显存
     （"grow to several GB per run at 768p"），必须实测是否 OOM。

  ⑤ **tail_correction = False** → 被丢掉的注意力尾部直接归零。开启后
     用一个池化项把尾部补回 softmax，让「没有任何注意力归零」，
     官方说"在高稀疏率下收益最大"，代价只是多一次 mean-pool。

所以第二批测试围绕这几项，不再测边际收益很低的采样器/调度器换法。

分组（每组只动一项或一组强相关项）：
  A  基线        现设置原样（4步/全稀疏/Off），用于客观对照
  G  6step       只把 4→6 步                     ← 官方推荐，预期主收益
  H  denselast   dense_last_steps=1（最后一步全注意力）← 官方称"看得见的误差"
  I  reflight    reference_protection=Light        ← 治多人一张脸
  J  tail        tail_correction=True             ← 治动作扭曲
  K  stabilize   stabilize_motion=True            ← 治重影/跳跃（可能 OOM）
  L  组合        6步 + dense_last=1 + Light + tail  ← 最终候选

用法：
  python _matrix2_test.py             # 只生成配置
  python _matrix2_test.py --run       # 提交
  python _matrix2_test.py --run --only G
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
OUTDIR = os.path.join(BASE, "ep001_segs", "matrix2")
SERVER = "http://127.0.0.1:8188"

# 每组只写与基线不同的项；未写的沿用现设置。
# dlast  -> H3SLAAttention 的 dense_last_steps（最后 N 步走全注意力）
MATRIX = {
    "A": dict(tag="base",     steps=None),
    "G": dict(tag="6step",    steps=6),
    "H": dict(tag="denselast", dlast=1),
    "I": dict(tag="reflight", refprot="Light"),
    "J": dict(tag="tail",     tail=True),
    "K": dict(tag="stabil",   stabilize=True),
    "L": dict(tag="combo6",   steps=6, dlast=1, refprot="Light", tail=True),
}

ORDER = ["A", "G", "H", "I", "J", "K", "L"]


def op_():
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
              "ALL_PROXY", "all_proxy"):
        os.environ.pop(k, None)
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def build(cfg):
    api = copy.deepcopy(json.load(io.open(SRC_API, encoding="utf-8")))
    prefix = "MT3_%s" % cfg["tag"]
    log = []
    for nid, nd in api.items():
        if not isinstance(nd, dict):
            continue
        ct, ins = nd.get("class_type"), nd.get("inputs", {})
        if ct == "BasicScheduler" and cfg.get("steps"):
            ins["steps"] = cfg["steps"]
            log.append("steps=%d" % cfg["steps"])
        elif ct == "H3SLAAttention":
            if cfg.get("dlast") is not None:
                ins["dense_last_steps"] = cfg["dlast"]
                log.append("dlast=%d" % cfg["dlast"])
            if cfg.get("refprot"):
                ins["reference_protection"] = cfg["refprot"]
                log.append("refprot=%s" % cfg["refprot"])
            if cfg.get("tail") is not None:
                ins["tail_correction"] = bool(cfg["tail"])
                log.append("tail=%s" % cfg["tail"])
            if cfg.get("stabilize") is not None:
                ins["stabilize_motion"] = bool(cfg["stabilize"])
                log.append("stabil=%s" % cfg["stabilize"])
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
    print(" 画质参数矩阵 v3（依据 SLA 官方 tooltip）")
    print(" 官方结论：说话/动作问题的主因是「步数不足」而不是稀疏采样 → 建议 6 步")
    print(" 当前 4 步；dense_steps=0 已含第0步，真正缺的是 dense_last_steps=0（末步全注意力）")
    print("=" * 70)
    for k in ids:
        cfg = MATRIX[k]
        api, prefix, log = build(cfg)
        json.dump(api, io.open(os.path.join(OUTDIR, "api_%s.json" % k), "w",
                               encoding="utf-8"), ensure_ascii=False, indent=1)
        print(" [%s] %-10s %s" % (k, cfg["tag"], " ".join(log) or "(同基线)"))
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
                data=json.dumps({"prompt": api, "client_id": "mt3"}).encode("utf-8"),
                headers={"Content-Type": "application/json"})
            pid = json.loads(op_().open(req, timeout=180).read().decode("utf-8"))["prompt_id"]
            io.open(os.path.join(OUTDIR, "pid_%s.txt" % k), "w",
                    encoding="utf-8").write(pid)
            print(" [%s] %-10s pid=%s" % (k, cfg["tag"], pid))
        except Exception as e:
            print(" [%s] 失败：%s" % (k, str(e)[:300]))
            return
        time.sleep(2)
    print("\n提交完毕。结果：python _matrix_result.py --set matrix2")


if __name__ == "__main__":
    main()
