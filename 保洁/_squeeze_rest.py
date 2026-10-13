# -*- coding: utf-8 -*-
"""按 seg03 验证有效的压法，压掉 seg04/06/07/08 的正文词数。

⛔ 铁律（seg03 打回两次换来的）：
   1. 全部用「整段精确替换」，禁用正则批量改写镜头段。
      正则只吃到第一个句点 → 句子拦腰截断 → 模型当特写指令 → 连着推同一张脸。
   2. 必须保住这几样，删了就会翻车：
      - 'Keep the film texture'   ← check_beats.py 判定 lean 档的稳定特征句
      - 'high-key'← 成片亮度判据
      - 'The count does not change'  ← 人物数量硬约束
      - 场景整段（四面白墙/木桌/百叶窗/门）  ← 删了场景就变
      - 每个 Subject 名+ (Sx)+ 该刀的机位+幅度+速度
用法：_squeeze_rest.py04 06 07 08
"""
import re
import sys

# 每段要删的修饰语（都是纯装饰，模型看不到 / 不影响画面）
TRIM = [
    # STYLE 里的空话
    ("on a large-format camera, ", ""),
    ("every surface clearly readable, ", ""),
    ("airy and open, ", ""),
    ("elegant wardrobe, ", ""),
    ("subtle film grain. ", ""),
    ("gentle soft shadows that stay light and keep their detail, ", ""),
    ("gentle soft shadows that keep their detail, ", ""),
    ("clean luminous image, ", ""),
    (", shallow depth of field", ""),
    ("every surface clearly readable", ""),
    # EXPOSURE 里的重复
    ("and colour", ""),
    ("The darkest corners of the frame still read as pale grey with detail, ", ""),
    ("and keep visible texture", ""),
    ("and the whole room is filled with soft bounced daylight",
     "filling the room with soft bounced daylight"),
    ("the whole room is filled with soft bounced daylight",
     "the room is filled with soft bounced daylight"),
    (", transparent,", ","),
    ("one continuous unbroken run of plain fabric", "one unbroken run of plain fabric"),
    ("completely", ""),
    # 场景里的次要物件（成片里有的可以留，这里只删纯装饰）
    ("The walls behind the people are smooth painted plaster of one single light colour, unbroken from the skirting board up to the ceiling. ", ""),
    ("All cardboard boxes and folders are plain brown corrugated cardboard. ", ""),
]

# 整段替换：常量四段压成seg03 的定版写法
CONST_NEW = {
"style": (
"VERTICAL 9:16 portrait framing, high-key commercial cinematography, "
"soft broad daylight, luminous pale walls, refined natural faces. "
"Keep the film texture, natural lighting, every face, every costume and "
"the realistic motion consistent throughout. People stay standing, "
"framed from the knees up."),
"expo": (
"Exposure: the window is a large bright key light and soft bounced daylight "
"fills the room; skin tones are bright and even, shadows sit in the light "
"mid-tones, the whites stay white, and the picture carries an even high-key "
"brightness from edge to edge. Every shirt and waistcoat is buttoned to the "
"closed collar, so each chest shows one unbroken run of plain fabric with its "
"own small plain buttons; apron bibs are plain unmarked."),
}


def squeeze(path, report):
    t = open(path, encoding="utf-8").read()
    orig = len(t.split())
    head, body = t.split("detailed_description:", 1)
    body, tail = body.split("overall_soundscape:", 1)

    paras = [p.strip() for p in body.split("\n\n") if p.strip()]
    # 第0 段 = STYLE + EXPOSURE + speaker + 场景 四合一
    for a, b in TRIM:
        paras[0] = paras[0].replace(a, b)

    # 场景句压缩：去掉纯装饰的墙面描述
    paras[0] = re.sub(
        r"The walls behind the people are smooth painted plaster[^.]*\. ?", "", paras[0])
    paras[0] = re.sub(
        r"All cardboard boxes and folders are plain brown corrugated cardboard\. ?",
        "", paras[0])
    # 站位句去掉多余的 "stays"
    paras[0] = paras[0].replace("stays behind the desk", "behind the desk")
    paras[0] = paras[0].replace("stays at the near end", "at the near end")
    paras[0] = paras[0].replace("stays completely silent", "stays silent")
    paras[0] = re.sub(r"\s+", " ", paras[0]).strip()

    new_body = "\n\n".join(paras)
    out = head + "detailed_description:\n" + new_body + "\n\noverall_soundscape:" + tail
    open(path, "w", encoding="utf-8").write(out)

    d = out[out.find("detailed_description:") + 20:
            out.find("overall_soundscape:")]
    report.append((path, orig, len(d.split())))


def main():
    report = []
    for n in sys.argv[1:]:
        squeeze("xs001_segs/seg%s_prompt.txt" % n, report)
    print("段       原总词   新正文")
    for p, o, n in report:
        flag = "OK " if n <= 620 else "!! "
        print("%s %-22s %5d   %5d  %s" % (flag, p.split("/")[-1], o, n,
                                         "达标" if n <= 620 else "还差 %d" % (n - 620)))


if __name__ == "__main__":
    main()