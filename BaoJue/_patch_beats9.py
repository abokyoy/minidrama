# -*- coding: utf-8 -*-
"""
第九轮补丁：把声景里「明确断言整个空间没有声音」的一类写法清干净。

为什么单独做一轮：第四轮复核已经证实，H3 对声景里的「否定声音」写法很敏感，
写 silence / muted / nothing at all 会把**人声一起压掉**。第五轮复核又指出
"dead quiet room / total hush / gone quiet / nothing but …" 属于同一类。

注意区分（不要误伤）：声景里写 "a quiet voice"、"one quiet question"、
"two quiet words" 是在形容**音量低**，不属这一类，一律保留不动。
只改那些说「房间/大堂/走廊整个静掉了」的写法。

用法： python _patch_beats9.py   （第二次运行报 MISS 属正常）
之后 check_beats.py 会把这一类词也拦下来（SOUNDSCAPE_BAD 已加）。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
BEATS = os.path.join(BASE, "ep001_beats")

TEXT_EDITS = [
    ("ep01_t13", "soundscape",
     "the corridor now almost empty and very quiet.",
     "the corridor now almost empty, the air-conditioning hum.",
     "声景：走廊「很安静」改成具象声源"),
    ("ep01_t28", "soundscape",
     "Her low clear voice in a dead-quiet room,",
     "Her low clear voice in a room where every voice has dropped,",
     "声景：dead-quiet 改正向"),
    ("ep01_t38", "soundscape",
     "Three voices trading in a dead-quiet room,",
     "Three voices trading in a room that has dropped very low,",
     "声景：dead-quiet 改正向"),
    ("ep01_t39", "soundscape",
     "then four quiet words and a total hush.",
     "then four quiet words and the whole room going still.",
     "声景：total hush 改正向"),
    ("ep01_t40", "soundscape",
     "Dead quiet room, the fluorescent panels,",
     "A room holding its breath, the fluorescent panels,",
     "声景：Dead quiet room 改正向"),
    ("ep01_t50", "soundscape",
     "then three seconds of dead room tone with only the clock,",
     "then three seconds with only the clock,",
     "声景：dead room tone 改正向"),
    ("ep01_t54", "soundscape",
     "one clipped male phrase, dead room tone, one person at the door breathing.",
     "one clipped male phrase, one person at the door breathing.",
     "声景：dead room tone 改正向"),
    ("ep01_t64", "soundscape",
     "One quiet courteous voice in a dead-still room,",
     "One quiet courteous voice in a room where nobody is moving,",
     "声景：dead-still 改正向"),
    ("ep01_t69", "soundscape",
     "then nothing but the ceiling lights and the clock,",
     "then only the ceiling lights and the clock,",
     "声景：nothing but 改正向"),
    ("ep01_t97", "soundscape",
     "the corridor outside gone quiet.",
     "the corridor outside dropping to a murmur.",
     "声景：gone quiet 改正向"),
    ("ep01_t110", "soundscape",
     "One flat quiet line in a lobby that has gone completely quiet,",
     "One flat quiet line in a lobby where every conversation has stopped,",
     "声景：gone completely quiet 改正向"),
]


def main():
    data = {}
    for f in sorted(os.listdir(BEATS)):
        if f.endswith(".json"):
            data[f] = json.load(io.open(os.path.join(BEATS, f), encoding="utf-8"))
    index = {}
    for f, segs in data.items():
        for s in segs:
            index[s["id"]] = (f, s)

    ok = miss = 0
    touched = set()
    for seg_id, field, old, new, why in TEXT_EDITS:
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
        touched.add(f)
        ok += 1
        print("OK    %s [%s]  %s" % (seg_id, field, why))

    for f in sorted(touched):
        path = os.path.join(BEATS, f)
        tmp = path + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data[f], fh, ensure_ascii=False, indent=1)
        os.replace(tmp, path)

    print("\n合计 应用 %d 条，未命中 %d 条" % (ok, miss))
    return 0


if __name__ == "__main__":
    sys.exit(main())
