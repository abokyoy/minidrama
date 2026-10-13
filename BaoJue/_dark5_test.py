# -*- coding: utf-8 -*-
"""5连黑实测（用户 2026-10-11 要求）：
「是否真的存在 多次连续接片会越来越黑 —— 连接5个视频 然后查看第5个视频光线是否和前面的比黑很多」
方法：连续 5 次 chain 续接同一个种子视频，每段出片后测平均亮度，对比衰减曲线。
跑法：等当前片1队列空闲后执行。用已有成片当种子（比如片1新出片）。
"""
import json, os, subprocess, sys, time, urllib.request

for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(k, None)

PORT = 8189
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"D:\output_h3off"
PY = r"C:/Users/86134/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
WF_CHAIN = r"E:\ComfyUI\ComfyUI_new\user\default\workflows\04_ref2v_seg2_chain.json"
RESULT = os.path.join(HERE, "xs001_segs", "_dark5_result.json")

def queue_busy():
    try:
        q = json.loads(urllib.request.urlopen(
            "http://127.0.0.1:%d/queue" % PORT, timeout=5).read())
        return len(q.get("queue_running", [])) + len(q.get("queue_pending", [])) > 0
    except Exception:
        return False

def wait_idle(timeout_s=7200):
    t0 = time.time()
    while queue_busy():
        if time.time() - t0 > timeout_s:
            raise SystemExit("等队列空闲超时")
        time.sleep(30)

def luma_of(mp4):
    """平均亮度：抽帧算均值。复用 _dup_check 的抽帧习惯但独立实现，拷到 ASCII 目录。"""
    tmp = r"C:\luma_tmp"
    os.makedirs(tmp, exist_ok=True)
    ff = os.path.join(tmp, "f.jpg")
    if os.path.exists(ff):
        os.remove(ff)
    r = subprocess.run(["ffmpeg", "-y", "-i", mp4, "-vframes", "1", "-vf",
                        "select=eq(n\\,48)", ff], capture_output=True)
    if not os.path.exists(ff):
        r = subprocess.run(["ffmpeg", "-y", "-i", mp4, "-vframes", "1", ff],
                           capture_output=True)
    if not os.path.exists(ff):
        return None
    r2 = subprocess.run([PY, "-c",
        "from PIL import Image;import sys;"
        "im=Image.open(r'%s').convert('L');"
        "px=list(im.getdata());print(round(sum(px)/len(px),1))" % ff],
        capture_output=True, text=True)
    try:
        return float(r2.stdout.strip())
    except ValueError:
        return None

def newest_mp4(prefix="dark5"):
    cands = []
    for d in (OUT, os.path.join(OUT, "off_draft"), os.path.join(OUT, "draft")):
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.startswith(prefix) and f.endswith("-audio.mp4"):
                    cands.append((os.path.getmtime(os.path.join(d, f)),
                                  os.path.join(d, f)))
    return max(cands)[1] if cands else None

def submit_chain(prev, out_prefix):
    """driver 用 job.json 传参（不支持 CLI 参数）。造 job → 调 driver。"""
    import io as _io
    job = {
        "workflow": WF_CHAIN,
        "prompt_file": os.path.join(HERE, "xs001_segs", "_dark5_prompt.txt"),
        "refs": [],
        "ref_dir": "",
        "prev_video": prev,
        "out_prefix": out_prefix,
        "quality": "preview25",
        "stage": "preview",
    }
    jf = os.path.join(HERE, "xs001_segs", "_dark5_job.json")
    with _io.open(jf, "w", encoding="utf-8") as f:
        f.write(json.dumps(job, ensure_ascii=False, indent=1))
    env = dict(os.environ)
    # driver 从 MINIDRAMA_COMFY_DIR/input 找参考图和 prev_video 相关文件；
    # chain 工作流不需要参考图，但保持与 _run_one 一致的环境。
    env["MINIDRAMA_COMFY_DIR"] = r"E:\ComfyUI\ComfyUI_h3official"
    return subprocess.run([PY, os.path.join(HERE, "h3_driver.py"), jf],
                          capture_output=True, text=True, timeout=2400, env=env)

def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else None
    if not seed or not os.path.exists(seed):
        raise SystemExit("用法: _dark5_test.py <种子视频绝对路径>")
    results = [{"seg": 0, "file": seed, "luma": luma_of(seed)}]
    print("seed luma:", results[0]["luma"], seed)

    prev = seed
    for i in range(1, 6):
        wait_idle()
        out = submit_chain(prev, "off_dark5_%02d" % i)
        # 等落盘
        time.sleep(15)
        f = newest_mp4("off_dark5_%02d" % i)
        if not f:
            print("seg%d: 未找到输出！" % i, out.stdout[-400:], out.stderr[-200:])
            break
        lm = luma_of(f)
        results.append({"seg": i, "file": f, "luma": lm})
        print("seg%d luma: %s  %s" % (i, lm, f))
        prev = f
    with open(RESULT, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1)
    print("=== 亮度衰减曲线 ===")
    for r in results:
        print("seg%d: %s" % (r["seg"], r["luma"]))

if __name__ == "__main__":
    main()
