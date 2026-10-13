# -*- coding: utf-8 -*-
"""短剧调度看板 · 后台服务
════════════════════════════════════════════════════════════════════

用户 2026-10-09 要求（原话）：
  「你先做一个服务，然后就是做一个网站服务，然后我可以访问这个网页……
    它应该有这些功能，就是就是我们先做一个最小子功能，就是这个任务的查看，
    任务运行情况的查看……在网页上用图形化的形式能够显示这个任务的运行情况，
    并且的话可以直接在网页上预览这个生成的视频。」

⛔⛔⛔ 三条设计铁律：
  ① **零依赖**：只用 Python 标准库。不装 fastapi/flask —— 装包要走代理、
     会拖慢、还可能把正在跑的 GPU 环境搞坏。`http.server` 足够。
  ② **只读台账，绝不写**：这个服务是**看**的，不是调度器。
     改状态只能走 `reject` / `resume` 指令，且**转发给 scheduler.py**执行，
     不在这里直接改 show_ledger.json → 避免两个进程打架写坏台账。
  ③ **视频必须支持 Range**：`<video>` 要能拖进度条，静态文件服务不做
     Range 的话浏览器只能从头播到底，而且会整支下载。
"""

import io
import json
import mimetypes
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import show_ledger as L            # noqa: E402
# ⛔ 档位常量与调度器同源，避免两边写死两个值（改一处就不同步）
PROFILE_PREVIEW = "preview25"
PROFILE_FINAL = "hd_turbo8"

OUT_DIR = r"D:\output_h3off"
WEB = os.path.join(HERE, "web")
PORT = 8848
COMFY_PORT = 8189
SCRIPT_MD = os.path.join(HERE, "ep001", "文字剧本.md")

# ══════════════════════════════════════════════════════════════
# 片 → 剧本行号区间
# 用户 2026-10-10 要求（原话）：
#   「脚本 和 H3的提示词 都给我 …… 你在网页上也在片 预览 下方新增tab
#     把这个片的 脚本、H3提示词 都显示」
#
# ⛔ 8 片全部出自剧本「场次 1-2」（188–400 行区间），行号是从
#   `ep001/文字剧本.md` 逐行核对出来的，**改剧本必须重核这里**。
#   每片给「本片台词 + 前后各留一点动作描述」，这样网页上
#   能看出这句台词在剧本的哪个位置。
# ══════════════════════════════════════════════════════════════
SEG_SCRIPT = {
    1: (194, 200, "撞门拍桌"),
    2: (202, 208, "点名"),
    3: (210, 212, "小唐作证"),
    4: (214, 224, "看清楚再说"),
    5: (226, 228, "掏兜"),
    6: (230, 232, "不能搜我"),
    7: (234, 236, "那就是心虚"),
    8: (242, 256, "还有"),
}

# 空间锚点（剧本 0.2 节的轴线铁律）—— 每次都显示在 tab 顶部，
# 因为「钱经理右后、苏小满左前」是用户投诉过的第一个问题。
ANCHOR_TEXT = (
    "轴线铁律：钱经理在画面右后，苏小满在画面左前，两人始终隔着办公桌对望，不许互换站边。\n"
    "钱经理：站桌子后侧，背靠窗柜，面朝门/面朝苏小满。\n"
    "苏小满：站桌子前侧，背靠门，面朝钱经理。\n"
    "小唐：门内靠南（画面下侧）墙边，缩着肩。\n"
    "门口：门外走廊挤一圈围观的人，全程不说话。"
)

# 状态 → 前端配色（key 与 show_ledger 里的状态一致）
ST_LABEL = {
    "done": "已完成", "running": "生成中", "pending": "排队中",
    "hold": "待重排", "rejected": "已否定",
}


# ────────────────────────────────────────────── 数据采集
def comfy_queue():
    """ComfyUI 实时队列：谁在跑、谁在等。判活用（show=True 模式下日志不更新）。

    ⛔ 2026-10-11 补：手动 `_run_one.py` 跑的片不写台账 started_at/run_epoch，
      网页「已运行 X 分」就空着。ComfyUI 的 /queue 每项自带 [priority, id, ...]
      外加第 4 元素 timestamps（[生成epoch, 提交epoch]）→ 直接取来当运行起点，
      snapshot 时塞给 summarize，前端就有时长可算了。
    """
    try:
        o = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        d = json.loads(o.open("http://127.0.0.1:%d/queue" % COMFY_PORT,
                              timeout=5).read().decode())
        run = d.get("queue_running") or []
        pend = d.get("queue_pending") or d.get("queue") or []
        # 取正在跑任务的提交时间：第4元素 meta 里的 create_time（毫秒epoch）
        q_epoch = None
        for item in run:
            if isinstance(item, list) and len(item) >= 4 \
                    and isinstance(item[3], dict):
                ct = item[3].get("create_time")
                if isinstance(ct, (int, float)):
                    q_epoch = float(ct) / 1000.0
                    break
        return {"alive": True, "running": len(run), "pending": len(pend),
                "gpu_busy": bool(run), "run_epoch": q_epoch}
    except Exception:
        return {"alive": False, "running": 0, "pending": 0, "gpu_busy": False,
                "run_epoch": None}


def gpu_info():
    """显存占用，判断显卡在不在干活。"""
    try:
        p = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=6)
        a = [x.strip() for x in p.stdout.strip().split(",")]
        if len(a) >= 3:
            return {"util": int(a[0]), "mem_used": int(a[1]), "mem_total": int(a[2])}
    except Exception:
        pass
    return {"util": None, "mem_used": None, "mem_total": None}


def sysmem_info():
    """系统内存占用率。⛔ >90% = 走页文件 = 采样掉速 2.5 倍（2026-10-07 实测）。
    网页要在生成中把这个警告亮出来（用户 2026-10-10 10:58 要求）。"""
    try:
        import ctypes

        class MEM(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_uint32), ("dwMemoryLoad", ctypes.c_uint32),
                ("ullTotalPhys", ctypes.c_uint64), ("ullAvailPhys", ctypes.c_uint64),
                ("ullTotalPageFile", ctypes.c_uint64), ("ullAvailPageFile", ctypes.c_uint64),
                ("ullTotalVirtual", ctypes.c_uint64), ("ullAvailVirtual", ctypes.c_uint64),
                ("ullAvailExtendedVirtual", ctypes.c_uint64)]

        m = MEM()
        m.dwLength = ctypes.sizeof(MEM)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            return {"load": int(m.dwMemoryLoad),
                    "avail_gb": round(m.ullAvailPhys / 2**30, 1)}
    except Exception:
        pass
    return {"load": None, "avail_gb": None}


def find_draft(sid):
    """第 sid 片的**预出片**（低分辨率那张），优先带 -audio 的。

    ⛔⛔⛔ 2026-10-10 用户提出「先出低分辨率预览，对了再升高清」。
      预览片落在 `D:\\output_h3off\\draft\\` 子目录，跟终版片**分开**。
      必须分开的原因：预览片和终版片同名前缀时，
      `newest("off_xs01_t01")` 会捡到昨天那张低清的，
      网页就会把预览当终版给用户看（用户看到的分辨率永远上不去）。
    """
    d = os.path.join(OUT_DIR, "draft")
    if not os.path.isdir(d):
        return None
    c = [f for f in os.listdir(d)
         if f.startswith("off_xs01_t%02d" % sid) and f.endswith(".mp4")
         and "_000" in f]
    if not c:
        return None
    au = [f for f in c if "-audio" in f]
    f = sorted(au)[-1] if au else sorted(c)[-1]
    p = os.path.join(d, f)
    mt = os.path.getmtime(p)
    return {"name": f, "size_mb": round(os.path.getsize(p) / 1048576.0, 2),
            "mtime": time.strftime("%m-%d %H:%M", time.localtime(mt)),
            "has_audio": "-audio" in f, "ts": int(mt)}


def find_video(sid, running=False):
    """第 sid 片的成片，优先带 -audio 的。

    ⛔⛔⛔ 2026-10-09 15:45 修：正在重跑的片**不能挂旧片**。
      当时片3 状态是「生成中」，页面却把 10-08 21:44 的 `t03_00010-audio.mp4`
      摆在预览位 → 用户以为新片出来了，看的其实是两天前的废片。

    ⛔ 踩坑：先用「字符串比时间」`mtime_HH:MM:SS > started_at_HH:MM:SS` 判新旧，
      跨天就废（昨天 21:44 的片 vs 今天 15:26 开跑 → "21:44" > "15:26" 判成新的）。
      → 修法：**统一成时间戳（秒）比**，并且在**调度器侧**额外记 `run_epoch`。
    """
    if not os.path.isdir(OUT_DIR):
        return None
    c = [f for f in os.listdir(OUT_DIR)
         if f.startswith("off_xs01_t%02d" % sid) and f.endswith(".mp4")
         and "_000" in f]
    if not c:
        return None
    au = [f for f in c if "-audio" in f]
    f = sorted(au)[-1] if au else sorted(c)[-1]
    p = os.path.join(OUT_DIR, f)
    mt = os.path.getmtime(p)
    if running:
        led = L.load()
        sg = led["segments"][str(sid)]
        t0 = sg.get("run_epoch")
        if t0 is None:
            t0 = _epoch_of_today(sg.get("started_at"))
        if t0 and mt < float(t0):
            return None              # 旧片，本次还没落盘
    # ⛔ 还没生成的片，目录里可能躺着**上一次跑剩的旧片**（片4-6 现在就是）。
    #    不标出来的话，用户点开预览会以为「已经做过了」→ 必须显式标 stale。
    fresh = bool(L.S(L.load(), sid).get("out"))
    return {"name": f, "size_mb": round(os.path.getsize(p) / 1048576.0, 2),
            "mtime": time.strftime("%m-%d %H:%M", time.localtime(mt)),
            "has_audio": "-audio" in f, "ts": int(mt),
            "stale": not fresh}


def _epoch_of_today(hhmmss):
    """'15:26:34' → 今天这个时刻的时间戳。台账只存时分秒，这里补上日期。"""
    if not hhmmss:
        return None
    for f in ("%Y-%m-%d %H:%M:%S", "%H:%M:%S"):
        try:
            t = time.strptime(time.strftime("%Y-%m-%d ") + hhmmss, f)
            return time.mktime(t)
        except Exception:
            continue
    return None


def scheduler_alive():
    """调度器进程还在不在。⛔ 崩了要立刻在页面上报出来。

    踩过的坑：调度器被 kill / 崩了，台账里那一片永远停在「生成中」，
    页面就一直转圈，用户以为在跑，其实显卡空着。
    → 用 `run_epoch` 判**超时**：跑一片 25–30 分钟，超过 75 分钟还没落盘
      就标成「疑似中断」，让看板立刻显示红色。
    """
    led = L.load()
    now = time.time()
    stale = []
    for k, sg in led["segments"].items():
        if sg["status"] != "running":
            continue
        t0 = sg.get("run_epoch")
        if t0 and now - float(t0) > 75 * 60:
            stale.append({"seg": int(k), "mins": int((now - float(t0)) / 60)})
    return stale


def _seg_prev_video(sid, stage):
    """chain 片要参考的上一段成片（调度器 find_prev 的网页版）。"""
    pre = ("draft/off_xs01_t%02d" % (sid - 1)) if stage == "preview" \
        else ("off_xs01_t%02d" % (sid - 1))
    p = L.newest(pre) if hasattr(L, "newest") else None
    if not p:
        # 简版：直接扫目录
        d = os.path.join(OUT_DIR, "draft") if stage == "preview" else OUT_DIR
        if os.path.isdir(d):
            c = [f for f in os.listdir(d)
                 if ("t%02d_" % (sid - 1)) in f and f.endswith("-audio.mp4")]
            if c:
                p = os.path.join(d, sorted(c)[-1])
    if p and os.path.exists(p):
        rel = os.path.relpath(p, OUT_DIR).replace("\\", "/")
        return {"name": rel,
                "size_mb": round(os.path.getsize(p) / 1048576.0, 2),
                "mtime": time.strftime("%m-%d %H:%M",
                                       time.localtime(os.path.getmtime(p)))}
    return None


# 参考图逻辑名 → 展示信息（md5 与 _run_one 的 md5 同源）
REF_DISPLAY = [
    {"name": "r01_ref1__9caa7471.png", "src": "assets_single/char_qianjingli.png",
     "who": "钱经理（正面全身单人）"},
    {"name": "r02_ref2__bcad60c8.png", "src": "assets_single/char_suxiaoman.png",
     "who": "苏小满（正面全身单人）"},
    {"name": "r03_ref3__016bdb32.png", "src": "assets_single/char_xiaotang.png",
     "who": "小唐（正面全身单人）"},
    {"name": "r04_ref4__a039524b.png", "src": "assets_single/sc_office_pano.png",
     "who": "办公室场景全景"},
]


def snapshot():
    """看板一次要的全量数据。"""
    led = L.load()
    stale = scheduler_alive()
    stale_segs = {s["seg"] for s in stale}
    segs = []
    for k in sorted(led["segments"], key=lambda x: int(x)):
        sg = led["segments"][k]
        sid = int(k)
        st = sg["status"]
        if sid in stale_segs:
            st = "rejected"          # 调度器死了 → 显示红色，别一直转圈
        v = find_video(sid, running=(st == "running"))
        dr = find_draft(sid)
        segs.append({
            "seg": sid, "chain": sg["chain"], "pos": sg["pos"],
            "kind": sg["kind"], "status": st,
            # ⛔ 阶段：preview=只有预出片在等你确认；final=已出/在出终版
            "stage": sg.get("stage") or "final",
            "profile": (PROFILE_PREVIEW if (sg.get("stage") or "final") == "preview"
                        else PROFILE_FINAL),
            "draft": dr,
            "label": ("疑似中断（%d分钟无产出）" % stale[0]["mins"])
                     if sid in stale_segs else ST_LABEL.get(sg["status"], sg["status"]),
            "words": sg.get("words"), "reviewed": sg.get("reviewed"),
            "approved": bool(sg.get("approved_by_user")),
            "video": v, "out": os.path.basename(sg["out"]) if sg.get("out") else None,
            "size_mb": sg.get("size_mb"), "wh": sg.get("wh"),
            "history": sg.get("history", [])[-3:],
            "started_at": sg.get("started_at"),
            "run_epoch": sg.get("run_epoch"),
            "prompt_lines": sg.get("prompt_lines"),
            "prompt_sha": sg.get("prompt_sha"),
            # ⛔ 2026-10-10 线性任务列表新增：
            "prev_video": (_seg_prev_video(sid, sg.get("stage") or "preview")
                           if sg["kind"] == "chain" else None),
        })
    q = comfy_queue()
    g = gpu_info()
    sm = sysmem_info()
    # ⛔ 2026-10-10 SQLite 化：snapshot 顺手带全量操作流水，网页不用二次请求
    try:
        ops = L.ops_history(limit=60)
    except Exception:
        ops = []
    return {
        "title": led.get("title", ""),
        "chain_size": L.CHAIN_SIZE,
        "updated": time.strftime("%H:%M:%S"),
        "segments": segs,
        "queue": q,
        "gpu": g,
        "sysmem": sm,
        "stale": stale,
        "ops": ops,
        "refs": REF_DISPLAY,
        "summary": summarize(segs, q),
    }


def summarize(segs, q):
    done = sum(1 for s in segs if s["status"] == "done")
    run = next((s for s in segs if s["status"] == "running"), None)
    # ⛔⛔⛔ 2026-10-09 20:33 台账与实际脱节，用户在网页上看到「没有正在生成的」，
    #   但 GPU 明明 100% 在跑。
    #   根因：**网页只信台账**。台账被人工重置成 pending、调度器进程死掉没回写、
    #   打断信号误触发 —— 任何一种都会让台账说「没在跑」，而 ComfyUI 其实在跑。
    #   → 台账说没跑、但 ComfyUI 队列有任务在跑时，**信 ComfyUI**（它才是真相）。
    gpu_says_busy = bool(q.get("running")) or bool(q.get("gpu_busy"))
    if run is None and gpu_says_busy:
        # ⛔⛔⛔ 2026-10-11 修：之前兜底永远挑「第一个 pending = 片1」，
        #   手动跑片3 时网页却显示「在跑片1」。
        #   → 改成挑「第一个 pending/hold 且还没出片(out 为空)」的片，
        #   即真正下一个要生成的片；都出过了就退回第一个 pending。
        cand = next((s for s in segs
                     if s["status"] in ("pending", "hold") and not s.get("out")),
                    None)
        if cand is None:
            cand = next((s for s in segs
                         if s["status"] in ("pending", "hold")), None)
        if cand:
            cand = dict(cand)
            cand["status"] = "running"
            cand["label"] = "生成中（台账未同步，以 ComfyUI 队列为准）"
            cand["seg_mismatch"] = True
            # ⛔ 2026-10-11：手动跑的片没有 started_at，前端「已运行」会空。
            #   用 ComfyUI 队列时间戳补一个，前端照常显示时长。
            if not cand.get("started_at") and q.get("run_epoch"):
                cand["run_epoch"] = q["run_epoch"]
                cand["started_at"] = time.strftime(
                    "%H:%M:%S", time.localtime(q["run_epoch"]))
            for i, s in enumerate(segs):
                if s["seg"] == cand["seg"]:
                    segs[i] = cand
                    run = cand
                    break
    return {
        "total": len(segs), "done": done,
        "running": run["seg"] if run else None,
        "running_chain": run["chain"] if run else None,
        "running_stage": run["stage"] if run else None,   # low/high 标注用
        "next": next((s["seg"] for s in segs if s["status"] == "pending"), None),
        "gpu_busy": q["gpu_busy"],
        "mismatch": bool(run and run.get("seg_mismatch")),
        # ⛔ 预出片待确认的数量 —— 网页要显示「N 片等你确认」
        "draft_waiting": sum(1 for s in segs
                             if s.get("draft") and s["status"] == "hold"),
    }


# ────────────────────────────────────────────── HTTP
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass                        # 静音，别刷屏

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def _send(self, code, body=b"", ctype="text/html; charset=utf-8", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    # ── 页面
    def do_GET(self):
        p = self.path.split("?")[0]
        try:
            if p in ("/", "/index.html"):
                return self._page()
            if p == "/api/state":
                return self._json(snapshot())
            if p == "/api/ops":
                # SQLite 操作流水：?seg=5 只看某片，否则看全部最近100条
                m = re.search(r"[?&]seg=(\d+)", self.path)
                import show_ledger as _L2
                return self._json({"ops": _L2.ops_history(
                    int(m.group(1)) if m else None, limit=100)})
            if p.startswith("/api/prompt/"):
                return self._prompt(int(p.rsplit("/", 1)[1]))
            if p.startswith("/api/script/"):
                return self._script(int(p.rsplit("/", 1)[1]))
            if p.startswith("/video/"):
                return self._video(p[7:])
            if p.startswith("/thumb/"):
                return self._thumb(p[7:])
            if p.startswith("/ref/"):
                # 参考图预览：只允许 assets_single/ 下的文件名
                fn = os.path.basename(p[5:])
                fp = os.path.join(HERE, "assets_single", fn)
                if os.path.isfile(fp):
                    with open(fp, "rb") as f:
                        return self._send(200, f.read(), "image/png")
                return self._send(404, b"no ref", "text/plain")
            return self._send(404, b"not found", "text/plain")
        except Exception as e:
            return self._json({"error": str(e)}, 500)

    # ── 指令（转发给 scheduler.py，不直接写台账）
    def do_POST(self):
        p = self.path.split("?")[0]
        try:
            n = int(self.headers.get("Content-Length") or 0)
            req = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
            if p == "/api/reject":
                return self._json(self._cmd("reject", [str(req.get("seg")),
                                                       req.get("why", "网页否定")]))
            if p == "/api/resume":
                return self._json(self._cmd("resume", [str(req.get("chain")),
                                                       req.get("why", "网页插队")]))
            if p == "/api/approve":
                return self._json(self._cmd("approve", [str(req.get("seg"))]))
            if p == "/api/preflight":
                return self._json(self._cmd("preflight", [str(req.get("seg"))]))
            if p == "/api/rerun":
                # 「重跑低清」= 否定（同链可能连带）+ 转预出片档重排
                seg = str(req.get("seg"))
                why = req.get("why") or "网页点「重跑低清」"
                out1 = self._cmd("reject", [seg, why])
                out2 = self._cmd("preflight", [seg])
                import show_ledger as _L3
                _L3.log_op(int(seg), "web_rerun", why)
                return self._json({"ok": out1.get("ok") and out2.get("ok"),
                                   "out": out1.get("out", "") + out2.get("out", "")})
            if p == "/api/promote":
                return self._json(self._cmd("promote", [str(req.get("seg"))]))
            return self._send(404, b"no api", "text/plain")
        except Exception as e:
            return self._json({"error": str(e)}, 500)

    def _cmd(self, verb, args):
        """跑 scheduler.py 的指令。⛔ 调完立刻回，不等 GPU。"""
        py = sys.executable
        r = subprocess.run([py, os.path.join(HERE, "scheduler.py"), verb] + args,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120, cwd=HERE)
        return {"ok": r.returncode == 0,
                "out": ((r.stdout or "") + (r.stderr or ""))[-1200:]}

    def _prompt(self, sid):
        """片 sid 的 H3 提示词全文（只读，方便对着改）。"""
        led = L.load()
        p = os.path.join(HERE, "xs001_segs", L.S(led, sid)["prompt"])
        if not os.path.exists(p):
            return self._json({"error": "提示词不在"}, 404)
        return self._json({"seg": sid, "text": io.open(p, encoding="utf-8").read()})

    def _script(self, sid):
        """片 sid 在剧本里的原文 + 该片实际用的 H3 台词（对照用）。

        ⛔ 为什么两个都要返回：用户投诉「对话都是乱的」，根因是
        **提示词里的台词被安到了错的人头上**（seg02 把钱经理的
        「收台的时候，就你一个人在」写成了苏小满说的）。
        → 网页上把「剧本原文」和「实际送进模型的台词」并排放，
          一眼就能看出谁错了。这比只看提示词有用得多。
        """
        if not os.path.exists(SCRIPT_MD):
            return self._json({"error": "剧本不在"}, 404)
        rng = SEG_SCRIPT.get(sid)
        if not rng:
            return self._json({"error": "片 %d 还没在剧本里定位" % sid}, 404)
        a, b, title = rng
        lines = io.open(SCRIPT_MD, encoding="utf-8").read().split("\n")

        # 往外多带一点，句子才完整
        lo, hi = max(0, a - 4), min(len(lines), b + 3)
        body = "\n".join(
            ("%d| %s" % (i + 1, lines[i])) if lines[i].strip() else ""
            for i in range(lo, hi)).strip()

        # 这片提示词里真正写着的台词（谁说了什么）
        used = []
        pp = os.path.join(HERE, "xs001_segs",
                          L.S(L.load(), sid)["prompt"])
        if os.path.exists(pp):
            t = io.open(pp, encoding="utf-8").read()
            # ⛔ 台词是中文，**只能按第一个中文句号断**。
            #   用 `[^.]+?`（英文点）会把后面 `小唐 (S3) stands…` 整段
            #   英文描述一起吃进来 —— 已在单元测试里抓到。
            # ⛔ `finditer` 从上一次匹配的**结尾**继续扫，会吞掉
            #   「下一句」的说话人标记（实测片1 只抓到 3 句里的第 1 句）
            #   → 改用「零宽断言」，每次只吃标记本身，长度不前进。
            # ⛔⛔⛔ 别用正则去切台词，切了 4 次都切错（吃过亏）：
            #   中文里本身带句号（「小唐。看清楚了，再说。」）、
            #   非贪婪只吃一个字、贪婪又把后面整段英文描述吃进来。
            # → 直接在**整篇提示词**里找剧本台词表的每个句子，
            #   找到就说明这片确实有这句，说话人按剧本认定。
            #   这也让网页显示的「实际用了什么」永远和校验器同源。
            try:
                sys.path.insert(0, HERE)
                from _check_lines import LINE_OWNER
            except ImportError:
                LINE_OWNER = {}
            for key, owner in LINE_OWNER.items():
                # ⛔ 短词必须连着后面的中文标点一起匹配，
                #   否则「掏兜」会命中「掏兜里…」之类的地方
                if len(key) < 3:
                    if (key + "。") in t:
                        used.append({"who": owner, "line": key + "。"})
                    continue
                if key in t:
                    used.append({"who": owner, "line": key})

        return self._json({
            "seg": sid, "title": title,
            "anchor": ANCHOR_TEXT,
            "body": body,
            "used": used,
            "source": os.path.relpath(SCRIPT_MD, HERE).replace("\\", "/"),
        })

    # ── 视频（⛔ 必须 Range，否则 <video> 拖不动进度条）
    def _video(self, name):
        """name 可以是 `draft/off_xs01_t01_00003-audio.mp4`（预出片）。"""
        # ⛔⛔⛔ 2026-10-10 预出片：必须允许 `draft/` 前缀，但**只允许这一层**，
        #   且必须仍然落在 OUT_DIR 里 —— 绝不能让 URL 变成任意路径穿越。
        name = name.replace("\\", "/")
        sub = ""
        if name.startswith("draft/"):
            sub = "draft"
            name = name[6:]
        name = os.path.basename(name)
        base = os.path.join(OUT_DIR, sub) if sub else OUT_DIR
        p = os.path.join(base, name)
        # 双保险：规范化后必须还在允许的目录里
        real = os.path.abspath(p)
        allowed = (os.path.abspath(os.path.join(OUT_DIR, "draft"))
                   if sub else os.path.abspath(OUT_DIR))
        if not real.startswith(allowed) or not os.path.exists(real) \
                or not name.endswith(".mp4"):
            return self._send(404, b"no video", "text/plain")
        size = os.path.getsize(real)
        p = real
        rng = self.headers.get("Range")
        ctype = "video/mp4"
        if rng and rng.startswith("bytes="):
            m = re.match(r"bytes=(\d*)-(\d*)", rng)
            s = int(m.group(1)) if m and m.group(1) else 0
            e = int(m.group(2)) if m and m.group(2) else 0
            e = e or size - 1
            e = min(e, size - 1)
            if s >= size:
                self.send_response(416)
                self.send_header("Content-Range", "bytes */%d" % size)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(206)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", "bytes %d-%d/%d" % (s, e, size))
            self.send_header("Content-Length", str(e - s + 1))
            self.end_headers()
            with open(p, "rb") as f:
                f.seek(s)
                left = e - s + 1
                while left > 0:
                    chunk = f.read(min(65536, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(size))
        self.end_headers()
        with open(p, "rb") as f:
            while True:
                chunk = f.read(262144)
                if not chunk:
                    break
                self.wfile.write(chunk)

    def _thumb(self, name):
        name = os.path.basename(name)
        p = os.path.join(OUT_DIR, name)
        if not os.path.exists(p):
            return self._send(404, b"no thumb", "text/plain")
        ct = mimetypes.guess_type(p)[0] or "image/png"
        with open(p, "rb") as f:
            b = f.read()
        self._send(200, b, ct, {"Cache-Control": "max-age=30"})

    def _page(self):
        f = os.path.join(WEB, "index.html")
        if not os.path.exists(f):
            return self._send(500, b"web/index.html missing", "text/plain")
        self._send(200, io.open(f, "rb").read())


def _lan_ip():
    """拿本机在局域网里的 IP（连不上 localhost 时可以用这个地址）。"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))     # 不会真发包
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            import socket
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def main():
    os.makedirs(WEB, exist_ok=True)
    # ⛔⛔⛔ 2026-10-09 20:58 用户连续打回两次「网页打不开」。
    #   原罪：只绑 127.0.0.1 → 浏览器若把 localhost 走代理，或用 IPv6 的 ::1
    #   访问，就全连不上，页面一直「连接中」。
    # → 绑 0.0.0.0：**IPv4 所有网卡**都收，localhost / 127.0.0.1 /
    #   局域网 IP 全部可达。IPv6 的 ::1 仍然不通 → 页面里加一行提示即可。
    # ⛔ 2026-10-10 手机公网访问：绑 IPv6 双栈（:: 同时收 v4+v6，0.0.0.0 只有 v4）
    class DualStackServer(ThreadingHTTPServer):
        address_family = socket.AF_INET6

        def server_bind(self):
            # ⛔⛔⛔ 2026-10-10 12:20 手机断连事故根因：
            #   光绑 "::" 在 Windows 上默认 v6ONLY=1 → **只收 IPv6，IPv4 全拒**
            #   （电脑上 127.0.0.1 打不开 = 用户看到「服务断了」）。
            #   必须 V6ONLY=0 才是真正双栈：一个套接字同时收 v4（映射地址）+v6。
            try:
                self.socket.setsockopt(
                    socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            except OSError:
                pass
            super().server_bind()

    try:
        srv = DualStackServer(("::", PORT), H)
    except OSError:
        srv = ThreadingHTTPServer(("0.0.0.0", PORT), H)
    lan = _lan_ip()
    print("=" * 56, flush=True)
    print(" 看板已启动，任选下面任一地址在浏览器打开：", flush=True)
    print("   ① http://localhost:%d← 试这个" % PORT, flush=True)
    print("   ② http://127.0.0.1:%d" % PORT, flush=True)
    print("   ③ http://%s:%d    ← 局域网/手机也能看" % (lan, PORT), flush=True)
    print("=" * 56, flush=True)
    print("台账 %s｜成片目录 %s" % (L.LEDGER, OUT_DIR), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    main()
