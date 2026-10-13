# -*- coding: utf-8 -*-
r"""
第六轮补丁：第三轮**复核**（_verify_A/B/C.md）剩下的问题。

来源：
  _verify_A：原第14条 PARTIAL（t42 钱经理仍离桌）+ 新增 1 条（t43 同源）
  _verify_B：新增 2 条（t53 声景 silent / t52 道具与 Entry 打架）
  _verify_C：原第5条 PARTIAL（t117 跨剪辑）+ 新增 5 条
             （t108/t110 参考图带进了不在场的钱经理；t109/t112 用办公室场景图配大堂；
               t96–t98 与 ANCHOR_14 打架；t114 Entry 承诺了不存在的镜头 + 重复"走出玻璃门"；
               t117 段内"blue dusk"与当天日戏曝光打架）

注：t42/t43 与 t96–t98 的根因是**锚点写死了钱经理的调度**，本轮改为
    修正 storyboard_render.py 里的 ANCHOR_12 / ANCHOR_14（见同批次的 Edit），
    beats 侧只把含糊写法写明确。
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BEATS = os.path.join(BASE, "ep001_beats")
MISS = []

PATCHES = {
    # ------------------------------------------------------------- verify-B
    "ep01_t52": [
        ("she sets the phone down flat on the desk between herself and the card, screen up, and lets go of it.",
         "she sets the phone down flat on the desk between herself and 周总监 (S6), screen up, and lets go of it, the black card still held in her other hand."),
    ],
    "ep01_t53": [
        ("the room silent enough to hear the ceiling lights.",
         "the room holding still enough to hear the ceiling lights."),
    ],    "ep01_t61": [
        ("in a brisk brisk Mandarin", "in a brisk Mandarin"),
    ],
    # ------------------------------------------------------------- verify-C（t96–t98 写明确）
    "ep01_t96": [
        ("钱经理 (S3) is mid-room with the resignation form still in his hand;",
         "钱经理 (S3) is on the near side of the desk, just in from the doorway, with the resignation form still in his hand;"),
    ],
    "ep01_t97": [
        ("钱经理 (S3) is in front of him with one hand still outstretched;",
         "钱经理 (S3) is a step in front of him on the door side with one hand still outstretched;"),
    ],
    "ep01_t98": [
        ("钱经理 (S3) has backed half a step away;",
         "钱经理 (S3) has backed half a step away toward the far side of the desk;"),
    ],
    # ------------------------------------------------------------- verify-C（t114 动线）
    "ep01_t114": [
        ("苏小满 (S1) already a few paces out on the paving with her cardboard box; then the sequence cuts back inside — first to the third-floor corridor outside the office, then to the ground-floor lobby looking back toward the lift bank.",
         "苏小满 (S1) already out on the paving a few paces clear of the doors with her cardboard box; the beat opens on one short cutaway back inside, then stays outside."),
        ("[Shot 2] At 00:02.800, outside and already through: 苏小满 (S1) takes the last few strides clear of the glass doors and out onto the open forecourt with the cardboard box in her arms, and stops.",
         "[Shot 2] At 00:02.800, outside on the forecourt: 苏小满 (S1) walks the last few paces further out into the open middle of the paving with the cardboard box in her arms, and stops."),
    ],
    # ------------------------------------------------------------- verify-C（t117 光照）
    "ep01_t117": [
        ("the car pulls away from the kerb into the blue dusk with its tail lights coming on;",
         "the car pulls away from the kerb into the late-afternoon light with its tail lights coming on;"),
    ],
    # ------------------------------------------------------------- verify-A（t43 跟随关系写明确）
    "ep01_t43": [
        ("[Shot 1] Medium: 周总监 (S6) walks past the manager without answering him, crosses to the desk and takes the card out of the other man's hand as he goes.",
         "[Shot 1] Medium: 周总监 (S6) walks past the manager without answering him and crosses to the desk, taking the card out of the other man's hand as he goes; 钱经理 (S3) trails a step behind him and stops in his shadow."),
    ],
}

# ------------------------------------------------------------- verify-C（参考图配错）
# 判据：大堂段 t108/t110 正文里根本没有钱经理，却把 char_qianjingli 当参考图；
#       t109/t112 是大堂段却配了办公室场景图。
REFS = {
    "ep01_t108": ["suxiaoman", "xiaoluo", "lobby_1f", "building_exterior"],
    "ep01_t109": ["suxiaoman", "xiaoluo", "lobby_1f", "building_exterior"],
    "ep01_t110": ["suxiaoman", "xiaoluo", "lobby_1f"],
    "ep01_t112": ["suxiaoman", "xiaoluo", "lobby_1f", "building_exterior"],
}


def main():
    for f in sorted(os.listdir(BEATS)):
        if not f.endswith(".json"):
            continue
        p = os.path.join(BEATS, f)
        data = json.load(io.open(p, encoding="utf-8"))
        touched = False
        for seg in data:
            for old, new in PATCHES.get(seg["id"], []):
                hit = False
                for key in ("shots", "soundscape", "summary"):
                    v = seg.get(key)
                    if isinstance(v, str) and old in v:
                        seg[key] = v.replace(old, new)
                        hit = True
                        touched = True
                if not hit:
                    MISS.append("%s %s 未命中: %s" % (f, seg["id"], old[:65]))
            if seg["id"] in REFS:
                if seg["refs"] != REFS[seg["id"]]:
                    seg["refs"] = list(REFS[seg["id"]])
                    touched = True
        if touched:
            io.open(p, "w", encoding="utf-8").write(
                json.dumps(data, ensure_ascii=False, indent=1))

    if MISS:
        print("== 未命中 %d 条 ==" % len(MISS))
        for m in MISS:
            print("  " + m)
        return 1
    print("第六轮补丁全部命中并写入（含参考图纠正 %d 段）。" % len(REFS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
