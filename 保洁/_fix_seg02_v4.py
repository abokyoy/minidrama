# -*- coding: utf-8 -*-
"""第2 段第四轮：治「对称补全」导致的左右各一个苏小满。

第4 轮（换单人参考图）后：左一个苏小满 + 中间钱经理 + 右一个苏小满。
三个 -> 两个，有改善但没根治。

⭐ 新发现的诱因（我自己写的）：
  提示词里反复出现「each one holding her or his own **half of the frame**」
  「far half / near half」「**left** / **right**」这种**对称描述**，
  等于在告诉模型「画面左右两边各摆一个人」→ 它就对称补全，真的变两个。

官方文档对得上：
  "Use **one primary identity source**. Add extra images only when they provide a
   missing angle or detail."
  "The problem isn't how many references you upload, but what information each
   reference contributes."
→ 一段只给「人物身份图」，场景靠文字描述，不再塞环境参考图跟人物抢。

改法：
  1. 删掉所有 half / each one holding / 左右对称的说法，改成具体机位
     （钱经理在桌子后头靠文件柜，苏小满在桌子靠门那头背对镜头）
  2. refs 去掉场景图 —— 只留两张人物身份图
  3. 零否定词
"""
import io
import json

BEATS = "xs001_beats/scene11.json"

# ---------- 1. refs：去掉环境图，只留两张人物身份图 ----------
segs = json.load(io.open(BEATS, encoding="utf-8"))
s = segs[1]
old = list(s["refs"])
s["refs"] = ["qianjingli", "suxiaoman"]
print("refs: %s -> %s" % (old, s["refs"]))

# ---------- 2. lean_anchor：去掉对称描述，改具体机位 ----------
OLD_ANCHOR = s.get("lean_anchor", "")

NEW_ANCHOR = (
    "The office is one small private room: a wooden desk stands across the middle of it, "
    "long side to the camera, and behind that desk the wall is covered with grey metal "
    "filing cabinets. Bright mid-morning daylight comes through venetian blinds on the "
    "right-hand wall and lays bright bands across the desk top and the floor. "
    "The people named in this beat are the only people in it: the manager stays behind "
    "the desk on the far side and the cleaner stays at the near end with her back to the "
    "camera. "
    "钱经理 (S3), the manager, is a stocky middle-aged man in a white shirt and charcoal "
    "waistcoat; he stays on the far side of that desk for the entire clip, standing behind "
    "it with the filing cabinets directly behind his back, facing the camera, his weight "
    "on the desk. "
    "苏小满 (S1), the cleaner, is a young woman in a navy work shirt with a grey apron; "
    "she stays on the near side of that desk for the entire clip, standing with her back "
    "to the camera and the doorway behind her, facing him. "
    "The camera stands on the near side of the desk and looks across it at him, so he is "
    "further away and smaller, and she is closer to the lens with her back turned. "
    "Everything past them is bare: the doorway at the back stays shut, the corridor "
    "beyond it is a plain empty passage, and the desk between them is clear except a "
    "single sheet of paper and one pen lying flat near its middle."
)
s["lean_anchor"] = NEW_ANCHOR
print("lean_anchor: %d 字 -> %d 字" % (len(OLD_ANCHOR), len(NEW_ANCHOR)))

# ---------- 3. shots：Entry state 里的对称描述也改掉 ----------
old_entry = s["shots"].split("\n")[0]
NEW_ENTRY = (
    "Entry state, re-anchored to the reference image: 钱经理 (S3) is leaning on the far "
    "side of the desk with one palm flat on it, the grey filing cabinets directly behind "
    "him, facing the camera; 苏小满 (S1) stands at the near side of the desk with her back "
    "to the camera and the shut doorway behind her, facing him. The doorway and the "
    "corridor beyond it are a plain bare passage."
)
assert old_entry in s["shots"], "seg02 Entry state 没匹配上"
s["shots"] = s["shots"].replace(old_entry, NEW_ENTRY, 1)

# Shot 3 里也有"wide two-shot ... both of them motionless at either side of it"
reps = [
    ("wide two-shot across the desk, both of them motionless at either side of it, "
     "the room very still, the two of them alone in the frame with clear empty space "
     "behind each of them.",
     "wide shot across the desk: he stands behind it facing the lens, she stands at the "
     "near end with her back to the lens, the grey filing cabinets fill the wall behind "
     "him and the shut doorway fills the wall behind her, and the whole room stays very "
     "still."),
]
for a, b in reps:
    assert a in s["shots"], "seg02 没匹配上: " + a[:40]
    s["shots"] = s["shots"].replace(a, b, 1)

with io.open(BEATS, "w", encoding="utf-8") as f:
    f.write(json.dumps(segs, ensure_ascii=False, indent=2))

# ---------- 4. 复查对称词 ----------
import re
txt = NEW_ANCHOR + " " + s["shots"]
for kw in ["half of frame", "each one holding", "left", "right", "centre", "axis"]:
    n = len(re.findall(r"%s" % kw, txt, re.I))
    print("  %-18s %d 次" % (kw, n))
bad = re.compile(r"nobody|no one|no other|never |duplicat|half of frame|"
                 r"each one holding", re.I)
print("  否定/对称词命中:", sorted(set(m.group(0) for m in bad.finditer(txt))) or "无")
print("\n写回完成")