# -*- coding: utf-8 -*-
"""只跑**一段** H3 生成，跑完就收工（不接着跑链上的下一段）。

为什么要这个（2026-10-04 21:25）：
  迭代调画质时，用户要的是「出一段看看效果」，不是等 5 段全出。
  而计划任务那条链路（_run_gen → gen_worker → 链组调度）会：
    · kill 掉我刚重启的 ComfyUI
    · 跑完自动接下一段
  我停计划任务时（Stop-ScheduledTask）**连带把 driver 和 ComfyUI 一起带走了**，
  t01 白跑 6 分钟。所以单段必须**脱离计划任务**、自己管 ComfyUI 生命周期。

流程（自包含，不碰任何计划任务）：
  1. 扫引用图，把**软调版**参考图拷到 ComfyUI 能读的纯 ASCII 目录
  2. 起 ComfyUI（直接开子进程，不走计划任务）
  3. 等就绪（轮询 /system_stats）
  4. 跑 h3_driver.py 跑这一段
  5. 打印成片路径 + 各项指标（p05/p95/p99/饱和/局部对比 vs Seedance 4支目标）
  6. **留着 ComfyUI 不杀**（下次还能接着跑；用户要看画面，不需要省显存）

用法：
  python _run_one.py# 跑 manifest 里第 1 段（老实例 8188）
  python _run_one.py 2          # 跑第 2 段
  python _run_one.py 1 official  # ★ 跑官方原版实例（8189，新模型新工作流）
"""
import glob
import io
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
COMFY_DIR = r"E:\ComfyUI\ComfyUI-master\ComfyUI-master"
COMFY_PY = os.path.join(COMFY_DIR, "venv", "Scripts", "python.exe")
OUT = r"D:\output\new"
SEGS = os.path.join(BASE, "xs001_segs")
REF_OUT = r"C:\Users\86134\.workbuddy\cache\comfy_refs"     # 纯 ASCII，ComfyUI 读图要用
TEMP_DIR = r"D:\ComfyUI_out\ComfyUI-master\temp"
# ⛔ 2026-10-08 15:37：给 show=True 的可见窗口用。cmd.exe 处理非 ASCII 路径有
#    已知毛病（与「bat 中文名被 cmd mangle」同源），所以 console 日志必须落
#    在**纯 ASCII** 目录，否则 tee 静默失败、日志文件不生成。
RO_TMP_ASCII = TEMP_DIR

# ── 官方原版实例（2026-10-06 新增）────────────────────────────────
# 端口 8189 / 输出 D:\output_h3off / ComfyUI_h3official 目录 / 官方原版模型
# 老实例的一切**一个字都不改**，两边靠端口彻底隔离。
OFFICIAL_DIR = r"E:\ComfyUI\ComfyUI_h3official"
OFFICIAL_PORT = 8189
OFFICIAL_OUT = r"D:\output_h3off"
OFFICIAL_TEMP = r"D:\ComfyUI_out\h3official\temp"
# 官方 turbo 档用的工作流（基于现行工作流改：模型名 + LoRA 由 driver 运行时注入）
OFFICIAL_WF = (r"E:\ComfyUI\ComfyUI_new\user\default\workflows"
               r"\04_ref2v_4step_sla_ganloss_fixed.json")


def pop_proxy():
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
              "ALL_PROXY", "all_proxy"):
        os.environ.pop(k, None)
    os.environ["no_proxy"] = "127.0.0.1,localhost"
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"


def comfy_alive(port=8188):
    try:
        urllib.request.urlopen("http://127.0.0.1:%d/system_stats" % port, timeout=5)
        return True
    except Exception:
        return False


def start_comfy(port=8188, cdir=None, out=None, temp=None, tag="one",
                show=True):
    """启动 ComfyUI。

    show=True（默认）→ **弹一个可见的黑窗口**，用户能实时看采样进度。
        用户 2026-10-08 明确要求：「下次启动 你尝试使用前台运行 让我可以看到黑窗口
        我能实时看到进度」。
        用的是 CREATE_NEW_CONSOLE（0x10）而不是 CREATE_NO_WINDOW（0x08000000）——
        后者会把 stdout 藏进日志文件，屏幕上什么都看不到。
    show=False → 原来的后台模式（日志写文件）。给无人值守/自动化用。

    ⚠️ 两种模式都还额外写一份到 logs/comfy_<tag>.log，窗口只是多一份可见输出。
    ⚠️ ComfyUI 启动权只属于生成器：人手动 start 会清空队列（driver 死等）。
    """
    if comfy_alive(port):
        print("ComfyUI 已在运行（端口 %d）" % port)
        return None
    cdir = cdir or COMFY_DIR
    out = out or OUT
    temp = temp or TEMP_DIR
    os.makedirs(temp, exist_ok=True)
    log = os.path.join(BASE, "logs", "comfy_%s.log" % tag)
    os.makedirs(os.path.dirname(log), exist_ok=True)
    # 2026-10-10 内存优化：ComfyUI 常驻 12GB RAM（模型缓存贪着不放）→
    # --cache-none 让每个节点跑完即释放缓存，牺牲少量速度换回 ~6GB 内存。
    # 若实测掉速明显，可换 --cache-ram 4（RAM 压力阈值缓存，折中）。
    cmd = [COMFY_PY, "main.py", "--lowvram", "--enable-triton-backend",
           "--cache-none",
           "--port", str(port),
           "--output-directory", out, "--temp-directory", temp]
    if cdir == OFFICIAL_DIR:
        cmd += ["--user-directory", os.path.join(OFFICIAL_DIR, "user")]
    logfh = open(log, "ab")
    if show:
        # ⛔⛔⛔ 2026-10-08 15:50 连续踩了四坑，逐一记录：
        #   ① stdout=logfh + CREATE_NEW_CONSOLE → 窗口全空（重定向优先级更高）
        #   ② 改成 cmd /c "... | tee 日志" → 日志路径含中文「保洁」，
        #      cmd 按 GBK 读成乱码 → tee 静默失败、**ComfyUI 根本起不来**
        #   ③ 加 UTF-8 BOM → 依然乱码（cmd 不看 BOM）
        #   ④ 把日志改到纯 ASCII 目录 + cmd /c → ComfyUI 仍起不来
        #      （手动前台跑同一条命令完全正常 → 问题在 cmd /c 这层包装）
        # → 结论：**别用 cmd /c 包管道**。最朴素的做法就是「不传任何重定向」，
        #   子进程直接继承新建的可见控制台，文字打在黑窗口里。
        #   日志另开一个后台线程从 /system_stats 拿，不依赖 stdout 重定向。
        flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0x10)
        p = subprocess.Popen(cmd, cwd=cdir, creationflags=flags)
        print("ComfyUI 已开可见窗口（pid=%d 端口 %d）" % (p.pid, port), flush=True)
        print("  ▸ 那个黑窗口就是实时进度：能看到 8 步采样一步步走")
        print("  ▸ 关掉那个窗口会杀掉 ComfyUI，别关（等生成完自动退出）")
        print("  ▸ 另开一个窗口跑看进度.bat 可看进度条")
    else:
        p = subprocess.Popen(cmd, cwd=cdir, stdout=logfh,
                             stderr=subprocess.STDOUT,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000))
        print("ComfyUI 启动 pid=%d 端口 %d …" % (p.pid, port), end="", flush=True)
    for i in range(120):
        time.sleep(2)
        if comfy_alive(port):
            if not show:
                print(" 就绪（%ds）" % (i * 2 + 2))
            else:
                print("  ▸ 就绪（%ds）" % (i * 2 + 2))
            return p
    raise SystemExit("ComfyUI 120 秒未就绪，看 " + log)


def ref_dir_for(official=False):
    """ComfyUI 实例自己的 input 目录（两个实例路径不同，不能混用）。"""
    return os.path.join(OFFICIAL_DIR if official else COMFY_DIR, "input")


def _md5(path):
    """内容短哈希 —— 参考图文件名里带它，换图后文件名必变（见 stage_refs）。"""
    import hashlib
    return hashlib.md5(open(path, "rb").read()).hexdigest()[:8]


def _pick_src_dir(job, official=False):
    """挑参考图来源目录，并打印实际用的那份。

    显式用同名文件在**两个目录**里找：manifest 里存的是逻辑名对应的
    `char_xxx.png` / `sc_xxx.png`，软调版目录里是同一批文件名。

    参考图来源（2026-10-07 决定性修正）：
      **只用 *_single/ 目录**（单人版参考图）。

    ⛔⛔⛔ 为什么必须换成单人版（这是人物复制的真病根）：
      原来的 char_xxx.png 是「三视图 + 大头像」的**设计图**——
      同一个人在那张图上出现了 4 次（大头像 + 正面 + 侧面 + 背面）。
      模型看到的是「四个人」，于是照着画出两个苏小满 / 三个苏小满。
      它不是在犯迷糊，它是在**忠实执行参考图**。
      → 前面三轮我改提示词、砍参考图、禁否定词，全是白费，方向错了。
      → 现在用 _make_single_refs.py 从设计图里裁出「正面全身一个人」，
        落到 assets_single/ 与 assets_soft_single/。

    official=True / False 只影响软调版选择，不影响单人版这件事。

    ⚠️ 换过参考图之后必须核对实际用的是哪一份（2026-10-07 栽过两次）：
      ① 我重画了 assets/ 的工牌图，但 assets_soft/ 里那份**也带工牌**，
         而这里是「哪个目录先凑齐就用哪个」→ 悄悄用了旧图，
         白跑 3 段 45 分钟才发现画面里工牌还在。
      ② 更隐蔽的一层：源目录对了，**但送进 ComfyUI 的那份是旧的** ——
         ComfyUI 的 input/ 里躺着一张同名旧图。见 stage_refs 的说明。
    → 现在这里打目录 + 字节数，stage_refs 打落盘后的真实文件名，两处都能对。
    """
    # ⛔ job 里自带 ref_dir 时优先用它 —— 测试任务（修仙换装）要用
    #    assets_face/脸部特写，不是正片的单人全身图。
    job_dir = job.get("ref_dir")
    if job_dir and os.path.isdir(job_dir) and all(
            os.path.exists(os.path.join(job_dir, r)) for r in job["refs"]):
        src_dir = job_dir
        label = "job 指定 %s/" % os.path.basename(job_dir)
        print("  参考图来源: %s" % label)
        for r in job["refs"]:
            print("    %-22s %d bytes"
                  % (r, os.path.getsize(os.path.join(src_dir, r))))
        return src_dir

    cands = []
    if official:
        cands = [os.path.join(BASE, "assets_single"),
                 os.path.join(BASE, "assets_soft_single")]
        label = "官方原版 单人版 assets_single/"
    else:
        cands = [os.path.join(BASE, "assets_soft_single"),
                 os.path.join(BASE, "assets_single")]
        label = "软调版 单人版 assets_soft_single/"
    src_dir = None
    for d in cands:
        if os.path.isdir(d) and all(
                os.path.exists(os.path.join(d, r)) for r in job["refs"]):
            src_dir = d
            break
    if src_dir is None:
        raise SystemExit("两个目录都找不到这些参考图: %s"
                         % ", ".join(job["refs"]))
    print("  参考图来源: %s" % label)
    # ⚠️ 换过参考图之后必须核对实际用的是哪一份（2026-10-07 栽过）：
    #   我重画了 assets/ 的工牌图，但 assets_soft/ 里那份**也带工牌**，
    #   而这里是「哪个目录先凑齐就用哪个」→ 悄悄用了旧图，
    #   白跑 3 段 45 分钟才发现画面里工牌还在。
    #→ 把实际用的目录 + 每张图的字节数打出来，肉眼就能对。
    for r in job["refs"]:
        print("    %-22s %d bytes" % (r, os.path.getsize(os.path.join(src_dir, r))))
    return src_dir


def stage_refs(job, official=False):
    """把参考图放进 **ComfyUI 自己的 input 目录**（见 _pick_src_dir 选好的来源）。

    ⛔⛔⛔ 2026-10-07 栽过的最隐蔽的一坑（用户亲自抓出来的）：
    原实现把图拷到 `~\\.workbuddy\\cache\\comfy_refs`，workflow 里写的是
    **裸文件名** `r01_ref1.png`。ComfyUI 是在**自己的 input 目录**里找这个名字的
    —— 而那个目录里已经躺着一张 9 月份的旧图（`r01_ref1.png` = 3181021b6b，
    上面清清楚楚挂着工牌「陈慧敏」）。ComfyUI 遇到同名会**自动改名另存**
    （于是出现 `r01_ref1 (1).png` … `(8).png` 一堆副本），但**读的时候仍然读
    自己 input 目录里那个旧名字**。
    → 结果：我以为换了新参考图，日志也打印了源目录和字节数，
      **模型拿到的却是带工牌的旧图**。白跑 16 分钟。
    → 一度误判成「交叉背带导致模型生成工牌」，方向完全错了。

    **两条铁律**：
      ① 参考图必须落在 ComfyUI 实例的 `input/` 里（两个实例路径不同）。
      ② 文件名里带**内容 md5 前 8 位** —— 换图后文件名一定变，
         绝不可能命中旧文件，也不需要靠删除去重。
    """
    src_dir = _pick_src_dir(job, official)
    ref_out = ref_dir_for(official)
    os.makedirs(ref_out, exist_ok=True)

    names = []
    for i, r in enumerate(job["refs"]):
        src = os.path.join(src_dir, r)
        stem = "r%02d_ref%d__%s" % (i + 1, i + 1, _md5(src))
        dst = os.path.join(ref_out, stem + ".png")
        if not os.path.exists(dst):          # 同名同内容 = 同一张图，可复用
            shutil.copy2(src, dst)
        names.append(os.path.basename(dst))
    print("    → ComfyUI input/ %s" % names)
    return names


def build_job(idx, official=False, segs_dir=None):
    """从 jobNN.json 造一个 run 版：填好 workflow、拷好参考图。

    segs_dir: 测试用（2026-10-08 修仙特效）。给了就用那个目录下的 job，
              且**尊重 job 里自带的 prompt_file / ref_dir**（修仙测试要用
              脸部参考图 assets_face，不是正片的 assets_single）。
    """
    sd = segs_dir or SEGS
    jf = os.path.join(sd, "job%02d.json" % idx)
    job = json.load(io.open(jf, encoding="utf-8"))
    custom = bool(segs_dir)
    if not custom:
        job["prompt_file"] = os.path.join(sd, "seg%02d_prompt.txt" % idx)
    job["refs"] = stage_refs(job, official=official)
    if official:
        job["workflow"] = OFFICIAL_WF
        # 官方实例输出独立目录，文件名前缀加 off_ 免得跟老片混淆
        job["out_prefix"] = "off_" + job["out_prefix"]
    else:
        job["workflow"] = (r"E:\ComfyUI\ComfyUI_new\user\default\workflows"
                           r"\04_ref2v_4step_sla_ganloss_fixed.json")
    if not custom:
        job["ref_dir"] = ref_dir_for(official)
    else:
        # 测试任务：job 里写的是**源目录**，但 stage_refs 出来的图落在
        # ComfyUI 自己的 input/ 里 → ref_dir 必须指向那里（跟正片一致）。
        job["ref_dir"] = ref_dir_for(official)
    job["prev_video"] = None
    rf = os.path.join(sd, "job%02d_run%s.json" % (idx, "_off" if official else ""))
    with io.open(rf, "w", encoding="utf-8") as f:
        f.write(json.dumps(job, ensure_ascii=False, indent=1))
    return rf, job


def reclaim_before_gen():
    """生成前清场（用户 2026-10-07 要求）。

    为什么必须每次都做：
      实测 8 步采样里**第 1 步要195-214 秒**，第 2 步之后稳定在 70-74 秒。
      第 1 步慢 = 模型正在往内存/显存里加载，机器越挤加载越慢。
      机器上常驻 300+ 进程占 ~12GB，腾一下就能把加载时间压下来。

    保留（用户点名）：WorkBuddy / v2rayN / mstsc 远程桌面 / 网易UU远程。
    失败不影响生成 —— 体检和清场都是「尽力而为」。
    """
    print("\n" + "=" * 66)
    print(" 生成前清场")
    print("=" * 66)
    try:
        import subprocess as sp
        py = sys.executable
        r = sp.run([py, os.path.join(BASE, "_prep_gen.py"), "--clean"],
                   capture_output=True, text=True, encoding="utf-8",
                   errors="replace", timeout=180)
        out = r.stdout or ""
        # 只打关键几行，别把整个进程表糊在生成日志里
        for line in out.splitlines():
            s = line.strip()
            if (s.startswith("已关") or "物理内存" in s or "显存" in s
                    or "进程数" in s or "ComfyUI" in s):
                print("  " + s)
    except Exception as e:
        print("  清场跳过（%s）" % e)


def main():
    pop_proxy()
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    official = len(sys.argv) > 2 and sys.argv[2] == "official"

    # ⛔ 清场必须在 start_comfy 之前：ComfyUI 一起来就占住内存，
    #    这时再去关别的应用腾的空间已经不多了。
    reclaim_before_gen()

    if official:
        print("=" * 66)
        print(" 官方原版实例（端口 %d，输出 %s）" % (OFFICIAL_PORT, OFFICIAL_OUT))
        print("=" * 66)
    rf, job = build_job(idx, official)
    print("段：%s" % job["out_prefix"])
    print("参考图：%s" % ", ".join(job["refs"]))
    print("提示词：%s（%d 词）" % (os.path.basename(job["prompt_file"]),
                              len(io.open(job["prompt_file"], encoding="utf-8").read().split())))

    if official:
        start_comfy(OFFICIAL_PORT, OFFICIAL_DIR, OFFICIAL_OUT,
                    OFFICIAL_TEMP, "official")
        # 告诉 driver 连新端口
        os.environ["MINIDRAMA_PORT"] = str(OFFICIAL_PORT)
        out_dir = OFFICIAL_OUT
    else:
        start_comfy()
        out_dir = OUT
    env = dict(os.environ)
    env["MINIDRAMA_PORT"] = str(OFFICIAL_PORT if official else 8188)
    t0 = time.time()
    r = subprocess.run([sys.executable, os.path.join(BASE, "h3_driver.py"), rf],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env)
    print("driver rc=%d  用时 %.1f 分钟" % (r.returncode, (time.time() - t0) / 60))
    tail = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()[-10:]
    for l in tail:
        print("   " + l)

    p = os.path.join(out_dir, job["out_prefix"] + "_00001.mp4")
    if not os.path.exists(p):
        print("\n没出片")
        return
    print("\n成片: %s（%.1f MB）" % (p, os.path.getsize(p) / 1048576.0))

    sys.path.insert(0, BASE)
    import _softgrade as SG
    m = SG.measure(p, "one_%02d" % idx)
    tj = os.path.join(BASE, "_seedance_target.json")
    if os.path.exists(tj):
        d = json.load(io.open(tj, encoding="utf-8"))
        T, S, TOL = d["target"], d["stdev"], d["tol"]
        print("\n%-8s %8s %8s %8s  %s" % ("指标", "本段", "SD目标", "容差", "判定"))
        for k in SG.KEYS + ["sat", "local", "contrast", "dyn"]:
            v, t, tol = m[k], T[k], TOL[k]
            ok = "✔" if abs(v - t) <= tol else ("↑" if v > t else "↓")
            print("%-8s %8.1f %8.1f %8.1f  %s" % (k, v, t, tol, ok))
    else:
        print("  " + "  ".join("%s=%.1f" % (k, m[k]) for k in SG.KEYS))
        print("  饱和=%.1f 局部对比=%.2f" % (m["sat"], m["local"]))


if __name__ == "__main__":
    main()
