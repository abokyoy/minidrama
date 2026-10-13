# -*- coding: utf-8 -*-
"""校验 ep004 / ep005 的第①②步产物。不信任自述，逐项机器核对。"""
import re, io, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
BAN = ["昏暗", "万山", "退进阴影", "沉进暗处", "只有一小块亮着",
       "一片漆黑", "漆黑一片", "dark room", "the black doorway", "dimly lit"]
BADTXT = ["屏幕上显示", "手机上写着", "屏幕上打出", "显示着「", '屏幕上写着']

def lines_of(src):
    """从原剧本抽出 (角色, 台词) 序列"""
    out = []
    for ln in io.open(src, encoding="utf-8"):
        m = re.match(r"^\*\*(.+?)\*\*\s*(（[^）]*）)?\s*[:：]\s*(.+?)\s*$", ln.strip())
        if m:
            role = m.group(1).strip()
            note = (m.group(2) or "").strip()
            text = m.group(3).strip()
            out.append((role, note, text))
    return out

def check(ep):
    print("=" * 18, ep)
    src = os.path.join(BASE, ep + ".md")
    prose_p = os.path.join(BASE, ep, "文字剧本.md")
    con1 = os.path.join(BASE, ep, "连续脚本_part1.md")
    con2 = os.path.join(BASE, ep, "连续脚本_part2.md")
    for p in (prose_p, con1, con2):
        if not os.path.exists(p):
            print("  ✗ 缺文件:", p); return
    prose = io.open(prose_p, encoding="utf-8").read()
    # 1) 台词逐字 + 顺序
    dlg = lines_of(src)
    missing = [d for d in dlg if d[2] not in prose]
    print("  台词 %d 句，未逐字命中 %d 句" % (len(dlg), len(missing)))
    for d in missing[:8]: print("     ✗", d[0], d[2][:40])
    # 顺序
    pos, ok = -1, True
    for r, n, t in dlg:
        i = prose.find(t, pos + 1)
        if i < 0: ok = False; print("     ✗ 顺序乱:", t[:30]); break
        pos = i
    print("  顺序:", "OK" if ok else "✗")
    # 2) 禁用词
    hits = [w for w in BAN if w in prose]
    print("  禁用词:", hits if hits else "无")
    # 3) 会烧字幕的写法（全文，含连续脚本）
    allt = prose + io.open(con1, encoding="utf-8").read() + io.open(con2, encoding="utf-8").read()
    bh = [w for w in BADTXT if w in allt]
    print("  烧字幕写法:", bh if bh else "无")
    # 4) 文字剧本里台词行不许有引号
    q = [ln.strip() for ln in io.open(prose_p, encoding="utf-8")
         if re.match(r"^\*\*.+\*\*：", ln.strip()) and ("「" in ln or '"' in ln)]
    print("  文字剧本台词带引号:", len(q), "行", ("例:" + q[0][:50]) if q else "")
    # 5) 镜号连续性
    nums = []
    for p in (con1, con2):
        nums += [int(x) for x in re.findall(r"\*\*P(\d+)\*\*", io.open(p, encoding="utf-8").read())]
    print("  镜号 %d 个，范围 P%02d–P%02d" % (len(nums), min(nums), max(nums)),
          "| 连续:", "OK" if nums == list(range(1, len(nums) + 1)) else "✗ 有跳号/重复")
    # 6) 数字字段
    print("  行数：文字剧本 %d / 连续 part1 %d / part2 %d" % (
        len(io.open(prose_p, encoding="utf-8").readlines()),
        len(io.open(con1, encoding="utf-8").readlines()),
        len(io.open(con2, encoding="utf-8").readlines())))

for ep in ("ep004", "ep005"):
    check(ep)
