# -*- coding: utf-8 -*-
r"""把 seg03 正文压到 620 词以内（用户 2026-10-08 20:13 明确要求）。

⛔ 之前我一直说「seg02 认可的版本是 778 词，所以不压」——
   这是拿「别人也超标」当不修的理由。用户明确要求压到 620，执行。

压的原则（⛔ 不能把画面改差）：
  · **场景/风格/曝光/服装四段是逐字常量，seg01-05 都在用** → 不动
    （动了就跟已认可段脱节）
  · 只压**镜头段**：每刀 60-70 词足够，官方范本 6 刀共 560 词 ≈ 每刀 93 词，
    但官方那是纯动作片无对白；对白段镜头可以更短。
  · 保留全部关键识别特征（三人服装颜色区分、脸型差异）。
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEGD = os.path.join(HERE, "xs001_segs")

# 压缩版镜头段：6 刀，每刀 ≤62 词，识别特征一个不减
SHOTS = {
"03": (
    "[Shot 1] Static Shot, medium three-shot, exactly three people: 钱经理 (S3) behind the "
    "desk in his white shirt and dark grey waistcoat; 小唐 (S4) on the open floor beside it, "
    "shorter than 苏小满 (S1), in pale sky-blue; 苏小满 (S1) at the near end with her back to "
    "the camera, taller, in dark navy with her long black hair loose down her back. The count "
    "does not change.\n\n"
    "[Shot 2] At 00:01.250, Camera: Push In with small amplitude at fast speed, pushing in on "
    "钱经理 (S3) as he finishes looking at 小唐 (S4) and turns his eyes onto 苏小满 (S1); his "
    "collar catches the blind-light and his palm stays flat on the wood. His mouth stays shut "
    "through this beat.\n\n"
    "[Shot 3] At 00:02.500, Camera: Truck Left with medium amplitude at fast speed, sliding "
    "sideways to a closer single on 小唐 (S4): blunt straight bangs across her forehead, "
    "jaw-length hair swinging once as her shoulders come up, her small round face with full "
    "cheeks turned three-quarters away, the pale sky-blue of her uniform reading clearly against "
    "the pale wall. She speaks in a small thin nervous Mandarin: "
    "[Chinese] 钱经理。中午，我看见她往兜里塞东西。没看清。\n\n"
    "[Shot 4] At 00:03.750, Camera: Static Shot, holding the same three-person frame: 钱经理 "
    "(S3) still behind the desk in dark grey, 苏小满 (S1) at the near end in dark navy, 小唐 (S4) "
    "on the open floor at the left of frame in pale sky-blue, clearly a different person from "
    "苏小满 (S1). The camera is locked off and does not move, follow, pan, or track in this "
    "beat.\n\n"
    "[Shot 5] At 00:05.000, Camera: Truck Left with medium amplitude at fast speed, sliding "
    "sideways and settling on 钱经理 (S3) from the chest up; his palm lies flat on the wood, the "
    "blind-light band runs across his waistcoat, and his eyes stay on 苏小满 (S1) off to the "
    "right of frame. The camera travels in a straight line and stays level.\n\n"
    "[Shot 6] At 00:06.500, Camera: Pull Out with large amplitude at slow speed, pulling out to "
    "reveal the whole office, still exactly three people: 钱经理 (S3) behind the desk, 苏小满 "
    "(S1) at the near end with her back to the camera in dark navy, 小唐 (S4) on the open floor "
    "in pale sky-blue. The count does not change.\n\n"
    "From [Shot 4] through [Shot 6] the only mouth movement in frame is 钱经理 (S3) swallowing; "
    "every line of dialogue has already finished, and the office falls into room tone.\n\n"
    "No slow-motion, no soft dissolves, no fades, no unnecessary transitions; use hard cuts only "
    "and no on-screen text, letters, logos, subtitles, or watermarks."
),
}


def body_words(t):
    b = t[t.index("detailed_description:"):]
    b = re.split(r"No slow-motion", b)[0]
    return len(b.split())


def main():
    segs = [int(a) for a in sys.argv[1:]] or [3]
    for s in segs:
        p = os.path.join(SEGD, "seg%02d_prompt.txt" % s)
        t = io.open(p, encoding="utf-8").read()
        before = body_words(t)

        m = re.search(r"\[Shot 1\].*?(?=\noverall_soundscape:)", t, re.S)
        if not m:
            print("seg%02d 没找到镜头段" % s)
            continue
        head, tail = t[:m.start()], t[m.end():]
        new = SHOTS.get("%02d" % s)
        if new is None:
            print("seg%02d 没准备压缩版镜头" % s)
            continue
        io.open(p, "w", encoding="utf-8").write(head + new + tail)

        after = body_words(io.open(p, encoding="utf-8").read())
        print("seg%02d  正文 %d -> %d 词  %s" % (s, before, after,
                                                "✅" if after <= 620 else "❌ 还超"))


if __name__ == "__main__":
    main()