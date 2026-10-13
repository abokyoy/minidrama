# -*- coding: utf-8 -*-
r"""
派生 A/B/C 三个 chain 变体工作流（2026-10-09）

原文件一个字都不动，三个变体各自另存。

★ 为什么会有这三个 ★
官方节点能力查证（E:\ComfyUI\ComfyUI_h3official\comfy_extras\nodes_minimax_h3.py）：
  MiniMaxH3ImageToVideo   first_frame = geometry anchor（plain stretch，几何锚）
                          last_frame  = follower（aspect-preserving cover-crop）
  MiniMaxH3AddGuide       任意帧锚定；frame_idx 负数 = 从末尾倒数
                          "Chain several nodes to anchor several frames"
  音视频轨与图像走同一个 frame_idx，共享一条时间轴
我们现在只用了 AddGuide 的 frame_idx=0（拿上一段尾帧当首帧），另外三个能力没用。

★ 三个变体各验一件事 ★
A 双端锚：头尾都锁。现有 chain 拿上一段**最后 22 帧**锚在本段 frame 0；
  变体 A 在本段末尾再加一个 AddGuide（frame_idx = 242，即最后一帧）
  锚住**下一段该长什么样**？——不，锚不住未来。
  → 正确定义：把上一段的**头 22 帧**也拿来锚本段尾部（frame_idx=-22 区域），
    让本段尾帧与上一段头帧呼应，形成闭环约束；实测是否比只锚头更稳/更僵。
  简化可测版本：**同时锚头 22 帧 + 单帧尾（frame_idx=242）**，单帧来自上一段首帧 PNG。
  这一版能直接回答："本段末帧被锁住后，衔接是否改善、是否变僵"。

B 音轨锚：VHS_LoadVideoPath 的 audio 输出口 → AddGuide 的 audio 输入，
  audio_vae 接节点 120（minimax_h3_audio_vae_fp32）。
  现状：每段环境音/台词音轨都从零重起 → 段间声音有断点。
  验："音轨延续能不能消掉断点"。

C 单帧几何锚：把 910 的 frame_load_cap 从 22 改成 1、skip_first_frames 改成 242。
  即只取上一段**最后一帧**这一张图来锚本段首帧，走的是 AddGuide 的 image 通道
  （center cover-crop），而不是 22 帧 clip。
  对照官方 first_frame 的 plain stretch：AddGuide 用 center，ImageToVideo 用 stretch。
  验："单帧锚 vs 22 帧 clip 锚，哪个衔接更好"。

★ 用法 ★
  python _mk_variants.py            # 只建文件，不生成
  python _chain.py 5 --kind=chain --wf=vA --force
"""
import os, json, io, shutil, copy

WF_DIR = r"E:\ComfyUI\ComfyUI_new\user\default\workflows"
SRC = os.path.join(WF_DIR, "04_ref2v_seg2_chain.json")

VARIANTS = {
    "vA": "04_ref2v_seg2_chain_vA_dualanchor.json",
    "vB": "04_ref2v_seg2_chain_vB_audio.json",
    "vC": "04_ref2v_seg2_chain_vC_singleframe.json",
}

VIDEO_NODE = 910     # VHS_LoadVideoPath
GUIDE_NODE = 911     # MiniMaxH3AddGuide（现有）
GUIDE2_ID = 913      # MiniMaxH3AddGuide（A 变体新增：锚本段末帧）
LOAD2_ID = 912       # LoadImage（A 变体新增：取上一段首帧 PNG）
AUDIO_VAE_NODE = 120 # VAELoader audio


def find_node(wf, nid):
    for n in wf["nodes"]:
        if n["id"] == nid:
            return n
    raise KeyError("节点 %s 不存在" % nid)


def next_link_id(wf):
    return max([lk[0] for lk in wf["links"]] or [0]) + 1


def add_link(wf, src, sslot, dst, dslot, typ):
    lid = next_link_id(wf)
    wf["links"].append([lid, src, sslot, dst, dslot, typ])
    for n in wf["nodes"]:
        if n["id"] == dst:
            for s in (n.get("inputs") or []):
                if s["name"] == dslot:
                    s["link"] = lid
        if n["id"] == src:
            for i, s in enumerate(n.get("outputs") or []):
                if i == sslot:
                    # ⛔ 未接线的输出口 links 是 None（不是 []），
                    #    setdefault 不会替换已存在的 None → add_link 直接崩在这。
                    if s.get("links") is None:
                        s["links"] = []
                    if lid not in s["links"]:
                        s["links"].append(lid)
    return lid


# ── A：双端锚 ──────────────────────────────────────────────
def make_vA(wf, head_ref_png):
    """本段首帧锚上一段尾 22 帧（保留）；本段末帧锚上一段**首帧** PNG（新增）。

    为什么要锚上一段的首帧：本段末帧 → 下一段首帧。
    下一段接的就是本段末帧。所以锁本段末帧 = 为下一段定死起点。
    参考物选「上一段首帧」是因为它是全片唯一一个 100% 干净的锚（没被任何 drift 污染），
    相当于给每一段都留一个回到基准的机会。
    """
    w = copy.deepcopy(wf)
    g = find_node(w, GUIDE_NODE)

    # 912: LoadImage —— 上一段首帧 PNG
    w["nodes"].append({
        "id": LOAD2_ID, "type": "LoadImage", "pos": [120, 700],
        "size": [340, 320], "flags": {}, "order": 30,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "IMAGE", "type": "IMAGE", "links": [], "slot_index": 0},
            {"name": "MASK", "type": "MASK", "links": [], "slot_index": 1},
        ],
        "properties": {"Node name for S&R": "LoadImage"},
        "widgets_values": [head_ref_png, "image"],
    })

    # 913: 第二个 AddGuide，锚本段末帧（frame_idx=242 = 243-1）
    w["nodes"].append({
        "id": GUIDE2_ID, "type": "MiniMaxH3AddGuide", "pos": [520, 700],
        "size": [300, 200], "flags": {}, "order": 31,
        "mode": 0,
        "inputs": [
            {"name": "positive", "type": "CONDITIONING", "link": None},
            {"name": "vae", "type": "VAE", "link": None},
            {"name": "audio_vae", "type": "VAE", "link": None},
            {"name": "latent", "type": "LATENT", "link": None},
            {"name": "image", "type": "IMAGE", "link": None},
            {"name": "audio", "type": "AUDIO", "link": None},
        ],
        "outputs": [
            {"name": "positive", "type": "CONDITIONING", "links": [], "slot_index": 0},
        ],
        "properties": {"Node name for S&R": "MiniMaxH3AddGuide"},
        "widgets_values": [242],
    })

    vae = find_node(w, AUDIO_VAE_NODE)
    video_vae = None
    for n in w["nodes"]:
        if n["id"] == 119:
            video_vae = n

    # 链路：911.positive → 913.positive；903.LATENT → 913.latent；
    #       119(视频VAE) → 913.vae；912.IMAGE → 913.image；913.positive → 126
    add_link(w, GUIDE_NODE, 0, GUIDE2_ID, "positive", "CONDITIONING")
    add_link(w, 119, 0, GUIDE2_ID, "vae", "VAE")
    add_link(w, 903, 1, GUIDE2_ID, "latent", "LATENT")
    add_link(w, LOAD2_ID, 0, GUIDE2_ID, "image", "IMAGE")

    # 126 BasicGuider 的 conditioning 原本接 911（link 44）→ 改接 913。
    # ⛔ 必须**删掉旧 link 44**，不是只把 input.link 置 None。
    #    留着 = 一条既不连源也不连目标的死链；ComfyUI 的 UI→API 转换
    #    （h3_driver.convert）会照它的(src,sslot)去 911 输出取 CONDITIONING，
    #    于是 911 的输出被白白分叉出去，911→126 这条链的语义就乱了。
    #    _wf_check.py 第4 项（孤儿/死链）就是为抓这个而写的。
    w["links"] = [lk for lk in w["links"] if lk[0] != 44]
    for n in w["nodes"]:
        if n["id"] == GUIDE_NODE:
            for s in n.get("outputs") or []:
                if s.get("links") and 44 in s["links"]:
                    s["links"].remove(44)
    for n in w["nodes"]:
        if n["id"] == 126:
            for s in n["inputs"]:
                if s["name"] == "conditioning":
                    s["link"] = None
    add_link(w, GUIDE2_ID, 0, 126, "conditioning", "CONDITIONING")

    w["last_node_id"] = max(w.get("last_node_id", 0), GUIDE2_ID)
    return w


# ── B：音轨锚 ──────────────────────────────────────────────
def make_vB(wf):
    """VHS_LoadVideoPath 的 audio 输出口 → AddGuide 的 audio 输入。
    audio_vae 接 120（minimax_h3_audio_vae_fp32）。
    910 的 audio 输出 slot 索引 = 2（IMAGE=0, frame_count=1, audio=2, video_info=3）。
    911 的 audio 输入 slot 名 = 'audio'。
    """
    w = copy.deepcopy(wf)
    v = find_node(w, VIDEO_NODE)
    # 确认 audio 是第几个输出
    outs = [o["name"] for o in (v.get("outputs") or [])]
    if "audio" not in outs:
        raise SystemExit("910 没有 audio 输出口，实际是：%s" % outs)
    aidx = outs.index("audio")
    add_link(w, VIDEO_NODE, aidx, GUIDE_NODE, "audio", "AUDIO")
    add_link(w, AUDIO_VAE_NODE, 0, GUIDE_NODE, "audio_vae", "VAE")
    return w


# ── C：最小锚帧 ────────────────────────────────────────────
def make_vC(wf):
    """只取上一段最后 **5 帧**锚本段首帧，而不是 22 帧 clip。

    ⛔⛔ 第一版写的是 frame_load_cap=1，实测直接报错（本机踩坑，务必记住）：
        RuntimeError: stack expects a non-empty TensorList
        节点 911 MiniMaxH3AddGuide → _resize(image[:1], ...)
    根因在 VHS_LoadVideoPath：format="H3" 时会做帧数对齐（load_video_nodes.py
    line 388），H3 的 frames 规则是 (17,5)，即要求 帧数 % 17 == 5：
        frames = (len(images) - 5) // 17 * 17 + 5
        images = images[:frames]
    cap=1 → (1-5)//17*17+5 = -4 → images 被截成空列表 →下游 stack 炸。
    ⚠️ 所以 **合法锚帧长度只有 5 / 22 / 39…**（17k+5），
       **最小是 5 帧，不存在"单帧锚"**。
    → cap=5, skip = 243-5 = 238。

    ⚠️ h3_driver.py 在 chain 分支里会强制改写 skip_first_frames=221，
       所以 driver 必须同步支持 prev_cap / prev_skip 覆盖（已加）。
    """
    w = copy.deepcopy(wf)
    v = find_node(w, VIDEO_NODE)
    wv = v.get("widgets_values")
    if isinstance(wv, dict):
        wv["frame_load_cap"] = 5
        wv["skip_first_frames"] = 238
    else:
        raise SystemExit("910 widgets_values 是 list，需要按位置改，请先核对")
    return w


def main():
    print("源工作流:", SRC)
    wf = json.load(io.open(SRC, encoding="utf-8"))
    head = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "xs001_segs", "_head_ref.png")
    print("上一段首帧参考图(912 用):", head, "存在" if os.path.exists(head) else "★缺")

    built = {}
    try:
        built["vA"] = make_vA(wf, os.path.basename(head))
    except Exception as e:
        print("!! vA 失败:", e)
    try:
        built["vB"] = make_vB(wf)
    except Exception as e:
        print("!! vB 失败:", e)
    try:
        built["vC"] = make_vC(wf)
    except Exception as e:
        print("!! vC 失败:", e)

    for k, w in built.items():
        out = os.path.join(WF_DIR, VARIANTS[k])
        json.dump(w, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  建好 %-4s -> %s  (nodes=%d links=%d)"
              % (k, os.path.basename(out), len(w["nodes"]), len(w["links"])))

    # 逐个打印校验点
    print("\n--- 校验点 ---")
    if "vA" in built:
        w = built["vA"]
        g2 = find_node(w, GUIDE2_ID)
        conds = [(s["name"], s["link"]) for s in g2["inputs"]]
        print("vA 913 frame_idx =", g2["widgets_values"])
        print("vA 913 inputs   =", conds)
        gd = find_node(w, 126)
        print("vA 126 conditioning link =",
              [s["link"] for s in gd["inputs"] if s["name"] == "conditioning"])
    if "vB" in built:
        w = built["vB"]
        g = find_node(w, GUIDE_NODE)
        print("vB 911 inputs   =", [(s["name"], s["link"]) for s in g["inputs"]])
    if "vC" in built:
        w = built["vC"]
        v = find_node(w, VIDEO_NODE)
        print("vC 910 widgets  =", v["widgets_values"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())