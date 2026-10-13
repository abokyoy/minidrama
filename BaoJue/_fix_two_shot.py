#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""清「双人镜头但提示词写着三个人」的病 —— 天花板黑碎片的真正根源。

⛔⛔⛔ 2026-10-09 21:10 片2 成片实锤（off_xs01_t02_00016）：
  画面 f004-f023 几乎每帧天花板都是黑色乱碎片（像电视雪花）。
  我抽帧看出来的，用户只看出「很多黑影子」。

  根因不是渲染bug，是**提示词自相矛盾**：
    seg02 是 `medium two-shot`（只有钱经理 + 苏小满），
    但同一份提示词的站位段写着 `the three of them`，
    而且还逐个描述了第三个人 `小唐 (S3) on the right side of the room
    beside the grey sofa...`、音效段还写 `a nervous swallow from 小唐`。
    → **模型被命令画出第三个人，但 seg02 没给他参考图**
      → 它只能用黑色乱碎片把他糊在天花板上。

  这正是记忆里那条铁律的第七次复发：
    「为了修A 问题而引入的新名词/多余人物，会被模型实体化」。
    这次是反过来 —— **该删的人没删**。

  ✅ 正确做法：双人镜头的提示词里，第三个人**一个字都不能留**：
     - 站位段的「三个人」→ 改成具名的两个人
     - 站位段里那半句第三人描述 → 整句删
     - `<Subject 3>` 定义 → 删（含其参考图）
     - retention 里的 `<Subject 3>` 行 → 删
     - Speaker labels 里的 (S3) → 删
     - 音效/配乐段里的第三人 → 改成房间音

⛔⛔ 禁否定式改法：不要写「nobody else」「the room has only two people」
   —— 否定句会被模型实体化（实测反复踩）。
   → 只能**彻底不提第三个人**，一个词都不留。
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.join(HERE, "xs001_segs")


def fix(tag, keep_en, gone):
    """keep_en=英文写法(如「钱经理 (S1) and 苏小满 (S2)」)；gone=该片不存在的人名。"""
    p = os.path.join(SEG, "%s_prompt.txt" % tag)
    s = io.open(p, encoding="utf-8").read()
    orig = len(s)

    log = []

    # ① 站位段：the three of them → 具名的留下的人
    old3 = "and the three of them hold these same standing places"
    if old3 in s:
        s = s.replace(old3, "and %s hold these same standing places" % keep_en, 1)
        log.append("① 站位段 'three of them' → %s" % keep_en)

    # ② 站位段里第三个人的半句（形如 "; 小唐 (S3) on the right side of the room ... desk."）
    if gone:
        import re
        # 匹配：; <名> (S3) 开头、到句号为止的一段
        pat = re.compile(r";\s*" + re.escape(gone) + r"\s*\(S3\)[^;]*?\.")
        s2, n = pat.subn("", s)
        if n:
            s = s2
            log.append("② 删站位段里 %s 那半句（%d 处）" % (gone, n))

    # ③ <Subject 3> 定义块
    i = s.find("<Subject 3>")
    if i >= 0:
        # 从 <Subject 3> 到下一个 <Picture
        j = s.find("<Picture", i)
        if j < 0:
            j = len(s)
        s = s[:i] + s[j:]
        log.append("③ 删 <Subject 3> 定义块")

    # ④ retention 里的 <Subject 3> 行
    lines = s.split("\n")
    before = len(lines)
    lines = [l for l in lines if not l.startswith("<Subject 3>")]
    if len(lines) != before:
        s = "\n".join(lines)
        log.append("④ 删 retention 的 <Subject 3> 行")

    # ⑤ Speaker labels 去掉 (S3)
    if "(S3)" in s:
        import re
        s = re.sub(r",\s*\(S3\)\s*[^.,;]+", "", s, count=1)
        log.append("⑤ Speaker labels 去掉 (S3)")

    # ⑥ 全文件最后的第三人名残留（音效/配乐段）
    if gone:
        cnt = s.count(gone)
        if cnt:
            # 音效段：把第三人称改成房间音
            s = re.sub(
                r"(one |a )(nervous|quiet|soft|sharp)?[^,;]*?" + re.escape(gone) + r"[^,;]*",
                r"\1quiet room tone", s)
            s = s.replace(gone, "the room")
            log.append("⑥ 音效/配乐段第三人名残留 %d 处已改写" % cnt)

    io.open(p, "w", encoding="utf-8").write(s)

    # 复查
    left = {}
    for k in (gone or "小唐", "S3", "Subject 3", "Picture 3", "three"):
        left[k] = s.count(k)
    print("[%s] 字符数 %d -> %d" % (tag, orig, len(s)))
    for l in log:
        print("     " + l)
    print("     复查残留: %s   字数 %d -> %d"
          % (left, orig, len(s)))
    return left


if __name__ == "__main__":
    # 每片：保留的人（名字, 英文写法, 该片不存在的人）
    PLAN = {
        "seg02": (["钱经理", "苏小满", "小唐"], ["钱经理 (S1) and 苏小满 (S2)"], "小唐"),
        "seg05": (["钱经理", "苏小满", "小唐"], ["钱经理 (S1) and 苏小满 (S2)"], "小唐"),
        "seg06": (["钱经理", "苏小满", "小唐"], ["钱经理 (S1) and 苏小满 (S2)"], "小唐"),
    }
    tags = sys.argv[1:] or list(PLAN)
    for t in tags:
        if t not in PLAN:
            print("[%s] 不在计划里，跳过" % t)
            continue
        fix(t, PLAN[t][1], PLAN[t][2])
        print()