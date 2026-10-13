# -*- coding: utf-8 -*-
"""GPU 任务调度服务（Task Scheduler）
════════════════════════════════════════════════════════════════════════

⛔⛔⛔ 2026-10-09 用户定义的调度语义（原话照抄，不许自行简化）：

  1. 「GPU 就从前往后去取一个片，然后来运行。只要用户不打断你，
      那你就一直往后跑，确保 GPU 一直在运行。」

  2. 「如果用户提出来问题，对某一个片提出质疑，那你就看，
      如果说当前 GPU 在运行的任务不是这一个片所在的链，那你就不用管，
      就等 GPU 把当前这一次任务运行完，运行完了以后，然后再**插队**。」

  3. 「如果说当前的任务刚好又是这个片所在的这个链，那么就**停止当前的这个
      生成的任务**，直接跳到下一个链的第一个片去做，
      同时你开始分析问题……然后你再**插队**。」

  4. 「假设你现在正在跑第二链的第三片。这时用户提出第二链第二片有问题。
      你先停止掉第二链第三片，启动第三链的第一片，回来分析问题，
      调整提示词，把第二链的第二片和第三片**插队**到队列里。
      GPU 运行完第三链第一片以后看到插队了，就运行第二链第二片、第三片，
      然后继续到第三链。」

设计成**一个常驻进程 + 一个台账文件 + 几条指令**：
  · 台账 `show_ledger.json` 是唯一事实来源（片/链/状态/产出）
  · 主循环 `run`：取片 → 提交 GPU → 等落盘 → 回写台账 → 取下一片
  · 指令（另开终端随时打，不影响正在跑的那片）：
      status              看板
      reject <片号> [理由] 用户否定这片 → 整链打回
      resume <链号>       改完提示词后重排这条链 → 插队
      pause / resume-all  全局暂停 / 继续
  · 调度器**随时可被打断**：`reject` 若命中当前正在跑的链 → 立刻 kill 当前
    任务、清队列、跳到下一链第一片。

════════════════════════════════════════════════════════════════════════
"""

import io
import json
import os
import hashlib
import re
import signal
import subprocess
import sys
import time

import show_ledger as L
import _run_one as RO

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OUT_DIR = r"D:\output_h3off"
WF_DIR = r"E:\ComfyUI\ComfyUI_new\user\default\workflows"
WF_FIXED = os.path.join(WF_DIR, "04_ref2v_4step_sla_ganloss_fixed.json")
WF_CHAIN = os.path.join(WF_DIR, "04_ref2v_seg2_chain.json")
DRIVER = os.path.join(HERE, "h3_driver.py")
KILL = os.path.join(HERE, "_kill_old.py")

_reuse = RO._REFS_FULL if hasattr(RO, "_REFS_FULL") else None


def log(*a):
    print("[%s]" % time.strftime("%H:%M:%S"), *a, flush=True)


# ══════════════════════════════════════════════════════════════════
#  资产侧
# ══════════════════════════════════════════════════════════════════
REFS = ["r01_ref1__9caa7471.png", "r02_ref2__bcad60c8.png",
        "r03_ref3__016bdb32.png", "r04_ref4__a039524b.png"]
WANT_ASPECT = "4:3 (Standard)"


def comfy_alive():
    try:
        import urllib.request
        o = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        o.open("http://127.0.0.1:%d/system_stats" % RO.OFFICIAL_PORT, timeout=8).read()
        return True
    except Exception:
        return False


def kill_comfy():
    os.environ["MINIDRAMA_PORT"] = str(RO.OFFICIAL_PORT)
    subprocess.run([sys.executable, KILL], capture_output=True,
                   text=True, timeout=200, cwd=HERE)


def back_to_pending(sid, why=""):
    """把片退回 pending。⛔ 卡在 running 的片永远不会被 next_pending 捡起来。"""
    led = L.load()
    v = L.S(led, sid)
    v["status"] = L.ST_PENDING
    v["out"] = None
    v["run_epoch"] = None
    v["started_at"] = None
    hist = v.get("history") or []
    hist.append("退回pending: " + why)
    v["history"] = hist[-8:]
    L.save(led)
    log("  ↩ seg%02d 已退回 pending（%s）" % (sid, why))


def ensure_comfy():
    """⛔ ComfyUI 的启停权只属于调度器（手动 start 会清空队列，driver 死等）。

    ⛔⛔⛔ 2026-10-09 20:25 用户明确要求（10-08 同一要求，我不该改）：
      「我不是要求你每一次启动的都是可以看得见的黑窗口吗？」
      → show=True，用 CREATE_NEW_CONSOLE 弹一个**用户能看见的黑窗口**，
        能实时看到 8 步采样一步步走。

      ⚠️ 那为什么 20:08-20:22 我把它改成 show=False 反而起不来？
         真因不是 show=True，而是**调度器本身被后台无窗口方式起**
         （CREATE_NO_WINDOW 的进程再去弹新控制台，弹不出来）。
         → 现在调度器用 Bash(run_in_background=true) 起（有真控制台），
           show=True 能正常弹窗。**不要因为 20:08 那次误诊就改回后台模式。**

    ⛔ 另一个坑：cdir 必须显式传 OFFICIAL_DIR。传 None 会用 COMFY_DIR
      （旧实例 ComfyUI-master）当工作目录，但端口/输出目录是官方实例的。
    """
    if comfy_alive():
        return
    log("ComfyUI 未运行 → 启动可见黑窗口（端口 %d, 目录 %s）"
        % (RO.OFFICIAL_PORT, RO.OFFICIAL_DIR))
    RO.start_comfy(port=RO.OFFICIAL_PORT, cdir=RO.OFFICIAL_DIR, out=OUT_DIR,
                   temp=RO.OFFICIAL_TEMP, tag="sched", show=True)
    for _ in range(60):
        if comfy_alive():
            log("ComfyUI 就绪（可见黑窗口已开，能实时看采样进度）")
            return
        time.sleep(3)
    # ⛔⛔ 别再 SystemExit 让整个调度器退出 = 没人再管后面的片 = GPU 空转。
    #   起不来就把这一片退回 pending，看门狗下一轮再试。
    log("‼ ComfyUI 起不来（等 180 秒仍无响应）→ 本片退回 pending，调度器退出")
    raise SystemExit(9)


# ══════════════════════════════════════════════════════════════════
#  生成侧
# ══════════════════════════════════════════════════════════════════
def newest(prefix):
    """最新的成片。⛔ **优先要 `-audio.mp4`**（带配音的那支才是能看的成片）。

    踩过的坑：同一 prefix 下有 `xxx.mp4` 和 `xxx-audio.mp4` 两只，
    字典序 `-audio` 排在后面本来正好，但一旦有 `xxx (1)-audio.mp4` 这类
    ComfyUI 自动改名副本就会挑错 → 用户拿到没声音的片。
    → 显式分两级取：先只找 `-audio`，找不到再退回任意 mp4。

    ⛔⛔⛔ 2026-10-10 14:45 补：prefix 可能带子目录（预出片是 `draft/off_xs01_tNN`）。
      旧版只 `os.listdir(OUT_DIR)` 顶层 → draft/ 里的成片**永远看不到**，
      真实事故：片1 预出片 13:52 落盘，调度器在等待循环里看不见，
      傻等满 60 分钟判「超时」，还把这条链断掉跑去跑别的链。
    → prefix 含 `/` 时先拆出子目录，在子目录里找。
    """
    d = OUT_DIR
    sub = ""
    if "/" in prefix:
        sub, prefix = prefix.split("/", 1)
        d = os.path.join(d, sub)
    if not os.path.isdir(d):
        return None
    c = [f for f in os.listdir(d) if f.startswith(prefix) and f.endswith(".mp4")
         and "_000" in f]
    if not c:
        return None
    au = [f for f in c if "-audio" in f]
    return os.path.join(d, sorted(au)[-1] if au else sorted(c)[-1])


def probe_size(path):
    try:
        p = subprocess.run(["ffprobe", "-v", "quiet", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height",
                            "-of", "csv=p=0:s=x", path],
                           capture_output=True, text=True, timeout=60)
        w, h = p.stdout.strip().split("x")[:2]
        return int(w), int(h)
    except Exception:
        return 0, 0


def stale_reason(path):
    """旧片作废判定：画幅不对 / 成片比提示词旧 → 必须重跑。"""
    if not path:
        return None
    w, h = probe_size(path)
    aw, ah = L.ASPECT_W_H.get(WANT_ASPECT, (4, 3)) if hasattr(L, "ASPECT_W_H") \
        else (4, 3)
    if w and h and abs((w / float(h)) - (aw / float(ah))) / (aw / float(ah)) > 0.03:
        return "画幅不符（成片 %dx%d，要 %dx%d）" % (w, h, aw, ah)
    return None


def prompt_fingerprint(path):
    """提示词指纹：大小 + 全文 md5。用来证明「这一片跑的时候用的是哪一版」。

    ⛔⛔⛔ 2026-10-10 用户抓到的错就是这个：
      「你在网页上看到片4的提示词是对的，你出来的视频是错的，
        你到底传了什么提示词？？？」
      网页读的是**改完之后**的文件，片子跑的是**提交那一刻**的文件，
      两个东西没有任何关联 → 用户完全看不到片子里到底跑了什么。
      → 从此 job 里留指纹，出片后跟盘上现文件比对，不一致就作废重跑。
    """
    try:
        b = open(path, "rb").read()
    except OSError:
        return ""
    return "%d:%s" % (len(b), hashlib.md5(b).hexdigest()[:12])


def prompt_lines(path):
    """提示词里「谁说了什么」，原样记进 job —— 出片后直接对照，用户一眼能看懂。"""
    try:
        t = io.open(path, encoding="utf-8").read()
    except IOError:
        return []
    out = []
    for m in re.finditer(
            r"(钱经理|苏小满|小唐)\s*\(S\d\)\s*speaks[^:]*:?\s*"
            r"\[Chinese\]\s*(.{0,40}?)。", t):
        out.append({"who": m.group(1), "line": m.group(2).strip()})
    return out


def prompt_drift_reason(sid, job):
    """成片跑完时查：提示词是不是在这片开跑之后被改过。

    改过了 → 这一片是用旧版跑的，**作废**。
    （这是 09:34 那次「提示词对、视频错」的根治点）

    ⚠️⛔ 自测抓到的坑：**必须优先用传入的 job**，不能只读磁盘上的
       `schNN.json`。原来只读磁盘 → 传进来的 job 被无视 → 防线形同虚设
       （用模拟场景验证时立刻报「没拦住」）。
       磁盘那份是**热启动**路径用的（`wait_inflight` 接管在飞的片）。
    """
    pp = (job or {}).get("prompt_file")
    sha = (job or {}).get("prompt_sha")
    if not pp or not sha:
        jf = os.path.join(HERE, "xs001_segs", "sch%02d.json" % sid)
        if not os.path.exists(jf):
            return None
        try:
            j = json.load(io.open(jf, encoding="utf-8"))
        except Exception:
            return None
        pp = j.get("prompt_file")
        sha = j.get("prompt_sha")
    if not pp or not sha or not os.path.exists(pp):
        return None
    now = prompt_fingerprint(pp)
    if now != sha:
        return ("提示词在本片开跑后被改过（提交时 %s → 现在 %s），"
                "这片用的是旧版，成果作废重跑" % (sha, now))
    return None


def find_prev(sid, stage=None):
    """chain 片要接的上一段成片。

    ⛔⛔⛔ 2026-10-10 加 stage：预览片必须接**上一段的预览片**。
      预览阶段如果去接终版（或反过来），两段的分辨率/几何基准不同，
      接出来的画面会跳。之前没这参数，是拿 `off_xs01_tNN` 统一找的。
    """
    stage = stage or "preview"   # ⛔ 2026-10-10 用户铁律：缺省低清
    pre = ("draft/off_xs01_t%02d" % (sid - 1)) if stage == "preview" \
        else ("off_xs01_t%02d" % (sid - 1))
    p = newest(pre)
    if p and os.path.exists(p):
        return p
    # ⛔ 预览片找不到同阶段的上一段时，**不退回终版**（几何基准不一致会跳）。
    #   宁可退回 fixed 重新起画面，也不能接错锚 —— 已在这行下面处理。
    for d in (OUT_DIR, r"D:\output"):
        if not os.path.isdir(d):
            continue
        sub = os.path.join(d, "draft") if stage == "preview" else d
        if not os.path.isdir(sub):
            continue
        c = [f for f in os.listdir(sub)
             if ("t%02d" % (sid - 1)) in f and f.endswith(".mp4")]
        if c:
            return os.path.join(sub, sorted(c)[-1])
    return None


# ══════════════════════════════════════════════════════════════
#  预出片 → 终版（用户 2026-10-10 提出）
#  原话：「能不能先预出片 就是运行产出分辨率低的 看看是否都对 提高出片的速度
#        然后 预出片是对的话 再运行提高分辨率的工作流」
#
#  ⛔⛔⛔ 设计上只降分辨率，**其余参数一律不动**
#     （同模型 / 同 8 步 / 同 LoRA / 同 VAE），只把 mp 从 0.75 降到 0.25。
#     理由：如果「预览」用的是另一套参数，那「预览对」就不能推出
#     「终版也对」——这个方案就失去意义了。
#     步数也绝不能减：步数一少画面本身就糙（实测 6 步亮度掉到 87.8）。
#
#  阶段记在台账每片的 `stage` 字段：
#     preview → 用 preview25 跑（576x448，约终版 1/3 时间）
#     final   → 用 hd_turbo8 跑（1024x768），存成终版存档
#  没跑过预出片的片（老片/已认可片）直接走 final，不额外花时间。
# ══════════════════════════════════════════════════════════════
PROFILE_PREVIEW = "preview25"
PROFILE_PREVIEW_HI = "preview40"
PROFILE_FINAL = "hd_turbo8"
PREVIEW_TAGS = {PROFILE_PREVIEW, PROFILE_PREVIEW_HI}


def profile_for_stage(stage):
    # ⛔ 2026-10-10 用户铁律：缺省= preview（低清），绝不缺省高清
    return {"preview": PROFILE_PREVIEW, "final": PROFILE_FINAL}.get(
        stage or "preview", PROFILE_PREVIEW)


def make_job(sid, kind, prev, led):
    """造 job json。⛔ 提示词一律现读盘上的文件（用户改完就生效，不用重建台账）。"""
    sg = L.S(led, sid)
    pp = os.path.join(HERE, "xs001_segs", sg["prompt"])
    # ⛔ 本片跑哪个档：预览档 还是 终版档
    # ⛔⛔⛔ 2026-10-10 14:50 用户铁律（「只有用户要求才跑高清 默认都是低分辨
    #   率的快速出片」）：缺省= preview。要高清必须用户点「升高清·出终版」。
    stage = sg.get("stage") or "preview"
    prof = profile_for_stage(stage)
    # ⛔⛔⛔ 2026-10-10 09:34 用户抓到的最阴的一次错：
    #   「你在网页上看到片4的提示词是对的，你出来的视频是错的，到底传了什么？」
    #   真因：**09:08 提交片4，用的是当天 09:17 才修好的那份之前的老提示词**。
    #   老版里钱经理说的是「你今天把话说清楚。」+「小唐。看清楚了，再说。」
    #   ——两句都是他的，苏小满和小唐全程闭嘴。
    #   我改完提示词就以为完事了，**没管已经提交在跑的那一片**。
    # → 铁律：**改提示词后，凡是「提示词 mtime 比本片开跑时间新」的成片一律作废。**
    #   这里把提交时刻的指纹（大小+哈希+台词）写进 job，出片后用来比对。
    job = {
        "workflow": WF_FIXED if kind == "fixed" else WF_CHAIN,
        "prompt_file": os.path.abspath(pp),
        "prompt_sha": prompt_fingerprint(pp),
        "prompt_mtime": os.path.getmtime(pp) if os.path.exists(pp) else 0,
        "prompt_lines": prompt_lines(pp),
        "quality": prof,                 # ⛔ 每片单独指定，不动全局档
        "stage": stage,
        # ⛔⛔⛔ 预览片和终版片**必须分开命名**。
        #   否则出终版后，`newest("off_xs01_t01")` 捡到的可能是昨天那张预览片，
        #   网页就会拿预览当终版给你看（用户看到的就会是低清的）。
        #   预览统一落到 draft_ 子目录，终版落回原前缀。
        "out_prefix": ("draft/off_xs01_t%02d" % sid) if stage == "preview"
                      else ("off_xs01_t%02d" % sid),
        "refs": list(REFS),
        "ref_dir": RO.ref_dir_for(True),
        "prev_video": prev if kind == "chain" else None,
    }
    jf = os.path.join(HERE, "xs001_segs", "sch%02d.json" % sid)
    with io.open(jf, "w", encoding="utf-8") as f:
        f.write(json.dumps(job, ensure_ascii=False, indent=1))
    return jf, job


def run_segment(sid, led, stopfile=None):
    """跑一片。跑完回写台账。返回 'done' / 'rejected' / 'killed' / 'draft'。"""
    sg = L.S(led, sid)
    kind = sg["kind"]
    # ⛔⛔⛔ 2026-10-10 14:50 用户铁律：缺省= preview（低清）。
    stage = sg.get("stage") or "preview"
    prof = profile_for_stage(stage)
    # ⛔ 预览片找的是 draft/ 子目录，终版片找的是原前缀 —— 两者不能混
    prefix = ("draft/off_xs01_t%02d" % sid) if stage == "preview" \
        else ("off_xs01_t%02d" % sid)
    why = stale_reason(newest(prefix))
    if why:
        log("seg%02d 旧片作废（%s）→ 重跑" % (sid, why))
    # ⛔ chain 片要接的**上一段成片**：预览阶段必须接「上一段的预览片」，
    #   否则会把上一段的终版（或不存在）当锚，几何对不上。
    prev = find_prev(sid, stage=stage) if kind == "chain" else None
    if kind == "chain" and not prev:
        log("seg%02d 找不到上一段成片 → 退回 fixed（不会静默出错）" % sid)
        kind = "fixed"
    jf, job = make_job(sid, kind, prev, led)
    log("── seg%02d 开始（链%d·第%d片，%s，%s档）"
        % (sid, sg["chain"], sg["pos"], kind,
           "预出片" if stage == "preview" else "终版"))
    L.log_op(sid, "start", "%s·%s档 pid提交" %
             (kind, "低清" if stage == "preview" else "高清"))

    try:
        ensure_comfy()
    except SystemExit:
        back_to_pending(sid, "ComfyUI 起不来")
        raise
    except Exception as e:
        log("‼ seg%02d 启 ComfyUI 异常：%r" % (sid, e))
        back_to_pending(sid, "启 ComfyUI 异常 %r" % (e,))
        return "error"
    env = dict(os.environ)
    env["MINIDRAMA_PORT"] = str(RO.OFFICIAL_PORT)
    env["MINIDRAMA_DEEPQ"] = "1"

    # ⛔ 提交用 --qsubmit（只入队不阻塞），等待用轮询 —— 这样主循环随时能看打断信号
    try:
        p = subprocess.run([sys.executable, "-u", DRIVER, "--qjob=" + jf, "--qsubmit"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=900, env=env, cwd=HERE)
    except Exception as e:
        log("‼ seg%02d 提交进程异常：%r" % (sid, e))
        back_to_pending(sid, "提交进程异常 %r" % (e,))
        return "error"
    out = (p.stdout or "") + (p.stderr or "")
    pid = ""
    for ln in out.splitlines():
        if ln.startswith("PROMPT_ID="):
            pid = ln.split("=", 1)[1].strip()
        if any(k in ln for k in ("参考图", "QUALITY", "MODEL", "ERROR", "!!")):
            log("  ", ln.strip())
    if not pid:
        log("‼ seg%02d 提交失败：%s" % (sid, out[-600:]))
        back_to_pending(sid, "提交失败")
        return "error"
    log("  已入队 pid=%s，开始等" % pid[:8])

    led = L.load()
    L.S(led, sid)["status"] = L.ST_RUNNING
    L.S(led, sid)["pid"] = pid
    L.S(led, sid)["started_at"] = time.strftime("%H:%M:%S")
    # ⛔ 2026-10-09 15:45：另存**时间戳**。台账那个 "15:26:34" 字符串
    #    跨天比较会判错（昨天 21:44 的旧片 > 今天 15:26 → 误判成新片），
    #    网页靠这个戳判断「成片是不是本次跑出来的」。
    L.S(led, sid)["run_epoch"] = int(time.time())
    L.save(led)
    t0 = time.time()
    import sched_stop as SS
    # ⛔⛔⛔ 落盘判定的基准时间 = **本次提交之前**。
    #   踩过的最严重的坑（2026-10-09 16:24）：
    #   片4 在 15:59 被放弃（但已落盘），16:24 重新跑它 →
    #   等待循环只判「文件存在 + mtime 在 1 小时内」→ 17 秒就把
    #   **15:59 那个旧片当成新片**报完成 → 下一片拿它当尾帧续接 → 整链污染。
    #   ⛔ 判据必须是「落盘时间 >= 本次开跑时间」，且要**先删旧片**。
    base_ts = time.time() - 2          # 留 2 秒余量（文件系统时间戳精度）
    # 重跑前先把上一支同 prefix 的成片挪走，避免误认
    old = newest(prefix)
    if old:
        try:
            bak = os.path.join(OUT_DIR, "_stale", os.path.basename(old))
            os.makedirs(os.path.dirname(bak), exist_ok=True)
            if not os.path.exists(bak):
                os.replace(old, bak)
            log("  ↳ 旧片已挪走防误认: %s → _stale/%s"
                % (os.path.basename(old), os.path.basename(bak)))
        except Exception as e:
            log("  ↳ 旧片挪走失败（%s），改用时间戳严判" % e)
    while True:
        time.sleep(15)
        # ① 打断信号：用户否定了同链的片 → 立刻放弃这一片，让位给下一条链
        msg = SS.take(sid)
        if msg and msg.get("kill"):
            log("⚡ 收到打断（%s）→ 放弃 seg%02d（已跑 %.0f 分钟），跳下一条链"
                % (msg.get("why", ""), sid, (time.time() - t0) / 60))
            L.log_op(sid, "kill", msg.get("why", ""))
            SS.clear(sid)
            kill_comfy()
            led = L.load()
            if L.S(led, sid)["status"] == L.ST_RUNNING:
                L.S(led, sid)["status"] = L.ST_PENDING
            L.save(led)
            return "killed"
        # ② 落盘？⛔⛔ 必须 mtime >= base_ts（本次开跑之后），否则是旧片
        got = newest(prefix)
        if got and os.path.getmtime(got) >= base_ts:
            w, h = probe_size(got)
            sz = os.path.getsize(got) / 1048576.0
            # ⛔⛔⛔ 2026-10-10 09:34 根治点：这一片跑的这十几分钟里，
            #   提示词可能被我改了（就为了赶进度边跑边改）。
            #   → 一致才收成果；不一致 = 片子是旧版提示词跑的，直接作废重跑。
            #     否则网页上显示着新提示词、播放器里放着旧版片，
            #     用户完全看不出片子跑的是哪一版（用户就是这么抓到我错的）。
            drift = prompt_drift_reason(sid, job)
            if drift:
                log("⛔⛔ seg%02d 作废重跑：%s" % (sid, drift))
                L.log_op(sid, "stale_prompt", drift)
                led = L.load()
                L.S(led, sid)["status"] = L.ST_PENDING
                L.S(led, sid)["out"] = None
                L.S(led, sid).pop("run_epoch", None)
                L.S(led, sid).pop("started_at", None)
                L.S(led, sid).setdefault("history", []).append(
                    {"t": time.strftime("%H:%M:%S"), "why": drift})
                L.save(led)
                return "stale_prompt"
            led = L.load()
            # ⛔ 预览片存 draft_out，**不占 out**（out 留给终版）。
            #   网页默认播 out；预览片另开一个字段，晋级后终版才填 out。
            if stage == "preview":
                L.S(led, sid)["draft_out"] = got
                L.S(led, sid)["draft_wh"] = "%dx%d" % (w, h)
                L.S(led, sid)["draft_size_mb"] = round(sz, 2)
                # ⛔ 状态用 hold（待确认），不用 done —— 否则调度器会
                #   立刻去取下一片，等于把没验过的片当成功往下续接。
                L.S(led, sid)["status"] = L.ST_HOLD
                L.S(led, sid)["stage"] = "preview"
            else:
                L.S(led, sid)["out"] = got
                L.S(led, sid)["status"] = L.ST_DONE
                L.S(led, sid)["size_mb"] = round(sz, 2)
                L.S(led, sid)["wh"] = "%dx%d" % (w, h)
                L.S(led, sid)["stage"] = "final"
            L.S(led, sid)["prompt_sha"] = job.get("prompt_sha")
            L.S(led, sid)["prompt_lines"] = job.get("prompt_lines")
            L.S(led, sid).pop("run_epoch", None)
            L.S(led, sid).pop("started_at", None)
            L.save(led)
            if job.get("prompt_lines"):
                log("   本片实际传的台词：" + " / ".join(
                    "%s「%s」" % (x["who"], x["line"])
                    for x in job["prompt_lines"]))
            if stage == "preview":
                log("🎞 seg%02d 预出片完成 %dx%d %.2fMB → %s"
                    "（等你确认；点网页「升高清」才出终版）"
                    % (sid, w, h, sz, os.path.basename(got)))
                L.log_op(sid, "draft_done", "%dx%d %.1fMB %s"
                         % (w, h, sz, os.path.basename(got)))
                return "draft"
            log("✅ seg%02d 完成 %.2fMB %dx%d → %s"
                % (sid, sz, w, h, os.path.basename(got)))
            L.log_op(sid, "final_done", "%dx%d %.1fMB %s"
                     % (w, h, sz, os.path.basename(got)))
            return "done"
        if time.time() - t0 > 3600:
            log("!! seg%02d 超 60 分钟未落盘" % sid)
            return "error"


# ══════════════════════════════════════════════════════════════════
#  主循环
# ══════════════════════════════════════════════════════════════════
def wait_inflight(timeout=3600):
    """⛔⛔⛔ 启动时若台账里有 running 的片 → **先把它等完**再取新片。

    场景（2026-10-09 15:25 真实发生）：上一版 `_chain.py` 批任务正在跑片3，
    我要换成调度器接管。如果调度器不管直接取下一个片，
    旧批任务落盘后也会去取片4 → **两路同时提交，GPU 抢显存 / 跑出重复片**。
    → 规则：**同一时刻只允许一个片在飞**。调度器启动先等在飞的那片落地。
    """
    led = L.load()
    flying = [int(k) for k, sg in led["segments"].items()
              if sg["status"] == L.ST_RUNNING]
    if not flying:
        return []
    sid = flying[-1]
    prefix = "off_xs01_t%02d" % sid
    # ⛔⛔⛔ 2026-10-09 16:26 补：同样不能只看「文件存在」！
    #   接管时这片**上一次跑可能已经落盘又被否**（15:59 片4 被放弃但已落盘）。
    #   判据必须是「mtime >= 台账里记的 run_epoch」，否则会把旧片当本次成果。
    t0 = led["segments"][str(sid)].get("run_epoch")
    log("⏳ 台账里片%d 正在跑（上一轮提交）→ 先等它落盘，不重复提交" % sid)
    t_start = time.time()
    dead_checked = 0.0
    while time.time() - t_start < timeout:
        # ⛔⛔⛔ 2026-10-10 10:39 补：ComfyUI 都死了还在等 = 死等 1 小时白烧
        #   （真实发生：10:29 重启后片1 是旧进程提交的，ComfyUI 随后死掉，
        #    调度器在 wait_inflight 里干等，没人拉起 ComfyUI。）
        #   → 每 60 秒探活一次，连续 2 次死 → 认定上一轮任务已丢失，
        #     把这片退回 pending，跳出等待走正常取片（ensure_comfy 会拉起 ComfyUI）。
        if time.time() - dead_checked >= 60:
            dead_checked = time.time()
            if not comfy_alive():
                log("⚠ ComfyUI 无响应（等待期间探活失败）→ 再等 60s 复核…")
                time.sleep(60)
                if not comfy_alive():
                    log("⛔ ComfyUI 确认死亡，上一轮任务已丢失 → 片%d 退回 pending，"
                        "拉起 ComfyUI 重新开工" % sid)
                    led = L.load()
                    sg = L.S(led, sid)
                    sg["status"] = L.ST_PENDING
                    sg.pop("run_epoch", None)
                    sg.pop("started_at", None)
                    sg.setdefault("history", []).append(
                        {"t": time.strftime("%H:%M:%S"),
                         "why": "ComfyUI 死亡，上一轮任务丢失，重新排队"})
                    L.save(led)
                    return []
        got = newest(prefix)
        if got and (t0 is None or os.path.getmtime(got) >= float(t0) - 2):
            # ⛔ 同样要查提示词漂移（上一轮提交、本轮才改的提示词）
            drift = prompt_drift_reason(sid, {})
            if drift:
                log("⛔⛔ 接管时发现片%d 作废：%s" % (sid, drift))
                led = L.load()
                sg = L.S(led, sid)
                sg["status"] = L.ST_PENDING
                sg.pop("out", None)
                sg.pop("run_epoch", None)
                sg.pop("started_at", None)
                sg.setdefault("history", []).append(
                    {"t": time.strftime("%H:%M:%S"), "why": drift})
                L.save(led)
                return [sid]
            w, h = probe_size(got)
            led = L.load()
            sg = L.S(led, sid)
            sg["out"] = got
            sg["size_mb"] = round(os.path.getsize(got) / 1048576.0, 2)
            sg["wh"] = "%dx%d" % (w, h)
            sg.pop("started_at", None)
            sg.pop("pid", None)
            if sg["status"] == L.ST_RUNNING:
                sg["status"] = L.ST_DONE
            L.save(led)
            log("✅ 接管：片%d 已落盘 %.2fMB %dx%d" % (sid, sg["size_mb"], w, h))
            return [sid]
        time.sleep(15)
    log("⚠ 等片%d 超时，按未完成处理" % sid)
    led = L.load()
    if L.S(led, sid)["status"] == L.ST_RUNNING:
        L.S(led, sid)["status"] = L.ST_PENDING
        L.save(led)
    return []


def run(only_chain=None, max_seg=99, stopfile=None):
    led = L.load()
    log("调度器启动｜SQLite台账 %s｜%d 片 / 每链 %d 片"
        % (getattr(L, "DB_PATH", L.LEDGER), len(led["segments"]), L.CHAIN_SIZE))
    wait_inflight()                      # ⛔ 先等在飞的片，别双开
    led = L.load()
    log(L.table(led))
    n = 0
    last_chain = None
    stale_n = 0            # 连续「提示词漂移作废」次数，防打转
    while n < max_seg:
        led = L.load()
        sid = L.next_pending(led, only_chain=only_chain)
        if sid is None:
            log("没有待跑的片了。调度器待命（可随时 `resume <链号>` 插队）")
            return 0
        cid = L.S(led, sid)["chain"]
        # ⛔ 断链：换链时重启 ComfyUI（越接越黑，用户 10-08 实测）
        if last_chain is not None and cid != last_chain:
            log("── 断链（第%d链 → 第%d链）：重启 ComfyUI ──" % (last_chain, cid))
            kill_comfy()
            time.sleep(5)
        last_chain = cid
        # 参考图预取：开跑前拷好，段间零拷贝
        RO.reclaim_before_gen()
        r = run_segment(sid, led, stopfile=stopfile)
        n += 1
        if r == "killed":
            log("跳到下一条链")
            last_chain = None
        elif r == "stale_prompt":
            # ⛔ 提示词在跑的过程中被改了 → 这片作废。
            #   片已回 pending，主循环下一轮会重取它（自动用新版重跑，
            #   显卡一秒不停）。但若提示词还在被人反复改，会打转——
            #   → 数一下连续作废次数，超过 3 次就停下让人先改完。
            stale_n += 1
            log("提示词漂移已连续 %d 次" % stale_n)
            if stale_n >= 3:
                log("⛔⛔ 提示词还在被反复改动，先停手改完再跑（防打转）")
                break
        else:
            stale_n = 0
    return n


# ══════════════════════════════════════════════════════════════════
#  指令入口
# ══════════════════════════════════════════════════════════════════
def cmd_status():
    led = L.load()
    print(L.table(led))
    print("\n队列: %s" % ("运行中" if comfy_alive() else "ComfyUI 未起"))


def cmd_reject(sid, why="用户否定"):
    """用户否定某片 → **整条链**打回 pending（用户原话：同链后面几片也会有问题）。

    ⛔⛔⛔ 这里是打断语义的落地点（用户 2026-10-09 定义，必须一字不差照做）：
      · 当前正在跑的片**不在**这条链 → 不打断！只把链打回，它自然会在轮到时重跑
      · 当前正在跑的片**在**这条链   → 立刻发停机信号，调度器放弃当前片跳下一链
    """
    L.log_op(sid, "web_reject", why)
    import sched_stop as SS
    led = L.load()
    cid = L.chain_of(sid)
    running = SS.current_running(led)
    hit = L.set_chain(led, cid, L.ST_PENDING, why)
    if running is not None and L.chain_of(running) == cid:
        # 同链 → 放弃当前片，让位给下一条链
        SS.put_kill(running, "用户否定片%d（同链%d）" % (sid, cid))
        print("⚡ 当前正在跑的是片%d，与你否定的片%d **同属链%d**"
              % (running, sid, cid))
        print("   → 已发停机信号，调度器会放弃片%d 并跳到下一条链的第一片"
              % running)
    elif running is not None:
        print("ℹ 当前正在跑的是片%d（链%d），与你否定的片%d（链%d）**不同链**"
              % (running, L.chain_of(running), sid, cid))
        print("   → 不打断！等片%d 跑完，链%d 自然会重排重跑" % (running, cid))
    else:
        print("ℹ 当前没有在跑的片，链%d 直接重排" % cid)
    # 被打回的那片若是 running，要从 running 状态改回 pending
    if running is not None and L.chain_of(running) == cid:
        L.S(led, running)["status"] = L.ST_REJECTED
    L.save(led)
    print("链%d 整条打回待重排：片 %s" % (cid, hit))
    return cid


def cmd_resume(cid, why="改完提示词重排"):
    led = L.load()
    hit = L.set_chain(led, cid, L.ST_PENDING, why)
    L.save(led)
    print("链%d 已插队重排：片 %s（下一个空闲 GPU 周期就跑）" % (cid, hit))
    return cid


def cmd_preflight(sid):
    """把片转为「先出预出片」：低分辨率跑一遍，先验对错。

    用户 2026-10-10 要求：
      「能不能先预出片 就是运行产出分辨率低的 看看是否都对 …
        然后 预出片是对的话 再运行提高分辨率的工作流」
    ⛔ 预出片落 `draft/` 子目录、状态 hold，**不占 out**（终版位置），
      调度器也不会因为它就往下续接下一片。
    """
    L.log_op(sid, "web_preflight", "转低清重跑")
    led = L.load()
    sg = L.S(led, sid)
    sg["stage"] = "preview"
    sg["status"] = L.ST_PENDING
    sg.setdefault("history", []).append(
        {"t": time.strftime("%H:%M:%S"),
         "why": "转预出片模式（%s，约 1/3 时间）" % PROFILE_PREVIEW})
    L.save(led)
    print("片%d 已转预出片模式（%s）。它会先出低分辨率预览片，"
          "你在网页上看过、点「升高清出终版」才继续。"
          % (sid, PROFILE_PREVIEW))
    return sid


def cmd_promote(sid):
    """预出片验过了 → 切到终版档重跑，同名存终版存档。

    ⛔ 终版片落回原前缀 `off_xs01_tNN`，**预览片保留在 draft/ 里**。
      → 网页能同时看到两个，坏了可以回看预出片。
    ⛔ 用 `rejected` 而不是 pending：让调度器知道这片是「人确认过要升」的，
       不被 hold 跳过（hold 的片调度器会整链跳过）。
    """
    L.log_op(sid, "web_promote", "用户确认 → 升高清出终版")
    led = L.load()
    sg = L.S(led, sid)
    if sg.get("stage") == "preview" and not sg.get("draft_out"):
        print("⛔ 片%d 还没有预出片可升，先跑预出片" % sid)
        return None
    sg["stage"] = "final"
    sg["status"] = L.ST_PENDING
    sg.setdefault("history", []).append(
        {"t": time.strftime("%H:%M:%S"),
         "why": "预出片已确认 → 升高清出终版（%s）" % PROFILE_FINAL})
    L.save(led)
    print("片%d 已排入终版队列（%s）。终版存 off_xs01_t%02d，预览片留在 draft/。"
          % (sid, PROFILE_FINAL, sid))
    return sid


def cmd_approve(sid, why="用户认可"):
    """用户点头某片 → 标 approved_by_user，同链被打回时**跳过它**。"""
    L.log_op(sid, "web_approve", why)
    led = L.load()
    sg = L.S(led, sid)
    sg["approved_by_user"] = True
    if sg["status"] == L.ST_REJECTED:
        sg["status"] = L.ST_DONE
    L.save(led)
    print("片%d 已标记认可（同链重排时不会被推翻）" % sid)
    return sid


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("status", "st"):
        cmd_status()
    elif a[0] == "init":
        sids = [int(x) for x in a[1:]] or list(range(1, 9))
        L.save(L.build(sids, title="X003 保洁"))
        print("台账已建：%s" % L.LEDGER)
        cmd_status()
    elif a[0] in ("run", "go"):
        stop = a[a.index("--stopfile") + 1] if "--stopfile" in a else None
        mx = int(a[a.index("--max") + 1]) if "--max" in a else 99
        run(max_seg=mx, stopfile=stop)
    elif a[0] == "reject":
        cmd_reject(int(a[1]), a[2] if len(a) > 2 else "用户否定")
    elif a[0] == "resume":
        cmd_resume(int(a[1]), a[2] if len(a) > 2 else "改完提示词重排")
    elif a[0] == "approve":
        cmd_approve(int(a[1]), a[2] if len(a) > 2 else "用户认可")
    elif a[0] in ("preflight", "pf"):
        cmd_preflight(int(a[1]))
    elif a[0] in ("promote", "up"):
        cmd_promote(int(a[1]))
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    for _s in (signal.SIGINT,):
        try:
            signal.signal(_s, lambda *_: (log("收到中断，当前片跑完就停"),
                                          sys.exit(130)))
        except Exception:
            pass
    main()
