# -*- coding: utf-8 -*-
r"""ep003 第②层审核整改补丁（对应 _verify9_ep003a.md / _verify9_ep003b.md）。

只改 beats 里的 Entry / 镜头描述 / refs，不动任何一句台词。
每条替换都带断言，匹配不到就报错计数，绝不静默跳过。

用法： python _patch_ep003.py
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
BEATS = os.path.join(BASE, "ep003_beats")

n_ok = n_bad = 0


def load():
    out = {}
    for f in sorted(os.listdir(BEATS)):
        if f.endswith(".json"):
            out[f] = json.load(io.open(os.path.join(BEATS, f), encoding="utf-8"))
    return out


def save(data):
    for f, arr in data.items():
        p = os.path.join(BEATS, f)
        tmp = p + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            json.dump(arr, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, p)


def seg(data, sid):
    for arr in data.values():
        for s in arr:
            if s["id"] == sid:
                return s
    raise SystemExit("找不到段 %s" % sid)


DATA = load()


def rep(sid, field, old, new):
    global n_ok, n_bad
    s = seg(DATA, sid)
    v = s.get(field) or ""
    if old not in v:
        print("  ✗ %s.%s 未匹配：%s" % (sid, field, old[:70]))
        n_bad += 1
        return
    s[field] = v.replace(old, new, 1)
    n_ok += 1


def add_ref(sid, key):
    global n_ok, n_bad
    s = seg(DATA, sid)
    if key in s["refs"]:
        n_ok += 1
        return
    if len(s["refs"]) >= 6:
        print("  ✗ %s 已经有 6 张参考图，加不进 %s" % (sid, key))
        n_bad += 1
        return
    s["refs"].append(key)
    n_ok += 1


# ==================================================== 高：seg14(t20) 门房被写成"昏暗"（违反"不许偏黑"）
rep("ep03_t20", "shots",
    "the narrow gatehouse room, dim, with only a thin line of daylight leaking in at the door crack and beyond "
    "the inner door;",
    "the narrow gatehouse room, bright and airy in the mid-morning, its ceiling light switched on and daylight "
    "pouring in through the open inner door;")

# ==================================================== 中：seg23(t29) 同一处的"退进阴影/没入黑暗"
rep("ep03_t29", "shots",
    "pulls the door further open and retreats into the shadow of the room, head lowering; but once he is back in "
    "the shadow, his eyes still follow half a beat after the direction she walks, and then he is gone into the dark "
    "of the room.",
    "pulls the door further open and steps back into the far corner of the room, head lowering; but even from "
    "there his eyes still follow half a beat after the direction she walks, and then he settles out of the framing, "
    "softly readable against the room's shaded far corner.")

# ==================================================== 高：seg50(t66) → seg51(t67) 陆崇"手挪到小几"没有可见交代
rep("ep03_t66", "shots",
    "she wants the rule, not a favour: [Chinese] 写着送医人的名字。",
    "she wants the rule, not a favour: [Chinese] 写着送医人的名字。 At the east window, behind her eyeline, "
    "陆崇's (S15) leaning weight settles and his hand comes to rest flat on the small side table beside his chair.")
add_ref("ep03_t66", "luchong")

# ==================================================== 高：seg66/67/68（t111/t112/t113）整段把小罗丢了，
#                                                     到 t114 又凭空出现 —— 组内 Entry 对不上末拍
_XL = ("小罗 (S7) trails a further half step behind 苏小满 (S1), nearest to camera, his face travelling "
       "between the two women; ")
rep("ep03_t111", "shots",
    "陆蔓 (S8) walks at the front of the deep veranda with her back to camera; 苏小满 (S1) follows half a step "
    "at her left-rear facing her back;",
    "陆蔓 (S8) walks at the front of the deep veranda with her back to camera; 苏小满 (S1) follows half a step "
    "at her left-rear facing her back; " + _XL)
rep("ep03_t112", "shots",
    "苏小满 (S1) follows half a step at 陆蔓's (S8) left-rear, facing the far end of the veranda; 陆蔓 (S8) walks "
    "ahead with her back to camera;",
    "苏小满 (S1) follows half a step at 陆蔓's (S8) left-rear, facing the far end of the veranda; 陆蔓 (S8) walks "
    "ahead with her back to camera; " + _XL)
rep("ep03_t113", "shots",
    "苏小满 (S1) walks half a step behind 陆蔓 (S8) with her head down; 陆蔓 (S8) is ahead with her back to "
    "camera and still moving away.",
    "苏小满 (S1) walks half a step behind 陆蔓 (S8) with her head down; 陆蔓 (S8) is ahead with her back to "
    "camera and still moving away; " + _XL.rstrip("; ") + ".")
for sid in ("ep03_t111", "ep03_t112", "ep03_t113"):
    add_ref(sid, "xiaoluo")

# ==================================================== 中：seg97(t151) 上一段（t150）主角是二楼窗后的陆崇，
#                                                     这一段 Entry 没把他带过来
rep("ep03_t151", "shots",
    "the veranda runs away from her toward the moon gate.",
    "the veranda runs away from her toward the moon gate; 陆崇 (S15) is still up at the first-floor window above "
    "and behind her, out of this framing.")

save(DATA)
print("ep003 beats 补丁：成功 %d 条，失败 %d 条" % (n_ok, n_bad))
sys.exit(1 if n_bad else 0)
