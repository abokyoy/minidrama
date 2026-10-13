# -*- coding: utf-8 -*-
"""修「说话人自己被写成闭嘴」的自相矛盾（2026-10-10 片4 苏小满消失）。

⛔⛔⛔ 现象：seg04 成片（off_xs01_t04_00005-audio.mp4）
   f001-f012 三个人 → **f013 起苏小满消失**，画面只剩 2 人。

   病根 = `_fix_lock_mouth.py` 昨晚插入闭嘴描写时，
   **把说话人自己也写了闭嘴**：
     `钱经理 (S1) … his palm flat on the wood and his jaw set hard;
      his lips stay pressed shut and his jaw does not move;      ←❌ 闭嘴
      he then swings his chin round … and speaks two short lines… ← 又开口
      he is the only person in frame whose mouth moves`            ← 又说唯一口型
   → 三处互相矛盾。模型读到「嘴紧闭」就当真了 → 钱经理全程不出声，
     画面能量逐渐散掉 → 后半段人消失。

✅ 正确写法：**说话人绝不能写闭嘴**。闭嘴只写给「不开口的那两个人」。
   说话人的口型只用正面描述：`mouth opening wide on each`。

⚠️ 全片体检：任何「X (Sn) … 段」里如果同时出现
   闭嘴描写 + `X (Sn) speaks` → 报红。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.join(HERE, "xs001_segs")

PEOPLE = ("钱经理", "苏小满", "小唐")
CLOSED = ("lips stay pressed shut", "mouth closed", "jaw does not move",
          "mouth does not move")


def seg_bounds(s):
    """返回 {人名: (start, end)}，范围限定在 ONE CONTINUOUS TAKE 那一段。"""
    st = s.find("ONE CONTINUOUS TAKE")
    assert st >= 0
    head = s.find("ten seconds:", st)
    body = s[head:]
    out = {}
    for i, w in enumerate(PEOPLE):
        k = body.find("%s (S" % w)
        if k < 0:
            continue
        ends = [x for x in (body.find("%s (S" % o, k + 10) for o in PEOPLE
                            if o != w) if x > k]
        out[w] = (head + k, head + (min(ends) if ends else len(body)))
    return out


def check(tag):
    p = os.path.join(SEG, "%s_prompt.txt" % tag)
    s = io.open(p, encoding="utf-8").read()
    b = seg_bounds(s)
    bad = []
    speakers = set(re.findall(r"(小唐|苏小满|钱经理) \(S\d\) speaks", s))
    for w, (a, z) in b.items():
        txt = s[a:z]
        has_closed = any(c in txt for c in CLOSED)
        says = ("%s (S" % w) in txt and re.search(
            re.escape(w) + r" \(S\d\) speaks", txt) is not None
        if says and has_closed:
            bad.append("⛔ 说话人 %s 自己被写了闭嘴（`%s`）→ 模型会当真，"
                       "他全程不出声，后半段画面会散人"
                       % (w, next(c for c in CLOSED if c in txt)))
    if bad:
        print("[%s] ❌ %d 项" % (tag, len(bad)))
        for x in bad:
            print("      - " + x)
        return False
    print("[%s] ✅ 无自相矛盾（说话人: %s）"
          % (tag, ",".join(sorted(speakers)) or "无台词"))
    return True


def fix(tag):
    p = os.path.join(SEG, "%s_prompt.txt" % tag)
    s = io.open(p, encoding="utf-8").read()
    speakers = set(re.findall(r"(小唐|苏小满|钱经理) \(S\d\) speaks", s))
    b = seg_bounds(s)
    n = 0
    for w in speakers:
        if w not in b:
            continue
        a, z = b[w]
        seg = s[a:z]
        new = seg
        for c in CLOSED:
            # 只删这一处，后面紧跟分号或逗号的
            new = re.sub(r"[^,;]*?" + re.escape(c) + r"[^,;]*?[;,]?\s*",
                         "", new, count=1)
        if new != seg:
            s = s[:a] + new + s[z:]
            b = seg_bounds(s)
            n += 1
            print("   %s 已删 %s 的闭嘴描写" % (tag, w))
    io.open(p, "w", encoding="utf-8").write(s)
    print("[%s] 改了 %d 处" % (tag, n))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fix":
        for t in sys.argv[2:]:
            fix(t)
        print()
    ok = True
    tags = sys.argv[2:] if (len(sys.argv) > 2 and sys.argv[1] == "fix") \
        else sys.argv[1:]
    for t in (tags or ["seg%02d" % i for i in range(1, 9)]):
        if os.path.exists(os.path.join(SEG, "%s_prompt.txt" % t)):
            ok = check(t) and ok
    print()
    print("全部通过" if ok else "⛔ 有片自相矛盾 → 出片会散人/不出声")
    sys.exit(0 if ok else 1)