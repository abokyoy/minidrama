# -*- coding: utf-8 -*-
"""把 seg02~07 的三个病根一次性改掉。⛔ 全部用「整串精确替换」，不用正则，
正则批量改写镜头段会拦腰截断（seg03 惨案）。
病根：
 1. 「The count does not change / exactly three people / the only people in it」
    = 反复念叨「人、人数、唯一」→ 模型多画人（两个小唐）
 2. 房间描述写的是「灰铁文件柜 + 平嵌木门」，实际 P4 是
    「浅木柜 + L 形办公桌 + 右侧灰沙发 + 左侧门洞」→ 拼凑房间
 3. 「with her back to the camera」模型 hold 不住，会画成正面 → 改明确侧身
"""
import io
import os
import sys

SEG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xs001_segs")

# ---------- 1. 房间描述：换成与 P4 逐字一致的版本 ----------
OLD_ROOM_VARIANTS = [
    # seg02
    ("The whole clip takes place in one small private office and the camera never leaves it. "
     "The room has four plain white walls, a grey metal filing cabinet along the far wall, "
     "a long wooden desk standing across the middle of the floor, venetian blinds on the "
     "right-hand wall laying bright bands across the desk top, and a closed wooden door set "
     "flat into the back wall. The walls behind the people are smooth painted plaster of one "
     "single light colour, unbroken from the skirting board up to the ceiling. All cardboard "
     "boxes and folders are plain brown corrugated cardboard. The people named in this beat "
     "are the only people in it: the manager stays behind the desk on the far side, the "
     "cleaner stays at the near end of it with her back to the camera, and the colleague "
     "stands where this beat places her. The count does not change."),
    # seg03
    ("The whole clip takes place in one small private office and the camera never leaves it: "
     "four plain white walls, a long wooden desk across the middle, venetian blinds on the "
     "right-hand wall laying bright bands across the desk top, and a closed wooden door set "
     "flat into the back wall. The count does not change."),
    # seg04 / seg05
    ("The whole clip takes place in one small private office and the camera never leaves it: "
     "four plain white walls, a grey metal filing cabinet along the far wall, a long wooden "
     "desk across the middle, venetian blinds on the right-hand wall laying bright bands "
     "across the desk top, and a closed wooden door set flat into the back wall. The people "
     "named in this beat are the only people in it: 钱经理 (S3) behind the desk on the far "
     "side, 苏小满 (S1) at the near end of it with her back to the camera, and 小唐 (S4) "
     "clear at the far left of frame near the back wall. The count does not change."),
    # seg06 / seg07（没有房间句，只有站位句）
    ("The people named in this beat are the only people in it: 钱经理 (S3) behind the desk "
     "on the far side, 苏小满 (S1) at the near end of it with her back to the camera, and "
     "小唐 (S4) clear at the far left of frame near the back wall. The count does not change."),
]

NEW_ROOM = (
    "The whole clip takes place in the one office shown in <Picture 4>, and the three of them "
    "hold these same standing places from the first frame to the last: 钱经理 (S3) behind the "
    "L-shaped desk in the middle of the room, three-quarters to the camera; 苏小满 (S1) at the "
    "near left corner of that desk in right profile facing right towards him, both feet flat "
    "on the tile; 小唐 (S4) on the right side of the room beside the grey sofa in left profile, "
    "facing left towards the desk."
)

PICTURE4_LINE = (
    "<Picture 4>: the office layout reference for 万山大厦 — this same single room is the set "
    "for the whole clip. Light-oak storage cabinets along the back-left wall with plain brown "
    "cardboard boxes stacked on top; a low wooden credenza under the back window with a "
    "printer, files and two potted green plants; an L-shaped wooden office desk with a black "
    "monitor, keyboard and document tray in the middle of the room, a black swivel chair "
    "pushed in; a grey fabric sofa with wooden armrests and a low wooden coffee table under "
    "the long window on the right; an open doorway with a grey metal frame on the left. Pale "
    "grey polished tile floor, white acoustic ceiling with recessed light panels."
)

# ---------- 2. 「人数/唯一」类否定串 → 直接删 ----------
DELETE_STRINGS = [
    " The count does not change.",
    " exactly three people:",
    ", exactly three people",
    " The count does not change",
]

# ---------- 3. 「back to the camera」→ 明确侧身 ----------
BACK_TO_CAMERA_FIX = [
    ("苏小满 (S1) at the near end with her back to the camera",
     "苏小满 (S1) at the near left corner of the desk in right profile facing right"),
    ("苏小满 (S1) at the near end of it with her back to the camera",
     "苏小满 (S1) at the near left corner of that desk in right profile facing right"),
    ("苏小满 (S1) at the near end with her back to the camera in dark navy",
     "苏小满 (S1) at the near left corner of the desk in right profile in dark navy"),
    ("苏小满 (S1) at the near end of the desk with her back to the camera, taller, in dark navy with a low ponytail",
     "苏小满 (S1) at the near left corner of the desk in right profile facing right, taller, in dark navy with a low ponytail"),
    ("苏小满 (S1) still at the near end with her back to the camera",
     "苏小满 (S1) still at the near left corner of the desk in right profile"),
    ("苏小满 (S1) at the near end with her back to the camera, taller, in dark navy with a low ponytail",
     "苏小满 (S1) at the near left corner of the desk in right profile, taller, in dark navy with a low ponytail"),
]

# 其它「far left of frame / on the open floor」也要归位到沙发边
POSITION_FIX = [
    ("小唐 (S4) against the back wall at the far left of frame, waiting",
     "小唐 (S4) beside the grey sofa at the right of frame in left profile, waiting"),
    ("小唐 (S4) clear at the far left of frame near the back wall",
     "小唐 (S4) beside the grey sofa at the right of frame in left profile"),
    ("小唐 (S4) clear at the far left of frame in light grey",
     "小唐 (S4) beside the grey sofa at the right of frame in light grey"),
    ("小唐 (S4) clear at the left of frame",
     "小唐 (S4) beside the grey sofa at the right of frame"),
    ("小唐 (S4) on the open floor beside it",
     "小唐 (S4) beside the grey sofa at the right of frame"),
    ("小唐 (S4) on the open floor at the left of frame in light grey",
     "小唐 (S4) beside the grey sofa at the right of frame in light grey"),
    ("小唐 (S4) on the open floor.",
     "小唐 (S4) beside the grey sofa at the right of frame."),
    ("钱经理 (S3) behind the desk in white shirt and dark grey waistcoat;",
     "钱经理 (S3) behind the L-shaped desk in white shirt and dark grey waistcoat;"),
    ("钱经理 (S3) behind the desk on the far side in white shirt and dark grey waistcoat;",
     "钱经理 (S3) behind the L-shaped desk in white shirt and dark grey waistcoat;"),
    ("钱经理 (S3) behind the desk on the far side in white shirt and dark grey waistcoat",
     "钱经理 (S3) behind the L-shaped desk in white shirt and dark grey waistcoat"),
    ("钱经理 (S3) on the far side with the filing cabinets behind his back, one palm flat on the wood;",
     "钱经理 (S3) behind the L-shaped desk in front of the light-oak cabinets, one palm flat on the wood;"),
    ("钱经理 (S3) on the far side with one palm flat on the wood;",
     "钱经理 (S3) behind the L-shaped desk with one palm flat on the wood;"),
    ("钱经理 (S3) on the far side of the desk",
     "钱经理 (S3) behind the L-shaped desk"),
    ("钱经理 (S3) behind the desk",
     "钱经理 (S3) behind the L-shaped desk"),
    ("钱经理 (S3) on the far side",
     "钱经理 (S3) behind the L-shaped desk"),
    ("钱经理 (S3) on the far side unfolds the paper flat on the wood",
     "钱经理 (S3) behind the L-shaped desk unfolds the paper flat on the wood"),
    ("钱经理 (S3) on the far side of it across the wood from her",
     "钱经理 (S3) behind the L-shaped desk across the wood from her"),
    ("钱经理 (S3) on the far side and 苏小满 (S1) at the near end with her back to the camera",
     "钱经理 (S3) behind the L-shaped desk and 苏小满 (S1) at the near left corner in right profile"),
    ("钱经理 (S3) still bearing down behind the desk",
     "钱经理 (S3) still bearing down behind the L-shaped desk"),
    ("a closed wooden door set flat into the back wall",
     "an open doorway with a grey metal frame on the left"),
    # ---- 第二轮补刀：残留词逐个精确换 ----
    ("苏小满 (S1) at the near end", "苏小满 (S1) at the near left corner of the desk in right profile"),
    ("苏小满 (S1) still at the near end", "苏小满 (S1) still at the near left corner of the desk"),
    ("clear at the far left of frame near the back wall",
     "beside the grey sofa at the right of frame in left profile"),
    ("on the open floor beside it", "beside the grey sofa at the right of frame"),
    ("on the open floor at the left of frame", "beside the grey sofa at the right of frame"),
    ("小唐 (S4) on the open floor", "小唐 (S4) beside the grey sofa at the right of frame"),
]

# retention_analysis 里 <Picture 4> 那一行（seg02~07 原本没有 Picture 4）
RETENTION_ADD = "<Picture 4>: fully_preserved - light-oak cabinets, L-shaped desk, grey sofa on the right, doorway on the left"


def fix_segment(name):
    path = os.path.join(SEG_DIR, name + "_prompt.txt")
    with io.open(path, encoding="utf-8") as f:
        t = f.read()
    orig = t
    report = []

    # 1. 房间/站位句
    room_hit = False
    for old in OLD_ROOM_VARIANTS:
        if old in t:
            t = t.replace(old, NEW_ROOM)
            room_hit = True
            report.append("room->P4一致版")
            break
    if not room_hit:
        report.append("!! 房间句没命中，需手工看")

    # 2. 插 <Picture 4> 到 subject_definitions 末尾
    #    ⛔ 判据要用 "<Picture 4>:"（定义行），不能用 "<Picture 4>"——
    #    房间句里已经含这个字符串，用后者会永远判"已存在"→ 永远插不进去
    if "<Picture 4>:" not in t:
        lines = t.split("\n")
        for i, ln in enumerate(lines):
            if ln.startswith("summary:"):
                lines.insert(i, PICTURE4_LINE)
                lines.insert(i + 1, "")
                break
        t = "\n".join(lines)
        report.append("+Picture4定义")
        # retention 也要加一行
        lines = t.split("\n")
        for i, ln in enumerate(lines):
            if ln.startswith("detailed_description:"):
                # 往上找 retention_analysis 段的最后一行
                j = i - 1
                while j > 0 and lines[j].strip() == "":
                    j -= 1
                lines.insert(j + 1, RETENTION_ADD)
                break
        t = "\n".join(lines)
        report.append("+Picture4 retention")

    # 3. 删人数/唯一类否定串
    for d in DELETE_STRINGS:
        if d in t:
            t = t.replace(d, "")
            report.append("删:" + d.strip()[:34])

    # 4. 站位归位
    n = 0
    for old, new in BACK_TO_CAMERA_FIX + POSITION_FIX:
        if old in t:
            t = t.replace(old, new)
            n += 1
    report.append("站位替换%d处" % n)

    # 5. 左右一致：far side / near end 残留检查
    left = []
    for bad in ("far side", "near end", "far left of frame", "open floor",
                "filing cabinet", "four plain white walls", "count does not change",
                "exactly three", "only people in it", "back to the camera"):
        if bad in t:
            left.append(bad)

    if t != orig:
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(t)
    return report, left


def main():
    allok = True
    for i in range(2, 8):
        name = "seg%02d" % i
        report, left = fix_segment(name)
        ok = not left
        allok = allok and ok
        print("[%s] %s" % (name, " / ".join(report)))
        if left:
            print("      ⛔ 残留: %s" % left)
    print("\n全部干净" if allok else "\n有残留，需手工处理")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
