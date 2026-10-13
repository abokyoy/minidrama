# -*- coding: utf-8 -*-
r"""
第四轮补丁：修第二轮子代理复核报出的问题。

原则（用户最高工作原则）：
  · 先把「站位/道具/朝向」锁成**唯一确定**的一条链，再写分镜；同一场里人物不许瞬移。
  · 锚点句只能描述**确定**的调度，不许出现 "may walk round ... into the middle-left" 这种放权。

本轮修：
  A. ANCHOR_12  钱经理站位改为「一次离桌」的确定调度；桌面道具改写
  B. ANCHOR_14  1-4 场办公室段：钱经理本来就是拦门的，锚点与正文对齐
  C. ANCHOR_15  车里陆蔓「从离开大楼起就在车上」，修「行进中上车」的硬伤
  D. t18–t35    办公室 18 段站位统一（钱经理不许站到苏小满那一侧 / mid-room）
  E. t67        跨镜头断句合成整句，避免两段各自生成音频接不上
  F. t106/115/129  台词补 (S1)
  G. t113→t114  去掉重复的「走出玻璃门」
  H. t117/t118  陆蔓上车时机对齐
  I. t126→t127  补「下车 + 小罗已在门外等候 + 陆蔓留在车上」的过渡
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BEATS = os.path.join(BASE, "ep001_beats")
RENDER = os.path.join(BASE, "storyboard_render.py")

MISS = []


# ---------------------------------------------------------------- 文本级补丁
def patch_text_file(path, pairs):
    src = io.open(path, encoding="utf-8").read()
    for i, (old, new) in enumerate(pairs, 1):
        if old not in src:
            MISS.append("%s #%d 未命中: %s" % (os.path.basename(path), i, old[:70]))
            continue
        if src.count(old) > 1:
            MISS.append("%s #%d 命中 %d 次（需唯一）: %s" % (os.path.basename(path), i, src.count(old), old[:50]))
        src = src.replace(old, new)
    io.open(path, "w", encoding="utf-8").write(src)


# ---------------------------------------------------------------- beats 补丁
def patch_beats(pairs_by_seg):
    """pairs_by_seg = {seg_id: [(old, new), ...]}"""
    for f in sorted(os.listdir(BEATS)):
        if not f.endswith(".json"):
            continue
        p = os.path.join(BEATS, f)
        data = json.load(io.open(p, encoding="utf-8"))
        touched = False
        for seg in data:
            for old, new in pairs_by_seg.get(seg["id"], []):
                if old not in seg["shots"]:
                    MISS.append("%s %s 未命中: %s" % (f, seg["id"], old[:70]))
                    continue
                if seg["shots"].count(old) > 1:
                    MISS.append("%s %s 命中多次: %s" % (f, seg["id"], old[:50]))
                seg["shots"] = seg["shots"].replace(old, new)
                touched = True
        if touched:
            io.open(p, "w", encoding="utf-8").write(
                json.dumps(data, ensure_ascii=False, indent=1))


# ================================================================ A/B/C 锚点
ANCHOR_PAIRS = [
    # --- A1 钱经理站位：把"may walk round into the middle-left"换成"一次离桌"的确定调度
    (
        '"room. 苏小满 (S1) ALWAYS stays on the NEAR side of the desk, between the desk and the door, back to the door, facing "\n'
        '    "the window side; she may turn on the spot but she never crosses to the far side and never moves to the middle of the "\n'
        '    "room. 钱经理 (S3) begins every beat on the FAR side of the desk, back to the window, facing the door; while 苏小满 "\n'
        '    "(S1) is in the room he may walk round the corner into the middle-left of the room and lean or sit, but he never gets "\n'
        '    "behind her towards the door; once she has left the room he is free to stand in front of the desk as well. 小唐 (S4) "',
        '"room. 苏小满 (S1) ALWAYS stays on the NEAR side of the desk, between the desk and the door, back to the door, facing "\n'
        '    "the window side; she may turn on the spot but she never crosses to the far side and never moves to the middle of the "\n'
        '    "room. 钱经理 (S3) begins every beat on the FAR side of the desk, back to the window, facing the door, and he STAYS "\n'
        '    "there except for exactly one excursion: in the 掏兜 beat he steps round the end of the desk onto the near side and "\n'
        '    "stands one pace in front of her; he stays there through the 心虚, 摆上桌, 还有 and 黑卡 beats; and at the end of the "\n'
        '    "拿来 beat, the moment the card is in his hand, he turns and walks back round to his place on the far side and stays "\n'
        '    "there for the rest of the scene. Apart from those two scripted moves he is never on the near side and NEVER in the "\n'
        '    "middle of the room — until 苏小满 (S1) has left the room, after which he is free to leave the desk and stand in "\n'
        '    "front of it. 小唐 (S4) "',
    ),
    # --- A2 桌面道具：开场是空桌面，钥匙+笔由苏小满自己放上去，纸单永不留在桌上
    (
        '"苏小满. The onlookers crowd the open doorway on the LEFT. On the desk surface the keys and the ballpoint pen lie "\n'
        '    "throughout; the folded paper form is in 苏小满\'s (S1) hand until she puts it away; the black card joins the desktop "\n'
        '    "only at the moment 钱经理 (S3) slaps it down. Never mirror, swap or re-arrange any of this."',
        '"苏小满. The onlookers crowd the open doorway on the LEFT. The desktop is bare at the start of the scene; 苏小满 (S1) "\n'
        '    "herself lays the bunch of keys and the ballpoint pen on it in the middle of the scene and only those two objects then "\n'
        '    "stay on it to the end; the folded paper form is in her hand or closed in her trouser pocket and is never left lying "\n'
        '    "on the desk; the black card joins the desktop only at the moment 钱经理 (S3) slaps it down. Never mirror, swap or "\n'
        '    "re-arrange any of this."',
    ),
    # --- B 1-4 场：钱经理本来就是拦门的，锚点改成与正文一致
    (
        '"Fixed spatial set-up for this whole beat, never change it. First half — the property office, exactly as before: the "\n'
        '    "door on the LEFT of frame, the window and cabinets on the RIGHT, the desk across the middle, 钱经理 (S3) on the far "\n'
        '    "side of the desk and 苏小满 (S1) on the near side facing him. Her open, emptied locker is on the back wall; the "\n'
        '    "cardboard box with her belongings sits on the desk on her side. 张总 (S10) bursts in through the LEFT door and stops "\n'
        '    "at the desk. Second half — she takes the box and walks out through the LEFT door into the third-floor corridor, takes "',
        '"Fixed spatial set-up for this whole beat, never change it. First half — the property office, exactly as before: the "\n'
        '    "door on the LEFT of frame, the window and cabinets on the RIGHT, the desk across the middle, 苏小满 (S1) on the NEAR "\n'
        '    "side of the desk with her back to the LEFT door. 钱经理 (S3) starts this scene leaning in — and blocking — the LEFT "\n'
        '    "doorway, half in and half out of the corridor, and because he is blocking her exit he stays on the near side of the "\n'
        '    "desk between her and the door until 张总 (S10) arrives; after that he retreats to the far side of the desk for the "\n'
        '    "rest of the office beats. Her open, emptied locker is on the back wall; the cardboard box with her belongings sits "\n'
        '    "on the desk on her side. 张总 (S10) bursts in through the LEFT door and stops two paces inside it. Second half — she "\n'
        '    "takes the box and walks out through the LEFT door into the third-floor corridor, takes "',
    ),
    # --- C 车内：陆蔓从离开大楼起就在车上，不能"行进中上车"
    (
        '"seat with one empty seat between them. City lights slide across the windows. At the destination the camera is outside: "',
        '"seat with one empty seat between them, and she has been in the car since it left the tower. City lights slide across "\n'
        '    "the windows. At the destination the camera is outside: "',
    ),
]

# ================================================================ D 办公室站位
OFFICE = {
    "ep01_t18": [
        ("钱经理 (S3) has come round from the far side and now stands in the middle-left of the room facing the right of frame;",
         "钱经理 (S3) is stepping round the end of the desk onto the NEAR side and closing to one pace in front of 苏小满 (S1);"),
    ],
    "ep01_t19": [
        ("钱经理 (S3) stands an arm's length in front of 苏小满 (S1) in the middle of the room;",
         "钱经理 (S3) stands one pace in front of 苏小满 (S1) on the NEAR side of the desk;"),
    ],
    "ep01_t20": [
        ("钱经理 (S3) is an arm's length in front of her, middle-left of frame;",
         "钱经理 (S3) is one pace in front of her on the NEAR side of the desk;"),
        ("a man's head and shoulder enter frame from the LEFT and lean in over the paper",
         "a man from the doorway puts his head and shoulder into frame from the LEFT and leans in over the paper"),
    ],
    "ep01_t21": [
        ("钱经理 (S3) is an arm's length in front of her.",
         "钱经理 (S3) stands one pace in front of her on the NEAR side of the desk."),
        ("he looks down at the three objects on the desk, unimpressed",
         "he looks down at the two objects on the desk, unimpressed"),
    ],
    "ep01_t22": [
        ("钱经理 (S3) in front of her; the crowd packed into the LEFT doorway.",
         "钱经理 (S3) stands one pace in front of her on the NEAR side of the desk; the crowd packed into the LEFT doorway."),
    ],
    "ep01_t23": [
        ("钱经理 (S3) stands an arm's length in front of her; the doorway crowd is still frozen on the LEFT.",
         "钱经理 (S3) stands one pace in front of her on the NEAR side of the desk; the doorway crowd is still frozen on the LEFT."),
        ("[Shot 2] At 00:04.600, close two hands:",
         "[Shot 2] At 00:03.200, close two hands:"),
        ("[Shot 3] At 00:06.600, close on his hands as he flips the card over, then over again,",
         "[Shot 3] At 00:05.400, close on his hands as he flips the card over, then over again,"),
        ("[Shot 4] At 00:08.800, extreme close-up on the back of the card and a single line of tiny stamped characters along its lower edge. Neither of them speaks now.",
         "[Shot 4] At 00:07.000, extreme close-up on the back of the card and a single line of tiny stamped characters along its "
         "lower edge. Neither of them speaks.\n"
         "[Shot 5] At 00:08.400, wide: 钱经理 (S3) turns on his heel and walks back round the end of the desk to his place on the "
         "FAR side, back to the window, the card held flat in one hand; 苏小满 (S1) stays where she is and watches him go; "
         "nobody else speaks."),
    ],
    "ep01_t24": [
        ("钱经理 (S3) holds the black card in both hands, tilted to the window light, on the middle-left of frame;",
         "钱经理 (S3) has just reached his place on the FAR side of the desk, back to the window, holding the black card in both hands and tilting it to the light;"),
    ],
    "ep01_t25": [
        ("钱经理 (S3) stands mid-room holding the card;",
         "钱经理 (S3) stands on the FAR side of the desk, back to the window, holding the card;"),
    ],
    "ep01_t26": [
        ("钱经理 (S3) mid-room with the card in his hand, 苏小满 (S1) on the near side of the desk facing him,",
         "钱经理 (S3) stands on the FAR side of the desk with the card in his hand, 苏小满 (S1) on the near side of the desk facing him,"),
        ("reverse onto 苏小满 (S1) between the desk and the card he is holding up;",
         "reverse onto 苏小满 (S1) on the near side of the desk with the card held up beyond it;"),
        ("hold on the card held up in the middle of the room, catching the blind-light.",
         "hold on the card held up on the FAR side of the desk, catching the blind-light."),
    ],
    "ep01_t27": [
        ("钱经理 (S3) holds the card up at eye level in the middle of the room facing the right of frame;",
         "钱经理 (S3) holds the card up at eye level on the FAR side of the desk, facing her across it;"),
        ("two-shot across the narrow gap with the raised card between them,",
         "two-shot across the desk with the raised card between them,"),
    ],
    "ep01_t28": [
        ("facing 钱经理 (S3), who holds the card up in the middle-left of frame; the crowd fills the LEFT doorway.",
         "facing 钱经理 (S3), who holds the card up on the FAR side of the desk; the crowd fills the LEFT doorway."),
    ],
    "ep01_t29": [
        ("facing 钱经理 (S3), who stands in the middle-left of frame;",
         "facing 钱经理 (S3), who stands on the FAR side of the desk, back to the window;"),
    ],
    "ep01_t30": [
        ("钱经理 (S3) mid-room holding the card low; the crowd at the LEFT doorway.",
         "钱经理 (S3) on the FAR side of the desk holding the card low; the crowd at the LEFT doorway."),
    ],
    "ep01_t31": [
        ("facing 钱经理 (S3) in the middle-left of frame; the keys, pen and paper form still on the desk.",
         "facing 钱经理 (S3) on the FAR side of the desk; the keys and the pen still on the desk, the folded paper form closed in her trouser pocket."),
        ("insert: the desk surface — keys, pen and folded form in a row, and the black card lying flat beside them where he put it down.",
         "insert: the desk surface — the keys and the pen in a row, and the black card lying flat beside them where he put it down."),
    ],
    "ep01_t32": [
        ("钱经理 (S3) stands mid-room with the card in his hand;",
         "钱经理 (S3) stands on the FAR side of the desk with the card in his hand;"),
    ],
    "ep01_t33": [
        ("钱经理 (S3) stands beside the desk where the card lies flat;",
         "钱经理 (S3) stands at the FAR side of the desk where the card lies flat;"),
    ],
    "ep01_t34": [
        ("钱经理 (S3) stands beside the desk with the card flat on it;",
         "钱经理 (S3) stands at the FAR side of the desk with the card flat on it in front of him;"),
    ],
    "ep01_t35": [
        ("钱经理 (S3) in front of her holding the card up; the crowd at the LEFT doorway.",
         "钱经理 (S3) on the FAR side of the desk holding the card up; the crowd at the LEFT doorway."),
    ],
    "ep01_t37": [
        ("钱经理 (S3) has stepped half a pace closer to the desk, facing 苏小满 (S1) across it;",
         "钱经理 (S3) stands at the FAR side of the desk, leaned half a pace in over it, facing 苏小满 (S1) across it;"),
    ],
    # --- E t67 跨镜头断句合并
    "ep01_t67": [
        ("[Shot 1] Medium: 小罗 (S7) holds the card up at chest height, addressing nobody in particular, in the same quiet courteous Mandarin, evenly: [Chinese] 这张卡，三天前，\n"
         "[Shot 2] At 00:04.000, closer on 小罗 (S7) as he goes on, still perfectly level: [Chinese] 是我们留给苏小姐的。\n"
         "[Shot 3] At 00:07.400, 小罗 (S7) turns a quarter step and runs his eyes slowly around the room — the manager, the doorway crowd, the director — before he adds it, still perfectly polite: [Chinese] 让各位，误会了。",
         "[Shot 1] Medium: 小罗 (S7) holds the card up at chest height, addressing nobody in particular, in the same quiet courteous Mandarin, evenly, one whole sentence in one breath: [Chinese] 这张卡，三天前，是我们留给苏小姐的。\n"
         "[Shot 2] At 00:06.000, closer on 小罗 (S7) as he goes on, still perfectly level: [Chinese] 让各位，误会了。\n"
         "[Shot 3] At 00:08.400, 小罗 (S7) turns a quarter step and runs his eyes slowly around the room — the manager, the doorway crowd, the director — without saying anything more."),
    ],
    # --- F 补 (S1)
    "ep01_t106": [
        ("[Shot 4] At 00:07.200, she straightens, hands the form back to 钱经理 (S3) with both hands,",
         "[Shot 4] At 00:07.200, 苏小满 (S1) straightens, hands the form back to 钱经理 (S3) with both hands,"),
    ],
    "ep01_t115": [
        ("[Shot 1] Medium: she does not get in. She turns her head toward 小罗 (S7) and asks it in her low even Mandarin,",
         "[Shot 1] Medium: 苏小满 (S1) does not get in. She turns her head toward 小罗 (S7) and asks it in her low even Mandarin,"),
    ],
    "ep01_t129": [
        ("[Shot 2] At 00:04.000, close on her face: she does not look at him.",
         "[Shot 2] At 00:04.000, close on 苏小满's (S1) face: she does not look at him."),
    ],
    # --- G t113→t114 去重
    "ep01_t114": [
        ("Entry state, taken from the reference images: outside, the bright paved forecourt with the row of black sedans along the kerb, the tower's entrance behind; inside, the lobby looking back toward the lift bank.",
         "Entry state, taken from the reference images: outside, the bright paved forecourt with the row of black sedans along the kerb and the tower's entrance behind, 苏小满 (S1) already a few paces out on the paving with her cardboard box; inside, the lobby looking back toward the lift bank."),
        ("At 00:02.800, outside: 苏小满 (S1) walks out through the glass doors onto the forecourt with the cardboard box in her arms, and stops.",
         "At 00:02.800, outside and already through: 苏小满 (S1) takes the last few strides clear of the glass doors and out onto the open forecourt with the cardboard box in her arms, and stops."),
    ],
    # --- H 陆蔓上车时机
    "ep01_t117": [
        ("At 00:09.400, the driver closes the rear door behind her with one soft push and the car pulls away from the kerb into the blue dusk with its tail lights coming on;",
         "At 00:09.400, the driver closes the rear door behind her with one soft push; 陆蔓 (S8), a composed woman of fifty in a deep-green jacquard silk qipao, is already seated on the LEFT rear seat with one empty place between them and looks out of the far window without turning her head; the car pulls away from the kerb into the blue dusk with its tail lights coming on;"),
    ],
    "ep01_t118": [
        ("苏小满 (S1) sits in the RIGHT rear seat with the cardboard box upright on her knees; the LEFT rear seat is still empty. 陆蔓 (S8) is a composed woman of fifty in a deep-green jacquard silk qipao.",
         "苏小满 (S1) sits in the RIGHT rear seat with the cardboard box upright on her knees; 陆蔓 (S8) sits in the LEFT rear seat, one empty place between them, and has been in the car since it left the tower. 陆蔓 (S8) is a composed woman of fifty in a deep-green jacquard silk qipao."),
        ("[Shot 1] Wide from the front: the car running through the city at night in warm amber light, the city sliding past the tinted glass, her cardboard box standing on her knees, her hands flat on top of it, the seat beside her empty.",
         "[Shot 1] Wide from the front: the car running through the city at night in warm amber light, the city sliding past the tinted glass, her cardboard box standing on her knees, her hands flat on top of it, the seat beside her occupied by a still, composed woman who has not looked at her once."),
        ("[Shot 2] At 00:03.400, the LEFT rear door opens and 陆蔓 (S8) gets in and settles onto the LEFT rear seat, pulling the door shut; one empty place between them. 苏小满 (S1) turns her head just enough to look at her without turning her shoulders.",
         "[Shot 2] At 00:03.400, 陆蔓 (S8) shifts slightly on the LEFT rear seat and settles back against the leather, one empty place between them; 苏小满 (S1) turns her head just enough to look at her without turning her shoulders."),
    ],
    # --- I t126→t127 过渡
    "ep01_t126": [
        ("[Shot 4] At 00:08.600, the car stops. Outside, a driver's door opens and footsteps come round the back. Nobody speaks in this beat.",
         "[Shot 4] At 00:07.600, from outside: the car stops at the foot of the gate; 小罗 (S7) and two of the suited men are already standing in the alley ahead of it, waiting; a driver's door opens and footsteps come round the back.\n"
         "[Shot 5] At 00:09.000, the rear door is opened for her; 苏小满 (S1) ducks her head and steps out onto the stone paving with the cardboard box in her arms, while 陆蔓 (S8) stays exactly where she is on the LEFT rear seat and does not get out. Nobody speaks in this beat."),
    ],
    "ep01_t127": [
        ("Entry state, re-anchored to the reference image: outside at night, 苏小满 (S1) stands on the stone paving in front of the tall vermilion lacquered double gate at the end of the alley, the cardboard box in her arms, one step OUTSIDE the stone threshold; 小罗 (S7) stands half a step behind her LEFT shoulder; the gate is shut except for a narrow gap of warm light.",
         "Entry state, re-anchored to the reference image: outside at night, 苏小满 (S1) has just got out of the car and stands on the stone paving in front of the tall vermilion lacquered double gate at the end of the alley, the cardboard box in her arms, one step OUTSIDE the stone threshold; 小罗 (S7) stands half a step behind her LEFT shoulder; the black sedan stands behind them in the alley with 陆蔓 (S8) still inside it; the gate is shut except for a narrow gap of warm light."),
    ],
}


def main():
    # 锚点（storyboard_render.py）
    if not os.path.exists(RENDER):
        print("!! 找不到", RENDER)
        return 2
    patch_text_file(RENDER, ANCHOR_PAIRS)
    # beats
    patch_beats(OFFICE)

    if MISS:
        print("== 未命中 %d 条 ==" % len(MISS))
        for m in MISS:
            print("  " + m)
        return 1
    print("全部补丁命中并写入。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
