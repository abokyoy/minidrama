# -*- coding: utf-8 -*-
"""按官方跑酷范本把正片五段统一重写（2026-10-08）。

用户要求（10:26）：
> 「官方的视频 非常有动感 镜头很快 分镜切换也很快 信息密度大很多」

官方范本要点（本项目此前全部没做到）：
- 10 秒 6 刀，每刀只做**一个**明确动作
- 每刀机位**都不同**（Static → Push In → Truck → Arc → Push In → Pull Out）
- 音效写到**毫秒**（a sharp breath at 2.6s）
- 配乐有**结构**（drone@0s → percussion@2s → cut@5.8s → pulse 回归）
- 结尾一段**逗号列出的具体风险否定**（官方范式，不是"零否定词"）
- 风格句带「keep ... consistent throughout」

⚠️ 铁律：
- 台词一字不改（CPS=3.2 钳位由渲染器负责）
- 零对称占比词（half of frame / own third / left-right）
- 胸前无文字
- 人数锁必须保留（check_beats 认 "the only people in it"）
- lean 档必须保留 "high-key brightness from edge to edge"（check_beats 认）
- ⚠️ 数据写进 **lean_shots**（渲染器第1128行读的是这个，不是 _lean_shots）
"""
import io
import json
import re

BEATS = "xs001_beats/scene11.json"
segs = json.load(io.open(BEATS, encoding="utf-8"))

# ══════════════════════════════════════════════════════════════
# 风格句 + 场景锚点：全片共用（官方范本的风格句写法）
# ══════════════════════════════════════════════════════════════
ANCHOR = (
    "The whole clip takes place in one small private office and the camera never leaves "
    "it. The room has four plain white walls, a grey metal filing cabinet along the far "
    "wall, a long wooden desk standing across the middle of the floor, venetian blinds on "
    "right-hand wall laying bright bands of light across the desk top, and a closed wooden "
    "door set flat into the back wall with a small silver handle. Bright mid-morning "
    "daylight fills the room. The walls behind the people are smooth painted plaster of one "
    "single light colour, unbroken from the skirting board up to the ceiling. All cardboard "
    "archive boxes and folders are plain brown corrugated cardboard. The people named in "
    "this beat are the only people in it: the manager stays behind the desk on the far side, "
    "the cleaner stays at the near end of it with her back to the camera, and the colleague "
    "stands where this beat places her. The count does not change."
)

# 官方范本的结尾约束段（逗号列出的具体风险否定）
GUARD = (
    "No slow-motion, no soft dissolves, no fades, no unnecessary transitions; "
    "use hard cuts only and no on-screen text, letters, logos, subtitles, or watermarks."
)

# ══════════════════════════════════════════════════════════════
# 各段 6 刀正文。台词原文一字不改。
# 机位序列对齐官方范本：Static → Push In → Truck → Arc → Push In → Pull Out
# ══════════════════════════════════════════════════════════════
SHOTS = {}

SHOTS[1] = (  # 撞门拍桌
    "[Shot 1] Static Shot, a medium two-shot inside the office: 钱经理 (S3) strides two paces "
    "in from the near end of the room, 小唐 (S4) one pace behind him, and he slams his palm "
    "flat on the long wooden desk; the grey metal filing cabinets fill the wall behind him.\n\n"
    "[Shot 2] At 00:02.000, Camera: Push In with small amplitude at slow speed, moving in on "
    "钱经理 (S3) as he leans his weight onto the desk and opens his mouth, speaking in a loud "
    "bullying nasal Mandarin: [Chinese] 三楼包厢。贵客丢了一只金耳钉。三万八。\n\n"
    "[Shot 3] At 00:04.200, Camera: Truck Right with medium amplitude at slow speed, swinging "
    "across the desk to a reverse single on 苏小满 (S1), the blind-laying light barring the "
    "wall behind her; she stands with her back to the camera and does not move her feet.\n\n"
    "[Shot 4] At 00:06.200, Camera: Arc Shot with medium amplitude at slow speed, curving "
    "around the near end of the desk as 苏小满 (S1) sets both hands flat on the desk top and "
    "slides the folder she was carrying onto it; 钱经理 (S3) watches the folder come down.\n\n"
    "[Shot 5] At 00:08.200, Camera: Push In with small amplitude at fast speed, closing in on "
    "the folder lying flat on the desk between them; both of their hands stay flat on the wood "
    "either side of it.\n\n"
    "[Shot 6] At 00:09.400, Camera: Pull Out with large amplitude at slow speed, revealing the "
    "whole office: 钱经理 (S3) still bearing down on the desk across from 苏小满 (S1), 小唐 (S4) "
    "standing clear of the desk end, the room very quiet.\n\n"
    "From [Shot 3] through [Shot 6] the only mouth movement in frame is the one line 钱经理 "
    "(S3) has already delivered in [Shot 2]; the office falls into room tone.\n\n"
    + GUARD
)

SHOTS[2] = (  # 点名（6 刀版）
    "[Shot 1] Static Shot, a medium two-shot across the desk: 钱经理 (S3) stands on the far "
    "side with the filing cabinets behind his back, one palm flat on the wood; 苏小满 (S1) "
    "stands at the near end with her back to the camera; 小唐 (S4) stands against the back "
    "wall at the far left of frame, waiting.\n\n"
    "[Shot 2] At 00:02.500, Camera: Push In with small amplitude at slow speed, moving in on "
    "钱经理 (S3) as he straightens up slowly, tucks both hands behind his back and tips his "
    "head to one side, fixing 苏小满 (S1) with the look of a man who has already decided. His "
    "mouth opens and he speaks in a flat accusing Mandarin: [Chinese] 收台的时候，就你一个人在。\n\n"
    "[Shot 3] At 00:05.000, Camera: Truck Right with medium amplitude at slow speed, swinging "
    "across the desk to a reverse single on 苏小满 (S1), the blind-laying light barring the "
    "wall behind her. She does not move her feet and does not look away, and she answers at "
    "once in a low steady Mandarin: [Chinese] 不是我。\n\n"
    "[Shot 4] At 00:07.000, Camera: Arc Shot with medium amplitude at slow speed, curving "
    "around the end of the desk as 钱经理 (S3) finishes the accusation and stops, and his eyes "
    "leave her; he turns his head and shoulders toward the left-hand wall. 苏小满 (S1) stays "
    "where she is, following him with her eyes.\n\n"
    "[Shot 5] At 00:08.500, Camera: Push In with small amplitude at fast speed, closing in on "
    "钱经理 (S3)'s face as he turns his head fully left and looks straight at 小唐 (S4) against "
    "the wall; the look lasts a beat and says everything. 小唐 (S4) sees it and pushes off the "
    "wall with her shoulder, taking the first step forward.\n\n"
    "[Shot 6] At 00:09.400, Camera: Pull Out with large amplitude at slow speed, revealing the "
    "whole office as 钱经理 (S3) gives one short jerk of his chin toward the open floor beside "
    "the desk. 苏小满 (S1) has gone very still, watching the colleague approach.\n\n"
    "From [Shot 4] through [Shot 6] the only mouth movement in frame is 钱经理 (S3) swallowing; "
    "every line of dialogue has already finished, and the office falls into room tone.\n\n"
    + GUARD
)

SHOTS[3] = (  # 小唐作证
    "[Shot 1] Static Shot, a medium three-shot: 钱经理 (S3) stands behind the desk facing the "
    "camera with one palm flat on the wood; 小唐 (S4) stands on the open floor beside the "
    "desk, a pace in from its near end, her hands folded low; 苏小满 (S1) stands at the near end "
    "of that desk with her back to the camera.\n\n"
    "[Shot 2] At 00:02.400, Camera: Push In with small amplitude at slow speed, moving in on "
    "钱经理 (S3)'s face as he finishes looking at 小唐 (S4) and turns his eyes to her face, "
    "waiting; he lifts one hand off the desk and turns it over, palm up, a short beckoning "
    "motion. His mouth stays shut through it.\n\n"
    "[Shot 3] At 00:04.600, Camera: Truck Right with medium amplitude at slow speed, swinging "
    "to a closer single on 小唐 (S4) standing on the open floor: she draws her shoulders up, "
    "keeps her eyes on the floor tiles and lets them flick once toward 苏小满 (S1), then away, "
    "and she speaks in a small thin nervous Mandarin: [Chinese] 钱经理。中午，我看见她往兜里塞东西。没看清。\n\n"
    "[Shot 4] At 00:07.400, Camera: Arc Shot with medium amplitude at slow speed, curving from "
    "小唐 (S4) around to 苏小满 (S1) at the near end of the desk, showing the distance between "
    "the two of them across the open floor.\n\n"
    "[Shot 5] At 00:08.800, Camera: Push In with small amplitude at fast speed, closing in on "
    "苏小满 (S1)'s face as she turns her head a few degrees toward 小唐 (S4) and holds there, "
    "her jaw setting.\n\n"
    "[Shot 6] At 00:09.500, Camera: Pull Out with large amplitude at slow speed, revealing all "
    "three of them in the office: the manager behind the desk, the colleague on the open floor, "
    "the cleaner at the near end of the desk with her back turned. Nobody moves.\n\n"
    "From [Shot 4] through [Shot 6] the only mouth movement in frame is 小唐 (S4) finishing the "
    "one line she has already delivered; the office falls into room tone.\n\n"
    + GUARD
)

SHOTS[4] = (  # 看清楚了再说
    "[Shot 1] Static Shot, a medium two-shot across the desk: 钱经理 (S3) stands on the far "
    "side facing the camera, 苏小满 (S1) at the near end with her back to the camera, the "
    "filing cabinets directly behind him.\n\n"
    "[Shot 2] At 00:02.200, Camera: Push In with small amplitude at slow speed, moving in on "
    "钱经理 (S3) as he plants both palms on the desk and leans forward; his mouth opens and he "
    "speaks in a loud nasal Mandarin: [Chinese] 你今天把话说清楚。\n\n"
    "[Shot 3] At 00:04.400, Camera: Truck Right with medium amplitude at slow speed, swinging "
    "across the desk to a reverse single on 苏小满 (S1), the blind-laying light barring the wall "
    "behind her. She turns her head and shoulders toward 小唐 (S4) off to the left of frame and "
    "speaks quietly in a low steady Mandarin: [Chinese] 小唐。看清楚了，再说。\n\n"
    "[Shot 4] At 00:06.800, Camera: Arc Shot with medium amplitude at slow speed, curving "
    "around the desk end toward 小唐 (S4), who takes one small step and then stops.\n\n"
    "[Shot 5] At 00:08.200, Camera: Push In with small amplitude at fast speed, closing in on "
    "小唐 (S4)'s face as her eyes drop to the floor and her shoulders come up.\n\n"
    "[Shot 6] At 00:09.400, Camera: Pull Out with large amplitude at slow speed, revealing the "
    "three of them holding their positions across the office floor, all of them very still.\n\n"
    "From [Shot 4] through [Shot 6] no mouth moves in frame; every line has already been "
    "delivered, and the office falls into room tone.\n\n"
    + GUARD
)

SHOTS[5] = (  # 掏兜
    "[Shot 1] Static Shot, a medium two-shot across the desk: 钱经理 (S3) stands on the far side "
    "with one palm flat on the wood; 苏小满 (S1) stands at the near end with her back to the "
    "camera; 小唐 (S4) stands clear at the far left of frame near the back wall.\n\n"
    "[Shot 2] At 00:02.200, Camera: Push In with small amplitude at slow speed, moving in on "
    "钱经理 (S3) as he turns his palm up over the desk in a flat demanding gesture and speaks in "
    "a loud nasal Mandarin: [Chinese] 兜掏出来。\n\n"
    "[Shot 3] At 00:04.200, Camera: Truck Right with medium amplitude at slow speed, swinging "
    "across to a closer single on 苏小满 (S1) at the near end of the desk; her hands stay at her "
    "own waist and she does not step forward.\n\n"
    "[Shot 4] At 00:06.000, Camera: Arc Shot with medium amplitude at slow speed, curving to "
    "show the open floor between 钱经理 (S3) and 苏小满 (S1), the distance neither of them "
    "crosses.\n\n"
    "[Shot 5] At 00:07.800, Camera: Push In with small amplitude at fast speed, closing in on "
    "苏小满 (S1)'s hands at her waist as her fingers go into her apron pocket and come out with "
    "a small folded paper, which she lays flat on the desk.\n\n"
    "[Shot 6] At 00:09.400, Camera: Pull Out with large amplitude at slow speed, revealing the "
    "whole office: the folded paper lying flat on the desk between the two of them, and 小唐 (S4) "
    "still standing clear at the far left of frame. Nobody moves.\n\n"
    "From [Shot 3] through [Shot 6] no mouth moves in frame; every line has already been "
    "delivered, and the office falls into room tone.\n\n"
    + GUARD
)

# ══════════════════════════════════════════════════════════════
# 音效：写到毫秒（官方范式）
# ══════════════════════════════════════════════════════════════
SOUND = {
    1: ("A clock ticking on the wall and the low hum of the ceiling lights throughout; one "
        "sharp heel strike at 0.3s as 钱经理 strides in; a flat palm slap on the desk top at "
        "1.2s; the scrape of a folder sliding across wood at 7.0s; room tone returns at 9.4s.",
        "A low sustained string drone enters at 0s, a single wood-block knock lands with the "
        "palm slap at 1.2s, and the track thins to one held note from 8.2s onward."),
    2: ("A clock ticking on the wall and the low hum of the ceiling lights throughout; a short "
        "inhale from 钱经理 at 2.3s before he speaks; one nervous swallow from 小唐 at 8.5s; the "
        "soft scrape of a shoe on the floor at 9.0s as she steps forward.",
        "A low sustained string drone begins at 0s and thins to a single held note from 8.5s, "
        "ending on a short cello pulse as the colleague steps forward."),
    3: ("A clock ticking on the wall and the low hum of the ceiling lights throughout; a small "
        "clearing of throat from 小唐 at 4.4s before she speaks; one sharp breath from 苏小满 at "
        "8.6s; room tone settles at 9.5s.",
        "A low sustained string drone begins at 0s, a single muted piano note enters at 2.4s "
        "when the manager beckons, and the track thins from 8.8s to one held note."),
    4: ("A clock ticking on the wall and the low hum of the ceiling lights throughout; a hard "
        "knuckle tap on the desk top at 2.0s; one small shoe step at 6.8s; room tone returns at "
        "9.4s.",
        "A low sustained string drone begins at 0s, a single wood-block knock lands at 2.0s with "
        "the knuckle tap, and one held cello note sustains from 8.2s."),
    5: ("A clock ticking on the wall and the low hum of the ceiling lights throughout; a short "
        "sharp breath from 苏小满 at 5.0s; the soft paper friction of a folded sheet at 7.8s as "
        "it comes out of the apron pocket; room tone settles at 9.4s.",
        "A low sustained string drone begins at 0s and thins to a single held note from 7.8s, "
        "ending on one short cello pulse as the paper is laid down."),
}

# ══════════════════════════════════════════════════════════════
# 写入：⚠️ 关键 —— 渲染器读的是 lean_shots，不是 _lean_shots
# ══════════════════════════════════════════════════════════════
for i, s in enumerate(segs, 1):
    s["lean_anchor"] = ANCHOR
    s["lean_shots"] = SHOTS[i]
    s["_lean_shots"] = SHOTS[i]          # 同步留档（旧工具可能读它）
    s["anchor"] = ANCHOR                 # 非lean 分支兜底
    s["shots"] = SHOTS[i]                # check_beats 读这个
    s["soundscape"], s["music"] = SOUND[i]

with io.open(BEATS, "w", encoding="utf-8") as f:
    f.write(json.dumps(segs, ensure_ascii=False, indent=2))

# ══════════════════════════════════════════════════════════════
# 自查
# ══════════════════════════════════════════════════════════════
print("段  刀数  机位种  正文字数  音效落点  约束段")
for i, s in enumerate(segs, 1):
    ls = s["lean_shots"]
    n = len(set(re.findall(r"\[Shot (\d+)\]", ls)))
    cams = re.findall(r"Camera: ([A-Z][a-zA-Z ]+?) with", ls)
    ss = s["soundscape"]
    hits = len(re.findall(r"at \d+\.\ds", ss))
    print("seg%02d  %2d   %2d     %4d      %d      %d"
          % (i, n, len(set(c.strip() for c in cams)), len(ls.split()), hits,
             len(re.findall(r"No ", ls))))
print()
# 台词原文必须一字不差
KEEP = {
    1: ["三楼包厢。贵客丢了一只金耳钉。三万八。"],
    2: ["收台的时候，就你一个人在。", "不是我。"],
    3: ["钱经理。中午，我看见她往兜里塞东西。没看清。"],
    4: ["你今天把话说清楚。", "小唐。看清楚了，再说。"],
    5: ["兜掏出来。"],
}
print("台词原样核对：")
ok = True
for i, s in enumerate(segs, 1):
    for line in KEEP[i]:
        hit = ("[Chinese] " + line) in s["lean_shots"]
        ok = ok and hit
        if not hit:
            print("  ❌ seg%02d 缺/改: %s" % (i, line))
print("  全部 %d 句一字未改：%s" % (sum(len(v) for v in KEEP.values()), "是" if ok else "否"))
print()
BAD = re.compile(r"\bnobody\b|\bno one\b|\bno other\b|half of (?:the )?frame|"
                 r"each one holding|own third|third of the frame|centre axis|"
                 r"left half of|right half of|duplicat", re.I)
for i, s in enumerate(segs, 1):
    body = s["lean_shots"]
    main = re.split(r"No slow-motion", body)[0]
    h = sorted(set(m.group(0) for m in BAD.finditer(main)))
    print("  seg%02d 正文否定/对称词: %s" % (i, h or "干净"))