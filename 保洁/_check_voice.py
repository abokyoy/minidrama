# -*- coding: utf-8 -*-
"""检查「台词归属」会不会被画面焦点抢走。

⛔⛔⛔ 2026-10-09 22:17 用户打回片3：苏小满说了小唐的台词「没看清」。
   提示词里归属写得**完全正确** —— `小唐 (S3) speaks: [Chinese] 没看清。`
   但成片里那句话是苏小满说的。

   病根不是写错了人，是**自己写的两句话在抢焦点**：
     ① `his eyes locked on 苏小满 (S2) … and not on 小唐 (S3)` 出现 2 次
        → 钱经理的视线两次钉在苏小满身上
     ② `and not on 小唐 (S3)` 是**否定句**
        → 我反复念叨「不要看小唐」= 反复把小唐推进注意力中心
        （否定句实体化，已在「凭空多个男人」「走廊是空的」上踩过多次）

   净效果：模型判定「画面焦点 = 苏小满」→ 唯一的台词给了她。
   ⭐ **说话人归属写对了，也会被「谁在画面中心」抢走。**

✅ 正确写法三条：
   1. ⛔ 台词归属的人身上不能有 `not on X` 这种否定
   2. 别把第三人称人物的视线/注意力锁给另一个角色
   3. 用**正面可观测**的表述锁死唯一口型：
      `she is the only person in frame whose mouth moves`
      ✅ 这是正面描述（可观测），不是否定句
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# ⛔ 台词表只有一个来源：_check_lines.py（从剧本抄的）。不许在本文件里再抄一份。
from _check_lines import LINE_OWNER          # noqa: E402

SEG = os.path.join(HERE, "xs001_segs")

# ══════════════════════════════════════════════════════════════
# ⛔⛔⛔ 2026-10-10 这张表原来是我**凭印象手写**的，结果写错了两处：
#     seg02 写成「苏小满」→ 剧本里「收台的时候，就你一个人在」是**钱经理**的台词
#     seg04 写成「钱经理」→ 剧本里「小唐。看清楚了，再说。」是**苏小满**的台词
#   同一个根因让我连着写错提示词、又写错检查器。
# → 现在改成**从剧本台词表自动推导**，不许再手填。
# ══════════════════════════════════════════════════════════════
_SPEAK_RE = re.compile(
    r"(钱经理|苏小满|小唐)\s*\(S\d\)\s*speaks[^:]*:?\s*\[Chinese\]\s*"
    r"([^.]+?)(?=\s*(?:钱经理|苏小满|小唐)\s*\(S\d\)\s*speaks|\.\s|$)", re.S)
_N_RE = re.compile(r"(钱经理|苏小满|小唐)\s*\(S\d\)\s*speaks")


def _expect_from_script(tag):
    """读提示词里的台词，拿剧本台词表反查真正该由谁说。"""
    p = os.path.join(SEG, "%s_prompt.txt" % tag)
    s = io.open(p, encoding="utf-8").read()
    owners = set()
    for _spk, line in _SPEAK_RE.findall(s):
        for key, owner in LINE_OWNER.items():
            if key in line:
                owners.add(owner)
    return owners


def check(tag, expect):
    p = os.path.join(SEG, "%s_prompt.txt" % tag)
    s = io.open(p, encoding="utf-8").read()
    bad = []

    # ① 台词归属写对了吗
    sp = re.findall(r"(小唐|苏小满|钱经理) \(S\d\) speaks", s)
    n_zh = s.count("[Chinese]")
    #⛔ 2026-10-09 22:40 用户明确要求：「把『没看清』这个台词删除掉」
    #   → seg03 现在是**零台词**片（三个人全程闭嘴）。
    #   所以「没有台词」不再是错误，只有「有台词但归属错」才报红。
    if n_zh == 0:
        if sp:
            bad.append("标了 speaks 但没有任何 [Chinese] 台词 → 会让模型自己编台词")
        for pat in ("before she speaks", "before he speaks", "clearing of throat"):
            if pat in s:
                bad.append("⛔ 零台词片里出现「%s」→ 模型会听到有人要说话，"
                           "然后把台词给画面中心那个人" % pat)
    elif not expect:
        # 提示词里的台词在剧本表里查不到对应说话人 → 不敢猜
        bad.append("台词在剧本台词表里查不到归属，请人工核对")
    elif expect - set(sp):
        bad.append("台词按剧本应由 %s 说，实际标记了 %s"
                   % ("、".join(sorted(expect)), set(sp) - expect))
    expect = expect or set(sp)

    # ② ⛔ 台词归属的人身上不能有否定
    for n in ("小唐", "苏小满", "钱经理"):
        for pat in ("and not on %s" % n, "not on %s" % n,
                    "not looking at %s" % n):
            if pat in s:
                bad.append("⛔否定句 `%s`（会把 %s 推进注意力中心 → 抢台词）"
                           % (pat, n))

    # ③ 注意力锁给别人的写法（这会把台词推给那个人）
    #⛔ 2026-10-09 22:20 收窄：原来把 `looking straight at her` 一律判红，
    #   结果 seg02/05/06 三个**双人片误报**—— 那些句子的主语是另一个人
    #   （「钱经理…looking straight at her」= 钱经理看苏小满），
    #   方向跟说话人一致，不是抢焦点。
    #   → 判据必须是：**「谁看谁」的主语是别人、宾语是说话人** 才算抢焦点。
    for pat in ("eyes locked on", "looking straight at her",
                "looking straight at him"):
        if pat not in s:
            continue
        for m in re.finditer(re.escape(pat) + r"([^,.;]{0,24})", s):
            head = s[max(0, m.start() - 120):m.start()]
            # 找出主语：看前面最近的那个 "X (Sn)" 或 "her/his"
            subj = None
            sm = re.findall(r"(钱经理|苏小满|小唐)", head)
            if sm:
                subj = sm[-1]
            tgt_txt = m.group(1)
            tgt = None
            if "苏小满" in tgt_txt or " her" in tgt_txt:
                tgt = "苏小满"
            elif "小唐" in tgt_txt or " her" in tgt_txt:
                tgt = "小唐"
            elif "钱经理" in tgt_txt or " him" in tgt_txt:
                tgt = "钱经理"
            # 只有「别人看说话人」且说话人不主导时才算抢焦点
            if subj and tgt and subj not in expect and tgt in expect:
                bad.append("注意力从 %s 锁到说话人 %s（`%s`）"
                           % (subj, "、".join(sorted(expect)), pat))
                break

    # ④ 多人镜头必须有「唯一口型」或「全员闭嘴」的正面锁定
    if "three-shot" in s:
        if n_zh == 0:
            # ⛔ 零台词片（seg03）：三张嘴必须**逐个人**写死闭嘴。
            #   ⛔ 判据必须按人算，不能按出现次数算 —— 同一句里
            #   「lips stay pressed shut」和「jaw does not move」会一起命中，
            #   按次数算会漏（坏样本验证过：注入后仍报绿 = 判据无效）。
            for who in ("小唐", "钱经理", "苏小满"):
                #⛔ 必须跳过开头那句景别声明（`medium three-shot on 钱经理 (S1),
                #   苏小满 (S2) and 小唐 (S3)`）—— 那里三个人名都出现，
                #   会被误当成描述段的开头。
                st = s.find("ONE CONTINUOUS TAKE")
                head = s.find("ten seconds:", st)          # 景别声明的结束点
                assert head > 0
                k = s.find("%s (S" % who, head + 12)
                if k < 0:
                    bad.append("零台词片里找不到 %s 的描述段" % who)
                    continue
                ends = [x for x in (s.find("%s (S" % o, k + 10)
                                    for o in ("小唐", "钱经理", "苏小满")
                                    if o != who)
                        if x > k]
                j = min(ends) if ends else len(s)
                segtxt = s[k:j]
                if not any(x in segtxt for x in
                           ("lips stay pressed shut", "mouth closed",
                            "jaw does not move", "mouth does not move")):
                    bad.append("零台词片：%s 的段里没有闭嘴描写 → "
                               "模型会自己挑画面中心的人说话" % who)
            # ⛔ 零台词片里出现「唯一口型」= 自相矛盾（既说唯一又说没人说话）
            if "the only person in frame whose mouth moves" in s:
                bad.append("⛔ 零台词片里出现「the only person in frame whose mouth "
                           "moves」→ 自相矛盾（说了唯一口型，又没有台词）")
            if "before she speaks" in s or "before he speaks" in s \
                    or "clearing of throat" in s:
                bad.append("⛔ 零台词片里出现「准备说话」类音效"
                           " → 模型会听到有人要说话")
        else:
            if "the only person in frame whose mouth moves" not in s and \
               "the only mouth" not in s:
                bad.append("三人镜头缺「唯一口型」正面锁定"
                           "（三人同框时模型会把台词给画面中心那个）")

    # ⑤ 其他人必须明写闭嘴
    n_closed = s.count("mouth closed") + s.count("lips stay pressed shut") + \
        s.count("jaw does not move") + s.count("mouth does not move")
    if "three-shot" in s and n_zh > 0 and n_closed < 2:
        bad.append("三个人的闭嘴描写不足（只找到 %d 处，需 ≥2）" % n_closed)

    if bad:
        print("[%s] ❌ %d 项" % (tag, len(bad)))
        for b in bad:
            print("      - " + b)
        return False
    print("[%s] ✅ 台词归属 %s，无抢焦点隐患" % (tag, expect))
    return True


if __name__ == "__main__":
    tags = sys.argv[1:] or sorted(
        (re.match(r"(seg\d\d)_prompt\.txt$", f).group(1)
         for f in os.listdir(SEG) if re.match(r"seg\d\d_prompt\.txt$", f)))

    # ⛔⛔⛔ 先自证本检查器会报红（校验器自己也会骗人，已踩过）。
    #   坏样本 = 历史上真实犯过的错：把钱经理的台词安给苏小满。
    _fake = ("苏小满 (S2) speaks with her mouth moving clearly as she answers him: "
             "[Chinese] 收台的时候，就你一个人在。")
    _probe = os.path.join(SEG, "_badseed_prompt.txt")
    try:
        io.open(_probe, "w", encoding="utf-8").write(_fake)
        _r = check("_badseed", {"钱经理"})
    finally:
        try:
            os.remove(_probe)
        except OSError:
            pass
    if _r:
        print("⛔⛔⛔ 检查器自己坏了：坏样本没报红，不许相信它的绿灯")
        sys.exit(3)

    ok = True
    for t in tags:
        ok = check(t, _expect_from_script(t)) and ok
    print()
    print("全部通过" if ok else "⛔ 有片子会被抢台词 → 出片必然念错人")
    sys.exit(0 if ok else 1)