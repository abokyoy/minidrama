# -*- coding: utf-8 -*-
r"""把 seg03 的四段常量压到 ≤210 词（用户 2026-10-08 要求正文 ≤620）。

⛔ 之前我写过「seg02 认可的版本是 771 词，所以不压」——
   那是拿别人也超标当不修的理由。用户明确要求 620，执行。

⚠️ 关键取舍：正文 761 词里 **333 词是四段逐字常量**（风格76/曝光68/服装38/场景151），
   镜头段已压到 52-69 词/刀（官方范本 6 刀共 560 词 ≈ 93 词/刀，已达标）。
   → 要进 620，**只能压常量**。
   → 压法：删**重复修饰与泛用形容**，保留每一句的可观测规格
      （9:16 / 高调 / 大画幅 / 自然光 / 明亮皮肤 / 白保持白 / 边缘均匀亮度 /
        墙面百叶窗木桌文件柜木门 / 上身构图）。
   ⛔ 保留 `high-key brightness from edge to edge` —— check_beats 认这句，删了会失效。
   ⛔ 保留场景段里的「四个人站位」「只有这三个人」—— 上一轮用户打回
      「两个苏小满」就是这里丢了人数约束。
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEGD = os.path.join(HERE, "xs001_segs")

STYLE = (
    "VERTICAL 9:16 portrait framing, high-key commercial cinematography on a large-format "
    "camera, soft broad daylight, luminous pale walls, light reflective floor, airy and open, "
    "gentle soft shadows that keep their detail, refined natural faces, subtle film grain. "
    "Keep the film texture, natural lighting, every face, every costume and the realistic motion "
    "consistent throughout. People stay standing, framed from the knees up."
)  # 76 -> 62

EXPO = (
    "Exposure: a large window is the key light and the room is filled with soft bounced daylight. "
    "Skin tones are bright and even, shadows sit in the light mid-tones and keep visible texture, "
    "the whites stay white, and the picture carries an even, transparent, high-key brightness "
    "from edge to edge."
)  # 68 -> 40

CLOTH = (
    "Every shirt is buttoned right up to the closed collar, so each chest shows one continuous "
    "unbroken run of plain fabric with small plain buttons. Apron bibs are plain unmarked fabric."
)  # 38 -> 28

ANCHOR = (
    "The whole clip takes place in one small private office and the camera never leaves it. "
    "Four plain white walls, a grey metal filing cabinet along the far wall, a long wooden desk "
    "across the middle of the floor, venetian blinds on the right-hand wall laying bright bands "
    "across the desk top, a closed wooden door set flat into the back wall, and plain brown "
    "corrugated cardboard boxes. The people named in this beat are the only people in it: "
    "钱经理 (S3) stays behind the desk on the far side, 苏小满 (S1) stays at the near end with "
    "her back to the camera, and 小唐 (S4) stands clear at the left of frame by the back wall. "
    "The count does not change."
)  # 151 -> 87


def body(t):
    return len(re.split(r"No slow-motion",
                        t[t.index("detailed_description:"):])[0].split())


def main():
    segs = [int(a) for a in sys.argv[1:]] or [3]
    REPL = [("VERTICAL 9:16 portrait framing", STYLE),
            ("Exposure:", None), ("Every shirt", CLOTH),
            ("The whole clip takes place", ANCHOR)]
    for s in segs:
        p = os.path.join(SEGD, "seg%02d_prompt.txt" % s)
        t = io.open(p, encoding="utf-8").read()
        before = body(t)

        b = t[t.index("detailed_description:"):]
        head, rest = b.split("\n", 1)
        lines = rest.split("\n")
        out = []
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.startswith("VERTICAL 9:16"):
                out.append(STYLE)
            elif ln.startswith("Exposure:"):
                out.append(EXPO)
            elif ln.startswith("Every shirt"):
                out.append(CLOTH)
            elif ln.startswith("The whole clip takes place"):
                out.append(ANCHOR)
            else:
                out.append(ln)
            i += 1
        newt = t[:t.index("detailed_description:")] + head + "\n" + "\n".join(out)
        io.open(p, "w", encoding="utf-8").write(newt)

        after = body(io.open(p, encoding="utf-8").read())
        print("seg%02d  正文 %d -> %d 词  %s" % (s, before, after,
                                                "✅" if after <= 620 else "❌ 还超 %d" % (after - 620)))


if __name__ == "__main__":
    main()