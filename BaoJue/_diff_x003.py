# -*- coding: utf-8 -*-
"""X003 终版剧本 vs 旧 ep001.md 台词逐条比对
目的：新剧本场次 1-1 与旧 ep001 场次 1-2 是同一场戏（办公室搜卡），
要确认「台词是否一字未改」，从而决定是复用旧分镜还是重建。
"""
import re, io, sys, difflib
sys.stdout.reconfigure(encoding="utf-8")

NEW = r"E:\LLM\try\minidrama\终版剧本\X003_终版.md"
OLD = r"E:\LLM\try\minidrama\保洁\ep001.md"


def lines_of(path):
    t = io.open(path, encoding="utf-8").read()
    out = []
    for ln in t.split("\n"):
        m = re.match(r"^\*\*([^*]+)\*\*(.*)$", ln.strip())
        if m:
            who = m.group(1)
            rest = re.sub(r"^（[^）]*）", "", m.group(2))
            rest = rest.lstrip("：:").strip()
            if rest:
                out.append((who, rest))
    return out


new_all = lines_of(NEW)
old_all = lines_of(OLD)

# X003 场次 1-1 切片
t = io.open(NEW, encoding="utf-8").read()
a = t.index("### 场次1-1")
b = t.index("### 场次1-2")
s11 = lines_of_t = []
for ln in t[a:b].split("\n"):
    m = re.match(r"^\*\*([^*]+)\*\*(.*)$", ln.strip())
    if m:
        rest = re.sub(r"^（[^）]*）", "", m.group(2))
        rest = rest.lstrip("：:").strip()
        if rest:
            s11.append((m.group(1), rest))

# 旧 ep001 场次 1-2 切片
to = io.open(OLD, encoding="utf-8").read()
ao = to.index("### 场次1-2")
bo = to.index("### 场次1-3")
o12 = []
for ln in to[ao:bo].split("\n"):
    m = re.match(r"^\*\*([^*]+)\*\*(.*)$", ln.strip())
    if m:
        rest = re.sub(r"^（[^）]*）", "", m.group(2))
        rest = rest.lstrip("：:").strip()
        if rest:
            o12.append((m.group(1), rest))

print("X003 场次1-1 台词 %d 条" % len(s11))
print("旧 ep001 场次1-2 台词 %d 条" % len(o12))
print("=" * 70)

fn = ["%s：%s" % x for x in s11]
fo = ["%s：%s" % x for x in o12]
same = 0
for line in difflib.unified_diff(fo, fn, "旧1-2", "X003_1-1", lineterm="", n=0):
    if line.startswith(("+++", "---", "@@")):
        print(line)
    elif line.startswith("-"):
        print("  旧有/新无: " + line[1:])
    elif line.startswith("+"):
        print("  新增  : " + line[1:])
    else:
        same += 1
print("=" * 70)
print("完全一致台词条数: %d / 新 %d" % (same, len(fn)))
