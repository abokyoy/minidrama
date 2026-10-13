# -*- coding: utf-8 -*-
r"""
实时进度看板 —— 单独开一个窗口，实时显示当前生成进度。

用法（生成的同时，另开一个终端跑）：
    python _progress.py            # 盯 8189 官方实例
    python _progress.py --port 8188
    python _progress.py --loop     # 生成结束后不退出，继续等下一段

为什么需要它：
  ComfyUI 启动分两种模式
    show=True （默认）→ 弹一个**可见黑窗口**，你直接看那个窗口
    show=False        → 后台跑，stdout 进 logs/comfy_*.log，屏幕啥也看不到
  这个看板是第三种「不占窗口也能看」的办法：读 ComfyUI 的
  /system_stats + /queue + 日志尾部，把 8 步采样进度画成进度条。

⛔ 它**只读不写**，不会碰 ComfyUI 的队列，不会干扰生成。
"""
import os, sys, time, json, re, argparse

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
           "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)
os.environ["no_proxy"] = "127.0.0.1,localhost"
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
# ⛔⛔ 2026-10-08 15:53 踩坑记录：
#   show=True（可见窗口）模式下，子进程**不继承 stdout 重定向**，所以
#   「项目 logs/comfy_official.log」和「我造的 console 日志」**都不会被写**。
#   唯一可靠的进度来源 = ComfyUI **自己**的日志（--user-directory 指定的那个）。
#   这条路径是项目自己配的、带 --log 才有，但实测它一直在写采样进度。
LOG = r"E:\ComfyUI\ComfyUI_h3official\user\comfyui_8189.log"
LOG_FALLBACK = os.path.join(HERE, "logs", "comfy_official.log")


def get(path, port, timeout=4):
    with urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, path),
                                timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def bar(pct, width=28, ch_done="#", ch_todo="-"):
    n = int(width * max(0.0, min(1.0, pct)))
    return ch_done * n + ch_todo * (width - n)


def read_tail(path, n=4000):
    """读日志尾部。⛔ 必须把 \\r 也换成 \\n —— ComfyUI 的 tqdm 进度条是用
     carriage return 覆盖同一行刷新，不换行。不处理的话 800 次刷新挤成一行，
    正则匹配不到 → 进度条永远停在 0%。"""
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            sz = f.tell()
            f.seek(max(0, sz - n))
            return f.read().decode("utf-8", "replace").replace("\r", "\n")
    except Exception:
        return ""


# ComfyUI 进度行长这样（⛔ 用 \r 覆盖同一行，不是换行）：
#   "  0%|          | 0/8 [00:00<?, ?it/s]"
#   " 50%|████      | 4/8 [06:12<?,  1.08s/it]"
#   "100%|██████████| 8/8 [12:24<?,  1.55s/it]"
# 之前踩坑：① 只按 \n 匹配 → 整段被当成一行，正则匹配不到 → 永远显示 0%
#          ② 没考虑 \r → 同一个采样过程的所有刷新行挤在一起
STEP_RE = re.compile(
    r"(\d{1,3})%\|[^|]*\|\s*(\d+)/(\d+)\s*\[([^\]]*)\]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8189)
    ap.add_argument("--loop", action="store_true", help="跑完继续等下一段")
    args = ap.parse_args()

    print("=" * 62)
    print(" 实时进度看板  端口 %d" % args.port)
    print(" 只读，不干扰生成。Ctrl+C 退出看板（不影响生成）")
    print("=" * 62)

    last_pct = -1
    while True:
        try:
            stats = get("/system_stats", args.port)
            q = get("/queue", args.port)
        except Exception as e:
            print("[%s] 连不上 ComfyUI（%s）"
                  % (time.strftime("%H:%M:%S"), e.__class__.__name__))
            if not args.loop:
                return
            time.sleep(5)
            continue

        running = q.get("queue_running") or []
        pending = q.get("queue_pending") or []
        dev = stats.get("devices", [{}])[0]
        vram = dev.get("vram_free", 0) / 1073741824.0
        vram_total = dev.get("vram_total", 1) / 1073741824.0

        # ⚠️ 两个日志都要看：show=True（默认，可见窗口）写 console 日志到纯 ASCII 目录，
        #    show=False（后台）写 logs/comfy_official.log。哪个新用哪个。
        txt = read_tail(LOG, 12000) or read_tail(LOG_FALLBACK, 12000)
        m = STEP_RE.findall(txt)
        pct, cur, tot, desc = 0, 0, 0, ""
        if m:
            pct_s, cur, tot, desc = m[-1]
            pct = int(pct_s)
        # ⛔ 第 0 步是「模型加载」，实测要 195–214 秒，期间**没有百分比**，
        #    不是卡死。不给提示的话会以为死了。
        note = ""
        if cur == 0 and "Initializing" in txt[-400:]:
            note = "  ← 模型加载中（实测 195-214 秒，正常的，不是卡死）"
        elif m and pct == 100:
            note = "  ← 采样完成，正在解码（1-2 分钟没百分比也正常）"

        print("\r" + " " * 100, end="")
        head = "%s [%s] %3d%%  步 %s/%s" % (
            time.strftime("%H:%M:%S"), bar(pct), pct, cur, tot)
        print("%-100s" % head, end="", flush=True)

        if not running and not pending:
            print()
            print("[%s] ★ 队列空（生成结束或还没提交）" % time.strftime("%H:%M:%S"))
            if not args.loop:
                print("  产物目录 D:\\output_h3off")
                return
        else:
            print("   显存空闲 %.1f/%.1f GB | 运行 %d 等待 %d%s"
                  % (vram, vram_total, len(running), len(pending), note))
        time.sleep(3 if pct > 0 and pct < 100 else 6)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n看板退出（生成继续）")
