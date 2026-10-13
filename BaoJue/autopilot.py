# -*- coding: utf-8 -*-
r"""
ep001 自动生成流水线
规则（用户最高原则）：
  · 每 3 段为一个「链组」，组内第 1 段用 fixed 工作流（参考图出画面），第 2、3 段用 chain 工作流（拿上一段尾帧续接）
  · 每开始一个新的链组（第 4、7、10… 段）之前，必须 kill 掉 ComfyUI 进程并重新启动，避免越接越黑
  · 输出统一落在 D:\output
  · 断点续跑：已存在成片的段直接跳过
用法： python autopilot.py ep001
"""
import os, sys, json, time, subprocess, urllib.request, urllib.error, shutil, signal

# 本机环境变量里的代理会 502 掉 127.0.0.1，必须先清掉
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
OUT_DIR = r"D:\output"
SERVER = "http://127.0.0.1:8188"
TAIL_SKIP = 221
GROUP = 3


def log(*a):
    print(time.strftime("[%Y-%m-%d %H:%M:%S]"), *a, flush=True)


def server_alive(timeout=5):
    try:
        with urllib.request.urlopen(SERVER + "/system_stats", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def kill_comfyui():
    """只杀跑 ComfyUI main.py 的 python 进程，绝不误杀 agent 自己的 python"""
    ps = (
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        "Where-Object { $_.CommandLine -like '*main.py*' -and $_.CommandLine -like '*ComfyUI*' } | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=120)
    for _ in range(30):
        if not server_alive(2):
            return True
        time.sleep(1)
    return not server_alive(2)


def start_comfyui():
    """等效于双击「启动旧版ComfyUI(视频).bat」：
       cd E:\\ComfyUI\\ComfyUI-master\\ComfyUI-master && venv\\Scripts\\python.exe main.py --lowvram ...
       （改成直接调 python 是为了把 stdout 落到日志里，方便无人值守时排查）"""
    logf = open(os.path.join(BASE, "ep001", "logs", "comfyui_autopilot.log"), "a", encoding="utf-8", errors="replace")
    cmd = [COMFY_PY, "main.py", "--lowvram", "--enable-triton-backend",
           "--output-directory", OUT_DIR,
           "--temp-directory", r"D:\ComfyUI_out\ComfyUI-master\temp"]
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000008  # DETACHED_PROCESS
    p = subprocess.Popen(cmd, cwd=COMFY_CWD, stdout=logf, stderr=subprocess.STDOUT,
                         creationflags=flags, close_fds=True)
    log("ComfyUI 启动 pid=%s，等待就绪…" % p.pid)
    for i in range(200):
        time.sleep(3)
        if server_alive(3):
            log("ComfyUI 就绪（%.0fs）" % ((i + 1) * 3))
            return True
    log("!! ComfyUI 启动超时")
    return False


def run_seg(job, workflow, prev_video):
    j = json.load(open(job["job"], encoding="utf-8"))
    j["workflow"] = workflow
    j["prev_video"] = prev_video
    if prev_video:
        j["prev_skip"] = TAIL_SKIP
    jf = job["job"].replace(".json", "_run.json")
    json.dump(j, open(jf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    t0 = time.time()
    r = subprocess.run([sys.executable, os.path.join(BASE, "h3_driver.py"), jf],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
    dt = time.time() - t0
    tail = "\n".join(((r.stdout or "") + "\n" + (r.stderr or "")).strip().splitlines()[-8:])
    return r.returncode, dt, tail


def main():
    ep = sys.argv[1]
    segs_dir = os.path.join(BASE, ep + "_segs")
    os.makedirs(os.path.join(BASE, ep, "logs"), exist_ok=True)
    manifest = json.load(open(os.path.join(segs_dir, "manifest.json"), encoding="utf-8"))
    state_f = os.path.join(segs_dir, "state.json")
    state = json.load(open(state_f, encoding="utf-8")) if os.path.exists(state_f) else {}

    if not server_alive():
        start_comfyui()

    for i, seg in enumerate(manifest):
        idx = i + 1
        pos = (i % GROUP) + 1                 # 组内位置 1/2/3
        prefix = seg["id"]
        done = os.path.join(OUT_DIR, "%s_00001-audio.mp4" % prefix)
        if prefix in state and state[prefix].get("ok") and os.path.exists(done):
            log("跳过 %s（已完成）" % prefix)
            continue

        if pos == 1:
            if i > 0:
                log("=== 新链组：kill ComfyUI 并重启（防越接越黑）===")
                kill_comfyui()
                time.sleep(4)
                if not start_comfyui():
                    state[prefix] = {"ok": False, "err": "comfyui start failed"}
                    json.dump(state, open(state_f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                    return 4
            wf, prev = WF_FIXED, None
        else:
            wf = WF_CHAIN
            prev = os.path.join(OUT_DIR, "%s_00001-audio.mp4" % manifest[i - 1]["id"])
            if not os.path.exists(prev):
                log("!! 上一段缺失 %s，本段降级用 fixed 工作流" % prev)
                wf, prev = WF_FIXED, None

        log("=== 第 %d 段/%d  %s  [%s] ===" % (idx, len(manifest), prefix,
                                               "fixed" if wf == WF_FIXED else "chain"))
        ok = False
        for attempt in (1, 2):
            rc, dt, tail = run_seg(seg, wf, prev)
            if rc == 0 and os.path.exists(done):
                ok = True
                log("完成 %s  %.1f 分钟" % (prefix, dt / 60))
                break
            log("失败 %s attempt=%d rc=%d\n%s" % (prefix, attempt, rc, tail))
            if attempt == 1:
                log("…失败后重启 ComfyUI 重试")
                kill_comfyui()
                time.sleep(4)
                start_comfyui()
                if wf == WF_CHAIN and not os.path.exists(prev):
                    wf, prev = WF_FIXED, None
        state[prefix] = {"ok": ok, "workflow": "fixed" if wf == WF_FIXED else "chain"}
        json.dump(state, open(state_f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    log("=== 全部完成 ===")


if __name__ == "__main__":
    main()
