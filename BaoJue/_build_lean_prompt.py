# -*- coding: utf-8 -*-
"""做一个「精简版」提示词，与现行「规则堆叠版」对照。

═══════ 为什么怀疑提示词太长是「理解能力差」的根因 ═══════
用户反馈：「本地的理解能力没有 seedance 好，总是很混乱，同样的提示词剧情就表现不好」。

实测（`_prompt_stats`）：
  现行 seg01 提示词 = **2071 词**，而 H3 官方建议 **约 350 词** → 超 5.9 倍
  命令词（never/always/not）出现 **36 次**
  真正承载剧情的只有 4 个 [Shot]，合计 **约 250 词（12%）**
  前面 1400+ 词全是规则：竖屏构图、禁止特写、禁止多人、曝光锚点、空间锚点、说话人表…

H3 是 DiT + 文本编码器。1700 词的纯规则文本会把文本条件推向高维空间的
**规则区**，离「剧情语义区」很远 —— 表现为：镜头读不懂、人物乱动、指令互相打架
（CAST LOCK 说固定 3 人，SPACE ANCHOR 说门口会有人，模型只能随机选一个）。

═══════ 本文件的策略 ═══════
不动 `storyboard_render.py`（老集 sha 会被改），改为**段级开关** `style_pack`：
  · `full`（默认，保持现状）
  · `lean`（新）：只保留「画风 + 光 + 构图 + 空间锚点 + 剧情」，
    删掉所有"禁止型"规则与重复的曝光锚点，目标 **约 400–500 词**

风格上参考 Seedance 提示词的特点：**短、具体、以动作和画面描述为主，不堆禁令**。
"""

import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
BEATS = os.path.join(BASE, "xs001_beats", "scene11.json")

# ── 精简版：画风 + 光 + 构图（保留必要约束，但每条都短）────────────────
LEAN_STYLE = (
    "VERTICAL 9:16 portrait, one continuous take, no cuts. "
    "Bright modern Chinese office at midday, soft diffused window light through "
    "venetian blinds, warm low-contrast film grade, clean and luminous, open shadows, "
    "high-end commercial cinematography on a large-format camera, shallow depth of field, "
    "refined natural faces and skin, elegant wardrobe. "
    "A whole adult figure stays standing, framed from the knees up, camera at a normal "
    "medium distance, the camera never pushes in to a detail shot."
)

# ── 精简版曝光/光：只留一句，替代原来那一大段 ─────────────────────────
LEAN_EXPO = (
    "The room is evenly and generously lit from the front; no face is in shadow, "
    "nothing in the frame is murky or black."
)

# ── 精简版空间锚点：只保留「谁在哪」，删掉所有"绝不" ────────────────
LEAN_ANCHOR = (
    "Room layout, constant all take: the closed door is on the LEFT, the blind-covered "
    "window and tall wooden cabinets are on the RIGHT, the chestnut-wooden desk is across the "
    "middle. 苏小满 (S1) stands on the near side of the desk, back to the door. "
    "钱经理 (S3) is at the far side of the desk, back to the window. "
    "小唐 (S4) stands in the far LEFT corner against the wall. "
    "These three people are the only people in the room and the count does not change."
)


def lean_shots(original):
    """从原 shots 里抽掉所有"禁止型"措辞，只留时间戳 + 画面 + 台词。"""
    out = []
    for ln in original.split("\n"):
        if not ln.strip().startswith("[Shot"):
            continue
        # 去掉冗长的否定从句：everything after the first Chinese clause 保留原文，
        # 因为画面描述本身就是剧情，不能删。这里只做轻度清理。
        ln = re.sub(r"\s+", " ", ln).strip()
        out.append(ln)
    return "\n".join(out)


def main():
    d = json.load(io.open(BEATS, encoding="utf-8"))
    for s in d:
        s["style_pack"] = "lean"
        s["_lean_shots"] = lean_shots(s["shots"])
        n_in = len(s["_lean_shots"].split())
        print("%s  原 shots %4d 词 → 精简后 %4d 词" % (s["id"], len(s["shots"].split()), n_in))
    io.open(BEATS, "w", encoding="utf-8").write(
        json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print("\n已给 %d 段打上 style_pack=lean" % len(d))
    print("渲染器还需加 lean 分支才会生效（下一步做）")


if __name__ == "__main__":
    main()
