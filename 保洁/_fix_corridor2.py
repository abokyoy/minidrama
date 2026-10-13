# -*- coding: utf-8 -*-
"""清掉残留的 corridor / doorway —— 包括 soundscape 字段。

ⓘsoundscape 也会被拼进提示词，**同样在念叨走廊**，必须一起改。
（这是我上一轮漏掉的：只改了 shots/anchor，没改 soundscape。）

残留清单：
  seg02 soundscape  faint corridor noise beyond the door
  seg02 shots       the shut doorway behind her
  seg02 lean_anchor the doorway behind her
  seg04 soundscape  muffled office noise from the corridor
  seg05 soundscape  distant corridor chatter
  seg05 shots       the shut doorway behind the camera
"""
import io
import json
import re

BEATS = "xs001_beats/scene11.json"
segs = json.load(io.open(BEATS, encoding="utf-8"))

REPS = [
    # ── soundscape：走廊声改成室内房间声 ──
    ("faint corridor noise beyond the door",
     "a faint breath of room tone from the ceiling lights"),
    ("muffled office noise from the corridor",
     "a muffled hum of room tone"),
    ("distant corridor chatter",
     "a low murmur of room tone"),
    # ── shots / anchor 里的 doorway → 后墙上的木门 ──
    ("the shut doorway behind her, facing him",
     "a plain stretch of white wall behind her, facing him"),
    ("the doorway behind her, facing him",
     "a plain stretch of white wall behind her, facing him"),
    ("the shut doorway behind the camera",
     "the closed wooden door in the back wall behind the camera"),
]

for idx in (2, 3, 4, 5):
    s = segs[idx - 1]
    for k in ("shots", "_lean_shots", "lean_anchor", "anchor",
              "soundscape", "summary"):
        t = s.get(k)
        if not t:
            continue
        orig = t
        for a, b in REPS:
            if a in t:
                t = t.replace(a, b, 1)
        if t != orig:
            s[k] = t
            print("  seg%02d [%-11s] 已改" % (idx, k))

with io.open(BEATS, "w", encoding="utf-8") as f:
    f.write(json.dumps(segs, ensure_ascii=False, indent=2))

print("\n===== 复查（全部字段）=====")
bad = re.compile(r"corridor|doorway|passage|hallway", re.I)
allclean = True
for i, s in enumerate(segs, 1):
    txt = " ".join(str(s.get(k) or "") for k in
                   ("shots", "_lean_shots", "lean_anchor", "anchor",
                    "summary", "soundscape"))
    hits = sorted(set(m.group(0) for m in bad.finditer(txt)))
    if i == 1:
        print("  seg01 （已验收，不动）%s" % (hits or ""))
        continue
    if hits:
        allclean = False
    print("  seg%02d %s" % (i, hits or "干净"))
print("\n结论:", "seg02-05 全部干净" if allclean else "还有残留")