# -*- coding: utf-8 -*-
"""等片8跑完、队列清空后，杀掉旧 ComfyUI（12GB 内存），让下次启动用 --cache-none 新参数。"""
import json, os, subprocess, sys, time, urllib.request

for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(k, None)

PORT = 8189
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "watch_restart_comfy.log")
DRAFT_T08 = r"D:\output_h3off\draft\off_xs01_t08_00001.mp4"

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("[%H:%M:%S] ") + msg + "\n")

def queue_empty():
    try:
        q = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/queue" % PORT, timeout=5).read())
        return len(q.get("queue_running", [])) == 0 and len(q.get("queue_pending", [])) == 0
    except Exception:
        return True  # 连不上 = 已经死了

def kill_comfy():
    r = subprocess.run(["tasklist", "/fo", "csv"], capture_output=True)
    txt = r.stdout.decode("gbk", errors="replace")
    import csv, io
    killed = []
    for row in csv.reader(io.StringIO(txt)):
        if len(row) >= 2 and row[0].lower() == "python.exe":
            pid = row[1]
            try:
                wm = subprocess.run(
                    ["wmic", "process", "where", "ProcessId=%s" % pid, "get", "CommandLine", "/format:list"],
                    capture_output=True, timeout=10)
                line = wm.stdout.decode("gbk", errors="replace")
                if "main.py" in line and ("ComfyUI" in line):
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                    killed.append(pid)
            except Exception:
                pass
    return killed

def main():
    log("watch start: waiting for seg8 done + queue empty")
    # 第一步：等队列空（当前片8在跑）
    for _ in range(60 * 40):  # 最多等 40 分钟
        if queue_empty():
            break
        time.sleep(15)
    # 第二步：确认片8已落盘（或队列确实空了）
    t0 = time.time()
    while not os.path.exists(DRAFT_T08) and time.time() - t0 < 180:
        time.sleep(10)
    log("queue empty, seg8 file exists=%s" % os.path.exists(DRAFT_T08))
    time.sleep(20)  # 留缓冲给调度器结算
    # 第三步：再确认一次队列仍为空（防止调度器立刻提交了下一片）
    if not queue_empty():
        log("queue refilled, abort restart")
        return
    killed = kill_comfy()
    log("killed: %s ; next start will use --cache-none" % killed)

if __name__ == "__main__":
    main()
