import io, json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
SEGD = os.path.join(BASE, "xs001_segs")

# ══════════════════════════════════════════════════════════════
# seg06 / seg07 / seg08 —— 承接 seg05 尾帧，剧情接 X003 第1集场次1-1
# seg05 尾帧状态：苏小满右手刚把折叠纸放在桌面中间；钱经理隔着桌逼过来；
#                 小唐 靠后墙站在画面左侧
# 机位全部稳定，⛔ 零甩镜（Whip Pan）—— 用户实测甩镜会导致观众晕
# ══════════════════════════════════════════════════════════════

ANCHOR = (
    # ⛔⛔ 2026-10-08 用户打回 seg06：「场景都变了 没有衔接第一段」。
    # 根因：我把 151 词的场景描述**删掉**了（前五段的场景是在 LEAN_* 常量里，
    # 但我这几段不走 storyboard_render，就没有那些常量）。
    # → 教训：续写段必须**逐字复刻**已认可段落的场景段落，不能"因为是常量所以省掉"。
    # 下面这段与 seg01-05 渲染出来的场景描述**逐字一致**（墙/百叶窗/文件柜/木桌/门）。
    "The whole clip takes place in one small private office and the camera never leaves it. "
    "The room has four plain white walls, a grey metal filing cabinet along the far wall, a long "
    "wooden desk standing across the middle of the floor, venetian blinds on the right-hand wall "
    "laying bright bands across the desk top, and a closed wooden door set flat into the back wall. "
    "The walls behind the people are smooth painted plaster of one single light colour, unbroken "
    "from the skirting board up to the ceiling. All cardboard boxes and folders are plain brown "
    "corrugated cardboard. The people named in this beat are the only people in it: the manager "
    "stays behind the desk on the far side, the cleaner stays at the near end of it with her back "
    "to the camera, and the colleague stands where this beat places her. The count does not change."
)

GUARD = (
    "No slow-motion, no soft dissolves, no fades, no unnecessary transitions; "
    "use hard cuts only and no on-screen text, letters, logos, subtitles, or watermarks."
)

CUTS = {
    "06": ("00:01.250", "00:02.500", "00:03.750", "00:05.000", "00:06.500"),
    "07": ("00:01.250", "00:02.500", "00:03.750", "00:05.000", "00:06.500"),
    "08": ("00:01.250", "00:02.500", "00:03.750", "00:05.000", "00:06.500"),
}

SHOTS = {}

# ── seg06：钱经理抢过纸 → 苏小满说「你们不能搜我」 ──────────────
SHOTS["06"] = (
    "[Shot 1] Static Shot, medium three-shot across the desk: 钱经理 (S3) on the far side with his "
    "palm flat on the wood beside the small folded paper lying at the middle of the desk top; "
    "苏小满 (S1) at the near end with her back to the camera, her right hand still resting on the "
    "desk beside the paper; 小唐 (S4) clear at the far left of frame near the back wall.\n\n"
    "[Shot 2] At 00:01.250, Camera: Push In with small amplitude at fast speed, pushing in on "
    "钱经理 (S3)'s hand as it closes over the folded paper and lifts it off the wood; the paper's "
    "crease catches the blind-light for a moment before his fist hides it. His mouth opens and he "
    "speaks in a short flat nasal Mandarin: [Chinese] 这字是你的吧。\n\n"
    "[Shot 3] At 00:02.500, Camera: Truck Right with medium amplitude at fast speed, sliding "
    "sideways across the desk to a reverse single on 苏小满 (S1), the blind-laying light barring "
    "the wall behind her; her hand leaves the desk and comes to rest flat against her own waist. "
    "She draws one step back from the wood and answers in a low steady Mandarin: "
    "[Chinese] 你们不能搜我。\n\n"
    "[Shot 4] At 00:03.750, Camera: Tracking Shot with medium amplitude at fast speed, tracking "
    "along the near side of the desk as 钱经理 (S3) unfolds the paper flat on the wood and pins "
    "it down with two fingers, his shoulders square and his eyes still on 苏小满 (S1).\n\n"
    "[Shot 5] At 00:05.000, Camera: Arc Shot with medium amplitude at fast speed, arcing in tight "
    "over 钱经理 (S3)'s shoulder onto the unfolded paper on the desk, its printed rows blurred and "
    "unreadable at this distance, his thumbnail tapping the top row once.\n\n"
    "[Shot 6] At 00:06.500, Camera: Pull Out with large amplitude at slow speed, pulling out to "
    "reveal the whole office: 钱经理 (S3) still bearing down across from 苏小满 (S1) with the "
    "paper spread before him on the desk, 小唐 (S4) still clear at the far left of frame with her "
    "arms wrapped around herself. All three hold their positions.\n\n"
    "From [Shot 4] through [Shot 6] the only mouth movement in frame is 钱经理 (S3) swallowing; "
    "every line of dialogue has already finished, and the office falls into room tone.\n\n"
    + GUARD
)

SOUND = {
    "06": (
        "A clock ticking on the wall and the low hum of the ceiling lights throughout; a short "
        "inhale from 钱经理 at 1.1s before he speaks; the crisp sound of paper unfolding on wood "
        "at 4.0s; one nervous swallow from 小唐 at 5.4s; a soft scrape of a shoe on the floor at "
        "6.8s as 苏小满 steps back."
    ),
}

MUSIC = {
    "06": (
        "A low sustained string drone begins at 0s, a single muted cello note enters at 1.25s "
        "when he starts speaking, and the track thins to a single held note from 5.0s."
    ),
}

# ── seg07：钱经理冷笑 → 小唐往前挪半步 ────────────────────────
SHOTS["07"] = (
    "[Shot 1] Static Shot, medium two-shot over the desk: 钱经理 (S3) on the far side with the "
    "paper spread flat before him and his hands flat on either side of it; 苏小满 (S1) at the near "
    "end with her back to the camera, one step further back from the wood than before; 小唐 (S4) "
    "clear at the far left of frame near the back wall.\n\n"
    "[Shot 2] At 00:01.250, Camera: Push In with small amplitude at fast speed, pushing in on "
    "钱经理 (S3)'s face as the corners of his mouth pull up and his eyes stay locked on "
    "苏小满 (S1); a band of blind-light runs across his cheekbone. His mouth opens and he speaks "
    "in a quiet nasal Mandarin: [Chinese] 那就是心虚。\n\n"
    "[Shot 3] At 00:02.500, Camera: Truck Left with medium amplitude at fast speed, sliding "
    "sideways toward the back wall to a closer single on 小唐 (S4); her arms stay crossed tight "
    "over her middle, her shoulders lift, and her eyes flick from 钱经理 (S3) to 苏小满 (S1) and "
    "then away to the floor tiles.\n\n"
    "[Shot 4] At 00:03.750, Camera: Tracking Shot with medium amplitude at fast speed, tracking "
    "slowly toward 小唐 (S4) as she unfolds her arms and shifts her weight off the wall, her "
    "forearms dropping to her sides, and she looks at 苏小满 (S1) directly.\n\n"
    "[Shot 5] At 00:05.000, Camera: Arc Shot with medium amplitude at fast speed, arcing around "
    "the desk end onto 苏小满 (S1)'s face in three-quarter view from behind her shoulder; her "
    "eyes stay on 小唐 (S4) and the muscles along her jaw set.\n\n"
    "[Shot 6] At 00:06.500, Camera: Pull Out with large amplitude at slow speed, pulling out to "
    "reveal the whole office: 钱经理 (S3) still behind the desk with the paper before him, "
    "苏小满 (S1) still at the near end, 小唐 (S4) now one pace forward from the back wall and no "
    "longer touching it. All three hold their positions.\n\n"
    "From [Shot 3] through [Shot 6] the only mouth movement in frame is 钱经理 (S3) swallowing; "
    "every line of dialogue has already finished, and the office falls into room tone.\n\n"
    + GUARD
)

SOUND["07"] = (
    "A clock ticking on the wall and the low hum of the ceiling lights throughout; a short "
    "inhale from 钱经理 at 1.1s before he speaks; the faint rustle of a cotton sleeve as 小唐 "
    "unfolds her arms at 3.8s; one soft step on the floor at 5.6s as she moves forward; room tone."
)
MUSIC["07"] = (
    "A low sustained string drone begins at 0s, a muted cello note enters at 1.25s when he "
    "speaks, and the track thins to a single held note from 5.0s."
)

# ── seg08：小唐开口 → 钱经理把纸推向苏小满 ────────────────────
SHOTS["08"] = (
    "[Shot 1] Static Shot, medium three-shot across the desk: 钱经理 (S3) on the far side with the "
    "paper spread flat before him; 苏小满 (S1) at the near end with her back to the camera, one "
    "step back from the wood; 小唐 (S4) one pace forward from the back wall, clear of it.\n\n"
    "[Shot 2] At 00:01.250, Camera: Push In with small amplitude at fast speed, pushing in on "
    "小唐 (S4)'s face as she lifts her chin and her mouth opens and she speaks in a small tight "
    "Mandarin: [Chinese] 我看见她了。\n\n"
    "[Shot 3] At 00:02.500, Camera: Truck Left with medium amplitude at fast speed, sliding "
    "sideways back toward the desk to a closer single on 苏小满 (S1); her shoulders turn a few "
    "degrees toward the voice, the loose hair at her temple lifting slightly, and her hands stay "
    "at her own waist.\n\n"
    "[Shot 4] At 00:03.750, Camera: Tracking Shot with medium amplitude at fast speed, tracking "
    "along the far side of the desk as 钱经理 (S3) takes two fingers and slides the unfolded paper "
    "across the wood until its edge stops at the near lip, the paper scraping over the varnish.\n\n"
    "[Shot 5] At 00:05.000, Camera: Arc Shot with medium amplitude at fast speed, arcing around "
    "the far end of the desk onto 钱经理 (S3)'s face as he withdraws his hand and squares his "
    "shoulders; the arc carries the blind-light band across his chest.\n\n"
    "[Shot 6] At 00:06.500, Camera: Pull Out with large amplitude at slow speed, pulling out to "
    "reveal the whole office: the paper lying flat at the near edge of the desk with its edge "
    "against the lip, 钱经理 (S3) behind the desk with his hands flat, 苏小满 (S1) standing clear "
    "of the near end, 小唐 (S4) one pace forward of the back wall. All three hold their positions.\n\n"
    "From [Shot 3] through [Shot 6] the only mouth movement in frame is 小唐 (S4) swallowing; "
    "every line of dialogue has already finished, and the office falls into room tone.\n\n"
    + GUARD
)
SOUND["08"] = (
    "A clock ticking on the wall and the low hum of the ceiling lights throughout; one short "
    "inhale from 小唐 at 1.1s before she speaks; the dry scrape of paper sliding over varnished "
    "wood from 3.8s to 5.0s; room tone."
)
MUSIC["08"] = (
    "A low sustained string drone begins at 0s, a single muted cello note enters at 1.25s when "
    "she speaks, the rhythm thins to a held note from 5.0s, and the whole track fades out by 9.5s."
)

KEEP = {
    "06": ["这字是你的吧。", "你们不能搜我。"],
    "07": ["那就是心虚。"],
    "08": ["我看见她了。"],
}

def build(seg_id):
    """生成 segNN_prompt.txt（内容与 storyboard_render 的 lean 档格式一致）"""
    ls = SHOTS[seg_id]
    cuts = CUTS[seg_id]
    # 校验切点与镜头数一致
    # ⛔ 只认**行首**的镜头标记 —— 「From [Shot 4] through [Shot 6]」那句消音声明里
    #    也带 [Shot N]，用 findall 会重复计数（踩过：seg06 报 8 刀，实际 6 刀）
    shots_only = ls.split("No slow-motion")[0]
    nums = [int(x) for x in re.findall(r"^\[Shot (\d+)\]", shots_only, re.M)]
    n = len(nums)
    assert nums == list(range(1, n + 1)), \
        "%s Shot 编号不连续: %s" % (seg_id, nums)
    assert n == len(cuts) + 1, "%s 镜头数 %d，应为 %d（1 段无时间戳 + %d 段带）" % (
        seg_id, n, len(cuts) + 1, len(cuts))
    got = re.findall(r"At (\d\d:\d\d\.\d\d\d)", ls)
    assert sorted(got) == sorted(cuts), \
        "%s 切点与 CUTS 表不一致: 提示词 %s vs 表 %s" % (seg_id, got, list(cuts))
    # 切点必须落在 10 秒内且严格递增
    sec = [float(t.split(":")[0]) * 60 + float(t.split(":")[1]) for t in got]
    assert all(sec[i] < sec[i + 1] for i in range(len(sec) - 1)), \
        "%s 切点不是严格递增: %s" % (seg_id, sec)
    assert max(sec) < 10.0, "%s 切点超出 10 秒: %s" % (seg_id, max(sec))
    # ⛔ 零甩镜自检 —— 用户实测 Whip Pan 让相机横扫、观众晕
    assert "Whip Pan" not in ls, "%s 含甩镜，必须换成 Truck" % seg_id
    for line in KEEP[seg_id]:
        assert ("[Chinese] " + line) in ls, "%s 缺台词: %s" % (seg_id, line)

    style = (
        # 2026-10-08 瘦身 76→48 词：与 storyboard_render 的 LEAN_STYLE 同源，
        # 但去掉每段都会重复的通用修饰，只保留**可观测**的画面规格。
        "VERTICAL 9:16 portrait framing, high-key commercial cinematography on a large-format "
        "camera, soft broad daylight, luminous pale walls, light reflective floor, airy and open, "
        "gentle soft shadows that keep their detail, refined natural faces, subtle film grain. "
        "Keep the film texture, natural lighting, every face, every costume and the realistic "
        "motion consistent throughout. People stay standing, framed from the knees up."
    )
    expo = (
        # 68→40 词。⛔ 保留 "high-key brightness from edge to edge" —— check_beats 认这句。
        "Exposure: a large window is the key light and the room is filled with soft bounced "
        "daylight. Skin tones are bright and even, shadows sit in the light mid-tones and keep "
        "visible texture, the whites stay white, and the picture carries an even, transparent, "
        "high-key brightness from edge to edge."
    )
    clothes = (
        # 44→30 词。⛔ 一个「不」字都没有（写 "no badge" 反而会强化生成胸牌）。
        "Every shirt is buttoned right up to the closed collar, so each chest shows one "
        "continuous unbroken run of plain fabric with small plain buttons. Apron bibs are plain "
        "unmarked fabric."
    )
    speakers = (
        "Speaker labels for this shot only: (S1) 苏小满, (S3) 钱经理, (S4) 小唐. "
        "Anyone not named here stays completely silent with a closed mouth."
    )
    sd = []
    sd.append("<Subject 1> — 苏小满: the woman in <Picture 1>. She has the same almond eyes, "
              "straight nose, small mouth and faint mole on her left cheek, with centre-parted "
              "black hair worn to her shoulders and loose. She wears a plain pale shirt under a "
              "grey work apron with plain straps and no pockets showing any print. "
              "It is the person shown in <Picture 1>.")
    sd.append("<Subject 2> — 钱经理: the man in <Picture 2>. He has the same broad round face, "
              "heavy-lidded narrow eyes, thick hair, broad nose and heavy jaw. He wears a pale "
              "shirt buttoned to the collar under a dark waistcoat. "
              "It is the person shown in <Picture 2>.")
    sd.append("<Subject 3> — 小唐: the woman in <Picture 3>. She has the same round young face, "
              "straight brows and shoulder-length black hair tied back. She wears a pale shirt "
              "under a grey work apron with plain straps. It is the person shown in <Picture 3>.")
    ra = []
    ra.append("<Subject 1> — 苏小满: fully_preserved - her almond eyes, straight nose, small "
              "mouth, faint mole on her left cheek and centre-parted black hair are retained in "
              "every shot.")
    ra.append("<Subject 2> — 钱经理: fully_preserved - his broad round face, heavy-lidded narrow "
              "eyes, thick hair, broad nose and heavy jaw are retained in every shot.")
    ra.append("<Subject 3> — 小唐: fully_preserved - her round young face, straight brows and "
              "shoulder-length black hair tied back are retained in every shot.")

    body = "\n".join([style, expo, clothes, speakers, ANCHOR, ls])
    t = ("subject_definitions:\n" + "\n".join(sd)
         + "\n\nsummary:\n"
         + "[reference generation] In a small private office a manager accuses a cleaner of "
           "stealing a customer's earring and forces her to empty her pockets, while a colleague "
           "watches from the back wall and then speaks up. Each picture supplies one face only.\n\n"
         + "retention_analysis:\n" + "\n".join(ra)
         + "\n\ndetailed_description:\n" + body
         + "\n\noverall_soundscape: " + SOUND[seg_id]
         + "\n\nnon_diegetic_music: " + MUSIC[seg_id] + "\n")
    p = os.path.join(SEGD, "seg%s_prompt.txt" % seg_id)
    io.open(p, "w", encoding="utf-8").write(t)
    return p, len(body.split()), n


if __name__ == "__main__":
    import sys
    ids = sys.argv[1:] or ["06", "07", "08"]
    print("段 刀数 正文词数 机位种 台词  文件")
    for sid in ids:
        p, nw, n = build(sid)
        ls = SHOTS[sid]
        cams = re.findall(r"Camera: ([A-Z][a-zA-Z ]+?) with", ls)
        nlines = len(KEEP[sid])
        print("seg%s  %d   %4d   %2d     %d    %s"
              % (sid, n, nw, len(set(c.strip() for c in cams)), nlines, p))
    # ⛔ 零甩镜自检 —— 用户实测 Whip Pan 会让相机横扫、观众晕
    for sid in ids:
        c = SHOTS[sid].count("Whip Pan")
        print("  seg%s 甩镜 %d %s" % (sid, c, "OK" if c == 0 else "!! 必须改掉"))
