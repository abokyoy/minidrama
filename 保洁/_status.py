# -*- coding: utf-8 -*-
"""看一眼当前状态：新成片画幅 / 旧产物 / manifest 与 state 的指纹是否一致。"""
import glob
import io
import json
import os
import struct

OUT = r"D:\output"
SEGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ep001_segs")


def png_size(p):
    with open(p, "rb") as f:
        d = f.read(33)
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", d[16:24])


print("== 当前成片 ==")
for p in sorted(glob.glob(os.path.join(OUT, "ep01_t*.png"))):
    print("  %-26s %s" % (os.path.basename(p), png_size(p)))

print("== _stale 里的旧产物（最近 6 个）==")
for p in sorted(glob.glob(os.path.join(OUT, "_stale", "*.png")))[-6:]:
    print("  %-40s %s" % (os.path.basename(p), png_size(p)))

man = json.load(io.open(os.path.join(SEGS, "manifest.json"), encoding="utf-8"))
st = json.load(io.open(os.path.join(SEGS, "state.json"), encoding="utf-8"))
print("== manifest vs state ==")
same = diff = 0
mismatch = []
for m in man:
    s = st.get(m["id"])
    if s and s.get("sha") == m["sha"]:
        same += 1
    else:
        diff += 1
        if s:
            mismatch.append(m["id"])
print("  指纹一致 %d 段；不一致/未生成 %d 段" % (same, diff))
print("  不一致的段：", mismatch[:12], "..." if len(mismatch) > 12 else "")
