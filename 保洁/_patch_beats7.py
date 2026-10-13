# -*- coding: utf-8 -*-
"""
第七轮补丁：整改第四轮 H3 复核（_verify4_A.md / _verify4_B.md）列出的全部问题。

A 组（1-2 场办公室，seg14–81）：
  seg42/43  钱经理不得二次离桌（ANCHOR_12 只允许「掏兜」一次离桌）
  seg20     对折纸单从不摊平、从不留在桌面
  seg41→42  黑卡从桌面到手要有交代
  seg14     删掉凭空出现的台灯/搪瓷缸，与「开场空桌」对齐
  seg65/66  钱经理不迈离远侧
  seg76     他先守在远侧看苏小满走，不许在房间中部
  seg17     横向双人改纵深前后排 + 钱经理钉回远侧
  seg63/70  "fan out into a line" 改纵深错列
  seg45/48/49/53/55/57  Entry 补钱经理，防 H3 把他抹掉
  seg81     删掉凭空出现的 pen tray

B 组（1-4b / 1-5，seg105–129）：
  seg98/99  钱经理退到桌子远侧要一步到位
  seg117    car_interior 是夜间图，降为「只做位置/道具参考，不做打光参考」
  seg108    Entry 与首镜时序对齐
  seg109/112/116  跨镜头同一说话人补 same voice and pace
  seg114/115   删掉没有对应画面的 lobby_1f 参考图
  seg119/121/126/128  声景里的 muted / 逼近无声写法改成正向写法
  seg57/63/70  同类声景写法一并收紧

用法： python _patch_beats7.py
幂等：重复运行第二次会报 MISS（因为已改过），这是正常的，不是错误。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
BEATS = os.path.join(BASE, "ep001_beats")

# ---------------------------------------------------------------- 1) 文本替换
# 结构： (seg_id, 字段, 旧原文, 新原文, 备注)
TEXT_EDITS = [
    # ---- A1/A2 钱经理二次离桌（高危） ----
    ("ep01_t42", "shots",
     "[Shot 1] Medium: 钱经理 (S3) comes out from behind the desk, crosses the few steps to 周总监 (S6) along the end of the desk, and stops at his LEFT shoulder, bending his head and shoulders in toward him with an ingratiating smile, both hands coming up.",
     "[Shot 1] Medium: 钱经理 (S3) does not leave the far side of the desk — he stays planted behind it, one hand flat on the wood while the other picks the black card up off the desktop, then turns his shoulders toward the door, ducks his head at 周总监 (S6) in an ingratiating bow and waves him in; 周总监 (S6) begins walking in toward the desk.",
     "A1 钱经理留在远侧汇报"),
    ("ep01_t42", "shots",
     "[Shot 3] At 00:05.400, 钱经理 (S3) lifts the black card up between them and taps it twice with a finger:",
     "[Shot 3] At 00:05.400, 钱经理 (S3) holds the black card up over the desk toward 周总监 (S6) and taps it twice with a finger:",
     "A1 卡在两人之间→朝周总监方向"),
    ("ep01_t43", "shots",
     "Entry state, re-anchored to the reference image: 钱经理 (S3) stands at 周总监's (S6) LEFT shoulder holding the card up; 苏小满 (S1) is on the near side of the desk with her back to the door; the crowd is flat against the doorway walls.",
     "Entry state, re-anchored to the reference image: 钱经理 (S3) stands on the FAR side of the desk holding the card up; 苏小满 (S1) is on the near side of the desk with her back to the door; 周总监 (S6) is just reaching the desk; the crowd is flat against the doorway walls.",
     "A2 Entry 钱经理回远侧"),
    ("ep01_t43", "shots",
     "[Shot 1] Medium: 周总监 (S6) walks past the manager without answering him and crosses to the desk, taking the card out of the other man's hand as he goes; 钱经理 (S3) trails a step behind him and stops in his shadow.",
     "[Shot 1] Medium: 周总监 (S6) crosses to the desk without answering the manager, taking the card out of 钱经理's (S3) hand over the desktop as he goes; 钱经理 (S3) stays where he is on the FAR side of the desk and does not follow.",
     "A2 周总监自己走过来取卡"),

    # ---- A3 纸单从不摊平 ----
    ("ep01_t20", "shots",
     "[Shot 2] At 00:03.000, extreme close-up on her hand taking out a single folded paper form and laying it flat; the fold opens under her palm.",
     "[Shot 2] At 00:03.000, extreme close-up on her hand drawing a single folded paper form halfway out of her pocket and holding it cupped in her palm, still folded.",
     "A3 纸单保持对折、不离手"),
    ("ep01_t20", "shots",
     "[Shot 3] At 00:05.600, a man from the doorway puts his head and shoulder into frame from the LEFT and leans in over the paper; 苏小满 (S1) claps her hand flat over the form and pulls it back into her palm in one quick movement, and the man straightens up again.",
     "[Shot 3] At 00:05.600, a man from the doorway puts his head and shoulder into frame from the LEFT and leans in toward her hand; 苏小满 (S1) closes her hand over the folded form and shoves it straight back down into her pocket in one quick movement, and the man straightens up again.",
     "A3 纸单塞回兜里"),

    # ---- A5 开场空桌：删台灯/搪瓷缸 ----
    ("ep01_t14", "shots",
     "the desk lamp jumps and the white enamel mug rocks on the bare desktop.",
     "his open palm cracks flat against the bare desktop and the venetian blinds tick against the glass.",
     "A5 桌面与开场空桌对齐"),

    # ---- A6 钱经理不迈离远侧 ----
    ("ep01_t65", "shots",
     "[Shot 2] At 00:06.200, wide: 钱经理 (S3) gets the rest of the way out of the chair so fast that its metal legs shriek across the tile; he takes one step toward 小罗 (S7) with both hands coming up and his mouth already open.",
     "[Shot 2] At 00:06.200, wide: 钱经理 (S3) gets the rest of the way out of the chair so fast that its metal legs shriek across the tile, but he stops dead at the far side of the desk and does not come round it, both hands coming up and his mouth already open.",
     "A6 起立但不离远侧"),
    ("ep01_t66", "shots",
     "钱经理 (S3) has stopped beside the chair;",
     "钱经理 (S3) is still standing at the far side of the desk beside his chair;",
     "A6 Entry 顺接"),

    # ---- A7 seg76 先守在远侧 ----
    ("ep01_t76", "shots",
     "钱经理 (S3) is left standing in the middle-left of the room where 苏小满 (S1) walked past him, a few steps away from the desk; the room is emptying, the crowd gone from the doorway.",
     "钱经理 (S3) is still at the far side of the desk where he leaned to watch 苏小满 (S1) go, a few steps from the desk; the room is emptying, the crowd gone from the doorway.",
     "A7 他先守远侧"),

    # ---- A8 seg17 纵深双人 + 钱经理钉回远侧 ----
    ("ep01_t17", "shots",
     "[Shot 3] At 00:08.600, wide: the two women at either end of the room's axis with the desk between them, 钱经理 (S3) motionless in the middle background watching them like a spectator, arms folded.",
     "[Shot 3] At 00:08.600, wide: the two women staged one behind the other along the room's depth axis — 小唐 (S4) nearer the door, 苏小满 (S1) nearer the desk — with 钱经理 (S3) motionless behind the desk, back to the window, watching them like a spectator, arms folded.",
     "A8 纵深前后排"),

    # ---- A10 竖屏：不许一字排开 ----
    ("ep01_t63", "shots",
     "four men in dark tailored suits follow him and fan out into a loose line against the LEFT wall.",
     "four men in dark tailored suits follow him and take up a staggered line along the LEFT wall, one behind another, receding into the depth of frame.",
     "A10 纵深错列"),
    ("ep01_t70", "shots",
     "four men in dark suits standing in a line along the LEFT wall,",
     "four men in dark suits standing one behind another along the LEFT wall, receding down the room,",
     "A10 纵深错列"),

    # ---- A11 Entry 补钱经理 ----
    ("ep01_t45", "shots",
     "苏小满 (S1) on the near side of the desk with her back to the door; 周总监 (S6) on the far side with one hand on the desk; the black card between them;",
     "苏小满 (S1) on the near side of the desk with her back to the door; 周总监 (S6) on the far side with one hand on the desk; 钱经理 (S3) further along the far side of the desk, back to the window, saying nothing; the black card between 苏小满 and 周总监;",
     "A11 Entry 补钱经理"),
    ("ep01_t48", "shots",
     "周总监 (S6) stands on the far side of the desk, 苏小满 (S1) on the near side with her back to the door, the card between them;",
     "周总监 (S6) stands on the far side of the desk, 苏小满 (S1) on the near side with her back to the door, 钱经理 (S3) further along the far side of the desk, back to the window, saying nothing, the card between 苏小满 and 周总监;",
     "A11 Entry 补钱经理"),
    ("ep01_t49", "shots",
     "周总监 (S6) on the far side of the desk; 苏小满 (S1) on the near side; the card flat on the desk between them;",
     "周总监 (S6) on the far side of the desk; 苏小满 (S1) on the near side; 钱经理 (S3) further along the far side of the desk, back to the window, saying nothing; the card flat on the desk between 苏小满 and 周总监;",
     "A11 Entry 补钱经理"),
    ("ep01_t53", "shots",
     "between 苏小满 (S1) on the near side and 周总监 (S6) on the far side; the crowd at the LEFT doorway.",
     "between 苏小满 (S1) on the near side and 周总监 (S6) on the far side; 钱经理 (S3) further along the far side of the desk, back to the window, saying nothing; the crowd at the LEFT doorway.",
     "A11 Entry 补钱经理"),
    ("ep01_t55", "shots",
     "苏小满 (S1) holds the black card on the near side; 周总监 (S6) on the far side; the crowd at the LEFT doorway.",
     "苏小满 (S1) holds the black card on the near side; 周总监 (S6) on the far side; 钱经理 (S3) further along the far side of the desk, back to the window, saying nothing; the crowd at the LEFT doorway.",
     "A11 Entry 补钱经理"),
    ("ep01_t57", "shots",
     "苏小满 (S1) standing over it on the near side; 周总监 (S6) on the far side; the crowd at the LEFT doorway.",
     "苏小满 (S1) standing over it on the near side; 周总监 (S6) on the far side; 钱经理 (S3) further along the far side of the desk, back to the window, saying nothing; the crowd at the LEFT doorway.",
     "A11 Entry 补钱经理"),

    # ---- A12 删掉凭空出现的 pen tray ----
    ("ep01_t81", "shots",
     "[Shot 3] At 00:05.800, insert on the desk: the scuff marks in the dust, the pen tray, the empty space where the black card lay.",
     "[Shot 3] At 00:05.800, insert on the desk: the scuff marks in the dust, the keys and the ballpoint pen, and the empty space where the black card lay.",
     "A12 复用已有道具"),

    # ===== B 组 =====
    ("ep01_t98", "shots",
     "钱经理 (S3) has backed half a step away toward the far side of the desk;",
     "钱经理 (S3) has retreated to the far side of the desk and stands behind it;",
     "B1 退位一步到位"),
    ("ep01_t99", "shots",
     "钱经理 (S3) stands half a step back from the desk;",
     "钱经理 (S3) stands on the FAR side of the desk, back to the window;",
     "B1 承接上一段"),
    ("ep01_t108", "shots",
     "小罗 (S7) and a file of eight suited men are already crossing the ground-floor lobby from the glass doors on the LEFT of frame toward the lift bank;",
     "小罗 (S7) and a file of eight suited men are just getting out of the cars at the kerb outside and will come in across the ground-floor lobby from the glass doors on the LEFT of frame toward the lift bank;",
     "B3 Entry 与首镜时序对齐"),
    ("ep01_t109", "shots",
     "[Shot 3] At 00:05.600, he adds the second half, evenly, watching her face:",
     "[Shot 3] At 00:05.600, he adds the second half in the same voice and at the same pace, evenly, watching her face:",
     "B7 跨镜头同说话人"),
    ("ep01_t112", "shots",
     "[Shot 2] At 00:05.000, 苏小满 (S1) goes on without pausing, still perfectly level:",
     "[Shot 2] At 00:05.000, 苏小满 (S1) goes on in the same voice and at the same pace, without pausing, still perfectly level:",
     "B7 跨镜头同说话人"),
    ("ep01_t116", "shots",
     "[Shot 2] At 00:04.000, 小罗 (S7) goes on, still pitched only for her:",
     "[Shot 2] At 00:04.000, 小罗 (S7) goes on in the same voice and at the same pace, still pitched only for her:",
     "B7 跨镜头同说话人"),
    ("ep01_t126", "shots",
     "the bright city noise drops away to nothing on the cut.",
     "the main-road hum thins out behind them on the cut.",
     "B5 声景正向写法"),

    # ===== 声景（soundscape）正向化 =====
    ("ep01_t57", "soundscape",
     "then nothing but room tone.",
     "then only room tone and a distant lift bell.",
     "声景正向写法"),
    ("ep01_t63", "soundscape",
     "then absolute quiet.",
     "then only leather soles and the crowd breathing.",
     "声景正向写法"),
    ("ep01_t70", "soundscape",
     "One quiet courteous question in a room with no other sound in it but the air conditioning and the clock.",
     "One quiet courteous question, the air conditioning, the clock.",
     "声景正向写法"),
    ("ep01_t111", "soundscape",
     "then a lobby in which nothing at all is making a sound except the air handling.",
     "then only the air handling, and the whole lobby holding still around them.",
     "B5 声景正向写法"),
    ("ep01_t119", "soundscape",
     "city traffic muted through the glass",
     "low city traffic through the glass",
     "B4 去掉 muted"),
    ("ep01_t121", "soundscape",
     "tyre noise and muted street traffic.",
     "tyre noise and low street traffic.",
     "B4 去掉 muted"),
    ("ep01_t126", "soundscape",
     "the main road noise cut off behind them",
     "the main road hum thinning out behind them",
     "B5 声景正向写法"),
    ("ep01_t128", "soundscape",
     "Almost nothing but damp night air, the lantern's paper creaking, a distant car, one long breath close to the mic.",
     "Damp night air, the lantern's paper creaking, a distant car, one long breath close to the mic.",
     "B5 声景正向写法"),

    # 第七轮补丁跑完后，新加的「声景也要扫」这条闸又抓出 3 处以前全漏网的。
    # 代价：t01 属于第 1 个链组，改了它整组（t01-t03）会重跑，约 30 分钟。
    # 值得——"muted 背景声" 与 "把声音静掉" 在 H3 眼里容易被混为一谈，宁可换词。
    ("ep01_t01", "soundscape",
     "muted ballroom chatter behind the red doors.",
     "faint ballroom chatter behind the red doors.",
     "声景去掉 muted"),
    ("ep01_t81", "soundscape",
     "Almost nothing: the ceiling lights, the clock, one hard swallow, a car passing in the street below, then the corridor's open quiet.",
     "The ceiling lights, the clock, one hard swallow, a car passing in the street below, the corridor's open quiet.",
     "声景去掉「几乎没有声音」写法"),
    ("ep01_t82", "soundscape",
     "low muted voices from the ward.",
     "low indistinct voices from the ward.",
     "声景去掉 muted"),
]

# ---------------------------------------------------------------- 2) 参考图改动
REPLACE_REF = {
    "ep01_t114": ("lobby_1f", "corridor_mid"),   # B6 删镜头没删干净的参考图
}
DROP_REF = {
    "ep01_t115": "lobby_1f",                     # B6 纯楼外戏，不要大堂图
}
# B2 car_interior 是夜间图，seg117 是傍晚日戏：降为只做位置/道具参考
REF_NOTES = {
    "ep01_t117": {
        "car_interior":
            "the rear cabin of a black executive sedan, seen from the front seats looking back — a wide pale-grey "
            "leather rear bench, a central armrest, chrome door handles, amber courtesy lamps along the roof lining, "
            "tinted windows. Use as the location and prop reference only, NOT for lighting; the light through the open "
            "rear door is bright late-afternoon daylight. The car in it is empty."
    },
}


def main():
    files = sorted([f for f in os.listdir(BEATS) if f.endswith(".json")])
    data = {}
    for f in files:
        data[f] = json.load(io.open(os.path.join(BEATS, f), encoding="utf-8"))
    index = {}
    for f, segs in data.items():
        for s in segs:
            index[s["id"]] = (f, s)

    ok = miss = 0

    for seg_id, field, old, new, why in TEXT_EDITS:
        if old == new:
            continue
        got = index.get(seg_id)
        if not got:
            print("MISS  段不存在  %s" % seg_id)
            miss += 1
            continue
        f, seg = got
        cur = seg.get(field, "")
        if old not in cur:
            print("MISS  %s [%s]  %s" % (seg_id, field, why))
            miss += 1
            continue
        seg[field] = cur.replace(old, new, 1)
        ok += 1
        print("OK    %s [%s]  %s" % (seg_id, field, why))

    for seg_id, (old_key, new_key) in REPLACE_REF.items():
        got = index.get(seg_id)
        if not got:
            print("MISS  段不存在  %s" % seg_id)
            miss += 1
            continue
        f, seg = got
        refs = seg.get("refs", [])
        if old_key not in refs:
            print("MISS  %s refs 里没有 %s" % (seg_id, old_key))
            miss += 1
            continue
        refs[refs.index(old_key)] = new_key
        ok += 1
        print("OK    %s refs  %s → %s" % (seg_id, old_key, new_key))

    for seg_id, key in DROP_REF.items():
        got = index.get(seg_id)
        if not got:
            print("MISS  段不存在  %s" % seg_id)
            miss += 1
            continue
        f, seg = got
        refs = seg.get("refs", [])
        if key not in refs:
            print("MISS  %s refs 里没有 %s" % (seg_id, key))
            miss += 1
            continue
        refs.remove(key)
        ok += 1
        print("OK    %s refs  删除 %s" % (seg_id, key))

    for seg_id, notes in REF_NOTES.items():
        got = index.get(seg_id)
        if not got:
            print("MISS  段不存在  %s" % seg_id)
            miss += 1
            continue
        f, seg = got
        cur = seg.get("ref_notes") or {}
        changed = False
        for k, v in notes.items():
            if cur.get(k) == v:
                continue
            cur[k] = v
            changed = True
        if not changed:
            print("MISS  %s ref_notes 已是目标值" % seg_id)
            miss += 1
            continue
        seg["ref_notes"] = cur
        ok += 1
        print("OK    %s ref_notes  %s" % (seg_id, ",".join(notes.keys())))

    # 落盘
    touched = set()
    for seg_id, field, old, new, why in TEXT_EDITS:
        got = index.get(seg_id)
        if got:
            touched.add(got[0])
    for d in (REPLACE_REF, DROP_REF, REF_NOTES):
        for seg_id in d:
            got = index.get(seg_id)
            if got:
                touched.add(got[0])

    for f in sorted(touched):
        path = os.path.join(BEATS, f)
        tmp = path + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data[f], fh, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
        print("写入 %s" % f)

    print("\n合计 应用 %d 条，未命中 %d 条" % (ok, miss))
    print("下一步： python storyboard_render.py ep001  &&  python check_beats.py ep001")
    return 0


if __name__ == "__main__":
    sys.exit(main())
