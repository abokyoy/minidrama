# -*- coding: utf-8 -*-
"""seg02 补上剧本漏掉的一拍：「钱经理转过头，斜了小唐一眼」。

用户 2026-10-07 20:23 指出：
> 「第二个应该是把小唐从外面叫进来」

对照剧本 X003_终版.md 第 20–30 行：
  20 △ 门被撞开。钱经理大步进来，身后的小唐，脸发白。
  22 **钱经理**（拍桌）：三楼包厢。贵客丢了一只金耳钉。三万八。
  24 **钱经理**（盯着苏小满）：收台的时候，就你一个人在。
  26 **苏小满**：不是我。
  28 △ **钱经理转过头，斜了小唐一眼。**←←← 我漏了这一拍
  30 **小唐**（保洁组同事，眼神躲闪）：钱经理。中午，我看见她往兜里塞东西。没看清。

我原来的分段：
  seg01 撞门拍桌（三楼包厢…三万八）
  seg02 对峙（收台时就你一人→ 不是我）        ← 少了第 28 行
  seg03 小唐作证                        ← 小唐突然就开口了，中间没有过渡

改法（方案 A：不加段数）：
  seg02 末尾加Shot 4：**钱经理转头，斜眼看向门口的小唐**（不说话，只是那个动作）
  → seg03 开头小唐已经在走进来，直接开口作证
  → 剧情接上了，段数不变（不用多花 15 分钟）

⛔ 零否定词，零对称词，零走廊词（沿用第 4 轮 + 第 31/32 节的三条铁律）。
"""
import io
import json
import re

BEATS = "xs001_beats/scene11.json"
segs = json.load(io.open(BEATS, encoding="utf-8"))

s = segs[1]
print("改前 seg02 标题: %s" % s.get("title"))

# ══════════════════════════════════════════════════════════════
# 1. Entry state：加入小唐（她在门口站着，等待被叫）
# ══════════════════════════════════════════════════════════════
old_entry = (s.get("shots") or "").split("\n")[0]
NEW_ENTRY = (
    "Entry state, re-anchored to the reference image: 钱经理 (S3) is leaning on the far "
    "side of the desk with one palm flat on it, the grey filing cabinets directly behind "
    "him, facing the camera; 苏小满 (S1) stands at the near side of the desk with her back "
    "to the camera and a plain stretch of white wall behind her, facing him; 小唐 (S4) "
    "stands against the back wall at the far left of frame, half inside the room, her "
    "shoulder blade on the white paint, waiting where she has been standing. The closed "
    "wooden door in the back wall stays shut, its surface plain wood."
)
assert old_entry in s["shots"], "seg02 Entry state 没匹配上"
s["shots"] = s["shots"].replace(old_entry, NEW_ENTRY, 1)

# ══════════════════════════════════════════════════════════════
# 2. Shot 3 / Shot 4 改成剧本第 28 行：钱经理转头斜小唐
# ══════════════════════════════════════════════════════════════
reps = [
    # Shot 3：原来只是 wide 空镜，现在改成「他开始转头」
    ("[Shot 3] At 00:07.800, wide shot across the desk: he stands behind it facing the "
     "lens, she stands at the near end with her back to the lens, the grey filing cabinets "
     "fill the wall behind him and a plain stretch of white wall with a band of "
     "blind-light fills the wall behind her, and the whole room stays very still.",
     "[Shot 3] At 00:07.800, medium over the desk: 钱经理 (S3) finishes the accusation and "
     "stops, and his eyes leave her. He turns his head and shoulders away from the desk "
     "toward the left-hand wall of the room, and the camera follows the turn. 苏小满 (S1) "
     "stays where she is at the near end of the desk, following him with her eyes."),
    # Shot 4：剧本第 28 行 —— 斜了小唐一眼（不说话）
    ("[Shot 4] At 00:09.200, the camera creeps a few centimetres closer on the desk "
     "surface between them. Neither of them speaks.",
     "[Shot 4] At 00:09.200, he has turned his head fully to the left and looks straight "
     "at 小唐 (S4) against the wall. The look lasts a beat and says everything: she is the "
     "next one. His lips stay closed through it. Then he gives one short jerk of his chin "
     "toward the open floor beside the desk, the gesture that tells her to come and stand "
     "there. 小唐 (S4) sees it, pushes off the wall with her shoulder and takes the first "
     "step forward into the room. 苏小满 (S1) has gone very still at the near end of the "
     "desk, watching the colleague approach. The room is quiet."),
]
for a, b in reps:
    assert a in s["shots"], "seg02 没匹配上: " + a[:46]
    s["shots"] = s["shots"].replace(a, b, 1)

# ══════════════════════════════════════════════════════════════
# 3. _lean_shots 同步（这个才是 lean 档实际生效的字段）
# ══════════════════════════════════════════════════════════════
LS = [
    ("[Shot 3] At 00:07.800, wide shot across the desk: he stands behind it facing the "
     "lens, she stands at the near end with her back to the lens, the grey filing cabinets "
     "fill the wall behind him and a plain stretch of white wall with a band of "
     "blind-light fills the wall behind her, and the whole room stays very still.",
     "[Shot 3] At 00:07.800, medium over the desk: 钱经理 (S3) finishes the accusation and "
     "stops, and his eyes leave her. He turns his head and shoulders away from the desk "
     "toward the left-hand wall of the room, and the camera follows the turn. 苏小满 (S1) "
     "stays where she is at the near end of the desk, following him with her eyes."),
    ("[Shot 4] At 00:09.200, the camera creeps a few centimetres closer on the desk "
     "surface between them. Neither of them speaks.",
     "[Shot 4] At 00:09.200, he has turned his head fully to the left and looks straight "
     "at 小唐 (S4) against the wall. The look lasts a beat and says everything: she is the "
     "next one. His lips stay closed through it. Then he gives one short jerk of his chin "
     "toward the open floor beside the desk, the gesture that tells her to come and stand "
     "there. 小唐 (S4) sees it, pushes off the wall with her shoulder and takes the first "
     "step forward into the room. 苏小满 (S1) has gone very still at the near end of the "
     "desk, watching the colleague approach. The room is quiet."),
]
t = s.get("_lean_shots") or ""
for a, b in LS:
    if a in t:
        t = t.replace(a, b, 1)
s["_lean_shots"] = t

# ══════════════════════════════════════════════════════════════
# 4. refs 要加小唐（她这一段出场了！）
# ══════════════════════════════════════════════════════════════
print("改前 seg02 refs: %s" % s["refs"])
s["refs"] = ["qianjingli", "suxiaoman", "xiaotang"]

# ══════════════════════════════════════════════════════════════
# 5. seg03 Entry state：小唐已经走到桌前，不再是贴墙站
# ══════════════════════════════════════════════════════════════
s3 = segs[2]
old_e3 = (s3.get("shots") or "").split("\n")[0]
NEW_E3 = (
    "Entry state, re-anchored to the reference image: 钱经理 (S3) stands behind the desk "
    "facing the camera, the grey filing cabinets directly behind his back, one palm flat "
    "on the desk top; 小唐 (S4) stands on the open floor beside the desk, a pace in from "
    "its near end, facing him with her hands folded low in front of her; 苏小满 (S1) stands "
    "at the near end of that desk with her back to the camera, facing them both. The "
    "people named in this beat are the only people in it: the manager stays behind the "
    "desk, the colleague stands in the open floor beside it, and the cleaner stays at the "
    "near end of it with her back turned. The closed wooden door in the back wall stays "
    "shut, its surface plain wood, and a band of blind-light runs across the white wall."
)
assert old_e3 in s3["shots"], "seg03 Entry state 没匹配上"
s3["shots"] = s3["shots"].replace(old_e3, NEW_E3, 1)

t3 = s3.get("_lean_shots") or ""
t3 = t3.replace(
    "[Shot 1] Medium: 钱经理 (S3) turns his shoulder toward the door and jerks his chin at "
    "小唐 (S4), summoning her forward with that gesture alone.",
    "[Shot 1] Medium: 钱经理 (S3) finishes looking at the colleague and turns his eyes to "
    "her face, waiting; he lifts one hand off the desk and turns it over, palm up, a short "
    "beckoning motion that means go on. His lips stay closed.",
    1)
s3["_lean_shots"] = t3

s3["shots"] = s3["shots"].replace(
    "[Shot 1] Medium: 钱经理 (S3) turns his shoulder toward the door and jerks his chin at "
    "小唐 (S4), summoning her forward with that gesture alone.",
    "[Shot 1] Medium: 钱经理 (S3) finishes looking at the colleague and turns his eyes to "
    "her face, waiting; he lifts one hand off the desk and turns it over, palm up, a short "
    "beckoning motion that means go on. His lips stay closed.",
    1)

# seg03 的小唐特写：她已经站在桌前了
for key in ("shots", "_lean_shots"):
    t = s3.get(key) or ""
    t = t.replace(
        "[Shot 2] At 00:02.000, closer on 小唐 (S4): she peels off the wall, folds her "
        "hands together, keeps her eyes on the floor tiles and lets them flick once toward "
        "苏小满 (S1), then away;",
        "[Shot 2] At 00:02.000, closer on 小唐 (S4) standing on the open floor beside the "
        "desk: she draws her shoulders up, keeps her eyes on the floor tiles and lets them "
        "flick once toward 苏小满 (S1), then away;",
        1)
    s3[key] = t

with io.open(BEATS, "w", encoding="utf-8") as f:
    f.write(json.dumps(segs, ensure_ascii=False, indent=2))

# ══════════════════════════════════════════════════════════════
# 6. 复查三条铁律
# ══════════════════════════════════════════════════════════════
print("\nseg02 refs: %s" % segs[1]["refs"])
BAD = re.compile(r"nobody|no one|no other|never |duplicat|half of the frame|"
                 r"half of frame|each one holding|own third|third of the frame|"
                 r"on the centre axis|corridor|doorway|passage|hallway", re.I)
print("\n===== 复查 =====")
for i, sg in enumerate(segs, 1):
    txt = " ".join(str(sg.get(k) or "") for k in
                   ("shots", "_lean_shots", "lean_anchor", "anchor",
                    "summary", "soundscape"))
    hits = sorted(set(m.group(0) for m in BAD.finditer(txt)))
    tag = "（seg01 已验收）" if i == 1 else (hits or "干净")
    print("  seg%02d %s" % (i, tag))

print("\nseg02 现在的 shots:")
print(segs[1]["shots"])