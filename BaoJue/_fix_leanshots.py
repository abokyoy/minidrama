# -*- coding: utf-8 -*-
"""清 _lean_shots 里的残留否定词（这个字段才是实际拼进提示词的）。

seg01 已经用户验收通过（off_xs01_t01_00009）→ **一个字不动**。
只清 seg03/04/05。
"""
import io
import json
import re

BEATS = "xs001_beats/scene11.json"
segs = json.load(io.open(BEATS, encoding="utf-8"))

REPS = [
    # ── seg05 shot2 / shot3 ──
    ("[Shot 2] At 00:07.200, reverse single on 苏小满 (S1), framed on her alone, one "
     "person in this shot, nobody behind her and nobody at the door: she takes one "
     "small half-step back",
     "[Shot 2] At 00:07.200, reverse single on 苏小满 (S1) filling the frame on her own, "
     "the plain office wall and the bright window band behind her, one person in this "
     "shot: she takes one small half-step back"),
    ("[Shot 3] At 00:09.400, close on the pocket under her fingers, the fabric pulled "
     "slightly taut, framed on her alone, no one else enters this frame. She is silent "
     "after that.",
     "[Shot 3] At 00:09.400, close on the pocket under her fingers, the fabric pulled "
     "slightly taut, her own hand and the cloth filling the whole frame. She is silent "
     "after that."),
    # ── seg03 shot1 / shot4 ──
    ("jerks his chin at 小唐 (S4), summoning her forward without a word.",
     "jerks his chin at 小唐 (S4), summoning her forward with that gesture alone."),
    ("[Shot 4] At 00:09.400, close on 钱经理 (S3) taking that in, the corner of his mouth "
     "pulling up. Nobody else speaks.",
     "[Shot 4] At 00:09.400, close on 钱经理 (S3) taking that in, the corner of his mouth "
     "pulling up, his lips closed for the rest of the shot."),
    # ── seg04 shot3 / shot4 ──
    ("[Shot 3] At 00:08.600, wide: the two women staged one behind the other along the "
     "room's depth axis — 小唐 (S4) nearer the door, 苏小满 (S1) nearer the desk — with "
     "钱经理 (S3) motionless behind the desk, back to the window, watching them like a "
     "spectator, arms folded.",
     "[Shot 3] At 00:08.600, wide: 小唐 (S4) stands at the left-hand doorway in the near "
     "part of the room, 苏小满 (S1) stands at the desk just behind her, and 钱经理 (S3) "
     "stands motionless behind the desk with the filing cabinets behind him, watching them "
     "like a spectator, arms folded."),
    ("[Shot 4] At 00:09.600, hold. Nobody moves and nobody speaks.",
     "[Shot 4] At 00:09.600, hold. All three of them stay exactly where they are, every "
     "mouth closed, the office still."),
    # ── seg03 shot2：'without' 描述台词风格可留，但 'lets them flick' 无害 ──
]

for idx in (3, 4, 5):
    s = segs[idx - 1]
    for k in ("shots", "_lean_shots"):
        t = s.get(k) or ""
        orig = t
        for a, b in REPS:
            if a in t:
                t = t.replace(a, b, 1)
        if t != orig:
            s[k] = t
            print("  seg%02d [%s] 已改" % (idx, k))

with io.open(BEATS, "w", encoding="utf-8") as f:
    f.write(json.dumps(segs, ensure_ascii=False, indent=2))

# ══════════════════════════════════════════════════════════════
BAD = re.compile(r"nobody|no one|no other|never |duplicat|half of the frame|"
                 r"half of frame|each one holding|own third|third of the frame|"
                 r"on the centre axis", re.I)
print("\n===== 复查（seg01 故意保留，用户已验收）=====")
for i, s in enumerate(segs, 1):
    txt = " ".join(str(s.get(k) or "") for k in
                   ("shots", "lean_anchor", "_lean_shots", "summary", "soundscape"))
    hits = sorted(set(m.group(0) for m in BAD.finditer(txt)))
    tag = "（已验收，不动）" if i == 1 else ("干净" if not hits else hits)
    print("  seg%02d %s" % (i, tag))