# -*- coding: utf-8 -*-
"""按「段落索引」精确替换，把seg04/06/07/08 正文压到 <=620 词。

⛔⛔⛔ 今天在压词上栽了三次，每次都是同一类错误：
   1) `_squeeze_seg03.py` 用正则批量改镜头段 → 句子拦腰截断（缺主语）
      → 模型当成特写指令 → 连着四刀重绘同一张脸 → 越推越透明
   2) `_squeeze_fix.py` 用 `re.sub(r"\.([A-Z])", ". \\1")` 补空格，
      把every face→eface、Every shirt→Eshirt、the line→eline、cabinet→ecabinet
      四个词被静默损坏，词数统计完全看不出来
   3) `_squeeze_exact.py` 用 `t.find(needle)` + `t.find("\n\n")` 定位，
      段落被吃掉（seg04 正文从 653 掉到 367）
   **本脚本只用「段落序号」定位，每段是list 里的一项，绝不跨段。**
   替换后立刻打印新旧词数 + 关键要素自检，任何一项掉了就报警。

用法：_squeeze_v2.py 04 06 07
"""
import re
import sys

# ---------- 共用定版块（照抄 seg03 已验证通过的写法） ----------
STYLE = ("VERTICAL 9:16 portrait framing, high-key commercial cinematography, "
         "soft broad daylight, luminous pale walls, refined natural faces. "
         "Keep the film texture, natural lighting, every face, every costume "
         "and the realistic motion consistent throughout. People stay standing, "
         "framed from the knees up.")

EXPO = ("Exposure: a large window is the key light and soft bounced daylight "
        "fills the room; skin tones are bright and even, shadows sit in the "
        "light mid-tones, the whites stay white, and the picture carries an even "
        "high-key brightness from edge to edge. Every shirt is buttoned to the "
        "closed collar, so each chest shows one unbroken run of plain fabric "
        "with small plain buttons; apron bibs are plain.")

SPEAKER = ("Speaker labels for this shot only: (S1) 苏小满, (S3) 钱经理, "
           "(S4) 小唐. Anyone not named here stays silent with a closed mouth.")

ROOM = ("The whole clip takes place in one small private office and the camera "
        "never leaves it: four plain white walls, a grey metal filing cabinet "
        "along the far wall, a long wooden desk across the middle, venetian "
        "blinds on the right-hand wall laying bright bands across the desk top, "
        "and a closed wooden door set flat into the back wall.")

BLOCK = ("The people named in this beat are the only people in it: 钱经理 (S3) "
         "behind the desk on the far side, 苏小满 (S1) at the near end of it with "
         "her back to the camera, and 小唐 (S4) clear at the far left of frame "
         "near the back wall. The count does not change.")

# ---------- 每段：{段序号: 新整段文本} ----------
# 段序号按 detailed_description 之后的空行分段，0 是 STYLE 段。
# ⚠ 只列出要换的段，没列的原样保留。
PLAN = {

"04": {
0: STYLE + "\n" + EXPO + "\n" + SPEAKER + "\n" + ROOM + " " + BLOCK,
},
"06": {
0: STYLE + "\n" + EXPO + "\n" + SPEAKER + "\n" + BLOCK,
},
"07": {
0: STYLE + "\n" + EXPO + "\n" + SPEAKER + "\n" + BLOCK,
},
"08": {
0: STYLE + "\n" + EXPO + "\n" + SPEAKER + "\n" + BLOCK,
},
"05": {
0: STYLE + "\n" + EXPO + "\n" + SPEAKER + "\n" + ROOM + " " + BLOCK,
},
"01": {
0: STYLE + "\n" + EXPO + "\n" + SPEAKER + "\n" + ROOM + " " + BLOCK,
},
}

# 必须活着的要素（删掉任一项 = 脚本改坏了）
MUST = ["Keep the film texture", "high-key", "Picture 1", "Picture 2",
        "Picture 3", "00:06.500", "The count does not change",
        "Speaker labels for this shot only"]


def run(seg):
    path = "xs001_segs/seg%s_prompt.txt" % seg
    t = open(path, encoding="utf-8").read()
    head, rest = t.split("detailed_description:", 1)
    body, tail = rest.split("overall_soundscape:", 1)

    paras = [p.strip() for p in re.split(r"\n\s*\n|\n(?=\[Shot)", body)
             if p.strip()]
    before = len(body.split())

    plan = PLAN.get(seg, {})
    for i, new in plan.items():
        if i >= len(paras):
            print("  [警告] 段号 %d 越界（共 %d 段）" % (i, len(paras)))
            continue
        paras[i] = new

    new_body = "\n\n".join(paras)
    out = head + "detailed_description:\n" + new_body + "\n\noverall_soundscape:" + tail

    # ---- 自检：要素还在吗 ----
    lost = [k for k in MUST if k not in out]
    d = out[out.find("detailed_description:") + 20:out.find("overall_soundscape:")]
    bw = len(d.split())

    if lost:
        print("  [中止] 要素被删：%s —— 已写回原文" % lost)
        return

    open(path, "w", encoding="utf-8").write(out)
    after = len(out.split())
    print("%s seg%s  正文 %4d → %4d 词   总 %4d 词   段数 %d   %s"
          % ("OK " if bw <= 620 else "!! ", seg, before, bw, after, len(paras),
             "达标" if bw <= 620 else "还差 %d" % (bw - 620)))


for n in sys.argv[1:]:
    run(n)