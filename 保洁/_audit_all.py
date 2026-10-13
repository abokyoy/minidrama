# -*- coding: utf-8 -*-
"""一次扫全部段，把每段的问题列出来（不生成，只体检）。

用法：
    "C:/Users/86134/.workbuddy/binaries/python/envs/default/Scripts/python.exe" \
        _audit_all.py xs001_segs

⛔ 为什么需要这个：单跑 _h3_audit.py 只能查一段，且图数要人肉传参。
   seg05 就是这么翻车的 —— 提示词里镜头有小唐 (S4)，但subject_definitions
   只定义了钱经理和苏小满，也没写 <Picture 3>。模型找不到第三张脸，
   就拿现有的脸凑 → 小唐长成苏小满的脸。
   这个脚本把「镜头里用到的人 vs 定义了的人」自动对账。
"""
import os
import re
import sys

SEGS_DIR = sys.argv[1] if len(sys.argv) > 1 else "xs001_segs"
BODY_MIN, BODY_MAX = 350, 620

# 用户已认可、成片定版的段 —— 不再压词。
# seg02 = off_xs01_t02_00013-audio.mp4，用户看过说「这个正片效果还可以」，
# 然后照着它的成片反推了 seg03 的人物外观。它是基准，不是待改稿。
APPROVED = {"02": "off_xs01_t02_00013-audio.mp4"}


def words(s):
    return len(s.split())


def audit(path, segno=None, approved=False):
    t = open(path, encoding="utf-8").read()
    problems = []

    for s in ["subject_definitions:", "summary:", "retention_analysis:",
              "detailed_description:", "overall_soundscape:",
              "non_diegetic_music:"]:
        if s not in t:
            problems.append("缺段落 " + s)

    head = t[:t.find("summary:")] if "summary:" in t else t
    body = ""
    if "detailed_description:" in t and "overall_soundscape:" in t:
        body = t[t.find("detailed_description:") + len("detailed_description:"):
                 t.find("overall_soundscape:")]
    else:
        problems.append("切不出正文段")

    bw = words(body)
    if body and not (BODY_MIN <= bw <= BODY_MAX):
        if approved:
            problems.append("ℹ定版豁免：正文 %d 词（用户已认可 %s，不压）"
                            % (bw, APPROVED.get(segno, "")))
        else:
            problems.append("正文 %d 词，不在 %d-%d" % (bw, BODY_MIN, BODY_MAX))

    # ---- 人物对账：镜头里 @了谁vs 定义了谁 ----
    defined = dict(re.findall(r"<Subject (\d+)> — ([^:]+):", head))
    used = set(re.findall(r"([一-龥]{2,4}) \((S\d+)\)", t))
    used_names = {nm for nm, _ in used}

    for nm in sorted(used_names - set(defined.values())):
        problems.append("⛔ 镜头里出现「%s」但subject_definitions 没定义它" % nm)

    # 定义了但整段没出现（可能是多余的图）
    for sid, nm in defined.items():
        if nm not in used_names:
            problems.append("⚠ 定义了「%s」但镜头里没用到（可能白给一张图）" % nm)

    # ---- Picture 对账 ----
    # ⛔ 关键：<Picture N> 未必都是「人」。
    #    人物图 = 被 subject_definitions 里的 "It is the person shown in <Picture N>" 认领。
    #    剩下的（环境布局图）允许存在，但必须在正文里被声明用途，
    #    否则模型会去复制那张图里的人 → 人物复制。
    claimed = {int(x) for x in re.findall(
        r"It is the person shown in <Picture (\d+)>", head)}
    allpics = {int(x) for x in re.findall(r"<Picture (\d+)>", t)}
    envpics = sorted(allpics - claimed)

    n_people = len(defined)
    if allpics and sorted(allpics) != list(range(1, len(allpics) + 1)):
        problems.append("⛔ Picture 编号跳号：%s" % sorted(allpics))
    if len(claimed) != n_people:
        problems.append("⛔ %d 个人物但只有 %d 张人物图被认领%s"
                        % (n_people, len(claimed), sorted(claimed)))
    for sid, nm in defined.items():
        blk = re.search(r"<Subject %s> — %s:.*?(?=<Subject |\Z)" % (sid, re.escape(nm)),
                        head, re.S)
        if blk and "<Picture" not in blk.group(0):
            problems.append("⛔ Subject %s(%s) 没写 It is the person shown in <Picture N>" % (sid, nm))
    for p in envpics:
        # 环境图必须在正文里出现用途声明
        if not re.search(r"<Picture %d>[^.]*(?:LAYOUT|reference ONLY|environment|room)" % p, t):
            problems.append("⛔ Picture %d 是没人认领的环境图，正文里没声明用途 → 模型会复制图里的人" % p)

    # ---- 晃镜三类 ----
    for bad in ("whip pan", "tracking shot", "arc shot"):
        if bad in t.lower():
            problems.append("⛔ 禁用机位 %s" % bad)

    # ---- 台词必须带 [Chinese] ----
    for m in re.finditer(r"\[Chinese\][^.\n]*", t):
        pass
    if "[Chinese]" not in t and "Mandarin:" in t:
        problems.append("⛔ 有台词但没写 [Chinese] 标签")

    return bw, len(defined), sorted(allpics), problems


def main():
    files = sorted(f for f in os.listdir(SEGS_DIR)
                   if re.match(r"seg\d\d_prompt\.txt$", f))
    print("=" * 78)
    print(" 全段体检: %s   （正文 %d-%d 词）" % (SEGS_DIR, BODY_MIN, BODY_MAX))
    print("=" * 78)
    bad = 0
    for f in files:
        segno = re.match(r"seg(\d\d)_prompt\.txt$", f).group(1)
        appr = segno in APPROVED
        bw, np_, pics, ps = audit(os.path.join(SEGS_DIR, f), segno, appr)
        hard = [p for p in ps if not p.startswith("ℹ")]
        flag = "OK  " if not hard else "!!  "
        if hard:
            bad += 1
        tag = "（定版）" if appr else ""
        print("%s %-20s 正文%5d词  人物%d  Picture%s %s"
              % (flag, f, bw, np_, pics, tag))
        for p in ps:
            print("       -> %s" % p)
    print("-" * 78)
    print(" %d / %d 段有问题（定版段不计入）" % (bad, len(files)))


if __name__ == "__main__":
    main()