#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""双人镜头第三人残留检查器（2026-10-09 片2 黑碎片事件后加）。

⛔⛔⛔ 起因：片2 成片 `off_xs01_t02_00016-audio.mp4` 天花板全是黑色乱碎片。
   病根 = seg02 是 `medium two-shot`（两个人），但提示词里到处还留着
   第三个���：站位段 `the three of them` + `小唐 (S3) on the right side...`、
   音效段 `a nervous swallow from 小唐`、`<Subject 3>` 定义和参考图。
   → 模型被命令画出第三个人，而双人片没给他参考图
     → 他就被糊成天花板上的黑色雪花。

⛔ 最重要的一条（踩坑最深）：**清理时不能把「小唐」硬替换成「the room」**
   → 会造出 `the room (S3) still beside the grey sofa`（房间站在沙发边）这种
   荒谬句子，比原来更糟。正解是**整句删掉**，一个字都不留。

用法：python _check_two_shot.py seg02 seg05 seg06 ...
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.join(HERE, "xs001_segs")

# 出现在这些片子里 = 不该存在的人
TWO_SHOT_SEGS = ("seg02", "seg05", "seg06")


def check(tag):
    p = os.path.join(SEG, "%s_prompt.txt" % tag)
    if not os.path.exists(p):
        print("[%s] 文件不存在" % tag)
        return False
    s = io.open(p, encoding="utf-8").read()
    bad = []

    is_two = "two-shot" in s
    # ① 双人片里不能有任何第三人痕迹
    if is_two:
        for k, why in (("小唐", "第三人中文名"),
                       ("S3", "第三人编号"),
                       ("Subject 3", "第三人定义"),
                       ("Picture 3", "第三人参考图"),
                       ("the three of them", "站位段说三个人"),
                       ("All three hold", "收尾句说三个人")):
            n = s.count(k)
            if n:
                bad.append("%s x%d（%s）" % (k, n, why))
        # 三人镜头的景别词
        if "three-shot" in s:
            bad.append("three-shot（这是三人镜头词，双人片不该有）")

    # ② 荒谬句（脚本替换留下的垃圾）
    for k in ("the room (S3)", "the room beside", "the room stands",
              "the room in left profile", "the room still"):
        if k in s:
            bad.append("荒谬句 '%s'" % k)

    # ③ 数字一致性：说是2人就不能出现 three/five 等
    m = re.search(r"same (two|three|four) people", s)
    if m and is_two and m.group(1) != "two":
        bad.append("「the same %s people」与 two-shot 矛盾" % m.group(1))

    if bad:
        print("[%s] ❌ %d 项" % (tag, len(bad)))
        for b in bad:
            print("      - " + b)
        return False
    print("[%s] ✅ 干净（%d 字符）" % (tag, len(s)))
    return True


if __name__ == "__main__":
    tags = sys.argv[1:] or list(TWO_SHOT_SEGS)
    ok = all([check(t) for t in tags])
    print()
    print("全部通过" if ok else "⛔ 有片子没过 → 那片出片必然出黑碎片/多余人")
    sys.exit(0 if ok else 1)