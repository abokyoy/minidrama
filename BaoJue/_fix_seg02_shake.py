# -*- coding: utf-8 -*-
"""修 seg02 的晃镜头。

用户 2026-10-08 15:02 反馈（看 off_xs01_t02_00011-audio.mp4）：
> 第一次 从钱经理切到苏小满 还可以  但是 从钱经理到小唐 就是晃过来的 后面都是晃的

逐镜核对机位后确认根因：
  Shot 2 Push In       → 推，整体平移，起点终点锚在人身上   ✅ 用户认可
  Shot 3 Truck Right   → 横移，同上                        ✅ 用户认可
  Shot 4 Tracking Shot → **相机跟着人走**                  ❌ 画面飘
  Shot 5 Arc Shot      → **相机绕着人转**                  ❌ 画面飘
  Shot 6 Pull Out      → 拉，整体平移                      ✅

→ 铁律：**快切段里禁用 Tracking Shot 和 Arc Shot**。
  相机自身移动的机位（跟拍/环绕）在 1.25 秒一刀的节奏下必然飘。
  只用「相机整体平移」类：Push In / Pull Out / Truck Left / Truck Right / Tilt / Pedestal，
  以及纯固定 Static Shot。
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "xs001_segs", "seg02_prompt.txt")

# ── 新镜头表：Shot4/5 换成不移动相机的机位，其余逐字保留 ──────────
SHOTS = (
    "[Shot 1] Static Shot, medium two-shot across the desk: 钱经理 (S3) on the far side with "
    "the filing cabinets behind his back, one palm flat on the wood; 苏小满 (S1) at the near end "
    "with her back to the camera; 小唐 (S4) against the back wall at the far left of frame, "
    "waiting.\n\n"
    "[Shot 2] At 00:01.250, Camera: Push In with small amplitude at fast speed, pushing in on "
    "钱经理 (S3) as he straightens up slowly, tucks both hands behind his back and tips his head "
    "to one side, fixing 苏小满 (S1) with the look of a man who has already decided; his collar "
    "catches the blind-light. His mouth opens and he speaks in a flat accusing Mandarin: "
    "[Chinese] 收台的时候，就你一个人在。\n\n"
    "[Shot 3] At 00:02.500, Camera: Truck Right with medium amplitude at fast speed, sliding "
    "sideways across the desk to a reverse single on 苏小满 (S1), the blind-laying light barring "
    "the wall behind her; her apron strap lifts slightly at the waist. She does not move her feet "
    "and does not look away, and she answers at once in a low steady Mandarin: [Chinese] 不是我。\n\n"
    # ⛔ 原 Tracking Shot（相机跟着人走 → 画面飘）→ 改 Static Shot：相机定住不动，
    #    只让人物自己转头。切换感靠硬切，不靠相机移动。
    "[Shot 4] At 00:03.750, Camera: Static Shot, holding the same wide frame as a man stops "
    "speaking and his eyes leave her; 钱经理 (S3) finishes the accusation and stops, and his eyes "
    "leave her; he turns his head and shoulders toward the left-hand wall. 苏小满 (S1) stays "
    "where she is, her eyes following his turn. The camera does not move at all through this beat.\n\n"
    # ⛔ 原 Arc Shot（相机绕着人转 → 画面飘）→ 改 Push In：相机沿直线推近，
    #    推到他脸上。仍然有推的动感，但相机路径是直的，不绕。
    "[Shot 5] At 00:05.000, Camera: Push In with small amplitude at fast speed, pushing straight "
    "in on 钱经理 (S3)'s face as he turns his head fully left and looks straight at 小唐 (S4) "
    "against the wall; the look lasts a beat and says everything. The camera travels in a straight "
    "line forward and does not swing around him.\n\n"
    "[Shot 6] At 00:06.500, Camera: Pull Out with large amplitude at slow speed, pulling out to "
    "reveal the whole office as 小唐 (S4) pushes off the wall with her shoulder and takes the "
    "first step forward, and 钱经理 (S3) gives one short jerk of his chin toward the open floor "
    "beside the desk; 苏小满 (S1) has gone very still, watching the colleague approach.\n\n"
    "From [Shot 4] through [Shot 6] the only mouth movement in frame is 钱经理 (S3) swallowing;\n"
    "every line of dialogue has already finished, and the office falls into room tone.\n\n"
    "No slow-motion, no soft dissolves, no fades, no unnecessary transitions; use hard cuts only "
    "and no on-screen text, letters, logos, subtitles, or watermarks."
)


def main():
    t = io.open(P, encoding="utf-8").read()
    m = re.search(r"\[Shot 1\].*?(?=\n\noverall_soundscape:)", t, re.S)
    if not m:
        print("!! 没找到镜头段，先看文件格式")
        return 1
    old = m.group(0)
    t2 = t[:m.start()] + SHOTS + t[m.end():]
    io.open(P, "w", encoding="utf-8").write(t2)

    # ── 自检 ────────────────────────────────────────────────
    print("原文机位 → 新机位")
    oc = re.findall(r"Camera: ([A-Z][a-zA-Z ]+?) with", old)
    nc = re.findall(r"Camera: ([A-Z][a-zA-Z ]+?) with", SHOTS)
    for a, b in zip(oc, nc):
        flag = "  (改)" if a != b else ""
        print("  %-16s -> %-14s%s" % (a, b, flag))

    BANNED = ("tracking shot", "arc shot", "whip pan")
    hit = [c for c in nc if c.lower() in BANNED]
    print("\n会晃的机位（跟拍/环绕/甩镜）: %s" % (hit or "0 个 ✅"))
    print("正文字数 %d（原来 %d）" % (len(SHOTS.split()), len(old.split())))
    if hit:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
