# -*- coding: utf-8 -*-
"""给所有三人镜头加「唯一口型」正面锁定（防台词被画面中心的人抢走）。

⛔⛔⛔ 起因：片3「没看清」本该小唐说，苏小满说了。
   `_check_voice.py` 借这件事把同类隐患全扫出来：
     seg01/04/07/08 = 三人镜头但没有「唯一口型」正面锁定
     seg04 = 闭嘴描写只有 1 处（三人里有两个人的嘴没写死）

✅ 统一改成正面可观测的表述（不是否定句）：
   说话人：`X is the only person in frame whose mouth moves, and it opens wide ...`
   其他人：`his lips stay pressed shut and his jaw does not move.`
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.join(HERE, "xs001_segs")

# 片 → (说话人, 另外两人)
PLAN = {
    "seg01": ("钱经理", "苏小满", "小唐"),
    "seg04": ("钱经理", "苏小满", "小唐"),
    "seg07": ("钱经理", "苏小满", "小唐"),
    "seg08": ("钱经理", "苏小满", "小唐"),
}

LOCK_CN = {
    "钱经理": "he is the only person in frame whose mouth moves",
    "苏小满": "she is the only person in frame whose mouth moves",
    "小唐": "she is the only person in frame whose mouth moves",
}


def apply(tag, speaker, *others):
    p = os.path.join(SEG, "%s_prompt.txt" % tag)
    s = io.open(p, encoding="utf-8").read()
    if LOCK_CN[speaker] in s:
        print("[%s] 已有唯一口型锁定，跳过" % tag)
        return
    # ① 在说话人第一次 speaks 之前插入口型锁定
    marker = "%s (S%d) speaks" % (
        speaker, {"钱经理": 1, "苏小满": 2, "小唐": 3}[speaker])
    i = s.find(marker)
    assert i > 0, "[%s] 找不到 %s" % (tag, marker)
    lock = ("%s, and it opens wide enough to shape every syllable as he delivers "
            "his lines in a loud nasal Mandarin: " % LOCK_CN[speaker])
    # 插到「speaks:」前最近的那个冒号之后
    j = s.rfind(": ", 0, i)
    s = s[:j + 2] + lock + s[j + 2:]
    print("[%s] ① 已给 %s 加唯一口型锁定" % (tag, speaker))

    # ② 补齐其他人的闭嘴描写
    for o in others:
        sid = {"钱经理": 1, "苏小满": 2, "小唐": 3}[o]
        nm = "%s (S%d)" % (o, sid)
        # 找这人的描述段，看有没有闭嘴描写
        k = s.find(nm)
        while k > 0:
            seg_end = s.find(";", k)
            segtxt = s[k:seg_end if seg_end > 0 else k + 200]
            if "mouth closed" not in segtxt and "lips stay pressed shut" not in segtxt \
                    and "mouth stays shut" not in segtxt:
                # 在这人段末补闭嘴
                pos = seg_end if seg_end > 0 else k + 160
                s = (s[:pos] + "; his lips stay pressed shut and his jaw does not move"
                     + s[pos:])
                print("[%s]   ② 已给 %s 补闭嘴描写" % (tag, o))
                break
            k = s.find(nm, k + 1)

    io.open(p, "w", encoding="utf-8").write(s)
    print("[%s] 完成" % tag)


if __name__ == "__main__":
    for tag, (sp, o1, o2) in sorted(PLAN.items()):
        apply(tag, sp, o1, o2)
        print()