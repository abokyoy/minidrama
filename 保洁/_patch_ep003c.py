# -*- coding: utf-8 -*-
"""ep003 补丁 C：柔化「门洞一片黑」的措辞。
3-1 门楼下明令是「bright and airy 的上午」，但脚本里把门洞反复写成 the black/dark doorway，
H3 会照着把门洞（画面纵深里最大的一块面积）拍成死黑，抵消掉曝光锚点。
改成「深门洞 / 门洞深处的暗影」——纵深信息保留，但不给曝光下指令。
（t78 的「dark red shawl 暗红色披肩」和 t160 的「the black of night 窗外夜色」是误报，不动。）
"""
import os, json
BASE = os.path.dirname(os.path.abspath(__file__))
MAP = [
 ("the dark doorway",           "the deep doorway"),
 ("the black doorway",          "the deep doorway"),
 ("the black of the doorway",   "the deep shade of the doorway"),
 ("into the dark gateway",      "into the deep gateway"),
]
tot = 0
for f in ("scene31.json", "scene32.json"):
    p = os.path.join(BASE, "ep003_beats", f)
    raw = open(p, encoding="utf-8").read()
    for a, b in MAP:
        c = raw.count(a)
        if c:
            raw = raw.replace(a, b); tot += c
            print("  %s  %-26s -> %-30s x%d" % (f, a, b, c))
    json.loads(raw)
    open(p, "w", encoding="utf-8").write(raw)
print("补丁 C：共替换 %d 处" % tot)
