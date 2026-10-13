# -*- coding: utf-8 -*-
"""xs001 t01「人物复制」整改补丁（幂等，可重复运行）

═══════��� 事故 ════════
用户反馈：`D:\\output\\new\\xs01_t01_00001.mp4` 「人走到一半 突然复制出另一个一样的人来」。
逐帧核查（_frame_dump.py，20 帧）发现的**不是**单一一次复制，而是**持续增员**：

| 帧   | 现象                                              |
|------|---------------------------------------------------|
| 0001 | 2 人（苏小满在桌前，钱经理刚进门）✅              |
| 0005 | 3 人 —— 门框处凭空多出**一个小唐** ❗            |
| 0012 | 4 人 —— 右侧又冒出**第二个钱经理**（同马甲同发型）❗ |
| 0013 | 4 人 —— 背景柜子右侧持续站着第四个人 ❗           |
| 0017 | 5 人 —— **凭空多出一个苏小满** ❗                |

→ 人数 2 → 3 → 4 → 5，**每一拍都在增员**。人脸检测器只数到 1 张脸
  （多出来的人都是侧脸/背身/低分辨率，检测器抓不到），所以检测器**发现不了这个问题**。

═══════ 根因（不是参数问题，是提示词结构问题）═══════
1. **Shot 1 一句话塞了两次「人进入画面」**：
   `钱经理 (S3) strides in` + `小唐 (S4) slips in behind him`。
   H3 ref2v 只有 10 秒，要在一个镜头里演两次入场 → 每次重绘门框区域就多复制一份在场人物。
   H3 是「逐帧重绘」，不是「录一段视频」——它不知道「已经有人进来了」，
   门框这种**高对比边框**是它最容易重绘失败的区域，于是每帧都在门框上长出新的人。
2. **给小唐写了一个框内位置**（`presses her back to the wall just inside the door`），
   等于给了 H3 一个「门框旁边应该站个人」的锚 → 每帧门框都自动补一个人。
3. **空间锚点 ANCHOR_12 里本来就写着** `The onlookers crowd the open doorway on the LEFT`
   + `小唐 (S4) starts against the wall just inside the LEFT door`
   → 和 Shot 1 的描述叠加，H3 拿到「门口有好几个人」+「小唐在门边」的组合
   → 门框被当成「人群区」无限增殖。

═══════ 修法 ═══════
A. **Shot 1 只让一个人进画面**（钱经理）。小唐改成「一开始就在画面里、站在门边墙角」，
   不是「跟着进来」。→ 全段只有**一次**入场动作。
B. **显式写死人数上限**：`EXACTLY three people in this shot: ... no other person enters,
   no one is duplicated, no one appears in the doorway behind them.`（H3 对否定句不可靠，
   所以正反两面都写：正面点名三人 + 反面禁止第四人）
C. **删掉「门口聚人」的锚点**（本段专用覆盖，不改全局 ANCHOR_12，避免影响 ep001–005）
D. **门框只作前景框边，不作站人位**：明写门框区域保持空、只有门框本身
E. **ref_notes** 给 office_pano 降级：办公桌是「背景陈设参考」，不作为构图依据
   （H3 容易照抄参考图里被裁掉的人）
"""

import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
BEATS = os.path.join(BASE, "xs001_beats", "scene11.json")

# 本段专用的空间锚点覆盖：删掉「门口聚人」那句，改成「门口空、只有三个人」
ANCHOR_T01 = (
    "Fixed spatial set-up for this whole take, never change it and never re-arrange: "
    "the door is on the LEFT of frame and it STAYS CLOSED AND EMPTY for the entire take — "
    "the doorway is a bare doorframe with nothing standing in it and nobody passing through it. "
    "There are EXACTLY THREE PEOPLE in this shot, always the same three, never a fourth: "
    "钱经理 (S3), 苏小满 (S1) and 小唐 (S4). Nobody else is in the room, nobody is in the corridor, "
    "no bystanders, no onlookers, no staff. "
    "苏小满 (S1) stands on the NEAR side of the desk on the RIGHT half of frame, back to the door, "
    "facing the far side, and she NEVER moves from that spot for the entire take. "
    "钱经理 (S3) enters through the LEFT door ONCE in the first two seconds, then STANDS STILL at the "
    "far side of the desk for the rest of the take, and he never walks in again. "
    "小唐 (S4) is ALREADY STANDING STILL in the far LEFT corner of frame when the take begins — "
    "she never walks in, she never passes through the door, she just stays pressed against that corner "
    "wall, in the LEFT third of frame and clearly separate from the doorframe. "
    "No person is duplicated, cloned, split into two, or fades in and out. "
    "The number of people never increases and never decreases. Never mirror or swap any of this."
)

# 本段 shots 全部重写
NEW_SHOTS = (
    "Entry state, re-anchored to the reference image: the bright property office of 万山大厦 — "
    "the door on the LEFT of frame is a bare closed doorframe with nothing in it, the venetian-blind "
    "window and the tall wooden cabinets are on the RIGHT, the chestnut-wooden desk stands across the "
    "middle of the room. EXACTLY THREE PEOPLE are present, the same three in every single frame: "
    "苏小满 (S1) in navy housekeeping uniform stands still on the NEAR side of the desk on the "
    "RIGHT half of frame with her back to the door; 钱经理 (S3) in a white shirt and charcoal waistcoat "
    "stands at the FAR side of the desk with his back to the window; 小唐 (S4) in a light-grey "
    "cleaning uniform stands still in the far LEFT corner of frame, flat against the wall, well "
    "inside the room and clear of the doorframe. The doorway, the corridor beyond it and the whole "
    "right-hand background stay empty of any further person for the entire take. Warm midday light "
    "comes through the blinds in long bright bands.\n"
    "[Shot 1] Wide, one continuous camera move, no cut: all three people are ALREADY in the room at "
    "the very first frame and all three are visible at once — there is NO entrance, nobody walks in, "
    "the door stays shut. 钱经理 (S3) strides the two paces from the far side of the door to the far "
    "side of the desk, his charcoal waistcoat swinging and his staff badge bouncing, and comes to a stop. "
    "苏小满 (S1) does not move at all. 小唐 (S4) does not move at all, she stays against the LEFT "
    "corner wall with only her eyes moving. The three of them are the only people in frame.\n"
    "[Shot 2] At 00:03.000, medium over the desk: 钱经理 (S3) at the far side plants both feet wide, "
    "leans forward on straight arms and slams his open palm flat onto the desktop; the palm lands flat "
    "against the bare desk. 苏小满 (S1) holds her ground on the near side, still unmoved. "
    "小唐 (S4) is still in the LEFT corner, unmoved. Three people, no more.\n"
    "[Shot 3] At 00:04.200, closer on 钱经理's (S3) flushed face as he announces it in a loud nasal "
    "Mandarin, filing each item like a charge sheet: [Chinese] 三楼包厢。贵客丢了一只金耳钉。三万八。\n"
    "[Shot 4] At 00:08.400, reverse over the desk onto 苏小满 (S1) on the near side, the blind-light "
    "barring the wall behind her: she stands perfectly still, both hands loose at her sides, chin "
    "level, eyes on him. Her mouth stays closed and she says nothing. 小唐 (S4) is still a small "
    "figure in the LEFT corner. The room is empty apart from these three."
)

NEW_SUMMARY = (
    "Interior of a bright modern property office at midday. EXACTLY THREE PEOPLE are present "
    "throughout and the number never changes: a young female cleaner in a navy housekeeping uniform "
    "standing still on the near side of a dark wooden desk, a middle-aged male property manager in a "
    "white shirt and charcoal waistcoat who strides two paces and slams his palm on the desk, and a "
    "young female colleague in a light-grey cleaning uniform standing motionless against the far LEFT "
    "corner wall. The left-hand door stays closed and the doorway stays empty — no one enters, no one "
    "leaves, no one is duplicated. Venetian-blind light bands fall across the room."
)

NEW_SOUND = (
    "Hard brisk footsteps on the tiled floor, the flat slap of a palm on wood, a chair creaking, "
    "the blind slats settling, the buzz of the ceiling fluorescent panels, a wall clock ticking, "
    "faint muffled traffic through the blinds."
)


def main():
    d = json.load(io.open(BEATS, encoding="utf-8"))
    hit = 0
    for s in d:
        # ── 全 5 段都是同一个 3 人室内场景（办公室搜卡）──
        # 所以 crowd=False 对 5 段全部成立，不只 t01。
        # 依据：CROWD_RULES 的「at most two background faces may be recognisable」
        # 在 3 人戏里等于许可 H3 加背景脸；t01 实测就是背景长到 5 个人。
        s["crowd"] = False
        if s["id"] != "xs01_t01":
            continue
        hit += 1
        s["shots"] = NEW_SHOTS
        s["summary"] = NEW_SUMMARY
        s["soundscape"] = NEW_SOUND
        s["anchor"] = ANCHOR_T01
        # 明确本段只有 3 个人：参考图只留 3 人 + 1 场景，且给场景图降级
        s["refs"] = ["qianjingli", "suxiaoman", "xiaotang", "office_pano"]
        s["ref_notes"] = {
            "office_pano": (
                "the property office of 万山大厦 seen empty, used for LAYOUT, FURNITURE and DAYLIGHT "
                "reference ONLY. Do NOT copy any person, figure, silhouette or body part that happens "
                "to be visible in this picture — the people in this shot come only from <Subject 1>, "
                "<Subject 2> and <Subject 3>. The room contains no other human being."
            )
        }
    if not hit:
        raise SystemExit("没找到 xs01_t01，检查 beats")
    io.open(BEATS, "w", encoding="utf-8").write(
        json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print("✓ 5 段全部 crowd=False；xs01_t01 深度整改")
    print("  · Shot 1 改为「三人在场、无人进门」（消除两次入场）")
    print("  · 新增本段专用锚点：门关闭且空，明确「EXACTLY THREE PEOPLE」")
    print("  · office_pano 降级为纯布景/光线参考，禁止抄参考图里的人")
    cn = re.findall(r"\[Chinese\]\s*([^\[\n]*)", NEW_SHOTS)
    n = sum(len(re.findall(r"[\u4e00-\u9fff]", x)) for x in cn)
    print("  台词 %d 字 / %d 句（10 秒上限 24 字）" % (n, len(cn)))


if __name__ == "__main__":
    main()
