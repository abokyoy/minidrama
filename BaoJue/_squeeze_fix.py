# -*- coding: utf-8 -*-
"""修正 _squeeze_rest.py 压完后留下的格式问题 + 再压一轮。

⛔ 第一版压出来的三个毛病（我审出来才发现，全是静默损坏）：
   1.段间空行被吃掉 → STYLE 和 Exposure 粘成一句
   2. 'cinematography soft broad' 少了逗号
   3. 'mid-tones , the whites' 逗号前多空格
   这些模型都能察觉得到（词法碎片），会让画面变怪。**压完必须人眼读一遍。**
用法：_squeeze_fix.py 04 06 07
"""
import re
import sys

BAD = [
    ("cinematography soft broad", "cinematography, soft broad"),
    ("pale walls, light reflective floor", "pale walls"),
    ("mid-tones ,", "mid-tones,"),
    ("refined natural faces, Keep the film texture", "refined natural faces. Keep the film texture"),
    ("knees up. Exposure:", "knees up.\nExposure:"),
    ("mouth. The whole clip takes place", "mouth.\nThe whole clip takes place"),
    ("change. [Shot 1]", "change.\n[Shot 1]"),
    ("change.\n\n[Shot 1]", "change.\n[Shot 1]"),
    ("stays silent with a closed mouth. The people named",
     "stays silent with a closed mouth.\nThe people named"),
]

# 镜头段里的纯装饰修饰（可删，不影响画面）
SHOT_TRIM = [
    ("the blind-laying light barring the wall behind her",
     "blind-light barring the wall behind her"),
    ("the blind-laying light barring the wall behind her;",
     "blind-light barring the wall behind her;"),
    ("her apron bib creasing at the waist, and speaks quietly in",
     "her apron bib creasing, and speaks quietly in"),
    (" the wood takes a faint shadow under both hands", ""),
    ("the paper's crease catches the blind-light for a moment before his fist hides it",
     "the crease catches the blind-light before his fist hides it"),
    ("and the camera is locked off and does not move",
     "and the camera is locked off"),
    (" The camera is locked off and does not move.", " The camera is locked off."),
    ("a band of blind-light runs across his cheekbone",
     "blind-light runs across his cheekbone"),
    ("for a moment", ""),
    ("slowly", ""),
    ("very ", ""),
    (" clearly", ""),
    (" slightly", ""),
]


def fix(path):
    t = open(path, encoding="utf-8").read()
    head, rest = t.split("detailed_description:", 1)
    body, tail = rest.split("overall_soundscape:", 1)

    # 1) 修格式
    for a, b in BAD:
        body = body.replace(a, b)

    # 2) 保证段间空行
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    body = "\n\n".join(paras)

    # 3) 修空格/标点毛刺
    body = re.sub(r"\s+,", ",", body)
    body = re.sub(r",\s*,", ",", body)
    body = re.sub(r"\.\s+\.", ". ", body)
    body = re.sub(r"[ \t]{2,}", " ", body)
    # 句号后如果缺空格（.The）补上
    body = re.sub(r"\.([A-Z])", r". \1", body)
    # 逗号后必须有空格（cinematography,soft）
    body = re.sub(r",([A-Za-z])", r", \1", body)

    # 4) 压镜头段
    for a, b in SHOT_TRIM:
        body = body.replace(a, b)

    out = head + "detailed_description:\n" + body + "\n\noverall_soundscape:" + tail
    open(path, "w", encoding="utf-8").write(out)

    d = out[out.find("detailed_description:") + 20:
            out.find("overall_soundscape:")]
    return len(d.split()), len(out.split())


for n in sys.argv[1:]:
    p = "xs001_segs/seg%s_prompt.txt" % n
    bw, tw = fix(p)
    print("%s 正文%4d 词  总%4d 词  %s"
          % ("OK " if bw <= 620 else "!! ", bw, tw,
             "达标" if bw <= 620 else "还差 %d" % (bw - 620)))