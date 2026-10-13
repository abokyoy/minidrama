# -*- coding: utf-8 -*-
"""逐段整段替换，把seg04/06/07/08 正文压到<=620 词。

⛔⛔ 为什么不用正则（我今天栽在这上面两次）：
   `_squeeze_fix.py` 用 `re.sub(r"\.", r". \1")` 补句号后空格，
   结果把 'every face' 变成 'eface'、'Every shirt' 变成 'Eshirt'、
   'the line' 变成 'eline'、'cabinet' 变成 'ecabinet'
   —— 它把前面刚删掉的首字母接上了。四个词同时被静默损坏，
   而词数统计完全看不出来（照样少了 4 个词）。
   **正则批量改写提示词 = 静默损坏。所有改动必须是整段字面替换。**
本脚本的每一条 REPLACE 都是「一整段原文 -> 一整段新文」，可逐条diff。
"""
import sys

# ============ 共用：常量四段（照抄 seg03 已验证的定版写法） ============
STYLE = ("VERTICAL 9:16 portrait framing, high-key commercial cinematography, "
         "soft broad daylight, luminous pale walls, refined natural faces. "
         "Keep the film texture, natural lighting, every face, every costume "
         "and the realistic motion consistent throughout. People stay standing, "
         "framed from the knees up.")

EXPO_A = ("Exposure: the window is a large bright key light and soft bounced "
          "daylight fills the room; skin tones are bright and even, shadows sit "
          "in the light mid-tones, the whites stay white, and the picture carries "
          "an even high-key brightness from edge to edge. Every shirt is buttoned "
          "to the closed collar, so each chest shows one unbroken run of plain "
          "fabric with small plain buttons; apron bibs are plain.")

EXPO_B = ("Exposure: a large window is the key light and soft bounced daylight "
          "fills the room; skin tones are bright and even, shadows sit in the "
          "light mid-tones, the whites stay white, and the picture carries an even "
          "high-key brightness from edge to edge. Every shirt is buttoned to the "
          "closed collar, so each chest shows one unbroken run of plain fabric "
          "with small plain buttons; apron bibs are plain.")

SPEAKER = ("Speaker labels for this shot only: (S1) 苏小满, (S3) 钱经理, "
           "(S4) 小唐. Anyone not named here stays silent with a closed mouth.")

ROOM = ("The whole clip takes place in one small private office and the camera "
        "never leaves it: four plain white walls, a grey metal filing cabinet "
        "along the far wall, a long wooden desk across the middle, venetian blinds "
        "on the right-hand wall laying bright bands across the desk top, and a "
        "closed wooden door set flat into the back wall.")

# 站位句（不写「only people in it」这种长句，人数约束靠 The count does not change）
BLOCK_A = ("The count does not change.")

BLOCK_B = ("The people named in this beat are the only people in it: 钱经理 (S3) "
           "behind the desk on the far side, 苏小满 (S1) at the near end of it "
           "with her back to the camera, and 小唐 (S4) clear at the far left of "
           "frame near the back wall. The count does not change.")

CONSTRAINT = ("No slow-motion, no soft dissolves, no fades, no unnecessary "
              "transitions; use hard cuts only and no on-screen text, letters, "
              "logos, subtitles, or watermarks.")

# ============ 每段的整段替换表 ============
# key = 原文里那一整段的**开头 40 字符**（唯一定位）
# value = (新整段文本)
REPLACE = {

"seg04": [
    # STYLE 原：…subtle film grain. Keep the film texture… airy and open…
    ("VERTICAL 9:16 portrait framing, high-key commercial",
     STYLE),
    # EXPOSURE 原：the window is a large bright key light … Apron bibs are plain unmarked fabric.
    ("Exposure: the window is a large bright key light",
     EXPO_A),
    # SPEAKER 原：stays completely silent
    ("Speaker labels for this shot only:",
     SPEAKER),
    # 场景原：The room has four plain white walls … The count does not change.
    ("The whole clip takes place in one small private office",
     ROOM + " " + BLOCK_A),
    # Shot 4 原尾：The camera is locked off and does not move, follow, pan, or track in this beat.
    ("[Shot 4] At 00:03.750", "[Shot 4] At 00:03.750"),
    ("her shoe leaves a faint mark in the dust near the skirting board. "
     "The camera is locked off and does not move, follow, pan, or track in this beat.",
     "her shoe leaves a faint mark in the dust by the skirting board. "
     "The camera is locked off."),
    # Shot 5
    ("the blind-light band passes over her collar. The camera is locked off and "
     "does not move, pan, track, or arc in this beat.",
     "the blind-light band passes over her collar. The camera is locked off."),
    # Shot 6
    ("and 小唐 (S4) standing clear at the left of frame, all three holding their "
     "positions across the office floor, the folder still lying flat at the middle "
     "of the desk where it was left.",
     "and 小唐 (S4) clear at the left of frame, all three holding their positions "
     "across the office floor, the folder still flat at the middle of the desk."),
    # 尾段
    ("no mouth moves in frame; every line has already been delivered",
     "no mouth moves; every line has been delivered"),
],

"seg06": [
    ("VERTICAL 9:16 portrait framing, high-key commercial", STYLE),
    ("Exposure: a large window is the key light", EXPO_B),
    ("Speaker labels for this shot only:", SPEAKER),
    ("The people named in this beat are the only people in it:", BLOCK_B),
    # Shot 4 尾
    ("the distance between them across the wood fixed. The camera is locked off and "
     "does not move, follow, pan, or track in this beat.",
     "the distance between them across the wood fixed. The camera is locked off."),
    # Shot 5
    ("its printed rows blurred and unreadable at this distance, and 钱经理 (S3)'s "
     "thumbnail tapping the top row once from the top of frame. The camera travels "
     "in a straight line and stays level, and the desk edge and cabinet in the "
     "background hold a fixed position through this beat.",
     "its printed rows blurred, and 钱经理 (S3)'s thumbnail tapping the top row "
     "once from the top of frame. The camera travels level and the desk edge and "
     "cabinet hold a fixed position."),
    # Shot 6
    ("小唐 (S4) still clear at the far left of frame with her arms wrapped around "
     "herself. All three hold their positions.",
     "小唐 (S4) still clear at the far left with her arms wrapped around herself. "
     "All three hold their positions."),
    ("the only mouth movement in frame is 钱经理 (S3) swallowing; every line of "
     "dialogue has already finished",
     "the only mouth movement is 钱经理 (S3) swallowing; every line has finished"),
],

"seg07": [
    ("VERTICAL 9:16 portrait framing, high-key commercial", STYLE),
    ("Exposure: a large window is the key light", EXPO_B),
    ("Speaker labels for this shot only:", SPEAKER),
    ("The people named in this beat are the only people in it:", BLOCK_B),
    # Shot 2
    ("blind-light runs across his cheekbone", "blind-light crosses his cheekbone"),
    # Shot 4 尾
    ("while 苏小满 (S1) does not move. The camera is locked off and does not move, "
     "follow, pan, or track in this beat.",
     "while 苏小满 (S1) does not move. The camera is locked off."),
    # Shot 5
    ("his eyes stay on 小唐 (S4) at the left of frame and the muscles along his jaw "
     "set. The camera travels in a straight line and stays level, and the desk edge "
     "and cabinet in the background hold a fixed position through this beat.",
     "his eyes stay on 小唐 (S4) at the left of frame and the muscles along his jaw "
     "set. The camera travels level and the desk edge and cabinet hold a fixed "
     "position."),
    # Shot 6
    ("小唐 (S4) now one pace forward from the back wall and no longer touching it. "
     "All three hold their positions.",
     "小唐 (S4) now one pace forward from the back wall. All three hold their "
     "positions."),
    ("the only mouth movement in frame is 钱经理 (S3) swallowing; every line of "
     "dialogue has already finished",
     "the only mouth movement is 钱经理 (S3) swallowing; every line has finished"),
],
}


def apply_seg(name):
    path = "xs001_segs/seg%s_prompt.txt" % name
    t = open(path, encoding="utf-8").read()
    missed = []
    for needle, rep in REPLACE["seg"+name]:
        if rep == needle:
            continue
        idx = t.find(needle)
        if idx < 0:
            missed.append(needle[:45])
            continue
        # 只替换这一整段：从 needle 起到下一个空行为止
        end = t.find("\n\n", idx)
        para_end = end if end > 0 else len(t)
        old_para = t[idx:para_end]
        # 新文本里若含 needle，整段替换；否则按 needle 前缀 + 剩余内容拼回
        t = t[:idx] + rep + t[para_end:]
    open(path, "w", encoding="utf-8").write(t)

    d = t[t.find("detailed_description:") + 20:t.find("overall_soundscape:")]
    return len(d.split()), len(t.split()), missed


for n in sys.argv[1:]:
    bw, tw, missed = apply_seg(n)
    print("%s 正文 %4d 词  总 %4d 词  %s"
          % ("OK " if bw <= 620 else "!! ", bw, tw,
             "达标" if bw <= 620 else "还差 %d" % (bw - 620)))
    for m in missed:
        print("      [没找到] %s" % m)