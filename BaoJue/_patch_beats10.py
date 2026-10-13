# -*- coding: utf-8 -*-
"""
第十轮补丁：整改第六轮复核（_verify6.md，seg82–seg104）的 16 条。

关键前提（这轮审核定级的依据）：`gen_worker.py` 里 `GROUP = 3`，**链式只存在于 3 段组内**。
组内相邻对（82→83、83→84 …）的 Entry 必须等于上一段尾帧，否则第一帧直接跳变 → 判「高」。

高 3 条
  83→84  组内链式跳变：83 尾帧两人都在走廊、纸单在拳里；84 Entry 却写她一个人、纸单已入兜
         → 医生凭空消失 + 道具跳变。改：84 Entry 接住 83 尾帧，把「进兜」写成可见动作。
  91→92  组内链式跳变：91 通篇写「办公室空无一人」，92 首帧钱经理就在门口
         → 改不了 92（三句台词已占满），必须在 91 结尾给他一个可见入场（新增 Shot 5 + 挂 ref）。
  98     声景 `only breathing in it` 等同禁用清单里的 `nothing but …`
         → 会把吼声和人声一起压掉。

中 5 条
  94     她站在门口却要「越过桌子够笔」——几何不成立，且违反固定空间规则（她恒在桌近侧）
  100/101 参考图漏挂画面里真实出现的人（100 缺苏小满、101 缺钱经理）
  88/89  声景 `go quieter` / `nothing in it` 两处否定式

低 8 条
  91/101/102 房间级 quiet 措辞；85/86/94 summary 的 `Silent beat:`；99 辞工单归因给错人；
  101 Entry 出现无来源动作 `half turned to leave`；83/84/86 越挂 hospital_ward、87 越挂 hospital_corridor；
  93 台词起点与上一句终点重叠（有时间余量，顺手收紧）。

【本轮不修】seg 92 / 100 的台词起点重叠：这两段三句台词按 2.5 字/秒算合计已 >10 秒，
在不改台词、不拆段的前提下无解，只能接受（实际短剧语速远超 2.5 字/秒，可正常交付）。

用法： python _patch_beats10.py   （第二次运行报 MISS 属正常）
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
BEATS = os.path.join(BASE, "ep001_beats")

TEXT_EDITS = [
    # ---------- 高 1：seg84 接住 seg83 的尾帧 ----------
    ("ep01_t84", "shots",
     "Entry state, re-anchored to the reference images: 苏小满 (S1) is alone in the corridor; the ward door is on the RIGHT of frame, the bench and the wall on the LEFT; the folded form is in her trouser pocket.",
     "Entry state, re-anchored to the reference images: 苏小满 (S1) stands in the corridor facing the ward door on the RIGHT with the folded form closed in her fist; 医生 (S11) is still beside her and is already turning back toward the ward door; the bench and the wall are on the LEFT.",
     "高1 seg84 Entry 接住 seg83 尾帧（医生还在场、纸单还在拳里）"),
    ("ep01_t84", "shots",
     "[Shot 1] Medium: 苏小满 (S1) crosses to the LEFT wall, lets her back settle against it just beside the bench, takes out her phone and dials with her thumb, holding the screen up close.",
     "[Shot 1] Medium: 医生 (S11) goes back in through the ward door on the RIGHT and it settles shut behind him; 苏小满 (S1) crosses to the LEFT wall, pushes the folded form down into her trouser pocket on the way, lets her back settle against the wall just beside the bench, takes out her phone and dials with her thumb, holding the screen up close.",
     "高1 把「医生退场 + 纸单进兜」写成可见动作"),

    # ---------- 高 2：seg91 结尾给钱经理一个可见入场 ----------
    ("ep01_t91", "shots",
     "the office is spotless and empty of anybody else;",
     "the office is spotless and empty of anybody else at the top of the beat;",
     "高2 seg91 Entry 限定「开场时」无人"),
    ("ep01_t91", "shots",
     "[Shot 4] At 00:07.400, extreme close-up on a thin notebook lying beside it, its pages crammed edge to edge with small neat handwritten numbers, the outer corners rubbed down to soft fur. Nobody speaks in this whole beat.",
     "[Shot 4] At 00:07.400, extreme close-up on a thin notebook lying beside it, its pages crammed edge to edge with small neat handwritten numbers, the outer corners rubbed down to soft fur.\n[Shot 5] At 00:09.200, rack focus off the box onto the open LEFT door: 钱经理 (S3) now stands in the doorway with his arms crossed, a shoulder against the doorframe, watching her. Nobody speaks in this whole beat.",
     "高2 新增 Shot 5：钱经理的可见入场"),

    # ---------- 高 3：seg98 声景 ----------
    ("ep01_t98", "soundscape",
     "Loud indignant shouting, a hand slapping the desk, then a very quiet room with only breathing in it.",
     "Loud indignant shouting, a hand slapping the desk, then the room left holding its breath under the ceiling lights.",
     "高3 声景去掉「只剩呼吸」式否定写法"),

    # ---------- 中 4：seg94 几何矛盾 + seg95 承接 ----------
    ("ep01_t94", "shots",
     "苏小满 (S1) stands one step inside the LEFT doorway of the office with the cardboard box in her arms; 钱经理 (S3) stands in front of her,",
     "苏小满 (S1) stands on the NEAR side of the desk with her back to the LEFT door, the cardboard box in her arms; 钱经理 (S3) stands in the doorway in front of her,",
     "中4 seg94 回到「她恒在桌近侧」的固定空间规则"),
    ("ep01_t95", "shots",
     "苏小满 (S1) stands in the LEFT doorway of the office with the cardboard box on one hip and her right hand still back over the desk;",
     "苏小满 (S1) stands on the NEAR side of the desk with the cardboard box on one hip and her right hand still back over the desk;",
     "中4 seg95 Entry 与 94 对齐"),

    # ---------- 中 7/8：声景否定式 ----------
    ("ep01_t88", "soundscape",
     "and then the room seems to go quieter.",
     "and under it only the ceiling lights and the window.",
     "中7 声景去掉 go quieter"),
    ("ep01_t89", "soundscape",
     "A faint slow voice, a pause with nothing in it, then a low urgent question,",
     "A faint slow voice, the room holding its breath, then a low urgent question,",
     "中8 声景去掉 nothing in it"),

    # ---------- 低 9/10/11：房间级 quiet ----------
    ("ep01_t91", "soundscape",
     "A quiet office in the afternoon: the ceiling lights,",
     "The office in the afternoon: the ceiling lights,",
     "低9 声景去掉房间级 quiet"),
    ("ep01_t101", "soundscape",
     "one soft careful voice in the sudden quiet.",
     "one soft careful voice coming through the room.",
     "低10 声景去掉 the sudden quiet"),
    ("ep01_t102", "soundscape",
     "a shuffling half bow, the office very quiet around it.",
     "a shuffling half bow, then only the clock and the lights.",
     "低11 声景去掉房间级 quiet"),

    # ---------- 低 12：summary 的 Silent beat ----------
    ("ep01_t85", "summary",
     "Silent beat: the call is cut off,",
     "Wordless beat: the call is cut off,",
     "低12 summary 也是 H3 输入，Silent 有连带压声风险"),
    ("ep01_t86", "summary",
     "Silent beat: the one piece of privacy",
     "Wordless beat: the one piece of privacy",
     "低12 同上"),
    ("ep01_t94", "summary",
     "Silent beat: she turns to look at the form,",
     "Wordless beat: she turns to look at the form,",
     "低12 同上"),

    # ---------- 低 13：辞工单是钱经理丢的，不是张总 ----------
    ("ep01_t99", "shots",
     "the blank resignation sheet 张总 (S10) threw down is lying face up on the desktop.",
     "the blank resignation sheet 钱经理 (S3) dropped on the desktop earlier is lying face up on it.",
     "低13 修正道具归因"),

    # ---------- 低 14：seg101 去掉无来源动作 ----------
    ("ep01_t101", "shots",
     "holding the cardboard box, half turned to leave; 张总 (S10) is at the desk",
     "holding the cardboard box; 张总 (S10) is at the desk",
     "低14 seg101 Entry 去掉「半转身要走」（seg100 尾帧没有这个动作）"),

    # ---------- 低 16：seg93 台词起点重叠（有时间余量）----------
    ("ep01_t93", "shots",
     "[Shot 3] At 00:07.000, closer on 钱经理's (S3) face as he delivers the last part flatly:",
     "[Shot 3] At 00:07.600, closer on 钱经理's (S3) face as he delivers the last part flatly:",
     "低16 seg93 第三句起点后移，避免与上一句结尾撞词"),
]

# ---------- 低 15：场景参考图越挂 ----------
DROP_REF = {
    "ep01_t83": "hospital_ward",
    "ep01_t84": "hospital_ward",
    "ep01_t86": "hospital_ward",
    "ep01_t87": "hospital_corridor",
}

# ---------- 中 5/6、高 2：漏挂的在场人物 ----------
ADD_REF = {
    "ep01_t91": ("qianjingli", 0),   # Shot 5 他出现在门口
    "ep01_t100": ("suxiaoman", 0),   # Shot 4 她一直在左侧门口看
    "ep01_t101": ("qianjingli", 2),  # Shot 4 他在背景里
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

    for seg_id, (key, pos) in ADD_REF.items():
        got = index.get(seg_id)
        if not got:
            print("MISS  段不存在  %s" % seg_id)
            miss += 1
            continue
        f, seg = got
        refs = seg.get("refs", [])
        if key in refs:
            print("MISS  %s refs 里已有 %s" % (seg_id, key))
            miss += 1
            continue
        if len(refs) >= 6:
            print("MISS  %s 参考图已达 6 张上限，不能再加 %s" % (seg_id, key))
            miss += 1
            continue
        refs.insert(min(pos, len(refs)), key)
        ok += 1
        print("OK    %s refs  新增 %s → %s" % (seg_id, key, refs))

    touched = set()
    for seg_id, *_ in TEXT_EDITS:
        got = index.get(seg_id)
        if got:
            touched.add(got[0])
    for d in (DROP_REF, ADD_REF):
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
