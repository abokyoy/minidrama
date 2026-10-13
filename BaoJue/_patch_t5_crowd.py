# -*- coding: utf-8 -*-
"""修 xs001 第5 段（seg05「掏兜」）的反打镜头**凭空多人**问题。

【症状】2026-10-07 第一集重做，seg05 最后一镜：苏小满转身看向门口时，
        画面里凭空多出两个人（灰衣 + 深蓝）。实际这一镜只有她一个人。

【根因】Entry state 写了 3 个人（钱经理、苏小满、小唐在门边），
        但 [Shot 2] 是 `reverse single on 苏小满` —— 反打单人镜头，
        镜头对着她、她背后就是门。提示词**没写"这一镜只有她一个人"**，
        模型就把 Entry state 里"门边的小唐"当成需要画进画面的人→ 又多一个，
        再加它自动补的群演 = 凭空两人。

        这是老毛病「Entry state 与正文打架」的新变种：
        以前是两者说不同的话，这次是两者各说各的但**镜头视角没约束人数**。

【修法】在 Shot 2 / Shot 3 里显式锁人数：
        - Shot 2：`framed on her alone, one person in this shot`
        - Shot 3：`on her alone, no one else enters this frame`
        只改 seg05，seg01–04 一个字节不动（改完必做 sha 验证）。
"""
import io
import json
import os
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
JF = os.path.join(BASE, "xs001_beats", "scene11.json")

# 两个字段都要改（`shots` 备份用，`_lean_shots` 才是实际渲染来源）
OLD_TAIL = ("[Shot 3] At 00:09.400, close on the pocket under her fingers, "
            "the fabric pulled slightly taut. She is silent after that.")
NEW_TAIL = ("[Shot 3] At 00:09.400, close on the pocket under her fingers, "
            "the fabric pulled slightly taut, framed on her alone, "
            "no one else enters this frame. She is silent after that.")

OLD_S2 = ("[Shot 2] At 00:07.200, reverse single on 苏小满 (S1): she takes "
          "one small half-step back, and her right hand closes slowly over the "
          "fabric of her own trouser pocket; she speaks quietly and clearly in "
          "low steady Mandarin: [Chinese] 你们不能搜我。")
NEW_S2 = ("[Shot 2] At 00:07.200, reverse single on 苏小满 (S1), framed on her "
          "alone, one person in this shot, nobody behind her and nobody at the "
          "door: she takes one small half-step back, and her right hand closes "
          "slowly over the fabric of her own trouser pocket; she speaks quietly "
          "and clearly in low steady Mandarin: [Chinese] 你们不能搜我。")


def patch(text):
    if "framed on her alone" in text:
        return text, False
    n = 0
    if OLD_S2 in text:
        text = text.replace(OLD_S2, NEW_S2)
        n += 1
    if OLD_TAIL in text:
        text = text.replace(OLD_TAIL, NEW_TAIL)
        n += 1
    return text, n


def main():
    shutil.copy2(JF, JF + ".bak_p5")
    d = json.load(io.open(JF, encoding="utf-8"))
    segs = d if isinstance(d, list) else d.get("segments", [])

    changed = []
    for sg in segs:
        # 只动第 5 段（id 形如 xs001_t05）
        sid = str(sg.get("id", ""))
        if not (sid.endswith("t05") or sid.endswith("_t05")):
            continue
        for f in ("shots", "_lean_shots"):
            if f not in sg:
                continue
            sg[f], n = patch(sg[f])
            if n:
                changed.append("%s.%s" % (sid, f))
                print("  ✓ %s / %s 改了 %d 处" % (sid, f, n))

    if not changed:
        print("没找到要改的内容（可能已改过，或段 id 不匹配）")
        return
    io.open(JF, "w", encoding="utf-8").write(
        json.dumps(d, ensure_ascii=False, indent=1))
    print("已改：%s" % ", ".join(changed))
    print("备份：%s.bak_p5" % os.path.basename(JF))


if __name__ == "__main__":
    main()
