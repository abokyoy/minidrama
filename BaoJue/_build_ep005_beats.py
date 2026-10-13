# -*- coding: utf-8 -*-
"""ep005 分镜 beats 生成器（第③步产物）
沿用 ep004 的紧凑 DSL：一段 JSON 有 9 个字段名 + 2000 字符样板，逐段手写容易漏字段；
脚本保证「字段齐全 / id 连续 / retention 默认一致 / shots 时刻格式统一」这些机械正确性。
内容（summary / shots / soundscape）仍然是逐镜手写的。

四个场次（子场次必须拆开带字母后缀，否则光照档和空间锚点都挂不上）：
  5-1  会客厅·上午·日戏   P01–P55 → t01–t55
  5-2  老宅门口·上午·日戏  P56–P78 → t56–t78
  5-3a 出租屋·深夜·夜戏    P79–P100 → t79–t100
  5-3b 楼门口路灯下·深夜   P101–P117 → t101–t117

铁律（ep004 已踩过并修好，这里直接遵守）：
  1. 台词写成 [Chinese] …，绝不加引号（引号 = 烧字幕）。
  2. 任何一段里有台词，本拍或上一拍必须有 (S#) 说话人标注。
  3. soundscape 不许出现 silence / silent / gone quiet / nothing but / dead quiet / total hush
     这些压人声的词。
  4. 不许出现 into the shadow / heavy shadow / in darkness / dim / unlit / the dark / gloomy
     这些压曝光的词——check_beats 是子串匹配，连否定句里也绝不能出现这些短语本身。
  5. 5-3a 手机屏与协议复印件上的任何文字一律不入画面，只写屏光与手部动作。
"""
import json, os, io, sys, re

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "ep005_beats")
EPS = "ep05"

CHARS = {"suxiaoman", "luchong", "luman", "luhang", "qinlvshi", "zhongshu"}
SCENES = {"lu_hall", "lu_hall_desk", "lu_gate", "lu_gatehouse", "rental_room",
          "rental_gate", "car_interior"}

# sc_car_interior.png 是**夜间**车厢参考图，而 5-2 是上午日戏。
# 不显式降级的话，H3 会把这张夜间图当打光参考，把日戏画面拉暗
# （ep001 seg117 踩过这个坑，渲染器 storyboard_render.py:837 留了这条降级口子）。
CAR_DAY_NOTE = (
 "the same rear cabin of a black executive saloon, seen from the front seats looking back — the wide pale-grey "
 "leather rear bench, the central armrest, chrome door handles and the tinted window on the far side. USE IT AS THE "
 "EXACT POSITION AND PROP REFERENCE ONLY: it is bright late-morning daylight outside this car and the whole cabin is "
 "filled with that daylight coming through the glass; the amber night lighting visible in the image must NOT be "
 "reproduced and the cabin must not be made darker than the bright street outside it."
)


def _ts(t):
    """把 'MM:SS.mmm' 或 'SS.mmm' 统一成 '00:MM.SSS'。
    ep001–ep003 的 H3 提示词里切点一律带 00: 前缀（At 00:02.400），
    ep004/ep005 最初写成 '06.000' 少了两位 → 口径不一致，且 check_beats 的
    TIME_RE 匹配不到会导致时长检查被整段跳过。这里强制补齐。"""
    if t is None:
        return None
    parts = t.split(":")
    if len(parts) == 2:
        return "%02d:%s" % (int(parts[0]), parts[1])
    return "00:%s" % t


def seg(tid, scene, title, chars, scens, summary, entry, shots, sound,
        music="N/A", cret=None, sret="weak_reference", ref_notes=None):
    """shots: [(拍号, 'MM:SS.mmm' 或 None, 画面文字), ...]；拍号 1 不带 At 时间戳。"""
    refs = list(chars) + list(scens)
    for r in refs:
        if r not in CHARS and r not in SCENES:
            raise SystemExit("未知参考图逻辑名: %s（段 %s）" % (r, tid))
    if len(refs) > 6:
        raise SystemExit("段 %s 参考图 %d 张，超过 6 张上限" % (tid, len(refs)))
    ret = {}
    for c in chars:
        ret[c] = (cret or {}).get(c, "fully_preserved")
    for s in scens:
        ret[s] = sret
    body = "Entry state, re-anchored to the reference images: " + entry
    prev_t = 0.0
    for n, t, txt in shots:
        ts = _ts(t)
        # 台词时序钳位：台词必须说得完，且必须晚于上一拍
        if "[Chinese]" in txt:
            cjk = len(re.findall(r"[\u4e00-\u9fff]", txt))
            latest = 10.0 + 0.15 - cjk / 3.2
            cur = prev_t if t is None else (int(ts.split(":")[0]) * 60 + float(ts.split(":")[1]))
            if cur > latest:
                cur = max(prev_t + 0.25, round(latest - 0.10, 3))
            if cur <= prev_t:
                cur = round(prev_t + 0.25, 3)
            mm = int(cur // 60)
            ss = cur - mm * 60
            ts = "%02d:%06.3f" % (mm, ss)
        body += "\n[Shot %d] %s%s" % (n, ("" if t is None else "At %s, " % ts), txt)
        if t is not None:
            prev_t = int(ts.split(":")[0]) * 60 + float(ts.split(":")[1])
    d = {"id": EPS + "_" + tid, "scene": scene, "title": title, "refs": refs,
         "retention": ret, "summary": summary, "shots": body,
         "soundscape": sound, "music": music}
    if ref_notes:
        d["ref_notes"] = ref_notes
    elif "car_interior" in refs:
        # 自动降级：白天戏用夜间车厢图当参考图时必须显式说明，否则画面被拉暗
        d["ref_notes"] = {"car_interior": CAR_DAY_NOTE}
    return d


def dump(fname, segs):
    p = os.path.join(OUT, fname)
    io.open(p, "w", encoding="utf-8").write(
        json.dumps(segs, ensure_ascii=False, indent=1) + "\n")
    print("  %-14s %3d 段  (%s – %s)" % (fname, len(segs), segs[0]["id"], segs[-1]["id"]))


# 会客厅的公共入画状态，逐段只写变化量
HALL_ENTRY = (
 "the long dark rosewood table running away from the camera through the middle of the bright hall; 陆崇 (S15) at "
 "the FAR head of it backed by the sideboard and the hanging landscape painting; 苏小满 (S1) standing at the NEAR head "
 "half a step left, the only person on her feet; 陆蔓 (S8) seated along the east long side mid-position with a tea "
 "cup; 陆航 (S14) leaning on the east window sill further back and higher, turning a cup; 秦律师 (S19) seated at the "
 "near head three-quarter to camera, half a step behind 苏小满's right shoulder; side-branch relatives and stewards "
 "staggered back along both flanks; the ceiling lights and the east window both on, the room bright and even"
)

# ═══════════════════════════════════════════════════════════════════
# 场次 5-1　陆家老宅 会客厅 · 上午（日戏）
# 长案为轴。`料`（牛皮纸档案袋＋几页纸＋一张按过手印的协议复印件）
# 行程：陆崇手边 → 推到长案中央 → 全程原封不动、无人翻开。
# ═══════════════════════════════════════════════════════════════════
HALL_ENTRY_STOOD = (
 "the long dark rosewood table running away from the camera through the middle of the bright hall; 陆崇 (S15) ON HIS FEET at "
 "the FAR head of it, standing in front of the sideboard and the hanging landscape painting where he has risen and "
 "where he stays on his feet to the end of the scene; 苏小满 (S1) standing at the NEAR head half a step left, the only "
 "person standing in the near half; 陆蔓 (S8) seated along the east long side mid-position with a tea cup; 陆航 (S14) "
 "leaning on the east window sill further back and higher, turning a cup; 秦律师 (S19) seated at the near head "
 "three-quarter to camera, half a step behind 苏小满's right shoulder; side-branch relatives and stewards staggered back "
 "along both flanks; the ceiling lights and the east window both on, the room bright and even"
)

S51 = [
seg("t01", "5-1", "满堂已就位", [], ["lu_hall"],
    "Wide: the reception hall of the 陆 family old mansion in the morning, already full — the long table and the "
    "polished floor along the bottom third, one row of people down each long side, and 苏小满 the only one standing.",
    HALL_ENTRY + "; every seat taken, nobody speaking, the long table and the polished floor filling the bottom third",
    [(1, None, "Wide from inside the doors looking in: the long table runs away through the middle of the hall, two "
               "rows of seated people along its long sides, nearer shoulders overlapping the row behind all the way to "
               "the far head; the bottom third is the matte red table top and the polished floor; morning light comes "
               "in at a slant through the east floor-to-ceiling window and the ceiling lights are on, so the whole hall "
               "reads bright and open; one person in the near half is standing and everybody else is seated."),
     (2, "04.500", "The hall holds: heads turn a little towards the near head of the table, then settle; the standing "
                   "figure at the near head does not move, and the file folder is still at the far head's right hand.")],
    "Low voices running along both sides of the table, a cup set down on wood, the ceiling light's faint electrical "
    "hum, morning birdsong from the east window."),

seg("t02", "5-1", "陆崇坐定", ["luchong"], ["lu_hall"],
    "Medium: 陆崇 (S15) sits at the far head of the long table, back straight, facing the near end, the kraft-paper "
    "file folder open at his right hand.",
    HALL_ENTRY + "; 陆崇 (S15) squared in his chair at the far head, the kraft folder open at his right hand",
    [(1, None, "Medium on 陆崇 (S15) at the far head of the long table, the sideboard and the hanging landscape "
               "painting behind him: dark navy stand-collar jacket, back perfectly straight, face turned down the "
               "table towards the near end; at his right hand a kraft-paper file folder with its mouth open and the "
               "edges of several pages showing; morning light from the east window falls across him from the side and "
               "the ceiling lights fill his face evenly."),
     (2, "05.000", "He shifts his weight a fraction, squares his shoulders to the table, and keeps both hands near "
                   "the folder without lifting it.")],
    "The room's low murmur, a chair leg easing on the floor, the folder's paper edge ruffling faintly."),

seg("t03", "5-1", "东侧：陆蔓与陆航", ["luman", "luhang"], ["lu_hall"],
    "Medium: along the east long side of the table mid-position 陆蔓 (S8) sits with a tea cup; further right and "
    "further back at the east window sill 陆航 (S14) leans on the wall turning a cup between his fingers.",
    HALL_ENTRY + "; 陆蔓 (S8) holding a tea cup at the east long side; 陆航 (S14) at the east window sill behind her",
    [(1, None, "Medium along the east long side of the table: 陆蔓 (S8) sits mid-position in a deep-green qipao with a "
               "dark-red shawl, a porcelain tea cup in her hand, turned side-on to the camera; further right and a "
               "clear depth step behind her, 陆航 (S14) in a pale beige knit sweater with the cuffs pushed to his "
               "forearms leans against the window sill, turning a cup in his fingertips; the two of them are staggered "
               "along the depth and never side by side; the bottom third is the table edge and the floor."),
     (2, "05.500", "陆航 (S14)'s fingers keep circling the cup rim; 陆蔓 (S8) holds her cup level and does not drink.")],
    "A cup against porcelain, the window's daylight breathing on the glass, low voices from the far head."),

seg("t04", "5-1", "近端：秦律师与站着的苏小满", ["suxiaoman", "qinlvshi"], ["lu_hall"],
    "Over-the-shoulder at the near head: 秦律师 (S19) sits three-quarter to camera with the verification folder open "
    "and a black pen in hand, and half a step nearer the camera and half a step left, 苏小满 (S1) stands facing the "
    "far head with both hands down at her sides.",
    HALL_ENTRY + "; 秦律师 (S19) seated at the near head; 苏小满 (S1) standing half a step left of the head, nearer "
    "the camera than him",
    [(1, None, "Over-the-shoulder at the near head of the table: 秦律师 (S19) sits in a dark suit with thin-rimmed "
               "glasses, three-quarter to the camera, the verification folder open in front of him and a black pen in "
               "his right hand; half a step nearer the camera and half a step to his left, 苏小满 (S1) stands in a "
               "plain light jacket over dark blue work clothes with a low ponytail, both hands hanging at her sides, "
               "facing the far head of the table; she overlaps him in depth and the two of them are never lined up "
               "beside each other."),
     (2, "05.000", "苏小满 (S1) keeps her shoulders level and her hands still; 秦律师 (S19) glances down at his open "
                   "folder and back up along the table.")],
    "Paper settling on the table, a pen cap clicked once, the room's low murmur continuing behind."),

seg("t05", "5-1", "把材料推到长案中央", ["luchong"], ["lu_hall_desk"],
    "High-angle close on the table top: 陆崇 (S15)'s hand presses the kraft folder and slides it forward until it "
    "stops at the centre of the long table, then withdraws; the folder, several pages and one photocopy of an "
    "agreement with a pale red thumbprint at its lower right lie in a row, and the printing on the paper is not "
    "legible.",
    HALL_ENTRY + "; on the table top, one kraft folder, several loose pages and one photocopy, face down at first",
    [(1, None, "High-angle close on the table top: 陆崇 (S15)'s hand presses flat on the kraft folder and slides it "
               "away from him along the wood until it stops at the centre of the long table, then lifts off and comes "
               "back to his own side; the folder's mouth is open with the edges of several pages showing, and lying on "
               "top of them is one photocopy of an agreement whose corner is furry and whose lower right corner carries "
               "a pale red thumbprint; the printing on the paper is too small to read; the upper two thirds is his hand "
               "and the wood, the bottom third is the table edge."),
     (2, "06.000", "陆崇 (S15) speaks from off the top of frame, his hand now withdrawn: [Chinese] 都看看。这是我让人查的。"),
     (3, "09.000", "The hand is gone; the file lies dead centre and nobody's hand comes near it.")],
    "Paper sliding over polished wood and stopping, a single quiet breath, chairs shifting at the far head."),

seg("t06", "5-1", "陆崇把话摊给满屋", ["luchong"], ["lu_hall"],
    "Medium: 陆崇 (S15) squares his body at the far head and addresses the near end in a flat tone, like reading out "
    "a list he wrote long ago; he does not look at 苏小满.",
    HALL_ENTRY + "; 陆崇 (S15) squared at the far head, hands back by the folder he has just pushed away",
    [(1, None, "Medium on 陆崇 (S15) at the far head: he squares his body to face the near end of the table and opens "
               "his mouth in an even, level tone, the way a man reads out a list he wrote days ago; his eyes stay on "
               "the middle distance of the table and do not go to 苏小满 (S1) at the near head; the ceiling light and "
               "the east window both fill his face evenly and the skin reads clear."),
     (2, "05.000", "He finishes a line, keeps his chin level, and waits half a beat before the next one.")],
    "His voice carrying the length of the table, the room's murmur dropping away under it."),

seg("t07", "5-1", "料停在中央，无人伸手", [], ["lu_hall_desk"],
    "Medium on the file: the kraft folder and its pages sit at the centre of the long table while the eyes of the "
    "relatives and stewards on both flanks drop onto it together, and not one hand reaches out.",
    HALL_ENTRY + "; the file now at the centre of the long table, everyone still seated",
    [(1, None, "Medium along the table axis onto the centre of the long table: the kraft folder, the pages and the "
               "agreement photocopy lie exactly where they were pushed, and from both flanks the heads of the "
               "side-branch relatives and the stewards come down to that same spot at the same moment; no hand comes "
               "towards it from either side; the bottom third is the table top and the folder's mouth."),
     (2, "05.500", "The heads stay bent towards it; the file does not move and is not opened.")],
    "Twenty people breathing, a chair creaking once, nothing touching paper."),

seg("t08", "5-1", "一句一句往下砸", ["luchong"], ["lu_hall"],
    "Close on 陆崇 (S15): he lays the words out one at a time, not fast, tail of each line held down; his chin lifts "
    "slightly, his eyes sweep the table and come back up to the near end.",
    HALL_ENTRY + "; 陆崇 (S15) at the far head, speaking, gaze moving from the table up to the near end",
    [(1, None, "Close on 陆崇 (S15) at the far head: he lays the words out one at a time, not fast, holding the tail "
               "of each line down; his chin lifts a fraction, his eyes go along the table surface and then come back up "
               "to the near end; the ceiling light lands on his face with generous front fill and the lines around his "
               "mouth stay readable rather than hollow."),
     (2, "05.000", "陆崇 (S15) speaks, [Chinese] 外包保洁。大学念了两年，退学。外婆重病，欠着医院二十万。"),
     (3, "09.500", "He keeps his eyes on the near end after the last number, waiting.")],
    "His voice level and unhurried down the table, the room behind it falling to a low attentive hum."),

seg("t09", "5-1", "反打：苏小满听着", ["suxiaoman"], ["lu_hall"],
    "Reverse on 苏小满 (S1): standing half a step left of the table head with her face to the far end, she listens "
    "with no movement in her face; her hands hang at her sides and her right fingers press together once and release; "
    "she does not look at the file.",
    HALL_ENTRY + "; 苏小满 (S1) standing at the near head, facing the far end, hands down at her sides",
    [(1, None, "Reverse at the near head: 苏小满 (S1) stands half a step left of the table head facing the far end and "
               "listens, and there is no rise or fall on her face while the words come across; both hands hang at her "
               "sides and her right fingers press together once and then let go; her eyes stay on the far head and "
               "never drop to the file in the middle of the table; the east window light falls across her front."),
     (2, "05.000", "She blinks once, slowly, and keeps her feet exactly where they are.")],
    "陆崇 (S15)'s voice arriving from off her front, the room's held breath, a distant cup."),

seg("t10", "5-1", "两侧交换了一个眼神", [], ["lu_hall"],
    "Medium on both flanks: along the two long sides of the table a relative and a steward exchange one look and do "
    "not say anything; the table top and the floor press the bottom edge of frame.",
    HALL_ENTRY + "; the seated rows on both flanks, all still",
    [(1, None, "Medium down the two long sides of the table: a side-branch relative on the east flank and a steward on "
               "the west flank turn their eyes towards each other for a moment and back to the centre, and neither "
               "makes a sound; everyone stays seated and staggered along the depth; the bottom third is the table top "
               "and the polished floor."),
     (2, "04.500", "The glance ends; both faces settle back to the far head.")],
    "Cloth shifting, one swallowed cough from the west flank, the room's low hush."),

seg("t11", "5-1", "目扫东侧", ["luchong"], ["lu_hall"],
    "Close on 陆崇 (S15): as the sum is named his eyes travel slowly along the east long side of the table; the "
    "question is asked to the whole room and lands on one person.",
    HALL_ENTRY + "; 陆崇 (S15) at the far head, eyes moving along the east side",
    [(1, None, "Close on 陆崇 (S15) at the far head: as he names the sum his eyes move slowly sideways along the east "
               "long side of the table, taking in the people seated there; the question is put to the whole room and "
               "its landing point is one person; the front fill on his face stays generous and even."),
     (2, "05.000", "陆崇 (S15) speaks, [Chinese] 半个月前，有人给她打了二十万。谁打的，各位心里有数。"),
     (3, "09.500", "His eyes stop on the east side and stay there.")],
    "His voice level, a chair easing on the far side, the room listening hard."),

seg("t12", "5-1", "陆蔓端茶一送", ["luman"], ["lu_hall"],
    "Close on the east long side: 陆蔓 (S8)'s hand holding the tea cup stalls for a fraction, her lashes lift for half "
    "a second, and she sends the cup to her lips and takes one mouthful, her face tidied clean.",
    HALL_ENTRY + "; 陆蔓 (S8) at the east long side with the tea cup in her hand",
    [(1, None, "Close on the east long side: the hand of 陆蔓 (S8) holding the porcelain cup stops for a fraction of a "
               "second, her lashes lift for half a second, and then she brings the cup to her lips and takes one "
               "measured mouthful and puts it back level; her face is tidied clean by the time the cup is down; she "
               "stays side-on to the camera in the right half of frame."),
     (2, "05.000", "The cup settles back on the table and her hands fold around it again.")],
    "Porcelique against porcelain, one swallow, cloth settling."),

seg("t13", "5-1", "按过手印四个字", ["luchong"], ["lu_hall"],
    "Close on 陆崇 (S15): he says the last line very slowly, letting the four words about the thumbprint out one at a "
    "time, and his eyes settle on the agreement at the centre of the table.",
    HALL_ENTRY + "; 陆崇 (S15) at the far head, eyes coming down to the centre of the table",
    [(1, None, "Close on 陆崇 (S15) at the far head: he says the last line very slowly and lets the four words about "
               "the thumbprint out one at a time; at the end of it his eyes come down to the agreement photocopy lying "
               "at the centre of the long table; the ceiling light and the window keep his face evenly filled."),
     (2, "05.000", "陆崇 (S15) speaks, [Chinese] 还有一样。她跟二房签过字，按过手印。白纸黑字，一张协议。"),
     (3, "09.500", "His gaze stays down on the paper at the centre of the table.")],
    "His voice slowing, a single leaf of paper settling, the room's held breath."),

seg("t14", "5-1", "纸与手印", [], ["lu_hall_desk"],
    "High-angle close: the agreement photocopy lies on top of the file at the centre of the table, its corner furry "
    "and a pale red thumbprint at the lower right, the pages beneath showing a row of edges; only the shape of the "
    "paper and the print are given, the printing is not legible.",
    HALL_ENTRY + "; the file at the centre of the long table, the agreement photocopy on top of it",
    [(1, None, "High-angle close onto the centre of the long table: the agreement photocopy lies on the very top of "
               "the file, its corner furry and its lower right corner carrying one pale red thumbprint, and the pages "
               "beneath it show a row of paper edges; the shot gives the shape of the paper and the print only, the "
               "printing on it is too small to read; the bottom third is the table edge and the wood grain."),
     (2, "05.000", "The paper does not move; the print stays where it is.")],
    "Paper on wood, the room's breath held, a distant chair."),

seg("t15", "5-1", "满堂目光扎向中央", [], ["lu_hall"],
    "Medium on the full room: every head turns to the centre of the long table at once; 陆蔓 (S8)'s cup hand stops "
    "and 陆航 (S14)'s fingers on the cup slow by half a beat.",
    HALL_ENTRY + "; the whole room seated, all heads coming round to the centre of the table",
    [(1, None, "Medium across the full room: every head at both long sides turns towards the centre of the long table "
               "in the same instant; on the east side 陆蔓 (S8)'s hand stops with the cup held level, and at the east "
               "window 陆航 (S14)'s fingers slow on the cup rim; nobody reaches out; the bottom third is the table top "
               "and the floor."),
     (2, "04.500", "The heads hold on the file; the room does not breathe out.")],
    "A dozen people inhaling together, cloth moving, the ceiling light's hum."),

seg("t16", "5-1", "陆蔓先发制人", ["luman"], ["lu_hall"],
    "Close on the east long side: 陆蔓 (S8) sets her cup down, sits straighter, lifts her chin and looks across to the "
    "far head out of the corner of her eye; the line comes out first.",
    HALL_ENTRY + "; 陆蔓 (S8) at the east long side, cup coming down onto the table",
    [(1, None, "Close on the east long side: 陆蔓 (S8) puts the tea cup down on the table, sits straighter in her "
               "chair, lifts her chin and turns her eyes across to the far head of the table out of the corner of them; "
               "the shot is tight on her upper body in the right half of frame with the room's brightness on her face."),
     (2, "04.500", "陆蔓 (S8) speaks, [Chinese] 陆崇，你说话就说话。看着我干什么。"),
     (3, "08.000", "She holds the look across the table, chin still up.")],
    "Porcelique set down hard on wood, her voice pitched to carry, the room quieting further."),

seg("t17", "5-1", "拢披肩，目扫两侧", ["luman"], ["lu_hall"],
    "Close on 陆蔓 (S8): her tone is a taut politeness with the tail of each line lifting; she tidies the edge of her "
    "dark-red shawl as she speaks and then looks along both sides of the room, checking who has followed her gaze.",
    HALL_ENTRY + "; 陆蔓 (S8) at the east long side, hands at the shawl edge",
    [(1, None, "Close on 陆蔓 (S8): her tone is a taut, courteous one with the tail of every line lifting; as she "
               "speaks she tidies the edge of her dark-red shawl with one hand, then turns her eyes along both sides "
               "of the room to check who has followed her gaze over there; the front fill keeps her face clear and "
               "even."),
     (2, "05.000", "Her eyes finish their sweep of both flanks and come back to the far head.")],
    "Fabric being smoothed, the low murmur restarting along the west flank."),

seg("t18", "5-1", "陆崇盯着苏小满", ["luchong", "suxiaoman"], ["lu_hall"],
    "Close on 陆崇 (S15): he does not acknowledge 陆蔓 (S8) at all — his head does not turn, his eyes go straight "
    "down the table to 苏小满 (S1) standing at the near head, his tone flat without rise or fall.",
    HALL_ENTRY + "; 陆崇 (S15) at the far head looking straight down the table; 苏小满 (S1) standing at the near head",
    [(1, None, "Close on 陆崇 (S15) at the far head: he does not take 陆蔓 (S8) at the east side at all — his head does "
               "not turn a fraction — and his eyes go straight down the length of the table to 苏小满 (S1) standing at "
               "the near head, and his tone comes out flat with no rise and no fall; the far head and the near head "
               "line up on the table's own depth axis."),
     (2, "04.500", "陆崇 (S15) speaks, [Chinese] 一个缺钱的保洁，忽然肯来认一门阔亲。"),
     (3, "08.500", "He keeps his eyes on her and does not blink through the end of the line.")],
    "His flat voice filling the hall, the room's air changing, a cup untouched."),

seg("t19", "5-1", "迎着这条视线", ["suxiaoman"], ["lu_hall"],
    "Reverse at the near head: 苏小满 (S1) looks straight back down the table, chin neither lifted nor dropped, her "
    "stance not giving an inch; the room's eyes are on her and she looks at nobody but the man at the far head.",
    HALL_ENTRY + "; 苏小满 (S1) standing at the near head, feet planted, facing the far head",
    [(1, None, "Reverse at the near head of the table: 苏小满 (S1) takes the look straight back, her chin neither "
               "lifted nor dropped and her stance giving nothing; the whole room's attention is on her and she returns "
               "it to nobody except the man at the far head; the east window light comes across her front and her face "
               "is evenly filled."),
     (2, "05.000", "Her hands stay at her sides and her feet do not move on the floor tiles.")],
    "The room pressing close around her, a chair easing, her breathing steady."),

seg("t20", "5-1", "把台子交给满堂", ["luchong"], ["lu_hall"],
    "Close on 陆崇 (S15): he leans half a fraction back into his chair as if handing the floor to the room, and he "
    "leaves half a beat of air on the question about who arranged it.",
    HALL_ENTRY + "; 陆崇 (S15) at the far head leaning half a fraction back in his chair",
    [(1, None, "Close on 陆崇 (S15) at the far head: he leans half a fraction back into his chair as if handing the "
               "floor over to the whole room, and he leaves half a beat of air on the question; the light on him stays "
               "even and his face stays readable."),
     (2, "04.000", "陆崇 (S15) speaks, [Chinese] 各位想想，这戏，是谁排的。"),
     (3, "07.500", "He stays leaned back and lets the length of the question sit there unanswered.")],
    "The question falling into the room, the length of it stretching, fabric shifting."),

seg("t21", "5-1", "无人接话", [], ["lu_hall"],
    "Medium down both sides of the table: the room goes quiet along both long sides, one of the relatives drops his "
    "head and nobody answers him.",
    HALL_ENTRY + "; both flanks seated, the file still at the centre of the table",
    [(1, None, "Medium down both long sides of the table: the room settles into quiet along both flanks, a relative "
               "on the east side drops his head towards the table and nobody picks the question up; the file stays at "
               "the centre of the table where it was pushed; the bottom third is the table top and the polished floor."),
     (2, "05.000", "Heads stay down or forward; no one answers.")],
    "A room not answering, a slow exhale from the far head, a clock somewhere in the hall."),

seg("t22", "5-1", "秦律师按住全场", ["qinlvshi", "suxiaoman"], ["lu_hall"],
    "Over-the-shoulder at the near head: 秦律师 (S19) raises a hand, presses it down flat on the table to push the room's "
    "noise down, and speaks level, going by his items; 苏小满 (S1)'s standing back is a step nearer the camera than he "
    "is, the two of them overlapping in depth.",
    HALL_ENTRY + "; 秦律师 (S19) at the near head raising a hand over the table; 苏小满 (S1) standing a step nearer "
    "the camera than him",
    [(1, None, "Over-the-shoulder at the near head: 秦律师 (S19) raises his hand, palm down, and presses it flat on "
               "the table in front of him to push the room's noise down, and he speaks in a level tone, going by his "
               "items; he sits three-quarter to the camera with the verification folder open in front of him; a step "
               "nearer the camera his back and shoulders belong to 苏小满 (S1) standing there, so the two of them "
               "overlap in depth and are never lined up beside each other."),
     (2, "05.000", "秦律师 (S19) speaks, [Chinese] 协议归协议。这一场，只认证据。"),
     (3, "08.500", "His hand settles on the table and stays there, keeping the room down.")],
    "His palm landing on wood, the room's noise falling away under his voice."),

seg("t23", "5-1", "镜片上的一道天光", ["qinlvshi"], ["lu_hall"],
    "Close on 秦律师 (S19): a line of window light crosses his glasses as he says the words about the evidence, and "
    "his gaze runs the length of the table to the far head.",
    HALL_ENTRY + "; 秦律师 (S19) seated at the near head, glasses catching the window",
    [(1, None, "Close on 秦律师 (S19) at the near head: a line of the east window's light crosses his thin-rimmed "
               "glasses as he says the words about the evidence, and his gaze runs the length of the long table to the "
               "far head; the light on his face is even and generous, the room behind him open and bright."),
     (2, "05.000", "He finishes the line and his eyes stay on the far head.")],
    "His voice settling the room, the window line sliding off the glass, a pen on paper."),

seg("t24", "5-1", "反打：眉心动一下", ["luchong"], ["lu_hall"],
    "Reverse on 陆崇 (S15): the line presses him half a beat — his brow moves very slightly and then he does not "
    "change; he does not argue, he only puts his eyes back on 苏小满 (S1) at the near head.",
    HALL_ENTRY + "; 陆崇 (S15) at the far head, eyes returning to the near head",
    [(1, None, "Reverse on 陆崇 (S15) at the far head: the line presses him for half a beat — the centre of his brow "
               "moves very slightly and then he is still; he makes no argument, he only moves his eyes back to 苏小满 "
               "(S1) standing at the near head; the light stays even on his face and reads clean."),
     (2, "05.000", "His eyes settle on the near head and stay there; he says nothing.")],
    "The room's quiet, a distant clock, his breath measured."),

seg("t25", "5-1", "满厅目光收拢到一个人", [], ["lu_hall"],
    "Wide: the room's attention draws in at once onto the one person standing at the near head — the east side looking, "
    "the west side looking, 陆航 (S14) at the window sill looking, 陆崇 (S15) at the far head looking hardest; the long "
    "table lines them all up in depth with her alone nearest and lowest.",
    HALL_ENTRY + "; the whole room's attention converging on the standing figure at the near head",
    [(1, None, "Wide from the near end of the hall: the room's attention draws in at once onto the one person standing "
               "at the near head of the long table — the east side is looking, the west side is looking, 陆航 (S14) at "
               "the east window sill has his cup raised and is looking, and 陆崇 (S15) at the far head is looking "
               "hardest; the long table lines all of them up along its depth with her alone nearest the camera and "
               "lowest in frame; the bottom third is the table top and the polished floor."),
     (2, "05.500", "Every face stays turned to her; she does not move under it.")],
    "A room's attention as a kind of quiet, a long held breath, the window."),

seg("t26", "5-1", "她站着，没动", ["suxiaoman"], ["lu_hall"],
    "Low close at the bottom third: 苏小满 (S1)'s two hands hang at her sides, the fingertips not curled, her shoe tips "
    "planted on the floor tiles; she is standing and she has not moved.",
    HALL_ENTRY + "; 苏小满 (S1) at the near head, framed low so her hands and shoes fill the bottom third",
    [(1, None, "Low close framing the bottom third of her body: the two hands of 苏小满 (S1) hang at her sides with the "
               "fingertips not curled, and her flat cloth shoes are planted on the polished floor tiles; the frame "
               "holds her there standing and not moving while the room's eyes stay on her; the light on her is even "
               "and her hands are clearly readable."),
     (2, "05.000", "Her fingers stay loose and her feet do not shift.")],
    "The room's quiet pressing close, cloth, a distant breath."),

seg("t27", "5-1", "有人花钱请来的演员", ["luchong"], ["lu_hall"],
    "Close on 陆崇 (S15): he says it very lightly, almost as a statement of fact, then lifts a cup from beside him and "
    "sips as if the matter were closed.",
    HALL_ENTRY + "; 陆崇 (S15) at the far head with a cup at his hand",
    [(1, None, "Close on 陆崇 (S15) at the far head: he says the line very lightly, almost as a statement of fact, and "
               "then he lifts a small cup from beside the folder and takes a sip, as if the matter were already closed; "
               "the ceiling light and the window keep his face evenly filled while he drinks."),
     (2, "04.500", "陆崇 (S15) speaks, [Chinese] 说白了。她从头到尾，就是有人花钱请来的演员。"),
     (3, "08.500", "The cup comes down and he settles back half a fraction into his chair.")],
    "A cup against porcelain, his light tone falling flat, the room listening."),

seg("t28", "5-1", "特写：她的眼", ["suxiaoman"], ["lu_hall"],
    "Close on 苏小满 (S1)'s eyes: the lashes do not tremble and the gaze does not move away — she is not untouched, she "
    "simply never intended to argue here; the hall's light sits in her pupils and they are very calm.",
    HALL_ENTRY + "; 苏小满 (S1) at the near head, framed tight on her eyes",
    [(1, None, "Close on the eyes of 苏小满 (S1): the lashes do not tremble and the gaze does not slide away — she is "
               "not a woman who has not been spoken to, she simply never intended to argue the point in this room; the "
               "hall's light sits as a small bright shape in her pupils and they are very calm; the skin around her eyes "
               "is evenly lit and reads clearly."),
     (2, "05.000", "She holds the look for a long beat without blinking.")],
    "The room's quiet, her steady breathing, a cup set down far away."),

seg("t29", "5-1", "陆蔓选择看戏", ["luman"], ["lu_hall"],
    "Close on the east long side: 陆蔓 (S8) picks her cup up again, leans back into the chair, and watches the file at "
    "the centre of the table through half-lowered lids — she has chosen not to take it up, and to watch.",
    HALL_ENTRY + "; 陆蔓 (S8) at the east long side leaning back with her cup",
    [(1, None, "Close on the east long side: 陆蔓 (S8) lifts her tea cup again, lets her weight go back into the chair, "
               "and looks at the file lying at the centre of the long table through half-lowered lids — she has chosen "
               "not to answer and has chosen to watch; the shot holds her side-on in the right half of frame with the "
               "room's brightness on her."),
     (2, "05.000", "The cup rests against her chest; her eyes stay on the file.")],
    "Porcelique against her palm, a long held quiet, the room's breath."),

seg("t30", "5-1", "杯沿与唇", ["luman"], ["lu_hall"],
    "Tight close: the cup rim touches 陆蔓 (S8)'s lower lip and she does not drink, it only rests there; a thin layer "
    "of steam rises into the ceiling light, and her eyes look past the rim at 苏小满 (S1) standing at the near head.",
    HALL_ENTRY + "; 陆蔓 (S8) at the east long side, cup at her lips",
    [(1, None, "Tight close: the rim of the cup touches the lower lip of 陆蔓 (S8) and she does not drink, it only "
               "rests there; a thin layer of steam rises off the tea into the ceiling light; above the rim her eyes "
               "look across the room at 苏小满 (S1) standing at the near head; the light on her face is soft and even "
               "and the steam reads clearly against it."),
     (2, "05.000", "The cup stays at her lips; her eyes stay on the standing woman.")],
    "Steam rising quietly, the room holding its breath around her, the window frame ticking."),

seg("t31", "5-1", "说完了吗", ["suxiaoman"], ["lu_hall"],
    "Over-the-shoulder at the near head: 苏小满 (S1) lifts her chin half a fraction, sends her gaze over the whole "
    "length of the table to the far head, and asks three words without raising her voice; her hands stay at her sides.",
    HALL_ENTRY + "; 苏小满 (S1) standing at the near head, chin lifted half a fraction",
    [(1, None, "Over-the-shoulder at the near head: 苏小满 (S1) lifts her chin half a fraction, sends her gaze over the "
               "whole length of the long table to the far head, and asks three words without raising her voice; both "
               "hands still hang at her sides, she does not lean on the table and does not fold her arms, and her stance "
               "is steady; the frame carries her in the near half with the table running away from her."),
     (2, "04.000", "苏小满 (S1) speaks, [Chinese] 说完了吗。"),
     (3, "06.500", "She holds her chin where it is and waits.")],
    "Three words going the length of the table, the room going quieter than it was."),

seg("t32", "5-1", "视线挪到她脸上", [], ["lu_hall"],
    "Medium on the full room: the room pauses half a beat — people on both the east and the west side move their eyes "
    "off the file and onto her face at the same time; 陆崇 (S15) at the far head does not answer, only looks at her.",
    HALL_ENTRY + "; the whole room seated, eyes coming off the file and onto 苏小满 (S1) at the near head",
    [(1, None, "Medium across the full room: the room pauses for half a beat — the people on the east side and the "
               "people on the west side move their eyes off the file at the centre of the table and onto 苏小满 (S1)'s "
               "face at the same time; 陆崇 (S15) at the far head does not answer and only looks at her; the bottom "
               "third is the table top and the floor."),
     (2, "05.000", "Her face holds every one of their eyes and nothing crosses it.")],
    "A room's gaze landing, a long held quiet, a cup not being drunk."),

seg("t33", "5-1", "我是保洁", ["suxiaoman"], ["lu_hall"],
    "Close at the near head: 苏小满 (S1) says it word by word, not fast; her chin stays level on the words about being a "
    "cleaner and her gaze runs half a circle along both sides of the table as she says what she wiped.",
    HALL_ENTRY + "; 苏小满 (S1) standing at the near head, gaze beginning to sweep both flanks",
    [(1, None, "Close at the near head: 苏小满 (S1) says it word by word and not fast; her chin stays level on the "
               "words about being a cleaner, and as she says what she wiped her gaze runs half a circle along both "
               "sides of the long table, taking in everybody in the room; the light on her face is even and her mouth "
               "is clearly readable."),
     (2, "05.000", "苏小满 (S1) speaks, [Chinese] 我是保洁。这半个月，在座各位面前的桌子，都是我擦的。"),
     (3, "09.500", "Her gaze finishes the half circle and comes back to the far head.")],
    "Her level voice filling the near half, the room listening without a sound."),

seg("t34", "5-1", "特写：手与围裙", ["suxiaoman"], ["lu_hall"],
    "Tight close on her hands: the grey-blue apron ties rise and fall once with her breathing and there is an old callus "
    "on the fingertips — these two hands are the evidence of the wiping.",
    HALL_ENTRY + "; 苏小满 (S1)'s hands hanging at her sides above the grey-blue apron",
    [(1, None, "Tight close on 苏小满 (S1)'s hands: the ties of her grey-blue apron rise and fall once with her "
               "breathing and there is an old callus on her fingertips, and these two hands hanging at her sides are "
               "the evidence of everything she has just said about wiping tables; the light is soft and even on the "
               "skin and the callus reads clearly."),
     (2, "05.000", "The hands stay still at her sides; only the apron ties move with her breathing.")],
    "Her breathing, cloth settling, the room's held air."),

seg("t35", "5-1", "二十二年与半个月", ["suxiaoman"], ["lu_hall"],
    "Over-the-shoulder at the near head: 苏小满 (S1) says it flatly, like something everybody already knows; the two "
    "numbers, twenty-two years and half a month, are bitten down hard.",
    HALL_ENTRY + "; 苏小满 (S1) standing at the near head, speaking flatly",
    [(1, None, "Over-the-shoulder at the near head: 苏小满 (S1) says it flatly, like a thing everybody in the room "
               "already knows, and the two numbers in it are bitten down hard; she keeps her hands at her sides and her "
               "feet where they are; the table runs away from her to the far head along the frame's depth."),
     (2, "05.000", "苏小满 (S1) speaks, [Chinese] 老爷子找人找了二十二年。你们找了半个月，找到我。"),
     (3, "09.000", "She lets the last number sit there and does not add anything.")],
    "Her flat voice, the number hanging in the room, a long held quiet."),

seg("t36", "5-1", "反打：端杯的手停在半空", ["luchong"], ["lu_hall"],
    "Reverse on 陆崇 (S15): the hand holding his cup stops in mid-air, the small movement at the centre of his brow "
    "appears a second time, and for the first time he does not answer at once.",
    HALL_ENTRY + "; 陆崇 (S15) at the far head with his cup stopped in mid-air",
    [(1, None, "Reverse on 陆崇 (S15) at the far head: the hand holding his cup stops in mid-air, the very small "
               "movement at the centre of his brow appears a second time, and he looks at the person standing at the "
               "near end without answering at once; the light on his face is even and generous and the pause is the "
               "only thing that has changed."),
     (2, "05.000", "He stays with the cup held up and does not put it down.")],
    "A room waiting, his cup not touching wood, a clock in the hall."),

seg("t37", "5-1", "现在说我假。行", ["suxiaoman"], ["lu_hall"],
    "Close at the near head: 苏小满 (S1) says the word with almost no expression and only sets her shoulder line a "
    "fraction flatter — the word is not submission, it is picking the words up.",
    HALL_ENTRY + "; 苏小满 (S1) at the near head, shoulders settling a fraction flatter",
    [(1, None, "Close at the near head: 苏小满 (S1) says the word with almost no expression on her face and only sets "
               "her shoulder line a fraction flatter as it comes out — the word is not giving in, it is picking up what "
               "was said and holding it; the light on her is soft and even."),
     (2, "04.000", "苏小满 (S1) speaks, [Chinese] 现在说我假。行。"),
     (3, "06.500", "Her shoulders stay the new fraction flatter and her hands stay at her sides.")],
    "One word dropping into the room, the room holding around it, cloth."),

seg("t38", "5-1", "找一个真的出来", ["suxiaoman", "luman", "luhang"], ["lu_hall"],
    "Over-the-shoulder at the near head: 苏小满 (S1) lands the last word firmly, moves her gaze off 陆崇 (S15) and lets "
    "it cross 陆蔓 (S8) at the east long side and 陆航 (S14) at the window sill — she is asking the whole room for an "
    "answer.",
    HALL_ENTRY + "; 苏小满 (S1) at the near head, gaze moving from the far head across the east side to the window sill",
    [(1, None, "Over-the-shoulder at the near head: 苏小满 (S1) lands the last word firmly, takes her gaze off 陆崇 "
               "(S15) and lets it cross 陆蔓 (S8) at the east long side and on to 陆航 (S14) at the east window sill — "
               "she is asking the whole room for an answer, not one man; the table's depth axis carries her look from "
               "the far head to the right of frame."),
     (2, "04.500", "苏小满 (S1) speaks, [Chinese] 你们给我找一个真的出来。"),
     (3, "08.000", "Her eyes come to rest on 陆航 (S14) at the window sill and hold.")],
    "Her steady voice, a room with nothing to say, a cup untouched."),

seg("t39", "5-1", "搁回桌面的杯盏", [], ["lu_hall"],
    "Wide: nobody in the room takes it up; face after face along both long sides of the table drops a little; 陆崇 "
    "(S15) at the far head sets his cup back down on the wood with a small sound.",
    HALL_ENTRY + "; the whole room silent, 苏小满 (S1) standing at the near head",
    [(1, None, "Wide across the hall: nobody in the room takes it up, and face after face along both long sides of the "
               "table drops a little; at the far head 陆崇 (S15) puts his cup back down on the wood with a small clear "
               "sound; 苏小满 (S1) is still the only one standing at the near head; the bottom third is the table top "
               "and the floor pressing the frame."),
     (2, "05.000", "The sound of the cup dies out and nobody fills it.")],
    "A cup going down on wood, a room not answering, a long held quiet."),

seg("t40", "5-1", "陆航从鼻子里笑出来", ["luhang"], ["lu_hall"],
    "Close at the window sill: 陆航 (S14) laughs out of his nose — very short, the tail of it hooking upward; he has "
    "not moved off the sill and his fingers are still turning the cup, as if watching a show worth its ticket.",
    HALL_ENTRY + "; 陆航 (S14) leaning on the east window sill with his cup",
    [(1, None, "Close at the east window sill: 陆航 (S14) laughs out of his nose — very short, the tail of it hooking "
               "upward; he has not moved off the sill and his fingers are still turning the cup in front of him, as if "
               "watching a show that has earned its ticket; the window's daylight falls on him from the side and his "
               "face is filled evenly."),
     (2, "04.500", "The laugh ends and his fingers keep going round the cup rim.")],
    "A short laugh through the nose, the cup turning, a room not reacting."),

seg("t41", "5-1", "陆蔓的眼刀", ["luman"], ["lu_hall"],
    "Close on the east long side: 陆蔓 (S8)'s look flies across at him without a sound — her brow presses down and her "
    "chin lifts, saying take that back now in the plainest way.",
    HALL_ENTRY + "; 陆蔓 (S8) at the east long side turning her eyes to 陆航 (S14) at the window sill",
    [(1, None, "Close on the east long side: the look of 陆蔓 (S8) flies across at him without a sound — her brow "
               "presses down and her chin lifts a little, which says take that back now in the plainest way available; "
               "she stays side-on to the camera with the room's brightness on her face."),
     (2, "04.000", "She holds it for a beat, then turns her face back to the far head.")],
    "Silk shifting, the room's held air, a faint cup sound."),

seg("t42", "5-1", "陆航把笑收了", ["luhang"], ["lu_hall"],
    "Close at the window sill: 陆航 (S14) takes the laugh back at once and lifts his cup to his mouth to cover half his "
    "face, while his shoulders stay loose — he really does find it funny.",
    HALL_ENTRY + "; 陆航 (S14) at the east window sill, cup lifted to his mouth",
    [(1, None, "Close at the east window sill: 陆航 (S14) takes the laugh back at once and lifts his cup to his mouth "
               "to cover half his face, while his shoulders stay loose — he really does find it funny; the window's "
               "daylight is on him and his eyes over the rim are still amused."),
     (2, "04.500", "The cup stays at his mouth and his shoulders stay down.")],
    "A cup lifted, a shoulder settling, the room's quiet."),

seg("t43", "5-1", "一只手拍在长案上", ["luchong"], ["lu_hall_desk"],
    "High-angle close: 陆崇 (S15)'s hand comes down flat on the long table with a slap — the cups jump and the file at "
    "the centre shifts in its own tray without anyone opening it; the upper two thirds is the hand pressed on the wood.",
    HALL_ENTRY + "; 陆崇 (S15)'s hand coming down on the table; the file at the centre of it",
    [(1, None, "High-angle close on the long table: the hand of 陆崇 (S15) comes down flat on the wood with a slap — "
               "the cups on the table jump and the file at the centre of it shifts inside its own open folder without "
               "anybody opening it; the upper two thirds is that hand pressed onto the wood and the bottom third is the "
               "table edge; the light on the wood is even and the print at the folder's mouth is still where it was."),
     (2, "04.500", "陆崇 (S15) speaks from above frame, [Chinese] 滚出去。这座宅子，从今天起没你的位置。"),
     (3, "08.500", "The cups stop rocking; the file lies where the jolt left it, still closed.")],
    "A slap on wood, cups jumping and settling, chairs jolting back."),

seg("t44", "5-1", "从主位上站起来", ["luchong"], ["lu_hall"],
    "Medium at the far head: 陆崇 (S15) rises from the presiding chair, his dark navy stand-collar jacket held straight "
    "in the window light, facing the near end, and one sentence presses the whole room down; standing, he holds up the "
    "whole depth of the long table by himself.",
    HALL_ENTRY_STOOD + "; 陆崇 (S15) rising from the far head into a standing position, still on the centre axis",
    [(1, None, "Medium at the far head: 陆崇 (S15) rises from the presiding chair, his dark navy stand-collar jacket "
               "held straight in the window light, and he faces down the table at the near end; one sentence presses "
               "the whole room down; standing at the far end he holds up the entire depth of the long table by himself "
               "and the sideboard and the landscape painting frame him; the ceiling light and the window keep his face "
               "and his standing figure evenly filled."),
     (2, "05.000", "He stands square on the centre axis, hands at his sides, and holds the room.")],
    "The chair easing back, his voice carrying, a room pressing down."),

seg("t45", "5-1", "满堂一震", [], ["lu_hall"],
    "Medium on the full room: the hall jolts — people on the east and west sides pull themselves back half an inch; 陆蔓 "
    "(S8) looks down at the table and 陆航 (S14) at the window sill does not move.",
    HALL_ENTRY_STOOD + "; the whole room jolting back, 陆崇 (S15) standing at the far head",
    [(1, None, "Medium across the hall: the room jolts — the people on the east side and the people on the west side "
               "draw themselves back half an inch in their chairs; 陆蔓 (S8) at the east long side looks down at the "
               "table in front of her and 陆航 (S14) at the window sill stops moving altogether; 陆崇 (S15) stands at the "
               "far head; the bottom third is the table top and the floor."),
     (2, "04.500", "The room holds the new position; nobody speaks.")],
    "Chairs drawing back, a room's held breath, the window."),

seg("t46", "5-1", "环视一圈", ["suxiaoman"], ["lu_hall"],
    "Medium at the near head: 苏小满 (S1) turns her head slowly all the way round — from the east long side to the west, "
    "to the window sill, and finally back to 陆崇 (S15) standing at the far head; she says it word by word, not loud, "
    "nothing slurred.",
    HALL_ENTRY_STOOD + "; 苏小满 (S1) at the near head, head turning from the east side round to the far head",
    [(1, None, "Medium at the near head: 苏小满 (S1) turns her head slowly all the way round — from the east long side "
               "to the west side, on to the window sill, and finally back to 陆崇 (S15) standing at the far head; she "
               "says it word by word, her voice not high and nothing slurred; the light on her stays even as she turns "
               "and the table's depth axis carries her gaze the whole way."),
     (2, "05.000", "苏小满 (S1) speaks, [Chinese] 我在陆家擦了半个月的桌子，擦得干净。"),
     (3, "09.000", "Her head comes to rest facing the far head.")],
    "Her steady voice, the room listening, a long held quiet."),

seg("t47", "5-1", "把擦得干净当底气", ["suxiaoman"], ["lu_hall"],
    "Close at the near head: 苏小满 (S1)'s gaze finally settles on 陆崇 (S15) and her chin sends half a fraction "
    "forward; her two hands do not make a single unnecessary move.",
    HALL_ENTRY_STOOD + "; 苏小满 (S1) at the near head, chin half a fraction forward, eyes on the far head",
    [(1, None, "Close at the near head: the gaze of 苏小满 (S1) finally settles on 陆崇 (S15) standing at the far head "
               "and her chin sends half a fraction forward; her two hands hang at her sides without a single "
               "unnecessary move, and she is treating the wiping she has done as her own ground to stand on; the light "
               "on her face is soft and even and her eyes do not move away."),
     (2, "05.000", "She holds the gaze and keeps her hands still.")],
    "Her breathing, the room's quiet, a distant clock."),

seg("t48", "5-1", "各自掂量", ["suxiaoman"], ["lu_hall"],
    "Over-the-shoulder at the near head: 苏小满 (S1) says it flat, the tail neither rising nor falling; the four words "
    "about weighing it for themselves are put down lightly and weigh more than the line before; she does not look at "
    "陆崇 (S15) and her gaze runs along both sides of the room.",
    HALL_ENTRY_STOOD + "; 苏小满 (S1) at the near head, gaze running along both flanks and not on the far head",
    [(1, None, "Over-the-shoulder at the near head: 苏小满 (S1) says it flat with the tail of the line neither rising "
               "nor falling; the four words about weighing it for themselves go down lightly and weigh more than the "
               "line before them; she does not look at 陆崇 (S15) and her gaze runs along both sides of the room "
               "instead; the light on her is even and her stance does not move."),
     (2, "05.000", "苏小满 (S1) speaks, [Chinese] 今天你们说的这些话，干不干净，各自掂量。"),
     (3, "09.000", "Her gaze finishes both flanks and comes to rest level in front of her.")],
    "Her flat voice, the room not answering, a cup on wood."),

seg("t49", "5-1", "我还会来", ["suxiaoman"], ["lu_hall"],
    "Close at the near head: 苏小满 (S1) bites down hard on the word about the rules — the line answers 秦律师 (S19)'s "
    "words about the evidence; as she says it her stance stays planted and her feet do not move an inch.",
    HALL_ENTRY_STOOD + "; 苏小满 (S1) at the near head, feet planted, speaking level",
    [(1, None, "Close at the near head: 苏小满 (S1) bites down hard on the word about the rules — the line is the answer "
               "to what 秦律师 (S19) said about evidence only; as she says it her stance stays planted and her feet do "
               "not move an inch on the floor; the light on her face is even and her mouth is clearly readable."),
     (2, "04.500", "苏小满 (S1) speaks, [Chinese] 核实的门，是你们自己家的规矩。我还会来。"),
     (3, "08.500", "She finishes and stays exactly where she is standing.")],
    "Her level voice, the room's held air, a clock in the hall."),

seg("t50", "5-1", "秦律师记下这一句", ["qinlvshi"], ["lu_hall"],
    "Reverse at the near head: 秦律师 (S19), three-quarter to the camera, looks up at her once — he says nothing, he "
    "only taps his pen once on the verification folder, as if putting the sentence on record.",
    HALL_ENTRY_STOOD + "; 秦律师 (S19) seated at the near head with his pen over the open folder",
    [(1, None, "Reverse at the near head: 秦律师 (S19), three-quarter to the camera, lifts his eyes to her once — he "
               "says nothing, he only taps the pen once on the open verification folder in front of him, as if putting "
               "the sentence on record; the light on him is even and the folder's pages lie open and unmarked."),
     (2, "04.500", "The pen lifts again and his eyes stay up for a moment.")],
    "A single pen tap on paper, the room's quiet, a clock."),

seg("t51", "5-1", "给老爷子一个交代", ["suxiaoman", "luchong"], ["lu_hall"],
    "Over-the-shoulder at the near head: 苏小满 (S1) says the last line slowest of all; on the words about giving the "
    "old master an answer she lifts her gaze past the far head and lands it on the landscape painting behind 陆崇 (S15) "
    "— as if looking at the man inside the painting.",
    HALL_ENTRY_STOOD + "; 苏小满 (S1) at the near head, gaze lifting past the far head to the painting on the wall",
    [(1, None, "Over-the-shoulder at the near head: 苏小满 (S1) says the last line slowest of all; on the words about "
               "giving the old master an answer she lifts her gaze past the far head where 陆崇 (S15) is standing and "
               "lands it on the landscape painting hung on the wall behind him — as if she were looking at the man "
               "inside the painting; the light on her face stays even as her eyes rise."),
     (2, "05.000", "苏小满 (S1) speaks, [Chinese] 不是来求你们。是来给老爷子一个交代。"),
     (3, "09.000", "Her eyes stay up on the painting; she does not lower them.")],
    "Her slowest line, the room not moving, a clock in the hall."),

seg("t52", "5-1", "接不住", ["luchong"], ["lu_hall"],
    "Reverse on 陆崇 (S15): he stands without moving and the centre of his brow shifts very slightly; the line lands "
    "and he does not answer it, because he cannot.",
    HALL_ENTRY_STOOD + "; 陆崇 (S15) standing at the far head, silent",
    [(1, None, "Reverse on 陆崇 (S15) at the far head: he stands without moving and the centre of his brow shifts very "
               "slightly; the line has landed and he does not take it up, because he cannot; the light on his standing "
               "figure stays even and generous and the landscape painting hangs behind his shoulder."),
     (2, "05.000", "He stays standing and says nothing at all.")],
    "A room's quiet, his breath, a distant clock."),

seg("t53", "5-1", "转身朝门走", ["suxiaoman"], ["lu_hall"],
    "Medium from the near head towards the door: 苏小满 (S1) turns round, her back to the long table and to everyone in "
    "the room, and walks towards the main doors at the near end; she walks steadily and does not look at anybody; the "
    "bottom third is her cloth shoes on the floor.",
    HALL_ENTRY_STOOD + "; 苏小满 (S1) turning away from the table at the near head and walking to the doors behind her",
    [(1, None, "Medium from the near head of the table towards the doors: 苏小满 (S1) turns round so that her back is "
               "to the long table and to everyone in the room, and she walks towards the main doors at the near end; she "
               "walks steadily and does not look back at anybody; the bottom third is her flat cloth shoes on the "
               "polished floor and the long table recedes behind her."),
     (2, "05.500", "She crosses the floor in a straight line, arms down, pace even.")],
    "Flat cloth shoes on a polished floor, a long held quiet, a chair."),

seg("t54", "5-1", "满堂目送", [], ["lu_hall"],
    "Wide: the camera stays put and the room watches her go — the people along both long sides turn their heads after "
    "her back and not one of them speaks; 陆崇 (S15) stands at the far head and 陆航 (S14) leans on the wall, and the "
    "hall is quiet enough to hear her footsteps.",
    HALL_ENTRY_STOOD + "; 苏小满 (S1) walking away towards the doors with the whole room turned after her",
    [(1, None, "Wide from inside the doors: the camera does not move and the room watches her go — the people along "
               "both long sides of the table turn their heads after her back and not one of them speaks; at the far "
               "head 陆崇 (S15) stands, at the east window sill 陆航 (S14) leans on the wall, and the hall is quiet "
               "enough to hear her footsteps on the floor; the bottom third is the table top and the polished floor."),
     (2, "05.500", "Her back reaches the doors; the room keeps looking after it.")],
    "Footsteps on a polished floor, a room saying nothing, a clock."),

seg("t55", "5-1", "原封未动", [], ["lu_hall_desk"],
    "High-angle close: the camera comes back to the centre of the long table — the kraft folder, the pages and the "
    "agreement photocopy with the thumbprint are still exactly where they were pushed, untouched; from being pushed to "
    "the centre to this room breaking up, nobody has opened them once.",
    HALL_ENTRY_STOOD + "; the file still at the centre of the long table, the room breaking up around it",
    [(1, None, "High-angle close coming back to the centre of the long table: the kraft folder, the several pages and "
               "the agreement photocopy with its pale red thumbprint are still exactly where they were pushed and have "
               "not been touched; from the moment they were pushed to the centre to this room breaking up, nobody has "
               "opened them once; the ceiling light falls steadily on the paper and the printing on it is still too "
               "small to read; the bottom third is the table edge."),
     (2, "06.000", "The file lies in the clearing hall, the print untouched, the pages shut together.")],
    "A hall emptying, distant footsteps, the ceiling light's hum."),
]

# ═══════════════════════════════════════════════════════════════════
# 场次 5-2　陆家老宅 门口 · 上午（日戏，紧接 5-1）
# 陆蔓恒在车内（中景偏右）、苏小满恒在车窗外（近半幅中轴偏左），
# 隔一扇车窗前后对视。两个关键动作点：t61 车窗降下、t73 车窗升起。
# ═══════════════════════════════════════════════════════════════════
GATE_ENTRY = (
 "the 陆 family gate tower with grey brick and grey tiled eaves at the FAR end of the depth axis facing the camera; "
 "three worn stone steps at the near end; a long saloon car parked below the steps with its flank to the camera and "
 "its window side facing the camera; 陆蔓 (S8) inside the car behind that window in the middle-ground right of centre; "
 "苏小满 (S1) outside the window in the near half a little left of centre; the flagstone ground and the car's wheel "
 "along the bottom third; clear bright morning light, faces front-lit, shadows open and low"
)

S52 = [
seg("t56", "5-2", "车刚发动", [], ["lu_gate"],
    "Wide from the mouth of the lane looking at the gate: the 陆 family old mansion's gate tower and stone steps close "
    "the depth axis, a long saloon is parked below the steps with its window side to the camera, and a thin line of "
    "exhaust just leaves the tail pipe.",
    GATE_ENTRY + "; the car just started, its body settling slightly on its springs",
    [(1, None, "Wide from the mouth of the lane towards the gate: the depth axis ends at the 陆 family old mansion's "
               "gate tower and its stone steps, and a long saloon is parked below the steps with its flank to the "
               "camera and its window side facing the camera, a thin line of exhaust just leaving the tail pipe; the "
               "bottom third is the flagstone ground; the morning is clear and bright and the whole front of the "
               "mansion reads evenly lit."),
     (2, "05.000", "The exhaust thins out; the car does not move yet.")],
    "An engine idling, exhaust, a bird in the locust tree, a distant gate."),

seg("t57", "5-2", "快步赶到车窗边", ["suxiaoman"], ["lu_gate"],
    "Medium tracking: 苏小满 (S1) comes down the steps quickly, three-quarter to the camera, and reaches the car window "
    "in a few strides; the saloon has just started and the body sinks slightly; the hem of her plain jacket lifts a "
    "little with the steps.",
    GATE_ENTRY + "; 苏小满 (S1) coming down the steps towards the car window",
    [(1, None, "Medium: 苏小满 (S1) comes down the stone steps quickly, three-quarter to the camera, and reaches the car "
               "window in a few strides; the long saloon has just started and its body sinks slightly on its "
               "springs; the hem of her plain light jacket lifts a little with the movement; she comes down the steps "
               "into the near half of frame, a little left of centre, and stops level with the closed window."),
     (2, "04.500", "She arrives at the window and turns to face the glass.")],
    "Fast cloth shoes on stone, the engine idling, her breathing coming up."),

seg("t58", "5-2", "车窗还升着", ["suxiaoman", "luman"], ["lu_gate", "car_interior"],
    "Medium at the car window: 苏小满 (S1) stands outside the window in the near half a little left of centre, facing "
    "the glass with her body slightly turned; the window is still up and the morning light lies on the glass, so 陆蔓 "
    "(S8) inside is only a soft shape.",
    GATE_ENTRY + "; the window still up; 苏小满 (S1) standing outside it; 陆蔓 (S8) a soft shape behind the glass",
    [(1, None, "Medium at the car window: 苏小满 (S1) stands outside the window in the near half of frame, a little "
               "left of centre, facing the glass with her body slightly turned; the window is still up and the morning "
               "light lies flat on the glass, and 陆蔓 (S8) inside is only a soft shape behind it; the car door's lower "
               "edge, the wheel and 苏小满 (S1)'s shoe tips fill the bottom third."),
     (2, "05.000", "苏小满 (S1) waits; the shape behind the glass does not move.")],
    "The engine idling, light traffic somewhere off the lane, a bird."),

seg("t59", "5-2", "陆女士", ["suxiaoman"], ["lu_gate"],
    "Close at the car window: 苏小满 (S1) calls once towards the glass, not loud and flat in tone; one hand rests "
    "lightly on the lower edge of the window frame without knocking; the bottom third is the car's lower door edge, the "
    "wheel and her shoe tips.",
    GATE_ENTRY + "; 苏小满 (S1) at the window, one hand resting on the frame's lower edge",
    [(1, None, "Close at the car window: 苏小满 (S1) calls once towards the glass, not loud and flat in tone; one hand "
               "rests lightly on the lower edge of the window frame and does not knock; the bottom third is the car's "
               "lower door edge, the wheel and her shoe tips; the morning light is even on her face and the glass "
               "beside her is clearly readable."),
     (2, "04.000", "苏小满 (S1) speaks, [Chinese] 陆女士。"),
     (3, "06.500", "Her hand stays on the frame and she waits for the glass to move.")],
    "The engine idling, her one flat word, a bird in the locust tree."),

seg("t60", "5-2", "玻璃后面的人", ["luman"], ["car_interior", "lu_gate"],
    "Medium from inside the car looking out through the glass: 陆蔓 (S8) sits in the rear seat, face turned to the "
    "window side, and lifts her lids to look once at the glass — she has heard, she simply does not move yet.",
    GATE_ENTRY + "; 陆蔓 (S8) in the rear seat with her face to the window side",
    [(1, None, "Medium from behind the window glass looking out: 陆蔓 (S8) sits in the rear seat in a deep-green qipao "
               "with a dark-red shawl and a pair of jade drops at her ears, her face turned to the window side, and she "
               "lifts her lids to look once at the glass in front of her — she has heard, she simply does not move yet; "
               "the car interior is lit by the morning coming through the glass and her face reads clearly."),
     (2, "05.000", "She holds the look for a beat and then lets her lids drop back half a fraction.")],
    "The engine idling through the bodywork, a faint road sound, the door trim."),

seg("t61", "5-2", "第一个动作点：车窗降下", [], ["lu_gate", "car_interior"],
    "Close on the car window: the glass comes down slowly — its top edge retreats inch by inch and the morning light "
    "cuts in through the widening gap, lighting the inside of the window frame.",
    GATE_ENTRY + "; the window glass in the act of coming down",
    [(1, None, "Close on the car window: the glass comes down slowly, its top edge retreating inch by inch, and the "
               "morning light cuts in through the widening gap and lights up the inside of the window frame; the frame "
               "and the moving glass fill the middle of the shot with the morning brightness on the glass edge; the "
               "bottom third is the car's lower door edge."),
     (2, "05.000", "The glass keeps coming down until the gap is wide enough for a voice to come out of.")],
    "The window motor's soft hum, the engine idling, the morning air moving past the frame."),

seg("t62", "5-2", "似笑非笑", ["luman"], ["car_interior", "lu_gate"],
    "Close inside the car: 陆蔓 (S8)'s face appears behind the lowered window — a smile that is not a smile, chin up, "
    "her gaze not squarely on 苏小满 (S1) but looking across from under half-lowered lids; she sits very steady with "
    "one hand on her knee.",
    GATE_ENTRY + "; the window now down, 陆蔓 (S8) revealed behind it",
    [(1, None, "Close inside the car: the face of 陆蔓 (S8) appears behind the lowered window — a smile that is not a "
               "smile, her chin up, her gaze not squarely on 苏小满 (S1) but sliding across from under half-lowered "
               "lids; she sits very steady in the rear seat with one hand on her knee; the morning light coming "
               "through the open window falls on her and the shot carries the window frame along its lower edge."),
     (2, "04.000", "陆蔓 (S8) speaks, [Chinese] 我劝你别喊了。"),
     (3, "07.000", "The half-smile stays; she does not look squarely at 苏小满 (S1).")],
    "The engine idling, her light tone, traffic somewhere off the lane."),

seg("t63", "5-2", "打上记号的人", ["luman"], ["car_interior", "lu_gate"],
    "Close inside the car: 陆蔓 (S8) unfolds the point layer by layer in a courteous tone that sounds like she is doing "
    "苏小满 (S1) a favour; her finger taps once on her knee on the words about the mark; the smile stays but stops "
    "before it reaches her eyes.",
    GATE_ENTRY + "; 陆蔓 (S8) in the rear seat, one hand on her knee",
    [(1, None, "Close inside the car: 陆蔓 (S8) unfolds the point layer by layer in a courteous tone that sounds like "
               "she is doing 苏小满 (S1) a favour; on the words about being marked her finger taps once on her knee; the "
               "half-smile stays on her face the whole time and stops before it reaches her eyes; the light through the "
               "open window is even on her."),
     (2, "05.000", "陆蔓 (S8) speaks, [Chinese] 你现在是陆崇打上记号的人。我跟你走太近，不好看。"),
     (3, "09.000", "Her finger settles back on her knee; the smile holds.")],
    "The engine idling, a light tap on fabric, her even tone."),

seg("t64", "5-2", "过肩：苏小满听着", ["suxiaoman", "luman"], ["lu_gate", "car_interior"],
    "Over-the-shoulder at the window: the shot looks past the window frame at her — 陆蔓 (S8) in the foreground inside "
    "the car, 苏小满 (S1) outside and a step nearer the camera; she listens without cutting in, both hands at her "
    "sides, and the wind moves her ponytail once.",
    GATE_ENTRY + "; 陆蔓 (S8) inside the car in the middle-ground right of centre; 苏小满 (S1) outside the window in the near half, the nearer of the two",
    [(1, None, "Over-the-shoulder at the car window: the shot looks past the window frame at 苏小满 (S1) — 陆蔓 (S8) is "
               "inside the car in the middle-ground right of centre and 苏小满 (S1) is outside the window in the near half a "
               "little left of centre, so 苏小满 (S1) is the nearer of the two and 陆蔓 (S8) the further, staggered along the car's depth and never side by side; she listens without cutting "
               "in, both hands at her sides, and the wind moves her low ponytail once; the morning light is even on her "
               "face through the open window's gap."),
     (2, "05.000", "She keeps her hands down and does not interrupt.")],
    "Wind in her hair, the engine idling, 陆蔓 (S8)'s voice from inside the car."),

seg("t65", "5-2", "铁盒的事", ["suxiaoman", "luman"], ["lu_gate", "car_interior"],
    "Over-the-shoulder at the window: 苏小满 (S1) says it very lightly, as if only to be said into the car; she leans "
    "half a fraction forward and her gaze goes over the window's lower edge into the car; the window frame crosses "
    "the lower edge of her face.",
    GATE_ENTRY + "; 苏小满 (S1) outside the window, leaning half a fraction forward",
    [(1, None, "Over-the-shoulder at the car window: 苏小满 (S1) says it very lightly, as if only to be said into the "
               "car; she leans half a fraction forward and her gaze goes over the window's lower edge into the cabin; "
               "the window frame crosses the lower edge of her face; 陆蔓 (S8) stays inside the car in the middle-ground right "
               "of centre, further from the camera than 苏小满 (S1), and the two of them remain staggered along the depth axis."),
     (2, "04.000", "苏小满 (S1) speaks, [Chinese] 铁盒的事，你是知道的。"),
     (3, "07.000", "She stays leaning that half fraction and keeps her eyes inside the car.")],
    "Wind, the engine idling, her low voice close to the glass."),

seg("t66", "5-2", "笑松了一瞬", ["luman"], ["car_interior", "lu_gate"],
    "Close inside the car: 陆蔓 (S8)'s lids lift half an inch, the habitual smile loosens for an instant and is put "
    "back at once; she does not answer straight away and moves her hand from her knee up to the window edge.",
    GATE_ENTRY + "; 陆蔓 (S8) in the rear seat, hand moving from her knee to the window edge",
    [(1, None, "Close inside the car: the lids of 陆蔓 (S8) lift half an inch, the habitual smile loosens for an "
               "instant and is put straight back; she does not answer at once, and her hand comes off her knee and up "
               "to the window's edge where it rests; the morning light through the open window is even on her face and "
               "the change is readable in it."),
     (2, "05.000", "Her hand settles on the window edge; the smile is back where it was.")],
    "The engine idling, fingertips on the window frame, a light road sound."),

seg("t67", "5-2", "谁碰谁倒霉", ["luman"], ["car_interior", "lu_gate"],
    "Close inside the car: 陆蔓 (S8) laughs out of her nose and leans half a fraction towards the window; on the words "
    "about whoever touches it she sounds lighter still, as if telling a stale story that has nothing to do with her; "
    "the morning light falls across half her face.",
    GATE_ENTRY + "; 陆蔓 (S8) in the rear seat leaning half a fraction towards the open window",
    [(1, None, "Close inside the car: 陆蔓 (S8) laughs out of her nose and leans half a fraction towards the open "
               "window; on the words about whoever touches it she sounds lighter still, as if telling a stale story that "
               "has nothing to do with her; the morning light falls across half her face and the rest of her is filled "
               "by the light coming through the glass; she stays behind the window frame."),
     (2, "05.000", "陆蔓 (S8) speaks, [Chinese] 铁盒？那玩意儿在杂物间躺了二十年。谁碰谁倒霉。"),
     (3, "09.000", "She holds the lean and the lightness; her eyes do not go to the window.")],
    "A short laugh, the engine idling, her light tone."),

seg("t68", "5-2", "敲车窗沿的手", ["luman"], ["car_interior", "lu_gate"],
    "Close on 陆蔓 (S8)'s hand on the window edge: a few fingers tap lightly on the window's lower frame, the nails "
    "bright in the morning light; the two light taps carry the same rhythm as the line about keeping away.",
    GATE_ENTRY + "; 陆蔓 (S8)'s hand resting on the window's lower frame",
    [(1, None, "Close on the hand of 陆蔓 (S8) where it rests on the car's window edge: a few fingers tap lightly on "
               "the window's lower frame, the nails bright in the morning light, and the two light taps carry exactly "
               "the same rhythm as the line about keeping away; the window frame and the open gap are right there in "
               "the shot and the light is even and clear."),
     (2, "04.500", "The fingers keep the light tapping for a moment, then settle.")],
    "Fingertips on painted metal, the engine idling, a light road sound."),

seg("t69", "5-2", "你要碰你自己碰", ["luman"], ["car_interior", "lu_gate"],
    "Close inside the car: 陆蔓 (S8) takes her eyes off 苏小满 (S1) and looks ahead towards the front of the car — the "
    "line is a hand-off; the smile is still at the corner of her mouth and her eyes have already stopped seeing her.",
    GATE_ENTRY + "; 陆蔓 (S8) in the rear seat turning her eyes away towards the front of the car",
    [(1, None, "Close inside the car: 陆蔓 (S8) takes her eyes off 苏小满 (S1) and looks ahead towards the front of the "
               "car — the line is a hand-off of the whole matter; the smile is still at the corner of her mouth and her "
               "eyes have already stopped seeing her; the light through the open window is even on her and the window "
               "frame runs across the lower part of the shot."),
     (2, "04.000", "陆蔓 (S8) speaks, [Chinese] 你要碰，你自己碰。"),
     (3, "07.000", "She keeps looking ahead; the smile stays; her eyes do not come back.")],
    "The engine idling, her tone with nothing behind it, a bird in the locust tree."),

seg("t70", "5-2", "你不帮我了", ["suxiaoman", "luman"], ["lu_gate", "car_interior"],
    "Over-the-shoulder at the window: 苏小满 (S1) lowers her voice a little and asks straight; she has not moved and is "
    "still standing outside the car, her gaze fixed on the face inside that has turned away.",
    GATE_ENTRY + "; 苏小满 (S1) outside the window, watching 陆蔓 (S8)'s turned face inside",
    [(1, None, "Over-the-shoulder at the car window: 苏小满 (S1) lowers her voice a little and asks the question "
               "straight; she has not moved and is still standing outside the car, her body slightly turned and her "
               "gaze fixed on the turned-away face inside; 陆蔓 (S8) remains inside the car in the middle-ground right of centre, "
               "further from the camera than 苏小满 (S1) in the near half, and the window frame runs between them."),
     (2, "04.000", "苏小满 (S1) speaks, [Chinese] 你不帮我了？"),
     (3, "06.500", "She holds her ground outside the window and waits.")],
    "Wind past the door, the engine idling, her low question."),

seg("t71", "5-2", "沉默一拍就是回答", ["luman"], ["car_interior", "lu_gate"],
    "Close inside the car: 陆蔓 (S8) does not turn round, only the corner of her eye moves; the jade drop at her ear "
    "swings very slightly with the car; she keeps the pause for one beat — that beat is the answer.",
    GATE_ENTRY + "; 陆蔓 (S8) in the rear seat, not turning towards the window",
    [(1, None, "Close inside the car: 陆蔓 (S8) does not turn round, only the corner of her eye moves; the jade drop at "
               "her ear swings very slightly with the car; she keeps the pause for one beat — that beat is the answer; "
               "the morning light stays even across her and the window frame runs across the lower part of the shot."),
     (2, "05.000", "The pause stretches and she still does not turn.")],
    "The engine idling, the bodywork ticking, one full beat of the room outside."),

seg("t72", "5-2", "看在你有用", ["luman"], ["car_interior", "lu_gate"],
    "Close inside the car: 陆蔓 (S8) finally turns her face back half an inch and lets the line drop; on the two words "
    "about being useful her tone is the flattest of the whole conversation, as if grading the quality of goods; then "
    "her hand lifts to press the window control on the door.",
    GATE_ENTRY + "; 陆蔓 (S8) turning half an inch back, hand lifting to the window control",
    [(1, None, "Close inside the car: 陆蔓 (S8) finally turns her face back half an inch and lets the line drop; on the "
               "two words about being useful her tone is the flattest of the whole conversation, as if grading the "
               "quality of goods; then her hand lifts off the window edge and presses the window control on the door; "
               "the light through the open window is even on her face and the frame is still down."),
     (2, "05.000", "陆蔓 (S8) speaks, [Chinese] 二十万，是看在你有用。"),
     (3, "09.000", "Her fingers close on the window control.")],
    "The engine idling, a finger pressing the control, her flat tone."),

seg("t73", "5-2", "第二个动作点：车窗升起", ["luman"], ["lu_gate", "car_interior"],
    "Close on the car window: the glass starts to go up — its lower edge rises from the inside of the window frame, "
    "first cutting off the lower half of 陆蔓 (S8)'s face and then taking the whole face away; the morning light is cut "
    "into stripes by the rising glass.",
    GATE_ENTRY + "; the window glass in the act of going up, 陆蔓 (S8) behind it",
    [(1, None, "Close on the car window: the glass starts to go up — its lower edge rises from the inside of the window "
               "frame, first cutting off the lower half of 陆蔓 (S8)'s face and then taking the whole face away; the "
               "morning light is cut into stripes by the rising glass; the car's lower door edge and the wheel sit "
               "along the bottom third and the whole front of the car reads clearly in the bright morning."),
     (2, "05.000", "The glass keeps rising; her face goes from half to nothing behind it.")],
    "The window motor's soft hum rising, the engine idling, the stripes of light moving across the paint."),

seg("t74", "5-2", "从车窗缝里丢出来", ["luman"], ["lu_gate", "car_interior"],
    "Close on the window gap: the line is thrown out of a gap that has not finished closing — the camera sits on that "
    "narrowing slot of glass, and inside it only 陆蔓 (S8)'s mouth and half an eye are left; when the line ends that "
    "half eye moves away as well.",
    GATE_ENTRY + "; the window nearly shut, only a narrow gap left with 陆蔓 (S8)'s mouth and half an eye in it",
    [(1, None, "Close on the window gap: the line is thrown out of a gap that has not finished closing — the camera "
               "sits on that narrowing slot of glass, and inside it only the mouth of 陆蔓 (S8) and half an eye are "
               "left; the morning light runs along the top edge of the rising glass; when the line ends that half eye "
               "moves away as well and the gap holds only her mouth."),
     (2, "04.000", "陆蔓 (S8) speaks, [Chinese] 现在，你是个麻烦。"),
     (3, "07.000", "The half eye goes; the gap narrows further and the mouth leaves the light.")],
    "The window motor's hum, her voice coming through a narrowing gap, the engine idling."),

seg("t75", "5-2", "嗒地一声升到顶", [], ["lu_gate"],
    "Close on the window at the top: the glass arrives at the top with a click — inside and out are cut apart for good; "
    "the glass carries the half reflection of 苏小满 (S1) and 陆蔓 (S8) inside is now only a deep-green shape.",
    GATE_ENTRY + "; the window up and closed, the car still parked below the steps",
    [(1, None, "Close on the car window at the top: the glass arrives at the top with a click — inside and out are cut "
               "apart for good; the glass carries the half reflection of 苏小满 (S1) standing outside, and inside, 陆蔓 "
               "(S8) is now only a deep-green shape with no features left in it; the flagstone ground and the car's "
               "wheel hold the bottom third and the morning light is even across the whole car side."),
     (2, "05.000", "The reflection of 苏小满 (S1) holds on the glass and does not move.")],
    "The click dying away, the engine idling, a bird in the locust tree."),

seg("t76", "5-2", "车身启动驶离", ["suxiaoman"], ["lu_gate"],
    "Medium on the car: the long saloon starts and drives away into the depth of the lane, its tyres running over the "
    "flagstone and its body passing close by 苏小满 (S1) — she stands still and only turns her face to watch the window "
    "go; the bottom third is the wheel and the ground.",
    GATE_ENTRY + "; the car starting and driving away down the depth axis; 苏小满 (S1) standing and watching",
    [(1, None, "Medium on the car: the long saloon starts and drives away into the depth of the lane, its tyres "
               "running over the flagstone and its body passing close beside 苏小满 (S1) — she stands still and only "
               "turns her face to watch the window go; the bottom third is the wheel and the ground; the gate tower "
               "stays at the far end of the depth axis and the morning stays bright across the open forecourt."),
     (2, "05.000", "苏小满 (S1) turns her head and watches the car recede; her feet do not move.")],
    "Tyres on flagstone, the engine pulling away, a long held quiet behind it."),

seg("t77", "5-2", "特写：她的脸", ["suxiaoman"], ["lu_gate"],
    "Close on 苏小满 (S1)'s face: the morning light falls across it from the front and the wind lifts the loose hair at "
    "her forehead and temples; she does not frown and her eyes do not redden, she only looks the way the car went with "
    "a very still gaze; her jawline is set and her lips do not move.",
    GATE_ENTRY + "; 苏小满 (S1) in the near half a little left of centre, watching the car go",
    [(1, None, "Close on the face of 苏小满 (S1): the morning light falls across it from the front and the wind lifts "
               "the loose hair at her forehead and her temples; she does not frown and her eyes do not redden, she "
               "only looks the way the car went with a very still gaze; her jawline is set and her lips do not move; the "
               "light on her skin is soft and even and the wind in her hair is the only thing in the frame that moves."),
     (2, "05.000", "Her eyes stay on the empty lane and her jaw stays set.")],
    "Wind in her hair, the car far down the lane and fading, a bird in the locust tree."),

seg("t78", "5-2", "台阶下只剩她一个人", ["suxiaoman"], ["lu_gate"],
    "Medium: 苏小满 (S1) stands alone at the foot of the steps in the near half a little left of centre, the long "
    "saloon gone far down the lane with only its tail left; behind her are the gate tower and the stone steps, and the "
    "bottom third is the flagstone ground and her shoe tips; the whole lane has only her on it.",
    GATE_ENTRY + "; the car far down the lane, 苏小满 (S1) alone at the foot of the steps",
    [(1, None, "Medium: 苏小满 (S1) stands alone at the foot of the steps in the near half of frame, a little left of "
               "centre, and the long saloon has gone far down the lane with only its tail left; behind her are the "
               "gate tower and the stone steps; the bottom third is the flagstone ground and her shoe tips; the whole "
               "lane has only her on it and the morning stays clear and bright across the open forecourt."),
     (2, "05.000", "She does not follow the car and does not turn back towards the door.")],
    "Wind on the lane, a bird, a very long held quiet, the gate tower's stones warming."),
]

# ═══════════════════════════════════════════════════════════════════
# 场次 5-3a　出租屋 · 深夜（夜戏，光照档 night_room_small）
# H3 文字铁律：手机屏与协议复印件上的任何文字一律不入画面，
# 只写屏光的跳动和手部动作；所有字句内容归 summary / 旁白层。
# ═══════════════════════════════════════════════════════════════════
ROOM_ENTRY = (
 "the small old wooden table at the foot of the bed in the middle-ground with its top along the bottom third; 苏小满 "
 "(S1) on the near side of it, seated on the edge of the bed with her back to the room door and three-quarter turned "
 "to the camera; the round flush ceiling light at the centre of the room switched on AND the old table lamp on the "
 "bedside cabinet switched on, both practicals lit; the small curtained window at the far end of the room with the lit "
 "night outside it; on the table top the photocopy of the agreement and her mobile phone, which starts in her hand; "
 "yellowed walls, dark red old tile floor, the bed and the table and the window and the person never lined up in a row"
)

S53A = [
seg("t79", "5-3a", "消息在不停刷新", ["suxiaoman"], ["rental_room"],
    "High-angle close on the mobile phone on the small wooden table: cold white light from the screen throws a small "
    "bright patch on the dimmer tabletop, and bars of message light jump one after another up the screen — every bar "
    "that jumps makes the frame brightness flicker; no writing appears in the frame, only the jumping light.",
    ROOM_ENTRY + "; the mobile phone in 苏小满 (S1)'s hand at the near edge of the table, its light moving",
    [(1, None, "High-angle close on the small wooden table: the mobile phone in 苏小满 (S1)'s hand throws cold white "
               "light onto the tabletop as a small bright patch, and bars of message light jump one after another up "
               "the screen — every bar that jumps makes the brightness in the frame flicker; the frame contains the "
               "jumping light only and no writing of any kind; the table top runs along the bottom third and the round "
               "ceiling light and the old table lamp are both on above."),
     (2, "05.500", "The bars keep arriving and the flicker keeps going; her thumb does not move.")],
    "A phone buzzing once against wood, the ceiling light's hum, a clock on the wall."),

seg("t80", "5-3a", "屏光打在脸上", ["suxiaoman"], ["rental_room"],
    "Close from the phone up to 苏小满 (S1)'s face: the screen's cold white light comes up from below onto her face, and "
    "as the bars of light jump her face brightens and dims with them; the room's warm light and the screen's cold light "
    "lie over each other in layers.",
    ROOM_ENTRY + "; 苏小满 (S1) seated at the near side of the table, the phone's light coming up onto her face",
    [(1, None, "Close from the phone up to the face of 苏小满 (S1): the screen's cold white light comes up from below "
               "onto her face, and as the bars of light jump upwards her face brightens and dims with them; the room's "
               "warm ceiling light and the bedside lamp lie over the cold screen light in layers on her skin, so her "
               "face is evenly readable and clearly lit; she does not raise her head."),
     (2, "05.000", "Her face keeps brightening and dimming with the bars; her eyes stay on the screen.")],
    "The phone's buzz on the table, the ceiling light's hum, her quiet breath."),

seg("t81", "5-3a", "光条一路往上堆", [], ["rental_room"],
    "Close on the screen from above: bar after bar of light stacks up along the screen — only the movement of "
    "information refreshing endlessly is given, and none of the words go into the frame.",
    ROOM_ENTRY + "; the phone lying on the table with its light moving",
    [(1, None, "Close from above on the phone's screen lying on the table: bar after bar of light stacks up along it, "
               "one pressing on another and travelling upwards; the shot gives the movement of information refreshing "
               "endlessly and none of the words go into the frame, only the light; the table top and the edge of the "
               "agreement photocopy sit along the bottom third and both lamps in the room stay on."),
     (2, "05.000", "The bars keep stacking and the light keeps shifting.")],
    "A phone buzzing twice, the wall clock, the ceiling light's hum."),

seg("t82", "5-3a", "眼跟着光条抬", ["suxiaoman"], ["rental_room"],
    "Reverse close on 苏小满 (S1): the screen's cold light runs across her face line after line, and her eyes lift a "
    "little with the bars, a small bright shape in her pupils; the ceiling light's warm light is still on her shoulder "
    "and every part of the room is fully lit.",
    ROOM_ENTRY + "; 苏小满 (S1) seated at the near side of the table, eyes lifting with the moving light",
    [(1, None, "Reverse close on 苏小满 (S1): the screen's cold white light runs across her face line after line, and "
               "her eyes lift a little as the bars go by, with a small bright shape sitting in her pupils; the warm "
               "light of the ceiling fixture is still on her shoulder and every part of the room is fully lit; her face stays "
               "clearly readable as the cold and the warm light layer over each other."),
     (2, "05.000", "Her eyes lift with the last bar and settle.")],
    "The phone's buzz, the wall clock's escapement, her steady breath."),

seg("t83", "5-3a", "看得很久", ["suxiaoman"], ["rental_room"],
    "Medium at the table: 苏小满 (S1) sits on the edge of the bed, leans forward a little, holds the phone in both hands "
    "and stares at the screen without moving; the bedside lamp's warm light falls on her right shoulder and the screen's "
    "cold light on her face; she looks for so long that the camera does not move either.",
    ROOM_ENTRY + "; 苏小满 (S1) seated on the bed's edge at the near side of the table, holding the phone in both hands",
    [(1, None, "Medium at the table: 苏小满 (S1) sits on the edge of the bed and leans forward a little, holding the "
               "phone in both hands and staring at its screen without moving her eyes; the old bedside lamp's warm light "
               "falls on her right shoulder and the screen's cold light falls on her face; she looks for so long that "
               "the camera does not move either; the round ceiling light is on above and the little window sits at the "
               "far end with the lit night beyond it."),
     (2, "06.000", "She keeps looking; only the light on her face changes as the screen refreshes.")],
    "The phone's buzz, a clock on the wall, the ceiling light's hum."),

seg("t84", "5-3a", "拇指悬在屏面上", ["suxiaoman"], ["rental_room"],
    "Close on her thumb resting on the screen: the pad of it hovers above the glass and neither comes down nor moves "
    "away; she has not swiped a single thing away.",
    ROOM_ENTRY + "; 苏小满 (S1)'s thumb hovering over the screen in her hand",
    [(1, None, "Close on the thumb of 苏小满 (S1) where it rests on the phone: the pad of it hovers above the glass and "
               "neither comes down nor moves away, and she has not swiped a single thing away; the phone's cold light "
               "falls on the pad of the thumb and on the table below, and both lamps in the room stay on."),
     (2, "05.000", "The thumb holds its place above the glass.")],
    "The clock on the wall, the phone's faint buzz, her breath."),

seg("t85", "5-3a", "输入框被点开", ["suxiaoman"], ["rental_room"],
    "Close below the screen: her thumb presses once, an input cursor appears at the lower part of the screen and blinks "
    "on and off — only the action of the input field being opened is given, and no character of any kind.",
    ROOM_ENTRY + "; the phone in 苏小满 (S1)'s hand, its input field just opened",
    [(1, None, "Close on the lower part of the screen in 苏小满 (S1)'s hand: her thumb presses once, an input cursor "
               "comes up at the bottom of the screen and blinks on and off; the frame gives the action of the input "
               "field being opened and no character of any kind appears in it; the cold screen light lies on her thumb "
               "and the table top and both room lamps stay on."),
     (2, "05.000", "The cursor keeps blinking; her thumb lifts a fraction and stays.")],
    "A single thumb press on glass, the blinking cursor making no sound, the wall clock."),

seg("t86", "5-3a", "一个一个按下去", ["suxiaoman"], ["rental_room"],
    "Tight close: her thumb goes down on the keys one at a time — each key makes the screen's cold light jump and the "
    "input area lights up one cell at a time; what she is typing stays out of the frame.",
    ROOM_ENTRY + "; 苏小满 (S1)'s thumb working on the phone in her hand above the table",
    [(1, None, "Tight close: the thumb of 苏小满 (S1) goes down on the keys one at a time — each key makes the "
               "screen's cold white light jump and the input area lights up one cell at a time; what she is typing "
               "stays out of the frame and the frame carries only the light and her moving thumb; the table top is "
               "along the bottom third and the warm lamp light falls across the back of her hand."),
     (2, "06.000", "The cells keep lighting one after another; her thumb does not slow.")],
    "Faint key taps on glass, the clock on the wall, the ceiling light's hum."),

seg("t87", "5-3a", "拇指停在发送上方", ["suxiaoman"], ["rental_room"],
    "Close above her thumb: the pad hovers over the send position on the right of the screen and stops there — it is "
    "one layer of light away from the glass and does not press down.",
    ROOM_ENTRY + "; 苏小满 (S1)'s thumb stopped above the send position",
    [(1, None, "Close above the thumb: the pad of 苏小满 (S1)'s thumb hovers over the send position on the right side of "
               "the screen and stops there — it is one layer of light away from the glass and it does not press down; "
               "the phone's cold light lies on the pad and the table below, and the frame holds on that stopped thumb "
               "with the two room lamps on in the background."),
     (2, "05.000", "The thumb stays stopped above the glass and does not commit.")],
    "The clock's escapement, her breath held, a very long held quiet."),

seg("t88", "5-3a", "唇轻轻抿了一下", ["suxiaoman"], ["rental_room"],
    "Reverse close on 苏小满 (S1): the screen's cold white light is on her face, her eyes stay on the position she has "
    "just typed at, and her lips press together lightly; her hand stops in mid-air and the room's only sound is the "
    "table lamp's small electrical hum.",
    ROOM_ENTRY + "; 苏小满 (S1) seated with her hand stopped in mid-air above the phone",
    [(1, None, "Reverse close on 苏小满 (S1): the screen's cold white light is on her face, her eyes stay fixed on the "
               "position she has just typed at, and her lips press together lightly; her hand stops in mid-air above the "
               "table and the room's only sound is the small electrical hum of the bedside lamp; the ceiling light is on "
               "and her face stays clearly readable under both lights."),
     (2, "05.000", "Her hand stays in mid-air and her lips stay pressed.")],
    "The table lamp's hum, a long held quiet, the wall clock."),

seg("t89", "5-3a", "按住协议那一处", ["suxiaoman"], ["rental_room"],
    "High-angle close on the table: the photocopy of the agreement lies on the small wooden table with an old fold "
    "crease across one corner, and her other hand comes over from beside the screen and presses down on one particular "
    "line of it — the line itself is never shown, only the spot her finger rests on and the paper around it.",
    ROOM_ENTRY + "; the agreement photocopy on the table with 苏小满 (S1)'s finger pressed on one line of it",
    [(1, None, "High-angle close on the table: the photocopy of the agreement lies on the small wooden table with an old "
               "fold crease across one corner, and the other hand of 苏小满 (S1) comes over from beside the screen and "
               "presses down on one particular line of it — the line itself is never shown, and the frame gives only "
               "the spot her finger rests on and the paper around it, with the phone's cold light lying across the "
               "sheet; both room lamps stay on above."),
     (2, "05.500", "Her finger stays pressed on that spot; the paper does not move.")],
    "Paper under a fingertip, the phone's buzz, the wall clock."),

seg("t90", "5-3a", "目光移到协议上", ["suxiaoman"], ["rental_room"],
    "Reverse close on 苏小满 (S1): her gaze moves off the phone onto the agreement photocopy on the table and stops "
    "there; the screen's cold light and the bedside lamp's warm light both fall on her face, and she does not move.",
    ROOM_ENTRY + "; 苏小满 (S1) seated, her gaze now down on the agreement on the table",
    [(1, None, "Reverse close on 苏小满 (S1): her gaze moves off the phone and down onto the agreement photocopy lying "
               "on the small wooden table and stops there; the screen's cold light and the bedside lamp's warm light "
               "both fall on her face at once and she does not move; the round ceiling light is on above her and the "
               "room reads warm and clearly lit with the window's night at the far end."),
     (2, "05.000", "Her eyes stay on the paper and her hands stay where they are.")],
    "The lamp's hum, the clock on the wall, a very long held quiet."),

seg("t91", "5-3a", "一个键一个键地删", ["suxiaoman"], ["rental_room"],
    "Close from above on the screen: her thumb goes back to the input area and presses delete again and again — the "
    "line of light in the input area retreats one cell at a time and the screen flickers with every cell that goes; she "
    "deletes slowly, one key at a time.",
    ROOM_ENTRY + "; the phone on the table with 苏小满 (S1)'s thumb deleting in the input area",
    [(1, None, "Close from above on the screen: the thumb of 苏小满 (S1) goes back into the input area and presses "
               "delete again and again — the line of light in the input area retreats one cell at a time and the screen "
               "flickers with every cell that goes; she deletes slowly, one key at a time, and no character of any kind "
               "is shown in the frame, only the retreating light; the table top and the paper lie along the bottom "
               "third and both lamps stay on."),
     (2, "06.000", "The cells keep retreating one at a time and the screen keeps flickering.")],
    "Faint key taps on glass, the wall clock, the ceiling light's hum."),

seg("t92", "5-3a", "她删的是那句", ["suxiaoman"], ["rental_room"],
    "Close on 苏小满 (S1)'s eyes: the cold white light jumps in her pupils and her gaze does not lose its level; with "
    "every cell deleted her eyes follow it down steadily — what she is deleting is the line she nearly said out loud.",
    ROOM_ENTRY + "; 苏小满 (S1) seated, her eyes following the deletion",
    [(1, None, "Close on the eyes of 苏小满 (S1): the cold white light jumps in her pupils and her gaze does not lose "
               "its level; with every cell deleted her eyes follow it down in a steady way — what she is deleting is "
               "the line she nearly said out loud; the light on her face is even and her eyes stay calm throughout, and "
               "the frame carries only her eyes and the moving light in them."),
     (2, "05.000", "Her eyes keep following and stay level.")],
    "The clock on the wall, her steady breath, a very long held quiet."),

seg("t93", "5-3a", "一个也不剩", ["suxiaoman"], ["rental_room"],
    "Tight close: the last cell of light in the input area retreats and the screen goes back to an empty lit surface; "
    "the cursor blinks on and off again — that line of text is not one character left.",
    ROOM_ENTRY + "; the phone's input area now empty, the cursor blinking",
    [(1, None, "Tight close: the last cell of light in the input area retreats and the screen goes back to an empty lit "
               "surface, and the cursor blinks on and off again — that line of text is not one character left; the "
               "frame gives the empty lit surface and the blinking cursor and no writing of any kind, with the table "
               "top and her thumbs at the bottom third and both room lamps on."),
     (2, "05.000", "The cursor keeps blinking on the empty screen.")],
    "The cursor making no sound, the wall clock, the ceiling light's hum."),

seg("t94", "5-3a", "把手机扣下", ["suxiaoman"], ["rental_room"],
    "Close: she turns the phone over and puts it face down on the small wooden table — the screen's light is eaten by "
    "the table and only a faint rim of light is left along the table's edge; her palm presses once on the back of the "
    "phone before she withdraws it.",
    ROOM_ENTRY + "; the phone being turned face down onto the table; the screen light going out of frame",
    [(1, None, "Close: 苏小满 (S1) turns the phone over and puts it face down on the small wooden table — the screen's "
               "light is eaten by the table and only a faint rim of light is left along the table's edge; her palm "
               "presses once on the back of the phone and then withdraws; the room's two lamps stay on and the frame "
               "keeps the table top and the back of the phone along the bottom third."),
     (2, "05.000", "Her hand comes away and the phone lies face down and still.")],
    "The phone touching wood, the table lamp's hum, the wall clock."),

seg("t95", "5-3a", "屋子安静下来", ["suxiaoman"], ["rental_room"],
    "Medium on the room: the rented room settles — the round ceiling light is on and the old bedside lamp is on, the "
    "yellowed walls, the dark red floor tiles and the rolled quilt are all readable; the curtain is half open at the "
    "far end and the night beyond it is lit; the only thing to hear is the wall clock going one tick at a time; the "
    "light has not been pulled down anywhere.",
    ROOM_ENTRY + "; the phone now face down on the table; 苏小满 (S1) seated still on the bed's edge",
    [(1, None, "Medium on the room: the rented room settles — the round ceiling light is on and the old bedside lamp is "
               "on, and the yellowed walls, the dark red floor tiles and the rolled quilt are all clearly readable; the "
               "curtain is half open at the far end and the night beyond it is lit; the only thing to hear is the wall "
               "clock going one tick at a time; the light has not been pulled down anywhere in the room; 苏小满 (S1) "
               "sits still on the edge of the bed in the near half with the phone face down on the table in front of "
               "her."),
     (2, "06.000", "She stays seated and does not move; the room holds its light.")],
    "A wall clock going one tick at a time, the two lamps' hum, the room's still air."),

seg("t96", "5-3a", "猛地抬头", ["suxiaoman"], ["rental_room"],
    "Close: 苏小满 (S1)'s head snaps up — the sound comes from downstairs, from below and beyond the depth of frame; she "
    "is still on the edge of the bed with one hand braced on the table's edge and her eyes go first towards the room "
    "door.",
    ROOM_ENTRY + "; 苏小满 (S1) seated with one hand on the table's edge, head lifting towards the door",
    [(1, None, "Close: the head of 苏小满 (S1) snaps up — the sound comes from downstairs, from below and beyond the "
               "depth of frame; she is still sitting on the edge of the bed with one hand braced on the table's edge and "
               "her eyes go first towards the room door; the ceiling light and the bedside lamp are both on and her face "
               "and the door behind her are both clearly readable in the same frame."),
     (2, "04.500", "Her head stays up and her eyes stay on the door.")],
    "A voice from downstairs arriving, her quick breath, the wall clock."),

seg("t97", "5-3a", "窗外与门外都亮着", [], ["rental_room"],
    "Close along the depth to the small window at the far end: the curtain is half open and the warm light of the "
    "street lamp below comes in; the stairwell light outside the room door is on as well — the night outside is lit and "
    "not dark anywhere.",
    ROOM_ENTRY + "; the small window at the far end of the room and the room door behind the camera's near side",
    [(1, None, "Close along the depth of the room to the small curtained window at the far end: the curtain is half "
               "open and the warm light of the street lamp below comes in through it; the stairwell light outside the "
               "room door is on as well, so the night is lit from both the far window and the near door; the two lamps "
               "inside stay on and the whole room reads warm and clearly lit with nothing pulled down."),
     (2, "05.000", "The light from the window and the light from the stairwell both hold.")],
    "The stairwell light's buzz through the door, the street below, the wall clock."),

seg("t98", "5-3a", "楼下那一嗓子", ["suxiaoman"], ["rental_room"],
    "Close on 苏小满 (S1): she sits on the edge of the bed with her head turned to listen to the shout from downstairs — "
    "the voice is bright and carrying, a neighbour's voice; she does not answer, and first she picks the phone up off "
    "the table and pushes it into her jacket pocket; she is alone in the frame and the neighbour is never seen.",
    ROOM_ENTRY + "; the phone picked up off the table and pushed into 苏小满 (S1)'s jacket pocket",
    [(1, None, "Close on 苏小满 (S1): she sits on the edge of the bed with her head turned to listen to the shout coming "
               "from downstairs — the voice is bright and carrying, the kind of voice a neighbour has; she does not "
               "answer, and first she picks the phone up off the table and pushes it into her jacket pocket; she is "
               "alone in the frame and the neighbour is never seen, only ever heard from downstairs and numbered (S21); the ceiling light and the bedside lamp are both on "
               "and her face is clearly lit as she listens."),
     (2, "05.000", "A neighbour's voice (S21) calls up the stairwell from below, off frame and never seen: [Chinese] 小满！楼下有个老头，等你俩钟头了！"),
     (3, "09.000", "苏小满 (S1)'s hand presses the phone down into her pocket and her head turns to the door.")],
    "A neighbour's voice calling up the stairwell, the phone going into fabric, the wall clock."),

seg("t99", "5-3a", "起身披外套", ["suxiaoman"], ["rental_room"],
    "Medium: she stands up, grabs the jacket lying at the foot of the bed and throws it on, and her feet are already "
    "moving towards the door; the bedside lamp is still on and the ceiling light is still on; the bottom third is the "
    "floor tiles and her shoes.",
    ROOM_ENTRY + "; 苏小满 (S1) rising from the bed's edge, the jacket coming off the bed onto her shoulders",
    [(1, None, "Medium: 苏小满 (S1) stands up from the edge of the bed, grabs the jacket lying at the foot of the bed "
               "and throws it over her shoulders, and her feet are already moving towards the door; the bedside lamp is "
               "still on and the ceiling light is still on; the bottom third is the dark red floor tiles and her shoes, "
               "and the table with the phone's place now empty sits behind her."),
     (2, "05.000", "She takes two steps towards the door with the jacket on and her head turning to the stairwell.")],
    "Cloth being pulled on, her quick steps on the tiles, the neighbour's voice fading below."),

seg("t100", "5-3a", "跑进楼道", ["suxiaoman"], ["rental_room"],
    "Medium: she pushes the room door open and runs into the stairwell — the stairwell light is on and it shows the "
    "stairs clearly; her footsteps knock through the stairwell one after another and one hand holds the banister as she "
    "goes down fast.",
    ROOM_ENTRY + "; the room door open to the lit stairwell beyond; 苏小满 (S1) moving out of the room",
    [(1, None, "Medium: 苏小满 (S1) pushes the room door open and runs into the stairwell — the stairwell light is on "
               "and it shows the stairs clearly; her footsteps knock through the stairwell one after another and one hand "
               "holds the banister as she goes down fast; the room behind her keeps both its lamps on and the door stays "
               "open; the frame looks along the stairwell's depth with her going down it."),
     (2, "05.000", "She takes the stairs down two at a time, one hand sliding along the banister.")],
    "Footsteps running down a stairwell, a hand sliding on a banister, the stairwell light's buzz."),
]

# ═══════════════════════════════════════════════════════════════════
# 场次 5-3b　楼门口 路灯下 · 深夜（夜戏，光照档 night_practical）
# 忠叔恒在台阶上路灯下（中景偏右，更远一档）、
# 苏小满恒在台阶下（近半幅中轴偏左，更近一档），台阶上下前后对望。
# 忠叔目光下移 → 旧红绳特写 → 「这条绳，我见过」。
# ═══════════════════════════════════════════════════════════════════
DOOR_ENTRY = (
 "the old residential block's street doorway at the FAR end of the depth axis and a little left of centre, two or "
 "three worn concrete steps up to a half-open metal gate with the stairwell light glowing through the gap, and one old "
 "street lamp directly overhead switched on and throwing a warm yellow pool over the doorstep; the concrete steps and "
 "the ground along the bottom third; 忠叔 (S18) up on those steps under the lamp, above and beyond 苏小满 (S1), in the "
 "middle-ground right of centre; 苏小满 (S1) at the foot of the steps in the near half a little left of centre, one "
 "depth step nearer the camera; a bicycle leaning against the wall beside the gate and a few old flyers on the wall; "
 "it is night and the street lamp, the stairwell light and the lamps along the street are all on"
)

S53B = [
seg("t101", "5-3b", "跑下台阶站住", ["zhongshu", "suxiaoman"], ["rental_gate"],
    "Wide at the street doorway: the old block's doorway, the half-open metal gate with the stairwell light coming "
    "through the gap, the old street lamp overhead throwing a warm yellow pool on the doorstep, the bicycle and the old "
    "flyers on the wall; 忠叔 (S18) stands under the lamp above the steps and 苏小满 (S1) comes down the stairwell and "
    "stops at the foot of the steps; the night is lit.",
    DOOR_ENTRY + "; 忠叔 (S18) standing under the lamp on the steps; 苏小满 (S1) arriving at the foot of the steps",
    [(1, None, "Wide at the street doorway of the old low-rise block: the doorway opening, the half-open metal gate "
               "with the stairwell light glowing through the gap, the old street lamp directly overhead throwing a warm "
               "yellow pool over the doorstep, a bicycle leaning against the wall beside the gate and a few old flyers "
               "pasted on the plastered wall; up on the steps under the lamp stands 忠叔 (S18) in a dark grey "
               "front-buttoned jacket with a ring of old brass keys at his waist, stooped; 苏小满 (S1) comes down the "
               "stairwell and stops at the foot of the steps; the bottom third is the concrete steps and the worn bare "
               "ground, and the night is lit rather than dark."),
     (2, "06.000", "苏小满 (S1)'s feet stop on the ground below the steps; 忠叔 (S18) does not move.")],
    "A street lamp's electrical hum, a key ring moving once at his waist, the stairwell light through the gate gap."),

seg("t102", "5-3b", "忠叔开口", ["zhongshu"], ["rental_gate"],
    "Close under the lamp: 忠叔 (S18) stands in the warm yellow light coming down from above, his back stooped and his "
    "head habitually pushed forward; he looks at her for a long time before he gets the two words out — not loud, the "
    "tail a little dry; the ring of old brass keys at his waist gives back a glint of light.",
    DOOR_ENTRY + "; 忠叔 (S18) under the lamp on the steps, head pushed forward",
    [(1, None, "Close under the old street lamp: 忠叔 (S18) stands in the warm yellow light coming down from above, "
               "which lights his face and shoulders clearly, his back stooped and his head pushed forward out of habit; "
               "he looks at her for a long time before he gets the two words out; the ring of old brass keys at his "
               "waist gives back a small glint in the lamplight; the street lamp, the stairwell light and the street "
               "lamps are all on and his whole figure reads clearly."),
     (2, "05.000", "忠叔 (S18) speaks, [Chinese] 姑娘。"),
     (3, "07.500", "He keeps his head pushed forward and his eyes on her.")],
    "A street lamp's hum, his dry two words, keys shifting at his waist."),

seg("t103", "5-3b", "她停住脚步", ["suxiaoman"], ["rental_gate"],
    "Reverse close on 苏小满 (S1): she has just come down the steps and stands at their foot, a depth step nearer the "
    "camera than 忠叔 (S18) is and a little left of centre, breathing slightly; she recognises the face and her feet "
    "slow to a stop; the bottom third is the concrete steps and the worn ground.",
    DOOR_ENTRY + "; 苏小满 (S1) at the foot of the steps, breathing slightly, coming to a stop",
    [(1, None, "Reverse close on 苏小满 (S1): she has just come down the steps and stands at their foot, a depth step "
               "nearer the camera than 忠叔 (S18) is and a little left of centre, breathing slightly; she recognises the "
               "face and her feet slow down and stop; the warm lamp light falls on her from above and behind and the "
               "stairwell light from the gate gap fills the near side of her face; the bottom third is the concrete "
               "steps and the worn bare ground."),
     (2, "05.000", "Her breathing slows; her feet stop moving on the ground.")],
    "Her breath slowing, the street lamp's hum, a distant door."),

seg("t104", "5-3b", "您是忠叔", ["suxiaoman", "zhongshu"], ["rental_gate"],
    "Over-the-shoulder at the foot of the steps: 苏小满 (S1) says it steadily, though she herself pauses half a beat on "
    "the words about the doorman; she looks up at the old man under the lamp with both hands still held above her knees "
    "from the run; 忠叔 (S18) is in the foreground under the lamp and she is a step nearer the camera, the two of them "
    "overlapping in depth.",
    DOOR_ENTRY + "; 忠叔 (S18) in the foreground under the lamp; 苏小满 (S1) at the foot of the steps, nearer the camera",
    [(1, None, "Over-the-shoulder at the foot of the steps: 苏小满 (S1) says it steadily, though on the words about the "
               "doorman she herself pauses half a beat first; she looks up at the old man under the lamp with both hands "
               "still held above her knees from the run; 忠叔 (S18) stands in the foreground under the lamp and she is a "
               "step nearer the camera, so the two of them overlap in depth up the steps and are never side by side; the "
               "lamp and the stairwell light are both on and both faces are readable."),
     (2, "05.000", "苏小满 (S1) speaks, [Chinese] 您是，老爷子家看门的忠叔。"),
     (3, "08.500", "She keeps her hands above her knees and looks up at him.")],
    "Her steady question, the street lamp's hum, keys at his waist."),

seg("t105", "5-3b", "他抬眼看她", ["zhongshu"], ["rental_gate"],
    "Reverse close on 忠叔 (S18): he does not answer at once, his clouded old eyes lift to look at her once and his "
    "Adam's apple moves; the warm lamp light brings out the lines on his face very clearly.",
    DOOR_ENTRY + "; 忠叔 (S18) under the lamp on the steps, eyes lifting",
    [(1, None, "Reverse close on 忠叔 (S18): he does not answer at once, his clouded old eyes lift to look at her once "
               "and his Adam's apple moves; the warm yellow light of the old street lamp brings out the lines on his "
               "face very clearly and the stairwell light fills the near side; the whole figure is evenly lit and "
               "readable, the night around him being lit rather than dark."),
     (2, "05.000", "He holds her gaze for a beat and does not speak.")],
    "A swallow in his throat, the street lamp's hum, the stairwell light's buzz."),

seg("t106", "5-3b", "也开车的", ["zhongshu"], ["rental_gate"],
    "Close under the lamp: 忠叔 (S18) slowly shakes his head, and as he says it his gaze leaves her face and goes to "
    "the far end of the street; the four words about driving come out very lightly, as if fished out of something long "
    "gone; he coughs once and draws his gaze back.",
    DOOR_ENTRY + "; 忠叔 (S18) under the lamp, head shaking, gaze moving to the far street",
    [(1, None, "Close under the old street lamp: 忠叔 (S18) slowly shakes his head, and as he says it his gaze leaves "
               "her face and goes to the far end of the street; the four words about driving come out very lightly, as if "
               "fished out of something long gone that nobody has mentioned; the warm lamp light holds the lines on his "
               "face; the lamps along the street are on all the way into the distance."),
     (2, "05.000", "忠叔 (S18) speaks, [Chinese] 看门的。也开车的。"),
     (3, "08.500", "He coughs once and draws his gaze back to her.")],
    "A slow cough, his dry voice, the street lamp's hum."),

seg("t107", "5-3b", "目光下移", ["zhongshu", "suxiaoman"], ["rental_gate"],
    "Close along 忠叔 (S18)'s gaze: his eyes move down from 苏小满 (S1)'s face — past her jaw, past her neck; the depth "
    "of the shot has his old eyes in front at one side and her collar behind, and one downward line of sight pins the "
    "two together.",
    DOOR_ENTRY + "; 忠叔 (S18)'s old eyes in the foreground, 苏小满 (S1)'s collar behind him in depth",
    [(1, None, "Close along the line of 忠叔 (S18)'s gaze: his eyes move down from the face of 苏小满 (S1) — past her jaw, "
               "past her neck; the depth of the shot has his old eyes in front at one side of frame and her collar "
               "behind, and one downward line of sight pins the two of them together; the warm lamp light falls on both "
               "and the street lamp, the stairwell light and the street lamps are all on."),
     (2, "05.000", "The downward look stops at her collar and stays there.")],
    "The street lamp's hum, his breath, a distant door."),

seg("t108", "5-3b", "领口那截旧红绳", ["suxiaoman"], ["rental_gate"],
    "Close landing on the collar: the collar of her plain light jacket is open a little and between the stand collars of "
    "her work clothes a short length of old red cord shows, its knot rubbed furry; the warm lamp light lands on that "
    "short length of cord and shows that old colour very clearly.",
    DOOR_ENTRY + "; 苏小满 (S1)'s collar with the old red cord showing at her chest",
    [(1, None, "Close landing on her collar: the collar of 苏小满 (S1)'s plain light jacket is open a little and "
               "between the stand collars of her work clothes a short length of old red cord shows, its knot rubbed furry "
               "from wear; the warm yellow light of the street lamp lands on that short length of cord and shows that old "
               "colour very clearly; the street lamp, the stairwell light and the street lamps are all on and the whole "
               "frame is warm and clearly readable."),
     (2, "05.000", "The cord stays where it is; the lamplight holds on it.")],
    "The street lamp's hum, a faint fabric shift, a very long held quiet."),

seg("t109", "5-3b", "这条绳我见过", ["zhongshu"], ["rental_gate"],
    "Close under the lamp: 忠叔 (S18)'s voice goes hoarse and he starts himself with the line — as if it had been held "
    "in too long and he was not ready for it even as it left him; the hand on his arm, its back covered with old age "
    "spots, lifts to point vaguely and then drops again.",
    DOOR_ENTRY + "; 忠叔 (S18) under the lamp, one hand lifting and dropping",
    [(1, None, "Close under the old street lamp: the voice of 忠叔 (S18) goes hoarse and he gives a small start on the "
               "line — as if it had been held in too long and he was not ready for it even as it left him; the hand on "
               "his arm, its back covered with old age spots, lifts to point vaguely at her and then drops back to his "
               "side; the warm lamp light is even on his face and the keys at his waist hang still."),
     (2, "05.000", "忠叔 (S18) speaks, [Chinese] 这条绳，我见过。"),
     (3, "08.500", "His hand has dropped; he stays under the lamp and looks at her.")],
    "His hoarse voice, the street lamp's hum, a key shifting once."),

seg("t110", "5-3b", "她眼睛抬起来", ["suxiaoman"], ["rental_gate"],
    "Reverse close on 苏小满 (S1): her eyes lift at once and fix straight on 忠叔 (S18) — she has understood the weight "
    "of the sentence; the lamp light lights her face very clearly, her lips do not move and her eyes change first.",
    DOOR_ENTRY + "; 苏小满 (S1) at the foot of the steps, eyes lifting onto 忠叔 (S18)",
    [(1, None, "Reverse close on 苏小满 (S1): her eyes lift at once and fix straight on 忠叔 (S18) standing above her on "
               "the steps — she has understood the weight of the sentence; the warm street lamp light falls on her face "
               "and lights it very clearly, her lips do not move and her eyes change before anything else does; the "
               "stairwell light from the gate gap fills the near side of her face and the whole figure reads clearly."),
     (2, "05.000", "Her eyes stay fixed on him and her lips stay closed.")],
    "Her steady breath, the street lamp's hum, the stairwell light's buzz."),

seg("t111", "5-3b", "整个人僵住", ["suxiaoman"], ["rental_gate"],
    "Close on 苏小满 (S1)'s face: she is frozen where she stands — her lashes stop and do not blink, her throat gathers "
    "in once and her shoulders forget to move; the warm lamplight falls on half her face and the street lamp sits as a "
    "small shape in her pupils.",
    DOOR_ENTRY + "; 苏小满 (S1) at the foot of the steps, frozen in place",
    [(1, None, "Close on the face of 苏小满 (S1): she is frozen where she stands — her lashes stop and do not blink, her "
               "throat gathers in once and her shoulders forget to move; the warm yellow lamplight falls on half her face "
               "and the old street lamp sits as a small bright shape in her pupils; the night around her is lit by the "
               "lamp, the stairwell light and the street lamps, and her face is clearly readable."),
     (2, "05.000", "She does not move; the lamplight holds on her.")],
    "A very long held quiet, her breath stopping, the street lamp's hum."),

seg("t112", "5-3b", "明晚九点修车铺", ["zhongshu", "suxiaoman"], ["rental_gate"],
    "Close under the lamp: 忠叔 (S18) says it word by word as if afraid she will not remember; he leans his body "
    "forward a little and the ring of old brass keys at his waist moves with him; his eyes do not go to her cord again, "
    "they go straight into her eyes.",
    DOOR_ENTRY + "; 忠叔 (S18) under the lamp leaning forward; 苏小满 (S1) at the foot of the steps",
    [(1, None, "Close under the old street lamp: 忠叔 (S18) says it word by word as if afraid she will not remember it; "
               "he leans his body forward a little and the ring of old brass keys at his waist moves with him; his eyes "
               "do not drop to her cord again, they go straight into her eyes; the place he names is only mentioned in "
               "the line and nothing of it appears in the frame, the shot staying on him under the lamp with the lit "
               "street behind."),
     (2, "05.000", "忠叔 (S18) speaks, [Chinese] 明晚九点，城东快活巷口。我侄子开的修车铺。"),
     (3, "09.000", "He holds his eyes in hers and stays leaning forward.")],
    "His careful voice, keys moving at his waist, the street lamp's hum."),

seg("t113", "5-3b", "很轻地点头", ["suxiaoman"], ["rental_gate"],
    "Reverse close on 苏小满 (S1): she listens and nods once — very slightly, almost not there; she is still standing at "
    "the foot of the steps and has not moved forward; the bottom third is the concrete steps and her shoe tips.",
    DOOR_ENTRY + "; 苏小满 (S1) at the foot of the steps, nodding very slightly",
    [(1, None, "Reverse close on 苏小满 (S1): she listens and nods once — very slightly, almost not there; she is still "
               "standing at the foot of the steps and has not moved forward a step; the warm lamp light falls on her from "
               "above and the stairwell light fills the near side of her face; the bottom third is the concrete steps and "
               "her shoe tips and the whole figure is clearly readable."),
     (2, "05.000", "The nod finishes and she stays exactly where she is.")],
    "A long held quiet, her breath, the street lamp's hum."),

seg("t114", "5-3b", "憋了十五年", ["zhongshu"], ["rental_gate"],
    "Close under the lamp: 忠叔 (S18) says the last line very low with the three words about fifteen years bitten down "
    "hardest; when it is done he takes his gaze off her face and looks towards the doorway as if he were already "
    "moving away; the warm lamplight lays his shadow on the steps.",
    DOOR_ENTRY + "; 忠叔 (S18) under the lamp, gaze moving off her towards the doorway",
    [(1, None, "Close under the old street lamp: 忠叔 (S18) says the last line very low with the three words about "
               "fifteen years bitten down hardest; when it is done he takes his gaze off her face and looks towards the "
               "street doorway as if he were already moving away; the warm yellow lamplight lays his shadow back along "
               "the concrete steps and the whole figure stays clearly readable."),
     (2, "05.000", "忠叔 (S18) speaks, [Chinese] 有些话，我憋了十五年了。"),
     (3, "08.500", "His gaze stays off her and towards the doorway; his body starts to turn.")],
    "His lowest line, the street lamp's hum, keys at his waist."),

seg("t115", "5-3b", "转身往街口走", ["zhongshu"], ["rental_gate"],
    "Medium: 忠叔 (S18) turns round with his back to 苏小满 (S1) and walks towards the far end of the street — his back "
    "is stooped but his steps are quick; the lamplight lights his back first and then pushes him further away down the "
    "frame; the bottom third is the worn ground.",
    DOOR_ENTRY + "; 忠叔 (S18) turning away and walking towards the far end of the street",
    [(1, None, "Medium: 忠叔 (S18) turns round with his back to 苏小满 (S1) and walks towards the far end of the street "
               "— his back is stooped but his steps are quick; the lamplight lights his back first and then pushes him "
               "further away into the depth of frame; the lamps along the street are on all the way so his receding "
               "figure stays readable; the bottom third is the worn bare ground."),
     (2, "05.500", "He walks further down the street and gets smaller; the keys at his waist move with each step.")],
    "Quick flat steps on worn ground, keys jingling, the street lamp's hum."),

seg("t116", "5-3b", "手虚碰领口那根绳", ["suxiaoman"], ["rental_gate"],
    "Medium at the foot of the steps: 苏小满 (S1) is still standing where she was, her gaze following 忠叔 (S18)'s "
    "back; one of her hands has risen to her collar and her fingertips touch the outside of that cord lightly — she "
    "does not dare touch it properly; the wind lifts the hem of her jacket.",
    DOOR_ENTRY + "; 苏小满 (S1) at the foot of the steps, watching him go, fingertips at her collar",
    [(1, None, "Medium at the foot of the steps: 苏小满 (S1) is still standing where she was and her gaze follows the "
               "back of 忠叔 (S18); one of her hands has risen to her collar and her fingertips touch the outside of "
               "that old cord lightly — she does not dare touch it properly; the wind lifts the hem of her jacket; the "
               "warm lamp light is on her from above and the stairwell light from behind, and the steps and the ground "
               "hold the bottom third."),
     (2, "05.500", "Her fingertips stay on the outside of the cord without pressing; her feet do not move.")],
    "Wind in her jacket, his keys jingling away, the street lamp's hum."),

seg("t117", "5-3b", "本集收尾", ["suxiaoman"], ["rental_gate"],
    "Wide closing on the street doorway: the old block's doorway — the concrete steps, the half-open metal gate, the "
    "bicycle leaning beside it and the old flyers on the wall all lit in the warm yellow of the old street lamp; the "
    "stairwell light is on too; 忠叔 (S18)'s back has gone far off and 苏小满 (S1) stands alone at the foot of the "
    "steps; the bottom third is the concrete steps and the ground.",
    DOOR_ENTRY + "; 忠叔 (S18) gone far off; 苏小满 (S1) alone at the foot of the steps",
    [(1, None, "Wide closing on the street doorway of the old low-rise block: the concrete steps, the half-open metal "
               "gate, the bicycle leaning against the wall beside it and the old flyers pasted there are all lit in the "
               "warm yellow of the old street lamp, and the stairwell light is on as well; 忠叔 (S18)'s back has gone far "
               "off down the street and 苏小满 (S1) stands alone at the foot of the steps in the near half; the bottom "
               "third is the concrete steps and the worn ground, and the night is lit rather than dark."),
     (2, "07.000", "She stands still at the foot of the steps and the doorway holds its light.")],
    "The street lamp's hum, the stairwell light's buzz, his keys jingling far off, then the open night taking over.",
    "A low string rises and lifts once, then holds suspended."),
]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(OUT, exist_ok=True)
    dump("scene51.json", S51)
    dump("scene52.json", S52)
    dump("scene53a.json", S53A)
    dump("scene53b.json", S53B)
    allseg = S51 + S52 + S53A + S53B
    ids = [x["id"] for x in allseg]
    assert ids == ["ep05_t%02d" % i for i in range(1, len(ids) + 1)], "id 不连续"
    print("  合计 %d 段，id 连续 ep05_t01 – ep05_t%02d" % (len(ids), len(ids)))
