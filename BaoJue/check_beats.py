# -*- coding: utf-8 -*-
r"""
分镜机械自检：把「人工审核」里最容易算错的几条变成脚本，每次改完 beats 必须跑一遍。
检查项：
  1. 时间窗：每句 [Chinese] 台词 起始时刻 + 字数/2.5 必须 <= 10.0s（可设 0.15s 容差）
  2. 说话人：每句 [Chinese] 的**同一拍或上一拍**必须出现 (S#)，且该 (S#) 必须挂在台词所指的人身上
  3. 禁用词：no intelligible / without sound / no dialogue / silence 之类否定声音的写法
  4. 台词不得被引号包裹
  5. 日戏段不得出现会让画面变暗的硬描述
  6. 每段必须含锚点句与曝光重锚句（由渲染器自动前置，这里校验渲染后的 prompt）
用法： python check_beats.py ep001
"""
import io
import json
import glob
import os
import re
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
CPS = 3.2          # 汉字/秒
# 原值 2.5 = 150 字/分，比正常中文口语（200–260 字/分）慢太多，结果 ep004 那种 26–31 字的长台词
# （台词一个字都不许改）会被误判成「台词超时间窗」。3.2 = 192 字/分，仍明显慢于真人语速，
# 给的是下限而不是上限 —— 宁可放宽校验，也不要逼着改台词。
TOL = 0.15         # 容差
SHOT_RE = re.compile(r"\[Shot\s+\d+\]")
TIME_RE = re.compile(r"At\s+(\d{2}):(\d{2})\.(\d{3})")
CN_RE = re.compile(r"\[Chinese\]([^\n\[]*)")
SPK_RE = re.compile(r"\(S(\d+)\)")
CJK = re.compile(r"[\u4e00-\u9fff]")
BAD_PHRASES = ["no intelligible", "without sound", "no dialogue", "no speech", "soundless",
               "without any sound", "mute",
               # 第三轮审核（A/B）实测：声景里写 silence 会把人声压掉，一律换成正向写法
               "silence", "silent room", "silent lobby"]
# 第四轮复核发现：不是关键词但同样会把 H3 人声压掉的「逼近无声」写法。
# 这类只在 overall_soundscape 里才致命，所以单独一张表、只扫声景。
# 第五轮复核补充：还有一类是「明确断言整个空间没有声音」，同属会把 H3 人声压掉的风险。
# 注意 "a quiet voice / one quiet question" 是形容音量低，不在这一类，不要误伤。
SOUNDSCAPE_BAD = ["absolute quiet", "nothing at all", "drops away to nothing",
                  "no other sound", "almost nothing", "nothing but room tone",
                  "not a sound", "in which nothing", "to nothing on the cut",
                  "dead quiet", "dead-quiet", "dead still", "dead-still",
                  "dead room tone", "total hush", "gone quiet", "nothing but"]
DARK_WORDS = [" pitch dark", " in darkness", "dimly lit", "murky", "unlit"]
# ---- 2026-10-03 用户反馈「成片偏黑、人物阴影过重、不柔和」后新增 ----
# 教训：以前这个扫描**只查 shots 字段、且只查日戏**，于是两个大漏网：
#   ① summary / soundscape 是另写的散文，同一句意思措辞不同；它们同样会被拼进提示词，
#      补丁只改 shots 时，summary 里的旧致暗文案会原样送进 H3（ep003 实测漏了 3 段）。
#   ② 「退进阴影 / 沉进暗处 / 只有一小块亮着」这类**打光指令**不分日戏夜戏，夜戏照写一样会把画面压黑。
# 现在：三个字段全查；强指令（DARK_ERR）在日戏里直接算错，软措辞（DARK_WARN_RE）一律提示。
DARK_ERR = ["into the shadow", "into the dark", "into shadow", "in darkness", "into darkness",
            "pitch-black", "pitch black", "deep shadow", "deep shadows", "heavy shadow",
            "swallowed by the dark", "swallowed by darkness", "into the black", "into blackness"]
DARK_WARN_RE = re.compile(
    r"\bthe\s+(?:dark|black)\b(?!\s+(?:red|blue|green|brown|grey|gray|purple|maroon|navy))"
    r"|\bshadowy\b|\bhalf[- ]lit\b|\bdimly\b|\bdim\b|\bgloom\w*|\bmurky\b|\bunlit\b|\bonly\b[^.]{0,40}\blit\b",
    re.I)
# 用户 2026-10-03：不要烧字幕。任何"画面里出现文字"的写法都要拦下来。
SUBTITLE_WORDS = ["subtitle", "caption", "lower-third", "lower third", "title card",
                  "on-screen text", "on screen text", "text overlay", "watermark",
                  "burned-in text", "字幕"]

NAME2SPK = {
    "苏小满": "S1", "女贵宾": "S2", "钱经理": "S3", "小唐": "S4", "阿芳": "S5", "周总监": "S6",
    "小罗": "S7", "陆蔓": "S8", "外婆": "S9", "张总": "S10", "医生": "S11", "前台": "S12",
    "陆航": "S14", "陆崇": "S15", "心腹": "S16", "收费员": "S17", "忠叔": "S18", "秦律师": "S19",
    "护士长": "S20", "邻居": "S21",
}

# 场景 → 光照档。第 2 集起 2-1/2-2/2-5 是室内夜戏，不能被当成日戏（否则 DARK_WORDS 提示会误报，
# 而且夜戏本来就该按"亮着的夜"来写）。第 3 集 3-6 出租屋、第 4 集 4-3/4-4、第 5 集 5-3a/5-3b 同理。
# ⚠️ 场次编号带字母后缀的，是「一个场次里换了地点」拆出来的子场次（4-1a 护士站 / 4-1b 走廊、
#    5-3a 出租屋 / 5-3b 楼门口）；它们的光照档不同，所以必须分开登记。
SCENE_LIGHT = {
    "1-3": "dusk", "1-5": "night",
    "2-1": "night", "2-2": "night", "2-5": "night",
    "3-6": "night",
    "4-3": "night", "4-4": "night",
    "5-3a": "night", "5-3b": "night",
}


def parse_shots(shots, seg_id, errors):
    """把 shots 拆成拍，返回 [(time, text), ...]"""
    parts = SHOT_RE.split(shots)
    heads = SHOT_RE.findall(shots)
    out = []
    t = 0.0
    # parts[0] 是 Entry state 段
    for i, body in enumerate(parts[1:]):
        m = TIME_RE.search(body)
        if m:
            t = int(m.group(1)) * 60 + int(m.group(2)) + int(m.group(3)) / 1000.0
        out.append((t, body.strip(), heads[i] if i < len(heads) else ""))
    return out


def cn_line(raw):
    """从 [Chinese] 之后的内容里，切出真正那段中文台词。
    台词后面常跟英文说明（Hold on 钱经理 (S3)…），必须切掉，否则会把英文里的人名也算成台词字数。"""
    raw = raw.replace("\n", " ")
    ids = [raw.rfind(ch) for ch in "。！？…"]
    k = max(ids)
    if k >= 0:
        return raw[:k + 1]
    return re.split(r"\s[A-Za-z]", raw)[0]


def check_seg(seg, errors, warns):
    sid = seg["id"]
    shots = seg["shots"]
    # 时刻递增且 < 10
    t_prev = -1.0
    for t, body, head in parse_shots(shots, sid, errors):
        if t < t_prev:
            errors.append((sid, "时刻倒退", "%s 的 At %.3f 小于上一拍 %.3f" % (head, t, t_prev)))
        t_prev = t
        if t > 10.0:
            errors.append((sid, "时间越界", "%s 起始 %.3f > 10.0s" % (head, t)))

    # 逐句台词：时间窗 + 说话人
    parts = SHOT_RE.split(shots)
    times = []
    t = 0.0
    for body in parts[1:]:
        m = TIME_RE.search(body)
        if m:
            t = int(m.group(1)) * 60 + int(m.group(2)) + int(m.group(3)) / 1000.0
        times.append((t, body))
    for i, (t, body) in enumerate(times):
        for m in CN_RE.finditer(body):
            line = cn_line(m.group(1))
            pre = body[max(0, m.start() - 6):m.start()]
            if '"' in line or "'" in line or '"' in pre or "'" in pre:
                errors.append((sid, "台词被引号包裹", "第%d拍 «%s»" % (i + 1, line.strip()[:16])))
            n = len(CJK.findall(line))
            if not n:
                continue
            end = t + n / CPS
            if end > 10.0 + TOL:
                errors.append((sid, "台词超时间窗",
                               "第%d拍 [%.3f + %d字/2.5 = %.2fs] «%s»" % (i + 1, t, n, end, line.strip())))
            # 说话人：本拍或上一拍必须出现 (S#)
            ctx = body + (" || " + times[i - 1][1] if i > 0 else "")
            if not SPK_RE.search(ctx):
                errors.append((sid, "台词缺说话人标注",
                               "第%d拍 «%s» 附近没有任何 (S#)" % (i + 1, line.strip()[:16])))
        # ⚠️ 2026-10-08 补：官方跑酷范本在**结尾约束段**里就明写
        #   "no slow-motion, ..., no on-screen text, letters, logos, subtitles, or watermarks"
        #   这正是防止烧字幕的正道，不是违规写法。
        # → 扫描前先切掉结尾约束段（从 "No slow-motion" 或 "No " 起，到段落结束）。
        scan = body
        # 官方跑酷范本在结尾约束段明写 "No slow-motion, ..., no on-screen text,
        # letters, logos, subtitles, or watermarks" —— 这正是防烧字幕的正道。
        # 约束段特征：含 ≥3 个逗号分隔的风险名词，或以 Both/All 开头让人闭嘴。
        # ⛔ 只豁免**这一段**，正文里其它地方的否定照旧判红。
        tail_start = 0
        for m in re.finditer(r"(?:^|(?<=[.;])\s+)([A-Z][^.]{0,400}?)\.", body):
            cand = m.group(1)
            if (cand.count(",") >= 3 and re.search(r"\bno\b", cand, re.I)) or \
               re.match(r"\s*(both|all|two)\b.*\b(no|speaking no|"
                        r"mouths closed|mouth closed)\b", cand, re.I):
                # ⚠️ 取**最小**命中位置 = 约束段的真正起点。
                #   曾踩坑：这里写成「每命中就覆盖」→ 取到最后一个位置，
                #   漏掉约束段第一句（Both people ... speaking no dialogue）。
                tail_start = m.start(1) if tail_start == 0 else min(tail_start, m.start(1))
        if tail_start > 0:
            scan = body[:tail_start]
        for w in BAD_PHRASES:
            if w in scan.lower():
                errors.append((sid, "禁用否定声音写法", "第%d拍 出现 «%s»" % (i + 1, w)))
        for w in SUBTITLE_WORDS:
            if w in scan.lower():
                errors.append((sid, "出现字幕/画面文字写法", "第%d拍 出现 «%s»（用户要求不烧字幕）" % (i + 1, w)))
    # 第四轮复核：声景（overall_soundscape）以前完全没被扫过，
    # 导致 muted / silence / "nothing at all is making a sound" 这类写法一路漏网，
    # 而它们恰恰是最容易把 H3 人声压掉的。这里补上。
    ss = (seg.get("soundscape") or "")
    low = ss.lower()
    for w in BAD_PHRASES:
        if w in low:
            errors.append((sid, "声景否定声音写法", "overall_soundscape 出现 «%s»" % w))
    for w in SOUNDSCAPE_BAD:
        if w in low:
            errors.append((sid, "声景逼近无声写法", "overall_soundscape 出现 «%s»（会压掉人声）" % w))
    for w in SUBTITLE_WORDS:
        if w in low:
            errors.append((sid, "声景出现字幕/画面文字写法", "overall_soundscape 出现 «%s»" % w))

    # ---- 致暗措辞扫描（三个字段都要查，理由见 DARK_ERR 上方注释）----
    is_day = (seg.get("_light", "day") == "day")
    for fname, ftxt in (("shots", shots), ("summary", seg.get("summary") or ""),
                        ("soundscape", ss)):
        low_f = ftxt.lower()
        for w in DARK_ERR:
            if w in low_f:
                (errors if is_day else warns).append(
                    (sid, "致暗打光指令", "%s 出现 «%s»%s" % (fname, w, "" if is_day else "（夜戏也建议改）")))
        for m in DARK_WARN_RE.finditer(ftxt):
            warns.append((sid, "疑似压暗描述", "%s 出现 «%s»" % (fname, m.group(0).strip())))
        if is_day:
            for w in DARK_WORDS:
                if w in low_f:
                    warns.append((sid, "疑似压暗描述", "%s 出现 «%s»" % (fname, w.strip())))


def main():
    ep = sys.argv[1] if len(sys.argv) > 1 else "ep001"
    beats_dir = os.path.join(BASE, ep + "_beats")
    segs_dir = os.path.join(BASE, ep + "_segs")

    beats = []
    for f in sorted(glob.glob(os.path.join(beats_dir, "*.json"))):
        beats.extend(json.load(io.open(f, encoding="utf-8")))

    errors, warns = [], []
    for seg in beats:
        seg["_light"] = SCENE_LIGHT.get(seg.get("scene", ""), "day")
        check_seg(seg, errors, warns)

    # 渲染产物检查：锚点 + 曝光重锚必须都在
    prompts = sorted(glob.glob(os.path.join(segs_dir, "seg*_prompt.txt")))
    if len(prompts) != len(beats):
        errors.append(("-", "渲染数量不符", "%d 个 prompt vs %d 段 beats" % (len(prompts), len(beats))))
    for p in prompts:
        txt = io.open(p, encoding="utf-8").read()
        n = os.path.basename(p)
        # ⚠️ 2026-10-04 19:10 例外：lean 档（段里 style_pack=lean）**故意**不含这些
        # 长曝光锚点 —— 它换成一句短的 LEAN_EXPO。原因是 2071 词的规则堆叠把剧情
        # 挤掉了（H3 官方建议约 350 词），用户反馈「理解能力差、总是很混乱」。
        # 所以 lean 档只校验它自己的那句短光指令。
        # ⚠️ 2026-10-08 修：原来用 "one continuous take" 判定 lean 档，
        # 但 2026-10-08 改 LEAN_STYLE 时把那句话删了（它与官方 6 刀硬切范本矛盾）
        # → 判定失效，全部段掉进非 lean 分支，报 4 条假错误。
        # 现在改用 lean 档的稳定特征句。
        if "style_pack=lean" in txt or "Keep the film texture" in txt or \
                "high-key brightness from edge to edge" in txt:
            # 2026-10-04 20:05 LEAN_EXPO 改写成正向亮度分布描述（否定式会让 H3
            # 压死暗部），校验锚点随之改成新文案的关键句。
            if "high-key brightness from edge to edge" not in txt:
                errors.append((n, "lean 档缺光指令", "没有 LEAN_EXPO 那句"))
            if "the only people in it" not in txt and "only people who exist" not in txt:
                errors.append((n, "lean 档缺人数锁", "没有明确人数"))
        else:
            if "Fixed spatial set-up" not in txt:
                errors.append((n, "缺锚点句", "没有 Fixed spatial set-up"))
            if "Exposure" not in txt:
                errors.append((n, "缺曝光重锚", "没有 Exposure 段"))
            if "LIGHTING IS SOFT, BRIGHT AND FLATTERING" not in txt:
                errors.append((n, "缺软光总闸", "没有 SOFT_LIGHT 段（会导致画面偏黑、阴影过重）"))
            if "LOW shadow density" not in txt:
                errors.append((n, "缺低阴影密度重锚", "曝光重锚里没有 LOW shadow density"))
            if "lifted blacks" not in txt:
                errors.append((n, "缺提黑位", "没有 lifted blacks（黑位压死会显得脏、暗）"))
        # <Picture n> 悬空检查：<Picture n>: 显式定义，或写在 <Subject i> 行里的也算定义
        defined = set(int(x) for x in re.findall(r"<Picture (\d+)>:", txt))
        for line in txt.splitlines():
            if line.startswith("<Subject"):
                defined |= set(int(x) for x in re.findall(r"<Picture (\d+)>", line))
        used = set(int(x) for x in re.findall(r"<Picture (\d+)>", txt))
        if used - defined:
            errors.append((n, "参考图编号悬空", "用到但未定义: %s" % sorted(used - defined)))

    print("检查 %d 段，错误 %d 条，提示 %d 条" % (len(beats), len(errors), len(warns)))
    if errors:
        print("\n== 错误 ==")
        for sid, kind, detail in errors:
            print("  %-10s %-16s %s" % (sid, kind, detail))
    if warns:
        print("\n== 提示 ==")
        for sid, kind, detail in warns:
            print("  %-10s %-16s %s" % (sid, kind, detail))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
