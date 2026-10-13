# -*- coding: utf-8 -*-
"""seg06/07/08 的subject_definitions 与 retention_analysis 是从**病房那条线**复制来的：
  -人物编号反了（Subject 1 = 苏小满，而seg01~05 是 钱经理）
  - 服装描述完全不同（「浅色衬衫 + 灰围裙」vs 正片的「白衬衫黑马甲 / 深藏青制服+灰围裙 / 浅灰制服」）
  - summary 还留着「Each picture supplies one face only」（病房那条线的口径）
→ 直接跑等于演员换装换人。镜头段本身是好的，只换身份块。
⛔ 整串精确替换，不用正则（正则改镜头段=拦腰截断）。
"""
import io
import os
import sys

SEG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xs001_segs")

# seg01~05 的正确口径，逐字复用
GOOD_HEADER = """subject_definitions:
<Subject 1> — 钱经理: a 45-year-old male property manager. Slightly overweight, slicked-back oily hair, round face, an ingratiating smile that flips into a scowl, white shirt buttoned to the closed collar under a dark grey buttoned waistcoat, dark grey trousers, black leather shoes. His voice is loud, nasal and bullying, standard Mandarin. It is the person shown in <Picture 1>.
<Subject 2> — 苏小满: a 25-year-old female cleaner. Preserve her exact face, small lean build, centre-parted black hair in a low practical ponytail, plain dark-navy button-up work shirt buttoned to the closed collar with small plain buttons down the front, a worn grey apron over dark navy trousers, black cloth shoes. Her voice is low, steady and slightly hoarse, standard Mandarin. It is the person shown in <Picture 2>.
<Subject 3> — 小唐: a 22-year-old female cleaning-team colleague. Thin, pale, narrow shoulders, shifty sidelong eyes, hair tied back in a low ponytail, light-grey button-up work shirt with a pointed collar and matching light-grey trousers, a light-grey apron tied round her waist, black cloth shoes. Her voice is small, thin and nervous. It is the person shown in <Picture 3>.
<Picture 4>: the office layout reference for 万山大厦 — this same single room is the set for the whole clip. Light-oak storage cabinets along the back-left wall with plain brown cardboard boxes stacked on top; a low wooden credenza under the back window with a printer, files and two potted green plants; an L-shaped wooden office desk with a black monitor, keyboard and document tray in the middle of the room, a black swivel chair pushed in; a grey fabric sofa with wooden armrests and a low wooden coffee table under the long window on the right; an open doorway with a grey metal frame on the left. Pale grey polished tile floor, white acoustic ceiling with recessed light panels.
"""

GOOD_RETENTION = """retention_analysis:
<Subject 1> — 钱经理: fully_preserved - slicked-back oily hair, round face, dark grey buttoned waistcoat over a white shirt
<Subject 2> — 苏小满: fully_preserved - centre-parted black hair in a low practical ponytail, dark navy work shirt, worn grey apron
<Subject 3> — 小唐: fully_preserved - hair in a low ponytail, light-grey work shirt, light-grey apron
<Picture 4>: fully_preserved - light-oak cabinets, L-shaped desk, grey sofa on the right, doorway on the left
"""

GOOD_SUMMARY = ("summary:\n[reference generation] The manager accuses the cleaner of "
                "stealing a customer's gold earring and orders her to empty her pockets; "
                "she refuses and backs away from the desk; the colleague by the sofa "
                "watches without moving.\n")

# 病房线遗留串→ 正片口径
REPL = [
    ("summary:\n[reference generation] In a small private office a manager accuses a "
     "cleaner of stealing a customer's earring and forces her to empty her pockets, while "
     "a colleague watches from the back wall and then speaks up. Each picture supplies one "
     "face only.\n", GOOD_SUMMARY),
    # 曝光/按钮描述统一（病房线是 a large window，正片是 long right-hand window）
    ("Exposure: a large window is the key light and the room is filled with soft bounced "
     "daylight. Skin tones are bright and even, shadows sit in the light mid-tones and keep "
     "visible texture, the whites stay white, and the picture carries an even, transparent, "
     "high-key brightness from edge to edge.",
     "Exposure: the long right-hand window is the key light and soft bounced daylight fills "
     "the room; skin tones are bright and even, shadows sit in the light mid-tones, the "
     "whites stay white, and the picture carries an even high-key brightness from edge to "
     "edge."),
    ("Every shirt is buttoned right up to the closed collar, so each chest shows one "
     "unbroken run of plain fabric with small plain buttons. Apron bibs are plain.",
     "Every shirt and waistcoat is buttoned right up to the closed collar, so each chest "
     "shows one continuous unbroken run of plain fabric with its own small plain buttons down "
     "the front. Apron bibs are plain unmarked fabric."),
]


def fix(name):
    path = os.path.join(SEG_DIR, name + "_prompt.txt")
    t = io.open(path, encoding="utf-8").read()
    orig = t
    rep = []

    # 1. 换身份块：从 "subject_definitions:" 到第一个 "<Picture 4>" 行结束
    i = t.index("subject_definitions:")
    j = t.index("summary:")
    t = t[:i] + GOOD_HEADER + "\n" + t[j:]
    rep.append("身份块→正片口径")

    # 2. 换 retention 块
    i = t.index("retention_analysis:")
    j = t.index("detailed_description:")
    t = t[:i] + GOOD_RETENTION + "\n" + t[j:]
    rep.append("retention→正片口径")

    # 3. summary / exposure / 纽扣
    for old, new in REPL:
        if old in t:
            t = t.replace(old, new)
            rep.append("修:" + new[:24])

    if t != orig:
        io.open(path, "w", encoding="utf-8", newline="\n").write(t)
    return rep


def main():
    for sid in (6, 7, 8):
        name = "seg%02d" % sid
        print("[%s] %s" % (name, " / ".join(fix(name))))
    # 自检
    print()
    bad = 0
    for sid in range(1, 9):
        name = "seg%02d" % sid
        t = io.open(os.path.join(SEG_DIR, name + "_prompt.txt"), encoding="utf-8").read()
        errs = []
        if "<Subject 1> — 钱经理" not in t:
            errs.append("Subject1 不是钱经理")
        if "Each picture supplies one face only" in t:
            errs.append("病房线summary 残留")
        if "a plain pale shirt under a grey work apron" in t:
            errs.append("病房线服装 残留")
        for k in ("VERTICAL 9:16", "The count does not change", "the only people in it",
                  "back to the camera", "near end", "far left of frame",
                  "filing cabinet", "grey metal filing"):
            if k in t:
                errs.append("残留:" + k)
        if "<Picture 4>:" not in t:
            errs.append("缺 Picture4")
        if errs:
            bad += 1
            print("[%s] ⛔ %s" % (name, errs))
        else:
            print("[%s] ✅" % name)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
