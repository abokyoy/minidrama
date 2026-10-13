# -*- coding: utf-8 -*-
"""补丁 2：修 scene12d.json 里的 T60 / T67（长台词拆拍）"""
import io
import os

B = r"E:\LLM\try\minidrama\保洁\ep001_beats"
FN = "scene12d.json"

PATCHES = [
    # T60：25 字拆 3 拍，不改一个字
    ("[Shot 1] Wide: the LEFT doorway crowd splits as 前台 (S12) shoulders through, phone held up in one hand, half running, blazer flying.\\n[Shot 2] At 00:00.400, medium: she comes straight to the desk, holds the phone up toward 钱经理 (S3) and rattles it out in a loud bright panicked Mandarin, at a shout, very fast and breathless, all in one rush: [Chinese] 钱经理！客人来电话了！耳钉找到了！掉在他自己车里，座位缝里！\\n[Shot 3] At 00:08.800, wide and held: the chair legs come down with a bang. Every single person in the room has gone still. Nobody says a word to 苏小满 (S1).\\n[Shot 4] At 00:09.600, hold on 苏小满 (S1) standing exactly where she was, no expression change at all.",
     "[Shot 1] Wide: the LEFT doorway crowd splits as 前台 (S12) shoulders through, phone held up in one hand, half running, blazer flying, and 前台 (S12) starts shouting before she is even through the door, in a loud bright panicked Mandarin: [Chinese] 钱经理！客人来电话了！\\n[Shot 2] At 00:04.000, medium: she is at the desk now, holding the phone up toward 钱经理 (S3), and 前台 (S12) goes on at a shout in one burst: [Chinese] 耳钉找到了！\\n[Shot 3] At 00:05.400, closer on her flushed face as 前台 (S12) finishes it in one rush: [Chinese] 掉在他自己车里，座位缝里！\\n[Shot 4] At 00:09.000, wide and held: the chair legs come down with a bang. Every single person in the room has gone still. Nobody says a word to 苏小满 (S1), who stands exactly where she was with no expression change at all."),

    # T67：24 字拆 3 拍
    ("[Shot 1] Medium: 小罗 (S7) holds the card up at chest height, addressing nobody in particular, in the same quiet courteous Mandarin, evenly, one clause at a time: [Chinese] 这张卡，三天前，是我们留给苏小姐的。\\n[Shot 2] At 00:08.400, he turns a quarter step and runs his eyes slowly around the room — the manager, the doorway crowd, the director — before he adds it, still perfectly polite: [Chinese] 让各位，误会了。\\n[Shot 3] At 00:09.400, wide and held: absolute stillness. 钱经理 (S3) has gone grey, 小唐 (S4) at the door is white as paper, and nobody in the doorway makes a sound.\\n[Shot 4] At 00:09.800, hold on 苏小满 (S1), the only person in the room who has not changed at all.",
     "[Shot 1] Medium: 小罗 (S7) holds the card up at chest height, addressing nobody in particular, in the same quiet courteous Mandarin, evenly: [Chinese] 这张卡，三天前，\\n[Shot 2] At 00:04.000, closer on 小罗 (S7) as he goes on, still perfectly level: [Chinese] 是我们留给苏小姐的。\\n[Shot 3] At 00:07.400, 小罗 (S7) turns a quarter step and runs his eyes slowly around the room — the manager, the doorway crowd, the director — before he adds it, still perfectly polite: [Chinese] 让各位，误会了。\\n[Shot 4] At 00:09.400, wide and held: absolute stillness. 钱经理 (S3) has gone grey, 小唐 (S4) at the door is white as paper, and nobody in the doorway makes a sound; 苏小满 (S1) is the only person in the room who has not changed at all."),
]

if __name__ == "__main__":
    p = os.path.join(B, FN)
    s = io.open(p, "r", encoding="utf-8").read()
    for old, new in PATCHES:
        if old not in s:
            print("MISS", old[:70])
            continue
        s = s.replace(old, new, 1)
        print("OK  ", new[:70])
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
