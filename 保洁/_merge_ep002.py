# -*- coding: utf-8 -*-
r"""把 ep002 的三段连续脚本合并成一份，镜号全局重编为 P001…，并生成分镜脚本.md。

为什么需要它：
  ep002 的 ②连续脚本 是分三个子代理并行写的（场次 2-1/2-2、2-3/2-4、2-5），
  三份各自从 P01 编号，必须重编成全局唯一，否则第③步对不上。

用法： python _merge_ep002.py
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
EP = sys.argv[1] if len(sys.argv) > 1 else "ep002"

# 集号 → (标题, 合并后的文件头记号行)
EP_META = {
    "ep002": ("第 2 集《雇来的小姐》",
              "`满`＝苏小满(S1)，`蔓`＝陆蔓(S8)，`航`＝陆航(S14)，`陆`＝陆崇(S15)，`心`＝心腹(S16)，\n"
              "> `收`＝收费员(S17)，`芳`＝阿芳(S5)，`前`＝前台(S12)，`钱`＝钱经理(S3)，`婆`＝外婆(S9)，`佣`＝老佣人。"),
    "ep003": ("第 3 集《第一场核实会》",
              "`满`＝苏小满(S1)，`罗`＝小罗(S7)，`蔓`＝陆蔓(S8)，`航`＝陆航(S14)，`崇`＝陆崇(S15)；\n"
              "> `忠`＝忠叔(S18)，`秦`＝秦律师(S19)。"),
    "ep004": ("第 4 集《核实的第一道门》",
              "`满`＝苏小满(S1)，`宾`＝女贵宾(S2)，`钱`＝钱经理(S3)，`唐`＝小唐(S4)，`芳`＝阿芳(S5)，\n"
              "> `周`＝周总监(S6)，`罗`＝小罗(S7)，`蔓`＝陆蔓(S8)，`婆`＝外婆(S9)，`张`＝张总(S10)，\n"
              "> `医`＝医生(S11)，`前`＝前台(S12)，`航`＝陆航(S14)，`崇`＝陆崇(S15)，`心`＝心腹(S16)，\n"
              "> `收`＝收费员(S17)，`忠`＝忠叔(S18)，`秦`＝秦律师(S19)，`长`＝护士长(S20)。"),
    "ep005": ("第 5 集《第一百三十八个名字》",
              "`满`＝苏小满(S1)，`蔓`＝陆蔓(S8)，`航`＝陆航(S14)，`陆`＝陆崇(S15)，`忠`＝忠叔(S18)，\n"
              "> `秦`＝秦律师(S19)，`邻`＝邻居(S21，画外)。"
              "道具：`料`＝陆崇那摞材料（牛皮纸档案袋＋几页纸＋一张按过手印的协议复印件），\n"
              "> `绳`＝旧红绳（一直在领口内，本集才第一次被看见），`协`＝协议复印件，`机`＝苏小满的手机。"),
}

PARTS = [os.path.join(BASE, EP, "连续脚本_part%d.md" % i) for i in (1, 2, 3)]

_ttl, _mk = EP_META.get(EP, ("第 ? 集", ""))

HEADER = ("""# 《第一百三十八个名字》%s— 连续脚本（逐镜头连续性表）

> **第②步产物。** 依据：`文字剧本.md`。
> 用途：**逐镜头锁定人物的位置、朝向、手里拿着什么、身上什么状态**，保证"上一镜的出镜状态 = 下一镜的入镜状态"。
> **任何镜头都不许违背《文字剧本》第零节的空间锚点。** 分镜脚本（第③步）只能从这里取内容，不许自己编站位。
> 本文件由 `连续脚本_part1/2/3.md` 合并、镜号全局重编而来（`_merge_ep002.py`）。
>
> 记号：%s
> 每镜格式：`编号『景别·机位』画面内容 ／ 台词 ／ 站位 ／ 出镜状态`。

---

""" % (_ttl, _mk))

P_RE = re.compile(r"^(\s*-\s*\*\*)P(\d+)(\*\*)", re.M)


def merge():
    out = [HEADER]
    n = 0
    for p in PARTS:
        if not os.path.exists(p):
            continue   # 有些集只拆了两部分，缺的跳过
        txt = io.open(p, encoding="utf-8").read()
        # 去掉各份自己的大标题与导语（第一处 '---' 之前的内容），保留小节与镜表
        idx = txt.find("\n---\n")
        body = txt[idx + 5:] if idx >= 0 else txt
        # 各份自己的 ## 标题重编为全局小节序号
        out.append(body.strip() + "\n\n")
        out.append("---\n\n")
        n += len(P_RE.findall(txt))
    whole = "".join(out)

    # 全局重编镜号
    counter = [0]

    def _renum(m):
        counter[0] += 1
        return "%sP%03d%s" % (m.group(1), counter[0], m.group(3))

    whole = P_RE.sub(_renum, whole)

    dst = os.path.join(BASE, EP, "连续脚本.md")
    tmp = dst + ".tmp"
    io.open(tmp, "w", encoding="utf-8").write(whole)
    os.replace(tmp, dst)
    print("合并 %d 个文件，共 %d 镜 → %s" % (len(PARTS), counter[0], dst))
    return 0


def storyboard_doc():
    """由 manifest.json 生成第③步文档：每段一行（段号／场次／台词字数／标题／参考图数）。"""
    man = json.load(io.open(os.path.join(BASE, EP + "_segs", "manifest.json"), encoding="utf-8"))
    beats = []
    import glob
    for f in sorted(glob.glob(os.path.join(BASE, EP + "_beats", "*.json"))):
        beats.extend(json.load(io.open(f, encoding="utf-8")))
    by_id = {b["id"]: b for b in beats}

    L = []
    L.append("# 《第一百三十八个名字》%s— 分镜脚本（段表）\n" % _ttl)
    L.append("> **第③步产物。** 依据：`连续脚本.md`。本文件把逐镜连续性表**按 10 秒一段**组合成 `T##` 分镜段。")
    L.append("> 每段再由 `storyboard_render.py` 渲染成 H3 ref2v 六段式提示词（`%s_segs/segNN_prompt.txt`）。\n" % EP)
    L.append("> **铁律**：每段第一拍接上一段最后一拍；段内中文台词 ≤ 24 字（约 2.5 字/秒 × 10 秒）；超了必须拆段。")
    L.append("> 画幅：**9:16 竖屏**（AGENTS.md 15.1）；不烧任何字幕（15.6）；每段最多 6 张参考图，只放**本段真的在场**的人与场景（15.8）。\n")
    L.append("---\n")
    L.append("## 一、全片段落总表\n")
    L.append("| 段号 | id | 场次 | 标题 | 台词 | 镜数 | 参考图 |")
    L.append("|---|---|---|---|---|---|---|")
    for m in man:
        b = by_id.get(m["id"], {})
        lines = re.findall(r"\[Chinese\]\s*([^\[\n]*)", b.get("shots", ""))
        dlg = " ／ ".join(x.strip() for x in lines) if lines else "—"
        L.append("| seg%02d | %s | %s | %s | %s（%d字） | %s | %d |"
                 % (m["n"], m["id"], m.get("scene", ""), m.get("title", ""),
                    dlg, m.get("chars", 0), m.get("shots", ""), m.get("refs", 0)))
    L.append("")
    L.append("## 二、链组与重启节奏\n")
    L.append("- 每 **3 段**为一个链组：组头用 `04_ref2v_4step_sla_ganloss_fixed.json`，组内第 2、3 段用 "
             "`04_ref2v_seg2_chain.json`（拿上一段尾帧当首帧，`prev_skip=221`）。")
    L.append("- 每满 3 段（即组头开跑前）由 `gen_worker.py` **kill 并重启 ComfyUI**，防「越接越黑」。")
    L.append("- 每段生成后自动跑 `_grade.py` 后期调色（提黑位＋压对比），并复测亮度（p05/med/mean）。")
    L.append("- 分镜内容指纹写进 `ep002_segs/manifest.json` 的 `sha`；`gen_worker.py --watch` 每组开跑前重读，"
             "改了哪一段就只补跑那一个链组。\n")

    dst = os.path.join(BASE, EP, "分镜脚本.md")
    tmp = dst + ".tmp"
    io.open(tmp, "w", encoding="utf-8").write("\n".join(L) + "\n")
    os.replace(tmp, dst)
    print("分镜脚本：%d 段 → %s" % (len(man), dst))
    return 0


if __name__ == "__main__":
    rc = merge()
    if rc == 0:
        rc = storyboard_doc()
    sys.exit(rc)
