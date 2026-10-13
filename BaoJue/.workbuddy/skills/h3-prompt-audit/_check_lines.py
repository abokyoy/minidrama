# -*- coding: utf-8 -*-
"""台词归属校验器（用户 2026-10-10 拍板新加）
════════════════════════════════════════════════════════════════════

用户原话：
  「链1的三个视频 一塌糊涂 没有一个对的 …… 对话都是乱的」

**根因不是模型，是我把台词安到了错的人头上。**
剧本 `ep001/文字剧本.md` 场次1-2 的原文：

  钱经理（拍桌）：三楼包厢。贵客丢了一只金耳钉。三万八。
  钱经理（盯着苏小满）：收台的时候，就你一个人在。
  苏小满：不是我。
  小唐：钱经理。中午，我看见她往兜里塞东西。没看清。
  苏小满：小唐。看清楚了，再说。
  小唐：反正，我看见了。

实际写进提示词的（错）：
  seg02  苏小满 (S2) speaks: 收台的时候，就你一个人在。   ← 这是钱经理的台词！
  seg04  钱经理 (S1) speaks: 小唐。看清楚了，再说。       ← 这是苏小满的台词！

⛔⛔⛔ 铁律：**台词归属只能从剧本抄，不能凭印象写。**
  凭印象写 = 必然错 = 观众一秒就听出来「这句话不该你说」。

本脚本把剧本台词建成一张「台词 → 真正说话人」的表，
再逐片扫描提示词，凡是「某人说了不属于他的台词」一律报红。

用法：python _check_lines.py
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEGDIR = "E:/LLM/try/minidrama/保洁/xs001_segs"
SCRIPT = os.path.join(HERE, "ep001", "文字剧本.md")

# ══════════════════════════════════════════════════════════════
# 剧本台词表：台词原文 → 真正的说话人
# ⛔ 只收场次 1-2（8 片全部出自这一场）。
# ⚠️「没看清」已按用户要求删除，不进表。
# ══════════════════════════════════════════════════════════════
# ⛔ 太短的词不能进表，否则会误匹配（「还有」会命中「还有别人」）
MIN_KEY_LEN = 4
LINE_OWNER = {
    "三楼包厢": "钱经理",
    "贵客丢了一只金耳钉": "钱经理",
    "三万八": "钱经理",
    "收台的时候，就你一个人在": "钱经理",      # ← seg02 曾经安给苏小满
    "不是我": "苏小满",
    "中午，我看见她往兜里塞东西": "小唐",
    "小唐。看清楚了，再说": "苏小满",          # ← seg04 曾经安给钱经理
    "反正，我看见了": "小唐",
    "掏兜": "钱经理",                        # ← seg05 曾写成「兜掏出来」（编的）
    "自己掏，还是我喊保安": "钱经理",
    "你们不能搜我": "苏小满",                # ← seg06 曾给钱经理编了句「这字是你的吧」
    "那就是心虚": "钱经理",
    "还有": "钱经理",                        # ← seg08 曾编成「我看见她了」
}

# 用户明确要求删除的台词 —— 出现即报红
BANNED_LINES = ["没看清"]

# 场景名必须是剧本里的，剧本全文只有「景宸大厦」和「万山」（黑卡上的字）
RIGHT_BUILDING = "景宸大厦"
WRONG_BUILDING = "万山大厦"

# 剧本 0.2 明确：门口挤了一圈围观的人
EMPTY_DOORWAY_BAD = [
    "the empty doorway",
    "shows only the corridor wall",
    "doorway shows only",
    "NOT at either woman",
    "not at either woman",
]

# 说话人 + 台词的匹配式：名字 … (S?) speaks … [Chinese] 台词
SPEAK_RE = re.compile(
    r"(钱经理|苏小满|小唐)\s*\(S\d\)\s*speaks[^:]*:?\s*\[Chinese\]\s*([^.]+?)(?=\s*(?:钱经理|苏小满|小唐)\s*\(S\d\)\s*speaks|\.\s|$)",
    re.S,
)
NAMES_RE = re.compile(r"(钱经理|苏小满|小唐)\s*\(S\d\)\s*speaks")


def load_lines():
    out = {}
    for f in sorted(os.listdir(SEGDIR)):
        m = re.match(r"(seg\d\d)_prompt\.txt$", f)
        if not m:
            continue
        p = os.path.join(SEGDIR, f)
        out[m.group(1)] = io.open(p, encoding="utf-8").read()
    return out


# ⛔ 台词后不能紧跟下一个说话人标记 —— 用户 2026-10-10 09:56 抓到的错
#   现象：成片里**把钱经理三个字念出来了**。
#   原因：我写成
#     …: [Chinese] 贵客丢了一只金耳钉。 钱经理 (S1) speaks, …: [Chinese] 三万八。
#   台词和下一个说话人标记之间**没有硬边界**，模型把「钱经理 (S1) speaks」
#   当成了这一刀台词的一部分，一起念了出来。
#   官方规范（SKILL.md 对话语法节）：
#     说话人身份 + (S1) + says/sings: [Chinese] 原句
#     → 标签内只有语言标签 + 原句 + 标点，**后面不再跟任何标记**。
#   正解：每句台词**独占一行**，句末就是结束，标记另起一行重新写。
#
# ⚠️ 判据必须是「**同一行内**紧跟」才算错：
#   跨行是正解（我要的就是换行），之前用 \s* 匹配把正确的换行也报红了。
_TIGHT = re.compile(
    r"(\[Chinese\][^\[\n]*?[。！])[ \t]*"
    r"(?:钱经理|苏小满|小唐)\s*\(S\d\)\s*(?:speaks|says|answers|sings)")

# ⛔ 台词绝不能用引号包 —— 引号是留给画面上看得见的文字的，
#   一包就把字烧进画面（官方规范明写）。
_QUOTED = re.compile(r'\[Chinese\][^\n]*[“”"]')


def check(tag, text):
    """返回问题列表。"""
    bad = []

    # ① 台词归属：某人说了不属于他的台词
    for spk, line in SPEAK_RE.findall(text):
        line = line.strip().rstrip("。")
        for key, owner in LINE_OWNER.items():
            if key in line and owner != spk:
                bad.append(
                    "台词归属错：「%s」按剧本是**%s**说的，"
                    "这里写成了 %s 说的" % (line, owner, spk))
        # ⛔ 反向漏检：台词表里根本没有这句话 → 说明是我编的
        if not any(k in line for k in LINE_OWNER):
            bad.append("台词「%s」不在剧本台词表里 —— 是编的，"
                       "必须换成剧本原句" % line)

    # ② 用户要求删除的台词
    for b in BANNED_LINES:
        if b in text:
            bad.append("已删除的台词又出现了：「%s」" % b)

    # ③ 楼名
    if WRONG_BUILDING in text:
        bad.append("楼名错：提示词写「%s」，剧本是「%s」"
                   % (WRONG_BUILDING, RIGHT_BUILDING))

    # ④ 门口人群 / 否定句
    for b in EMPTY_DOORWAY_BAD:
        if b in text:
            bad.append("门口/否定句：「%s」—— 剧本里门口有一圈围观的人，"
                       "且不要用否定句强调" % b)

    # ⑤ ⛔⛔⛔ 台词后紧跟说话人标记 → 模型会把标记念出来（用户 09:56 抓到）
    for m in _TIGHT.finditer(text):
        bad.append("台词「%s」后面紧跟说话人标记，中间没有硬边界 → "
                   "模型会把「钱经理 (S1) speaks」当台词念出来。"
                   "每句台词必须独占一行，句末就是结束。"
                   % m.group(1)[9:][:24])

    # ⑥ 台词被引号包 → 字会被烧进画面
    if _QUOTED.search(text):
        bad.append("台词被引号包了 —— 官方规范：引号只留给画面上看得见的文字，"
                   "包住台词会把字烧进画面")

    # ⑤ 说话人自己被写闭嘴
    for name in set(NAMES_RE.findall(text)):
        pass
    for m in re.finditer(r"(钱经理|苏小满|小唐)", text):
        nm = m.group(1)
        tail = text[m.end():m.end() + 160]
        if "speaks" in tail:
            seg = tail.split("speaks", 1)[1][:200]
            if "lips stay pressed shut" in seg or "mouth closed the whole time" in seg:
                bad.append("%s 被写了 speaks，又被写闭嘴（自相矛盾）" % nm)

    return bad


def main():
    lines = load_lines()
    if not lines:
        print("找不到 seg*_prompt.txt")
        return 2

    # ── 先自证：用一个已知错答案的坏样本确认本检查器会报红
    good, bad_seed = True, True
    # 坏样本 = 2026-10-10 用户真实抓到的那个错：
    #   台词后面紧跟下一个说话人标记 → 成片里念出了「钱经理」三个字
    fake = ("苏小满 (S2) speaks: [Chinese] 收台的时候，就你一个人在。"
            " 景宸大厦 万山大厦 the empty doorway 没关系\n"
            "钱经理 (S1) speaks: [Chinese] 贵客丢了一只金耳钉。"
            "钱经理 (S1) speaks: [Chinese] 三万八。\n"
            '苏小满 (S2) speaks: [Chinese] "不是我。"')
    if not check("BADSEED", fake):
        print("⛔⛔⛔ 检查器自己坏了：坏样本没报红，不许相信它的绿灯")
        return 3

    # ② 正样本自检：正确的写法（台词独占一行）**不许**误报
    ok_seed = ("钱经理 (S1) speaks, his mouth opening wide: [Chinese] 三楼包厢。\n"
               "钱经理 (S1) speaks again: [Chinese] 三万八。\n"
               "苏小满 (S2) stands … and keeps her mouth closed the whole time.")
    _e = check("GOODSEED", ok_seed)
    _tight_only = [x for x in _e if "紧跟说话人标记" in x]
    if _tight_only:
        print("⛔⛔⛔ 检查器误伤了正确的写法：%s" % _tight_only)
        return 4

    total = 0
    for tag in sorted(lines):
        errs = check(tag, lines[tag])
        if errs:
            print("[%s] ⛔ %d 处问题" % (tag, len(errs)))
            for e in errs:
                print("        · " + e)
            total += len(errs)
        else:
            print("[%s] ✅ 台词归属与场景都对" % tag)

    print("=" * 60)
    if total:
        print("共 %d 处问题 —— 不许提交，先改" % total)
        return 1
    print("全部通过（检查器已用坏样本自检过，会报红）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
