# -*- coding: utf-8 -*-
"""手动跑片时同步台账状态到 SQLite（show_ledger.db）。

⛔ 2026-10-11 踩坑：网页只读 show_ledger.db，不直接读 JSON；
   之前手改 JSON 白改，网页永远显示旧状态。
   手动 `_run_one.py` 跑片不会回写 DB，所以每跑一片都要在这里
   标 running / done，网页「正在生成」才不会串到片1。

用法：
  python seg_mark.py 3 running            # 提交时标 生成中
  python seg_mark.py 3 done OUT_PATH      # 落盘后标 已完成 + 成片路径
  python seg_mark.py 3 running --epoch    # 顺带写入 ComfyUI 队列起跑时间
"""
import sys, time, json
import show_ledger as L


def main():
    if len(sys.argv) < 3:
        print("用法: seg_mark.py <seg> running|done [out_path] [--epoch]")
        return
    seg = str(sys.argv[1])
    st = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else None
    epoch = "--epoch" in sys.argv

    led = L.load()
    sg = led["segments"][seg]
    sg["status"] = st
    if out:
        sg["out"] = out
    if st == "running":
        sg["out"] = None  # 正在重跑，旧成片路径先清空，网页才不挂旧片
        if epoch:
            import os, urllib.request
            for k in list(os.environ):
                if "proxy" in k.lower():
                    os.environ.pop(k)
            try:
                q = json.loads(urllib.request.build_opener(
                    urllib.request.ProxyHandler({})).open(
                    "http://127.0.0.1:8189/queue", timeout=5).read())
                for it in (q.get("queue_running") or []):
                    if isinstance(it, list) and len(it) >= 4 \
                            and isinstance(it[3], dict):
                        ct = it[3].get("create_time")
                        if isinstance(ct, (int, float)):
                            sg["run_epoch"] = ct / 1000.0
                            sg["started_at"] = time.strftime(
                                "%H:%M:%S", time.localtime(ct / 1000.0))
                            break
            except Exception:
                pass
        if "run_epoch" not in sg:
            sg["run_epoch"] = time.time()
            sg["started_at"] = time.strftime("%H:%M:%S")
    L.save(led)
    print("seg%s -> %s | out=%s" % (seg, st, sg.get("out")))


if __name__ == "__main__":
    main()
