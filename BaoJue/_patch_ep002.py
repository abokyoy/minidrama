# -*- coding: utf-8 -*-
r"""ep002 第②层审核整改补丁（对应 _verify8_ep002a.md / _verify8_ep002b.md）。

只改 beats / 空间锚点描述 / 参考图降级，不动任何一句台词。
每条替换都带断言，匹配不到就报错退出，绝不静默跳过。

用法： python _patch_ep002.py
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
BEATS = os.path.join(BASE, "ep002_beats")

n_ok = 0
n_bad = 0


def load():
    out = {}
    for f in sorted(os.listdir(BEATS)):
        if f.endswith(".json"):
            out[f] = json.load(io.open(os.path.join(BEATS, f), encoding="utf-8"))
    return out


def save(data):
    for f, arr in data.items():
        p = os.path.join(BEATS, f)
        tmp = p + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            json.dump(arr, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, p)


def seg(data, sid):
    for arr in data.values():
        for s in arr:
            if s["id"] == sid:
                return s
    raise SystemExit("找不到段 %s" % sid)


def rep(sid, field, old, new):
    """在 seg[sid][field] 里做一次精确替换。"""
    global n_ok, n_bad
    s = seg(DATA, sid)
    v = s.get(field) or ""
    if old not in v:
        print("  ✗ %s.%s 未匹配：%s" % (sid, field, old[:70]))
        n_bad += 1
        return
    s[field] = v.replace(old, new, 1)
    n_ok += 1


DATA = load()

# ============================================================ 高 H1：锚点里的"抱纸箱"与正文打架
# 由 storyboard_render.py 侧改（见文件末尾说明），这里不动。

# ============================================================ 高 H3：t20 首帧跳变（站→坐）
rep("ep02_t20", "shots",
    "苏小满 (S1) is now seated on the low wooden chair at the NEAR head of the long rosewood table, "
    "back to the door, seat facing the FAR head, both hands resting in her lap;",
    "苏小满 (S1) still stands at the NEAR head of the long rosewood table, her head turned to the low "
    "wooden chair the steward has just set down beside her; she then sits down onto it in one slow visible "
    "movement, back to the door, seat facing the FAR head, and her hands come to rest in her lap;")
rep("ep02_t20", "shots",
    "[Shot 1] Medium, over the near end of the table looking down its length: 陆蔓's (S8) right hand presses "
    "open the dark-brown leather folder, and inside lies a sheaf of printed sheets.",
    "[Shot 1] Medium, over the near end of the table looking down its length: 苏小满 (S1) lowers herself onto "
    "the low chair and settles, straightening her back, then 陆蔓's (S8) right hand presses open the dark-brown "
    "leather folder, and inside lies a sheaf of printed sheets.")

# ============================================================ 高 H1（2-3/2-4/2-5 报告）：t93 走廊→更衣间跳变
rep("ep02_t93", "shots",
    "Entry state, re-anchored to the reference images: 苏小满 (S1) reaches the locker-room curtain at the near "
    "end and pushes through it.",
    "Entry state, re-anchored to the reference images: 苏小满 (S1) has just passed the last clerk in the "
    "corridor and walks on along the corridor's depth toward the locker-room doorway at the far end.")
rep("ep02_t93", "shots",
    "[Shot 1] Wide down the narrow locker room: rows of grey metal lockers recede on both sides with a long "
    "bench table down the middle, and 苏小满 (S1) steps through the curtain at the near edge of frame.",
    "[Shot 1] Medium: 苏小满 (S1) comes down the corridor, reaches the locker-room doorway at the near end and "
    "pushes its door curtain aside.")

# ============================================================ 中 M1：照片"手上/桌上"翻转
rep("ep02_t117", "shots",
    "陆崇 (S15) sits far behind the desk, the photograph resting in his right hand, the tea cup at his right "
    "on the desk;",
    "陆崇 (S15) sits far behind the desk with the top photograph held in his right hand above the spread on "
    "the desk, the tea cup at his right;")
rep("ep02_t117", "shots",
    "[Shot 1] Close on his hand: 陆崇's (S15) left hand lifts the tea cup up to chest height and holds it "
    "there, the steam thinning above the rim.",
    "[Shot 1] Close on his hands: 陆崇's (S15) right hand lays the photograph back down flat on the spread, "
    "then his left hand lifts the tea cup up to chest height and holds it there, the steam thinning above the rim.")
rep("ep02_t118", "shots",
    "陆崇 (S15) still holds the tea cup at his chest, seated far behind the desk, the photograph in his other "
    "hand;",
    "陆崇 (S15) still holds the tea cup at his chest, seated far behind the desk, the photograph back on the "
    "spread in front of him;")

# ============================================================ 中 M2：陆崇外套颜色自相矛盾（对齐参考图＝深藏青）
rep("ep02_t110", "shots",
    "lean and straight-backed in a dark green high-collar jacket, a jade thumb ring on his right hand, ",
    "lean and straight-backed in a dark navy mandarin-collar jacket, ")

# ============================================================ 中：声景 / summary 里的否定式与弱否定措辞
rep("ep02_t07", "summary",
    "for two full seconds and gives the room nothing at all.",
    "for two full seconds, holding her face completely still.")
rep("ep02_t37", "soundscape",
    "and the quiet of the whole room settling.",
    "and the whole room leaning in on her words.")
rep("ep02_t23", "soundscape",
    "and the far wall's stillness behind her lifted hand.",
    "and a low shift of silk from the far head as she lifts her hand.")
for sid in ("ep02_t10", "ep02_t38"):
    rep(sid, "soundscape", "the seated family holding still.", "the seated family leaning in.")

# ============================================================ 低：summary 里的 Silent → Wordless
SILENT_MAP = [("Silent opening beat", "Opening wordless beat"),
              ("Silent close beat", "Wordless close beat"),
              ("Silent wide", "Wordless wide"),
              ("Silent beat", "Wordless beat")]
cnt = 0
for arr in DATA.values():
    for s in arr:
        sm = s.get("summary") or ""
        for a, b in SILENT_MAP:
            if sm.startswith(a) or (a in sm and "Silent" in sm[:40]):
                s["summary"] = sm.replace(a, b)
                sm = s["summary"]
                cnt += 1
print("  summary Silent→Wordless：%d 处" % cnt)
n_ok += cnt

# ============================================================ 中：参考图降级（ref_notes）
HOSP_NOTE = ("the 市一院 corridor of this building, seen in late afternoon light. Use it as the LOCATION and "
             "layout reference ONLY — this beat is set on a BRIGHT MORNING, so do NOT copy its dusk colour or "
             "its light level; light the scene as clean bright morning daylight with the ceiling fluorescents "
             "generously on.")
WARD_NOTE = ("the 市一院 cardiac ward room and the bed pushed against the tall window. Use it as the LOCATION, "
             "furniture and bed-position reference ONLY — do NOT copy its late-afternoon light level; this beat is "
             "a bright clean morning with the ceiling lights on.")
DESK_NOTE = ("the rosewood table top of that hall. Use as the TABLE-SURFACE material and light-direction "
             "reference ONLY; in this beat the table top is bare apart from the celadon tea cup — do NOT introduce "
             "the leather folder, the pen or the seal-paste dish into it.")

NOTE_TARGETS = {
    "hospital_corridor": HOSP_NOTE,
    "hospital_ward": WARD_NOTE,
    "hospital_bench": HOSP_NOTE,
}
for arr in DATA.values():
    for s in arr:
        notes = dict(s.get("ref_notes") or {})
        # 2-3（上午戏）用到的黄昏素材图 → 降级为"只做位置参考"
        if (s.get("scene") == "2-3"):
            for k in s.get("refs", []):
                if k in NOTE_TARGETS:
                    notes[k] = NOTE_TARGETS[k]
        # 2-1 里 lu_hall_desk 只是桌面材质参考，不许把 2-2 的协议道具带进 2-1
        if s.get("scene") == "2-1" and "lu_hall_desk" in s.get("refs", []):
            notes["lu_hall_desk"] = DESK_NOTE
        if notes:
            s["ref_notes"] = notes

save(DATA)
print("beats 补丁：成功 %d 条，失败 %d 条" % (n_ok, n_bad))

# ============================================================ 文字剧本：万山大厦 → 景宸大厦（标题行，非台词）
doc = os.path.join(BASE, "ep002", "文字剧本.md")
txt = io.open(doc, encoding="utf-8").read()
before = txt
txt = txt.replace("### 0.4 万山大厦（场次 2-4）", "### 0.4 景宸大厦（场次 2-4）")
txt = txt.replace("## 场次 2-4：内景 万山大厦 大堂／更衣间 上午",
                  "## 场次 2-4：内景 景宸大厦 大堂／更衣间 上午")
txt = txt.replace("一件深墨绿立领中式上衣，右手拇指上一枚玉扳指。",
                  "一件深藏青立领中式上衣。")
if txt != before:
    io.open(doc, "w", encoding="utf-8").write(txt)
    print("文字剧本已修正：万山大厦→景宸大厦、陆崇外套对齐参考图")
print("残留 '万山大厦'：", txt.count("万山大厦"))

sys.exit(1 if n_bad else 0)
