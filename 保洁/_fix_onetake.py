#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对话戏改「一镜到底」—— ⛔ 去掉 [Shot N] 分段标记。

⛔⛔⛔ 2026-10-09 20:10 第六次打回根因（抽帧实锤 off_xs01_t01_00014）：
  提示词里逐刀写了 [Shot 1]…[Shot 6]，景别每刀都锁成同一句
  `medium-wide three-shot`，可成片 10 秒里模型还是自己切了两次：
     f001-f004  三人中景
     f005-f011  钱经理近景     ← 切了
     f012-f016  三人中景
     f017-f020  小唐近景       ← 又切
     f021-f030  三人中景

  → **`[Shot N]` 这个标记本身就是「在这里切一刀」的指令**。
    写得越规整（6 个切点 + 每点时间戳），模型切得越准。
    景别锁死只能防「切了之后构图不对」，**防不了「它就是要切」**。

  ✅ 正解：整片**不出现任何 [Shot N]**，写成一整段连续动作流。
     动作靠「然后 / 接着 / 随即」串起来，时间靠台词里的说话顺序表达。
     相机一句话说死：locked off，且明说 no cuts。

本脚本只做整段替换，**⛔ 禁正则逐刀改写**（10-08 铁律：正则截断会留下缺主语的碎片）。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.join(HERE, "xs001_segs")

# ══════════════════════════════════════════════════════════════════
#  每片一整段「一镜到底」正文。写死，不做任何模式化推导 ——
#  ⛔ 这不是批量活，每片的动作/台词/景别都不一样，逐片手写才安全。
# ══════════════════════════════════════════════════════════════════

TAKE = {}

TAKE["seg01"] = (
    # 景别：medium-wide three-shot（沿用已认可的）
    "ONE CONTINUOUS TAKE, medium-wide three-shot across the L-shaped desk, "
    "framed from the knees up, camera locked off for all ten seconds: "
    "钱经理 (S1) stands behind the L-shaped desk in the middle of the room with his "
    "body square to the desk and his head turned to the open doorway at frame left, "
    "shouting into that empty doorway; he then takes one quick step forward and slams "
    "his palm flat on the wood, and a band of daylight slides across his chest as he "
    "leans over the desk bearing down on the folder lying flat at the middle of it, "
    "his chin lifting towards that doorway while his jaw and lips move clearly as he "
    "shouts three short lines one after another into the doorway: "
    "钱经理 (S1) speaks, his mouth opening wide as he shouts: [Chinese] 三楼包厢。 "
    "钱经理 (S1) speaks, his mouth opening wide as he shouts: [Chinese] 贵客丢了一只金耳钉。 "
    "钱经理 (S1) speaks, his mouth opening wide as he shouts: [Chinese] 三万八。 "
    "苏小满 (S2) stands at the near left corner of that desk in right profile facing "
    "right towards him, both feet flat on the tile, and she keeps her mouth closed the "
    "whole time and does not move; "
    "小唐 (S3) stands on the right side of the room beside the grey sofa in left "
    "profile facing left towards the desk, and she lowers her eyes, her fingers closing "
    "on the sofa's wooden arm and her jaw setting tight, staying exactly where she stands "
    "with her mouth closed the whole time. "
    "The framing never changes once: the same three people stay visible in the same "
    "three places at the same size from the first frame to the last, and the open "
    "doorway at frame left shows only the corridor wall beyond it."
)

TAKE["seg02"] = (
    "ONE CONTINUOUS TAKE, medium two-shot on 钱经理 (S1) and 苏小满 (S2) across the "
    "corner of the L-shaped desk, framed from the knees up, camera locked off for all "
    "ten seconds: "
    "苏小满 (S2) stands at the near left corner of the desk in right profile facing "
    "right towards him, both feet flat on the tile, her grey apron hanging straight "
    "down the front of her navy work shirt; she keeps her weight even and does not step "
    "and does not move her hands, and she speaks in a low steady slightly hoarse voice "
    "with her mouth opening and her jaw moving clearly as she answers him: "
    "苏小满 (S2) speaks: [Chinese] 收台的时候，就你一个人在。 "
    "钱经理 (S1) sits on the far side of that desk corner with his body square to the "
    "desk and his head turned to the right towards her at that corner, looking "
    "straight at her; he keeps both hands flat on the wood and his mouth closed the "
    "whole time and he listens without moving. "
    "The framing never changes once: the same two people stay visible in the same two "
    "places at the same size from the first frame to the last, and the open doorway at "
    "frame left shows only the corridor wall beyond it."
)

TAKE["seg03"] = (
    "ONE CONTINUOUS TAKE, medium three-shot on 钱经理 (S1), 苏小满 (S2) and 小唐 (S3) "
    "in the middle of the room, framed from the knees up, camera locked off for all ten "
    "seconds: "
    "小唐 (S3) stands beside the grey sofa at frame right in left profile facing left "
    "towards the desk, and her eyes stay cast down at the floor with her head lowered "
    "away from the desk the whole time she talks, her fingers tightening on the sofa's "
    "wooden arm; she speaks in a small thin nervous voice with her mouth moving clearly: "
    "小唐 (S3) speaks: [Chinese] 没看清。 "
    "钱经理 (S1) is behind the L-shaped desk with his body square to the desk and his "
    "head turned to the right, his eyes locked on 苏小满 (S2) at the near left corner "
    "of that desk and not on 小唐 (S3) beside the sofa; he keeps his mouth closed and "
    "he does not move; "
    "苏小满 (S2) stands at the near left corner of the desk in right profile facing "
    "right towards him, both feet flat on the tile, her mouth closed, waiting. "
    "The framing never changes once: the same three people stay visible in the same "
    "three places at the same size from the first frame to the last, and the open "
    "doorway at frame left shows only the corridor wall beyond it."
)


TAKE["seg04"] = (
    "ONE CONTINUOUS TAKE, medium three-shot on 钱经理 (S1), 苏小满 (S2) and 小唐 (S3) "
    "across the L-shaped desk, framed from the knees up, camera locked off for all ten "
    "seconds: "
    "钱经理 (S1) stands behind the L-shaped desk in white shirt and dark waistcoat, his "
    "body square to the desk and his head turned slightly right towards 苏小满 (S2) at the "
    "near left corner of it, his palm flat on the wood and his jaw set hard; he then "
    "swings his chin round towards the doorway at frame left and speaks two short lines "
    "one after another in the same loud nasal Mandarin, his mouth opening wide on each: "
    "钱经理 (S1) speaks with his mouth opening wide as he shouts: [Chinese] 你今天把话说清楚。 "
    "钱经理 (S1) speaks with his mouth opening wide as he calls out to her: [Chinese] 小唐。看清楚了，再说。 "
    "苏小满 (S2) stands at the near left corner of the desk in right profile facing right "
    "towards him, both feet flat on the tile, her jaw tightening once and her mouth staying "
    "closed the whole time; "
    "小唐 (S3) stands beside the grey sofa at frame right in left profile facing left towards "
    "the desk, her eyes cast down at the floor and her fingers pressed on the sofa's wooden "
    "arm, staying exactly where she stands with her mouth closed the whole time. "
    "The framing never changes once: the same three people stay visible in the same three "
    "places at the same size from the first frame to the last, and the open doorway at "
    "frame left shows only the corridor wall beyond it."
)

TAKE["seg07"] = (
    "ONE CONTINUOUS TAKE, medium-wide three-shot on 钱经理 (S1), 苏小满 (S2) and 小唐 (S3) "
    "across the L-shaped desk in front of the light-oak cabinets, framed from the knees up, "
    "camera locked off for all ten seconds: "
    "钱经理 (S1) stands behind the L-shaped desk with his body square to the desk and his "
    "head turned slightly right, his forefinger pressed down on the unfolded paper lying "
    "flat on the wood; he speaks one short line in a loud nasal Mandarin with his mouth "
    "opening wide and his chin lifted: "
    "钱经理 (S1) speaks with his mouth opening wide as he declares: [Chinese] 那就是心虚。 "
    "苏小满 (S2) stands at the near left corner of the desk in right profile facing right "
    "towards him, both feet flat on the tile, her shoulders squared and her mouth closed "
    "the whole time; "
    "小唐 (S3) stands beside the grey sofa at frame right in left profile facing left towards "
    "the desk, her eyes lowered and her fingers tightening on the sofa's wooden arm, staying "
    "exactly where she stands with her mouth closed the whole time. "
    "The framing never changes once: the same three people stay visible in the same three "
    "places at the same size from the first frame to the last, and the open doorway at "
    "frame left shows only the corridor wall beyond it."
)

TAKE["seg08"] = (
    "ONE CONTINUOUS TAKE, medium-wide three-shot on 钱经理 (S1), 苏小满 (S2) and 小唐 (S3) "
    "across the L-shaped desk, framed from the knees up, camera locked off for all ten "
    "seconds: "
    "钱经理 (S1) stands behind the L-shaped desk with the unfolded paper spread flat before "
    "him, his body square to the desk and his head turned slightly right towards 苏小满 (S2), "
    "both palms flat on the wood; he speaks one short line in a loud nasal Mandarin with "
    "his mouth opening wide and his eyebrows lifting: "
    "钱经理 (S1) speaks with his mouth opening wide as he announces: [Chinese] 我看见她了。 "
    "苏小满 (S2) stands at the near left corner of the desk in right profile facing right "
    "towards him, both feet flat on the tile, her mouth closed and her eyes on him the whole "
    "time; "
    "小唐 (S3) stands beside the grey sofa at frame right in left profile facing left towards "
    "the desk, her eyes cast down at the floor and her jaw setting tight as she swallows "
    "once, staying exactly where she stands with her mouth closed the whole time. "
    "The framing never changes once: the same three people stay visible in the same three "
    "places at the same size from the first frame to the last, and the open doorway at "
    "frame left shows only the corridor wall beyond it."
)


TAKE["seg05"] = (
    "ONE CONTINUOUS TAKE, medium two-shot on 钱经理 (S1) and 苏小满 (S2) across the corner "
    "of the L-shaped desk, framed from the knees up, camera locked off for all ten seconds: "
    "钱经理 (S1) sits on the far side of that desk corner with his body square to the desk "
    "and his head turned to the right towards her at that corner, looking straight at her; he "
    "draws a folded paper out of the desk drawer and lays it flat on the wood between them, "
    "then he speaks one short line in a low steady Mandarin with his mouth moving clearly "
    "and one eyebrow lifting: "
    "钱经理 (S1) speaks with his mouth moving clearly as he orders: [Chinese] 兜掏出来。 "
    "苏小满 (S2) stands at the near left corner of the desk in right profile facing right "
    "towards him, both feet flat on the tile, her grey apron hanging straight down the front "
    "of her navy work shirt and her hands still at her sides; she keeps her eyes on his face "
    "and her mouth closed the whole time and does not step. "
    "The framing never changes once: the same two people stay visible in the same two places "
    "at the same size from the first frame to the last, and the open doorway at frame left "
    "shows only the corridor wall beyond it."
)

TAKE["seg06"] = (
    "ONE CONTINUOUS TAKE, medium two-shot on 钱经理 (S1) and 苏小满 (S2) across the corner of "
    "the L-shaped desk, framed from the knees up, camera locked off for all ten seconds: "
    "钱经理 (S1) sits on the far side of that desk corner with the paper spread flat before "
    "him on the wood, his body square to the desk and his head turned to the right towards "
    "her at that corner, looking straight at her; he speaks one short line in a level cold "
    "Mandarin with his mouth moving clearly and his forefinger resting on the paper: "
    "钱经理 (S1) speaks with his mouth moving clearly as he asks: [Chinese] 这字是你的吧。 "
    "苏小满 (S2) stands at the near left corner of the desk in right profile facing right "
    "towards him, both feet flat on the tile; her chin lifts a little and her brows draw "
    "together as she answers him in the same low steady slightly hoarse voice with her mouth "
    "moving clearly, without stepping: "
    "苏小满 (S2) speaks with her mouth moving clearly as she answers: [Chinese] 你们不能搜我。 "
    "The framing never changes once: the same two people stay visible in the same two places "
    "at the same size from the first frame to the last, and the open doorway at frame left "
    "shows only the corridor wall beyond it."
)


def rewrite(tag, body):
    """把 segXX_prompt.txt 里 [Shot 1]…最后一段 整段换成 body。"""
    p = os.path.join(SEG, "%s_prompt.txt" % tag)
    src = io.open(p, encoding="utf-8").read()
    i = src.find("[Shot 1]")
    if i < 0:
        print("  [%s] 找不到 [Shot 1] → 跳过" % tag)
        return False
    j = src.find("No slow-motion")
    if j < 0:
        print("  [%s] 找不到约束段 → 跳过" % tag)
        return False
    # 约束段前若有 "From [Shot N] onward…" 这种跨镜描述，一并清掉
    k = src.rfind("From [Shot", i, j)
    tail_start = k if k > 0 else i

    new = (src[:i]
           + body + "\n\n"
           + src[j:])
    if tail_start > i:
        # 把 From [Shot..] 那句单独剔除：重新拼一次
        mid = src[tail_start:j]
        new = (src[:i] + body + "\n\n" + src[j:])

    bak = p + ".bak_onetake"
    if not os.path.exists(bak):
        os.replace(p, bak)
        io.open(p, "w", encoding="utf-8").write(new)
        return True
    else:
        io.open(p, "w", encoding="utf-8").write(new)
        return True


def main():
    tags = sys.argv[1:] or ["seg01", "seg02", "seg03"]
    for tag in tags:
        if tag not in TAKE:
            print("[%s] 没有配 TAKE → 跳过" % tag)
            continue
        ok = rewrite(tag, TAKE[tag])
        txt = io.open(os.path.join(SEG, "%s_prompt.txt" % tag),
                      encoding="utf-8").read()
        n = len(re.findall(r"^\[Shot \d\]", txt, re.M))
        print("[%s] %s  残留 [Shot N] 行数=%d  字数=%d"
              % (tag, "已改" if ok else "跳过", n, len(txt.split())))
        if n:
            print("     ⛔ 还有残留 → 需人工看")


if __name__ == "__main__":
    main()