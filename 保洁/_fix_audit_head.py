# -*- coding: utf-8 -*-
"""把误占文件头的 helper 整块挪到 import 之后。"""
import io
import os
import py_compile

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_h3_audit.py")
txt = io.open(P, encoding="utf-8").read()
lines = txt.split("\n")

# helper 块：从第 0 行（注 释的 ═══）到 def audit_onetake 结束
# audit_onetake 结束 = 下一个顶层 def/空行组之前
i_start = 0
while i_start < len(lines) and (lines[i_start].startswith("#")
                               or lines[i_start].startswith("ONETAKE")
                               or not lines[i_start].strip()):
    i_start += 1
    if lines[i_start - 1].startswith("def audit_onetake"):
        break
# 更稳：直接定位
i_start = 0
for i, l in enumerate(lines):
    if l.startswith("ONETAKE_HEAD"):
        i_start = i
        break
#往上吃到 ═══ 注释头
while i_start > 0 and lines[i_start - 1].strip():
    i_start -= 1
while i_start > 0 and (lines[i_start - 1].startswith("#")
                       or not lines[i_start - 1].strip()):
    i_start -= 1

# 块尾：audit_onetake 函数体结束（下一个顶层 def）
i_end = None
for i in range(i_start, len(lines)):
    if lines[i].startswith("def words("):
        i_end = i
        break
assert i_end is not None
# 往上吃空行
while i_end - 1 > i_start and not lines[i_end - 1].strip():
    i_end -= 1

block = lines[i_start:i_end]
rest = lines[:i_start] + lines[i_end:]
print("搬走%d..%d 共 %d 行" % (i_start, i_end, len(block)))

# 插到 import 区之后（找到最后一个顶层 import 或常量赋值之前）
ins = 0
for i, l in enumerate(rest[:40]):
    if l.startswith("import ") or l.startswith("from ") or l.startswith("SECTIONS"):
        ins = i + 1
out = rest[:ins] + [""] + block + rest[ins:]
io.open(P, "w", encoding="utf-8").write("\n".join(out))
print("写回完成")
try:
    py_compile.compile(P, doraise=True)
    print("✅ 语法通过")
except Exception as e:
    print("‼", e)
    raise SystemExit(1)