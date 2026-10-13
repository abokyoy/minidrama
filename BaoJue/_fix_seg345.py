# -*- coding: utf-8 -*-
"""seg03/04/05 参考图竞争修复（照 seg02 已验证通过的配方）。

三条铁律：
  1) 一段只给 1 张环境图 —— 两张环境图抢「环境」这个角色，人物身份就会被忽略
     （官方原话：If several references compete to define the same property, reduce them）
  2) 画面里出现的人必须有其参考图 —— 写了人却没给图，模型只能自己编 → 复制
  3) 零否定词 —— 扩散模型没有否定能力，写 nobody/no one 等于反复提醒它「有人」
"""
import json
import io

P = "xs001_beats/scene11.json"
segs = json.load(io.open(P, encoding="utf-8"))
changes = []

# ---------- seg03: 3 人 + 1 张环境图，已是安全结构，仅统一环境图为 pano ----------
s = segs[2]
old = list(s["refs"])
s["refs"] = ["xiaotang", "qianjingli", "suxiaoman", "office_pano"]
changes.append(("seg03 refs", old, list(s["refs"])))

# ---------- seg04: 补钱经理参考图 + 2 张环境图砍到 1 张 ----------
s = segs[3]
old = list(s["refs"])
s["refs"] = ["suxiaoman", "xiaotang", "qianjingli", "office_pano"]
changes.append(("seg04 refs", old, list(s["refs"])))

# ---------- seg05: 2 张环境图砍到 1 张 ----------
s = segs[4]
old = list(s["refs"])
s["refs"] = ["qianjingli", "suxiaoman", "office_pano"]
changes.append(("seg05 refs", old, list(s["refs"])))

# ---------- seg05 正文：清掉没参考图的小唐 + 改掉 shots 里的否定句 ----------
s = segs[4]
old_entry = s["shots"].split("\n")[0]
new_entry = ("Entry state, re-anchored to the reference image: 钱经理 (S3) is stepping "
             "round the end of the desk onto the NEAR side and closing to one pace in "
             "front of 苏小满 (S1); 苏小满 (S1) is on the near side of the desk with her "
             "back to the door, facing him across one pace of bare floor; EXACTLY TWO "
             "PEOPLE are present and it is always these same two — the manager in the "
             "white shirt and charcoal waistcoat and the cleaner in the navy uniform "
             "with the grey apron, each one holding her or his own half of the frame, "
             "and the room, the doorway and the corridor beyond it stay bare and the "
             "eye goes to the pair.")
assert old_entry in s["shots"], "seg05 Entry state 没匹配上"
s["shots"] = s["shots"].replace(old_entry, new_entry, 1)
changes.append(("seg05 entry", old_entry[:60] + "...", new_entry[:60] + "..."))

# Shot 2 / Shot 3 里的 nobody / no one / alone 全是否定词，改成正面说法
reps = [
    ("reverse single on 苏小满 (S1), framed on her alone, one person in this shot, "
     "nobody behind her and nobody at the door: she takes one small half-step back",
     "reverse single on 苏小满 (S1) filling the frame on her own, the plain office wall "
     "and the bright window band behind her, one person in this shot: she takes one "
     "small half-step back"),
    ("close on the pocket under her fingers, the fabric pulled slightly taut, framed on "
     "her alone, no one else enters this frame. She is silent after that.",
     "close on the pocket under her fingers, the fabric pulled slightly taut, her own "
     "hand and the cloth filling the whole frame. She is silent after that."),
]
for a, b in reps:
    assert a in s["shots"], "seg05 没匹配上: " + a[:40]
    s["shots"] = s["shots"].replace(a, b, 1)
    changes.append(("seg05 shot", a[:50] + "...", b[:50] + "..."))

# ---------- seg03/04 的 Entry state 也补上人数锁（正面表述）----------
s = segs[2]
s["shots"] = s["shots"].replace(
    "小唐 (S4) is still flattened against the wall just inside the LEFT door, "
    "lower-left of frame.",
    "小唐 (S4) is still flattened against the wall just inside the LEFT door, "
    "lower-left of frame. EXACTLY THREE PEOPLE are present and it is always these "
    "same three — 钱经理 (S3) behind the desk on the far side, 苏小满 (S1) at the "
    "near side with her back to the door, and 小唐 (S4) low at the LEFT door, each "
    "one holding her or his own third of the frame.",
    1)

s = segs[3]
s["shots"] = s["shots"].replace(
    "钱经理 (S3) on the far side of the desk.",
    "钱经理 (S3) on the far side of the desk. EXACTLY THREE PEOPLE are present and "
    "it is always these same three — 苏小满 (S1) at the near side with her back to "
    "the door, 小唐 (S4) one step in from the LEFT door low in frame, and 钱经理 (S3) "
    "behind the desk on the far side, each one holding her or his own third of the frame.",
    1)

with io.open(P, "w", encoding="utf-8") as f:
    f.write(json.dumps(segs, ensure_ascii=False, indent=2))

for name, a, b in changes:
    print("· %s\n    旧 %s\n    新 %s" % (name, a, b))
print("\n写回完成")