# -*- coding: utf-8 -*-
"""seg03/04/05 清掉对称描述（照seg02 第4 轮已验证有效的配方）。

第 2 段的病：`each one holding her or his own half of the frame`
→ 模型把它读成「画面左右各站一个人」→ 对称补全成两个苏小满。
→ 改成**具体机位**（谁在哪、面朝哪、镜头在哪）后彻底解决（20 帧逐帧核对只有两人）。

seg03/04/05 同样带着这些词，且 seg03/04 用的是「own third of the frame」（各占三分之一）
→ 三人段会变成对称三连。必须一起清掉。

同时按 seg02 的做法：refs 去掉环境图，只留人物身份图。
（官方：Use one primary identity source / Do not send references as an
undifferentiated pile.）
"""
import io
import json
import re

BEATS = "xs001_beats/scene11.json"
segs = json.load(io.open(BEATS, encoding="utf-8"))

# ══════════════════════════════════════════════════════════════
# 1. refs：去掉环境图，只留人物身份图（照 seg02 第4轮）
# ══════════════════════════════════════════════════════════════
NEW_REFS = {
    3: ["qianjingli", "suxiaoman", "xiaotang"],
    4: ["qianjingli", "suxiaoman", "xiaotang"],
    5: ["qianjingli", "suxiaoman"],
}
for idx, refs in NEW_REFS.items():
    s = segs[idx - 1]
    print("seg%02d refs: %s -> %s" % (idx, s["refs"], refs))
    s["refs"] = refs

# ══════════════════════════════════════════════════════════════
# 2. Entry state：去掉「各占一半/三分之一」，改成具体机位
# ══════════════════════════════════════════════════════════════
ENTRY = {
    3: (
        "Entry state, re-anchored to the reference image: 钱经理 (S3) stands behind the "
        "desk facing the camera, the grey filing cabinets directly behind his back, one "
        "palm flat on the desk top; 苏小满 (S1) stands at the near end of that desk with "
        "her back to the camera, facing him; 小唐 (S4) stands flattened against the wall "
        "beside the shut doorway at the far left of frame, half a step in from it, her "
        "shoulder touching the doorframe. "
        "The people named in this beat are the only people in it: the manager stays behind "
        "the desk, the cleaner stays at the near end of it with her back turned, and the "
        "young colleague stays low at the left-hand doorway, watching from where she "
        "stands. The doorway itself stays shut and the corridor beyond it is a plain "
        "bare passage."
    ),
    4: (
        "Entry state, re-anchored to the reference image: 苏小满 (S1) stands at the near "
        "end of the desk with her back to the camera, facing the doorway; 小唐 (S4) has "
        "taken one step in from the wall and now stands beside the shut doorway at the far "
        "left of frame, her hand on the doorframe; 钱经理 (S3) stands behind the desk on the "
        "far side, the grey filing cabinets behind him, facing the lens with his arms "
        "folded. "
        "The people named in this beat are the only people in it: the two women stand one "
        "behind the other along the depth of the room, the colleague nearer the doorway and "
        "the cleaner nearer the desk, and the manager stays behind the desk watching them. "
        "The doorway stays shut and the corridor beyond it is a plain bare passage."
    ),
    5: (
        "Entry state, re-anchored to the reference image: 钱经理 (S3) is stepping round "
        "the end of the desk onto the near side and closing to one pace in front of "
        "苏小满 (S1); 苏小满 (S1) stands at the near end of the desk with her back to the "
        "camera, facing him across one pace of bare floor. "
        "The people named in this beat are the only people in it: the manager stands in "
        "front of the cleaner, one pace away, and they hold the shot together — the desk "
        "behind them, the grey filing cabinets to one side, the shut doorway behind the "
        "camera. The doorway and the corridor beyond it are a plain bare passage."
    ),
}

for idx, new_entry in ENTRY.items():
    s = segs[idx - 1]
    old_entry = (s.get("shots") or "").split("\n")[0]
    assert old_entry in s["shots"], "seg%02d Entry state 没匹配上" % idx
    s["shots"] = s["shots"].replace(old_entry, new_entry, 1)
    print("seg%02d Entry 已改写 (%d 字 -> %d 字)"
          % (idx, len(old_entry), len(new_entry)))

# ══════════════════════════════════════════════════════════════
# 3. 正文里其它对称/否定表述
# ══════════════════════════════════════════════════════════════
BODY_REPS = [
    # seg04 shot3 深度轴摆位，改成具体站位（不写「一前一后」的比例）
    ("wide: the two women staged one behind the other along the room's depth axis — "
     "小唐 (S4) nearer the door, 苏小满 (S1) nearer the desk — with 钱经理 (S3) motionless "
     "behind the desk, back to the window, watching them like a spectator, arms folded.",
     "wide: 小唐 (S4) stands at the left-hand doorway in the near part of the room, "
     "苏小满 (S1) stands at the desk just behind her, and 钱经理 (S3) stands motionless "
     "behind the desk with the filing cabinets behind him, watching them like a spectator, "
     "arms folded."),
    # seg04 shot4
    ("At 00:09.600, hold. Nobody moves and nobody speaks.",
     "At 00:09.600, hold. All three of them stay exactly where they are, every mouth "
     "closed, the office still."),
    # seg03 shot4
    ("close on 钱经理 (S3) taking that in, the corner of his mouth pulling up. Nobody "
     "else speaks.",
     "close on 钱经理 (S3) taking that in, the corner of his mouth pulling up, his lips "
     "closed for the rest of the shot."),
    # seg03 shot1 否定词
    ("jerks his chin at 小唐 (S4), summoning her forward without a word.",
     "jerks his chin at 小唐 (S4), summoning her forward with that gesture alone."),
]
for idx in (3, 4, 5):
    s = segs[idx - 1]
    for a, b in BODY_REPS:
        if a in s["shots"]:
            s["shots"] = s["shots"].replace(a, b, 1)
            print("  seg%02d 改: %s..." % (idx, a[:44]))

with io.open(BEATS, "w", encoding="utf-8") as f:
    f.write(json.dumps(segs, ensure_ascii=False, indent=2))

# ══════════════════════════════════════════════════════════════
# 4. 复查
# ══════════════════════════════════════════════════════════════
BAD = re.compile(r"half of the frame|half of frame|each one holding|own third|"
                 r"third of the frame|on the centre axis|far half|near half|"
                 r"nobody|no one|no other|never |duplicat", re.I)
print("\n===== 复查 =====")
ok = True
for i, s in enumerate(segs, 1):
    txt = " ".join(str(s.get(k) or "") for k in
                   ("shots", "lean_anchor", "anchor", "_lean_shots",
                    "summary", "soundscape"))
    hits = sorted(set(m.group(0) for m in BAD.finditer(txt)))
    if hits:
        ok = False
    print("  seg%02d %s" % (i, hits or "干净"))
print("\n结论:", "全部干净" if ok else "还有残留")