# -*- coding: utf-8 -*-
"""修复 _h3_audit.py：helper 被误插进 audit() 体内，搬回顶层。"""
import io
import os
import py_compile

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_h3_audit.py")
lines = io.open(P, encoding="utf-8").read().split("\n")

# 找 helper 块：从「一镜到底（ONE CONTINUOUS TAKE）专用判据集」那行开始
i0 = None
for i, l in enumerate(lines):
    if "一镜到底（ONE CONTINUOUS TAKE）专用判据集" in l:
        i0 = i - 1              # 上一行是注释块起点
        break
assert i0 is not None, "找不到 helper 块起点"
# 往上吃掉紧挨着的 # ══ 注释行
while i0 > 0 and lines[i0 - 1].strip().startswith("#"):
    i0 -= 1

# helper 块结束：从 i0 往下找到 "def chk(cond, good, why):" 这一行
i1 = None
for i in range(i0, len(lines)):
    if lines[i].startswith("def chk(cond, good, why):"):
        i1 = i
        break
assert i1 is not None, "找不到 def chk"
# 往上吃掉 chk 前的空行
while i1 - 1 > i0 and lines[i1 - 1].strip() == "":
    i1 -= 1

block = lines[i0:i1]
print("搬走 %d 行（%d..%d）" % (len(block), i0, i1))

# 抽掉块，把剩下拼起来；def chk 恢复成 audit 内的局部函数
rest = lines[:i0] + lines[i1:]

# helper 里的行首有 3 级缩进的错位（原本按顶层写但插进了函数里）——
# 现在搬到顶层，把公共行统一降 4 空格
norm = []
for l in block:
    if l.startswith("#"):
        norm.append(l.lstrip("#")[:0] + l) if False else norm.append(l)
    else:
        norm.append(l)

# 去掉 helper 内部所有行尾多出的缩进差异：按最小缩进对齐
body = [l for l in norm if l.strip()]
min_ind = min(len(l) - len(l.lstrip()) for l in body) if body else 0
fixed = []
for l in norm:
    if not l.strip():
        fixed.append("")
    else:
        fixed.append(l[min_ind:] if len(l) - len(l.lstrip()) >= min_ind else l)

out = "\n".join(fixed + ["", ""] + rest)
io.open(P, "w", encoding="utf-8").write(out)
print("写回完成")
try:
    py_compile.compile(P, doraise=True)
    print("✅ 语法通过")
except Exception as e:
    print("‼ 仍报错：", e)