# -*- coding: utf-8 -*-
r"""
ep001 并发生成器（审核即生成）

与旧 autopilot 的区别：
  · 不再"一次性把 129 段跑完就退出"，而是**常驻**：持续监视 manifest 里每段的内容指纹(sha)，
    一旦某段分镜被改（审核意见落地 → storyboard_render 重渲染），立刻重跑。
  · **每个链组开跑前都重读一次 manifest**（2026-10-03 修）：以前是"整轮 129 段的计划只算一次"，
    分镜改在整轮跑完（约 24 小时）之后才生效，等于没做到"审核一条就同步生成一条"。现在改成
    逐组复查，改动最多 20 秒~一个组的时长就被接上。
  · 失效粒度 = **3 段链组**：链式依赖只存在于组内（第 2、3 段吃上一段的尾帧），
    所以只要组内任一段变了，就从该组「第一个失效的段」起顺序重跑，组头重跑前 kill+重启 ComfyUI。
  · 重跑前把旧成片挪到 D:\output\_stale\，避免 ComfyUI 的自动编号变成 _00002 把链式引用打断。

用法：
  python gen_worker.py ep001            # 跑一遍（补齐所有未完成 / 已失效的段）后退出
  python gen_worker.py ep001 --watch    # 常驻：跑完一遍后每 20s 复查 sha，有变化就补跑
"""
import os
import sys
import json
import time
import shutil
import subprocess
import urllib.request

for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)
os.environ["no_proxy"] = "127.0.0.1,localhost"
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

BASE = os.path.dirname(os.path.abspath(__file__))
WF_DIR = r"E:\ComfyUI\ComfyUI_new\user\default\workflows"
WF_FIXED = os.path.join(WF_DIR, "04_ref2v_4step_sla_ganloss_fixed.json")
WF_CHAIN = os.path.join(WF_DIR, "04_ref2v_seg2_chain.json")
COMFY_CWD = r"E:\ComfyUI\ComfyUI-master\ComfyUI-master"
COMFY_PY = os.path.join(COMFY_CWD, r"venv\Scripts\python.exe")
# 输出根目录。可以用环境变量 MINIDRAMA_OUT 覆盖（2026-10-04 新增）：
# 之前是写死的 D:\output，要换目录就得改代码；而"重跑一遍到新目录"这种
# 需求会反复出现（参数升级后重跑、画质对比留底），硬编码太容易漏改。
OUT_DIR = os.environ.get("MINIDRAMA_OUT", r"D:\output")
STALE_DIR = os.path.join(OUT_DIR, "_stale")
SERVER = "http://127.0.0.1:8188"
TAIL_SKIP = 221
GROUP = 3
# 花屏判定阈值（kbps）。实测：正常段 3500~5000，reference_protection=Light
# 造成的花屏段 10374。取 8000 两者分得很开。见 glitch_check()。
GLITCH_KBPS = 8000
FFPROBE = r"E:\Program Files\ffmpeg\bin\ffprobe.exe"

WATCH = "--watch" in sys.argv
_POS = [a for a in sys.argv[1:] if not a.startswith("--")]

# 多集连续跑：不带参数就自动发现所有已经有 manifest 的集，按集号顺序一集一集跑。
# 用户 2026-10-03：「持续生成视频，直到完成所有剧本的视频」——
# 所以 ep001 跑完必须能自己接上 ep002，不需要有人来重启。
if _POS:
    EPS = _POS
else:
    EPS = sorted(d[:-5] for d in os.listdir(BASE)
                 if d.endswith("_segs") and os.path.exists(os.path.join(BASE, d, "manifest.json")))

# 这三项随"当前集"切换，由 use_ep() 设置
EP = None
SEGS = None
LOGS = None
STATE_F = None
# 统一日志：不管跑哪一集都汇总到这里，方便盯一条流水线
MAIN_LOG = os.path.join(BASE, "logs")


def use_ep(ep):
    global EP, SEGS, LOGS, STATE_F
    EP = ep
    SEGS = os.path.join(BASE, ep + "_segs")
    LOGS = os.path.join(BASE, ep, "logs")
    STATE_F = os.path.join(SEGS, "state.json")


def log(*a):
    line = "%s %s" % (time.strftime("[%Y-%m-%d %H:%M:%S]"), " ".join(str(x) for x in a))
    if EP:
        line = "[%s] %s" % (EP, line)
    print(line, flush=True)
    for d in (LOGS, MAIN_LOG):
        if not d:
            continue
        try:
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "gen_worker.log"), "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


# ------------------------------------------------------------------ ComfyUI
def server_alive(timeout=5):
    try:
        with urllib.request.urlopen(SERVER + "/system_stats", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _ps(cmd, timeout=180):
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                   capture_output=True, timeout=timeout)


def kill_comfyui():
    _ps("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        "Where-Object { $_.CommandLine -like '*main.py*' -and $_.CommandLine -like '*ComfyUI*' } | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }")
    for _ in range(40):
        if not server_alive(2):
            return True
        time.sleep(1)
    return not server_alive(2)


def start_comfyui():
    os.makedirs(LOGS, exist_ok=True)
    logf = open(os.path.join(LOGS, "comfyui_autopilot.log"), "a", encoding="utf-8", errors="replace")
    cmd = [COMFY_PY, "main.py", "--lowvram", "--enable-triton-backend",
           "--output-directory", OUT_DIR,
           "--temp-directory", r"D:\ComfyUI_out\ComfyUI-master\temp"]
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000008
    p = subprocess.Popen(cmd, cwd=COMFY_CWD, stdout=logf, stderr=subprocess.STDOUT,
                         creationflags=flags, close_fds=True)
    log("ComfyUI 启动 pid=%s，等待就绪…" % p.pid)
    for i in range(200):
        time.sleep(3)
        if server_alive(3):
            log("ComfyUI 就绪（%ds）" % ((i + 1) * 3))
            return True
    log("!! ComfyUI 启动超时")
    return False


# ------------------------------------------------------------------ 段状态
def out_audio(seg_id):
    return os.path.join(OUT_DIR, "%s_00001-audio.mp4" % seg_id)


def out_png(seg_id):
    return os.path.join(OUT_DIR, "%s_00001.png" % seg_id)


# 用户 2026-10-03 实看反馈：「视频有点偏黑，人物阴影过重，没有柔和的感觉」。
# 那条反馈的本质是**暗部被压死**（实测老片第 5 百分位灰度只有 2~20，目标要 ≥45）。
# 所以每跑完一段都自动量一次首帧灰度，不达标直接在日志里报警——
# 这样"变暗"不会等到人工看片才发现，也不用有人盯着。
MEASURE_SRC = ("import sys,json;from PIL import Image;"
               "h=Image.open(sys.argv[1]).convert('L').histogram();t=sum(h);c=0;g={}\n"
               "for i,v in enumerate(h):\n"
               "    c+=v\n"
               "    if 'p05' not in g and c>=t*.05: g['p05']=i\n"
               "    if 'med' not in g and c>=t*.5: g['med']=i\n"
               "    if 'p90' not in g and c>=t*.9: g['p90']=i\n"
               "g['mean']=round(sum(i*v for i,v in enumerate(h))/t,1)\n"
               "print(json.dumps(g))")
PY_IMG = r"E:\ComfyUI\ComfyUI-master\ComfyUI-master\venv\Scripts\python.exe"


GRADE_PY = os.path.join(BASE, "_grade.py")

# 2026-10-04 20:40 起**默认关闭**生成后自动调色。
# 原因：用户要求「一次生成就是 Seedance 的效果」，不要事后补救。
# 而 tone 的正解已经搬到**输入端** —— assets_soft/ 参考图按 Seedance 实测分布调过
# （高光 roll-off、饱和收敛），H3 ref2v 会连色调一起复制，出片天生就柔和高调。
# 再叠一层 _grade.py 的「提黑位」只会二次动色，把刚对的东西又调歪
# （实测 t01 自动调色后 mean=130/med=141，比原片更亮更平，反而不对了）。
# 需要旧的补救式调色时：设环境变量 MINIDRAMA_GRADE=1。
GRADE_ON = os.environ.get("MINIDRAMA_GRADE", "0") == "1"


def grade_seg(seg_id):
    if not GRADE_ON:
        log("    跳过调色（MINIDRAMA_GRADE=0，质感由 assets_soft 参考图在输入端保证）")
        return


def grade_seg(seg_id):
    """后期调色（提黑位 + 压对比 + 去冷色）。

    为什么必须做：实测三轮，提示词写满 BRIGHT/NOT dark、场景参考图也从中位 77 提到 155，
    成片的 mean 只从 99.6 动到 101.4 —— H3 这条工作流本身就往高对比暗调走，提示词推不动。
    后期调色是确定性的，6 秒一段，还能**把已经生成的段一起救回来**。
    调的是 -audio.mp4（交付件，也是链式参考），所以链式"越接越黑"会被一起压住。

    ⚠️ 已默认关闭（见 GRADE_ON）。tone 改在输入端做：assets_soft/ 参考图按
       Seedance 实测分布调过，H3 ref2v 会连色调一起复制，出片天生就柔和高调。
    """
    p = os.path.join(OUT_DIR, "%s_00001.mp4" % seg_id)
    if not os.path.exists(p):
        return
    try:
        r = subprocess.run([sys.executable, GRADE_PY, p],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=900)
        if r.returncode != 0:
            log("    !! 调色失败 %s: %s" % (seg_id, ((r.stdout or "") + (r.stderr or ""))[-200:]))
        else:
            log("    调色 %s 完成（提黑位 + 压对比）" % seg_id)
    except Exception as e:
        log("    !! 调色异常 %s: %r" % (seg_id, e))


def brightness(seg_id):
    """量首帧灰度：p05 代表暗部有没有被压死（用户说的"阴影过重"就是它太低）。"""
    p = out_png(seg_id)
    if not os.path.exists(p):
        return None
    try:
        r = subprocess.run([PY_IMG, "-c", MEASURE_SRC, p],
                           capture_output=True, text=True, timeout=120)
        return json.loads((r.stdout or "").strip().splitlines()[-1])
    except Exception as e:
        log("    亮度测量失败 %s: %r" % (seg_id, e))
        return None


def glitch_check(seg_id):
    """检测**花屏**（彩色噪点 / 规则网格纹理覆盖全片）。

    ⛔ 为什么必须单独加这个检查（2026-10-04 16:23 实测事故）：
      reference_protection=Light 生成的 ep01_t01 **整段 11 帧全部花屏**，
      人物完全不可辨。但同一段的亮度检测报的是
          mean=164.9 med=169 p05=88 p90=216  **OK**
      —— 因为亮度只看**灰度均值**，彩噪对灰度均值影响很小，
      所以"亮度正常"完全掩盖了"画面已废"。
      → 教训：**校验项必须覆盖"画面是否还能看"**，不能只覆盖亮度。

    判据用**码率**：花屏段实测 10.4 Mbps，同一段正常成片只有 4.2 Mbps
    （噪点/网格纹理的数据量比干净画面大得多）。阈值取 8 Mbps ——
    正常段实测区间 3.5~5.0 Mbps，坏段 10.4，分得很开。
    零成本（ffprobe 一次），不需要解码。
    """
    p = out_audio(seg_id)
    if not os.path.exists(p):
        return None
    try:
        r = subprocess.run([FFPROBE, "-v", "error", "-show_entries",
                            "format=bit_rate", "-of", "csv=p=0", p],
                           capture_output=True, text=True, errors="replace",
                           timeout=90)
        kbps = int(float((r.stdout or "0").strip())) // 1000
        return kbps
    except Exception as e:
        log("    花屏检测失败 %s: %r" % (seg_id, e))
        return None


def archive_old(seg_id):
    """重跑前把旧成片挪走，否则 ComfyUI 会输出成 _00002 而链式引用仍指向 _00001。"""
    os.makedirs(STALE_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    moved = 0
    for f in os.listdir(OUT_DIR):
        if f.startswith(seg_id + "_") and os.path.isfile(os.path.join(OUT_DIR, f)):
            shutil.move(os.path.join(OUT_DIR, f),
                        os.path.join(STALE_DIR, "%s.%s" % (stamp, f)))
            moved += 1
    if moved:
        log("  归档旧成片 %d 个 → _stale" % moved)


SEG_TIMEOUT = 3600   # 单段上限。正常 10~19 分钟，给到 60 分钟就是 3 倍余量；
                     # 超了就当"卡死"处理，绝不能无限等下去（用户 2026-10-03：禁止长时间等待）


def run_seg(seg, workflow, prev_video):
    j = json.load(open(seg["job"], encoding="utf-8"))
    j["workflow"] = workflow
    j["prev_video"] = prev_video
    if prev_video:
        j["prev_skip"] = TAIL_SKIP
    jf = seg["job"].replace(".json", "_run.json")
    with open(jf, "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=1)
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, os.path.join(BASE, "h3_driver.py"), jf],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=SEG_TIMEOUT)
        rc, out = r.returncode, (r.stdout or "") + "\n" + (r.stderr or "")
    except subprocess.TimeoutExpired:
        # 卡死：不再往上抛（抛出去会让这一轮直接崩），而是当成一次失败，
        # 交给 do_group 既有的"重试 + kill/重启 ComfyUI"逻辑处理。
        rc, out = 124, "TIMEOUT after %ds —— 判定卡死，重启 ComfyUI 重试" % SEG_TIMEOUT
    tail = "\n".join(out.strip().splitlines()[-6:])
    return rc, time.time() - t0, tail


def do_group(members, state, start_at):
    """重跑一组的 start_at..末尾。start_at==0 说明组头要重跑 → 先 kill+重启。

    链组是按 manifest 下标每 3 段硬切的，**不认场次边界**。
    所以会出现「本组第 2/3 段已经换了场次（甚至换了昼夜）」的情况 ——
    那时候再拿上一段的尾帧当首帧，就是夜里会客厅直接接次日医院，场景+时间双跳变。
    修法：**场次一变，这一段就当组头处理**，用 fixed 工作流从参考图从零重建。
    """
    bad_ids = []
    for i in range(start_at, len(members)):
        seg = members[i]
        sid = seg["id"]
        prev_scene = members[i - 1].get("scene") if i > 0 else None
        scene_break = (i > 0 and seg.get("scene") != prev_scene)
        is_head = (i == 0)
        if is_head:
            log("=== %s 链组头：kill ComfyUI 并重启（防越接越黑）===" % sid)
            kill_comfyui()
            time.sleep(4)
            if not start_comfyui():
                state[sid] = {"ok": False, "sha": seg["sha"], "err": "comfyui start failed"}
                save(state)
                return False
            wf, prev = WF_FIXED, None
        elif scene_break:
            log("=== %s 换场次（%s → %s）：改用 fixed 工作流，从参考图重建 ==="
                % (sid, prev_scene, seg.get("scene")))
            wf, prev = WF_FIXED, None
        else:
            wf = WF_CHAIN
            prev = out_audio(members[i - 1]["id"])
            if not os.path.exists(prev):
                log("!! 上一段缺失 %s，本段降级用 fixed" % prev)
                wf, prev = WF_FIXED, None

        archive_old(sid)
        log("--- %s  scene %s  %s  [%s]" % (sid, seg.get("scene"), seg.get("title"),
                                            "fixed" if wf == WF_FIXED else "chain"))
        ok = False
        for attempt in (1, 2):
            rc, dt, tail = run_seg(seg, wf, prev)
            if rc == 0 and os.path.exists(out_audio(sid)):
                ok = True
                log("    完成 %s  %.1f 分钟" % (sid, dt / 60))
                grade_seg(sid)
                b = brightness(sid)
                if b:
                    # 阈值按「有没有把暗部压死」来定，而不是按"整幅平均亮度"——
                    # 特写镜头里人物穿深色工装、背后是深色背景，mean 天生就低（t04 是 100.5），
                    # 但人脸的曝光和柔和感都是对的。按旧的 mean<120 判，会一直误报。
                    bad = []
                    if b["p05"] < 35:
                        bad.append("暗部压死")
                    if b["med"] < 100:
                        bad.append("大面积偏黑")
                    if b["mean"] < 92:
                        bad.append("平均亮度偏低")
                    if b["p90"] > 250:
                        bad.append("亮部近过曝")
                    log("    亮度 %s  mean=%.1f med=%d p05=%d p90=%d%s"
                        % (sid, b["mean"], b["med"], b["p05"], b["p90"],
                           ("  ⚠️ " + " / ".join(bad)) if bad else "  OK"))
                # 花屏检测：亮度合格 **不代表画面能看**（见 glitch_check 文档）
                kb = glitch_check(sid)
                if kb:
                    if kb > GLITCH_KBPS:
                        # 标成失败 → state 不会认为它完成，watch 模式下一轮会重跑
                        state[sid] = {"ok": False, "sha": seg["sha"],
                                      "err": "glitch %d kbps" % kb}
                        log("    花屏 %s  码率=%d kbps（阈值%d）→ 标记失败，"
                            "画面已废，请检查画质档位" % (sid, kb, GLITCH_KBPS))
                        save(state)
                        bad_ids.append(sid)
                    else:
                        log("    码率 %s  %d kbps（正常）" % (sid, kb))
                break
            log("    失败 %s attempt=%d rc=%d\n%s" % (sid, attempt, rc, tail))
            if attempt == 1:
                kill_comfyui()
                time.sleep(4)
                start_comfyui()
                if wf == WF_CHAIN and not os.path.exists(prev):
                    wf, prev = WF_FIXED, None
        state[sid] = {"ok": ok, "sha": seg["sha"],
                      "wf": "fixed" if wf == WF_FIXED else "chain",
                      "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
        save(state)
    return True


def load_state():
    if os.path.exists(STATE_F):
        try:
            return json.load(open(STATE_F, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save(state):
    tmp = STATE_F + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_F)


def fresh(seg, state):
    st = state.get(seg["id"]) or {}
    return bool(st.get("ok")) and st.get("sha") == seg["sha"] and os.path.exists(out_audio(seg["id"]))


def load_manifest():
    return json.load(open(os.path.join(SEGS, "manifest.json"), encoding="utf-8"))


def first_bad(members, state):
    """组内第一个「不新鲜」的段号；全组新鲜返回 None。"""
    for i, m in enumerate(members):
        if not fresh(m, state):
            return i
    return None


def one_pass_ep():
    manifest = load_manifest()
    state = load_state()

    plan = []
    for g0 in range(0, len(manifest), GROUP):
        members = manifest[g0:g0 + GROUP]
        bad = first_bad(members, state)
        if bad is not None:
            plan.append((g0, bad))

    if not plan:
        # 安静返回：main 每 20 秒复查一次，这里如果打日志会刷屏
        return 0

    log("待处理 %d 个链组，共 %d 段。" % (len(plan), sum(len(manifest[g:g + GROUP]) - b for g, b in plan)))
    for g0, _ in plan:
        # 用户要求「审核出来一条就同步生成一条，并发执行」——
        # 所以每开跑一个链组之前都要重读 manifest/state：
        #   · 前面的组跑完，可能已经把这组需要的上一段补齐了，这组就不用再跑；
        #   · 也可能审核刚好改了这一组/后面的段，指纹变了，这一步就得跟着变。
        # 绝不能还用几小时前算好的计划往下跑。
        manifest = load_manifest()
        state = load_state()
        members = manifest[g0:g0 + GROUP]
        if not members:
            continue
        bad = first_bad(members, state)
        if bad is None:
            continue
        if not do_group(members, state, bad):
            return 4
    log("本轮完成。")
    return 0


def one_pass():
    """一集一集地跑；没有 manifest 的集直接跳过（分镜还没做好的集不会被误跑）。"""
    if EPS:
        # 先定好"当前集"，否则 LOGS 还是 None，start_comfyui() 里的
        # os.makedirs(LOGS) 会抛 TypeError 把整轮打断。
        use_ep(EPS[0])
    if not server_alive():
        start_comfyui()
    skipped = []
    for ep in EPS:
        use_ep(ep)
        if not os.path.exists(os.path.join(SEGS, "manifest.json")):
            skipped.append(ep)
            continue
        rc = one_pass_ep()
        if rc:
            return rc
    if skipped:
        log("跳过（还没有分镜 manifest）：%s" % ", ".join(skipped))
    return 0


def main():
    os.makedirs(MAIN_LOG, exist_ok=True)
    log("进入监视模式：每 20s 复查 manifest 指纹，发现分镜改动即补跑。集队列=%s"
        % (", ".join(EPS) if EPS else "(空)"))
    while True:
        try:
            rc = one_pass()
        except Exception as e:
            log("本轮异常：%r，30s 后重试" % (e,))
            time.sleep(30)
            continue
        if rc:
            return rc
        if not WATCH:
            return 0
        time.sleep(20)


if __name__ == "__main__":
    sys.exit(main())
