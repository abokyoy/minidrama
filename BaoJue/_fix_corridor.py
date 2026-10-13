# -*- coding: utf-8 -*-
"""治「过道/走廊」串场：删掉所有 corridor/doorway 反复念叨，改成正面办公室细节。

用户 2026-10-07 19:24 指出：
  seg02 在办公室 ✅，但seg03 的特写背景**变成了绿色调的过道** ❌，两段不衔接。

⭐ 病根还是「否定式反复念叨」（和工牌、否定句同一个模子）：
  为了「排除走廊」，我在 seg02/03/04/05 每段都写了
    "the doorway stays shut and the **corridor** beyond it is a plain bare **passage**"
  → 走廊词密度：seg02=10 次、seg03=5、seg04=8、seg05=5
  → **反复念叨 = 强化先验**，模型真的造了一条过道出来。

⚠️ 与 seg01 的差异：seg01 也有 9 次「door」，但它带 4 张参考图（含场景图）
  压住了，所以画面仍是办公室。seg02–05 现在不带场景图了（官方：用一张主要身份图），
  没有场景图兜底 → 文字里每念一次走廊，就多一分被拉过去的可能。

改法（零否定 + 正面锚点）：
  1. 全删corridor / doorway / passage / bare passage
  2. 每段开头加一句**正面**的场景锚点：这是一间办公室，四面白墙+百叶窗+灰色文件柜+木桌
  3. 「门」只保留为「一扇关着的木门嵌在墙上」，并明确它在**房间内部的后墙**
     → 用「嵌在后墙上的一扇关闭的木门」代替「门后面是走廊」
  4. 声音里的 corridor noise 改成 room tone（同样在念叨走廊）
"""
import io
import json
import re

BEATS = "xs001_beats/scene11.json"
segs = json.load(io.open(BEATS, encoding="utf-8"))

# ══════════════════════════════════════════════════════════════
# 1. 逐句替换：走廊/门口 → 房间内部的后墙
# ══════════════════════════════════════════════════════════════
REPS = [
    # ── seg02 ──
    ("Everything past them is bare: the doorway at the back stays shut, the corridor "
     "beyond it is a plain empty passage, and the desk between them is clear except a "
     "single sheet of paper and one pen lying flat near its middle.",
     "The room around them is plain and bright: white walls, a band of venetian-blind "
     "light on the right-hand wall, a closed wooden door set flat into the back wall, and "
     "the desk between them clear except a single sheet of paper and one pen lying flat "
     "near its middle."),
    ("The doorway and the corridor beyond it are a plain bare passage.",
     "The closed wooden door in the back wall stays shut and its surface is plain wood."),
    ("the grey filing cabinets fill the wall behind him and the shut doorway fills the "
     "wall behind her, and the whole room stays very still.",
     "the grey filing cabinets fill the wall behind him and a plain stretch of white wall "
     "with a band of blind-light fills the wall behind her, and the whole room stays "
     "very still."),
    ("one nervous swallow, faint corridor noise beyond the door.",
     "one nervous swallow, a faint breath of room tone from the ceiling lights."),
    # ── seg03 ──
    ("小唐 (S4) stands flattened against the wall beside the shut doorway at the far left "
     "of frame, half a step in from it, her shoulder touching the doorframe.",
     "小唐 (S4) stands flattened against the back wall at the far left of frame, her "
     "shoulder blade pressed to the white paint and her hands folded low in front of her."),
    ("and the young colleague stays low at the left-hand doorway, watching from where she "
     "stands. The doorway itself stays shut and the corridor beyond it is a plain bare "
     "passage.",
     "and the young colleague stays low against the left-hand wall, watching from where "
     "she stands. The closed wooden door in the back wall stays shut, its surface plain "
     "wood, and a band of blind-light runs across the white wall behind her."),
    # ── seg04 ──
    ("苏小满 (S1) stands at the near end of the desk with her back to the camera, facing "
     "the doorway; 小唐 (S4) has taken one step in from the wall and now stands beside the "
     "shut doorway at the far left of frame, her hand on the doorframe;",
     "苏小满 (S1) stands at the near end of the desk with her back to the camera, facing "
     "the back wall; 小唐 (S4) has taken one step in from the wall and now stands against "
     "the left-hand wall at the far left of frame, her palm flat on the white paint;"),
    ("the colleague nearer the doorway and the cleaner nearer the desk, and the manager "
     "stays behind the desk watching them. The doorway stays shut and the corridor beyond "
     "it is a plain bare passage.",
     "the colleague nearer the back wall and the cleaner nearer the desk, and the manager "
     "stays behind the desk watching them. The closed wooden door in the back wall stays "
     "shut, its surface plain wood, and a band of blind-light lies across the floor."),
    ("小唐 (S4) stands at the left-hand doorway in the near part of the room,",
     "小唐 (S4) stands against the left-hand wall in the near part of the room,"),
    ("the wall clock ticking, muffled office noise from the corridor.",
     "the wall clock ticking, a muffled hum of room tone."),
    # ── seg05 ──
    ("the desk behind them, the grey filing cabinets to one side, the shut doorway behind "
     "the camera. The doorway and the corridor beyond it are a plain bare passage.",
     "the desk behind them, the grey filing cabinets to one side, the closed wooden door "
     "in the back wall behind the camera with its surface plain wood, and white walls "
     "carrying a band of blind-light."),
    ("the fluorescent hum, distant corridor chatter.",
     "the fluorescent hum, a low murmur of room tone."),
]

for idx in (2, 3, 4, 5):
    s = segs[idx - 1]
    for k in ("shots", "_lean_shots", "lean_anchor", "anchor"):
        t = s.get(k)
        if not t:
            continue
        orig = t
        for a, b in REPS:
            if a in t:
                t = t.replace(a, b, 1)
        if t != orig:
            s[k] = t
            print("  seg%02d [%s] 已改" % (idx, k))

# ══════════════════════════════════════════════════════════════
# 2. 给 seg02–05 每段加正面场景锚点（lean_anchor）
#    seg02 已有具体的锚点，保留；其余三段补上同一间办公室的正面描述
# ══════════════════════════════════════════════════════════════
ROOM = (
    "The whole clip takes place in one small private office and the camera never leaves "
    "it. The room has four plain white walls, a grey metal filing cabinet along the far "
    "wall, a long wooden desk standing across the middle of the floor, and venetian "
    "blinds on the right-hand wall laying bright bands of light across the desk top and "
    "the floor. A closed wooden door is set flat into the back wall, its surface plain "
    "wood with a small silver handle. Everything in this room reads as an office interior: "
    "the desk, the cabinet, the blinds and the plain painted walls."
)
for idx in (2, 3, 4, 5):
    s = segs[idx - 1]
    a = s.get("lean_anchor") or ""
    if "one small private office" not in a:
        s["lean_anchor"] = ROOM + " " + a if a else ROOM
        print("  seg%02d 加了正面场景锚点" % idx)

with io.open(BEATS, "w", encoding="utf-8") as f:
    f.write(json.dumps(segs, ensure_ascii=False, indent=2))

# ══════════════════════════════════════════════════════════════
# 3. 复查
# ══════════════════════════════════════════════════════════════
print("\n===== 复查走廊/门口类词 =====")
for i, s in enumerate(segs, 1):
    txt = " ".join(str(s.get(k) or "") for k in
                   ("shots", "_lean_shots", "lean_anchor", "anchor",
                    "summary", "soundscape"))
    cnt = {k: len(re.findall(k, txt, re.I))
           for k in ("corridor", "doorway", "passage", "hallway")}
    tag = "（seg01 已验收）" if i == 1 else cnt
    print("  seg%02d %s" % (i, tag))