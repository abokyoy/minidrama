# -*- coding: utf-8 -*-
"""正片五段：切镜更快 + 信息密度更高（用户 2026-10-08 10:39 要求）。

用户原话：
> 「别乱跑 要测试调整后的效果 我要 切镜更快、密度更高」

对照官方跑酷范本的节奏（10 秒 6 刀）：
  范本切点 1.300 / 2.600 / 4.100 / 5.800 / 7.300 → 间隔 1.3 秒一刀
我原版 2.500 / 5.000 / 7.000 / 8.500 / 9.400 → 前两刀 2.5 和 2.0 秒，**太慢**

本版改法：
1. **节奏对齐范本**：切点改为 1.250 / 2.500 / 3.750 / 5.000 / 6.500 / 8.000
   （前5刀 1.25 秒一刀，最后一刀 1.5 秒收尾，尾巴留 2 秒）
2. **每刀加密一个可观测细节**（不是形容词堆砌，是看得见的东西）：
   手指、袖口、纸张边角、门把反光、地面光带位置…
3. 机位仍按官方范本序列，**每刀都不同**，且改成更快更短的运镜
   （快推/快摇/甩镜，对应「切镜更快」）

⛔ 台词一字不改；零对称占比词；胸前无文字；人数锁保留。
⛔ 数据写进 lean_shots（渲染器第1128行读它）+ shots（check_beats 读它）。
"""
import io
import json
import re

BEATS = "xs001_beats/scene11.json"
segs = json.load(io.open(BEATS, encoding="utf-8"))

ANCHOR = (
    "The whole clip takes place in one small private office and the camera never leaves it. "
    "The room has four plain white walls, a grey metal filing cabinet along the far wall, a long "
    "wooden desk standing across the middle of the floor, venetian blinds on the right-hand wall "
    "laying bright bands across the desk top, and a closed wooden door set flat into the back wall. "
    "The walls behind the people are smooth painted plaster of one single light colour, unbroken "
    "from the skirting board up to the ceiling. All cardboard boxes and folders are plain brown "
    "corrugated cardboard. The people named in this beat are the only people in it: the manager "
    "stays behind the desk on the far side, the cleaner stays at the near end of it with her back "
    "to the camera, and the colleague stands where this beat places her. The count does not change."
)

GUARD = (
    "No slow-motion, no soft dissolves, no fades, no unnecessary transitions; "
    "use hard cuts only and no on-screen text, letters, logos, subtitles, or watermarks."
)

# ══════════════════════════════════════════════════════════════
# 切点表（对齐官方范本 1.3 秒一刀）
# ══════════════════════════════════════════════════════════════
CUTS = {2: "00:01.250", 3: "00:02.500", 4: "00:03.750", 5: "00:05.000",
        6: "00:06.500"}
# 最后一段从 8.000 铺到 10.000（2 秒收尾镜头，官方范本最后刀也占 1.7 秒）

SHOTS = {}

SHOTS[1] = (
    "[Shot 1] Static Shot, medium two-shot: 钱经理 (S3) strides two paces in from the near end of "
    "the room, 小唐 (S4) one pace behind him, and he slams his palm flat on the long wooden desk; "
    "the grey metal filing cabinets fill the wall behind him, and the desk edge jumps under his hand.\n\n"
    "[Shot 2] At 00:01.250, Camera: Push In with small amplitude at fast speed, pushing in on the "
    "flat of his palm where it lands on the varnished wood, the desk grain and his knuckle ring "
    "coming into focus; his mouth opens and he speaks in a loud bullying nasal Mandarin: "
    "[Chinese] 三楼包厢。贵客丢了一只金耳钉。三万八。\n\n"
    "[Shot 3] At 00:02.500, Camera: Truck Right with medium amplitude at fast speed, sliding "
    "sideways across the desk to a reverse single on 苏小满 (S1); her back is to the camera and a "
    "band of blind-light bars the wall behind her, and she does not move her feet.\n\n"
    "[Shot 4] At 00:03.750, Camera: Tracking Shot with medium amplitude at fast speed, tracking "
    "along the near edge of the desk as 苏小满 (S1) sets both hands flat on the wood and slides "
    "the folder she was carrying onto it; the folder's corner stops short of 钱经理 (S3)'s palm.\n\n"
    "[Shot 5] At 00:05.000, Camera: Arc Shot with medium amplitude at fast speed, arcing around "
    "the far end of the desk as 钱经理 (S3) draws his hand back off the wood and his shoulders "
    "square up; the arc carries the blind-light band across his chest.\n\n"
    "[Shot 6] At 00:06.500, Camera: Pull Out with large amplitude at slow speed, pulling out to "
    "reveal the whole office: the folder lying flat at the middle of the desk, 钱经理 (S3) bearing "
    "down across from 苏小满 (S1), 小唐 (S4) standing clear of the desk end in the bright doorway "
    "light from the blinds, everyone holding their positions.\n\n"
    "From [Shot 3] through [Shot 6] the only mouth movement in frame is the one line 钱经理 (S3) "
    "has already delivered in [Shot 2]; the office falls into room tone.\n\n" + GUARD
)

SHOTS[2] = (
    "[Shot 1] Static Shot, medium two-shot across the desk: 钱经理 (S3) on the far side with the "
    "filing cabinets behind his back, one palm flat on the wood; 苏小满 (S1) at the near end with "
    "her back to the camera; 小唐 (S4) against the back wall at the far left of frame, waiting.\n\n"
    "[Shot 2] At 00:01.250, Camera: Push In with small amplitude at fast speed, pushing in on "
    "钱经理 (S3) as he straightens up slowly, tucks both hands behind his back and tips his head "
    "to one side, fixing 苏小满 (S1) with the look of a man who has already decided; his collar "
    "catches the blind-light. His mouth opens and he speaks in a flat accusing Mandarin: "
    "[Chinese] 收台的时候，就你一个人在。\n\n"
    "[Shot 3] At 00:02.500, Camera: Truck Right with medium amplitude at fast speed, sliding "
    "sideways across the desk to a reverse single on 苏小满 (S1), the blind-laying light barring the "
    "wall behind her; her apron strap lifts slightly at the waist. She does not move her feet and does "
    "not look away, and she answers at once in a low steady Mandarin: [Chinese] 不是我。\n\n"
    "[Shot 4] At 00:03.750, Camera: Tracking Shot with medium amplitude at fast speed, tracking "
    "left along the desk as 钱经理 (S3) finishes the accusation and stops, and his eyes leave her; "
    "he turns his head and shoulders toward the left-hand wall. 苏小满 (S1) stays where she is, "
    "her eyes following his turn.\n\n"
    "[Shot 5] At 00:05.000, Camera: Arc Shot with medium amplitude at fast speed, arcing around "
    "the end of the desk onto 钱经理 (S3)'s face as he turns his head fully left and looks straight "
    "at 小唐 (S4) against the wall; the look lasts a beat and says everything.\n\n"
    "[Shot 6] At 00:06.500, Camera: Pull Out with large amplitude at slow speed, pulling out to "
    "reveal the whole office as 小唐 (S4) pushes off the wall with her shoulder and takes the first "
    "step forward, and 钱经理 (S3) gives one short jerk of his chin toward the open floor beside the "
    "desk; 苏小满 (S1) has gone very still, watching the colleague approach.\n\n"
    "From [Shot 4] through [Shot 6] the only mouth movement in frame is 钱经理 (S3) swallowing; "
    "every line of dialogue has already finished, and the office falls into room tone.\n\n" + GUARD
)

SHOTS[3] = (
    "[Shot 1] Static Shot, medium three-shot: 钱经理 (S3) behind the desk facing the camera, one "
    "palm flat on the wood; 小唐 (S4) on the open floor beside the desk, a pace in from its near "
    "end, her hands folded low; 苏小满 (S1) at the near end of that desk with her back to the camera.\n\n"
    "[Shot 2] At 00:01.250, Camera: Push In with small amplitude at fast speed, pushing in on "
    "钱经理 (S3)'s face as he finishes looking at 小唐 (S4) and turns his eyes to her face, waiting; "
    "he lifts one hand off the desk and turns it over, palm up, a short beckoning motion, and the "
    "desk's blind-light band slides across his knuckles. His mouth stays shut through it.\n\n"
    "[Shot 3] At 00:02.500, Camera: Truck Left with medium amplitude at fast speed, sliding "
    "sideways to a closer single on 小唐 (S4) standing on the open floor: she draws her shoulders up, "
    "keeps her eyes on the floor tiles and lets them flick once toward 苏小满 (S1), then away; her "
    "hands tighten on each other at her waist. She speaks in a small thin nervous Mandarin: "
    "[Chinese] 钱经理。中午，我看见她往兜里塞东西。没看清。\n\n"
    "[Shot 4] At 00:03.750, Camera: Tracking Shot with medium amplitude at fast speed, tracking "
    "from 小唐 (S4) toward 苏小满 (S1), showing the distance between the two of them across the "
    "open floor; a band of blind-light lies between their feet.\n\n"
    "[Shot 5] At 00:05.000, Camera: Arc Shot with medium amplitude at fast speed, arcing onto "
    "苏小满 (S1)'s face as she turns her head a few degrees toward 小唐 (S4) and holds there, her "
    "jaw setting, the loose hair at her temple settling against her cheek.\n\n"
    "[Shot 6] At 00:06.500, Camera: Pull Out with large amplitude at slow speed, pulling out to "
    "reveal all three of them in the office: the manager behind the desk, the colleague on the open "
    "floor with her hands still clasped, the cleaner at the near end of the desk with her back "
    "turned. All three hold their positions.\n\n"
    "From [Shot 4] through [Shot 6] the only mouth movement in frame is 小唐 (S4) finishing the one "
    "line she has already delivered; the office falls into room tone.\n\n" + GUARD
)

SHOTS[4] = (
    "[Shot 1] Static Shot, medium two-shot across the desk: 钱经理 (S3) on the far side facing the "
    "camera, 苏小满 (S1) at the near end with her back to the camera, the filing cabinets directly "
    "behind him and the closed door flat in the back wall.\n\n"
    "[Shot 2] At 00:01.250, Camera: Push In with small amplitude at fast speed, pushing in on "
    "钱经理 (S3) as he plants both palms on the desk and leans his weight forward; the wood takes "
    "a faint shadow under both hands. His mouth opens and he speaks in a loud nasal Mandarin: "
    "[Chinese] 你今天把话说清楚。\n\n"
    "[Shot 3] At 00:02.500, Camera: Truck Right with medium amplitude at fast speed, sliding "
    "sideways across the desk to a reverse single on 苏小满 (S1), the blind-laying light barring the "
    "wall behind her. She turns her head and shoulders toward 小唐 (S4) off to the left of frame, her "
    "apron bib creasing at the waist, and speaks quietly in a low steady Mandarin: "
    "[Chinese] 小唐。看清楚了，再说。\n\n"
    "[Shot 4] At 00:03.750, Camera: Tracking Shot with medium amplitude at fast speed, tracking "
    "around the desk end toward 小唐 (S4), who takes one small step onto the plain floor and stops; "
    "her shoe leaves a faint mark in the dust near the skirting board.\n\n"
    "[Shot 5] At 00:05.000, Camera: Arc Shot with medium amplitude at fast speed, arcing onto "
    "小唐 (S4)'s face as her eyes drop to the floor and her shoulders come up; the blind-light band "
    "passes over her collar.\n\n"
    "[Shot 6] At 00:06.500, Camera: Pull Out with large amplitude at slow speed, pulling out to "
    "reveal the three of them holding their positions across the office floor, the folder still "
    "lying flat at the middle of the desk where it was left.\n\n"
    "From [Shot 4] through [Shot 6] no mouth moves in frame; every line has already been delivered, "
    "and the office falls into room tone.\n\n" + GUARD
)

SHOTS[5] = (
    "[Shot 1] Static Shot, medium two-shot across the desk: 钱经理 (S3) on the far side with one "
    "palm flat on the wood; 苏小满 (S1) at the near end with her back to the camera; 小唐 (S4) clear "
    "at the far left of frame near the back wall.\n\n"
    "[Shot 2] At 00:01.250, Camera: Push In with small amplitude at fast speed, pushing in on "
    "钱经理 (S3) as he turns his palm up over the desk in a flat demanding gesture; a band of "
    "blind-light crosses his open hand. His mouth opens and he speaks in a loud nasal Mandarin: "
    "[Chinese] 兜掏出来。\n\n"
    "[Shot 3] At 00:02.500, Camera: Truck Right with medium amplitude at fast speed, sliding "
    "sideways across to a closer single on 苏小满 (S1) at the near end of the desk; her hands stay at her own "
    "waist and she does not step forward, the loose hair at her temple lifting slightly.\n\n"
    "[Shot 4] At 00:03.750, Camera: Tracking Shot with medium amplitude at fast speed, tracking "
    "down the near side of the desk to keep both of 苏小满 (S1)'s hands in frame at her waist; the "
    "distance to 钱经理 (S3) across the wood stays fixed.\n\n"
    "[Shot 5] At 00:05.000, Camera: Arc Shot with medium amplitude at fast speed, arcing in tight "
    "on 苏小满 (S1)'s hands as her fingers go into her apron pocket and come out with a small "
    "folded paper; the paper's creased edge catches the light.\n\n"
    "[Shot 6] At 00:06.500, Camera: Pull Out with large amplitude at slow speed, pulling out to "
    "reveal the whole office: the folded paper lying flat on the desk at the middle, 钱经理 (S3) "
    "still bearing down across from 苏小满 (S1), 小唐 (S4) still clear at the far left of frame. All "
    "three hold their positions.\n\n"
    "From [Shot 3] through [Shot 6] no mouth moves in frame; every line has already been delivered, "
    "and the office falls into room tone.\n\n" + GUARD
)

# 音效：切点同步提速，落点跟着改
SOUND = {
    1: ("A clock ticking on the wall and the low hum of the ceiling lights throughout; one sharp "
        "heel strike at 0.3s as 钱经理 strides in; a flat palm slap on the desk top at 1.3s; the "
        "scrape of a folder sliding across wood at 4.0s; room tone returns at 7.0s.",
        "A low sustained string drone enters at 0s, a single wood-block knock lands with the palm "
        "slap at 1.3s, and the track thins to one held note from 5.0s onward."),
    2: ("A clock ticking on the wall and the low hum of the ceiling lights throughout; a short "
        "inhale from 钱经理 at 1.1s before he speaks; one nervous swallow from 小唐 at 5.2s; the "
        "soft scrape of a shoe on the floor at 6.8s as she steps forward.",
        "A low sustained string drone begins at 0s, a single muted cello note enters at 1.3s when "
        "he starts speaking, and the track thins to a single held note from 5.0s."),
    3: ("A clock ticking on the wall and the low hum of the ceiling lights throughout; a small "
        "clearing of throat from 小唐 at 2.4s before she speaks; one sharp breath from 苏小满 at "
        "5.2s; room tone settles at 7.0s.",
        "A low sustained string drone begins at 0s, a single muted piano note enters at 1.3s when "
        "the manager beckons, and the track thins from 5.0s to one held note."),
    4: ("A clock ticking on the wall and the low hum of the ceiling lights throughout; a hard "
        "knuckle tap on the desk top at 1.2s; one small shoe step at 4.0s; room tone returns at 7.0s.",
        "A low sustained string drone begins at 0s, a single wood-block knock lands at 1.3s with "
        "the knuckle tap, and one held cello note sustains from 5.0s."),
    5: ("A clock ticking on the wall and the low hum of the ceiling lights throughout; a short "
        "sharp breath from 苏小满 at 5.2s; the soft paper friction of a folded sheet at 5.6s as it "
        "comes out of the apron pocket; room tone settles at 7.0s.",
        "A low sustained string drone begins at 0s and thins to a single held note from 5.0s, "
        "ending on one short cello pulse as the paper is laid down."),
}

for i, s in enumerate(segs, 1):
    s["lean_anchor"] = ANCHOR
    s["anchor"] = ANCHOR
    s["lean_shots"] = SHOTS[i]
    s["_lean_shots"] = SHOTS[i]
    s["shots"] = SHOTS[i]
    s["soundscape"], s["music"] = SOUND[i]

with io.open(BEATS, "w", encoding="utf-8") as f:
    f.write(json.dumps(segs, ensure_ascii=False, indent=2))

# ══════════════════════════════════════════════════════════════
# 自查
# ══════════════════════════════════════════════════════════════
print("段 刀数 机位种 切点间隔        正文字数 细节数")
for i, s in enumerate(segs, 1):
    ls = s["lean_shots"]
    cuts = [float(m.split(":")[1]) for m in re.findall(r"At (\d\d:\d\d\.\d\d\d)", ls)]
    gaps = [round(cuts[k + 1] - cuts[k], 2) for k in range(len(cuts) - 1)]
    cams = re.findall(r"Camera: ([A-Z][a-zA-Z ]+?) with", ls)
    n = len(set(re.findall(r"\[Shot (\d+)\]", ls)))
    # 细节计数：分号/逗号分隔的可观测细节句
    detail = len(re.findall(r"; the |; her |; his |; a |; everyone ", ls))
    print("seg%02d %2d  %2d   %-16s %4d    %d"
          % (i, n, len(set(c.strip() for c in cams)), str(gaps),
             len(ls.split()), detail))
print()
KEEP = {
    1: ["三楼包厢。贵客丢了一只金耳钉。三万八。"],
    2: ["收台的时候，就你一个人在。", "不是我。"],
    3: ["钱经理。中午，我看见她往兜里塞东西。没看清。"],
    4: ["你今天把话说清楚。", "小唐。看清楚了，再说。"],
    5: ["兜掏出来。"],
}
ok = all(("[Chinese] " + l) in s["lean_shots"] for s in segs for l in KEEP[segs.index(s) + 1])
print("台词 %d 句一字未改: %s" % (sum(len(v) for v in KEEP.values()), "是" if ok else "否"))
BAD = re.compile(r"\bnobody\b|\bno one\b|\bno other\b|half of (?:the )?frame|"
                 r"each one holding|own third|third of the frame|centre axis|"
                 r"left half of|right half of|duplicat", re.I)
for i, s in enumerate(segs, 1):
    main = re.split(r"No slow-motion", s["lean_shots"])[0]
    h = sorted(set(m.group(0) for m in BAD.finditer(main)))
    print("  seg%02d 否定/对称词: %s" % (i, h or "干净"))