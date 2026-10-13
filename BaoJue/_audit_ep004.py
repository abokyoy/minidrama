# -*- coding: utf-8 -*-
"""生成 _verify10_ep004.md 的逐段检查表（机械列自动取数，判断列人工编码）"""
import json, os, re

files = ["scene41a.json", "scene41b.json", "scene42.json", "scene43.json", "scene44.json"]
segs = []
for f in files:
    segs.extend(json.load(open(os.path.join("ep004_beats", f), encoding="utf-8")))

NAME = {"S1": "苏小满", "S3": "钱经理", "S4": "小唐", "S7": "小罗",
        "S11": "医生", "S15": "陆崇", "S16": "心腹", "S20": "护士长"}

SILENT_NEAR = set()
for s in segs:
    low = s["soundscape"].lower()
    if any(w in low for w in ["quiet", "still air", "stillness", "then quiet"]):
        SILENT_NEAR.add(s["id"])

TEXT_RISK = {"ep04_t17", "ep04_t36", "ep04_t68", "ep04_t85", "ep04_t101", "ep04_t103"}

FIT = {"ep04_t41", "ep04_t49", "ep04_t54", "ep04_t61", "ep04_t63", "ep04_t70", "ep04_t92"}

STUDY_LIGHT = {s["id"] for s in segs if s["scene"] == "4-4"}

SEVERE = {
    "ep04_t12": "医生被推到近景前景，自相矛盾且违锚点",
    "ep04_t16": "医生被推到近景前景，违 4-1b 锚点",
    "ep04_t25": "工牌在 t24 拍于近端，t25 却在远端他手边",
    "ep04_t33": "同事与小唐凭空出现（t22–t32 从未在场）",
    "ep04_t37": "钱经理无交代回到远端",
    "ep04_t38": "钱经理又跳回近景前景（承 t37 链式）",
    "ep04_t81": "手电从货架瞬移回她手里",
    "ep04_t83": "她已带手电出门，手电却回到货架上",
    "ep04_t94": "回溯动作「一直在敲」前段从未建立",
    "ep04_t101": "文件从心腹手里回到桌面",
    "ep04_t103": "文件位置同 t101，且语义倒错",
    "ep04_t104": "文件位置同 t101",
}
SEVERE_NOTE = {"ep04_t94"}  # 94 归一般，见下

MINOR = {
    "ep04_t02": "入场说笔在胸前口袋，Shot 2 笔已在手",
    "ep04_t05": "手从「悬空未碰」变成「搭在台面」（承 t04 链式）",
    "ep04_t08": "声景 quiet 近亲词",
    "ep04_t15": "声景写明「四秒不说话」",
    "ep04_t52": "refs 缺 suxiaoman（她本人入画）",
    "ep04_t58": "声景写「光束刮擦货架」",
    "ep04_t61": "台词内出现未注册人名「陆总」",
    "ep04_t93": "配乐三连之一",
    "ep04_t95": "配乐三连之一",
    "ep04_t97": "配乐三连之一",
    "ep04_t101": "另有 the the 重复字",
}
MINOR.pop("ep04_t101", None)  # 101 已判严重

rows = []
for s in segs:
    sid = s["id"]
    shots = s["shots"]
    lines = re.findall(r"\[Chinese\]([^\n]*)", shots)
    n = sum(len(re.findall(r"[\u4e00-\u9fff]", L)) for L in lines)
    tags = sorted(set(re.findall(r"\((S\d+)\)", shots)), key=lambda x: int(x[1:]))
    spk = "／".join(f"{NAME.get(t, t)} {t}" for t in tags) if lines else "—"

    sil = "注意" if sid in SILENT_NEAR else "合格"
    txt = "注意" if sid in TEXT_RISK else "合格"
    words = len(shots.split())

    if sid in SEVERE and sid not in SEVERE_NOTE:
        anc, verdict = "✗ " + SEVERE[sid], "**严重**"
    elif sid in SEVERE_NOTE:
        anc, verdict = "△ " + SEVERE[sid], "整改"
    elif sid in MINOR:
        anc, verdict = "✓", "整改"
    elif sid in FIT:
        anc, verdict = "✓ 台词超时", "整改"
    elif sid in SILENT_NEAR or sid in TEXT_RISK:
        anc, verdict = "✓", "整改"
    elif sid in STUDY_LIGHT:
        anc, verdict = "△ 天花板灯≠参考图的落地灯", "整改"
    elif words < 100:
        anc, verdict = "✓", "整改"
    else:
        anc, verdict = "✓", "通过"

    rows.append((sid, spk, n if lines else "—", sil, "合格", txt, anc, verdict, words))

out = ["| 段号 | 说话人 | 台词字数 | 声景 | 曝光 | 文字 | 锚点 | 结论 |",
       "|---|---|---|---|---|---|---|---|"]
for r in rows:
    out.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % r[:8])
print("\n".join(out))
print()
print("TOTAL", len(rows))
print("严重", sum(1 for r in rows if r[7] == "**严重**"))
print("整改", sum(1 for r in rows if r[7] == "整改"))
print("通过", sum(1 for r in rows if r[7] == "通过"))
print("声景注意", len(SILENT_NEAR), "文字注意", len(TEXT_RISK), "台词超时", len(FIT))
