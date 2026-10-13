# -*- coding: utf-8 -*-
r"""
按三组审核意见批量修正分镜源数据。
注意：beats JSON 里换行是字面量 \n（反斜杠+n），所以 Python 源里要写 \\n。
"""
import io
import json
import os
import sys

B = r"E:\LLM\try\minidrama\保洁\ep001_beats"

PATCHES = [
    # ---------- scene12b ----------
    ("scene12b.json",
     "[Shot 3] At 00:04.400, closer on 周总监 (S6) as he speaks in a low, slow, completely level Mandarin, letting the silence do the work: [Chinese] 小钱。干什么呢。\\n[Shot 4] At 00:08.000, he adds the second line with a small tip of his head: [Chinese] 吵得，一层楼都听得见。 Hold on 钱经理 (S3), who has gone stiff. 苏小满 (S1) stays silent.",
     "[Shot 3] At 00:03.600, closer on 周总监 (S6) as he speaks in a low, slow, completely level Mandarin, letting the silence do the work: [Chinese] 小钱。干什么呢。\\n[Shot 4] At 00:06.000, 周总监 (S6) adds the second line with a small tip of his head: [Chinese] 吵得，一层楼都听得见。 Hold on 钱经理 (S3), who has gone stiff. 苏小满 (S1) stays silent with her mouth closed."),

    ("scene12b.json",
     "[Shot 2] At 00:02.400, close on 钱经理 (S3) as he tells it fast and pleased, in a loud nasal Mandarin: [Chinese] 总监。抓着个内贼。\\n[Shot 3] At 00:05.800, he lifts the black card up between them and taps it twice with a finger: [Chinese] 偷东西，偷到万山的卡上了。",
     "[Shot 2] At 00:02.000, close on 钱经理 (S3) as he tells it fast and pleased, in a loud nasal Mandarin: [Chinese] 总监。抓着个内贼。\\n[Shot 3] At 00:05.400, 钱经理 (S3) lifts the black card up between them and taps it twice with a finger: [Chinese] 偷东西，偷到万山的卡上了。"),

    ("scene12b.json",
     "[Shot 4] At 00:07.600, then, still looking at her: [Chinese] 入职多久了。 Hold on 苏小满 (S1), who answers nothing yet.",
     "[Shot 4] At 00:07.600, 周总监 (S6), still looking at 苏小满 (S1): [Chinese] 入职多久了。 Hold on 苏小满 (S1), who answers nothing yet."),

    # ---------- scene12c ----------
    ("scene12c.json",
     "[Chinese] 你还挺牛。\\n[Shot 2] At 00:05.000, he pushes it further, throwing his chin toward the doorway crowd for the laugh: [Chinese] 人家大户人家求你，你还端上了。",
     "[Chinese] 你还挺牛。\\n[Shot 2] At 00:04.600, 钱经理 (S3) pushes it further, throwing his chin toward the doorway crowd for the laugh: [Chinese] 人家大户人家求你，你还端上了。"),

    ("scene12c.json",
     "[Chinese] 打完，两清。你走你的路。\\n[Shot 2] At 00:08.000, closer on his face as he adds the alternative with no change of tone at all: [Chinese] 要不，你承认是你偷的。",
     "[Chinese] 打完，两清。你走你的路。\\n[Shot 2] At 00:06.000, closer on 周总监's (S6) face as he adds the alternative with no change of tone at all: [Chinese] 要不，你承认是你偷的。"),

    # T60：25 字拆成 3 拍（一句台词分三镜，不改字）
    ("scene12c.json",
     "[Shot 1] Wide: the LEFT doorway crowd splits as 前台 (S12) shoulders through, phone held up in one hand, half running, blazer flying.\\n[Shot 2] At 00:00.400, medium: she comes straight to the desk, holds the phone up toward 钱经理 (S3) and rattles it out in a loud bright panicked Mandarin, at a shout, very fast and breathless, all in one rush: [Chinese] 钱经理！客人来电话了！耳钉找到了！掉在他自己车里，座位缝里！\\n[Shot 3] At 00:08.800, wide and held: the chair legs come down with a bang. Every single person in the room has gone still. Nobody says a word to 苏小满 (S1).\\n[Shot 4] At 00:09.600, hold on 苏小满 (S1) standing exactly where she was, no expression change at all.",
     "[Shot 1] Wide: the LEFT doorway crowd splits as 前台 (S12) shoulders through, phone held up in one hand, half running, blazer flying, and 前台 (S12) starts shouting before she is even through the door, in a loud bright panicked Mandarin: [Chinese] 钱经理！客人来电话了！\\n[Shot 2] At 00:04.000, medium: she is at the desk now, holding the phone up toward 钱经理 (S3), and 前台 (S12) goes on at a shout in one burst: [Chinese] 耳钉找到了！\\n[Shot 3] At 00:05.400, closer on her flushed face as 前台 (S12) finishes it in one rush: [Chinese] 掉在他自己车里，座位缝里！\\n[Shot 4] At 00:09.000, wide and held: the chair legs come down with a bang. Every single person in the room has gone still. Nobody says a word to 苏小满 (S1), who stands exactly where she was with no expression change at all."),

    # T67：24 字拆成 3 拍
    ("scene12c.json",
     "[Shot 1] Medium: 小罗 (S7) holds the card up at chest height, addressing nobody in particular, in the same quiet courteous Mandarin, evenly, one clause at a time: [Chinese] 这张卡，三天前，是我们留给苏小姐的。\\n[Shot 2] At 00:08.400, he turns a quarter step and runs his eyes slowly around the room — the manager, the doorway crowd, the director — before he adds it, still perfectly polite: [Chinese] 让各位，误会了。\\n[Shot 3] At 00:09.400, wide and held: absolute stillness. 钱经理 (S3) has gone grey, 小唐 (S4) at the door is white as paper, and nobody in the doorway makes a sound.\\n[Shot 4] At 00:09.800, hold on 苏小满 (S1), the only person in the room who has not changed at all.",
     "[Shot 1] Medium: 小罗 (S7) holds the card up at chest height, addressing nobody in particular, in the same quiet courteous Mandarin, evenly: [Chinese] 这张卡，三天前，\\n[Shot 2] At 00:04.000, closer on 小罗 (S7) as he goes on, still perfectly level: [Chinese] 是我们留给苏小姐的。\\n[Shot 3] At 00:07.400, 小罗 (S7) turns a quarter step and runs his eyes slowly around the room — the manager, the doorway crowd, the director — before he adds it, still perfectly polite: [Chinese] 让各位，误会了。\\n[Shot 4] At 00:09.400, wide and held: absolute stillness. 钱经理 (S3) has gone grey, 小唐 (S4) at the door is white as paper, and nobody in the doorway makes a sound; 苏小满 (S1) is the only person in the room who has not changed at all."),

    # ---------- scene12e ----------
    ("scene12e.json",
     "钱经理 (S3) is behind him on the left, still at the desk; the room is emptying, the crowd gone from the doorway.",
     "钱经理 (S3) is left standing in the middle-left of the room where 苏小满 (S1) walked past him, a few steps away from the desk; the room is emptying, the crowd gone from the doorway."),

    ("scene12e.json",
     "Entry state, re-anchored to the reference image: 钱经理 (S3) stands on the near side of the desk; 周总监 (S6) on the far side behind it; the black card is gone from the desktop, leaving the empty dark wood.",
     "Entry state, re-anchored to the reference image: 周总监 (S6) has walked back and stands behind the desk on the far side; 钱经理 (S3) stands in front of the desk on the lower-left of frame facing him; the black card is gone from the desktop, leaving the empty dark wood."),

    ("scene12e.json",
     "周总监 (S6) stands behind the desk on the far side; 钱经理 (S3) on the near side, leaning in; the office empty, the LEFT door still open to the corridor.",
     "周总监 (S6) stands behind the desk on the far side; 钱经理 (S3) leans in toward him from the lower-left of frame in front of the desk; the office empty, the LEFT door still open to the corridor."),

    ("scene12e.json",
     "Nobody speaks and there is no dialogue in this beat at all.",
     "Nobody speaks in this beat and every mouth stays shut."),

    # ---------- scene13 ----------
    ("scene13.json",
     "cool-blue evening light through tall windows and warm tungsten spill from the ward doorway.",
     "generous ceiling fluorescents switched on, blue evening light from the tall window at the far end of the corridor, and warm tungsten spill from the ward doorway."),

    ("scene13.json",
     "[Shot 1] Medium: she crosses to the LEFT wall, lets her back settle against it just beside the bench, takes out her phone and dials with her thumb, holding the screen up close.",
     "[Shot 1] Medium: 苏小满 (S1) crosses to the LEFT wall, lets her back settle against it just beside the bench, takes out her phone and dials with her thumb, holding the screen up close."),

    # ---------- scene14a ----------
    ("scene14a.json",
     "Same office, second day, taken from the reference images: door on the LEFT of frame, the venetian-blind window and tall wooden cabinets on the RIGHT, the desk across the middle; bright early-afternoon light through the blinds, the room spotless.",
     "Entry state, new day, same office, taken from the reference images: 苏小满 (S1) stands on the NEAR side of the desk with her back to the LEFT door and her cardboard box on the desk beside her; the office is spotless and empty of anybody else; door on the LEFT of frame, the venetian-blind window and tall wooden cabinets on the RIGHT; bright early-afternoon light through the blinds."),

    ("scene14a.json",
     "[Shot 1] Medium: 苏小满 (S1) lifts the box to her chest, turns and walks toward the LEFT door; 钱经理 (S3) does not move out of the way, so she has to stop a step short of him.\\n[Shot 2] At 00:03.600, he holds out a printed form in one hand and taps it twice with the other, speaking in a brisk transactional Mandarin, one clause at a time: [Chinese] 辞工单还没签。签了，这个月工资给你。不签，一分没有。\\n[Shot 3] At 00:09.400, reverse onto 苏小满 (S1): the box still in her arms, the form held out in front of her face; she stops moving altogether.\\n[Shot 4] At 00:09.800, close on the printed form filling the space between them, his two fingers tapping it. Neither of them speaks again here.",
     "[Shot 1] Medium: 苏小满 (S1) lifts the box to her chest and turns toward the LEFT door; 钱经理 (S3) blocks it, holds out a printed form in one hand and taps it twice with the other, speaking in a brisk transactional Mandarin: [Chinese] 辞工单还没签。\\n[Shot 2] At 00:03.600, 钱经理 (S3) goes on without a pause, tapping the form again: [Chinese] 签了，这个月工资给你。\\n[Shot 3] At 00:07.000, closer on 钱经理's (S3) face as he delivers the last part flatly: [Chinese] 不签，一分没有。\\n[Shot 4] At 00:09.400, reverse onto 苏小满 (S1): the box still in her arms, the form held out in front of her face; she stops moving altogether and says nothing."),

    ("scene14a.json",
     "[Shot 1] Medium: 张总 (S10) brings his flat palm down on the desk so hard that the pen tray jumps, then leans over it toward the manager and spits it out at a shout, very fast, in one long unbroken burst of loud Mandarin: [Chinese] 正常流程？人家一句话，明年，咱们公司就得从这楼里滚出去！\\n[Shot 2] At 00:08.600, wide: 钱经理 (S3) has both hands up in front of his chest as if warding off a blow; the resignation form has slid to the floor.\\n[Shot 3] At 00:09.400, cut to 苏小满 (S1) in the doorway, watching all of it without a flicker.\\n[Shot 4] At 00:09.800, hold on the room. Nobody else speaks.",
     "[Shot 1] Medium: 张总 (S10) brings his flat palm down on the desk so hard that the pen tray jumps, then leans over it toward 钱经理 (S3) and spits it out at a shout in loud Mandarin: [Chinese] 正常流程？\\n[Shot 2] At 00:02.400, 张总 (S10) jabs the air with one finger, hammering each phrase: [Chinese] 人家一句话，明年，\\n[Shot 3] At 00:04.200, closer on 张总's (S10) flushed sweating face as he finishes it, still shouting: [Chinese] 咱们公司就得从这楼里滚出去！\\n[Shot 4] At 00:09.400, wide and held: 钱经理 (S3) has both hands up in front of his chest as if warding off a blow, the resignation form has slid across the desktop, and 苏小满 (S1) watches all of it from the LEFT doorway without a flicker. Nobody else speaks."),

    # ---------- scene14b ----------
    ("scene14b.json",
     "[Shot 4] At 00:08.400, she straightens, hands the form back to 钱经理 (S3) with both hands, and says it in her flat low Mandarin: [Chinese] 字，我自己写的。",
     "[Shot 4] At 00:07.200, she straightens, hands the form back to 钱经理 (S3) with both hands, and says it in her flat low Mandarin: [Chinese] 字，我自己写的。"),

    # T115/T116/T117：小罗统一站 LEFT 肩后（与 1-5 锚点一致）
    ("scene14b.json",
     "小罗 (S7) has followed her out and stands a step behind her right shoulder",
     "小罗 (S7) has followed her out and stands half a step behind her LEFT shoulder"),

    ("scene14b.json",
     "[Shot 1] Close on 小罗 (S7): he takes half a step closer and drops his voice so that only she can hear, speaking low and quickly, in his courteous even Mandarin, all of it in one breathless run: [Chinese] 上车说。您外婆在市一院，八楼。陆总要谈的事，还是三天前那件。\\n[Shot 2] At 00:06.600, thin view of the interior of the car beyond him through the open door: the pale-grey leather rear bench, the warm amber lights along the roof lining, the far back seat empty and waiting.\\n[Shot 3] At 00:09.000, tight on 苏小满's (S1) eyes as the eighth floor lands.\\n[Shot 4] At 00:09.800, hold on her face. She does not answer.",
     "[Shot 1] Close on 小罗 (S7): he takes half a step closer and drops his voice so that only she can hear, speaking low and quickly in his courteous even Mandarin: [Chinese] 上车说。\\n[Shot 2] At 00:04.000, 小罗 (S7) goes on, still pitched only for her: [Chinese] 您外婆在市一院，八楼。\\n[Shot 3] At 00:08.600, tight on 苏小满's (S1) eyes as the ward floor lands.\\n[Shot 4] At 00:09.600, hold on her face. She does not answer."),

    ("scene14b.json",
     "苏小满 (S1) stands at the open rear door of the black sedan on the bright forecourt with the box in her arms; 小罗 (S7) is a step behind her right shoulder; the driver holds the door.",
     "苏小满 (S1) stands at the open rear door of the black sedan on the late-afternoon forecourt with the box in her arms; 小罗 (S7) is half a step behind her LEFT shoulder; the driver holds the door."),

    ("scene14b.json",
     "苏小满 (S1) stands at the open rear door of the black sedan on the forecourt; 小罗 (S7) is behind her right shoulder; the car interior is visible through the open door",
     "苏小满 (S1) stands at the open rear door of the black sedan on the forecourt; 小罗 (S7) is half a step behind her LEFT shoulder; the car interior is visible through the open door"),

    ("scene14b.json",
     "[Shot 2] At 00:03.200, medium: she lifts the cardboard box and sets it in on the seat first, then ducks her head and gets in after it.\\n[Shot 3] At 00:06.200, the driver closes the rear door behind her with one soft push; through the tinted glass her shape settles onto the pale-grey bench with the box on her knees.\\n[Shot 4] At 00:08.400, the car pulls away from the kerb and the bright forecourt slides out of frame; the next black car in the line moves up to take its place. Nobody speaks in this beat.",
     "[Shot 2] At 00:02.000, close on 小罗 (S7) as he finishes what he started, still quietly and only for her: [Chinese] 陆总要谈的事，还是三天前那件。\\n[Shot 3] At 00:08.000, medium: she lifts the cardboard box and sets it in on the seat first, then ducks her head and gets in after it.\\n[Shot 4] At 00:09.400, the driver closes the rear door behind her with one soft push and the car pulls away from the kerb into the blue dusk with its tail lights coming on; the next black car in the line moves up to take its place. Nobody else speaks in this beat."),

    # ---------- scene15 ----------
    ("scene15.json",
     "New location, taken from the reference image: the rear cabin of the black sedan seen from the front seats looking back — a wide pale-grey leather rear bench with a central armrest, warm amber courtesy lights along the roof lining, tinted windows with bright city bokeh sliding past outside. 苏小满 (S1) sits in the RIGHT rear seat with the cardboard box upright on her knees. 陆蔓 (S8), a composed woman of fifty in a deep-green jacquard silk qipao, sits in the LEFT rear seat, one empty place between them.",
     "Entry state, new location, much later that night, taken from the reference image: the rear cabin of the moving black sedan seen from the front seats looking back — a wide pale-grey leather rear bench with a central armrest, warm amber courtesy lights along the roof lining, tinted windows with bright city bokeh sliding past outside. 苏小满 (S1) sits in the RIGHT rear seat with the cardboard box upright on her knees; the LEFT rear seat is still empty. 陆蔓 (S8) is a composed woman of fifty in a deep-green jacquard silk qipao."),

    ("scene15.json",
     "[Shot 1] Wide from the front: the car interior in warm amber light, the city sliding past the tinted glass, her cardboard box standing on her knees, her hands flat on top of it.\\n[Shot 2] At 00:03.400, she turns her head just enough to look at the woman on her left without turning her shoulders.",
     "[Shot 1] Wide from the front: the car running through the city at night in warm amber light, the city sliding past the tinted glass, her cardboard box standing on her knees, her hands flat on top of it, the seat beside her empty.\\n[Shot 2] At 00:03.400, the LEFT rear door opens and 陆蔓 (S8) gets in and settles onto the LEFT rear seat, pulling the door shut; one empty place between them. 苏小满 (S1) turns her head just enough to look at her without turning her shoulders."),

    ("scene15.json",
     "New location, night: the back of the moving car. She sits with her cardboard box on her knees, and a well-dressed woman of about fifty gets in beside her.",
     "Night, much later the same evening: the back of the moving car. She sits with her cardboard box on her knees, and the woman who was introduced as 陆总 gets in and settles into the seat beside her."),

    ("scene15.json",
     "a young man's voice comes through the crack, casual and impatient, entirely unaware he can be heard: [Chinese] 姐，人到了没？……管他真的假的。能签字，就行。 The voice belongs to 陆航 (S14), who stays completely off screen and is never seen in this beat.",
     "a young man's voice (S14) comes through the crack, casual and impatient, entirely unaware he can be heard: [Chinese] 姐，人到了没？……管他真的假的。能签字，就行。 陆航 (S14) stays completely off screen and is never seen in this beat."),
]

# T116 去掉 car_interior（白天外景段不该拿夜内景当光照参考）
REF_FIX = {
    ("scene14b.json", "ep01_t116"): (["xiaoluo", "suxiaoman", "building_exterior"],
                                    {"building_exterior": "fully_preserved"}),
}


def apply_text_patches():
    ok = miss = 0
    for fn, old, new in PATCHES:
        p = os.path.join(B, fn)
        s = io.open(p, "r", encoding="utf-8").read()
        if old not in s:
            print("  MISS  %-16s %s" % (fn, old[:60].replace("\n", " ")))
            miss += 1
            continue
        s = s.replace(old, new, 1)
        io.open(p, "w", encoding="utf-8", newline="\n").write(s)
        print("  OK    %-16s %s" % (fn, new[:60].replace("\n", " ")))
        ok += 1
    return ok, miss


def apply_ref_fixes():
    for (fn, sid), (refs, ret) in REF_FIX.items():
        p = os.path.join(B, fn)
        d = json.load(io.open(p, "r", encoding="utf-8"))
        hit = False
        for seg in d:
            if seg["id"] == sid:
                seg["refs"] = refs
                seg["retention"] = ret
                hit = True
        if not hit:
            print("  MISS ref", fn, sid)
            continue
        io.open(p, "w", encoding="utf-8", newline="\n").write(
            json.dumps(d, ensure_ascii=False, indent=1))
        print("  OK   ref %-16s %s -> %s" % (fn, sid, refs))


if __name__ == "__main__":
    print("--- 文本替换 ---")
    ok, miss = apply_text_patches()
    print("--- ref 修正 ---")
    apply_ref_fixes()
    print("文本替换成功 %d / 失败 %d" % (ok, miss))
