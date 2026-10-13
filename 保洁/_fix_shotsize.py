# -*- coding: utf-8 -*-
"""⛔⛔⛔ 景别统一：每片所有刀锁回**第 1 刀的景别**。

**病根（2026-10-09 16:45 用户第五次打回实锤）**：
片1 明明 5 刀都写了 `Static Shot`，1.3 秒处还是硬切到近景 + 多出一个白衬衫男人。
逐帧核实：
```
t=1.0s ✅ 三人中远景    t=1.2s ✅ 还是三人
t=1.3s ❌ 近景 + 多一个白衬衫领带男 + 小唐消失
```
**根因**：`[Shot 1] medium-wide three-shot` 但 `[Shot 2] a medium shot of 钱经理`
—— 景别不同 = 模型重新构图 = 新构图里桌子旁有空位 = **模型补人填空**。

⭐ 关键认知：**写了 5 刀 `Static Shot` 也不等于一镜到底。**
景别（shot size）是独立于机位（camera move）的第二个维度，**必须逐字锁死**。

**修法**：把每片第 2 刀及以后的景别描述，整串替换成
`holding the exact same <第1刀景别> framing of shot 1 with the same three people in the same places`。

⛔ 铁律：**整串精确替换，禁止正则改写镜头段**（10-08 16:45 踩过拦腰截断）。
本脚本只用正则**定位和统计**，改写一律整串。
"""

import io
import re
import sys

BASE = "xs001_segs"

# 景别名 → 统一说法（只认这些，其余原样保留）
SIZE_PAT = (r"medium-wide three-shot|medium two-shot|medium three-shot|"
            r"medium close-up|medium shot|wide shot|two-shot|three-shot|"
            r"close-up|close single|reverse single|a single|single on")


def shot_lines(t):
    """⛔ 判镜头定义行必须「行首 + 带时间戳」，不能全文 findall
       （正文里 `From [Shot 4] through…` 这类跨镜句会带 [Shot N]，会被数错）"""
    return re.findall(r"^\[Shot \d\][^\n]*", t, re.M)


def first_size(t):
    m = re.search(r"^\[Shot 1\][^\n]*", t, re.M)
    if not m:
        return None
    mm = re.search(SIZE_PAT, m.group(0))
    return mm.group(0) if mm else None


def all_sizes(t):
    out = []
    for ln in shot_lines(t):
        mm = re.search(SIZE_PAT, ln)
        out.append(mm.group(0) if mm else None)
    return out


def fix(sid):
    p = "%s/seg%02d_prompt.txt" % (BASE, sid)
    t0 = io.open(p, encoding="utf-8").read()
    tgt = first_size(t0)
    if not tgt:
        return None, "第1刀没识别出景别", None
    # 统一锚句：每刀 Camera: 之后到「of 某人 / :」之前的景别部分全换掉
    t = t0
    n = 0
    for ln in t.split("\n"):
        if not re.match(r"^\[Shot [2-9]\]", ln):
            continue
        if tgt in ln:
            continue
        mm = re.search(SIZE_PAT, ln)
        if not mm:
            continue
        old = mm.group(0)
        new = "the exact same %s framing of shot 1" % tgt
        t = t.replace(old, new, 1)
        n += 1
    # 第1刀本身也把景别写死（模型才认这是锁）
    if tgt in t:
        t = t.replace("Camera: Static Shot, ", "Camera: Static Shot, locked off, ", 1) \
            if "Camera: Static Shot, " in t else t
    io.open(p, "w", encoding="utf-8").write(t)
    return tgt, n, all_sizes(t)


if __name__ == "__main__":
    sids = [int(x) for x in sys.argv[1:]] or list(range(1, 9))
    for sid in sids:
        tgt, n, after = fix(sid)
        if tgt is None:
            print("seg%02d  ❌ %s" % (sid, n))
            continue
        ok = all(s == tgt for s in after if s)
        print("seg%02d  锁定景别=%-22s 改写 %d 刀  %s"
              % (sid, tgt, n, "✅ 全部一致" if ok else "⚠ 剩余: %s" % after))
