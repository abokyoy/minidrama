# -*- coding: utf-8 -*-
"""
第八轮补丁：整改第五轮聚焦复核（_verify5.md）列出的 9 条 + 2 条范围外观察。

H1（高危） seg97→seg98 位置跳变
    链式生成里「上一段末帧 = 下一段首帧」，所以 seg98 的 Entry 必须等于 seg97 的结尾。
    seg97 结尾钱经理还在门侧（张总身前半步），seg98 Entry 却已经「退到远侧」，
    中间没有任何镜头交代这一步——必然跳变。改法：seg98 Entry 写成「他仍在门侧」，
    再在 Shot 2 里给他一个可见的「绕桌子退回远侧」动作。

M1（中）  seg20 声景里写 "paper unfolding"，与「纸单始终对折、绝不摊开」正面冲突。

L 系列    seg119 声景 "The cabin's quiet"；seg109/112 挂着没入画的 building_exterior；
          seg76 Entry 自相矛盾（"at the far side of the desk … a few steps from the desk"）；
          seg117 Entry 的 "amber roof lights" 没写是否点亮（H3 会当夜间打光）；
          seg55 Shot 里 "nothing at all"；seg99 桌面 "resignation form" 与苏小满兜里
          "folded paper form" 同名易混；seg114→115 小罗凭空多出。

范围外    seg118 summary 与自身锚点矛盾（说陆蔓「上车」，其实她一直在车上）；
          seg96 声景 "nothing but heavy breathing" 归一成正向写法。

用法： python _patch_beats8.py   （第二次运行报 MISS 属正常）
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
BEATS = os.path.join(BASE, "ep001_beats")

TEXT_EDITS = [
    # ---- H1：seg98 承接 seg97 的结尾位置，并给出可见的退位动作 ----
    ("ep01_t98", "shots",
     "Entry state, re-anchored to the reference image: 张总 (S10) stands at the desk with one hand flat on it; 钱经理 (S3) has retreated to the far side of the desk and stands behind it; 苏小满 (S1) is still in the LEFT doorway with the cardboard box in her arms.",
     "Entry state, re-anchored to the reference image: 张总 (S10) stands at the desk with one hand flat on it, having just crossed to it; 钱经理 (S3) is still on the door side of the desk, half a step in front of where 张总 (S10) left him, one hand up; 苏小满 (S1) is still in the LEFT doorway with the cardboard box in her arms.",
     "H1 seg98 开场位置接住 seg97 结尾"),
    ("ep01_t98", "shots",
     "[Shot 2] At 00:07.000, wide of the room: 钱经理 (S3) with his head down, 张总 (S10) red in the face, and 苏小满 (S1) standing in the doorway watching it happen with no expression at all.",
     "[Shot 2] At 00:07.000, wide of the room: 钱经理 (S3) backs away round the end of the desk to the FAR side and stands there with his head down, 张总 (S10) red in the face, and 苏小满 (S1) standing in the doorway watching it happen with no expression at all.",
     "H1 补上「退回远侧」的可见动作"),

    # ---- M1：纸单始终对折，声景不能写 unfolding ----
    ("ep01_t20", "soundscape",
     "paper unfolding,",
     "a folded paper crackling,",
     "M1 纸单不摊开"),

    # ---- L：声景正向化 ----
    ("ep01_t119", "soundscape",
     "The cabin's quiet, a low female voice",
     "The cabin's low road hum, a low female voice",
     "L seg119 声景正向化"),
    ("ep01_t96", "soundscape",
     "then nothing but heavy breathing.",
     "then only heavy breathing.",
     "范围外 seg96 声景正向化"),

    # ---- L：seg76 Entry 自相矛盾 ----
    ("ep01_t76", "shots",
     "钱经理 (S3) is still at the far side of the desk where he leaned to watch 苏小满 (S1) go, a few steps from the desk;",
     "钱经理 (S3) is still on the far side of the desk, a few steps back from it, where he leaned to watch 苏小满 (S1) go;",
     "L seg76 措辞矛盾"),

    # ---- L：seg117 Entry 的琥珀灯要写清「此刻不亮」，否则 H3 会当夜间打光 ----
    ("ep01_t117", "shots",
     "the car interior is visible through the open door — pale-grey leather bench, amber roof lights.",
     "the car interior is visible through the open door — pale-grey leather bench, the amber roof lining lights switched off in the daylight.",
     "L seg117 别把夜间氛围灯当打光"),

    # ---- L：seg55 Shot 里的 nothing at all ----
    ("ep01_t55", "shots",
     "on the other end there is a full second of nothing at all,",
     "on the other end a full second of open line,",
     "L seg55 去掉「完全没有声音」写法"),

    # ---- L：seg99 桌面那张「离职单」改名，别和苏小满兜里的对折纸单混 ----
    ("ep01_t99", "shots",
     "the resignation form is lying face up on the desktop where it was dropped.",
     "the blank resignation sheet 张总 (S10) threw down is lying face up on the desktop.",
     "L 避免同名混淆"),
    ("ep01_t99", "shots",
     "[Shot 2] At 00:07.000, insert on the desk: the printed resignation form, face up, its blank signature line empty.",
     "[Shot 2] At 00:07.000, insert on the desk: the blank resignation sheet, face up, its blank signature line empty.",
     "L 避免同名混淆"),

    # ---- L：seg114 补小罗出场，别让他在 seg115 凭空冒出来 ----
    ("ep01_t114", "shots",
     "[Shot 2] At 00:02.800, outside on the forecourt: 苏小满 (S1) walks the last few paces further out into the open middle of the paving with the cardboard box in her arms, and stops.",
     "[Shot 2] At 00:02.800, outside on the forecourt: 苏小满 (S1) walks the last few paces further out into the open middle of the paving with the cardboard box in her arms; 小罗 (S7) comes out through the glass doors after her and stops half a step behind her LEFT shoulder, and she stops.",
     "L seg114 补小罗出场"),

    # ---- 范围外：seg118 summary 与锚点矛盾 ----
    ("ep01_t118", "summary",
     "and the woman who was introduced as 陆总 gets in and settles into the seat beside her.",
     "and the woman introduced as 陆总 has been sitting one place away from her since the car left the tower.",
     "范围外 seg118 summary 与锚点对齐"),
]

# seg109 / seg112 全程在大堂内，楼外那排车没进画面，参考图不该挂着
DROP_REF = {
    "ep01_t109": "building_exterior",
    "ep01_t112": "building_exterior",
}


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
        ok += 1
        print("OK    %s [%s]  %s" % (seg_id, field, why))

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

    touched = set()
    for seg_id, *_ in TEXT_EDITS:
        got = index.get(seg_id)
        if got:
            touched.add(got[0])
    for seg_id in DROP_REF:
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
