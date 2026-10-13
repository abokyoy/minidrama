# -*- coding: utf-8 -*-
r"""
正片续写链 —— 每 3 段一个链组（用户 2026-10-08 16:17 拍板的核心模式）

★ 工作流模式（最重要，务必照此执行）★
  seg01 fixed           ← 从参考图出画面
  seg02 chain ← seg01   ← 拿上一段尾帧续接
  seg03 chain ← seg02
  ────── 断链 ──────      （重启 ComfyUI，避免越接越黑）
  seg04 fixed
  seg05 chain ← seg04
  seg06 chain ← seg05
  ────── 断链 ──────
  seg07 fixed ...

  规律：段号 % 3 == 1 → fixed；否则 → chain 接上一段。

★ 这一批段号（seg02 已用 00013 跑完，跳过）★
  seg03 fixed（组内第1段）→ seg04 chain → seg05 chain
  → seg06 fixed → seg07 chain → seg08 chain

⛔ 四条铁律（都是踩坑踩出来的）★
  1. chain 第 1 段绝对不能用：节点 910 里写死了别人电脑的路径 Z:\wx\...
     prev_video=None 时必须 fixed，否则报 HTTP 400 Invalid file path
  2. 参考图 refs 必须与已认可段**逐字一致**（seg05 是 2 张，多给 1 张 → 画出两个苏小满）
  3. 场景段落必须整段抄过去，不能因为「渲染器会拼常量」就省 → 省了场景就变
  4. h3_driver.py 自己不起 ComfyUI → 必须借 _run_one.py 的 start_comfy/reclaim

用法：
    python _chain.py 3 4 5           # 跑指定段（自动判断 fixed/chain）
    python _chain.py 3 4 5 6 7 8     # 连跑，按 3 段一组自动断链
    python _chain.py 3 4 5 --force   # 已有成片也重跑
"""
import os, sys, io, json, time, subprocess, glob, importlib.util, re

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
           "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)
os.environ["no_proxy"] = "127.0.0.1,localhost"
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# ⚠️ h3_driver.py 自己不会起 ComfyUI（踩过：直接调它 → WinError 10061 拒连）
_spec = importlib.util.spec_from_file_location("ro", os.path.join(HERE, "_run_one.py"))
RO = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RO)

DRIVER = os.path.join(HERE, "h3_driver.py")
OUT_DIR = r"D:\output_h3off"
INST_DIR = r"E:\ComfyUI\ComfyUI_h3official"
WF_DIR = r"E:\ComfyUI\ComfyUI_new\user\default\workflows"
WF = {
    "fixed": os.path.join(WF_DIR, "04_ref2v_4step_sla_ganloss_fixed.json"),
    "chain": os.path.join(WF_DIR, "04_ref2v_seg2_chain.json"),
}
# ⛔ 2026-10-09 新增：A/B/C 三个变体（由 _mk_variants.py 从 chain 派生，原文件不动）
#   vA 双端锚：头 22 帧 + 末帧单图（912 LoadImage → 913 AddGuide frame_idx=242）
#   vB 音轨锚：910.audio → 911.audio，audio_vae 接 120
#   vC 单帧几何锚：910.frame_load_cap=1, skip=242
WF_VARIANTS = {
    "vA": (os.path.join(WF_DIR, "04_ref2v_seg2_chain_vA_dualanchor.json"), {}),
    "vB": (os.path.join(WF_DIR, "04_ref2v_seg2_chain_vB_audio.json"), {}),
    # ⛔ C 必须同时给 prev_cap=5 / prev_skip=238，否则 driver 沿用工作流默认的
    #    cap=22 → 跑的还是 22 帧 clip 锚，「C 变体」名存实亡。
    # ⛔⛔ cap 只能是 5/22/39…（17k+5），**不能是 1**。实测 cap=1 直接报
    #    RuntimeError: stack expects a non-empty TensorList ——
    #    VHS 的 format="H3" 会做 (n-5)//17*17+5 的截断，cap=1 → -4 帧 → 空列表。
    #    → 最小锚帧是 5 帧，不存在「单帧锚」。
    "vC": (os.path.join(WF_DIR, "04_ref2v_seg2_chain_vC_singleframe.json"),
           {"prev_cap": 5, "prev_skip": 238}),
}
HEAD_REF = os.path.join(HERE, "xs001_segs", "_head_ref.png")
# ⛔⛔ 参考图必须与提示词里的 <Picture N> 数量**严格一致**（2026-10-08 打回）
# 踩坑记录：提示词有 3 个 Subject（钱经理/苏小满/小唐），我只给 2 张图
#   → 小唐的「It is the person shown in <Picture 3>」找不到对应脸
#   → 模型只能拿现有脸来凑 → **小唐长成苏小满的脸**（用户打回原话：
#      「两个苏小满 那个小唐 是苏小满的脸」）。
# 上一轮我为了防「人物复制」把第 3 张删了，同样是错的 —— 人物复制的原因是
#   **一张图里有几个人**，不是图的数量。三个人就给三张单人图。
# → 校验：refs 数量必须等于提示词里出现的最大 <Picture N>。
#
# ⛔⛔ 2026-10-09 又踩一次：REFS 被我写死成 3 张，但 **seg01 是 4 张**
#   （三个人的脸 + 一张办公室全景布局图 <Picture 4>）
#   → seg01 跑起来直接SystemExit(5) 报错，浪费一次起 ComfyUI 的时间。
# → REFS **按段号取**，不要一份列表打天下。
#   查某段到底该给几张：直接读它的 job0N_run_off.json，那才是上次真正跑通的配置。
# ⛔⛔ 2026-10-09 第二次：seg02~07 原本只给 3 张（没房间图），
#   但 2026-10-09 10:15 起全部七段都加了 <Picture 4> 房间布局图
#   → 不给图 = 房间每段由模型自由发挥 = 「场景都变了 没有衔接」（用户原话）
#   → 现在七段统一 4 张：钱经理 / 苏小满 / 小唐 / 办公室全景
#   ⚠️ 顺序不能变：<Picture N> 的 N 就是 refs 列表下标+1
_REFS_FULL = ["r01_ref1__9caa7471.png", "r02_ref2__bcad60c8.png",
              "r03_ref3__016bdb32.png", "r04_ref4__a039524b.png"]
REFS_BY_SEG = dict((i, list(_REFS_FULL)) for i in range(1, 9))
# 兜底：没登记的段用这个（⚠️ 不保证对，跑之前先对账提示词里的<Picture N>）
REFS = list(_REFS_FULL)
GROUP = 3          # 每 3 段一个链组
KEEP_PREV = True   # True = 组内接上一段；False = 组内第2段也重新出画面
# 当前规格。⛔ 换过画幅/改过提示词后旧片必须作废重跑（stale_reason 用它判定）
WANT_ASPECT = "4:3 (Standard)"


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


def kind_of(seg_no):
    """段号 → 工作流。★ 核心模式：每 3 段一组，组内第 1 段 fixed。

    ⛔ 但真正决定用 fixed 的不是段号，而是**有没有上一段尾帧可接**：
      chain 工作流节点 910 里写死了别人电脑的路径 Z:\\wx\\...，
      prev_video=None 时 driver 不会改它 → 报 HTTP 400 Invalid file path。
      所以：组内第 1 段（固定）**或** 本次是断链后第一段（无 prev）→ 必须 fixed。
    """
    return "fixed" if (seg_no - 1) % GROUP == 0 else "chain"


def kind_for_run(seg_no, prev):
    """实际该用哪个工作流 —— 有 prev 才能用 chain。"""
    if not prev:
        return "fixed"     # ⛔ 无上一段尾帧 → 必须 fixed（chain 会 400）
    # 2026-10-11 实测：连续2跳 chain 站位延续、亮度不坠（c1_end/c2/c3 四帧核验）。
    # 用户痛斥「位置变来变去」→ 设 H3_CHAIN_ALL=1 时只要有 prev 就全链，消灭跳变。
    if os.environ.get("H3_CHAIN_ALL") == "1":
        return "chain"
    return kind_of(seg_no)


def newest(prefix):
    """按修改时间取最新成片。⛔ 绝不信日志里的路径（一直报 D:\\output\\，
    实际在 D:\\output_h3off\\；序号也报 1 实际是 13）"""
    fs = glob.glob(os.path.join(OUT_DIR, prefix + "*.mp4"))
    return max(fs, key=os.path.getmtime) if fs else None


# ── 旧片作废判定（2026-10-09 新增）─────────────────────────────────
# 起因：跳过逻辑原本只看「文件存不存在」→ 10-08 的 9:16 竖屏旧片
#       被当成本轮 4:3 的成片跳过，用户以为我没跑。
ASPECT_W_H = {"4:3 (Standard)": (4, 3), "9:16 (Portrait)": (9, 16),
              "3:4 (Standard)": (3, 4), "16:9 (Standard)": (16, 9)}


def _probe_size(path):
    """不 ffprobe，用文件头读宽高（避免 OpenCV 读不了中文路径的老坑）。"""
    try:
        import subprocess as sp
        out = sp.run(["ffprobe", "-v", "quiet", "-select_streams", "v:0",
                      "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x",
                      path], capture_output=True, text=True, timeout=30).stdout.strip()
        w, h = out.split("x")[:2]
        return int(w), int(h)
    except Exception:
        return None


def stale_reason(path, kind):
    """成片与当前规格不符 → 返回原因字符串；没问题 → None。"""
    if not path or not os.path.exists(path):
        return None
    # ① 画幅对不上（换过画幅的旧片必须作废）
    want = ASPECT_W_H.get(WANT_ASPECT)
    got = _probe_size(path)
    if want and got:
        pw, ph = want
        gw, gh = got
        # 容差 3%，避开 1024x768 vs 1023x768 这类取整
        if abs(gw / float(gh) - pw / float(ph)) > 0.03:
            return "画幅不符（成片 %dx%d≈%.2f，要 %dx%d≈%.2f）" % (
                gw, gh, gw / float(gh), pw, ph, pw / float(ph))
    # ② 成片早于提示词文件 = 提示词改过了，这片是旧提示词出的
    seg_prompt = os.path.join(HERE, "xs001_segs", "seg%02d_prompt.txt"
                              % int(re.search(r"t(\d+)", path).group(1)))
    if os.path.exists(seg_prompt):
        if os.path.getmtime(path) < os.path.getmtime(seg_prompt):
            return "成片比提示词旧（提示词已改）"
    return None


def find_prev_video(sid):
    """找上一段（sid-1）最新的成片，作为 chain 的引导视频。

    ⛔⛔ 这段函数是 2026-10-08 21:12 补的。之前单段跑（_chain.py 3）
    prev 永远是 None → kind_for_run 退回 fixed → **chain 一次都没真跑起来**，
    我却把「续写链模式落地」写进了 MEMORY.md。用户骂「搞了这么久没有续写链过」。

    两种落盘位置都要找（日志打印的位置长期不可信）：
      D:\\output_h3off\\  ← 官方实例真实输出目录
      D:\\output\\        ← 日志里一直报的那个（假的）
    优先挑带 -audio 的（有音轨=完整成片）。
    """
    for cand in ("D:/output_h3off", "D:/output", OUT_DIR):
        prefix = "off_xs01_t%02d" % (sid - 1)
        fs = glob.glob(os.path.join(cand, prefix + "*-audio.mp4"))
        if fs:
            return max(fs, key=os.path.getmtime)
    return None


def kill_comfy():
    os.environ["MINIDRAMA_PORT"] = str(RO.OFFICIAL_PORT)
    subprocess.run([sys.executable, os.path.join(HERE, "_kill_old.py")],
                   capture_output=True, text=True, timeout=180, cwd=HERE)


def run_driver(job_path, env, timeout=3000):
    p = subprocess.run([sys.executable, "-u", DRIVER, job_path],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, env=env, cwd=HERE)
    out = (p.stdout or "") + (p.stderr or "")
    for ln in out.splitlines():
        if any(k in ln for k in ("SUBMITTED", "DONE", "SAVED", "成片", "ERROR",
                                 "QUALITY", "MODEL", "LORA", "参考图")):
            log("  ", ln.strip())
    if p.returncode != 0:
        log("!! driver 退出码", p.returncode)
        log(out[-1200:])
        raise SystemExit(p.returncode)


def main():
    force = "--force" in sys.argv
    # ⛔ 2026-10-08 22:20 加：--kind chain|fixed 强制覆盖组规则。
    #   起因：seg04 按「每 3 段一组」该用 fixed，但 fixed 从零重建 →
    #   场景全漂（钱经理从站变坐、桌上多个台灯、地上多把椅子）。
    #   实测 chain 版场景完全接住，所以链组断链点也允许手动指定 chain。
    forced_kind = None
    for a in sys.argv:
        if a.startswith("--kind="):
            forced_kind = a.split("=", 1)[1]
    # ⛔ 2026-10-09：--wf=vA|vB|vC 指定变体工作流（A/B/C 实验用）
    forced_wf = None
    for a in sys.argv:
        if a.startswith("--wf="):
            forced_wf = a.split("=", 1)[1]
    args = [a for a in sys.argv[1:]
            if not a.startswith("--") and not a.startswith("--kind=")
            and not a.startswith("--wf=")]

    # --plan 只打印工作流分配，不生成（先看清再烧显存）
    if "--plan" in sys.argv:
        nums = [int(a) for a in args] or list(range(1, GROUP * 3 + 1))
        print("段号 -> 工作流（每 %d 段一组，组内第 1 段 fixed）" % GROUP)
        for n in range(1, max(nums) + 1):
            g = (n - 1) // GROUP
            mark = "  <- 断链重启 ComfyUI" if (n - 1) % GROUP == 0 and n > 1 else ""
            print("  seg%02d  %-6s  第%d组%s" % (n, kind_of(n), g + 1, mark))
        return 0

    if not args:
        print(__doc__)
        return 1
    segs = [int(a) for a in args]

    log("=" * 66)
    plan = []
    for n in segs:
        k = kind_of(n)
        plan.append("%02d:%s" % (n, k))
    log(" 工作流模式（每 %d 段一组，组内第 1 段 fixed）: %s"
        % (GROUP, "  ".join(plan)))
    log(" 参考图（按段取）: " + "; ".join(
        "seg%02d=%d张" % (n, len(REFS_BY_SEG.get(n, REFS))) for n in segs))
    log("=" * 66)

    # ── ⭐⭐⭐ 最高原则：显卡永远不许空转（2026-10-09 用户原话）────────────
    # 「最高效利用显卡 确保显卡一直在跑任务…要合理调度显卡资源
    #   确保显卡一直有任务在做」
    #
    # 空转发生在哪：每段之间要「拷参考图 → 建 job.json → 重启 ComfyUI」，
    # 这些全是 CPU/磁盘活，**GPU 这几秒到几十秒完全闲着**。
    # 解法：**开跑前把本批全部段的参考图一次性拷进 ComfyUI 的 input/**，
    # 循环里只读缓存下来的文件名 → 段间零拷贝，GPU 立刻接下一段。
    #
    # ⚠️ 提交进队列**不占显存**，所以提前准备是安全的；
    #    真正抢显存会崩的是「两实例同时采样」，那个仍然禁止。
    # ⛔⛔⛔ 2026-10-09 15:10 修：预取的源目录找错了，白跑 6 次「预取跳过」。
    #   REFS_BY_SEG 里存的是**已暂存名**（r01_ref1__<md5>.png），
    #   它们只存在于 ComfyUI 自己的 input/ 里（job 的 ref_dir 就指那儿），
    #   源目录 assets_single/ 装的是 char_xxx.png 这种逻辑名 → 永远找不到。
    #   正确顺序：先看 ComfyUI input/（多半已在，直接白拿），
    #   缺了才从逻辑名源目录 stage 一遍。
    PREFETCHED = {}
    t_pf = time.time()
    cdir = RO.ref_dir_for(True)
    for sid in segs:
        raw = list(REFS_BY_SEG.get(sid, REFS))
        if all(os.path.exists(os.path.join(cdir, r)) for r in raw):
            PREFETCHED[sid] = list(raw)          # 已在 input/，零拷贝直接用
            continue
        # 缺图：按逻辑名（char_*.png / sc_*.png）从源目录 stage
        logical = [r.split("__")[0] for r in raw]   # r01_ref1__xxx → 交给 manifest 还原
        try:
            PREFETCHED[sid] = RO.stage_refs({"refs": logical}, official=True)
        except Exception as e:
            log(" seg%02d 参考图预取失败（%s）→ 段内自己处理" % (sid, e))
    log(" 参考图：%d/%d 段就绪（ComfyUI input/ 命中 %d 段），用时 %.1fs"
        % (len(PREFETCHED), len(segs),
           sum(1 for sid in segs if PREFETCHED.get(sid) ==
               list(REFS_BY_SEG.get(sid, REFS))), time.time() - t_pf))

    # ⛔ 铁律 4：清场 + 自己起 ComfyUI
    RO.reclaim_before_gen()

    prev = None
    last_group = None
    # ⛔⛔ 2026-10-08 21:12 修：单段入口必须去磁盘找上一段的成片。
    #    以前 prev 只在「连续跑多段」时才有值，单段跑永远是 None → 永远 fixed。
    #    这就是「写了 chain 模式但一次没真跑过」的原因。
    if len(segs) == 1 and (kind_of(segs[0]) == "chain" or forced_kind == "chain"):
        prev = find_prev_video(segs[0])
        log(" 单段入口：按段号找上一段成片 -> %s"
            % (os.path.basename(prev) if prev else "（找不到，将退回 fixed）"))

    for n, sid in enumerate(segs, 1):
        prefix = "off_xs01_t%02d" % sid

        # 断链：换组时 kill + 重启 ComfyUI（越接越黑）
        if last_group is not None and (sid - 1) // GROUP != last_group:
            log("── 断链（第 %d 组 → 第 %d 组）：重启 ComfyUI ──"
                % (last_group + 1, (sid - 1) // GROUP + 1))
            kill_comfy()
            RO.reclaim_before_gen()
            prev = None
        last_group = (sid - 1) // GROUP

        # ⛔⛔⛔ 2026-10-09 13:32 修：连跑多段时，**每段都要重新找上一段尾帧**。
        #   以前 prev 只在两种情况有值：①单段入口 find_prev_video ②上一段刚跑完。
        #   于是「连跑 3 4 5 6 7 8」的第一段 seg03 若不是链组开头（3 不是），
        #   prev=None → kind_for_run 退回 fixed → 硬校验 SystemExit(6) 中止。
        #   症状：日志只到[1/6] seg03 就停，看起来像「跑不动了」。
        #   2026-10-11 修：H3_CHAIN_ALL=1 时 fixed 档也要找上一段尾帧
        #   （否则链组头部 seg04/seg07 永远 prev=None → 永远 fixed → 跳变回归）。
        if prev is None and (kind_of(sid) == "chain"
                             or os.environ.get("H3_CHAIN_ALL") == "1"):
            prev = find_prev_video(sid)
            log("  ↳ 接上一段（%s）: %s"
                % (sid - 1, os.path.basename(prev) if prev else "（找不到）"))

        # ⛔ 真正的工作流由「有没有 prev」决定（chain 无 prev 会 400）
        kind = kind_for_run(sid, prev)
        if forced_kind:
            kind = forced_kind
            if kind == "chain" and not prev:
                log("!! --kind=chain 但找不到上一段尾帧，无法续写")
                raise SystemExit(7)

        existing = newest(prefix)
        # ⛔⛔⛔ 2026-10-09 10:40 打回：跳过逻辑只看「文件存不存在」，
        #   于是 10-08 那批 9:16 竖屏旧片被当成本轮 4:3 的成片跳过
        #   （用户要看新片，结果拿到的是昨天的旧片，还以为我没跑）。
        #   判断标准必须包含「规格是否与当前一致」+「是否比提示词新」。
        why = stale_reason(existing, kind) if existing else None
        if existing and not force and not why:
            log("[%d/%d] seg%02d 已有成片，跳过 -> %s"
                % (n, len(segs), sid, os.path.basename(existing)))
            prev = existing
            continue
        if existing and why:
            log("[%d/%d] seg%02d 旧片作废（%s）-> 重跑 %s"
                % (n, len(segs), sid, why, kind))

        log("[%d/%d] seg%02d  工作流=%s  prev=%s"
            % (n, len(segs), sid, kind,
               os.path.basename(prev) if prev else "(无，用参考图)"))

        # ⛔⛔ 2026-10-08 21:12 加：chain 静默退回 fixed 必须当场报出来。
        #    以前没有这道校验，于是「计划 chain / 实际 fixed」被日志第 177 行
        #    一行字带过，我看了 20 多次都没发现，害我以为 chain 已在用。
        if kind_of(sid) == "chain" and kind != "chain":
            log("!!⛔⛔ 本该 chain 却退回 fixed：上一段尾帧没找到")
            log("   计划 = %s" % " ".join("%02d:%s" % (x, kind_of(x)) for x in segs))
            log("   根因：链组第1 段之后每一段都必须接上一段尾帧；")
            log("   找不到就说明上一段根本没生成过，或落盘在别处。")
            if "--allow-fixed-fallback" not in sys.argv:
                log("   不许静默降级。确认要用 fixed 请显式加 --allow-fixed-fallback")
                raise SystemExit(6)

        # 断链后需要重新起 ComfyUI
        if not RO.comfy_alive(RO.OFFICIAL_PORT):
            RO.start_comfy(RO.OFFICIAL_PORT, RO.OFFICIAL_DIR, RO.OFFICIAL_OUT,
                           RO.OFFICIAL_TEMP, "official", show=True)
        env = dict(os.environ)
        env["MINIDRAMA_PORT"] = str(RO.OFFICIAL_PORT)

        refs = PREFETCHED.get(sid)
        if refs is None:
            refs = list(REFS_BY_SEG.get(sid, REFS))
        job = {
            "workflow": WF[kind],
            "prompt_file": os.path.join(HERE, "xs001_segs", "seg%02d_prompt.txt" % sid),
            "out_prefix": prefix,
            "ref_dir": os.path.join(INST_DIR, "input"),
            "refs": refs,
            "prev_video": prev,
        }
        tag = kind
        if forced_wf:
            if forced_wf not in WF_VARIANTS:
                raise SystemExit("未知变体 %s（可选 %s）"
                                 % (forced_wf, "/".join(WF_VARIANTS)))
            wpath, extra = WF_VARIANTS[forced_wf]
            if not os.path.exists(wpath):
                raise SystemExit("变体工作流不存在: %s（先跑 _mk_variants.py）" % wpath)
            job["workflow"] = wpath
            job.update(extra)
            tag = "%s/%s" % (kind, forced_wf)
            # A 变体多一个 912 LoadImage 节点，必须单独上传那张基准帧
            if forced_wf == "vA":
                if not os.path.exists(HEAD_REF):
                    raise SystemExit("vA 需要基准帧 %s（用 ffmpeg 从上一段首帧抽）"
                                     % HEAD_REF)
                job["guide_images"] = [{"node": "912", "file": HEAD_REF}]
            log("    变体工作流 = %s  (%s)"
                % (os.path.basename(wpath), tag))
        # ⛔ 铁律：refs 数量必须 == 提示词里最大的 <Picture N>，否则某个人没脸可用
        #    （踩过两次：3 个 Subject 只给 2 张图 → 小唐长成苏小满的脸；
        #seg01 是 4 张（P1~P3 人脸 + P4 布局图），我写死 3 张 → SystemExit(5)）
        pf = job["prompt_file"]
        txt = io.open(pf, encoding="utf-8").read()
        need = max([int(x) for x in re.findall(r"<Picture (\d+)>", txt)] or [0])
        if need != len(refs):
            log("!! 参考图数量不对：seg%02d 提示词要 <Picture 1..%d> 但只给了 %d 张"
                % (sid, need, len(refs)))
            log("   REFS_BY_SEG 里没登记这一段，或登记错了。"
                "查法：读 xs001_segs/job%02d_run_off.json —— 那是上次真跑通的配置" % sid)
            log("   少给图 → 那个 Subject 没脸可用，模型拿别人的脸凑"
                "（用户打回过：「小唐 是苏小满的脸」）")
            raise SystemExit(5)
        jp = os.path.join(HERE, "xs001_segs",
                          "job%02d_%s.json" % (sid, tag.replace("/", "_")))
        json.dump(job, io.open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        log("    作业文件 = %s" % os.path.basename(jp))
        run_driver(jp, env)

        got = newest(prefix)
        if not got:
            log("!! seg%02d 没找到成片" % sid)
            raise SystemExit(4)
        log("    -> %s  (%.2f MB)" % (got, os.path.getsize(got) / 1048576.0))
        prev = got

    log("=" * 66)
    log(" 跑完。产物：")
    for sid in segs:
        f = newest("off_xs01_t%02d" % sid)
        if f:
            log("  seg%02d  %-6s  %7.2f MB  %s"
                % (sid, kind_of(sid), os.path.getsize(f) / 1048576.0, f))
    log("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())
