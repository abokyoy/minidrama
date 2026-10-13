# -*- coding: utf-8 -*-
"""ep003 第②层审核整改 · 补丁 B
修复 A 版补丁的漏项：A 版只改中 shots 字段，而 summary / soundscape 是另写的一段散文，
同一句意思措辞不同，于是旧文案留了下来 —— 而 summary 同样会被拼进提示词。
本补丁专门清理 summary / soundscape 里残留的「致暗」措辞（用户反馈成片偏黑）。
"""
import json, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))

TOTAL = [0, 0]

def patch(fname, pairs):
    p = os.path.join(BASE, "ep003_beats", fname)
    raw = open(p, encoding="utf-8").read()
    ok = 0
    for old, new in pairs:
        n = raw.count(old)
        if n == 1:
            raw = raw.replace(old, new); ok += 1; continue
        if n == 0 and new in raw:
            ok += 1; continue          # 已应用过，幂等跳过
        print("  ! %s 命中 %d 次：%s" % (fname, n, old[:70]))
    json.loads(raw)            # 语法自检，坏 JSON 绝不落盘
    open(p, "w", encoding="utf-8").write(raw)
    print("  ok %s  生效 %d/%d 条" % (fname, ok, len(pairs)))
    return ok

# ---- scene31：门楼下是白天，明令「bright and airy」。原文却写「dark doorway / the black of the doorway」，
#      与自己的光照档打架，且会把门洞拍成一团死黑。改成「深门洞 / 门洞深处的暗影」，保留纵深但不压曝光。
TOTAL[0] += patch("scene31.json", [
 ("eyes still on the dark doorway",
  "eyes still on the deep inner doorway"),
 ("as the dark of the doorway swallows half her back",
  "as the deep doorway closes over half her back"),
 ("the hollow echo inside the dark doorway waiting for her",
  "the hollow echo inside the high doorway waiting for her"),
 ("sinking into the black of the doorway",
  "sinking into the deep shade of the doorway"),
])
TOTAL[1] += 4  # 已计入返回值

# ---- scene32：忠叔退回门房的写法是「退进阴影 / 一旦进了暗处」，这是**打光指令**不是环境描述，
#      H3 会照做，把门房拍黑。shots 字段 A 版已改，这里补 summary。
TOTAL[0] += patch("scene32.json", [
 ("retreats into the shadow of the gatehouse and lowers his head, yet once in the dark his eyes still follow half a beat after the direction she walks.",
  "steps back into the deep corner of the gatehouse and lowers his head, yet even from there his eyes still follow half a beat after the direction she walks."),
])
TOTAL[1] += 1

# ---- scene36：全剧最后一镜。summary 写「整个房间只有台灯下一小块亮着」= 高对比暗调，
#      正是用户说的「阴影过重、不柔和」。A 版改了 shots，summary 漏改。
TOTAL[0] += patch("scene36.json", [
 ("In the whole narrow room only the one small patch under the lamp is lit, and inside it there are only an old photograph and a face; she never answers the questions she has just put.",
  "The lamp's warm soft pool holds one old photograph and one face, and the little room stays softly readable all around them; she never answers the questions she has just put."),
 ("the warm light lying along her cheek while the room beyond her stays dim",
  "the warm light lying along her cheek while the little room beyond her stays soft and readable"),
])
TOTAL[1] += 2

print("ep003 补丁 B 完成：成功 %d / %d 条" % (TOTAL[0], TOTAL[1]))
