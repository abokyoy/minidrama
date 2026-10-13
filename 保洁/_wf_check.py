# -*- coding: utf-8 -*-
r"""静态校验三套变体工作流的 link 拓扑（不提交、不烧显存）。

为什么需要：vC 第一次跑才发现 cap=1 报错，那是**跑完27 分钟才炸**。
同样的错如果在 A/B 里也有，跑第二遍、第三遍才发现就太贵了。
→ 变体建完先过这一关：每条 link 的两端 slot 必须真的存在、真的登记了。

检查项：
  1. link 的 src/slot 落在源节点 outputs 范围内
  2. link_id 同时登记在源节点 outputs[sslot].links
  3. link_id 登记在目标节点某个 input.link
  4. 所有 input.link（非 None）都存在于 links 集合里（无孤儿）
  5. AddGuide 节点的 frame_idx 不越界（-1 视为末帧）
  6. AddGuide 若接了 audio 则必须接 audio_vae
  7. 910 的 frame_load_cap 必须是 17k+5（否则 VHS 会截成空列表）
"""
import os, json, io, sys

WF_DIR = r"E:\ComfyUI\ComfyUI_new\user\default\workflows"
FILES = [
    "04_ref2v_seg2_chain.json",
    "04_ref2v_seg2_chain_vA_dualanchor.json",
    "04_ref2v_seg2_chain_vB_audio.json",
    "04_ref2v_seg2_chain_vC_singleframe.json",
]
TOTAL_FRAMES = 243
LEGAL_ANCHOR = [5, 22, 39, 56, 73, 90, 107, 124, 141, 158, 175, 192, 209,
                226, 243]


def check(path):
    errs, warns = [], []
    d = json.load(io.open(path, encoding="utf-8"))
    nodes = {n["id"]: n for n in d["nodes"]}
    used = set()

    for lk in d["links"]:
        lid, src, ss, dst, ds, typ = lk
        used.add(lid)
        sn = nodes.get(src)
        dn = nodes.get(dst)
        if sn is None:
            errs.append("link%d 源节点 %s 不存在" % (lid, src)); continue
        if dn is None:
            errs.append("link%d 目标节点 %s 不存在" % (lid, dst)); continue
        so = sn.get("outputs") or []
        if ss >= len(so):
            errs.append("link%d 源 slot %d 越界（节点%s只有%d个输出）"
                        % (lid, ss, src, len(so))); continue
        if lid not in (so[ss].get("links") or []):
            errs.append("link%d 未登记在节点%s输出slot%d的links里" % (lid, src, ss))
        hit = False
        for s in dn.get("inputs") or []:
            if s.get("link") == lid:
                hit = True; break
        if not hit:
            errs.append("link%d 未登记在节点%s的任何input上" % (lid, dst))

    for n in d["nodes"]:
        for s in n.get("inputs") or []:
            l = s.get("link")
            if l is not None and l not in used:
                errs.append("节点%s 的input %s 指向不存在的link %s"
                            % (n["id"], s["name"], l))

    # AddGuide 专项
    for n in d["nodes"]:
        if n["type"] != "MiniMaxH3AddGuide":
            continue
        wv = n.get("widgets_values")
        fi = wv[0] if isinstance(wv, list) and wv else None
        ins = {s["name"]: s.get("link") for s in (n.get("inputs") or [])}
        if fi is None:
            errs.append("节点%s AddGuide 没有 frame_idx" % n["id"])
        else:
            res = fi if fi >= 0 else TOTAL_FRAMES + fi
            if res < 0 or res >= TOTAL_FRAMES:
                errs.append("节点%s frame_idx=%s → 解析成第%s帧，超出0..%d"
                            % (n["id"], fi, res, TOTAL_FRAMES - 1))
        # 末帧锚是否越界，取决于**实际 guide 帧数**：
        # guide 帧数由喂进来的 image 批量决定（<5 → 1；≥5 → 往 17k+5 收）。
        # LoadImage 只出 1 张 → guide_frames=1 → 锚在末帧合法。
        # VHS_LoadVideoPath 出 17k+5 的 clip（22 帧）→ 末帧放不下 → 会抛异常。
        guide_frames = 1
        if ins.get("image") is not None:
            for lk in d["links"]:
                if lk[3] == n["id"] and lk[5] == "IMAGE":
                    sn2 = nodes.get(lk[1])
                    if sn2 is not None and sn2["type"] == "VHS_LoadVideoPath":
                        cap = (sn2.get("widgets_values") or {}).get("frame_load_cap")
                        if isinstance(cap, int) and cap >= 5:
                            guide_frames = max((cap - 5) // 17 * 17 + 5, 5)
        if fi is not None and fi >= 0 and TOTAL_FRAMES - fi < guide_frames:
            errs.append("节点%s 的 %d 帧 guide clip 锚在第%s帧 → "
                        "%d+%d>%d，官方会抛 'does not fit in the video'"
                        % (n["id"], guide_frames, fi, fi, guide_frames, TOTAL_FRAMES))
        elif fi is not None and fi >= 0 and TOTAL_FRAMES - fi < 5:
            warns.append("节点%s 锚在第%s帧（离末帧不足 5 帧）" % (n["id"], fi))
        if ins.get("audio") is not None and ins.get("audio_vae") is None:
            errs.append("节点%s 接了 audio 但没接 audio_vae（官方会抛异常）" % n["id"])
        if ins.get("image") is None and ins.get("audio") is None:
            errs.append("节点%s 既没 image 也没 audio（官方会抛异常）" % n["id"])

    # 910 帧数栅格
    for n in d["nodes"]:
        if n["type"] != "VHS_LoadVideoPath":
            continue
        wv = n.get("widgets_values") or {}
        cap = wv.get("frame_load_cap")
        if isinstance(cap, int) and cap != 0:
            trunc = (cap - 5) // 17 * 17 + 5
            if trunc < 5:
                errs.append("910 frame_load_cap=%d → VHS 按17k+5 截断成 %d 帧"
                            "（空列表 → stack 报错）。最小合法锚帧是 5" % (cap, trunc))
            elif trunc != cap:
                warns.append("910 cap=%d 会被截成 %d 帧" % (cap, trunc))
    return errs, warns


def main():
    bad = 0
    for f in FILES:
        p = os.path.join(WF_DIR, f)
        if not os.path.exists(p):
            print("跳过（不存在）", f); continue
        errs, warns = check(p)
        tag = "OK " if not errs else "FAIL"
        print("[%s] %-46s nodes=%-3d links=%-3d 错%d 警告%d"
              % (tag, f, len(json.load(io.open(p, encoding="utf-8"))["nodes"]),
                 len(json.load(io.open(p, encoding="utf-8"))["links"]),
                 len(errs), len(warns)))
        for e in errs:
            print("      x", e)
        for w in warns:
            print("      ! ", w)
        bad += len(errs)
    print("\n%s" % ("全部通过" if bad == 0 else "有%d 处错，必须先修" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())