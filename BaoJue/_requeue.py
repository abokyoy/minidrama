# -*- coding: utf-8 -*-
"""重排 ComfyUI 测试队列：清掉低价值项，按「预期收益 × 确定性」重排。

为什么重排（2026-10-04）：
  v2 队列里 C（换 uni_pc 采样器）、D（换 sgm_uniform 调度器）属边际微调，
  而 SLA 节点官方 tooltip 指出真正的主因是**采样步数只有 4 步**，
  且我们把 dense_steps 设成了 0（等于把「定构图」的第 0 步也稀疏掉了）。
  每段测试要 10–16 分钟，队列必须按价值排序，不能让低价值项占着前面。

已完成的 b6dea842（8步+refmax 单测）正好覆盖「步数」这一条，保留不动。

用法：
  python _requeue.py --show          # 只看当前队列
  python _requeue.py --clear-pending  # 清掉排队中的（正在跑的不动）
  python _requeue.py --order         # 按优先级重新提交 v3 + 保留的 v2
"""
import io
import json
import os
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
SERVER = "http://127.0.0.1:8188"

# 优先级顺序：越靠前越先跑。
# 说明见每行注释。
#
# ⚠️ 2026-10-04 14:37 实测事故：v2 的 E 组（8步 + ref_image_size=max）
#    在 0/8 步的「Model Initializing」阶段就 CUDA OOM，
#    而且**把整个 ComfyUI 进程拖崩了**（不是单任务失败，是服务挂掉）：
#        0%|          | 0/8 [02:47<?, ?it/s,   Model Initializing ...  ]
#        [ERROR] aimdo: hostbuf_read_file_slice: device copy failed
#        torch.AcceleratorError: CUDA error: out of memory
#    → 「8步 + max 参考图」在本机 16GB 上**确认不可行**，已从计划里去掉。
#    剩下唯一还带 max 的是 B（4步 + max），显存峰值与基线相同（已实测）。
PRIORITY = [
    ("matrix2", "G"),   # 6 步 —— 官方 tooltip 直接点名的主因
    ("matrix2", "H"),   # dense_last_steps=1 —— 官方称"看得见的误差"
    ("matrix2", "I"),   # reference_protection=Light —— 治多人一张脸
    ("matrix2", "J"),   # tail_correction —— 治动作扭曲
    ("matrix2", "L"),   # 组合：6步+dense_last=1+Light+tail
    ("matrix2", "K"),   # stabilize_motion —— 治重影/跳跃（可能 OOM，放最后）
    ("matrix",  "B"),   # ref_image_size=max（4步，峰值同基线）
    ("matrix",  "F"),   # v2 组合（6步+max，中等风险）
]

DIRMAP = {"matrix2": "matrix2", "matrix": "matrix"}


def op_():
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
              "ALL_PROXY", "all_proxy"):
        os.environ.pop(k, None)
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def api_path(which, key):
    return os.path.join(BASE, "ep001_segs", DIRMAP[which], "api_%s.json" % key)


def show():
    q = json.loads(op_().open(SERVER + "/queue", timeout=30).read())
    print("=" * 60)
    print(" 运行中 %d，排队 %d" % (len(q.get("queue_running", [])),
                                  len(q.get("queue_pending", []))))
    print("=" * 60)
    for it in q.get("queue_running", []):
        print("  RUN  %s" % it[1])
    for i, it in enumerate(q.get("queue_pending", [])):
        print("  WAIT %s  (第 %d 位)" % (it[1], i + 1))


def clear_pending():
    # queue_running / queue_pending 的元素都是
    #   [队列序号(int), prompt_id(str), workflow(dict), extra(dict), 输出节点(list)]
    # prompt_id 在 index **1**，不是 0（踩过一次：it[0] 是序号，报 'int' has no 'subscript'）
    q = json.loads(op_().open(SERVER + "/queue", timeout=30).read())
    pend = [it[1] for it in q.get("queue_pending", [])]
    if not pend:
        print("排队区本来就是空的。")
        return
    for pid in pend:
        try:
            op_().open(urllib.request.Request(
                SERVER + "/queue", data=json.dumps({"delete": [pid]}).encode(),
                headers={"Content-Type": "application/json"}), timeout=30)
            print("  已移除 %s" % pid[:8])
        except Exception as e:
            print("  移除 %s 失败：%s" % (pid[:8], str(e)[:120]))
        time.sleep(0.3)


def order():
    print("按优先级重新提交：")
    for which, key in PRIORITY:
        p = api_path(which, key)
        if not os.path.exists(p):
            print(" [%s/%s] 缺少配置，跳过" % (which, key))
            continue
        api = json.load(io.open(p, encoding="utf-8"))
        # 改输出前缀，标注批次，避免和旧结果混淆
        for nd in api.values():
            if isinstance(nd, dict) and nd.get("class_type") == "VHS_VideoCombine":
                nd["inputs"]["filename_prefix"] = "MT3_%s" % key
        try:
            req = urllib.request.Request(
                SERVER + "/prompt",
                data=json.dumps({"prompt": api, "client_id": "requeue"}).encode("utf-8"),
                headers={"Content-Type": "application/json"})
            pid = json.loads(op_().open(req, timeout=180).read().decode("utf-8"))["prompt_id"]
            io.open(os.path.join(BASE, "ep001_segs", DIRMAP[which],
                                 "pid_%s.txt" % key), "w",
                    encoding="utf-8").write(pid)
            print(" [%s/%s] pid=%s" % (which, key, pid))
        except Exception as e:
            print(" [%s/%s] 失败：%s" % (which, key, str(e)[:200]))
        time.sleep(1.5)
    print("\n完成。跑完后：python _matrix_result.py --set matrix2")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--clear-pending" in sys.argv:
        clear_pending()
    elif "--order" in sys.argv:
        order()
    else:
        show()
