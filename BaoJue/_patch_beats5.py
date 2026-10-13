# -*- coding: utf-8 -*-
r"""
第五轮补丁：第三轮子代理审核（A/B/C 三份）的整改。

审核结论：_review_A.md(14) / _review_B.md(17) / _review_C.md(5)
本脚本把可执行的都落进 beats。分类：
  S. 声景里"silence / silent room"这类**否定声音写法**（会把人声压掉）→ 换成正向写法
  P. 道具连续性（圆珠笔/黑卡/对折纸单的出现时机与锚点不符）
  B. 人物调度与 ANCHOR_12 / ANCHOR_14 矛盾（钱经理越桌、周总监左右肩不一致、t74 自相矛盾）
  G. 场次切换 Entry 缺人物初始位置（t82 / t108）
  V. 竖屏构图（t109 八人横向散开）
  T. 跨镜头台词音频连续性说明（t117）
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BEATS = os.path.join(BASE, "ep001_beats")
MISS = []


def patch(pairs_by_seg, global_pairs):
    """global_pairs 对所有段的 shots/summary/soundscape/music 生效（允许 0 次命中）。"""
    for f in sorted(os.listdir(BEATS)):
        if not f.endswith(".json"):
            continue
        p = os.path.join(BEATS, f)
        data = json.load(io.open(p, encoding="utf-8"))
        touched = False

        for seg in data:
            for old, new in global_pairs:
                for key in ("shots", "summary", "soundscape", "music"):
                    v = seg.get(key)
                    if isinstance(v, str) and old in v:
                        seg[key] = v.replace(old, new)
                        touched = True
            for old, new, *keys in pairs_by_seg.get(seg["id"], []):
                ks = keys[0] if keys else ("shots",)
                for key in ks:
                    v = seg.get(key)
                    if not isinstance(v, str):
                        continue
                    if old not in v:
                        MISS.append("%s %s.%s 未命中: %s" % (f, seg["id"], key, old[:65]))
                        continue
                    if v.count(old) > 1:
                        MISS.append("%s %s.%s 命中多次: %s" % (f, seg["id"], key, old[:45]))
                    seg[key] = v.replace(old, new)
                    touched = True
        if touched:
            io.open(p, "w", encoding="utf-8").write(
                json.dumps(data, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- S 声景去 silence
GLOBAL = [
    ("Tense near-silence,", "Tense quiet,"),
    ("then a long silence;", "then a long held breath;"),
    ("in the silence.", "in the still room."),
    ("in the silence,", "in the still room,"),
    ("the crowd's held silence.", "the crowd's held breath."),
    ("cutting into the silence,", "cutting in,"),
    ("total silence in the doorway,", "the doorway holding its breath,"),
    ("utter silence in the doorway,", "the doorway holding its breath,"),
    ("a beat of silence,", "a held beat,"),
    ("letting the silence do the work", "letting the pause do the work"),
    ("then a silence with real weight in it,", "then a stillness with real weight in it,"),
    ("then a silence with weight in it;", "then a stillness with weight in it;"),
    ("complete silence around it,", "the room held still around it,"),
    ("A three-second silence,", "A three-second pause,"),
    ("the room's total silence around her.", "the room held still around her."),
    ("one second of line silence,", "one second of open line hiss,"),
    ("absolute silence.", "the whole room holding its breath."),
    ("and a silence in which nobody speaks.", "and the room going still."),
    ("very loud in the silence,", "very loud in the still room,"),
    ("total silence around it.", "the room held still."),
    ("then held silence.", "then a held chord."),
    ("its tail ringing on into silence.", "its tail ringing on into the dark."),
    # --- 房间级 silent → 正向写法
    ("in a silent room", "in a still room"),
    ("in a dead-silent room", "in a dead-still room"),
    ("the silent stone lobby", "the still stone lobby"),
    ("wide of the silent room.", "wide of the still room."),
    ("the room completely silent.", "the whole room held still."),
    ("the room goes silent.", "the room goes still."),
    ("the whole lobby going silent around them.", "the whole lobby going still around them."),
]

PATCHES = {
    # ------------------------------------------------------------ P / B / 空间
    "ep01_t08": [
        ("and glares at her in silence.", "and glares at her, lips pressed shut."),
    ],
    "ep01_t14": [
        ("the desk lamp jumps and the pen rolls.",
         "the desk lamp jumps and the white enamel mug rocks on the bare desktop."),
        ("papers settling, the buzz of the ceiling fluorescent panels",
         "the blind slats settling, the buzz of the ceiling fluorescent panels"),
    ],
    "ep01_t20": [
        ("the doorway crowd on the LEFT is watching in silence.",
         "the doorway crowd on the LEFT is watching, mouths shut."),
    ],
    "ep01_t31": [
        ("insert: the desk surface — the keys and the pen in a row, and the black card lying flat beside them where he put it down.",
         "insert: the desk surface — the keys and the pen in a row on the bare wood; the black card is still in his hand."),
    ],
    "ep01_t35": [
        ("everyone waiting, and no sound at all.",
         "everyone waiting, the whole room rigid."),
    ],
    "ep01_t42": [
        ("钱经理 (S3) crosses the room in three quick steps and stops at 周总监's (S6) right shoulder, bending his head and shoulders in toward him with an ingratiating smile, both hands coming up.",
         "钱经理 (S3) comes out from behind the desk, crosses the few steps to 周总监 (S6) along the end of the desk, and stops at his LEFT shoulder, bending his head and shoulders in toward him with an ingratiating smile, both hands coming up."),
    ],
    "ep01_t43": [
        ("钱经理 (S3) stands at 周总监's (S6) right shoulder holding the card up;",
         "钱经理 (S3) stands at 周总监's (S6) LEFT shoulder holding the card up;"),
    ],
    "ep01_t44": [
        ("钱经理 (S3) is behind and to the director's left, silent;",
         "钱经理 (S3) is behind and to the director's left, saying nothing;"),
    ],
    "ep01_t49": [
        ("the black card lying perfectly square on the dark wood, the keys, pen and folded form beside it.",
         "the black card lying perfectly square on the dark wood, the keys and the pen beside it."),
        ("She is silent, and so is everyone else.",
         "She says nothing, and neither does anyone else."),
    ],
    "ep01_t68": [
        ("钱经理 (S3) hurries two steps around the desk toward 小罗 (S7), bending at the waist as he goes, hands rubbing together.",
         "钱经理 (S3) stays on the far side of the desk and bends in toward 小罗 (S7) across it, hands rubbing together."),
    ],
    "ep01_t73": [
        ("the card, the keys, the pen and the folded paper form lie on the dark desktop in a row;",
         "the black card lies on the dark desktop and the keys and the pen lie beside it;"),
        ("[Shot 3] At 00:05.600, her fingers stop on the folded paper form and rest on it for a beat without lifting it.",
         "[Shot 3] At 00:05.600, she takes the folded paper form out of the trouser pocket where it has been since she snatched it back, and holds it flat in her palm for a beat without unfolding it."),
        ("[Shot 4] At 00:07.800, she picks the form up last, folds it twice more with careful fingers and puts it away deep, then stands.",
         "[Shot 4] At 00:07.800, she folds it once more with careful fingers and puts it away again, deeper this time, then stands."),
    ],
    "ep01_t74": [
        ("钱经理 (S3) is on the far side of the desk, a step behind her;",
         "钱经理 (S3) is still on the far side of the desk, half turned to follow her with his eyes;"),
        ("[Shot 1] Medium: 钱经理 (S3) hurries two steps after her with his shoulders rounded and his hands up,",
         "[Shot 1] Medium: 钱经理 (S3) leans out over the far side of the desk after her, shoulders rounded and both hands up,"),
        ("[Shot 4] At 00:09.800, hold on 钱经理 (S3) left standing mid-room with his hands still up",
         "[Shot 4] At 00:09.800, hold on 钱经理 (S3) left leaning over the desk with his hands still up"),
    ],
    # ------------------------------------------------------------ G 场次切换 Entry
    "ep01_t82": [
        ("blue evening light from the tall window at the far end of the corridor, and warm tungsten spill from the ward doorway.",
         "blue evening light from the tall window at the far end of the corridor, and warm tungsten spill from the ward doorway. 苏小满 (S1) stands in the corridor just clear of the ward door on the RIGHT, facing it, and 医生 (S11) is already stepping out through it toward her with a printed form in his hand."),
    ],
    "ep01_t108": [
        ("Entry state, new location, taken from the reference images: outside, the bright paved forecourt in front of 景宸大厦 with its row of black sedans along the kerb; inside, the ground-floor lobby with the reception counter on the RIGHT and a bank of lift doors ahead.",
         "Entry state, new location, taken from the reference images: 苏小满 (S1) is inside the lift coming down with her cardboard box; 小罗 (S7) and a file of eight suited men are already crossing the ground-floor lobby from the glass doors on the LEFT of frame toward the lift bank; the reception counter is on the RIGHT; outside, the bright paved forecourt in front of 景宸大厦 with its row of black sedans along the kerb."),
    ],
    # ------------------------------------------------------------ V 竖屏构图
    "ep01_t109": [
        ("the men behind him stop in the same instant and spread into a loose line.",
         "the men behind him stop in the same instant and close up one behind another in file at his back, stacked in depth."),
    ],
    # ------------------------------------------------------------ C 空间
    "ep01_t106": [
        ("[Shot 1] Medium: 钱经理 (S3) picks the form up off the desk, carries it round the desk in both hands held flat and level — the way a waiter carries a tray — and holds it out to her.",
         "[Shot 1] Medium: 钱经理 (S3) stays on the far side behind the desk; he picks the form up and holds it out flat in both hands, level as a tray, across the desk toward her, and 苏小满 (S1) walks the two steps in from the doorway to the desk edge to take it."),
        ("a ballpoint scrawling on paper, then one flat sentence in a silent room.",
         "a ballpoint scrawling on paper, then one flat sentence in a still room."),
    ],
    "ep01_t114": [
        ("[Shot 1] Close, back inside the lobby: 小唐 (S4) is pressed into a service doorway at the far end of the hall, head buried, shoulders hunched, peering out from behind the frame.",
         "[Shot 1] Close, cutting back upstairs to the third floor: 小唐 (S4) is pressed into the office doorframe in the corridor, head buried, shoulders hunched, peering out past the jamb after her."),
        ("inside, the lobby looking back toward the lift bank.",
         "then the sequence cuts back inside — first to the third-floor corridor outside the office, then to the ground-floor lobby looking back toward the lift bank."),
    ],
    # ------------------------------------------------------------ T 跨镜头台词
    "ep01_t117": [
        ("close on 小罗 (S7) as he finishes what he started, still quietly and only for her:",
         "close on 小罗 (S7) as he finishes what he started, still quietly and only for her, in exactly the same voice and at the same pace as the line before:"),
    ],
}


def main():
    patch(PATCHES, GLOBAL)

    # 复查：silence 必须清零；房间级 silent 也应清零
    import glob
    import re
    left = []
    for f in sorted(glob.glob(os.path.join(BEATS, "*.json"))):
        d = json.load(io.open(f, encoding="utf-8"))
        for b in d:
            for key in ("shots", "summary", "soundscape", "music"):
                s = b.get(key) or ""
                for m in re.finditer(r"[^.]*\bsilence\b[^.]*\.", s):
                    left.append("%s %s %s" % (b["id"], key, m.group(0).strip()[:80]))
    if left:
        print("== 仍残留 silence %d 处 ==" % len(left))
        for x in left:
            print("  " + x)

    if MISS:
        print("== 未命中 %d 条 ==" % len(MISS))
        for m in MISS:
            print("  " + m)
        return 1
    print("全部补丁命中并写入。" + ("(残留 silence %d)" % len(left) if left else "(silence 已清零)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
