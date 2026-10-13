# -*- coding: utf-8 -*-
"""⛔⛔⛔ 2026-10-09 15:55 用户第三次打回后的批量修正：对话戏一镜到底。

**用户原话**：
> 「现在我对 片1 2 3 都有意见 镜头切换 拉近 左切 右切 太频繁了 看的人头晕
>   三个片都要重新做 不要大幅度拉 推 切 太晕了」

**病根（不是「晃动」，是「动」）**：
之前的审计器只禁了 whip pan / tracking / arc 三类，**放过了 Push In / Pull Out / Truck**，
因为 10-08 那次用户说过「还可以」。这次用户把尺度改了：**不动就不晕**。

实测数据：片1/2/3 每片 6 刀里 3 刀在动，且**全是 fast speed**，切点 1.25 秒
→ 每 1.25 秒画面就晃一次，6 刀晃 3 次，必晕。

**修法**：
  ① 每片所有 `Camera: Push In / Pull Out / Truck L/R` → `Static Shot, locked off`
  ② 每片加一句全局约束：camera locked off / framing never changes
  ③ 保留「谁在哪、谁开口、嘴闭着」这些正片信息不动（只动相机，不动内容）

⛔⛔⛔ 铁律：**整串精确替换，禁止正则改写镜头段**
   （10-08 16:45 踩过：用正则批量改镜头段 → 只吃到第一个句点 → 句子拦腰截断
     → 缺主语 → 模型当成"特写脸部"指令 → 连续四刀同一张脸 → 越推越透明）
"""

import io
import re
import sys

BASE = "xs001_segs"

# ── ① 逐条整串替换表（长的在前，防吃掉半句）──────────────────────────
# 每条 = (原文, 新文)。原文必须**逐字**来自文件，否则不替换（并在报告里点名）。
REPL = []

# Shot 2: Push In with small amplitude at fast speed, pushing in on
REPL += [
    ("Camera: Push In with small amplitude at fast speed, pushing in on 钱经理 (S1) as he",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement, 钱经理 (S1) as he"),
    ("Camera: Push In with small amplitude at fast speed, pushing in on 钱经理 (S1)'s hand as it",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement, 钱经理 (S1)'s hand as it"),
    ("Camera: Push In with small amplitude at fast speed, pushing in on 钱经理 (S1)'s face as",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement, 钱经理 (S1)'s face as"),
]

# Shot 3: Truck Right with medium amplitude at fast speed, sliding sideways ...
REPL += [
    ("Camera: Truck Right with medium amplitude at fast speed, sliding sideways across the desk to a reverse single on 苏小满 (S2)",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement, 苏小满 (S2) still at the near left corner of the desk in right profile"),
    ("Camera: Truck Right with medium amplitude at fast speed, sliding sideways across the desk to a profile two-shot:",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement, the profile two-shot:"),
]

# Shot 5: Truck Left / Truck Right
REPL += [
    ("Camera: Truck Left with medium amplitude at fast speed, sliding sideways and settling on 钱经理 (S1) from the chest up",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement, 钱经理 (S1) behind the desk seen from the chest up"),
    ("Camera: Truck Left with medium amplitude at fast speed, sliding sideways to a single on 小唐 (S3) alone in the frame",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement and without cutting to a closer view, 小唐 (S3) beside the grey sofa at the right of frame"),
    ("Camera: Truck Right with medium amplitude at fast speed, sliding sideways and settling on",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement on"),
]

# Shot 6: Pull Out with large amplitude at slow speed
REPL += [
    ("Camera: Pull Out with large amplitude at slow speed, pulling out to the full room:",
     "Camera: Static Shot, locked off, holding the full room in the same wide frame without any camera movement:"),
    ("Camera: Pull Out with large amplitude at slow speed, pulling out to reveal the whole office as",
     "Camera: Static Shot, locked off, holding the whole office in the same wide frame without any camera movement as"),
    ("Camera: Pull Out with large amplitude at slow speed, pulling out to reveal the whole office and",
     "Camera: Static Shot, locked off, holding the whole office in the same wide frame without any camera movement and"),
    ("Camera: Pull Out with large amplitude at slow speed, pulling out to reveal",
     "Camera: Static Shot, locked off, holding the same wide frame without any camera movement to reveal"),
]

# ⛔ 第一轮跑完脚本自报 6 处没命中 —— 说明这些镜头原文各不相同。
#    逐条按**实际原文**补（不是猜），补完再跑一遍。已改过的串不再命中，天然幂等。
REPL += [
    ("Camera: Truck Right with medium amplitude at fast speed, sliding sideways across to a closer single on 苏小满 (S2)",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement, 苏小满 (S2) still at the near left corner of the desk in right profile"),
    ("Camera: Truck Left with medium amplitude at fast speed, sliding sideways across the desk and settling on the unfol",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement on the unfol"),
    ("Camera: Truck Left with medium amplitude at fast speed, sliding sideways toward the back wall to a closer single o",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement and without cutting closer, the single o"),
    ("Camera: Truck Right with medium amplitude at fast speed, sliding sideways toward the back wall and settling on 钱经理",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement, 钱经理"),
    ("Camera: Push In with small amplitude at fast speed, pushing in on 小唐 (S3)'s face as she",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement, 小唐 (S3) beside the grey sofa at the right of frame as she"),
    ("Camera: Truck Left with medium amplitude at fast speed, sliding sideways back toward the desk to a closer single o",
     "Camera: Static Shot, locked off, holding the same frame without any camera movement, the single o"),
]

# ② 全局约束（插在 exposure 行的 "People stay standing, framed from the knees up." 之后）
ANCHOR = "People stay standing, framed from the knees up."
LOCK = (ANCHOR + " The camera is locked off for the whole clip: the framing never changes "
        "and the size of everything in frame stays the same from the first frame to the last. "
        "All movement comes from the people inside the fixed frame.")


def fix(sid):
    p = "%s/seg%02d_prompt.txt" % (BASE, sid)
    t0 = io.open(p, encoding="utf-8").read()
    t = t0
    hits = []
    for old, new in REPL:
        if old in t:
            n = t.count(old)
            t = t.replace(old, new)
            hits.append((old[:46], n))
    # 全局约束
    if "The camera is locked off for the whole clip" not in t:
        if ANCHOR in t:
            t = t.replace(ANCHOR, LOCK, 1)
            hits.append(("+全局相机锁定约束", 1))
        else:
            hits.append(("!!没找到锚点，全局约束没插进去", 0))
    # 正文里重复的否定罗列（省词数）
    t = t.replace(" The camera is locked off and does not move, push, swing, or travel in this beat.", "", 1)
    io.open(p, "w", encoding="utf-8").write(t)
    # 自检
    left = re.findall(r"Camera:\s*(Push In|Pull Out|Truck [A-Za-z]+|"
                      r"Tracking Shot|Arc Shot|Whip Pan|Pan Left|Pan Right|Tilt)",
                      t)
    return len(t0), len(t), hits, left


if __name__ == "__main__":
    sids = [int(x) for x in sys.argv[1:]] or [1, 2, 3, 4, 5, 6, 7, 8]
    bad = 0
    for sid in sids:
        a, b, hits, left = fix(sid)
        print("seg%02d  %d -> %d 字符" % (sid, a, b))
        for h, n in hits:
            print("     ×%d  %s" % (n, h))
        if left:
            bad += 1
            print("     ❌ 残留动镜头: %s" % left)
        else:
            print("     ✅ 全部静止机位")
    sys.exit(1 if bad else 0)
