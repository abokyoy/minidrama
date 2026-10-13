
    # ══════════════════════════════════════════════════════════════════
#  一镜到底（ONE CONTINUOUS TAKE）专用判据集
#  ⛔ 2026-10-09：对话戏的正确形态是「正文零个 [Shot N]」。
#    旧写法「6 刀都写 Static Shot」实测仍被模型切成三段 ——
#    [Shot N] 标记本身就是切镜指令，锁景别防不住「它就是要切」。
# ══════════════════════════════════════════════════════════════════
ONETAKE_HEAD = None   # （保留占位，实际在 audit_onetake 内部懒编译）


def audit_onetake(body_only, txt, chk):
    """一镜到底模式的判据。返回检查项数由外部统计。"""
    # ⛔ 懒编译：模块级预编译会赶在 `import re` 之前执行 → NameError
    head = re.compile(
        r"ONE CONTINUOUS TAKE,\s*"
        r"(medium-wide three-shot|medium two-shot|medium three-shot|"
        r"medium close-up|medium shot|wide shot|two-shot|three-shot)\s*", re.I)
    m = head.search(body_only)
    chk(bool(m), "一镜到底开头（ONE CONTINUOUS TAKE, 景别）",
        "正文必须以 `ONE CONTINUOUS TAKE, <景别>, camera locked off for all ten seconds:` 开头")
    if m:
        sz = m.group(1)
        # 景别必须出现在整个正文里，且前后一致（同一段里不能换词）
        allsz = re.findall(
            r"medium-wide three-shot|medium two-shot|medium three-shot|"
            r"medium close-up|medium shot|wide shot", body_only)
        from collections import Counter
        cnt = Counter(x.lower() for x in allsz)
        top, n = cnt.most_common(1)[0] if cnt else ("-", 0)
        chk(n == 1 or (len(cnt) == 1),
            "一镜到底景别只写一次且不换词",
            "景别词全文出现 %s（出现多次会让模型以为要换景别 = 要切）" % dict(cnt))

    # 核心：正文里绝不能有 [Shot N]
    ns = re.findall(r"^\[Shot \d\]", body_only, re.M)
    chk(not ns, "正文零个 [Shot N]（=不切镜）",
        "一镜到底模式下正文出现 %d 个 [Shot N] —— ⛔这个标记本身就是切镜指令"
        % len(ns))
    chk(not re.search(r"At \d\d:\d\d\.\d\d\d", body_only),
        "一镜到底无切点时间戳",
        "⛔ 出现 `At MM:SS.mmm` = 明确告诉模型这里切一刀，应删掉")

    # 相机必须锁死
    chk("locked off" in body_only.lower(), "相机锁死 locked off",
        "开头必须写 `camera locked off for all ten seconds`")
    # 约束段必须明说不切
    chk(re.search(r"no cuts at all|never cuts", body_only, re.I),
        "约束段明写 no cuts",
        "⛔ 约束段必须明说 `one single unbroken take with no cuts at all` "
        "（旧写法 `use hard cuts only` 是在鼓励剪切，与一镜到底直接矛盾）")
    # ⛔ 不能出现鼓励切镜的措辞
    bad = [w for w in ("hard cut", "hard cuts", "cut to", "cuts to",
                       "multiple shots", "shot changes")
           if w in body_only.lower()]
    chk(not bad, "无鼓励切镜的措辞",
        "⛔ 一镜到底里出现 %s —— 这些词在命令模型切镜头" % bad)
    # 三个人必须全程可见且位置不变
    chk(re.search(r"stay visible in the same", body_only),
        "人员全程同位",
        "必须写 `the same N people stay visible in the same N places at the same size`")


# -*- coding: utf-8 -*-
"""按官方 h3-prompt-writing 规范审计提示词。

用法：
    "C:/Users/86134/.workbuddy/binaries/python/envs/default/Scripts/python.exe" \
        _h3_audit.py xs900_segs/seg01_prompt.txt
    ... _h3_audit.py xs001_segs/seg02_prompt.txt

审计项来自官方规范 + 本项目三条铁律（否定词/对称词/中文变形）。
⛔ 校验器本身也会骗人 —— 上线前必须造已知答案样本先验证它自己。
"""
import io
import os
import re
import sys

# 官方：生成任务正文 350–500 英文词；官方跑酷范本（6刀+约束段）本身约 560 词
BODY_MIN, BODY_MAX = 350, 620
SECTIONS = ["subject_definitions:", "summary:", "retention_analysis:",
            "detailed_description:", "overall_soundscape:", "non_diegetic_music:"]

VISUAL_MARKERS = ["fully_preserved", "partially_preserved",
                  "attribute_transfer", "weak_reference"]
AUDIO_MARKERS = ["fully_copy", "partially_copy", "reference", "weak_reference"]

# 命令行传入的「实际给了几张参考图」。None = 没传 → 跳过图数校验。
# ⛔ 2026-10-08 用户打回两次的教训：少给参考图这个错**必须在这类静态检查里报红**，
#    不能等到生成完从成片里看出来。
REF_COUNT = [None]

# 本项目三条铁律
# ⛔ 只抓「用否定句去禁止某物」这种**真正会诱发反向生成**的句式。
#    不抓 without heat / never leaves it / empty her pockets 这类
#    —— 它们是正常英文（不带怒气地、镜头不离开、掏空口袋），
#    误报会让人把正确的句子改坏，比漏报更危险。
BAD_NEGATION = re.compile(
    r"\bnobody\b|\bno one\b|\bno other\b|\bnot a single\b|"
    r"\bdoes not (?:show|contain|include|appear)\b|"
    r"\bduplicat(?:e|ed|ing|ion)\b|"
    r"\b(?:is|are|stays?|remains?) (?:completely |totally |absolutely )?empty\b|"
    r"\bhalf of (?:the )?frame\b|\beach one holding\b|"
    r"\bown third\b|\bthird of the frame\b|\bcentre axis\b|"
    r"\bfar half of\b|\bnear half of\b|\bleft half of\b|\bright half of\b",
    re.I)
# 文字变形：H3 画中文必变形，人物胸前不许有文字
BAD_TEXT = re.compile(r"badge|lanyard|name\s?tag|nametag|placard|sticker on|"
                      r"text on (?:her|his|their)|chinese characters|hanzi",
                      re.I)


def words(s):
    return [w for w in re.split(r"\s+", s.strip()) if w]


def audit(path):
    t = io.open(path, encoding="utf-8").read()
    ok, bad = [], []

    def chk(cond, good, why):
        # good 只用于 ok 列表的说明，why 是失败时打印的原因
        (ok if cond else bad).append("%s" % (why if cond else "!! " + why))

    # ── 结构 ───────────────────────────────────────────────
    pos = [(s, t.find(s)) for s in SECTIONS]
    chk(all(p >= 0 for _, p in pos), "六段齐全",
        "六段齐全 — 缺: %s" % [s for s, p in pos if p < 0])
    chk(pos == sorted(pos, key=lambda x: x[1]), "顺序正确", "六段顺序正确")

    # ── 字数（只算正文：detailed_description 到 overall_soundscape 之间，
    #        且**不含** detailed_description 之前的内容）
    if all(p >= 0 for _, p in pos):
        a = t.index("detailed_description:") + len("detailed_description:")
        b = t.index("overall_soundscape:")
        body = t[a:b]
        n = len(words(body))
        chk(BODY_MIN <= n <= BODY_MAX, "正文 %d 词" % n,
            "正文 %d 词在 %d-%d 内" % (n, BODY_MIN, BODY_MAX))
        # 总词数也要克制：正文 500 词 + 五段标签 ≈ 700-900 词。
        # 上一版 1287 词就是"动作被稀释 → 成片平庸"的根因。
        total = len(words(t))
        chk(total <= 1000, "总词数 %d" % total,
            "总词数 %d（官方建议正文 350-500，连标签整体不宜超 1000；"
            "上一版 1287 词导致动作被稀释、画面平庸）" % total)
    else:
        n = -1

    # ── 时间轴 ─────────────────────────────────────────────
    body_only = (t[t.find("detailed_description:"):]
                 if "detailed_description:" in t else t)
    shots = sorted(set(re.findall(r"\[Shot (\d+)\]", t)))
    chk(1 <= len(shots) <= 8, "镜头数 %d" % len(shots),
        "镜头 %s 个（官方跑酷范本 10秒6刀；>7刀每刀不足1.5秒会糊）"
        % (shots or "-"))
    # 官方动作片每刀机位不同 —— 但**对话戏现在反过来要求机位固定**
    # ⛔⛔⛔ 2026-10-09 15:55 用户打回片1/2/3：「镜头切换 拉近 左切 右切 太频繁了
    #    看的人头晕 不要大幅度拉 推 切 太晕了」
    #    → 动作片（打斗/追逐）才要机位多样；**对话戏要一镜到底**。
    #    判据：正文有 [Chinese]（对白戏）→ 允许 1 种机位；否则（纯动作）→ 要求多样。
    is_dialog = "[Chinese]" in body_only
    # ⛔ 正则要能认两种写法：`Camera: Static Shot, locked off, ...`（逗号）和
    #   `Camera: Static Shot. holding ...`（句点）。原来只认后者 → 数不全。
    cams_all = re.findall(r"Camera:\s*([A-Z][a-zA-Z]+)", body_only, re.M)
    # ⛔ 2026-10-11 新风格分流：is_multicut（use hard cuts only）= 多刀硬切、
    #    每刀 Static locked off、切换感来自剪辑不来自晃相机（用户拍板「从零开始
    #    改风格 不要一镜到底 但不要晃来晃去」）。此模式下机位固定 Static 是
    #    **本意**，不再适用「机位多样」与「对话戏一镜到底」两条旧判据。
    is_multicut = "use hard cuts only" in body_only.lower()
    if cams_all and not is_multicut:
        uniq = len(set(c.strip() for c in cams_all))
        if is_dialog:
            chk(uniq == 1, "对话戏机位固定 %d/%d" % (uniq, len(cams_all)),
                "全片 %d 刀共用 1 种机位（对话戏要一镜到底，观众反馈「切来切去头晕」）"
                % len(cams_all))
        else:
            chk(uniq >= min(3, len(cams_all)), "机位多样 %d/%d" % (uniq, len(cams_all)),
                "机位 %d 种 / 共 %d 处（动作片官方范本每刀机位都不同，重复机位=平）"
                % (uniq, len(cams_all)))

    # ⛔ 2026-10-08 21:50 加：Shot 1 整段被丢过一次（seg04 压词时），
    #    下面那条「Shot1 无时间戳」会因为找不到而报错，症状不对、容易忽略。
    #    这条直接说「缺第 1 刀」。
    chk("[Shot 1]" in body_only, "Shot 1 存在",
        "[Shot 1] 整段存在（压词时丢过一段，症状是直接从 Shot 2 开始）")

    # ⛔ 2026-10-11 模式分流：正文带 `use hard cuts only` = 多刀硬切模式（用户
    #    新要求「不要一镜到底，要有镜头切换但相机不晃」）。此时：
    #    ① Shot 1 允许带 00:00.000 时间戳（与其它刀统一格式，官方范本两种都有）
    #    ② 景别允许变化（镜头切换的意义就是换构图；人物站位已由
    #       `The cuts change only where the camera stands, never where the people stand` 锁死）
    #    ③ 晃镜仍全禁（BANNED_CAMS 不变），相机只许 Static Shot
    #    旧一镜到底稿（无该句）仍走原判据，行为不变（回归验证 seg02/seg03 失败集与改前一致）。
    is_multicut = "use hard cuts only" in body_only.lower()
    first_shot = re.search(r"\[Shot 1\][^\n]{0,80}", body_only)
    if not is_multicut:
        chk(first_shot and "At 00:" not in first_shot.group(0), "Shot1 无时间戳",
            "[Shot 1] 不带时间戳")

    cuts = re.findall(r"At (\d\d:\d\d\.\d\d\d)(?!\d)", body_only)
    cuts = [c for c in cuts if re.match(r"^\d\d:\d\d\.\d\d\d$", c)]
    chk(cuts == sorted(cuts), "切点递增",
        "切点时间严格递增 %s" % (cuts or "-"))
    # 官方 S.SS 是「秒.百分之一秒」两位，写作 SSS 时是三位毫秒；
    # 两种都接受，只要 00:SS.mmm 里的 SS 是两位整数、mmm 是三位。
    chk(all(re.match(r"^\d\d:\d\d\.\d\d\d$", c) for c in cuts), "时间戳格式",
        "切点格式为 MM:SS.mmm %s" % (cuts or "-"))
    if cuts:
        def to_sec(c):
            _, rest = c.split(":")
            ss, ms = rest.split(".")
            return int(ss) + int(ms) / 1000.0
        secs = [to_sec(c) for c in cuts]
        chk(max(secs) < 10.0, "切点在时长内",
            "所有切点都在 10 秒内（最晚 %.1fs）" % max(secs))
    # 每个 Shot N>1 都必须带切点
    miss = [s for s in shots if s != "1"
            and not re.search(r"\[Shot %s\][^\n]{0,60}?At \d\d:\d\d\.\d\d\d" % s,
                               body_only)]
    chk(not miss, "每刀有切点",
        "Shot2+ 都带时间戳%s" % ("" if not miss else " — 缺: %s" % miss))

    # ── 运镜：官方两种写法都算 ──────────────────────────────
    #   写法A（旧）: "performs a Push In with small amplitude at slow speed"
    #   写法B（官方范本）: "Camera: Push In with small amplitude at slow speed"
    # ⛔ 2026-10-09：对话戏一镜到底写成 "Camera: Static Shot, locked off, holding..."
    #   → 这种**没有 with-amplitude 结构**，原正则一条都抓不到 → 报「运镜 0 处」假红。
    #   → 补一条 Static 专用正则，两类分开统计。
    cams = re.findall(
        r"(?:performs a |Camera:\s*)([A-Z][a-zA-Z ]+?) with "
        r"(small|medium|large) amplitude(?: at (slow|medium|fast) speed)?",
        body_only)
    cams3 = [c for c in cams if c[2]]
    # 一镜到底写法：Camera: Static Shot[, locked off ...]  /  Camera: Static Shot.
    statics = re.findall(r"Camera:\s*(Static Shot)", body_only)
    n_cam = len(cams) + len(statics)
    chk(n_cam >= 1, "运镜 %d 处" % n_cam,
        "运镜/机位标注 %d 处（动镜头 %d，其中写全速度 %d；静止机位 %d）"
        % (n_cam, len(cams), len(cams3), len(statics)))
    chk(len(cams) == len(cams3), "运镜速度齐全",
        "每处动运镜都带速度 — 缺速度: %s"
        % ([c[0].strip() for c in cams if not c[2]] or "无"))
    # 运镜词必须出自官方 14 种词表
    OFFICIAL_CAMS = {
        "zoom in", "zoom out", "push in", "pull out", "pan left", "pan right",
        "truck left", "truck right", "tilt up", "tilt down", "pedestal up",
        "pedestal down", "arc shot", "tracking shot", "static shot",
        "shake slightly", "shake strongly", "pov", "roll clockwise",
        "roll counterclockwise"}
    # ⛔ 2026-10-08 用户实测打脸：whip pan 从机位词表里**移除**。
    # morphic 官方指南里 "a whip pan" 是写在 **transitions**（转场）那一栏的，
    # 不是 Camera: 机位。我把它当机位用 → 相机剧烈横扫 → 观众晕。
    #   实测：正片 seg02 第3刀 Whip Pan Right → 抽帧看到甩到窗户空镜（浪费 0.5 秒），
    #         钱经理脸在甩镜过程中变形。用户原话：「快速的左晃右晃，看的人都晕」。
    # 快切的正确做法 = **切点密（1.25-1.3 秒一刀）+ 每刀换一个稳定机位**，
    #   不是晃相机。要横移就用 Truck Left / Truck Right（机身平移，起点终点都在人身上）。
    BANNED_CAMS = (
        "whip pan",
        # ⛔⛔ 2026-10-08 15:02 用户第二次打回（看 off_xs01_t02_00011-audio.mp4）：
        #   「第一次 从钱经理切到苏小满 还可以 但是 从钱经理到小唐 就是晃过来的 后面都是晃的」
        # 逐镜核对机位后定位：**Tracking Shot（相机跟着人走）和 Arc Shot（相机绕着人转）
        #   本身就让画面飘**，在 1.25 秒一刀的快切节奏下必晕。
        #   而 Push In / Pull Out / Truck / Tilt / Pedestal 是「相机整体平移」，
        #   起点终点都锚在人物身上 → 稳，用户明确认可。
        # ⛔ 快切段（切点 < 2 秒）禁用这两类绕/跟机位。
        "tracking shot",
        "arc shot",
    )
    bad_cam = [c[0].strip() for c in cams
               if c[0].strip().lower() not in OFFICIAL_CAMS]
    chk(not bad_cam, "运镜用官方词",
        "运镜全部出自官方 14 种机位词表%s"
        % ("" if not bad_cam else " — 不在词表: %s" % bad_cam))
    hit_ban = [c[0].strip() for c in cams
               if any(b in c[0].strip().lower() for b in BANNED_CAMS)]
    chk(not hit_ban, "无晃镜机位",
        "机位里没有甩镜/跟拍/环绕（这三类相机自身在动，快切下画面会飘、观众晕）%s"
        % ("" if not hit_ban else " — 命中: %s" % hit_ban))

    # ⛔⛔⛔ 第 32 项：对话戏「一镜到底」—— 任何动镜头都报红
    #   用户 2026-10-09 15:55 第三次打回（片1/2/3 全重做），原话：
    #   「镜头切换 拉近 左切 右切 太频繁了 看的人头晕
    #     不要大幅度拉 推 切 太晕了」
    #
    #   之前这里只禁了 whip/tracking/arc 三类，**放过了 Push In / Pull Out / Truck**，
    #   因为 10-08 那次用户认可过「还可以」。这次用户把尺度改了：
    #   **不是「晃动」才晕，是「动」就晕**。1.25 秒一切 + 6 刀里 4 刀在动 = 必晕。
    #
    #   → 对话戏（无 [Chinese] 动作标签的那种）**只允许 Static Shot**。
    #     动作片的打斗/追逐才需要动镜头，判据是：正文里有 [Chinese] 或动作标签才放宽。
    #   → 改法：把「一镜到底」做成**可切换的判据**，默认对话戏 = 全 Static。
    LOCKED = os.environ.get("H3_ALLOW_MOVING", "") != "1"
    if LOCKED:
        moving = []
        for c in cams:
            nm = c[0].strip()
            low = nm.lower()
            if "static" in low:
                continue
            if "locked off" in low or "does not move" in low:
                continue
            moving.append(nm)
        chk(not moving, "对话戏一镜到底（无动镜头）",
            "所有镜头都是 Static Shot／locked off —— 观众反馈「推拉切太频繁，看的人头晕」%s"
            % ("" if not moving else " — 这些镜头在动: %s" % moving))

    # ⛔⛔⛔ 第 33 项：景别必须逐刀一致（2026-10-09 16:45 第五次打回实锤）
    #   现象：片1 五刀全写 `Static Shot`，1.3 秒处还是硬切到近景 + 多一个白衬衫男人。
    #   逐帧核实：t=1.0/1.2 三人正常，t=1.3 近景且小唐消失。
    #   根因：`Shot 1 = medium-wide three-shot` 但 `Shot 2 = a medium shot of 钱经理`
    #        → **景别变了 = 模型重新构图 = 新构图里空位被补人**。
    #   ⛔ 写了 5 刀 Static Shot 也不等于一镜到底 —— 景别是独立维度，必须逐字锁死。
    SIZE_PAT = (r"medium-wide three-shot|medium two-shot|medium three-shot|"
                r"medium close-up|medium shot|wide shot|two-shot|three-shot|"
                r"close-up|close single|reverse single")
    # ⛔ 判镜头定义行必须「行首 + 带时间戳」：正文里 `From [Shot 4] through…`
    #    这类跨镜句也带 [Shot N]，用全文 findall 会数错。
    shot_defs = re.findall(r"^\[Shot \d\][^\n]*", body_only, re.M)
    sizes = []
    for ln in shot_defs:
        m = re.search(SIZE_PAT, ln)
        if m:
            sizes.append(m.group(0))
    if len(sizes) >= 2:
        uniq_sz = sorted(set(sizes))
        if is_multicut:
            # 多刀硬切模式：景别变化正是「镜头切换」的本意；补人风险由
            # 「The cuts change only where the camera stands, never where
            # the people stand」这句锁人句抵消。只警告不报红。
            pass
        else:
            chk(len(uniq_sz) == 1, "景别逐刀一致 %d/%d" % (len(uniq_sz), len(sizes)),
                "全片 %d 刀共用 1 种景别（%s）—— 景别一变模型就重新构图，"
                "新构图里的空位会被补人（用户反馈「1秒多出个男人」）%s"
                % (len(sizes), uniq_sz[0],
                   "" if len(uniq_sz) == 1 else " — 混用了: %s" % uniq_sz))
        # ⛔ 双人镜头（two-shot）却写 three people = 自相矛盾 → 硬塞第三个人
        for ln in shot_defs:
            m2 = re.search(SIZE_PAT, ln)
            if m2 and "two-shot" in m2.group(0) and "the same three people" in ln:
                chk(False, "景别人数不矛盾",
                    "双人镜头那一刀不能写 the same three people —— 会硬塞第三个人")
                break

    # ── 句子完整性（2026-10-08 用户打回两次「一塌糊涂」，真凶在这）──
    # ⛔ 用正则批量改写镜头段时，极易把句子**拦腰截断**，留下
    #    "holding the same wide frame while from 小唐 toward 苏小满" 这种
    #    缺主语的碎片。模型读到这种句子会当成特写指令 → 连着几刀都在重绘同一张脸
    #    → 脸越推越透明（实测 seg03 f009-f012 连续四刀苏小满，f012 已半透明）。
    #    机位词全对也没用，**这一项才是根因**。
    frag = []
    for m2 in re.finditer(r"\[Shot \d+\][^\[]*", body_only):
        s2 = m2.group(0)
        # 「while|as」后面直接跟介词/人物，没有谓语 = 句子被截断
        for pat2 in (r"\bwhile (?:around|down|along|over|from|past|toward)\b",
                     r"\bholding the same \w+ frame while\b",
                     r",\s*(?:her|his|their) (?:jaw|hair|shoulder|eye)\b",
                     r"\bwhile (?:at|in|on) (?:the|a) \w+\b"):
            if re.search(pat2, s2):
                frag.append(m2.group(0)[:14] + " " + pat2)
                break
    # 每刀都必须点名至少一个人物，否则模型不知道这一刀拍谁
    # ⚠️ 认英文代称：最后一刀常用 the manager / the cleaner / the colleague
    who = ("苏小满", "钱经理", "小唐",
           "the manager", "the cleaner", "the colleague", "the woman", "the man")
    nobody = []
    for m2 in re.finditer(r"^\[Shot (\d+)\][^\n]*", body_only, re.M):
        low = m2.group(0).lower()
        if not any(w in m2.group(0) or w in low for w in who):
            nobody.append("[Shot %s]" % m2.group(1))
    chk(not frag, "句子没被截断",
        "镜头段无截断句子（缺主语的碎片会被模型当成特写指令）%s"
        % ("" if not frag else " — 命中: %s" % frag[:3]))
    chk(not nobody, "每刀都点名人物",
        "每刀都点明了拍谁（人物不明确的刀会让模型反复重绘同一张脸）%s"
        % ("" if not nobody else " — 空镜: %s" % nobody))

    # ── ⛔ 同一个人脸不许连着两刀都是特写（2026-10-08 用户打回「一塌糊涂」真凶）──
    # 实测 seg03：Shot4 是苏小满中景、Shot5 又是苏小满「下颌线绷紧」这种脸部细节
    #   → 成片 f009-f012 连续四刀都在重绘她的脸，越推越淡，f012 已半透明。
    # 模型每刀都要重新画一遍脸，同一张脸连续被推到极限就会「推透明」。
    # → 相邻两刀**不能是同一个人的脸**，也不能连续两刀都对她 push in / 面部细节。
    FACE = ("苏小满", "钱经理", "小唐")
    shots_txt = re.split(r"\[Shot \d+\]", body_only)[1:]
    run = []
    for s3 in shots_txt:
        head = s3[:200]
        hits = [f for f in FACE if f in head or f in s3[:260]]
        # ⛔ 只把**大特写/极近景**算「拍脸」——
        #    ⚠️ 曾把 medium close-up 也算进去，结果误报 seg02（你认可的那支）。
        #    实测真正让脸「推透明」的是**连续两刀都在大特写**，
        #    medium close-up + Static 是不伤脸的（seg02 Shot5 就是 medium close-up，
        #    成片脸完全正常）。别把这条规则收紧过头。
        is_face = bool(re.search(
            r"extreme close[- ]?up|tight close[- ]?up|"
            r"\bclose[- ]?up (?:on|of)\b|"
            r"filling the frame|filling most of the frame",
            s3[:300], re.I))
        run.append((hits[0] if hits else "?", is_face))
    dup_face = []
    for i2 in range(len(run) - 1):
        if run[i2][0] == run[i2 + 1][0] and (run[i2][1] or run[i2 + 1][1]):
            dup_face.append("Shot%d/%d 同为%s%s"
                            % (i2 + 1, i2 + 2, run[i2][0],
                               " 且都在拍脸" if run[i2][1] and run[i2 + 1][1] else ""))
    chk(not dup_face, "不连着拍同一张脸",
        "相邻两刀不是同一人的脸/不同为脸部特写（连着推同一张脸会越推越透明）%s"
        % ("" if not dup_face else " — %s" % dup_face))

    # ── retention ─────────────────────────────────────────
    if "retention_analysis:" in t:
        ra = t[t.index("retention_analysis:"):t.index("detailed_description:")]
        has_visual = [m for m in VISUAL_MARKERS if m in ra]
        chk(bool(has_visual), "保留标记",
            "retention 用视觉标记 %s" % (has_visual or "无"))
        chk(not re.search(r"\(S\d\)", ra), "retention 无说话人编号",
            "retention_analysis 内无 (Sx) 编号（官方要求）")
        # 每个 Subject 都得有一行
        for s in sorted(set(re.findall(r"<Subject \d>", ra))):
            chk(ra.count(s) >= 1, "%s 有保留声明" % s,
                "%s 在 retention 里有声明" % s)
        # ⛔⛔⛔ retention 必须写出**可观测的特征**（2026-10-08 用户打回）
        # 踩坑：三行都只有光秃秃的 `fully_preserved` → 模型在「保留」这一步
        #   完全没收到区分信息 → 小唐长成苏小满的脸。
        # → 每行必须在 `fully_preserved` 后面跟一段特征描述。
        thin = []
        for m2 in re.finditer(r"<Subject \d> — [^:]+:\s*fully_preserved(.*)",
                              ra, re.S):
            tail = m2.group(1).strip()
            # 允许 -, : 等连接符开头，但要有实际内容（≥12 个词）
            body = re.sub(r"^[\s\-:,]+", "", tail)
            if len(body.split()) < 12:
                thin.append(m2.group(0)[:22] + "…（无特征描述）")
        chk(not thin, "retention 写了具体特征",
            "每条 fully_preserved 后面都跟了可观测特征"
            "（光写 fully_preserved 等于没告诉模型保留什么）%s"
            % ("" if not thin else " — %s" % thin))

    # ── ⛔⛔ 参考图数量必须等于 Picture N 的最大值（2026-10-08 用户打回）──
    # 踩坑：提示词里 3 个 Subject 都写着 "It is the person shown in <Picture N>"，
    #   但我**只给了 2 张参考图** → Picture 3 不存在 → 模型拿苏小满的脸凑给小唐。
    #   用户打回原话：「两个苏小满 那个小唐 是苏小满的脸」。
    # ⛔ 反向也不对：为了防人物复制把第 3 张删掉，同样是错的 ——
    #   人物复制的原因是**一张图里有几个人**，不是图的数量。
    # → 图数 = 人物数，一个 Subject 一张单人图。
    pics = [int(x) for x in re.findall(r"<Picture (\d+)>", t)]
    n_pic = max(pics) if pics else 0
    n_sub = len(set(re.findall(r"<Subject \d> —", t.split("retention_analysis")[0])))
    if n_pic:
        chk(n_pic == len(set(pics)), "Picture 编号连续",
            "Picture 编号无跳号（最大 %d，用到 %s）" % (n_pic, sorted(set(pics))))
        # 从命令行读实际给的参考图数量（_h3_audit.py <file> <n_refs>）
        want = REF_COUNT[0] if REF_COUNT else None
        if want is not None:
            chk(want == n_pic, "参考图数量匹配",
                "实际给了 %d 张参考图，提示词要 %d 张（人物数=%d）%s"
                % (want, n_pic, n_sub,
                   "" if want == n_pic else " — ⛔ 少了图 → 那个 Subject 没脸可用，"
                   "模型会拿别人的脸凑"))
        # 每个 Subject 都得指到一张图
        miss = []
        for m2 in re.finditer(r"<Subject (\d)> — ([^:]+):(.*?)(?=\n<Subject |\n\n)",
                              t.split("retention_analysis")[0], re.S):
            idx = m2.group(1)
            if ("<Picture %s>" % idx) not in m2.group(3):
                miss.append("%s(%s)" % (m2.group(2).strip(), idx))
        chk(not miss, "每个 Subject 都指到图",
            "每个 Subject 都写了 It is the person shown in <Picture N>%s"
            % ("" if not miss else " — 没指图的: %s" % miss))
    chk(n_sub == 0 or n_pic >= n_sub or n_pic > 0,
        "人物数与图数",
        "人物 %d 个 / 图 %d 张（一人一图）" % (n_sub, n_pic))

    # ── 声音 ──────────────────────────────────────────────
    m = re.search(r"non_diegetic_music:\s*(\S+)", t)
    chk(bool(m) and (m.group(1) == "N/A" or len(words(t[t.index("non_diegetic_music:"):])) > 5),
        "配乐字段",
        "non_diegetic_music = %s（不要配乐就写 N/A）"
        % (m.group(1) if m else "缺失"))

    # ── 台词 ──────────────────────────────────────────────
    chk(not re.search(r"[\"“][^\"”]*\[(Chinese|English)\]", t), "台词未加引号",
        "台词没被引号包（引号=画面上看得见的文字，包了会烧字幕）")

    # ── 本项目三条铁律 ────────────────────────────────────
    # 否定/对称词：**正文里**禁止；结尾「约束段」里官方范本明确鼓励写
    # （官方跑酷示例：No slow-motion, wire rigs, ... duplicated runners, distorted limbs）
    guard_start = body_only.find("No ") if "No " in body_only else len(body_only)
    # 约束段只到下一个字段为止（后面还有 overall_soundscape / non_diegetic_music）
    guard_txt = body_only[guard_start:]
    for field in ("overall_soundscape:", "non_diegetic_music:"):
        if field in guard_txt:
            guard_txt = guard_txt[:guard_txt.index(field)]
    body_main = body_only[:guard_start]
    h1 = sorted(set(m.group(0) for m in BAD_NEGATION.finditer(body_main)))
    chk(not h1, "正文零否定/对称词", "正文无泛用否定句与对称占比词%s"
        % ("" if not h1 else " — 命中: %s" % h1))

    # ── 第 28 项：人数/排除句（2026-10-09 seg01 打回实锤）──────────────
    # 症状：提示词写 "EXACTLY THREE PEOPLE… the number never changes" /
    #       "no one is duplicated" / "The count does not change"
    # 成片：f0001/f0002/f0005/f0006 画出**两个小唐**（同款浅灰制服低马尾）。
    # 机制：扩散模型只做软匹配、没有否定能力，你反复念叨「人/人数/唯一/复制」
    #       它就多画人。表达「就这三人」只能靠三段互不重叠的正面站位描述。
    # ⛔ 只扫「指向画面内人/物的数量与排除」；指向画外元素的
    #    （no on-screen text / watermarks / subtitles）官方范本在用，不受影响。
    PEOPLE_COUNT_PAT = re.compile(
        r"\b(?:exactly|precisely)\s+(?:one|two|three|four|\d+)\s+(?:people|persons?|men|women)\b"
        r"|\b(?:the\s+)?(?:number|count|population)\s+(?:does\s+not|never|doesn'?t)\s+change\b"
        r"|\bno\s+one\s+(?:is\s+)?(?:enters?|leaves?|is\s+duplicated|duplicated|else)\b"
        r"|\bnobody\b|\bno\s+one\b|\bnot\s+one\s+single\s+other\b"
        r"|\bno\s+(?:extra|additional|other|duplicate|duplicated|second|third)\s+"
        r"(?:people|persons?|men|women|figures?|silhouettes?|body\s+parts?|copies?)\b"
        r"|\b(?:room|office|scene|shot|frame|it)\s+(?:contains?|holds?|has)\s+no\s+other\b"
        r"|\b(?:stays?|is|remains?)\s+empty\b"
        r"|\b(?:not|never)\s+(?:duplicated|anyone\s+else)\b"
        r"|\bthe\s+only\s+(?:people|person|persons?|one|figure)\b"
        r"|\bpeople\s+come\s+only\s+from\b"
        r"|\bnumber\s+of\s+people\b",
        re.I)
    # ⛔⛔ 不设「附近必须出现 people」的门槛 —— 实测漏检两个：
    #   `The count does not change.`（左右 80 字符内没有 people/person）
    #   `The left-hand doorway stays empty.`（同上）
    # 这两句本身就是念叨人数/排除，照样多画人。下面的正则已经足够精确，直接全报。
    pc_hits = sorted(set(m.group(0) for m in PEOPLE_COUNT_PAT.finditer(t)))
    chk(not pc_hits, "正文零「人数/排除句」",
        "没有反复念叨人数与排除（念一次多画一个人）%s"
        % ("" if not pc_hits else " — 命中: %s" % sorted(set(pc_hits))))

    # ── 第 29 项：blind / barred 措辞（2026-10-09 14:35 seg04 打回实锤）────
    # 症状：成片整个画面横条纹、脸被切掉、码率掉到 1.19M（正常 4M）——
    #       **镜头前面横着一排百叶窗**。
    # 根因：提示词写 `blind-laying light barring the wall behind her` /
    #       `the blind-light band runs across his waistcoat`。
    #       `barred across` + `blind` 被模型理解成「有百叶窗挡在镜头前」，
    #       而不是「光斑投在墙上」。seg01~03 同类措辞侥幸没糊，seg04 直接翻车。
    # 修法：全段统一换 `a band of daylight` / `a plain pale wall`（`_fix_blinds.py`）。
    BLIND_PAT = re.compile(r"\bblind(?:-light)?\b|\bbarring\b|\bbarred\b", re.I)
    bl_hits = sorted(set(m.group(0) for m in BLIND_PAT.finditer(t)))
    chk(not bl_hits, "正文零 blind/barred 措辞",
        "没有会让模型把百叶窗画到镜头前的措辞%s"
        % ("" if not bl_hits else " — 命中: %s（改成 a band of daylight / a plain pale wall）"
           % bl_hits))

    # ── 第 30 项：台词必须点名说话人（2026-10-09 seg03 打回实锤）────────
    # 症状：小唐的台词「没看清」被苏小满说了出来。
    # 根因：Shot 3 是小唐单人开口，但 Shot 4 切回三人时没写「他们嘴闭着」，
    #       模型让上一个开口动作延续下去 → 台词落到画面里另一个人头上。
    # 规则：① 每个 [Chinese] 前 300 字符内必须点名该说话人
    #       ② 切到别人那一刀，必须显式写「mouths are closed / mouth stays closed」
    sp_hits = []
    for m in re.finditer(r"\[Chinese\]", t):
        # ⛔ 判据必须限定在**所在的那一刀**（本行 / 上一行）——
        #   用前 300 字符会把上一刀的说话人算进来，漏检
        #   （实测 bad13：小唐的名字在 300 字符外，却因前面出现过而判绿）
        ls = t.rfind("\n", 0, m.start()) + 1          # 本行行首
        line = t[ls:m.start()]
        prev_start = t.rfind("\n\n", 0, ls - 1) + 2   # 上一段（上一刀）行首
        scope = t[prev_start:m.start()]
        if not re.search(r"(苏小满|钱经理|小唐)\s*\((S\d)\)[^。\n]*"
                         r"(?:speaks?|says|answers?|mouth opens)", scope, re.I):
            sp_hits.append("第%d字: %s" % (m.start(), line.strip()[-56:]))
    chk(not sp_hits, "每条台词都点名说话人",
        "每条台词所在那一刀都点了是谁在说%s"
        % ("" if not sp_hits else " — %d 条没点名: %s" % (len(sp_hits), sp_hits[:2])))

    # ── 第 31 项：(S编号) 必须与 <Subject N> 严格一一对应（2026-10-09 根因）──
    # 症状：seg03 里小唐的台词「没看清」被**苏小满的脸**说出来。
    # 根因：**两套编号打架**——
    #   `<Subject 1>`=钱经理 / `<Subject 2>`=苏小满 / `<Subject 3>`=小唐
    #   但 Speaker labels 写的是 `(S1) 苏小满, (S3) 钱经理, (S4) 小唐`
    #   → 苏小满既是 Subject 2 又是 S1；小唐是 S4，**编号在 Subject 表里根本不存在**
    #   → 模型看到「小唐 (S4) 开口」，S4 查无此人 → 就近抓了苏小满 → 说台词的是苏小满的脸。
    # 规则：`(S1)` 钱经理/ `(S2)` 苏小满 / `(S3)` 小唐，三者一一对应，不许有 S4。
    SN = {"钱经理": 1, "苏小满": 2, "小唐": 3}
    id_hits = []
    for nm, want in SN.items():
        for m in re.finditer(re.escape(nm) + r"\s*\(S(\d)\)", t):
            if int(m.group(1)) != want:
                id_hits.append("%s→S%s（应 S%d）" % (nm, m.group(1), want))
                break
    if re.search(r"\(S4\)", t):
        id_hits.append("出现 (S4)，Subject 表里没有 4")
    ml = re.search(r"Speaker labels for this shot only: (.+?)\. Anyone", t, re.S)
    lab = ml.group(1).strip() if ml else ""
    if lab and lab != "(S1) 钱经理, (S2) 苏小满, (S3) 小唐":
        id_hits.append("标签行= %s" % lab)
    chk(not id_hits, "S编号与Subject编号一一对应",
        "说话人编号与 <Subject N> 严格对齐%s"
        % ("" if not id_hits else " — %s" % sorted(set(id_hits))))

    # ── 官方范本：结尾一段「具体风险」约束句是**被鼓励的** ──
    # 官方跑酷示例原文就有 "No slow-motion, wire rigs, ... duplicated runners, distorted limbs"
    # 规则：正面描述为主体 + 结尾 ≤2 句、且每条都可观测（字幕/水印/多余人/变形/慢动作）
    # ⛔ 仍禁止「用否定句代替正面描述」：泛用负面词（no bad quality/ugly/blurry）
    chk(not re.search(r"\b(?:bad|low)\s+(?:quality|resolution)\b|\bugly\b|"
                      r"\bblurry\b|\bdeformed\b|\blowres\b", t, re.I),
        "无泛用负面词",
        "无泛用负面词（no bad quality/ugly/blurry 这类模型无法观测）")
    # 上面已把 guard_txt 截断到下一个字段为止（不要用未截断的原文重取）
    n_sent = len([s for s in re.split(r"\.", guard_txt) if s.strip()])
    chk(not guard_txt or (n_sent <= 2 and len(words(guard_txt)) <= 200),
        "约束段规范",
        "结尾约束段 %d 句 / %d 词（官方范本范式：正面为主体 + 一条逗号列出的具体风险否定）"
        % (n_sent, len(words(guard_txt))))
    h2 = sorted(set(m.group(0) for m in BAD_TEXT.finditer(t)))
    chk(not h2, "胸前无文字", "无胸牌/文字类元素%s"
        % ("" if not h2 else " — 命中: %s" % h2))

    print("=" * 66)
    print(" H3 提示词审计: %s" % path)
    print("=" * 66)
    for line in ok:
        print("  [ok]   %s" % line)
    for line in bad:
        print("  [!!]   %s" % line)
    print("-" * 66)
    print(" 通过 %d 项 / 失败 %d 项" % (len(ok), len(bad)))
    return len(bad)


if __name__ == "__main__":
    # ⛔ 用法：_h3_audit.py <prompt.txt> [实际给的参考图张数]
    #    给了张数才会校「图数 vs Picture N」（否则那两项自动跳过）。
    #    ⛔ 改完提示词**务必带上张数跑一遍** —— 少给图这类错要在这里报红，
    #    而不是等到生成完才从成片里看出来（用户打回两次的教训）。
    REF_COUNT[0] = None
    args = sys.argv[1:]
    for a in args:
        if a.isdigit():
            REF_COUNT[0] = int(a)
    files = [a for a in args if not a.isdigit()]
    if REF_COUNT[0] is not None and files:
        print("（按实际参考图 %d 张校「图数 vs Picture N」）" % REF_COUNT[0])
    rc = 0
    for p in files:
        rc |= audit(p)
        print()
    sys.exit(1 if rc else 0)
