# -*- coding: utf-8 -*-
"""补丁 3：补说话人编号 + 修 T59 时间窗"""
import io
import os

B = r"E:\LLM\try\minidrama\保洁\ep001_beats"

PATCHES = [
    ("scene12b.json",
     "Medium: she goes on without pause, still with no gesture beyond one small open palm, speaking in low even Mandarin as if reading out a fact:",
     "Medium: 苏小满 (S1) goes on without pause, still with no gesture beyond one small open palm, speaking in low even Mandarin as if reading out a fact:"),
    ("scene12b.json",
     "Medium: she keeps her eyes level with his and finishes the thought in the same flat, unhurried Mandarin, one hand still at her side:",
     "Medium: 苏小满 (S1) keeps her eyes level with 钱经理 (S3) and finishes the thought in the same flat, unhurried Mandarin, one hand still at her side:"),
    ("scene12b.json",
     "Close: she speaks quickly but with no hurry in her face, in a low fluent Mandarin that runs the clauses together, her gaze steady on him:",
     "Close: 苏小满 (S1) speaks quickly but with no hurry in her face, in a low fluent Mandarin that runs the clauses together, her gaze steady on 钱经理 (S3):"),

    ("scene12d.json",
     "[Shot 2] At 00:06.600, closer on his face as he adds the second half with a slow grin, and lets his forefinger start tapping the desktop:",
     "[Shot 2] At 00:04.600, closer on 钱经理's (S3) face as he adds the second half with a slow grin, and lets his forefinger start tapping the desktop:"),

    ("scene14b.json",
     "Medium: she looks him over once, from his collar to his shoes, with no surprise at all, and says it in her low flat Mandarin, half sigh and half statement:",
     "Medium: 苏小满 (S1) looks 小罗 (S7) over once, from his collar to his shoes, with no surprise at all, and says it in her low flat Mandarin, half sigh and half statement:"),
    ("scene14b.json",
     "Close: she looks straight at him and says the first one in her low flat Mandarin, stating it rather than accusing:",
     "Close: 苏小满 (S1) looks straight at 小罗 (S7) and says the first one in her low flat Mandarin, stating it rather than accusing:"),
    ("scene14b.json",
     "At 00:05.000, she goes on without pausing, still perfectly level:",
     "At 00:05.000, 苏小满 (S1) goes on without pausing, still perfectly level:"),
    ("scene14b.json",
     "Close: she finishes it in her low flat Mandarin, with one small nod as if confirming a fact to herself as much as to him:",
     "Close: 苏小满 (S1) finishes it in her low flat Mandarin, with one small nod as if confirming a fact to herself as much as to 小罗 (S7):"),
]

if __name__ == "__main__":
    ok = 0
    for fn, old, new in PATCHES:
        p = os.path.join(B, fn)
        s = io.open(p, "r", encoding="utf-8").read()
        if old not in s:
            print("MISS", fn, old[:60])
            continue
        io.open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
        print("OK  ", fn, new[:60])
        ok += 1
    print("成功 %d/%d" % (ok, len(PATCHES)))
