# -*- coding: utf-8 -*-
"""
MiniMax H3 ref2v 生成驱动（《第一百三十八个名字》短剧流水线）
用途：
  python h3_driver.py <job.json>
  job.json:
  {
    "workflow": "E:\\...\\04_ref2v_4step_sla_ganloss_fixed.json",
    "prompt_file": "E:\\...\\seg01_prompt.txt",
    "out_prefix": "ep01_s01",
    "refs": ["char_suxiaoman.png", "sc_corridor_pano.png", ...],   # 最多 6 张，按槽位顺序
    "prev_video": "D:\\output\\ep01_s01_00001.mp4" | null,          # 仅 chain 工作流用
    "prev_skip": 221
  }
输出：ComfyUI 直接写 D:\\output（启动参数 --output-directory "D:\\output"）
"""
import sys, os, json, time, urllib.request, urllib.parse, urllib.error

# 本机环境变量里的代理指向 WorkBuddy 内部代理，访问 127.0.0.1 会被它 502 掉，必须先清掉
for _k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_k, None)
os.environ["no_proxy"] = "127.0.0.1,localhost"
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

# ⭐ 端口可切换（2026-10-06）：老实例 8188，新建的「H3 官方原版」实例 8189。
#    用环境变量 MINIDRAMA_PORT 切，不改代码。默认 8188 = 老环境，行为完全不变。
SERVER = "http://127.0.0.1:%s" % os.environ.get("MINIDRAMA_PORT", "8188")
REF_NODE_IDS = [901, 904, 905, 906, 907, 908]     # REF IMAGE 1..6（902/903 是 VideoCombine / H3 节点，绝不能当图片槽）
PROMPT_NODE = "1"
OUT_NODE = "902"
CHAIN_VIDEO_NODE = "910"
CHAIN_GUIDE_NODE = "911"
TOTAL_FRAMES = 243          # 10s @24fps 经 ComfyMathExpression 取整后的实际帧数
TAIL_FRAMES = 22            # chain 工作流取上一段最后 22 帧做锚定
DEFAULT_PREV_SKIP = TOTAL_FRAMES - TAIL_FRAMES   # 221

# 画质档位文件（_quality.py 写入）。没有就返回空 dict → 沿用默认参数。
QUALITY_PROFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "_quality_profile.json")


def _load_quality_profile():
    """读画质档位。读不到/损坏都返回 {}，绝不因为档位问题让生成挂掉。"""
    try:
        if os.path.exists(QUALITY_PROFILE):
            with open(QUALITY_PROFILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print("QUALITY 档位读取失败（忽略，用默认参数）：%s" % str(e)[:120])
    return {}


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a)


def http_get(path, timeout=60):
    with urllib.request.urlopen(SERVER + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def http_post(path, data, timeout=120):
    req = urllib.request.Request(
        SERVER + path,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        log("HTTP", e.code, "BODY:", body[:3000])
        raise


def upload_image(path):
    boundary = "----agentboundary7MA4YWxkTrZu0gW"
    filename = os.path.basename(path)
    with open(path, "rb") as f:
        data = f.read()
    body = (
        "--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
        "Content-Type: image/png\r\n\r\n" % (boundary, filename)
    ).encode("utf-8") + data + ("\r\n--%s--\r\n" % boundary).encode("utf-8")
    req = urllib.request.Request(
        SERVER + "/upload/image",
        data=body,
        headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def build_link_map(wf):
    return {lk[0]: (lk[1], lk[2]) for lk in wf["links"]}


def convert(wf, obj):
    linkmap = build_link_map(wf)
    api = {}
    for n in wf["nodes"]:
        nid = str(n["id"])
        ct = n["type"]
        conns = {}
        for slot in (n.get("inputs") or []):
            lk = slot.get("link")
            if lk is not None and lk in linkmap:
                s, ss = linkmap[lk]
                conns[slot["name"]] = [str(s), ss]
        wv = n.get("widgets_values")
        inp = {}
        if isinstance(wv, dict):
            for k, v in wv.items():
                if k != "videopreview":
                    inp[k] = v
        else:
            wv = list(wv or [])
            flat = [x for x in wv if not (isinstance(x, dict) and ("videopreview" in x or "params" in x))]
            try:
                info = obj[ct]["input"]
            except KeyError:
                info = {}
            PRIM = {"INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"}
            wnames = []
            for grp in ("required", "optional"):
                for k, v in (info.get(grp) or {}).items():
                    if k in conns:
                        continue
                    t = v[0] if isinstance(v, list) else v
                    if isinstance(t, list) or t in PRIM:
                        wnames.append(k)
            for i, name in enumerate(wnames):
                if i < len(flat):
                    inp[name] = flat[i]
        inp.update(conns)
        api[nid] = {"class_type": ct, "inputs": inp}
    return api


def main(deep_queue_submit=False, deep_queue_wait=None):
    # ⛔ 深排队模式用 `--qjob=<a.json>` 传job，不能让 sys.argv[1] 顶掉
    if deep_queue_wait:
        wait_pid(deep_queue_wait)
        return
    jp = sys.argv[1]
    for a in sys.argv[1:]:
        if a.startswith("--qjob="):
            jp = a.split("=", 1)[1]
    job = json.load(open(jp, "r", encoding="utf-8"))
    wf = json.load(open(job["workflow"], "r", encoding="utf-8"))
    obj = http_get("/object_info")
    api = convert(wf, obj)

    prompt_text = open(job["prompt_file"], "r", encoding="utf-8").read()
    api[PROMPT_NODE]["inputs"]["value"] = prompt_text

    refs = job.get("refs") or []
    if len(refs) > 6:
        raise SystemExit("refs 最多 6 张")

    # ⛔ stage_refs() 返回的是**裸文件名**（r01_ref1__<md5>.png），
    #    图实际落在 ComfyUI 自己的 input/ 目录里（2026-10-08 修）。
    #    之前靠 job["ref_dir"] 指向 input 目录才能工作；
    #    测试任务（修仙换装）的 job 里 ref_dir 是**源目录**（assets_face/），
    #    在这里拼出的是源目录 → FileNotFoundError。
    # → 先去 ComfyUI input 目录找，找不到再退回 ref_dir。
    inp = os.path.join(os.environ.get("MINIDRAMA_COMFY_DIR", ""), "input") \
        if os.environ.get("MINIDRAMA_COMFY_DIR") else None
    cands = []
    if inp and os.path.isdir(inp):
        cands.append(inp)
    cands.append(job.get("ref_dir") or "")

    for r in refs:
        if os.path.isabs(r) and os.path.exists(r):
            p = r
        else:
            p = None
            for d in cands:
                if not d:
                    continue
                q = os.path.join(d, r)
                if os.path.exists(q):
                    p = q
                    break
            if p is None:
                p = os.path.join(job["ref_dir"], r)
        if not os.path.exists(p):
            raise SystemExit("参考图找不到: %s（找过 %s）"
                             % (r, " | ".join(x for x in cands if x)))
        upload_image(p)
    # 删掉多余的 LoadImage 之后，H3 节点（903）里指向它们的
    # `ref_images.ref_image_N` 键也必须一起删，否则会引用不存在的节点 → 校验失败。
    if "903" in api:
        ri = api["903"].get("inputs", {})
        for i, nid in enumerate(REF_NODE_IDS):
            if i >= len(refs):
                ri.pop("ref_images.ref_image_%d" % i, None)

    for i, nid in enumerate(REF_NODE_IDS):
        if i < len(refs):
            api[str(nid)]["inputs"]["image"] = os.path.basename(refs[i])
        else:
            # ⚠️ 必须把多余的参考图节点**整个删掉**（2026-10-06 踩坑）。
            # 工作流 901/904..908 六个 LoadImage 默认都填着
            # "workbuddy_placeholder_ref.png"，而 ComfyUI 收到 prompt 时会
            # **先校验所有节点**（含没接输出的）——占位图文件不存在 →
            # `Invalid image file` → 整份 prompt 被拒（HTTP 400），
            # 哪怕前几张都有真实图。t01 只有 4 张图，905-908 就是这种情况。
            # 老集一直没人踩到，是因为 manifest 里恰好每段都 6 张图。
            # ⚠️ 试过置空字符串**不行**，`exists_annotated_filepath("")`
            #    同样返回 False → 还是报 Invalid image file。只能删节点。
            api.pop(str(nid), None)

    if "903" in api:
        api["903"]["inputs"]["ref_image_size"] = "match"

    # ── guide_images：A/B/C 变体用来给额外 LoadImage 节点喂图（2026-10-09）──
    # A 变体的 912 节点是 LoadImage（取上一段首帧 PNG 当末帧锚），
    # 但 refs 只往 901/904..908 六个固定槽位塞，塞不进去 → 必须单独上传+改节点。
    # ⛔ 漏了这一步：文件没进 ComfyUI 的 input/ → 报 Invalid image file → HTTP 400。
    for gi in (job.get("guide_images") or []):
        nid = str(gi["node"])
        src = gi["file"]
        p = src if (os.path.isabs(src) and os.path.exists(src)) else None
        if p is None:
            for d in cands:
                if d and os.path.exists(os.path.join(d, src)):
                    p = os.path.join(d, src)
                    break
        if p is None:
            raise SystemExit("guide_images 文件找不到: %s" % src)
        up = upload_image(p)
        name = (up or {}).get("name") or os.path.basename(p)
        if nid not in api:
            raise SystemExit("guide_images 指向的节点 %s 不在工作流里" % nid)
        api[nid]["inputs"]["image"] = name
        print("GUIDE  node %s <- %s" % (nid, name))

    # ── 画质档位（2026-10-04 新增，见 _quality.py）─────────────────
    # 之前这里把 steps/scheduler/ref_image_size 全部硬编码，
    # 导致"换参数试画质"必须改代码。改成读档位：
    #   python _quality.py apply deep   # 切档并写 profile
    # 档位里没有的项沿用上面的默认值。
    prof = _load_quality_profile()
    # ⛔⛔⛔ 2026-10-10 用户提出「先低分辨率预出片验一遍，对了再升高清」。
    #   档位是**全局文件**读的 → 切一次档会同时影响所有片（两实例抢跑就乱）。
    # → job 里可以带 `quality`：带了就用它那份档位，不带才用全局。
    #   这样「第1片在预出片、第2片在出终版」可以同时跑，互不干扰。
    ov = job.get("quality")
    if ov:
        try:
            import _quality as _Q
            if ov not in _Q.PROFILES:
                print("‼ 未知档位 %r，沿用全局档 %r"
                      % (ov, prof.get("name")))
            else:
                prof = {"name": ov, "p": dict(_Q.PROFILES[ov]["p"])}
                print("QUALITY-OVERRIDE 采用 job 指定档：%s" % ov)
        except Exception as e:
            print("‼ 档位覆盖失败（沿用全局）：%r" % e)
    p = prof.get("p", {})
    sched_node = next((k for k, v in api.items()
                       if isinstance(v, dict) and v.get("class_type") == "BasicScheduler"), None)
    if sched_node and p.get("steps"):
        api[sched_node]["inputs"]["steps"] = int(p["steps"])
    if sched_node and p.get("sch"):
        api[sched_node]["inputs"]["scheduler"] = p["sch"]
    samp_node = next((k for k, v in api.items()
                      if isinstance(v, dict) and v.get("class_type") == "KSamplerSelect"), None)
    if samp_node and p.get("smp"):
        api[samp_node]["inputs"]["sampler_name"] = p["smp"]
    if "903" in api and p.get("ref"):
        api["903"]["inputs"]["ref_image_size"] = p["ref"]
    sla_node = next((k for k, v in api.items()
                     if isinstance(v, dict) and v.get("class_type") == "H3SLAAttention"), None)
    if sla_node:
        for key, field in (("dlast", "dense_last_steps"), ("refprot", "reference_protection"),
                           ("tail", "tail_correction"), ("stabilize", "stabilize_motion")):
            if p.get(key) is not None:
                api[sla_node]["inputs"][field] = (
                    bool(p[key]) if isinstance(p[key], bool) else p[key])
    if p:
        print("QUALITY profile=%s steps=%s ref=%s dlast=%s refprot=%s tail=%s"
              % (prof.get("name", "safe"), p.get("steps"), p.get("ref"),
                 p.get("dlast"), p.get("refprot"), p.get("tail")))

    # ── 换模型 / 挂 LoRA（2026-10-06 新增，官方 turbo 档用）──────────────
    # ⚠️ 老档位不带这两个键 → 完全不执行 → 老集api 一字不变，sha 不变。
    unet_node = next((k for k, v in api.items()
                      if isinstance(v, dict) and v.get("class_type") == "UNETLoader"), None)
    if p.get("unet"):
        if not unet_node:
            raise SystemExit("档位指定了 unet，但工作流里没有 UNETLoader")
        old = api[unet_node]["inputs"]["unet_name"]
        api[unet_node]["inputs"]["unet_name"] = p["unet"]
        if old != p["unet"]:
            print("MODEL  %s -> %s" % (old, p["unet"]))
    if p.get("vae"):
        vae_node = next((k for k, v in api.items()
                         if isinstance(v, dict) and v.get("class_type") == "VAELoader"
                         and "video" in str(v["inputs"].get("vae_name", ""))), None)
        if vae_node is None:
            # 兜底：取第一个名字里带 video 的
            for k, v in api.items():
                if isinstance(v, dict) and v.get("class_type") == "VAELoader" \
                        and "video" in str(v["inputs"].get("vae_name", "")):
                    vae_node = k
                    break
        if vae_node:
            oldv = api[vae_node]["inputs"]["vae_name"]
            api[vae_node]["inputs"]["vae_name"] = p["vae"]
            if oldv != p["vae"]:
                print("VAE    %s -> %s" % (oldv, p["vae"]))

    if p.get("lora"):
        # LoraLoaderModelOnly 必须插在 UNETLoader 之后、SLA/H3 之前：
        # 模型链是 UNETLoader(127) -> H3SLAAttention(900) -> MiniMaxH3SigmaShift(142) -> BasicScheduler(124)
        if unet_node is None:
            raise SystemExit("档位指定了 lora，但工作流里没有 UNETLoader")
        lora_id = "990"          # 独立 id，不与任何现有节点冲突
        api[lora_id] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": [unet_node, 0],
                "lora_name": p["lora"],
                "strength_model": float(p.get("lora_s", 1.0)),
            },
        }
        # 把原先指向 UNETLoader 的 MODEL 输入改指到 LoRA
        rewired = []
        for k, v in api.items():
            if not isinstance(v, dict) or k == lora_id:
                continue
            ins = v.get("inputs", {})
            for slot, val in list(ins.items()):
                if isinstance(val, list) and len(val) == 2 and val[0] == unet_node \
                        and v.get("class_type") in ("H3SLAAttention", "MiniMaxH3SigmaShift",
                                                    "BasicScheduler", "SamplerCustomAdvanced",
                                                    "BasicGuider", "LoraLoaderModelOnly"):
                    ins[slot] = [lora_id, 0]
                    rewired.append("%s.%s" % (k, slot))
        print("LORA   %s (strength=%s) 插入于 %s 之后，重连: %s"
              % (p["lora"], p.get("lora_s", 1.0), unet_node, ", ".join(rewired)))

    # ⛔ 2026-10-09 用户改需求：**4:3 横屏**（原来是 9:16 竖屏）。
    #    ResolutionSelector 的合法选项见 comfy_extras/nodes_resolution.py 的 AspectRatio 枚举：
    #      "1:1 (Square)" / "2:3 (Portrait Photo)" / "3:2 (Photo)" /
    #      "3:4 (Portrait Standard)" / "4:3 (Standard)" / "9:16 (Portrait Widescreen)" /
    #      "16:9 (Widescreen)" / "21:9 (Ultrawide)"
    #    ⚠️ 写错字符串会 400（它是 Combo，不是自由文本）。
    #    ⛔ 画幅变了，提示词里那句 "VERTICAL 9:16 portrait framing" 必须同步改，
    #       否则模型按提示词拉竖构图、画幅参数却被设成横 → 构图与画幅打架。
    res_node = job.get("resolution_node", "115")
    if res_node in api:
        api[res_node]["inputs"]["aspect_ratio"] = job.get("aspect_ratio", "4:3 (Standard)")
        if "megapixels" in api[res_node]["inputs"]:
            api[res_node]["inputs"]["megapixels"] = float(job.get("megapixels", 0.75))
        print("SIZEaspect=%s mp=%s"
              % (api[res_node]["inputs"]["aspect_ratio"],
                 api[res_node]["inputs"].get("megapixels")))

    api[OUT_NODE]["inputs"]["filename_prefix"] = job["out_prefix"]

    prev = job.get("prev_video")
    if prev:
        api[CHAIN_VIDEO_NODE]["inputs"]["video"] = prev
        api[CHAIN_VIDEO_NODE]["inputs"]["skip_first_frames"] = int(
            job.get("prev_skip", DEFAULT_PREV_SKIP)
        )
        # ⛔ 2026-10-09 新增：C 变体（单帧几何锚）要把 frame_load_cap 从 22 改成 1。
        #    不加这个开关时 driver 会沿用工作流里的 22 → 实际跑的还是 22 帧 clip 锚，
        #    「C 变体」名存实亡。job 里给了 prev_cap 才覆盖。
        if job.get("prev_cap") is not None:
            api[CHAIN_VIDEO_NODE]["inputs"]["frame_load_cap"] = int(job["prev_cap"])
        print("CHAIN  video=%s skip=%s cap=%s frame_idx=%s"
              % (os.path.basename(prev),
                 api[CHAIN_VIDEO_NODE]["inputs"]["skip_first_frames"],
                 api[CHAIN_VIDEO_NODE]["inputs"].get("frame_load_cap"),
                 (api.get(CHAIN_GUIDE_NODE) or {}).get("inputs", {}).get("frame_idx")))

    dbg = os.path.join(os.path.dirname(job["prompt_file"]), "_last_api.json")
    json.dump(api, open(dbg, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    pid = http_post("/prompt", {"prompt": api, "client_id": "autopilot"})["prompt_id"]
    log("SUBMITTED", pid, job["out_prefix"])

    # ── ⭐⭐⭐ 最高原则：显卡永远不许空转 ──
    # 深排队模式：只提交、不等待。调用方在上一段还在采样时就把它排进来，
    # GPU 上一段一结束自动接上，段间零空转。
    # ⛔ 提交进队列不占显存；抢显存的是「两实例同时采样」，那个仍然禁止。
    if deep_queue_submit:
        print("PROMPT_ID=" + pid)
        print("SAVED []")
        return

    t0 = time.time()
    wait_pid(pid)


def wait_pid(pid, timeout=3600):
    """轮询等一个已提交的任务完成（深排队模式下 pid 是提前排进去的）。"""
    t0 = time.time()
    while True:
        time.sleep(5)
        if time.time() - t0 > timeout:
            log("TIMEOUT waiting", pid)
            raise SystemExit(3)
        try:
            h = http_get("/history/" + pid)
        except Exception as e:
            log("poll err", e)
            continue
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("status_str") == "error":
                log("GEN_ERROR", json.dumps(st, ensure_ascii=False)[:2000])
                raise SystemExit(2)
            if st.get("completed"):
                outs = h[pid].get("outputs", {})
                saved = []
                for nid, o in outs.items():
                    for vk, vlist in o.items():
                        if isinstance(vlist, list):
                            for it in vlist:
                                if isinstance(it, dict) and it.get("filename"):
                                    saved.append(os.path.join(
                                        os.environ.get("MINIDRAMA_OUT", r"D:\output"),
                                        it.get("subfolder", ""), it["filename"]))
                log("DONE %.1fs" % (time.time() - t0), json.dumps(saved, ensure_ascii=False))
                print("SAVED " + json.dumps(saved))
                return


if __name__ == "__main__":
    # ── ⭐⭐⭐ 深度排队模式（2026-10-09 最高原则：显卡永远不许空转）──────
    # 用法：h3_driver.py --qjob=<a.json> --qsubmit
    #   --qsubmit：只 POST /prompt 进队列，打印 PROMPT_ID=<pid> 后**立刻返回**，
    #              不等结果。让调用方在上一段还在采样时就把下一段排进队列，
    #              GPU 上一段一结束就自动接上，中间零空转。
    #              ⛔ 提交进队列不占显存；真正抢显存的是「两实例同时采样」，仍禁止。
    #   --qwait=<pid>：轮询等某个已提交的任务完成。
    _a = sys.argv[1:] if len(sys.argv) > 1 else []
    if _a and any(x.startswith("--qjob=") for x in _a):
        _jp = [x.split("=", 1)[1] for x in _a if x.startswith("--qjob=")][0]
        _submit = "--qsubmit" in _a
        _waitpid = None
        for x in _a:
            if x.startswith("--qwait="):
                _waitpid = x.split("=", 1)[1]
        os.environ["MINIDRAMA_DEEPQ"] = "1"
        main(deep_queue_submit=_submit, deep_queue_wait=_waitpid)
        sys.exit(0)
    main()
