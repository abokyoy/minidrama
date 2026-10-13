# -*- coding: utf-8 -*-
"""seg02 按官方范本重写：6刀 / 每刀不同机位 / 音效到毫秒 / 配乐有结构 / 结尾约束段。

起因（用户 2026-10-08 10:26 原话）：
> 「我看官方的视频 非常有动感 镜头很快 分镜切换也很快 信息密度大很多」

并修正两个诊断出来的病灶：
1. lean_anchor 373 词（其他段只有 102）→ `_fix_corridor.py` 清走廊词时
   追加正面锚点，**追加成了两遍**：「灰色文件柜+木桌+百叶窗」重复。
2. 原 4 刀、无机位、无音效时间点、无配乐结构、无约束段。

参照：官方跑酷范本（10秒6刀，每刀不同机位，音效到毫秒，结尾约束段）。
⛔ 铁律三条：不许用否定句代替正面描述、零对称占比、胸前无文字。
   （结尾约束段是官方范式，允许写具体风险否定，但必须是可观测的。）
"""
import io
import json
import re

BEATS = "xs001_beats/scene11.json"
segs = json.load(io.open(BEATS, encoding="utf-8"))
s = segs[1]

# ══════════════════════════════════════════════════════════════
# 1. lean_anchor 瘦身：373 → 约 110 词
#    删掉重复的第二遍房间描述 + 逐句人物站位（站位属于镜头，属于 _lean_shots）
# ══════════════════════════════════════════════════════════════
NEW_LEAN_ANCHOR = (
    "The whole clip takes place in one small private office and the camera never "
    "leaves it. The room has four plain white walls, a grey metal filing cabinet "
    "along the far wall, a long wooden desk standing across the middle of the floor, "
    "venetian blinds on the right-hand wall laying bright bands of light across the "
    "desk top and the floor, and a closed wooden door set flat into the back wall with "
    "a small silver handle. Bright mid-morning daylight fills the room and every "
    "surface reads clearly."
)
s["lean_anchor"] = NEW_LEAN_ANCHOR

# ══════════════════════════════════════════════════════════════
# 2. _lean_shots 重写：4 刀 → 6 刀，每刀不同机位，台词时序不变
#    官方跑酷范本机位序列：Static → Push In → Arc → Tilt Up → Push In → Pull Out
#    台词「收台的时候，就你一个人在。」→「不是我。」必须一字不改
# ══════════════════════════════════════════════════════════════
NEW_LEAN_SHOTS = (
    "[Shot 1] Static Shot, a medium two-shot across the desk: 钱经理 (S3) stands on the "
    "far side of the desk with the grey filing cabinets directly behind his back, facing "
    "the camera, one palm flat on the desk; 苏小满 (S1) stands at the near end of that "
    "desk with her back to the camera and a plain stretch of white wall behind her, "
    "facing him; 小唐 (S4) stands against the back wall at the far left of frame, her "
    "shoulder blade on the white paint, waiting where she has been standing.\n\n"
    "[Shot 2] At 00:02.500, Camera: Push In with small amplitude at slow speed, moving "
    "in on 钱经理 (S3) as he straightens up slowly, tucks both hands behind his back and "
    "tips his head to one side, fixing 苏小满 (S1) with the look of a man who has already "
    "decided. His mouth opens and he speaks in a flat accusing Mandarin, one phrase at a "
    "time: [Chinese] 收台的时候，就你一个人在。\n\n"
    "[Shot 3] At 00:05.000, Camera: Truck Right with medium amplitude at slow speed, "
    "swinging across the desk to a reverse single on 苏小满 (S1), the blind-laying light "
    "barring the wall behind her. She does not move her feet and does not look away, and "
    "she answers at once in a low steady Mandarin: [Chinese] 不是我。\n\n"
    "[Shot 4] At 00:07.000, Camera: Arc Shot with medium amplitude at slow speed, "
    "curving around the end of the desk as 钱经理 (S3) finishes the accusation and stops, "
    "and his eyes leave her. He turns his head and shoulders away from the desk toward the "
    "left-hand wall of the room. 苏小满 (S1) stays where she is at the near end of the "
    "desk, following him with her eyes.\n\n"
    "[Shot 5] At 00:08.500, Camera: Push In with small amplitude at fast speed, closing "
    "in on 钱经理 (S3)'s face as he turns his head fully to the left and looks straight at "
    "小唐 (S4) against the wall. The look lasts a beat and says everything. His lips stay "
    "closed through it. 小唐 (S4) sees it and pushes off the wall with her shoulder, taking "
    "the first step forward into the room.\n\n"
    "[Shot 6] At 00:09.400, Camera: Pull Out with large amplitude at slow speed, "
    "revealing the whole office as 钱经理 (S3) gives one short jerk of his chin toward the "
    "open floor beside the desk. 苏小满 (S1) has gone very still at the near end of the "
    "desk, watching the colleague approach. The room is quiet.\n\n"
    "Both people at the desk keep their mouths closed through [Shot 4], [Shot 5] and "
    "[Shot 6], speaking no dialogue. No slow-motion, no soft dissolves, no fades, no "
    "unnecessary transitions; use hard cuts only and no on-screen text, letters, logos, "
    "subtitles, or watermarks."
)
s["_lean_shots"] = NEW_LEAN_SHOTS

# ══════════════════════════════════════════════════════════════
# 3. soundscape 加时间点（官方范式：a sharp breath at 2.6s）
#    台词时序不动，只补音效落点
# ══════════════════════════════════════════════════════════════
s["soundscape"] = (
    "A clock ticking on the wall, the low hum of the ceiling lights throughout; a sharp "
    "intake of breath from 钱经理 at 2.5s before he speaks; one nervous swallow from 小唐 "
    "at 8.5s; the soft scrape of a shoe on the floor at 9.0s as she steps forward."
)
s["music"] = (
    "A low sustained string drone begins at 0s and thins to a single held note from 8.5s, "
    "ending on a short cello pulse as the colleague steps forward."
)

# ══════════════════════════════════════════════════════════════
# 4. retention 去说话人编号（官方规定 retention 内不得出现 (Sx)）
# ══════════════════════════════════════════════════════════════
s["retention"] = {
    "qianjingli": "fully_preserved - his slicked-back oily hair, round face and dark grey "
                  "buttoned waistcoat over a white shirt are retained in every shot.",
    "suxiaoman": "fully_preserved - her centre-parted black hair in a low practical ponytail, "
                 "dark navy button-up work shirt and worn grey apron are retained in every shot.",
    "xiaotang": "fully_preserved - her hair tied back in a low ponytail, light-grey work shirt "
                "and light-grey apron are retained in every shot.",
}

with io.open(BEATS, "w", encoding="utf-8") as f:
    f.write(json.dumps(segs, ensure_ascii=False, indent=2))

# ══════════════════════════════════════════════════════════════
# 5. 复查：三条铁律 + 官方规范
# ══════════════════════════════════════════════════════════════
print("改后 seg02:")
print("  lean_anchor   %d 词" % len(s["lean_anchor"].split()))
print("  _lean_shots   %d 词" % len(s["_lean_shots"].split()))
print("  合计          %d 词（官方范本 ~560，其他段 ~250）"
      % (len(s["lean_anchor"].split()) + len(s["_lean_shots"].split())))
print("  refs          %s" % s["refs"])
print()

txt = " ".join(str(s.get(k) or "") for k in
               ("shots", "_lean_shots", "lean_anchor", "anchor", "summary", "soundscape"))
print("===== 铁律复查 =====")
# 正文区禁否定词；官方约束段允许 specific risk negatives
main = txt.split("No slow-motion")[0]
BAD = re.compile(r"\bnobody\b|\bno one\b|\bno other\b|never |duplicat|"
                 r"half of (?:the )?frame|each one holding|own third|"
                 r"third of the frame|centre axis|\bempty\b|\bnot\b", re.I)
hits = sorted(set(m.group(0) for m in BAD.finditer(main)))
print("  正文否定词/对称词:", hits or "干净")
CUT = re.compile(r"At (\d\d:\d\d\.\d\d\d)", txt)
cuts = CUT.findall(txt)
print("  切点:", cuts, "递增:", cuts == sorted(cuts))
CAM = re.findall(r"Camera: ([A-Z][a-zA-Z ]+?) with (?:small|medium|large) amplitude"
                 r"(?: at (?:slow|fast) speed)?", txt)
print("  机位 %d 刀 / %d 种" % (len(CAM), len(set(c[0].strip() for c in CAM))))
for c in CAM:
    print("      ", " ".join(c))
print("  台词原样:", "[Chinese] 收台的时候，就你一个人在。" in txt
      and "[Chinese] 不是我。" in txt)
print("  retention 含 (Sx):", bool(re.search(r"\(S\d\)", json.dumps(s["retention"], ensure_ascii=False))))