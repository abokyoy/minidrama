# -*- coding: utf-8 -*-
"""⛔⛔⛔ 2026-10-09 14:35 用户打回 seg04：「为啥隔着百叶窗」。

现象：成片 f0004–f0013 整个画面是横条纹，脸被切掉，码率只有 1.19M（正常 4M）。

根因：提示词里到处写 `blind-light` / `the blind-laying light barring the wall behind her`
/ `the blind-light band runs across his waistcoat`。
「barred across」「band」这类词+「blind」被模型理解成**镜头前面横着一排百叶窗**，
而不是「光斑投在墙上」。→ 同一批词在seg01~03 只是「脸上有光斑」（侥幸没糊），
到 seg04「barred」直接触发成遮挡。

修法：**全七段把 blind 相关措辞统一换成 `a band of daylight` / `plain pale wall`**。
- `blind-light band crosses his chest` → `a band of daylight crosses his chest`
- `the blind-laying light barring the wall behind her` → `a plain pale wall behind her`
- `his collar catches the blind-light` → `his collar catches the daylight`
- `the blind-light band runs across his waistcoat` → `a band of daylight crosses his waistcoat`
- `the blind-light band passes over her collar` → `a band of daylight crosses her collar`

⛔ 全部整串精确替换，禁止正则（正则改镜头段=拦腰截断，seg03 惨案）。
⛔ 顺带加一条审计：`blind` 出现在镜头段就报红。
"""
import io
import os
import sys

SEG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xs001_segs")

# 顺序敏感：长串在前，避免短串先吃掉长串的一半
REPL = [
    ("the blind-laying light barring the wall behind her",
     "a plain pale wall behind her"),
    ("the blind-laying light barring the wall behind him",
     "a plain pale wall behind him"),
    ("blind-light barring the wall behind her",
     "a plain pale wall behind her"),
    ("the blind-light band runs across his waistcoat",
     "a band of daylight crosses his waistcoat"),
    ("the blind-light band passes over her collar",
     "a band of daylight crosses her collar"),
    ("a band of blind-light crosses his chest",
     "a band of daylight crosses his chest"),
    ("a band of blind-light crosses his open hand",
     "a band of daylight crosses his open hand"),
    ("his collar catches the blind-light",
     "his collar catches the daylight"),
    ("a band of blind-light runs across his cheekbone",
     "a band of daylight crosses his cheekbone"),
    ("the paper's crease catches the blind-light",
     "the paper's crease catches the daylight"),
    ("the blind-light",
     "the daylight"),
    ("blind-light",
     "daylight"),
]


def fix(name):
    path = os.path.join(SEG_DIR, name + "_prompt.txt")
    t = io.open(path, encoding="utf-8").read()
    orig = t
    hits = []
    for old, new in REPL:
        n = t.count(old)
        if n:
            t = t.replace(old, new)
            hits.append("%s x%d" % (old[:34], n))
    if t != orig:
        io.open(path, "w", encoding="utf-8", newline="\n").write(t)
    return hits


def main():
    for sid in range(1, 9):
        name = "seg%02d" % sid
        hits = fix(name)
        print("[%s] %s" % (name, " / ".join(hits) if hits else "无blind 措辞"))

    # 自检：全八段不许再有 blind
    print()
    bad = 0
    for sid in range(1, 9):
        name = "seg%02d" % sid
        t = io.open(os.path.join(SEG_DIR, name + "_prompt.txt"),
                    encoding="utf-8").read()
        low = t.lower()
        errs = []
        if "blind" in low:
            errs.append("blind 残留")
        if "barring" in low or "barred " in low:
            errs.append("barred/barring 残留")
        # 台词归属：每个 [Chinese] 前 300 字符必须点名说话人
        for m in __import__("re").finditer(r"\[Chinese\]", t):
            head = t[max(0, m.start() - 300):m.start()]
            if not any(k in head for k in ("苏小满 (S1)", "钱经理 (S3)", "小唐 (S4)")):
                errs.append("有台词没点名说话人")
                break
        # Shot 编号不许重复。
        # ⛔ 只认行首的镜头定义行 `^\[Shot N\]`：
        #   正文里有 "From [Shot 4] through [Shot 6] the only mouth movement…" 这种
        #   跨镜提示句，里面也带 [Shot N] —— 用全文 findall 会误报成「编号重复」
        #   （实测八段全被误报）。判重要求该行同时含 "At 00:" 时间戳。
        nums = [x for x in __import__("re").findall(
            r"^\[Shot (\d+)\] At 00:", t, __import__("re").M)]
        if len(nums) != len(set(nums)):
            errs.append("Shot 编号重复:%s" % nums)
        if nums and nums != sorted(nums, key=int):
            errs.append("Shot 编号非递增:%s" % nums)
        if errs:
            bad += 1
            print("[%s] ⛔ %s" % (name, errs))
        else:
            print("[%s] ✅" % name)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
