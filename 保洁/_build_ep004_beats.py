# -*- coding: utf-8 -*-
"""ep004 分镜 beats 生成器（第③步产物）
用紧凑 DSL 写，装配成渲染器要的 9 字段 JSON。
为什么要脚本而不是手写 JSON：一段 JSON 有 9 个字段名 + 2000 字符样板，98 段手写会又慢又容易漏字段；
脚本能保证「字段齐全 / id 连续 / retention 默认值一致 / shots 时刻格式统一」这些机械正确性。
内容（summary / shots / soundscape）仍然是逐段手写的，不是模板套出来的。
"""
import json, os, io, sys, re

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "ep004_beats")
EPS = "ep04"

CHARS = {"suxiaoman", "nvguibin", "qianjingli", "xiaotang", "afang", "zhouzongjian",
         "xiaoluo", "luman", "waipo", "zhangzong", "yisheng", "qiantai", "luhang",
         "luchong", "xinfu", "shoufeiyuan", "zhongshu", "qinlvshi", "hushizhang"}
SCENES = {"hospital_station", "hospital_corridor", "lu_storage", "lu_study",
          "office_pano", "office_left", "office_right", "office_back", "office_mid", "office_close",
          "lu_hall", "lu_hall_desk", "lu_gate", "lu_gatehouse", "lu_veranda",
          "rental_room", "rental_gate", "corridor_pano", "hospital_ward", "hospital_bench",
          "hospital_pay", "locker", "lobby_1f", "building_exterior", "car_interior", "alley_gate"}


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
    return d


def dump(fname, segs):
    p = os.path.join(OUT, fname)
    io.open(p, "w", encoding="utf-8").write(
        json.dumps(segs, ensure_ascii=False, indent=1) + "\n")
    print("  %-14s %3d 段  (%s – %s)" % (fname, len(segs), segs[0]["id"], segs[-1]["id"]))


# ═══════════════════════════════════════════════════════════════════
# 场次 4-1a　市一院 住院部护士站 · 清晨（日戏）
# 护士长恒在台内（远），苏小满恒在台外（近），隔台前后对望。
# ═══════════════════════════════════════════════════════════════════
S41A = [
seg("t01", "4-1a", "清晨的护士站", [], ["hospital_station"],
    "Opening wide across the nurses' counter on a bright early morning: the pale counter runs across the "
    "MID-ground of the depth axis with an old desktop computer and several stacks of case files on it, the "
    "wall of medicine drawers closes the far side, ceiling lights on and clear morning window light raking "
    "in from the side and behind. Nobody is in the frame yet.",
    "the nurses' station of the city No.1 hospital on a bright early morning, seen from outside the counter "
    "looking in; the pale counter runs across the MID-ground, the wall of small medicine drawers closes the "
    "far side, the pale tile floor along the bottom third; the station is empty of people.",
    [(1, None, "Wide along the depth axis from outside the counter: the pale counter runs across the middle of "
               "frame with an old desktop computer, three neat stacks of case files, a pen and a thick "
               "bed-allocation ledger lying on it; behind it the wall of small built-in medicine drawers; the "
               "ceiling lights are on and clear morning window light comes in from the left and behind, so the "
               "whole station is bright, open and clean with every corner readable; the bottom third of frame "
               "is the counter edge and the pale tile floor."),
     (2, "06.000", "Slightly lower and closer to the counter, the light along the counter top even and generous, "
                  "the case-file stacks square to the lens, the drawer wall behind still fully lit and in "
                  "focus — a held establishing beat with nobody in it yet.")],
    "The building's morning air, the faint hum of the ceiling lights, a trolley wheel rattling somewhere down "
    "the corridor, and a pager buzzing twice far off.",
    "N/A"),

seg("t02", "4-1a", "翻本子的手", ["hushizhang"], ["hospital_station"],
    "Medium from inside the counter: the head nurse stands on the far side of it, head down, turning back the "
    "pages of the thick bed-allocation ledger with both hands, her brow knotted and her mouth pulled tight "
    "with the difficulty of what she is reading.",
    "the same nurses' station; 护士长 (S20) now stands behind the counter on the FAR side, facing out towards "
    "the near side, a thick bed-allocation ledger open in both hands at chest height; her pale uniform, white "
    "nursing shoes and the ballpoint pen clipped in her chest pocket are visible; the counter edge still cuts "
    "the bottom third.",
    [(1, None, "Medium from inside the counter looking out over it: 护士长 (S20), a woman in her early fifties "
               "with slightly rounded shoulders and thin half-rimmed spectacles, stands on the far side facing "
               "the near side, head down, turning back the pages of the thick ledger; her brow is knotted and "
               "her mouth pulled tight; the ceiling light falls evenly on her face and the pale counter."),
     (2, "05.200", "High angle down onto the open ledger: her finger holds one page flat while the other hand "
                  "runs down a column of bed numbers, and the tip of her pen comes to rest and stays there, "
                  "not touching the paper.")],
    "Pages turning in a thick ledger, the ballpoint pen tapping once against the paper, her plain apron and the "
    "faint squeak of her white shoes shifting on the tile.",
    "N/A"),

seg("t03", "4-1a", "今天要挪一挪", ["hushizhang", "suxiaoman"], ["hospital_station"],
    "The head nurse presses the page flat, looks up towards the near side and speaks, taking two tries to get "
    "the first clause out; 苏小满 (S1) is on the near side of the counter with her back to the door.",
    "护士长 (S20) still behind the counter with one hand pressed flat on the open ledger; 苏小满 (S1) has just "
    "arrived on the NEAR side of the counter, a little left of centre, facing in towards it, a plain thin coat "
    "thrown over her navy work shirt, her low ponytail between her shoulder blades; her hands hang at her sides.",
    [(1, None, "Medium inside the counter: 护士长 (S20) presses the open page flat under her palm and lifts her "
               "eyes towards the near side; her lips move twice before the words come, and she says, in a low "
               "apologetic standard Mandarin: [Chinese] 老太太的床位……今天要挪一挪。"),
     (2, "06.000", "Reverse over her shoulder towards the near side: 苏小满 (S1) stands facing the counter, and "
                  "on hearing it her body stops for a beat, her right hand rising to hover just above the "
                  "counter edge without touching it.")],
    "Her low apologetic voice cutting across the corridor air, a trolley rattling further away, the ceiling "
    "lights humming, and the girl's coat shifting as she stops moving.",
    "N/A"),

seg("t04", "4-1a", "挪去哪", ["suxiaoman", "hushizhang"], ["hospital_station"],
    "苏小满 (S1) asks where the bed is going to, her hand still hovering over the counter edge, her voice low "
    "and flat.",
    "苏小满 (S1) on the NEAR side of the counter, right hand hovering above the counter edge; 护士长 (S20) "
    "behind the counter with her palm still on the ledger.",
    [(1, None, "Medium three-quarter on 苏小满 (S1) from the near side of the counter, 护士长 (S20) blurred in the "
               "foreground: she keeps her hand where it is and asks, without raising her voice, "
               "[Chinese] 挪去哪？"),
     (2, "04.000", "Closer on her face as she waits for the answer: her jaw is set, her eyes stay level on the "
                  "woman behind the counter, and the hand at the counter edge does not move.")],
    "Her low steady slightly hoarse voice, the faint hum of the ceiling lights, a page settling in the ledger.",
    "N/A"),

seg("t05", "4-1a", "上面打了招呼", ["hushizhang", "suxiaoman"], ["hospital_station"],
    "The head nurse presses the ledger down, drops her voice and looks away towards the computer on the counter "
    "as she explains that the bed is going home for two weeks because someone upstairs has asked for it.",
    "护士长 (S20) behind the counter, her palm flat on the ledger; 苏小满 (S1) on the near side of the counter, "
    "hand now resting on the counter edge, facing in.",
    [(1, None, "Medium inside the counter: 护士长 (S20) presses the ledger down harder, drops her voice and lets "
               "her eyes slide away towards the old computer on the counter as she says, "
               "[Chinese] 先回家等两周。上面打了招呼，说有人要用床。"),
     (2, "07.000", "Closer on her face: the words cost her something; her brows pull together, she glances once "
                  "to her left along the counter and back down, and the hand on the ledger presses a little "
                  "harder than it needs to.")],
    "Her lowered voice close to the counter, the ledger's cover sliding on the laminate, a distant lift chime "
    "somewhere in the building.",
    "N/A"),

seg("t06", "4-1a", "哪个上面", ["suxiaoman", "hushizhang"], ["hospital_station"],
    "苏小满 (S1) steps half a pace forward, plants one hand on the counter edge and asks which upstairs she "
    "means, looking straight at the head nurse.",
    "苏小满 (S1) on the near side of the counter, one hand resting on the counter edge; 护士长 (S20) behind the "
    "counter, her eyes still turned away towards the computer.",
    [(1, None, "Over-shoulder from behind 护士长 (S20) towards the near side: 苏小满 (S1) steps half a pace "
               "forward, lays one hand flat on the counter edge, and asks with her eyes level on the woman "
               "across the counter: [Chinese] 上面？哪个上面？"),
     (2, "05.000", "Tighter on 苏小满 (S1): the hand on the counter edge takes her weight, her chin comes up a "
                  "little, and she does not blink; across the counter the head nurse's eyes come back to meet "
                  "hers and then drop away again.")],
    "Her hand sliding onto the laminate counter edge, the low hum of the lights, the girl's steady breathing "
    "close to the counter.",
    "N/A",

),

seg("t07", "4-1a", "你别为难我", ["hushizhang", "suxiaoman"], ["hospital_station"],
    "The head nurse meets those eyes for half a second, closes the ledger, tucks the pen back into her pocket "
    "and shakes her head lightly as she refuses to answer.",
    "护士长 (S20) behind the counter, 苏小满 (S1) on the near side with her hand on the counter edge, facing in.",
    [(1, None, "Medium inside the counter: 护士长 (S20) takes those eyes for half a second, then brings the "
               "ledger shut, slides the pen back into her chest pocket and shakes her head once, lightly, as "
               "she says, [Chinese] 小苏，你别为难我。"),
     (2, "04.600", "Closer on her as she finishes: her eyes have gone down to the counter top, the shut ledger "
                  "under her palm, her shoulders drawing in a fraction; the ceiling light still falls evenly "
                  "across her pale uniform with the shadow under her chin soft and open.")],
    "The ledger's covers meeting with a soft knock, her plain voice thinning out, the corridor air and a "
    "distant trolley.",
    "N/A"),

seg("t08", "4-1a", "手收回身侧", ["suxiaoman", "hushizhang"], ["hospital_station"],
    "Reverse on 苏小满 (S1): her hand comes off the counter edge and back to her side, she does not press the "
    "question, and her gaze moves off the nurse's face onto the old computer sitting on the counter.",
    "苏小满 (S1) on the near side of the counter, her hand just leaving the counter edge; 护士长 (S20) behind the "
    "counter with the shut ledger under her palm.",
    [(1, None, "Reverse medium on 苏小满 (S1) from inside the counter, 护士长 (S20) in the foreground: her hand "
               "comes slowly off the counter edge and back down to her side; she does not press the question "
               "again, and her gaze moves off the woman's face and settles instead on the old desktop computer "
               "sitting on the counter."),
     (2, "05.400", "Closer on her eyes and jaw: nothing rises in her face; she stands very straight, the "
                  "plain thin coat hanging still, and the only movement is her lower jaw setting once.")],
    "The quiet of her coat settling, a page left flat in the shut ledger, the corridor's morning air.",
    "N/A"),

seg("t09", "4-1a", "转身去走廊", ["suxiaoman", "hushizhang"], ["hospital_station", "hospital_corridor"],
    "The head nurse opens another register and lowers her head; 苏小满 (S1) turns away from the counter and "
    "walks off down the corridor with her back to the lens.",
    "苏小满 (S1) on the near side of the counter, having just taken her hand down; 护士长 (S20) behind the "
    "counter with the shut ledger.",
    [(1, None, "Medium from inside the counter: 护士长 (S20) opens a different register and lowers her head "
               "back over it; in the near half of frame 苏小满 (S1) turns away from the counter, her back to "
               "the lens, and starts walking out towards the corridor."),
     (2, "05.200", "The camera holds on the counter as she leaves frame: the shut ledger, the stacks of case "
                  "files, the old computer and the drawer wall behind all stay evenly lit, and the pale tile "
                  "floor is empty where she was standing.")],
    "Her steps walking away down the corridor, a register opening, the ceiling lights humming, her coat "
    "fading out of the room's air.",
    "N/A",
    ref_notes={"hospital_corridor": "Use this image ONLY for the corridor she walks into at the end of the "
              "beat — the nurses' station in the previous reference stays the location and lighting reference "
              "for the whole segment. Do not re-light the station from the corridor image."}),
]

# ═══════════════════════════════════════════════════════════════════
# 场次 4-1b　住院部走廊 · 清晨（日戏）
# 医生恒在纵深远端，苏小满恒在近端，沿走廊纵深前后对望。
# ═══════════════════════════════════════════════════════════════════
S41B = [
seg("t10", "4-1b", "走廊的尽头", [], ["hospital_corridor"],
    "Opening wide down the long inpatient corridor on a bright early morning: it runs away along the depth "
    "axis to a bright far end, ward doors with glass observation panels along one wall, a row of empty "
    "benches against the other, the fluorescents on and the polished tile floor along the bottom third.",
    "the inpatient-department corridor of the city No.1 hospital, bright early morning, the fluorescents on; "
    "the camera at the NEAR end looking down the length of the corridor; nobody in the frame.",
    [(1, None, "Wide down the length of the corridor: it runs away along the depth axis towards a bright far "
               "end; ward doors with glass observation panels line one wall, a row of empty benches stands "
               "against the other, the ceiling fluorescents are all on and the whole corridor is bright and "
               "evenly lit; the polished tile floor fills the bottom third, empty."),
     (2, "06.000", "The same corridor held a moment longer, the far end still bright, the empty benches still "
                  "empty, no shadow pooling anywhere along the floor or the skirting line.")],
    "The long even hum of the ceiling fluorescents, a nurse's rubber-soled footsteps crossing a far junction, "
    "a lift chime somewhere above.",
    "N/A"),

seg("t11", "4-1b", "走廊尽头的人", ["suxiaoman", "yisheng"], ["hospital_corridor"],
    "苏小满 (S1) walks away from the lens down the corridor a little left of centre, unhurried, and a man in "
    "a white coat is already standing at the bright far end, waiting for her.",
    "苏小满 (S1) has entered the corridor from the near end and is walking away from the lens along the depth "
    "axis, a little left of centre, the plain thin coat over her navy work shirt, hands at her sides; 医生 (S11) "
    "stands at the FAR end of the corridor in a white coat.",
    [(1, None, "Medium down the corridor, camera behind 苏小满 (S1) as she walks away from the lens along the "
               "depth axis, a little left of centre, unhurried; at the bright far end 医生 (S11) stands waiting "
               "in a white coat with an ID badge on his chest, small in the frame; the tile floor runs between "
               "them."),
     (2, "05.400", "Closer behind her shoulder as she nears him: her low ponytail sways with the walk, the "
                  "plain thin coat's hem moving, and the man at the far end turns his head a little towards "
                  "her approach.")],
    "Her flat shoes on the polished tile, her coat hem brushing, the corridor fluorescents, a distant trolley "
    "wheel.",
    "N/A"),

seg("t12", "4-1b", "他插着一只手", ["suxiaoman", "yisheng"], ["hospital_corridor"],
    "医生 (S11) stands in profile at the far end, one hand in his coat pocket, facing back down the corridor; "
    "苏小满 (S1) comes to a stop in the near half in front of him, and the two of them are staggered along the "
    "corridor's depth with him further from the camera and her nearer, never side by side.",
    "苏小满 (S1) stopped at the near end of the corridor facing the far end; 医生 (S11) at the far end in "
    "profile, one hand in his white coat pocket, facing the near end.",
    [(1, None, "Medium from the NEAR end of the corridor with 苏小满 (S1) in the near half of frame and 医生 "
               "(S11) in the far half: he stands in profile at the corridor's far end, one hand pushed into his "
               "white coat pocket, facing back down the corridor towards her; she has come to a stop in the near "
               "half facing him, the whole length of floor open and readable between them, both of them lit evenly "
               "by the fluorescents above."),
     (2, "05.600", "Reverse down the corridor: he keeps the profile and the pocketed hand, his head angled "
                  "towards her while his eyes stay off down the corridor; she stands still, weight even, her "
                  "hands at her sides, the floor between them clearly readable.")],
    "Fluorescent hum, a paper rustle from the pocketed hand, her steady unhurried breathing.",
    "N/A"),

seg("t13", "4-1b", "被人打了招呼", ["yisheng", "suxiaoman"], ["hospital_corridor"],
    "医生 (S11) turns his head towards her, drops his voice and tells her that her own schedule has been "
    "interfered with by somebody, the hand in his pocket shifting as he speaks.",
    "医生 (S11) at the far end in profile with his hand in his pocket; 苏小满 (S1) stopped at the near end "
    "facing him.",
    [(1, None, "Medium close on 医生 (S11), the corridor bright behind him: he turns his head towards her, "
               "drops his voice and says, [Chinese] 小苏，你的排期，被人打了招呼。"),
     (2, "05.000", "Tighter on his face as he keeps his eyes off down the corridor: the hand inside the pocket "
                  "moves once, his white coat collar shifting, and the fluorescents keep every plane of his "
                  "face open and readable.")],
    "His lowered voice in the corridor's echo, the hum of the fluorescents, a far-off lift chime.",
    "N/A"),

seg("t14", "4-1b", "谁的手这么长", ["yisheng", "suxiaoman"], ["hospital_corridor"],
    "The doctor glances down both ends of the corridor to make sure nobody is near, then finishes the sentence "
    "telling her she knows well enough whose hand is that long.",
    "医生 (S11) at the far end of the corridor, 苏小满 (S1) at the near end facing him.",
    [(1, None, "Medium on 医生 (S11): his eyes sweep once down the corridor towards the near end and once back "
               "towards the far end, checking the length of it, and then he says quietly, "
               "[Chinese] 谁的手这么长，你自己心里有数。"),
     (2, "05.200", "Closer as he finishes: the checking look settles back onto her face, his hand still inside "
                  "the pocket, his shoulders slightly rounded; the corridor behind him stays bright and fully "
                  "open with no dark stretch.")],
    "The corridor's long echo, a rubber-soled footstep turning a far corner, his low voice.",
    "N/A"),

seg("t15", "4-1b", "安静了几秒", ["suxiaoman", "yisheng"], ["hospital_corridor"],
    "Reverse on 苏小满 (S1): she stays quiet for several seconds, nothing moving in her face but one swallow, "
    "standing still with her hands at her sides.",
    "苏小满 (S1) at the near end of the corridor facing the doctor, hands at her sides, having just heard his "
    "warning.",
    [(1, None, "Reverse medium on 苏小满 (S1): she goes quiet for several seconds, nothing rising in her face; "
               "the only movement is one swallow at her throat; she stands very straight with her hands at "
               "her sides, facing him down the corridor, evenly lit and open."),
     (2, "05.600", "Closer on her eyes: they stay level on him, the corridor fluorescents reflected as small "
                  "highlights, and her jaw does not tighten; the plain thin collar at her throat lies flat "
                  "against the work shirt inside it.")],
    "Corridor air, a distant monitor beep, four full seconds of her not speaking, the fluorescents.",
    "N/A"),

seg("t16", "4-1b", "没招谁没惹谁", ["suxiaoman", "yisheng"], ["hospital_corridor"],
    "苏小满 (S1) lifts her eyes to him and says, quietly and with every word landing, that her grandmother's "
    "illness has harmed nobody and asked nobody for anything.",
    "苏小满 (S1) in the NEAR half of the corridor facing down its length, 医生 (S11) still at the FAR end facing "
    "her, further from the camera; she has just answered him and he has not moved.",
    [(1, None, "Reverse on 苏小满 (S1) from the FAR end of the corridor, with 医生 (S11)'s white-coated shoulder "
               "small and out of focus at the edge of frame: she lifts her eyes to him and says, her voice not "
               "raised, every word landing, "
               "[Chinese] 医生，我外婆的病，没招谁没惹谁。"),
     (2, "05.400", "Closer on her as the line ends: her chin stays level, her eyes do not leave him, and her "
                  "hands remain down at her sides; the corridor's bright even light keeps her whole face open.")],
    "Her low steady slightly hoarse voice down the corridor, the fluorescent hum, a monitor beeping far off.",
    "N/A"),

seg("t17", "4-1b", "拇指停在一行上", ["yisheng", "suxiaoman"], ["hospital_corridor"],
    "Close on the doctor's hand: he is holding a scheduling clipboard with a printed roster on it, and his "
    "thumb comes to rest on one particular line and stays there.",
    "医生 (S11) at the far end of the corridor with a scheduling clipboard in his hand; 苏小满 (S1) at the near "
    "end facing him.",
    [(1, None, "Close on the doctor's hand holding a scheduling clipboard: a printed roster of names and dates "
               "runs down the page in neat rows, and his thumb comes to rest on one particular line and stays "
               "there, pressing the paper slightly; the top two thirds are his hand and the page, the bottom "
               "third the corridor's polished tile out of focus."),
     (2, "05.000", "Tighter still on the thumb and the paper: the skin at the side of the thumb goes pale under "
                  "the pressure, the page does not move, and the corridor light rakes across the clipboard's "
                  "edge.")],
    "The board's stiff paper flexing faintly, his thumb's skin against it, the corridor hum behind.",
    "N/A"),

seg("t18", "4-1b", "我尽力拖", ["yisheng", "suxiaoman"], ["hospital_corridor"],
    "The doctor sighs, lets his shoulder drop, takes his hand out of his pocket and for the first time looks "
    "straight at her as he tells her he will hold it as long as he can.",
    "医生 (S11) at the far end of the corridor with the clipboard; 苏小满 (S1) at the near end facing him.",
    [(1, None, "Medium close on 医生 (S11): he sighs, one shoulder dropping, and brings the hand out of his "
               "pocket; for the first time his eyes come round to face her straight as he says, "
               "[Chinese] 我尽力拖。你快点想办法。"),
     (2, "05.400", "Closer on his face as he finishes: the sigh leaves his cheeks, the clipboard hangs at his "
                  "side now, and the corridor's even light keeps the lines around his eyes soft and readable "
                  "rather than hollow.")],
    "His sighing breath, the clipboard's edge tapping his thigh, the corridor's long fluorescent hum.",
    "N/A"),

seg("t19", "4-1b", "他走远了", ["suxiaoman", "yisheng"], ["hospital_corridor"],
    "The doctor turns and walks away down the corridor towards its bright far end, his white coat growing "
    "smaller; 苏小满 (S1) stays where she is, facing after him.",
    "医生 (S11) at the far end of the corridor, 苏小满 (S1) at the near end facing him.",
    [(1, None, "Medium down the corridor: 医生 (S11) turns and walks away from her along the depth axis "
               "towards the bright far end, his white coat shrinking with the distance; 苏小满 (S1) stays "
               "exactly where she is in the near half of frame, facing after him, hands still at her sides."),
     (2, "05.600", "The camera holds on her from behind and slightly to the side: she does not follow him with "
                  "her feet, only with her eyes; the far end of the corridor stays bright and open around his "
                  "receding figure and the empty benches stay empty.")],
    "His white coat's footsteps receding down the corridor, a far lift chime, her standing breathing.",
    "N/A"),

seg("t20", "4-1b", "她站在原地", ["suxiaoman"], ["hospital_corridor"],
    "Close on 苏小满 (S1) alone in the near end of the corridor, watching the direction he went, shoulders "
    "still, saying nothing; the tile floor and her shoe tips along the bottom third.",
    "苏小满 (S1) alone at the near end of the corridor, facing the direction the doctor walked, hands at her "
    "sides.",
    [(1, None, "Medium close on 苏小满 (S1) alone: she watches the direction the doctor went, her shoulders not "
               "moving and her mouth shut; the corridor stretches away from her to the bright far end; the "
               "bottom third of frame is the polished tile and the tips of her black cloth shoes."),
     (2, "06.200", "Closer on her face, three-quarter: her eyes stay on the far end, her jaw is set but her "
                  "eyes are dry, and the corridor's even light holds every plane of her face with soft open "
                  "shadows under the eyes and chin.")],
    "The corridor fluorescents, her own breathing, his footsteps thinning out towards the far end.",
    "A single low string note, held and then released.",
    {"suxiaoman": "fully_preserved"}),
]



# ═══════════════════════════════════════════════════════════════════
# 场次 4-2　景宸大厦 物业办公室 · 上午（日戏）
# 钱经理恒在长桌远端，苏小满恒在长桌近端，同事恒在她侧后方更近一档。
# ═══════════════════════════════════════════════════════════════════
OF = "office_pano"

S42 = [
seg("t21", "4-2", "长条会议桌", [], [OF],
    "Opening wide from inside the office door: a long conference table runs away along the depth axis with its "
    "long side to the camera, a stack of claim forms and a telephone on it, filing cabinets along the far wall "
    "and a venetian blind letting bright mid-morning light in; nobody in the frame.",
    "the property office of 景宸大厦 on a bright mid-morning, seen from inside the door looking in; the long "
    "conference table runs away along the depth axis with its long side to the camera, a stack of claim forms "
    "and a telephone lying on it; filing cabinets along the far wall, a venetian blind at the side with the "
    "ceiling lights on; the office is empty of people.",
    [(1, None, "Wide from inside the door down the length of the room: the long conference table runs away "
               "along the depth axis with its long side to the camera, a neat stack of claim forms and a "
               "telephone sitting on it; filing cabinets line the far wall and a venetian blind lets bright "
               "mid-morning light in across the floor, the ceiling lights on, the whole room open and clean; "
               "the table top and the floor tiles fill the bottom third."),
     (2, "06.000", "The same office held a moment longer, the blind's light lying in clean bands across the "
                  "table and the floor, the stack of forms square to the lens, the room empty and evenly lit "
                  "from edge to edge.")],
    "The building's daytime air, the telephone sitting untouched on the table, paper settling, a lift somewhere "
    "far off.",
    "N/A"),

seg("t22", "4-2", "她推门进来", ["suxiaoman", "qianjingli"], [OF],
    "苏小满 (S1) comes through the door and stops at the near end of the long table with her back to the door, "
    "facing the far end where 钱经理 (S3) is waiting; a work badge is clipped to her chest.",
    "苏小满 (S1) has just come through the door at the NEAR end of the office; 钱经理 (S3) stands at the FAR "
    "end of the long table with his hands empty, facing the near end.",
    [(1, None, "Medium from the door: 苏小满 (S1) steps in and stops at the NEAR end of the long table, her back "
               "to the door and her face to the far end; navy work shirt, grey-blue apron, low ponytail, and a "
               "work badge clipped to her chest; her hands hang at her sides."),
     (2, "04.800", "Reverse towards the far end: 钱经理 (S3) in a white shirt and dark grey waistcoat stands "
                  "behind the long table backed by the filing cabinets, facing her, both hands still empty, "
                  "waiting; the morning light from the blind falls across the table between them.")],
    "The door swinging shut behind her, her flat shoes on the tile, the office's daytime quiet.",
    "N/A"),

seg("t23", "4-2", "他迎上两步", ["qianjingli", "suxiaoman"], [OF],
    "钱经理 (S3) comes round the far end of the table towards her and tears the work badge off her chest in "
    "one movement; her shoulder twists aside and she has no time to stop him.",
    "苏小满 (S1) at the near end of the long table with the badge on her chest; 钱经理 (S3) moving towards her "
    "from the far end, both hands rising.",
    [(1, None, "Medium along the table's depth axis: 钱经理 (S3) comes round the far end of the table towards "
               "the near end and in one movement tears the work badge off 苏小满 (S1)'s chest; her shoulder is "
               "twisted aside by the pull and her hand starts up too late to stop it."),
     (2, "05.200", "Tighter on the two of them: the badge is clear of her chest and in his hand, her uniform "
                  "front slightly rumpled where it was clipped, and both of them are lit evenly from the "
                  "ceiling lights with the blind's bands on the table behind.")],
    "The badge's clip snapping off the cloth, his quick footsteps on the tile, her coat and apron shifting.",
    "N/A"),

seg("t24", "4-2", "啪地拍在桌上", ["qianjingli", "suxiaoman"], [OF],
    "Close on the table: he swings back and slaps the badge face-up onto the table top, where it rocks once "
    "and settles; her hands stay empty at her sides.",
    "the badge in 钱经理 (S3)'s hand above the long table; 苏小满 (S1) at the near end with her hands empty at "
    "her sides.",
    [(1, None, "Close on the long table: the work badge comes down flat onto the table top face-up and rocks "
               "once before settling, its clip bouncing; the top two thirds are his hand withdrawing and the "
               "badge, the bottom third the table's wooden edge and the floor beyond."),
     (2, "04.600", "Low angle along the table top: the badge lies still face-up under the ceiling light, the "
                  "stack of claim forms a short distance behind it, and at the near edge of frame the girl's "
                  "hands hang open and do not reach for it.")],
    "The badge slapping the table and its clip ringing, his palm coming down on the wood, the room's daytime "
    "quiet.",
    "N/A"),

seg("t25", "4-2", "你不用来了", ["qianjingli", "suxiaoman"], [OF],
    "钱经理 (S3) keeps one hand beside the badge he has just slapped down, lifts his chin towards her and "
    "says, loudly, that from today she is not to come in again.",
    "钱经理 (S3) still at the NEAR side of the long table where he came round to her, one hand flat on the wood "
    "beside the work badge he has just slapped down; 苏小满 (S1) at the NEAR end facing him, hands at her sides, "
    "the badge face-up on the wood between them.",
    [(1, None, "Medium on 钱经理 (S3) at the near side: one hand stays flat on the table beside the badge he has "
               "just slapped down, his chin lifts towards the near end and he calls out, loud and open, "
               "[Chinese] 苏小满。从今天起，你不用来了。"),
     (2, "05.400", "Closer on him as the line lands: his mouth stays open a fraction afterwards, his eyes fixed "
                  "down the table at her, and the morning light from the blind lies in bands across his white "
                  "shirt and the badge lying beside his hand.")],
    "His voice carrying across the room, the badge's clip still ringing faintly, the blind's light on the wall.",
    "N/A"),

seg("t26", "4-2", "为什么", ["suxiaoman", "qianjingli"], [OF],
    "Reverse on 苏小满 (S1): she looks down at the badge on the table, then lifts her eyes back to him and "
    "gives him three words, quiet and completely level.",
    "苏小满 (S1) at the near end of the long table facing him, her hands at her sides; the badge lies on the "
    "table between them.",
    [(1, None, "Reverse medium on 苏小满 (S1) from the far end of the table: she looks down at the badge lying "
               "on the table top, then lifts her eyes back up to him and says, not raising her voice at all, "
               "[Chinese] 为什么。"),
     (2, "03.600", "Closer on her face: the look she gives him is level and unhurried, her jaw set, her hands "
                  "still down; the ceiling light keeps her whole face open, with soft even shading under the eyes "
                  "and the chin.")],
    "Her low steady slightly hoarse voice, the room's quiet, a paper edge rustling on the table.",
    "N/A"),

seg("t27", "4-2", "大厦不敢留", ["qianjingli", "suxiaoman"], [OF],
    "钱经理 (S3) gives a cold laugh and spreads one hand flat on the table as he tells her someone upstairs has "
    "passed word down and the building dares not keep her on.",
    "钱经理 (S3) at the far end of the long table; 苏小满 (S1) at the near end facing him; the badge between "
    "them on the table.",
    [(1, None, "Medium on 钱经理 (S3): he gives a cold laugh and spreads one hand flat on the table top as he "
               "says, [Chinese] 上面递了话。你这号人，大厦不敢留。"),
     (2, "06.000", "Closer on him as he finishes: the spread hand stays on the wood, his eyes narrow down the "
                  "table, and the morning bands from the blind lie across his forearm; the room stays bright "
                  "and evenly lit around him.")],
    "His short cold laugh, his palm sliding on the table, the building's daytime air.",
    "N/A"),

seg("t28", "4-2", "你想擦哪层擦哪层", ["suxiaoman", "qianjingli"], [OF],
    "苏小满 (S1)'s jaw sets for a moment but she does not get angry, and she takes it back steadily, remind"
    "ing him that only days ago he told her she could clean whichever floor she liked.",
    "苏小满 (S1) at the near end of the long table facing 钱经理 (S3) at the far end.",
    [(1, None, "Reverse medium on 苏小满 (S1): her jaw sets for a moment but she does not raise her voice or "
               "lose her footing, and she says steadily, [Chinese] 前几天，你还说我想擦哪层擦哪层。"),
     (2, "05.400", "Closer as the line ends: she holds his eye across the whole length of the table, her "
                  "shoulders square, the apron's waist tie still; across the table he has gone a fraction "
                  "still, the badge untouched beside his hand.")],
    "Her steady low voice, the room's quiet, the blind's light shifting a little as clouds pass outside.",
    "N/A"),

seg("t29", "4-2", "前几天是前几天", ["qianjingli", "suxiaoman"], [OF],
    "钱经理 (S3) comes round the near side of the long table, leans half a pace in towards her and drops his "
    "voice as he says that before is before, and that he has heard things.",
    "钱经理 (S3) moving from the far end of the long table round to its near side, leaning towards 苏小满 (S1); "
    "she stays at the near end facing him.",
    [(1, None, "Medium along the table's depth axis: 钱经理 (S3) comes round from the far end of the long table "
               "to its near side, leans half a pace in towards 苏小满 (S1) and drops his voice as he says, "
               "[Chinese] 前几天是前几天。我可听说了。"),
     (2, "05.600", "Tighter on the two of them, him nearer the lens and her just behind: he keeps his weight "
                  "forward, she does not step back, and the ceiling light and the blind's bands keep both their "
                  "faces open and readable at this short range.")],
    "His lowered voice close to her, his shoes scraping a half step on the tile, the room's quiet.",
    "N/A"),

seg("t30", "4-2", "雇来演戏的", ["qianjingli", "suxiaoman"], [OF],
    "钱经理 (S3) squeezes his eyes to two slits and goes on, low in the throat, that she is somebody's hired "
    "actress, hired to play a part.",
    "钱经理 (S3) leaning in at the near side of the long table; 苏小满 (S1) just behind him in the near half "
    "of frame.",
    [(1, None, "Close on 钱经理 (S3) leaning in: his eyes squeeze down to two slits and he goes on in a low "
               "pressed voice, [Chinese] 你就是人家花钱雇的。雇来演戏的。"),
     (2, "05.600", "Over his shoulder towards 苏小满 (S1): she has not stepped back and has not moved her head; "
                  "her face is fully lit and completely level, and she is looking straight at him while he "
                  "occupies the near foreground.")],
    "His pressed low voice, the room's air, a distant lift stopping somewhere in the building.",
    "N/A"),

seg("t31", "4-2", "眼神沉了一下", ["suxiaoman"], [OF],
    "Close on 苏小满 (S1)'s eyes: her gaze sinks a little, her lashes do not tremble and her mouth does not "
    "move, only her pupils draw up very slightly.",
    "苏小满 (S1) at the near end of the long table, facing 钱经理 (S3) who is just off the near foreground.",
    [(1, None, "Close on 苏小满 (S1)'s eyes: her gaze sinks a little, her lashes do not tremble, the corners of "
               "her mouth do not move, and only her pupils draw up very slightly; the ceiling light puts a soft "
               "even wash across her brow and cheekbone, the shading under them soft and open."),
     (2, "05.000", "The same close held a beat longer, her eyes steady in the middle distance; around her the "
                  "office stays bright and even, the blind's light bands soft on the wall behind her.")],
    "Her steady breathing, the room's quiet, a faint paper rustle off to the side.",
    "A single low string note, sustained under the hold.",
    {"suxiaoman": "fully_preserved"}),

seg("t32", "4-2", "真凤凰", ["qianjingli", "suxiaoman"], [OF],
    "钱经理 (S3) clicks his tongue, shakes his head and fans a hand in front of his nose as he sneers about a "
    "real phoenix landing in their building's pool.",
    "钱经理 (S3) at the near side of the long table; 苏小满 (S1) behind him in the near half of frame.",
    [(1, None, "Medium on 钱经理 (S3): he clicks his tongue, shakes his head and fans one hand in front of his "
               "nose as he says, [Chinese] 我说呢。真凤凰，能落我们大厦的池子？"),
     (2, "05.800", "Closer as the sneer finishes: his fanning hand drops to the table edge, his head tilted, "
                  "and the light from the blind and the ceiling fixtures keeps the whole front of his face "
                  "readable and soft rather than harsh.")],
    "His tongue clicking, the fan of his hand, the office's daytime air.",
    "N/A"),

seg("t33", "4-2", "身后的几声低笑", ["suxiaoman", "xiaotang", "qianjingli"], [OF],
    "The camera turns past 苏小满 (S1)'s shoulder to the colleagues crowded a step behind her and nearer the "
    "door; several low laughs come from the nearest of them.",
    "苏小满 (S1) at the near end of the long table with her back to the door; behind her and nearer the lens a "
    "few colleagues stand staggered in depth; 钱经理 (S3) at the near side of the table.",
    [(1, None, "Medium turning past 苏小满 (S1)'s shoulder towards the door end: a few of her colleagues stand "
               "staggered in depth behind her and nearer the lens, several of them laughing low; 小唐 (S4) is "
               "among them, in a cleaning uniform, shoulders hunched, one hand over her mouth."),
     (2, "05.200", "The camera settles on the group: the laughter is coming from the nearest of them, faces "
                  "split between light and turn, and in the near foreground 苏小满 (S1)'s shoulder and the "
                  "back of her head stay steady and still.")],
    "Several low laughs close to the lens, a shoulder shaking, the office's quiet underneath them.",
    "N/A"),

seg("t34", "4-2", "小唐笑得最响", ["xiaotang", "suxiaoman"], [OF],
    "Close on 小唐 (S4) laughing hardest with her hand over her mouth, her shoulders shaking, her eyes sliding "
    "off towards the others.",
    "小唐 (S4) standing behind 苏小满 (S1) and nearer the door, in a cleaning uniform, shoulders hunched, one "
    "hand over her mouth.",
    [(1, None, "Close on 小唐 (S4): a small woman in a cleaning uniform with her shoulders hunched, laughing "
               "hardest of anyone with one hand clamped over her mouth, her shoulders shaking, her eyes "
               "sliding sideways towards the others in the group; the ceiling light is even on her whole face."),
     (2, "05.000", "The same close held as her laugh peaks and starts to break: her eyes flick once towards "
                  "苏小满 (S1) just off frame and back to the others, and her hand stays over her mouth.")],
    "Her muffled laughing, the group behind her catching it, the office's air.",
    "N/A"),

seg("t35", "4-2", "目光扫过那叠单", ["suxiaoman", "qianjingli"], [OF],
    "The camera comes back to 苏小满 (S1): her gaze does not go to the badge on the table but sweeps across the "
    "stack of claim forms lying on it.",
    "苏小满 (S1) at the near end of the long table; the badge and the stack of claim forms on the table between "
    "her and 钱经理 (S3).",
    [(1, None, "Medium on 苏小满 (S1) at the near end of the table: her gaze does not settle on the badge lying "
               "face-up on the table but sweeps across the stack of claim forms beside it, and she does not "
               "reach for either."),
     (2, "05.000", "Closer on her eyes tracking along the stack: her head turns very slightly with the "
                  "movement, her hands stay down at her sides, and the ceiling light keeps her face open as her "
                  "eyes come to rest.")],
    "Her low breathing, a page lifting slightly in the air from the blind, the room's quiet.",
    "N/A"),

seg("t36", "4-2", "三万六", ["suxiaoman"], [OF],
    "The camera presses down onto the stack of claim forms: the top sheet's printed columns are clear, its top "
    "line naming a third-floor carpet replacement at thirty-six thousand.",
    "the stack of claim forms on the long table, with 苏小满 (S1)'s hand just out of frame at the near edge.",
    [(1, None, "High angle pressing down onto the stack of claim forms: the top sheet's printed columns run "
               "across the page in neat rows and its top line names a third-floor carpet replacement at "
               "thirty-six thousand; the top two thirds of frame are the paper and the table's wooden edge, the "
               "bottom third the table surface out of focus."),
     (2, "05.400", "Tighter on the same sheet, the paper's fibre and the printed ruling sharp, the ceiling "
                  "light laying a clean even wash across it with no shadow gathering in the folds.")],
    "Paper settling on the table, her fingers lightly grazing the sheet's edge, the room's quiet.",
    "N/A"),

seg("t37", "4-2", "上个月换三楼地毯", ["suxiaoman", "qianjingli"], [OF],
    "苏小满 (S1) straightens up, takes the thread and tells 钱经理 (S3) that the third-floor carpet was "
    "replaced last month, her eyes coming up from the form to his face.",
    "苏小满 (S1) at the near end of the long table; the stack of claim forms in front of her; 钱经理 (S3) at "
    "the far end.",
    [(1, None, "Medium on 苏小满 (S1): she straightens up from the table and takes the thread, her eyes coming "
               "up from the claim form to 钱经理 (S3)'s face across the length of the table as she says, "
               "[Chinese] 钱经理，上个月换三楼地毯。"),
     (2, "04.800", "Closer on her as she holds his eye across the table: her voice is level and slower than "
                  "before, her hands rest on the table edge now, and the office stays bright around the two of "
                  "them.")],
    "Her steady low voice, the room's quiet, a distant lift chime.",
    "N/A"),

seg("t38", "4-2", "只有两卷样品", ["suxiaoman", "qianjingli"], [OF],
    "Over 钱经理 (S3)'s shoulder: 苏小满 (S1) sets one hand lightly on the table edge, not touching the badge, "
    "and lays the count out one clause at a time.",
    "钱经理 (S3) in the near foreground; 苏小满 (S1) behind him at the near end of the long table with one hand "
    "on the table edge.",
    [(1, None, "Over-shoulder with 钱经理 (S3) in the near foreground and 苏小满 (S1) behind him: she sets one "
               "hand lightly on the table's edge, well away from the badge, looks straight at him and says, "
               "[Chinese] 运上楼的，只有两卷样品。那天我值夜班，数过。"),
     (2, "06.400", "Closer on her over his shoulder as the line finishes: her hand stays flat on the wood, her "
                  "eyes never leave him, and the ceiling light holds her face even and open while his shoulder "
                  "occupies the near edge of frame.")],
    "Her hand sliding onto the table edge, her low voice, the office's daytime quiet.",
    "N/A"),

seg("t39", "4-2", "你胡说什么", ["qianjingli", "suxiaoman"], [OF],
    "钱经理 (S3)'s face changes, the hand he had on the table edge pulls back, he glances at the people behind "
    "her and only then pushes the words back at her.",
    "钱经理 (S3) at the near side of the long table, 苏小满 (S1) at the near end facing him; the colleagues "
    "behind her and nearer the door.",
    [(1, None, "Medium on 钱经理 (S3): his face changes, the hand that was on the table edge pulls back, he "
               "glances once over 苏小满 (S1)'s shoulder at the colleagues behind her, and only then pushes the "
               "words back, [Chinese] 你胡说什么。"),
     (2, "05.000", "Closer on him: the pulled-back hand grips the table edge again, his eyes come forward to "
                  "her face, and the light from the blind and the ceiling fixtures keeps his whole front "
                  "readable with soft open shadows.")],
    "His chair scraping a half step, his voice pitched higher, the room's quiet behind him.",
    "N/A"),

seg("t40", "4-2", "差着六位", ["suxiaoman", "qianjingli"], [OF],
    "苏小满 (S1) does not take the bait; she points one finger beside the serial-number column on the form and "
    "slows her delivery as she tells him the sample numbers and the batch numbers differ by six digits.",
    "苏小满 (S1) at the near end of the long table with one finger beside the form's serial column; 钱经理 (S3) "
    "in the near foreground.",
    [(1, None, "Over-shoulder with 钱经理 (S3) in the near foreground: 苏小满 (S1) does not take the bait; she "
               "sets one fingertip down beside the serial-number column on the claim form and slows her "
               "delivery as she says, [Chinese] 样品编号，和报销单上的批次，差着六位。"),
     (2, "06.000", "Closer on her hand and the page: her fingertip stays planted beside the printed column, the "
                  "paper's ruling running away under her finger, and her face above it stays level and "
                  "unhurried.")],
    "Her fingertip on the paper, her low steady voice, the room's quiet.",
    "N/A"),

seg("t41", "4-2", "单子在废纸桶里", ["suxiaoman", "qianjingli"], [OF],
    "苏小满 (S1) adds the last of it, her voice low and every word landing, still looking at the form: the "
    "rest of the goods came in through a back door, and the paperwork was in the waste paper bin, three times.",
    "苏小满 (S1) at the near end of the long table, fingertip still by the form's serial column; 钱经理 (S3) "
    "in the near foreground with his back partly to the lens.",
    [(1, None, "Over-shoulder with 钱经理 (S3) in the near foreground and 苏小满 (S1) behind him: she adds the "
               "last of it, her voice low and every word landing, her eyes still on the claim form rather than "
               "on him, [Chinese] 剩下的货从哪个后门进的，单子在废纸桶里，我收过三回。"),
     (2, "07.000", "Closer on her as the line ends: her fingertip is still beside the printed column, her "
                  "shoulders square, and the ceiling light keeps her face and the paper evenly lit together.")],
    "Her low voice, a page edge lifting slightly, the room's quiet settling after the line.",
    "N/A"),

seg("t42", "4-2", "他额头冒汗", ["qianjingli"], [OF],
    "Close on 钱经理 (S3): a thin sweat breaks across his forehead; he lifts a hand to wipe it, then seems to "
    "think better of it and lets the hand fall.",
    "钱经理 (S3) at the near side of the long table, facing 苏小满 (S1) who is off the near frame.",
    [(1, None, "Close on 钱经理 (S3): a thin sheen of sweat breaks across his forehead and temple; he lifts "
               "one hand to wipe it, then seems to think better of it and lets the hand fall away again; the "
               "ceiling light picks the sheen out on his skin without darkening the rest of his face."),
     (2, "05.400", "The same close held: the sweat stays on his forehead, his dropped hand grips the table edge "
                  "just out of frame, and his eyes come up towards the near end where she is standing.")],
    "His breathing slightly faster, his hand leaving the table edge, the office's air.",
    "N/A"),

seg("t43", "4-2", "你想干什么", ["qianjingli", "suxiaoman"], [OF],
    "钱经理 (S3) brings his voice down to where only she can hear it, leans in towards her and asks, with his "
    "eyes on her, what she thinks she is doing.",
    "钱经理 (S3) at the near side of the long table leaning towards 苏小满 (S1) at the near end.",
    [(1, None, "Medium close on 钱经理 (S3) leaning in: he brings his voice right down to where only she can "
               "hear it and asks, his eyes locked on her, [Chinese] 你想干什么？"),
     (2, "03.800", "Closer on his face as the question hangs: his mouth stays slightly open, the sweat still "
                  "on his forehead, and the two of them are lit evenly from the front with the office bright "
                  "around them.")],
    "His dropped voice, his breath close to her, the room's quiet.",
    "N/A"),

seg("t44", "4-2", "我就问一句", ["suxiaoman", "qianjingli"], [OF],
    "苏小满 (S1) does not step back; she answers in a completely level tone, as if discussing the most ordinary "
    "thing in the world.",
    "苏小满 (S1) at the near end of the long table facing 钱经理 (S3) at the near side.",
    [(1, None, "Over-shoulder with 钱经理 (S3) in the near foreground: 苏小满 (S1) does not step back and "
               "answers in a completely level tone, as if discussing the most ordinary thing in the world, "
               "[Chinese] 我不想干什么。我就问一句。"),
     (2, "04.600", "Closer on her over his shoulder: her face is calm and her eyes stay on him, her hands down "
                  "at her sides, and the ceiling light holds her evenly with no shadow gathering under her "
                  "cheekbones.")],
    "Her level low voice, the room's quiet, his breath held.",
    "N/A"),

seg("t45", "4-2", "谁让你去打的招呼", ["suxiaoman", "qianjingli"], [OF],
    "苏小满 (S1) says the next one very slowly, each word a step forward, her gaze dropping straight onto "
    "钱经理 (S3)'s face as she asks who it was that told him to pull strings about her grandmother's bed.",
    "苏小满 (S1) at the near end of the long table; 钱经理 (S3) in the near foreground.",
    [(1, None, "Over-shoulder with 钱经理 (S3) in the near foreground: 苏小满 (S1) puts the next one out very "
               "slowly, each word a step forward, her gaze dropping straight onto his face as she says, "
               "[Chinese] 我外婆那张床位，是谁让你去打的招呼。"),
     (2, "06.000", "Closer on her as the question closes: her chin is level, her eyes do not move off him, and "
                  "the office behind her stays bright and even, the blind's light soft on the far wall.")],
    "Her slow low voice, the room's air holding after it, his uneven breath.",
    "A low string entry, settling low and holding.",
    {"suxiaoman": "fully_preserved"}),

seg("t46", "4-2", "那不是我的主意", ["qianjingli", "suxiaoman"], [OF],
    "钱经理 (S3) goes rigid; his mouth moves once before the words arrive, and the fingers he has on the table "
    "edge curl in.",
    "钱经理 (S3) at the near side of the long table, 苏小满 (S1) at the near end facing him.",
    [(1, None, "Medium close on 钱经理 (S3): he goes rigid, his mouth moves once and does not immediately "
               "produce anything, the fingers he has on the table edge curl in, and then he says, "
               "[Chinese] ……那不是我的主意。"),
     (2, "04.000", "Closer on his face: the sweat is still there, his eyes come up to hers and then slide off, "
                  "and the front of his face stays evenly lit so that the hesitation is fully visible.")],
    "His stalled voice, the room's quiet, a faint paper rustle.",
    "N/A"),

seg("t47", "4-2", "我知道不是你的主意", ["suxiaoman", "qianjingli"], [OF],
    "苏小满 (S1) nods once, with no weight of accusation in it at all.",
    "苏小满 (S1) at the near end of the long table facing 钱经理 (S3) in the near foreground.",
    [(1, None, "Over-shoulder with 钱经理 (S3) in the near foreground: 苏小满 (S1) gives one small nod, with no "
               "weight of accusation in it at all, and says, [Chinese] 我知道不是你的主意。"),
     (2, "03.400", "Closer on her as she lifts her chin again: the nod leaves her face calm, her hands stay "
                  "down, and the ceiling light keeps her features soft and open.")],
    "Her level low voice, the room's quiet, his breath.",
    "N/A"),

seg("t48", "4-2", "你替我带句话", ["suxiaoman", "qianjingli"], [OF],
    "苏小满 (S1) draws the words in a notch and her voice drops lower but stays solid, telling him to pass on "
    "a message about what will happen if her grandmother loses that bed.",
    "苏小满 (S1) at the near end of the long table; 钱经理 (S3) in the near foreground with his back partly to "
    "the lens.",
    [(1, None, "Over-shoulder with 钱经理 (S3) in the near foreground: 苏小满 (S1) draws the words in a notch and "
               "her voice drops lower but stays solid as she says, "
               "[Chinese] 你替我带句话。我外婆要因为谁没了床位，出个三长两短。"),
     (2, "07.200", "Closer on her as the line closes: her eyes stay on him, her jaw set, the whole office "
                  "behind her bright and readable, and nothing in her face rises above the line of what she is "
                  "saying.")],
    "Her low steady voice, the room's air, a distant lift starting.",
    "N/A"),

seg("t49", "4-2", "一页一页翻出来", ["suxiaoman", "qianjingli"], [OF],
    "苏小满 (S1) delivers the last of it very steadily, her chin pushing forward a fraction — the first time "
    "in the scene she names what she intends to do.",
    "苏小满 (S1) at the near end of the long table facing 钱经理 (S3) in the near foreground.",
    [(1, None, "Over-shoulder with 钱经理 (S3) in the near foreground: 苏小满 (S1) delivers the last of it very "
               "steadily, her chin pushing forward a fraction, the first time she has named what she means to "
               "do, [Chinese] 我这辈子啥都不干，就干一件事。把你们这笔账，一页一页，翻出来。"),
     (2, "07.600", "Closer on her as the line ends: her chin stays forward, her eyes do not move, and the "
                  "office stays bright and even around her with the blind's bands soft on the wall.")],
    "Her low unhurried voice, the room's quiet holding it, a page settling on the table.",
    "A low string entry, sustained and unresolved.",
    {"suxiaoman": "fully_preserved"}),

seg("t50", "4-2", "工牌回兜里", ["suxiaoman", "qianjingli"], [OF],
    "Close on her hand and the table: she moves her hand off the edge onto the badge, picks it up, puts it "
    "into her own pocket and presses the pocket flat, all while telling him her pay runs to the end of the "
    "month and she has an attendance record every day.",
    "苏小满 (S1)'s hand moving from the table edge onto the badge; 钱经理 (S3) out of frame at the far side of "
    "the table.",
    [(1, None, "Close on 苏小满 (S1)'s hand and the table top: her hand comes off the edge onto the badge "
               "lying face-up, "
               "picks it up and goes down into her own apron pocket, then presses the pocket flat; the top two "
               "thirds are her hand, the badge and the table's wooden edge, the bottom third the table and floor "
               "beyond; she says as she does it, [Chinese] 工资结到月底。我每天有出勤记录。"),
     (2, "05.600", "The same close after the pocket is pressed flat: the badge is gone from the table, a clean "
                  "ring of unshadowed wood is left where it lay, and her hand comes away and drops to her side "
                  "at the near edge of frame.")],
    "The badge's clip brushing the apron, her low voice, the room's quiet.",
    "N/A"),

seg("t51", "4-2", "她转身出门", ["suxiaoman", "qianjingli"], [OF],
    "Medium: 苏小满 (S1) finishes, turns away from 钱经理 (S3) with her back to him and walks towards the door "
    "at the near end, not once looking back at the stack of claim forms.",
    "苏小满 (S1) at the near end of the long table, having just put the badge in her pocket; 钱经理 (S3) at the "
    "near side of the table.",
    [(1, None, "Medium from the table's far side: 苏小满 (S1) finishes what she is saying, turns away from "
               "钱经理 (S3) so that her back is to him and walks towards the door at the near end; she does not "
               "look back at the stack of claim forms even once."),
     (2, "05.200", "Closer from behind as she reaches the door: her hand goes to the handle, her shoulders stay "
                  "square and unhurried, and the office behind her stays bright, with the badge's clean ring "
                  "still visible on the table.")],
    "Her flat shoes walking away, the room's quiet, his breath behind her.",
    "N/A"),

seg("t52", "4-2", "门在身后关上", ["qianjingli"], [OF],
    "Close on the door: she goes out through it and it closes behind her, cutting off the last strip of "
    "corridor daylight; the room is left with 钱经理 (S3) alone beside the table.",
    "the door at the NEAR end of the office, closing behind 苏小满 (S1); 钱经理 (S3) in the room.",
    [(1, None, "Close on the door at the near end of the office: it swings closed behind 苏小满 (S1) and the "
               "handle settles; the last strip of corridor daylight narrows to a line and is gone, leaving the "
               "office lit only by its own ceiling lights and the blind; the bottom third is the door's lower "
               "panel and the floor in front of it."),
     (2, "05.000", "The closed door held for a beat: the handle stills, the room beyond it stays bright and "
                  "even, and the door's flat panel takes a soft vertical band of light down its middle.")],
    "The door's latch clicking home, her footsteps receding on the other side, the room's quiet.",
    "N/A"),

seg("t53", "4-2", "他盯着门", ["qianjingli"], [OF],
    "Close on 钱经理 (S3): he stares at the closed door for two seconds, his throat works once, and the smile "
    "will not stay on his face.",
    "钱经理 (S3) alone in the office beside the long table, facing the closed door at the near end.",
    [(1, None, "Close on 钱经理 (S3) alone: he stares at the closed door at the near end of the room for two "
               "seconds, his throat works once, and the smile he had will not stay where it was; the ceiling "
               "light is even on the whole front of his face so the change is fully readable."),
     (2, "05.400", "The same close held: his eyes stay on the door, the sweat on his forehead has not dried, "
                  "and behind him the bright office and the badge's clean ring on the table stay in soft "
                  "focus.")],
    "The room's quiet, his uneven breath, a pipe ticking somewhere in the wall.",
    "N/A"),

seg("t54", "4-2", "喂，是我", ["qianjingli"], [OF],
    "钱经理 (S3) snatches the telephone off the long table, turns his back on the door and speaks into it in a "
    "low voice, his eyes flicking towards the door as he talks.",
    "钱经理 (S3) alone in the office at the near side of the long table, reaching for the telephone; the door "
    "closed at the near end behind him.",
    [(1, None, "Medium close on 钱经理 (S3): he snatches the telephone off the long table, turns his back on the "
               "closed door and speaks into the receiver in a low voice, his eyes flicking towards the door as "
               "he talks, [Chinese] 喂，是我。那个苏小满，今天来闹了一场。地毯那笔账，她知道。"),
     (2, "07.000", "Closer on him as he finishes the line: the receiver is held hard to his ear, his eyes have "
                  "gone back to the table, and the office stays bright and even around him with the blind's "
                  "light lying across the wood.")],
    "The receiver picked up, his lowered voice down the line, the room's quiet.",
    "N/A"),

seg("t55", "4-2", "牌位空了一圈", ["qianjingli"], [OF],
    "Close on the table top: the stack of claim forms is still where it was, and where the badge lay there is "
    "now only a clean ring of unshadowed wood.",
    "the long table top with the stack of claim forms on it and the badge gone; 钱经理 (S3) off frame holding "
    "the telephone.",
    [(1, None, "Close on the long table top: the stack of claim forms lies where it has lain all along, the top "
               "sheet's printed columns undisturbed, and where the badge sat there is now only a clean ring of "
               "unshadowed wood; the top two thirds are paper and wood, the bottom third the table edge and "
               "floor out of focus."),
     (2, "05.400", "The same close held a moment longer: the blind's light shifts one band across the papers, "
                  "the empty ring stays clean, and nothing else on the table has been touched.")],
    "Paper settling, his lowered voice off frame down the telephone, the room's air.",
    "N/A"),

seg("t56", "4-2", "目光落回那叠单", ["qianjingli"], [OF],
    "Medium: 钱经理 (S3) stands with the receiver to his ear and his eyes drop back to the stack of claim forms "
    "on the table; the blind lays the mid-morning light across the desk in bands.",
    "钱经理 (S3) at the near side of the long table holding the receiver to his ear, the stack of claim forms "
    "in front of him.",
    [(1, None, "Medium on 钱经理 (S3): he stands with the receiver to his ear and his eyes drop back down to "
               "the stack of claim forms on the table in front of him; the venetian blind lays the mid-morning "
               "light across the desk in clean bands and the ceiling lights keep his face and waistcoat fully "
               "readable."),
     (2, "06.000", "Closer on his lowered eyes and the papers: the sweat has dried on his forehead, his jaw is "
                  "set, and the room behind him stays open and bright with the closed door at the near end.")],
    "His voice off frame down the line, the blind's light on the paper, the room's quiet.",
    "A low string note, unsettled and holding.",
    {"qianjingli": "fully_preserved"}),
]


# ═══════════════════════════════════════════════════════════════════
# 场次 4-3　陆家老宅 后院杂物间 · 当天夜里（夜戏 · 顶灯亮着的夜）
# 苏小满恒在货架前中景偏左且手持手电，小罗恒在她身后更近一档。
# ═══════════════════════════════════════════════════════════════════
S43 = [
seg("t57", "4-3", "两排铁货架", [], ["lu_storage"],
    "Opening wide from the doorway of the old mansion's rear storage room: two rows of iron shelving reach the "
    "ceiling either side of one deep centre aisle, a fluorescent tube on the ceiling is on and lights the "
    "shelves and the concrete floor, and the open doorway shows the lit courtyard outside; nobody in frame.",
    "the storage room in the rear courtyard of the 陆 family old house, at night; the ceiling fluorescent tube "
    "is switched on and lights the two rows of iron shelving and the bare concrete floor clearly; the open "
    "doorway at the near end shows the lit courtyard; the room is empty of people.",
    [(1, None, "Wide from the doorway looking in: two rows of rusted iron shelving reach up to the ceiling on "
               "either side of one deep centre aisle, loaded with old trunks, rolled carpets, dusty porcelain "
               "and old tools; a single fluorescent tube on the ceiling is switched on and lights the shelves "
               "and the bare concrete floor evenly; through the open doorway at the near end the courtyard "
               "lamps are on too, so the whole room reads as a lit night and every shelf, the floor and the "
               "walls are fully readable."),
     (2, "06.000", "The same room held a moment longer down the centre aisle: the tube light lies even along "
                  "the shelf boards, the concrete floor is swept clean with dust only in the far corners, and "
                  "the doorway's spill of courtyard light stays gentle in the near third.")],
    "The steady hum of the fluorescent tube, the night air coming in through the open doorway, a bicycle "
    "chain faintly outside in the courtyard.",
    "N/A"),

seg("t58", "4-3", "手电扫过货架", [], ["lu_storage"],
    "A torch beam sweeps the upper shelving: brass padlocks on the old trunks and a layer of dust on the rolled "
    "carpets come up clear in the light; the ceiling tube keeps the rest of the room readable behind them.",
    "the storage room with the ceiling tube on; a hand-held torch beam is now sweeping the upper shelving from "
    "the near end of the aisle; nobody's face is in frame.",
    [(1, None, "Medium up the aisle as a hand-held torch beam sweeps the upper shelving: brass padlocks on the "
               "old trunks and a thick layer of dust on the rolled carpets come up clear and bright in the "
               "moving light; the ceiling tube keeps the whole room readable behind the beam, so the image "
               "stays open and clear rather than one small lamp with everything else falling away around it."),
     (2, "05.000", "The beam continues along the shelf: dust lifts a little in the light and settles, the "
                  "trunks' surfaces are evenly lit from two directions at once, and the aisle floor below "
                  "stays plainly visible.")],
    "The fluorescent tube humming, the soft scrape of a torch beam crossing metal shelving, night air through "
    "the doorway.",
    "N/A"),

seg("t59", "4-3", "光斑停在瓷碗上", [], ["lu_storage"],
    "The torch beam stops on a dusty porcelain bowl: a fine crack runs along its rim and thin dust has settled "
    "inside it, all of it clearly legible under the ceiling tube.",
    "the torch beam resting on the middle shelf of the storage room, the ceiling tube on.",
    [(1, None, "Close on a dusty porcelain bowl on the shelf as the torch beam comes to rest on it: a fine "
               "crack runs along the rim and a thin layer of dust has settled inside; the tube light behind it "
               "gives a clean second source so the bowl's whole shape, the crack and the dust are all clearly "
               "readable, with the shelf and the aisle behind softly open."),
     (2, "05.400", "The same close held: the beam steadies on the bowl, the dust inside it undisturbed, and the "
                  "surrounding shelf stays evenly lit by the ceiling tube from above.")],
    "The tube's hum, the torch beam's faint hiss, dust settling on the shelf.",
    "N/A"),

seg("t60", "4-3", "她照着他打哈欠", ["suxiaoman", "xiaoluo"], ["lu_storage"],
    "苏小满 (S1) stands in front of the shelving with the torch in her hand, and behind her nearer the door "
    "小罗 (S7) is caught in a yawn, one hand over his mouth and his keys hanging from the other.",
    "苏小满 (S1) in front of the shelving in the middle-ground, a little left of centre, facing the shelves and "
    "turned three-quarter away from the lens, the torch in her hand; 小罗 (S7) behind her nearer the doorway, "
    "in a dark navy overcoat over a black turtleneck.",
    [(1, None, "Medium in the aisle: 苏小满 (S1) stands in front of the shelving in the middle-ground a little "
               "left of centre, facing the shelves and turned three-quarter away from the lens, her torch in "
               "her right hand throwing its beam up onto the shelves; behind her and nearer the doorway 小罗 (S7), "
               "in a dark navy overcoat, is caught in a yawn with one hand over his mouth and his car keys "
               "hanging from the other hand."),
     (2, "05.400", "The camera holds both of them in depth: she keeps her beam on the shelves and does not turn "
                  "round, he finishes the yawn and lowers his hand, and the ceiling tube keeps the whole aisle "
                  "and both of them evenly and generously lit.")],
    "小罗 (S7)'s yawn and the jingle of his keys, her coat hem shifting, the fluorescent tube, night air at the "
    "doorway.",
    "N/A"),

seg("t61", "4-3", "挨着找找", ["xiaoluo", "suxiaoman"], ["lu_storage"],
    "小罗 (S7) pulls the yawn back, says it in the tone of an ordinary instruction — the boss said to look "
    "through the old things from that year under the bridge for anything that matches — and puts his hand back "
    "in his coat pocket.",
    "苏小满 (S1) in front of the shelving with the torch in her hand, facing the shelves; 小罗 (S7) behind her "
    "nearer the doorway, his yawn finished, his hand going back into his coat pocket.",
    [(1, None, "Medium on 小罗 (S7) with 苏小满 (S1) in the near foreground and her back to the lens: he pulls "
               "the yawn back and says it in the tone of an ordinary instruction, "
               "[Chinese] 陆总说了。桥下那年的旧东西，你挨着找找，看有没有能对上的。"),
     (2, "05.800", "Closer on him as he finishes: his hand goes back into his overcoat pocket, his eyes stay on "
                  "her back, and the ceiling tube and the courtyard light through the doorway keep his face "
                  "open and readable with soft shadow under the cheekbones.")],
    "His low conversational voice in the aisle, his keys jingling once, the tube humming, her torch beam "
    "moving on the shelves.",
    "N/A"),

seg("t62", "4-3", "这间是杂物间", ["suxiaoman", "xiaoluo"], ["lu_storage"],
    "Reverse on 苏小满 (S1)'s profile: she answers offhand without taking her eyes off the shelves, the torch "
    "still lighting them.",
    "苏小满 (S1) in front of the shelving with the torch in her hand, her profile to the lens, facing the "
    "shelves; 小罗 (S7) behind her.",
    [(1, None, "Reverse medium on 苏小满 (S1)'s profile with the torch beam on the shelves beside her: she "
               "answers offhand without taking her eyes off the shelves, [Chinese] 这间是杂物间。"),
     (2, "03.400", "Closer on her profile: the torch beam washes the shelf edge just in front of her and "
                  "throws a soft edge of light along her cheek, while the ceiling tube keeps the whole side of "
                  "her face evenly open.")],
    "Her low steady voice, the torch beam hissing softly, the tube's hum, the aisle's night air.",
    "N/A"),

seg("t63", "4-3", "老爷子生前的怪毛病", ["xiaoluo", "suxiaoman"], ["lu_storage"],
    "小罗 (S7) shrugs, takes a hand out of his pocket and puts it straight back, saying that the old man had a "
    "strange habit and never kept good things indoors but pushed them all into the storage room.",
    "苏小满 (S1) in front of the shelving with the torch; 小罗 (S7) behind her and nearer the doorway.",
    [(1, None, "Medium on 小罗 (S7): he shrugs, takes one hand out of his pocket and puts it straight back, "
               "saying, [Chinese] 老爷子生前的怪毛病。好东西不往屋里放，净往杂物间塞。"),
     (2, "06.600", "Closer on him as the line finishes: his shrug settles, he leans his shoulder in towards the "
                  "shelving beside him, and the tube light overhead keeps every plane of his face readable.")],
    "His voice in the aisle, his shoulder against the metal shelving, the fluorescent hum.",
    "N/A"),

seg("t64", "4-3", "光一层层往下移", ["suxiaoman", "xiaoluo"], ["lu_storage"],
    "The torch beam travels down the shelving shelf by shelf, and 苏小满 (S1) runs her other palm along the "
    "shelf partition, her fingertip drawing a clean line through the dust.",
    "苏小满 (S1) in front of the shelving moving the torch beam down the shelves, her other hand on the shelf "
    "partition; 小罗 (S7) behind her, watching.",
    [(1, None, "Medium in the aisle: the torch beam travels down the shelving shelf by shelf while 苏小满 (S1) "
               "runs her other palm along the shelf partition; her fingertip draws a clean line through the dust "
               "and the beam lights each shelf board as it reaches it; behind her 小罗 (S7) leans on the "
               "shelving and watches."),
     (2, "05.600", "Closer on her hand and the shelf: the clean track in the dust runs down the partition and "
                  "the beam pools on the board below it, while the ceiling tube keeps the whole aisle open and "
                  "readable behind her arm.")],
    "Her palm dragging softly through dust, the torch beam on metal, the tube humming, night air at the doorway.",
    "N/A"),

seg("t65", "4-3", "蹲下去照最底层", ["suxiaoman", "xiaoluo"], ["lu_storage"],
    "苏小满 (S1) goes right down into a squat with her knees almost on the concrete and sweeps the torch across "
    "the bottom shelf; her low ponytail falls forward over her shoulder.",
    "苏小满 (S1) squatting in front of the bottom shelf with the torch in her hand, her low ponytail fallen "
    "forward; 小罗 (S7) behind her and nearer the doorway.",
    [(1, None, "Medium low in the aisle: 苏小满 (S1) goes right down into a squat with her knees almost on the "
               "concrete and sweeps the torch across the bottom shelf; her low ponytail falls forward over her "
               "shoulder and the beam runs along the lowest boards; the ceiling tube keeps the whole aisle, the "
               "shelves and the concrete floor clearly readable."),
     (2, "05.400", "Closer from behind her shoulder: she leans in towards the bottom shelf with the beam "
                  "leading, and behind her 小罗 (S7) shifts his weight to see past her into the corner of the "
                  "shelf.")],
    "Her knees and shoes on the concrete, the beam skimming the bottom shelf, the tube's hum, the doorway's "
    "courtyard air.",
    "N/A"),

seg("t66", "4-3", "铁皮盒子", [], ["lu_storage"],
    "The torch beam comes to rest on the bottom shelf: a tin box sits under a thick layer of dust, jammed into "
    "the corner among old nails and an old coil of rope.",
    "the torch beam resting on the bottom shelf of the storage room, the tin box in the corner among old nails "
    "and a coil of old rope.",
    [(1, None, "Close on the bottom shelf as the torch beam comes to rest: a dented tin box sits under a thick "
               "layer of dust, jammed into the corner of the shelf among a scatter of old nails and a coil of "
               "old rope; the ceiling tube behind gives a second clean source so the dust, the box's edges and "
               "the metal of the nails are all clearly legible, and the concrete floor along the bottom third "
               "stays plainly visible."),
     (2, "05.600", "Closer still on the tin box: the dust on its lid is unbroken, the box's seams and its "
                  "dented corners are readable in the beam, and nothing else on the shelf has been disturbed.")],
    "The torch beam steadying on metal, dust settling, the tube humming, the aisle's night air.",
    "N/A"),

seg("t67", "4-3", "一圈焊死的焊点", [], ["lu_storage"],
    "The camera tracks round the tin box: a ring of weld spots has been run all the way round the lid, uneven in "
    "size and crooked, sealing the lid onto the body for good.",
    "the torch beam on the tin box on the bottom shelf, the camera moving round its lid.",
    [(1, None, "Close tracking round the tin box's lid: a ring of weld spots runs all the way round where the "
               "lid meets the body, uneven in size and crooked, and it has sealed the lid onto the box for "
               "good; the torch beam and the ceiling tube light the weld beads from two directions so every "
               "one of them is clearly readable."),
     (2, "05.000", "The track continues and comes to rest on the far side of the ring: the weld beads catch the "
                  "light one after another, the dust on the lid is undisturbed, and the shelf and floor around "
                  "stay open and evenly lit.")],
    "The torch beam creeping along the weld line, the tube's hum, a night bird outside the doorway.",
    "N/A"),

seg("t68", "4-3", "两个歪扭的钢印字", [], ["lu_storage"],
    "The camera moves to the centre of the lid: two hand-stamped steel characters are pressed crooked into the "
    "metal there, the last stroke of the first one barely cut through.",
    "the torch beam on the centre of the tin box's lid, the two hand-stamped steel characters pressed into the "
    "metal.",
    [(1, None, "Close on the centre of the tin box's lid: two hand-stamped steel characters are pressed "
               "crookedly into the metal there, the last stroke of the first one barely cut through; the torch "
               "beam falls straight across them from above and the ceiling tube fills the strokes so they stay "
               "legible as stamped depressions in the metal, with the dust around them undisturbed."),
     (2, "05.200", "Closer still, the beam shifting a little so the two stamped characters catch the light along "
                  "their edges: the impressions are shallow and uneven, the metal around them still furred "
                  "with dust, and the shelf stays evenly lit behind.")],
    "The torch beam steady on the lid, the tube's hum, dust settling on metal.",
    "A single low string note, held.",
    {"lu_storage": "fully_preserved"}),

seg("t69", "4-3", "勿动", ["suxiaoman"], ["lu_storage"],
    "苏小满 (S1) leans in with the torch pointed straight at the two stamped characters and reads them out "
    "quietly to herself.",
    "苏小满 (S1) squatting in front of the bottom shelf with the torch in her hand, the beam on the tin box's "
    "lid.",
    [(1, None, "Medium close on 苏小满 (S1) squatting: she leans in with the torch pointed straight at the two "
               "stamped characters and reads them out quietly, [Chinese] 勿动。"),
     (2, "03.000", "Closer on her face above the beam: her eyes stay on the box, her lips just finishing the "
                  "two syllables, and the ceiling tube keeps her whole face open and soft above the torch pool.")],
    "Her low voice barely above the tube's hum, the torch beam steady, the aisle's night air.",
    "N/A"),

seg("t70", "4-3", "焊完就再没打开过", ["xiaoluo", "suxiaoman"], ["lu_storage"],
    "小罗 (S7) leans in past her to look at the box, points his chin at it and says offhand that the old man "
    "welded it himself, that he went berserk if anyone touched it, and that it was never opened after that.",
    "苏小满 (S1) squatting in front of the bottom shelf with the torch; 小罗 (S7) leaning in past her from "
    "behind, his chin pointing at the tin box.",
    [(1, None, "Medium with 苏小满 (S1) squatting in the near foreground and 小罗 (S7) leaning in past her from "
               "behind: he takes a look at the box, points his chin at it and says offhand, "
               "[Chinese] 那个啊。老爷子亲手焊的。谁碰跟谁急。焊完就再没打开过。"),
     (2, "07.000", "Closer on him as he finishes: he stays leaned in, one hand on the shelf edge above her, and "
                  "the tube light plus the torch pool light both their faces from two directions so nothing is "
                  "left in shadow between them.")],
    "His casual voice in the aisle, his hand on the shelf edge, the tube humming, her breathing.",
    "N/A"),

seg("t71", "4-3", "里面是什么", ["suxiaoman", "xiaoluo"], ["lu_storage"],
    "苏小满 (S1) does not turn round; the torch stays on the box as she asks what is inside it.",
    "苏小满 (S1) squatting in front of the bottom shelf with the torch on the tin box; 小罗 (S7) behind her.",
    [(1, None, "Medium close on 苏小满 (S1) still squatting with her back three-quarter to the lens: she does "
               "not turn round, the torch stays on the box, and she asks, [Chinese] 里面是什么？"),
     (2, "03.200", "Tighter on her from behind and above: the torch pool stays centred on the welded lid, her "
                  "shoulders do not turn, and the ceiling tube keeps her shoulders and the shelf around her "
                  "evenly lit.")],
    "Her low steady voice, the torch beam steady on the lid, the tube's hum, night air at the doorway.",
    "N/A"),

seg("t72", "4-3", "撬都撬不开", ["xiaoluo", "suxiaoman"], ["lu_storage"],
    "小罗 (S7) spreads one hand and shakes his head, saying nobody knows and that it cannot be prised open.",
    "苏小满 (S1) squatting in front of the bottom shelf with the torch; 小罗 (S7) behind her, spreading a hand.",
    [(1, None, "Medium on 小罗 (S7) behind her: he spreads one hand and shakes his head, saying, "
               "[Chinese] 鬼知道。撬都撬不开。"),
     (2, "04.000", "Closer on him as he drops the hand: the shrug settles into his shoulders, he leans back off "
                  "the shelf a little, and the ceiling tube and the doorway's courtyard light keep his face "
                  "fully readable.")],
    "His voice in the aisle, his hand dropping, the tube's hum, a night bird outside.",
    "N/A"),

seg("t73", "4-3", "轻轻抱起来", ["suxiaoman", "xiaoluo"], ["lu_storage"],
    "苏小满 (S1) slides both hands under the tin box and lifts it carefully off the bottom shelf, holding it "
    "the way you would hold something breakable.",
    "苏小满 (S1) squatting with both hands under the tin box, lifting it clear of the bottom shelf; 小罗 (S7) "
    "behind her watching.",
    [(1, None, "Medium low in the aisle: 苏小满 (S1) slides both hands under the tin box and lifts it carefully "
               "clear of the bottom shelf, holding it the way you would hold something breakable; behind her "
               "小罗 (S7) watches; the torch lies on the shelf where her hand left it, still throwing its beam "
               "across the corner and the scattered nails."),
     (2, "05.600", "Closer on the box in her hands: the dust on the lid is broken by her grip and a clean hand "
                  "print shows on the metal, while the ceiling tube keeps the box, her forearms and the whole "
                  "aisle evenly and openly lit.")],
    "The box lifting off metal, dust falling, her coat and apron shifting, the tube's hum.",
    "N/A"),

seg("t74", "4-3", "摇了摇", ["suxiaoman", "xiaoluo"], ["lu_storage"],
    "She gives the tin box one small shake, just enough to move whatever is inside it.",
    "苏小满 (S1) squatting and holding the tin box with both hands; 小罗 (S7) behind her.",
    [(1, None, "Medium close on 苏小满 (S1) squatting: she gives the tin box one small, controlled shake, just "
               "enough to move whatever is inside it, then stops; her elbows stay close to her body and the "
               "torch lies on the shelf behind, its beam still crossing the corner."),
     (2, "04.600", "Closer on the box in her hands as the movement ends: her hands hold it still again, a "
                  "faint trace of dust sifts down past them, and the ceiling tube keeps the whole shot open and "
                  "evenly lit.")],
    "The soft rattle of something loose inside the tin, dust sifting, the tube humming, her breathing.",
    "N/A"),

seg("t75", "4-3", "盒子里轻轻响了一声", [], ["lu_storage"],
    "Very close on the box: something inside shifts and rolls once with a small light sound, then stops.",
    "the tin box held in 苏小满 (S1)'s hands in the aisle, the torch on the shelf behind.",
    [(1, None, "Close on the tin box in her hands: something inside shifts and rolls once with a small light "
               "sound and then stops dead; the top two thirds are her hands and the box, the bottom third the "
               "concrete floor; the ceiling tube and the torch behind keep every plane of the metal and her "
               "fingers evenly lit."),
     (2, "05.000", "The same close held after the movement has stopped: the box is perfectly still in her grip, "
                  "her fingers have not tightened, and the dusty aisle behind stays open and readable.")],
    "One small rolling rattle from inside the tin, then quiet, her held breath, the tube's hum.",
    "A single low string note, held and unresolved.",
    {"lu_storage": "fully_preserved"}),

seg("t76", "4-3", "她停住了", ["suxiaoman", "xiaoluo"], ["lu_storage"],
    "苏小满 (S1) stops moving; something shifts in her eyes, and her hands do not tighten — she only steadies "
    "the box more securely.",
    "苏小满 (S1) squatting and holding the tin box still; 小罗 (S7) behind her.",
    [(1, None, "Close on 苏小满 (S1): she stops moving altogether, something shifts in her eyes, and her hands "
               "do not tighten on the box — she only steadies it more securely, elbows in, chin slightly down; "
               "the ceiling tube keeps the whole front of her face open with soft shadow at the jaw."),
     (2, "05.200", "The same close held: her eyes stay on the box, her grip stays gentle and deliberate, and "
                  "the aisle and the torch-lit corner behind her remain evenly readable.")],
    "Her steadying breath, the tube's hum, a night bird outside the doorway.",
    "N/A"),

seg("t77", "4-3", "放回去", ["suxiaoman", "xiaoluo"], ["lu_storage"],
    "苏小满 (S1) sets the tin box back where it was, between the old nails and the coil of rope, and repeats "
    "the two stamped words very quietly, her head down.",
    "苏小满 (S1) squatting and lowering the tin box back onto the bottom shelf; 小罗 (S7) behind her.",
    [(1, None, "Medium low in the aisle: 苏小满 (S1) sets the tin box back into its place on the bottom shelf "
               "between the old nails and the coil of old rope, and repeats the two stamped words very quietly "
               "with her head down, [Chinese] 勿动。"),
     (2, "05.200", "Closer on her hands letting go: her fingers come off the metal one at a time and the box "
                  "sits flush on the board, the torch and the ceiling tube keeping the shelf, her hands and her "
                  "face evenly and softly lit.")],
    "The box meeting the shelf board, her barely audible voice, the tube's hum, night air at the doorway.",
    "N/A"),

seg("t78", "4-3", "灰上的手印", [], ["lu_storage"],
    "Close on the box where it sits back: the thick dust around it is broken by the hand-print of its lift, a "
    "clean patch one size lighter than the rest.",
    "the tin box back in its corner on the bottom shelf, a clean hand-print break in the dust around it.",
    [(1, None, "Close on the tin box back in its corner on the bottom shelf: the thick dust around it is broken "
               "by the hand-print of its lift, a clean patch one size lighter than the surrounding grey, the "
               "shape of a hand and the shape of the box both readable in it; the ceiling tube and the torch "
               "light the shelf evenly and the concrete floor stays in the bottom third."),
     (2, "05.400", "The same close held: the clean patch does not fill in, the dust around it stays thick and "
                  "grey, and the whole corner of the shelf remains open and readable in two directions.")],
    "Dust settling, the tube's hum, a faint night breeze at the doorway.",
    "A single low string note, held.",
    {"lu_storage": "fully_preserved"}),

seg("t79", "4-3", "起身拍灰", ["suxiaoman", "xiaoluo"], ["lu_storage"],
    "苏小满 (S1) stands up, beats the dust off the front of her work clothes and steps back half a pace from "
    "the shelf.",
    "苏小满 (S1) standing up in front of the bottom shelf after having put the box back; 小罗 (S7) behind her.",
    [(1, None, "Medium in the aisle: 苏小满 (S1) stands up from her squat, beats the dust off the front of her "
               "work shirt and apron with both palms and steps back half a pace from the shelf; behind her "
               "小罗 (S7) has shifted his weight off the shelving; the ceiling tube keeps the whole aisle and "
               "both of them evenly lit."),
     (2, "05.000", "Closer on her as she finishes brushing off: dust drifts down through the torch beam and "
                  "her hands come to rest at her sides, her face open and fully readable under the tube.")],
    "Her palms beating on the cloth, dust falling through the beam, the tube humming, the doorway's air.",
    "N/A"),

seg("t80", "4-3", "又看了那盒子一眼", ["suxiaoman", "xiaoluo"], ["lu_storage"],
    "苏小满 (S1) looks back at the tin box once — just once, less than two seconds — and then goes on.",
    "苏小满 (S1) standing half a pace back from the bottom shelf, looking back at the tin box; 小罗 (S7) behind "
    "her nearer the doorway.",
    [(1, None, "Medium close on 苏小满 (S1) as she looks back at the tin box on the bottom shelf: just once, "
               "less than two seconds, her head turned over her shoulder and her eyes on it; behind her 小罗 (S7) "
               "is already turning away towards the doorway; the tube light and the torch keep the box and her "
               "face both plainly visible."),
     (2, "04.600", "Closer on her eyes as she turns away from the look: her gaze comes off the box and back "
                  "ahead, her jaw stays set, and the aisle around her stays open and evenly lit.")],
    "Her coat shifting as she turns, the tube's hum, his footsteps starting towards the door.",
    "N/A"),

seg("t81", "4-3", "小罗伸了个懒腰", ["xiaoluo", "suxiaoman"], ["lu_storage"],
    "小罗 (S7) has already turned for the door and stretches as he goes, and 苏小满 (S1) turns to follow with "
    "the torch still in her hand, its beam sliding along the concrete floor.",
    "苏小满 (S1) standing half a pace back from the bottom shelf with the torch in her hand; 小罗 (S7) heading "
    "for the doorway at the near end of the aisle, stretching as he goes.",
    [(1, None, "Medium down the aisle: 小罗 (S7) has already turned for the door and stretches as he walks, "
               "arms going up and back; 苏小满 (S1) turns to follow him, the torch still in her hand, its beam "
               "sliding along the concrete floor ahead of her; the ceiling tube keeps the whole aisle and both "
               "of them generously lit."),
     (2, "05.200", "The camera follows them towards the doorway: his stretch comes down, her beam pools on the "
                  "floor and swings up as she walks, and the courtyard light through the open door widens in "
                  "front of them.")],
    "His stretch and heavier footsteps, her flat shoes, the torch beam crossing the floor, the tube humming.",
    "N/A"),

seg("t82", "4-3", "走向亮着的夜", ["suxiaoman", "xiaoluo"], ["lu_storage"],
    "The two of them walk one after the other out through the doorway into the lit courtyard night; the tube "
    "light above stays on and the whole storage room stays clearly readable behind them.",
    "苏小满 (S1) and 小罗 (S7) walking one after the other towards the open doorway of the storage room, the "
    "torch in her hand; the courtyard lamps outside are on.",
    [(1, None, "Wide from inside the room: 苏小满 (S1) and 小罗 (S7) walk one after the other towards the open "
               "doorway, her torch beam bouncing along the concrete, the courtyard lamps outside throwing a "
               "warm light in over the threshold; the ceiling tube stays on above them and the whole room — the "
               "shelves, the floor, the bottom shelf with the tin box — remains clearly readable behind."),
     (2, "05.600", "The camera holds inside the room as they pass out through the door into the lit night: she "
                  "sets the torch down on the bottom shelf beside the tin box as she passes it, its beam staying "
                  "thrown across the corner, then the doorway's warm light widens across the concrete, and the "
                  "storage room itself stays open and "
                  "evenly lit, every shelf still visible.")],
    "Their footsteps crossing the threshold, the night air coming in, the tube humming behind them, a bicycle "
    "chain outside.",
    "N/A"),

seg("t83", "4-3", "盒留原处", [], ["lu_storage"],
    "Close on the bottom shelf: the tin box sits quietly between the old nails and the coil of rope, and the "
    "clean hand-print in the dust around it begins to settle back over.",
    "the tin box on the bottom shelf of the storage room after the two of them have gone out; the torch lies on "
    "the shelf where she set it down on her way past, its beam still thrown across the corner.",
    [(1, None, "Close on the bottom shelf of the storage room: the tin box sits quietly between the scatter of "
               "old nails and the coil of old rope, and the clean hand-print in the dust around it has begun to "
               "settle back over; the torch lies on the shelf where she set it down on her way past, still "
               "throwing its beam across the corner, and the ceiling tube keeps every shelf, the floor and the box evenly and "
               "clearly lit."),
     (2, "06.000", "The same close held as the scene settles: the dust slowly closing over the hand-print, the "
                  "box unmoving, and the whole aisle behind it open, bright and readable to the doorway.")],
    "The fluorescent tube's steady hum, dust settling, night air moving through the open doorway.",
    "A low string entry with one heavy accent, then held low.",
    {"lu_storage": "fully_preserved"}),
]

# ═══════════════════════════════════════════════════════════════════
# 场次 4-4　陆崇书房 · 同一夜稍晚（夜戏 · 台灯与顶灯全开的夜）
# 陆崇恒在书桌后远半幅，心腹恒在书桌前近半幅。
# ═══════════════════════════════════════════════════════════════════
S44 = [
seg("t84", "4-4", "书桌两侧", ["luchong", "xinfu"], ["lu_study"],
    "Opening medium from the study door: a deep dark-wood desk stands across the middle of the room, a "
    "green-shaded desk lamp lit on it and an old photograph lying open beside a document; 陆崇 (S15) sits "
    "behind the desk and 心腹 (S16) stands in front of it.",
    "the study of the 陆 family old house, later the same night; the green-shaded desk lamp on the desk is "
    "switched on and the study's ceiling light is on as well; 陆崇 (S15) sits behind the desk on the FAR side, "
    "facing the near end; 心腹 (S16) stands in front of the desk on the NEAR side, hands at his sides, facing "
    "him; an old photograph and a document lie on the desk.",
    [(1, None, "Medium from the study door looking in: a deep dark-wood desk stands across the middle of the "
               "room with the desk top filling the bottom third; the green-shaded desk lamp on it is switched "
               "on, an old photograph lies open on the wood and a document rests beside it; 陆崇 (S15) sits "
               "behind the desk on the far side facing the near end in a dark ink-blue stand-collar Chinese "
               "jacket; 心腹 (S16) stands in front of the desk on the near side with his hands at his sides, "
               "facing him; the study's ceiling light is on too, so the whole room and both faces are clearly "
               "readable."),
     (2, "05.600", "The camera settles on the two of them across the desk's depth: he sits square and still "
                  "with the lamp's warm light falling on half his face, the man before him stands straight and "
                  "still, and the bookcase wall behind is fully lit rather than lost.")],
    "The desk lamp's faint electrical hum, the study's stillness, a clock ticking on the far wall.",
    "N/A"),

seg("t85", "4-4", "桌上那张照片", [], ["lu_study"],
    "Close on the desk: the old photograph shows 苏小满 (S1) bent over sweeping with an old red cord hanging at "
    "her collar, and a document lies open next to it under the green lamp's light.",
    "the desk top of the study, the green-shaded lamp lit, the old photograph and a document lying on it.",
    [(1, None, "Close on the desk top: an old photograph lies on the wood showing 苏小满 (S1) bent over sweeping "
               "with an old red cord hanging at her collar, and a document lies open beside it; the green "
               "shaded lamp throws a warm pool of light across both while the study's ceiling light fills in the "
               "rest, so the whole print and the paper are evenly readable, the shading across them soft and open."),
     (2, "05.400", "Closer still on the photograph and the document side by side on the wood: the print's "
                  "surface and the document's printed rows are both legible under the two sources at once, and "
                  "the desk's grain runs clean between them.")],
    "The desk lamp's hum, the clock on the far wall ticking, the study's still air.",
    "N/A"),

seg("t86", "4-4", "整面书柜", ["luchong"], ["lu_study"],
    "The camera carries past 陆崇 (S15)'s shoulder across the whole bookcase wall behind him: dark wood, rows "
    "of old spines, the ceiling light resting evenly on them.",
    "陆崇 (S15) seated behind the desk in the study, with the bookcase wall directly behind him.",
    [(1, None, "Medium past 陆崇 (S15)'s shoulder: the whole bookcase wall behind him fills the frame — dark "
               "wood, rows and rows of old book spines, the study's ceiling light resting evenly across them so "
               "the whole wall is readable rather than lost behind him."),
     (2, "05.200", "The camera continues across the wall and stops on the shelves opposite: the spines stand in "
                  "even rows under the ceiling light, and the desk lamp's warm edge reaches only the lowest "
                  "shelf, leaving the upper wall clean and open.")],
    "The clock ticking, the desk lamp's hum, the study's still air.",
    "N/A"),

seg("t87", "4-4", "把材料推过去", ["luchong", "xinfu"], ["lu_study"],
    "陆崇 (S15) pushes a document across the desk towards 心腹 (S16); the paper slides over the wood and comes "
    "to rest by his hand.",
    "陆崇 (S15) seated behind the desk, the document in his hand; 心腹 (S16) standing in front of the desk with "
    "his hands at his sides.",
    [(1, None, "Close on the desk: 陆崇 (S15)'s hand takes a document and pushes it across the wood towards "
               "心腹 (S16) standing in front of the desk; the paper slides over the grain and comes to rest by "
               "the man's hand; the green-shaded lamp lights the slide and the study's ceiling light keeps the "
               "whole desk top evenly readable."),
     (2, "05.000", "Closer on the document arriving at his hand: the paper stops flat by his fingers, the "
                  "sender's hand withdrawing from the far side, and both men's hands are lit evenly from two "
                  "directions across the desk.")],
    "Paper sliding over the desk, the lamp's hum, the clock ticking.",
    "N/A"),

seg("t88", "4-4", "心腹接住材料", ["xinfu", "luchong"], ["lu_study"],
    "心腹 (S16) takes the document and lets it hang at his side; 陆崇 (S15)'s hand comes back and settles on "
    "the desk.",
    "心腹 (S16) standing in front of the desk with the document arriving at his hand; 陆崇 (S15) seated behind "
    "the desk.",
    [(1, None, "Medium: 心腹 (S16) takes the document at the near side of the desk and lets it hang at his side; "
               "behind the desk 陆崇 (S15)'s hand comes back and settles flat on the wood; the lamp's warm pool "
               "lies between them and the ceiling light keeps the whole room open."),
     (2, "05.000", "Closer on the two of them across the desk's depth: the man before the desk holds the "
                  "document straight down at his side and looks at the desktop rather than at his master, who "
                  "sits square and still behind it.")],
    "Paper settling against fabric, the lamp's hum, the clock's tick, the study's quiet.",
    "N/A"),

seg("t89", "4-4", "还拖着", ["xinfu", "luchong"], ["lu_study"],
    "心腹 (S16) reports it flatly, one clause at a time, his eyes on the desktop rather than on the man "
    "behind it — the hospital end is still being held, as instructed.",
    "心腹 (S16) standing in front of the desk with the document hanging at his side; 陆崇 (S15) seated behind "
    "the desk, hands on the wood.",
    [(1, None, "Medium close on 心腹 (S16) standing in front of the desk: he reports it flatly, one clause at a "
               "time, his eyes on the desktop rather than on the man behind it, and says, "
               "[Chinese] 医院那边，按您的意思，还拖着。"),
     (2, "04.400", "Closer on him as the line ends: the document hangs straight and still at his side, his "
                  "face is evenly lit from the front by the ceiling fixture, and the desk lamp's warm edge "
                  "falls along one side of his jaw.")],
    "His even voice in the study, the lamp's hum, the clock ticking on the far wall.",
    "N/A"),

seg("t90", "4-4", "又回了老宅", ["xinfu", "luchong"], ["lu_study"],
    "心腹 (S16) adds the second line and stops there, saying nothing more, the document held square in his hand.",
    "心腹 (S16) standing in front of the desk with the document; 陆崇 (S15) seated behind the desk, watching.",
    [(1, None, "Medium close on 心腹 (S16): he puts the second line out and stops there, saying nothing more, "
               "the document held square in his hand, [Chinese] 她今天去了，又回了老宅。"),
     (2, "04.000", "The same framing held after the line: his mouth closes and stays closed, his eyes stay "
                  "down on the desktop, and the study around him stays open and evenly lit with the ceiling "
                  "light and the desk lamp both on.")],
    "His short voice, the document's paper settling, the clock ticking, the lamp's hum.",
    "N/A"),

seg("t91", "4-4", "她碰什么了", ["luchong", "xinfu"], ["lu_study"],
    "陆崇 (S15) says it with his eyes down, almost expressionless, only the centre of his brow moving very "
    "slightly; he does not look at the man in front of him, he looks at the photograph on the desk as he asks "
    "what she touched.",
    "陆崇 (S15) seated behind the desk with his eyes lowered to the desk top; 心腹 (S16) standing in front of "
    "the desk.",
    [(1, None, "Medium close on 陆崇 (S15): he says it with his eyes down, almost expressionless, only the "
               "centre of his brow moving very slightly; he does not look at the man in front of him, he looks "
               "at the photograph lying on the desk as he asks, [Chinese] 她碰什么了。"),
     (2, "03.400", "Closer on his face: the green lamp's warm light falls on half of it while the ceiling "
                  "fixture fills the other half, so the whole face stays open and readable and the small "
                  "movement at his brow is the only thing that moves.")],
    "His low quiet voice, the desk lamp's hum, the clock ticking.",
    "N/A"),

seg("t92", "4-4", "焊死的铁盒子", ["xinfu", "luchong"], ["lu_study"],
    "心腹 (S16) dips his head slightly and reports it one item at a time: the storage room, and the welded tin "
    "box, which she picked up and shook.",
    "心腹 (S16) standing in front of the desk with the document; 陆崇 (S15) seated behind the desk.",
    [(1, None, "Medium close on 心腹 (S16): he dips his head slightly and reports it one item at a time, his "
               "eyes still down, [Chinese] 杂物间。那个焊死的铁盒子，她抱起来摇了摇。"),
     (2, "05.600", "The same framing held as the line closes: his head comes back up a fraction, the document "
                  "stays at his side, and the study stays bright and open around him with both the ceiling "
                  "light and the green-shaded lamp on.")],
    "His low voice, the clock ticking, the lamp's hum, the study's still air.",
    "N/A"),

seg("t93", "4-4", "脸色沉下去", ["luchong"], ["lu_study"],
    "Close on 陆崇 (S15): his colour sinks slowly, layer by layer, and the line of his jaw tightens a little.",
    "陆崇 (S15) seated behind the desk, hands on the wood, the photograph in front of him.",
    [(1, None, "Close on 陆崇 (S15): his colour sinks slowly, layer by layer, and the line of his jaw tightens a "
               "fraction; the green-shaded lamp's warm light still falls on half his face and the ceiling "
               "fixture still fills the rest, so the change is fully visible without his face going heavy or "
               "underlit."),
     (2, "05.200", "The same close held: his jaw stays set, his eyes stay down on the photograph, and the desk "
                  "lamp's pool and the ceiling light hold the whole study open around him.")],
    "The lamp's hum, the clock ticking, his slow even breathing.",
    "A low string entry, held underneath.",
    {"luchong": "fully_preserved"}),

seg("t94", "4-4", "手指停住", [], ["lu_study"],
    "Close on his hand on the desk: the fingers had been tapping the wood without rhythm, and now they stop — "
    "the pads pressed to the surface, neither lifted nor falling again.",
    "陆崇 (S15)'s hand resting on the desk beside the photograph, the green-shaded lamp on.",
    [(1, None, "Close on 陆崇 (S15)'s hand on the desk: the fingers had been tapping the wood without any "
               "rhythm, and now they stop — the pads pressed down onto the surface, neither lifted nor falling "
               "again; the green-shaded lamp's warm light lies along the knuckles and the ceiling fixture fills "
               "the rest, so the whole hand and the desk grain around it are clearly readable."),
     (2, "05.000", "The same close held: the hand does not move at all, the tendons standing still under the "
                  "skin, and the lamp's pool of light stays steady on the wood.")],
    "The lamp's hum, the clock ticking, his still breathing.",
    "N/A"),

seg("t95", "4-4", "埋了二十二年", ["luchong", "xinfu"], ["lu_study"],
    "After a long pause 陆崇 (S15) speaks, his voice pressed very low: twenty-two years, buried for twenty-two "
    "years.",
    "陆崇 (S15) seated behind the desk, his hand stopped on the wood; 心腹 (S16) standing in front of the desk.",
    [(1, None, "Medium close on 陆崇 (S15): after a long pause he speaks, his voice pressed very low, "
               "[Chinese] 二十二年了。埋了二十二年。"),
     (2, "04.200", "Closer on his face as the number goes out a second time: his eyes have not moved from the "
                  "desk, the lamp's warm light holds half his face and the ceiling light holds the rest, and "
                  "the man standing in front of the desk does not move either.")],
    "His low pressed voice, the clock ticking, the lamp's hum, the study's still air.",
    "A low string entry, sustained and low.",
    {"luchong": "fully_preserved"}),

seg("t96", "4-4", "她非要挖", ["luchong", "xinfu"], ["lu_study"],
    "陆崇 (S15) lifts his eyes off the photograph and moves them to the far edge of the desk, as if looking at "
    "something a long way off, and says she insists on digging it up.",
    "陆崇 (S15) seated behind the desk, his gaze moving from the photograph towards the far edge of the desk; "
    "心腹 (S16) standing in front of it.",
    [(1, None, "Medium close on 陆崇 (S15): he lifts his eyes off the photograph and moves them to the far edge "
               "of the desk, as if looking at something a long way off, and says, [Chinese] 她非要挖。"),
     (2, "03.200", "Closer on his face as the line ends: his gaze stays on that far point, the green-shaded "
                  "lamp's warm light steady on one side of him and the ceiling fixture steady on the other, his "
                  "whole face open and still.")],
    "His low voice, the clock ticking, the lamp's hum.",
    "N/A"),

seg("t97", "4-4", "最冷的一个眼神", ["luchong"], ["lu_study"],
    "Push in on 陆崇 (S15)'s eyes: his pupils are very still and the light in them does not move at all — the "
    "coldest look in the whole series.",
    "陆崇 (S15) seated behind the desk, his gaze fixed on the far edge of the desk; the study lit by both the "
    "ceiling fixture and the green-shaded lamp.",
    [(1, None, "Push in on 陆崇 (S15)'s eyes: his pupils are very still and the light in them does not move at "
               "all; the green-shaded lamp gives a small warm catchlight and the ceiling fixture gives a second "
               "softer one, so the whole eye area stays open and readable; this is the coldest look in the "
               "series."),
     (2, "05.400", "The same close held: nothing in his eyes shifts, no lid drops, and the study around him "
                  "stays bright, open and even with both lights on.")],
    "The lamp's hum, the clock ticking, his even slow breathing.",
    "A low string note, held without resolution.",
    {"luchong": "fully_preserved"}),

seg("t98", "4-4", "别怪我不客气", ["luchong", "xinfu"], ["lu_study"],
    "陆崇 (S15)'s voice drops lower still, almost forced out between his teeth, and the centre of his brow "
    "moves once more as he finishes.",
    "陆崇 (S15) seated behind the desk, gaze still fixed ahead; 心腹 (S16) standing in front of the desk.",
    [(1, None, "Medium close on 陆崇 (S15): his voice drops lower still, almost forced out between his teeth, and "
               "the centre of his brow moves once more as he says, [Chinese] 那就别怪我不客气。"),
     (2, "04.400", "Closer on his face as the line closes: his mouth stays shut after it, his gaze does not "
                  "move, and both the desk lamp and the ceiling fixture keep the whole front of his face "
                  "evenly lit and readable.")],
    "His low forced voice, the clock ticking, the lamp's hum, the study's still air.",
    "A single muted drum, felt rather than loud.",
    {"luchong": "fully_preserved"}),

seg("t99", "4-4", "心腹退半步", ["xinfu", "luchong"], ["lu_study"],
    "心腹 (S16) takes half a step back from the desk with his hands still down and the document unmoved; "
    "nothing crosses his face.",
    "心腹 (S16) standing half a pace back from in front of the desk, the document hanging at his side; 陆崇 "
    "(S15) seated behind the desk.",
    [(1, None, "Medium: 心腹 (S16) takes half a step back from in front of the desk with his hands still down and "
               "the document unmoved at his side; nothing crosses his face; behind the desk 陆崇 (S15) sits "
               "unmoved, and the study stays bright and open with the ceiling light and the green-shaded lamp "
               "both on."),
     (2, "05.000", "Closer on the man as he settles: his shoulders come down a fraction, the document hangs "
                  "straight and still, and the desk lamp's warm pool lies between the two of them.")],
    "One step back on the floor, the lamp's hum, the clock ticking, the study's quiet.",
    "N/A"),

seg("t100", "4-4", "靠向椅背", ["luchong", "xinfu"], ["lu_study"],
    "陆崇 (S15) leans back into his chair and sits there without moving; 心腹 (S16) steps forward, lays the document "
    "flat on the desk in front of him and withdraws his hand, leaving it there.",
    "陆崇 (S15) seated behind the desk leaning back into his chair; 心腹 (S16) standing half a pace back from "
    "the desk with the document in his hand.",
    [(1, None, "Medium close on 陆崇 (S15): he leans back into his chair and sits there without moving; the "
               "green-shaded lamp's warm light and the ceiling fixture together keep his whole face and the "
               "chair's dark wood back clearly readable; 心腹 (S16) stands half a pace back in the near half of "
               "frame with the document still in his hand."),
     (2, "05.400", "The same framing held: 心腹 (S16) steps forward one pace, lays the document flat on the desk "
                  "in front of 陆崇 (S15) so it lies square on the wood, and takes his hand away; 陆崇 (S15) stays "
                  "back in the chair with his hands on the desk, and the whole study remains evenly lit and readable.")],
    "The chair creaking once, the lamp's hum, the clock ticking.",
    "N/A"),

seg("t101", "4-4", "材料与照片都在原处", [], ["lu_study"],
    "Close on the desk: the document and the old photograph are both where they were, the green-shaded lamp's "
    "light falling across the paper.",
    "the desk top with the document and the old photograph lying on it, the green-shaded lamp lit.",
    [(1, None, "Close on the desk top: the document and the old photograph are both exactly where they were, the "
               "green-shaded lamp's light falling across the paper and the photograph's print; the ceiling "
               "fixture adds a second even source so both are fully readable and neither lies in shadow; the "
               "the wood grain runs clean around them."),
     (2, "05.200", "Closer still on the two of them lying side by side on the wood: the photograph's surface and "
                  "the document's printed rows are both legible, and the lamp's warm pool holds steady across "
                  "both.")],
    "The lamp's hum, the clock ticking, the study's still air.",
    "N/A"),

seg("t102", "4-4", "两人定格", ["luchong", "xinfu"], ["lu_study"],
    "Medium: 陆崇 (S15) sits back behind the desk and 心腹 (S16) stands in front of it; the ceiling light and "
    "the desk lamp are both on and the whole study is clearly readable.",
    "陆崇 (S15) seated back behind the desk; 心腹 (S16) standing in front of it; both the study's ceiling light "
    "and the green-shaded desk lamp are on.",
    [(1, None, "Medium across the desk's depth axis: 陆崇 (S15) sits back behind the desk in the far half of "
               "frame and 心腹 (S16) stands in front of it in the near half; the study's ceiling light and the "
               "green-shaded desk lamp are both switched on and the whole room — the bookcase wall, the desk, "
               "the floor — is clearly and evenly readable, with no corner of the room left dark."),
     (2, "06.000", "The same framing held a moment longer: neither man moves, the lamp's warm pool lies across "
                  "the desk between them, and the room stays open and bright to the edges of frame.")],
    "The lamp's hum, the clock ticking on the far wall, the study's still air.",
    "N/A"),

seg("t103", "4-4", "一处也没有压暗", ["luchong", "xinfu"], ["lu_study"],
    "Close on the green-shaded desk lamp: its glow falls across the edges of the document and the photograph on "
    "the desk, with the ceiling light layering down from above; nothing in the room is left dark.",
    "the green-shaded desk lamp lit on the desk beside the document and the old photograph, the study's ceiling "
    "light on above it.",
    [(1, None, "Close on the green-shaded desk lamp: its glow falls across the edges of the document and the "
               "old photograph lying on the desk, and the study's ceiling light layers down from above it; the "
               "wall behind, the bookcase edge and the desk surface are all lit at once, so nothing in this "
               "room is left with every surface still readable."),
     (2, "05.600", "The same close held: the lamp's warm pool stays steady on the paper, the ceiling light "
                  "keeps the whole upper frame open, and the room reads as a fully lit night rather than one lamp "
                  "standing in an otherwise empty frame.")],
    "The lamp's hum, the clock ticking, the study's still air.",
    "N/A"),

seg("t104", "4-4", "本集收尾", ["luchong", "xinfu"], ["lu_study"],
    "Medium: 陆崇 (S15) sits still in his chair behind the desk and 心腹 (S16) stands with his hands down in "
    "front of it; the study's ceiling light and the desk lamp are both on.",
    "陆崇 (S15) seated back and still behind the desk; 心腹 (S16) standing with his hands down in front of it; "
    "the study's ceiling light and the green-shaded desk lamp both on.",
    [(1, None, "Medium closing on the study: 陆崇 (S15) sits still in his chair behind the desk and 心腹 (S16) "
               "stands with his hands down in front of it; the study's ceiling light and the green-shaded desk "
               "lamp are both switched on, the bookcase wall and the whole desk are readable, and neither man "
               "moves; the frame holds on the two of them across the desk's depth with the lamp between them."),
     (2, "06.000", "The closing hold: the two of them stay exactly as they are in a fully lit room, the clock "
                  "ticking on the far wall, and the last of the lamp's warm pool lies across the document and "
                  "the photograph on the desk.")],
    "The lamp's hum, the clock ticking steadily, the study's still air.",
    "A single muted drum, then a low string held under the tail.",
    {"luchong": "fully_preserved"}),
]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(OUT, exist_ok=True)
    dump("scene41a.json", S41A)
    dump("scene41b.json", S41B)
    dump("scene42.json", S42)
    dump("scene43.json", S43)
    dump("scene44.json", S44)
    allseg = S41A + S41B + S42 + S43 + S44
    ids = [x["id"] for x in allseg]
    assert ids == ["ep04_t%02d" % i for i in range(1, len(ids) + 1)], "id 不连续"
    print("  合计 %d 段，id 连续 ep04_t01 – ep04_t%02d" % (len(ids), len(ids)))
