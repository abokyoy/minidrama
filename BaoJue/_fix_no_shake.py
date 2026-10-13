# -*- coding: utf-8 -*-
r"""把 seg03/04/05 的晃镜机位换成稳定机位（跟 seg02 定版方案一致）。

用户 2026-10-08 16:13 定版：`off_xs01_t02_00013` 验证通过
  Shot1 Static → Shot2 Push In → Shot3 Truck Right → Shot4 Static → Shot5 Static → Shot6 Pull Out
⛔ 禁用三类：Whip Pan / Tracking Shot / Arc Shot（相机自身在动 → 快切下画面飘）
⛔ 一支 10 秒里 Push In 最多 1 次（连着两刀推 → 脸糊）
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEGD = os.path.join(HERE, "xs001_segs")

# Tracking（跟拍）→ Static（相机锁死）；Arc（环绕）→ Truck（直线平移）
# 反向按实际内容挑：跟拍那句改成相机不动，环绕那句改成直线横移。
REPL = [
    # ── Tracking Shot：相机跟着人走 ────────────────────────
    (r"Camera: Tracking Shot with (?:medium|small|large) amplitude at fast speed, "
     r"tracking ([^.]*?)\.",
     r"Camera: Static Shot, holding the same wide frame while \1."
     r" The camera is locked off and does not move, follow, pan, or track in this beat."),
    # ── Arc Shot：相机绕着人转 ──────────────────────────
    (r"Camera: Arc Shot with (?:medium|small|large) amplitude at fast speed, "
     r"(?:arcing|arc-ing)[^.]*?,\s*",
     r"Camera: Truck Left with medium amplitude at fast speed, sliding sideways across the room, "),
]

# 改完追加的定版收尾（每段都要有，声明相机不动）
LOCK_SUFFIX = (" The camera travels in a straight line and stays level, "
               "and every wall, desk edge and cabinet in the background holds a fixed "
               "position through this beat.")


def fix(seg):
    p = os.path.join(SEGD, "seg%02d_prompt.txt" % seg)
    t = io.open(p, encoding="utf-8").read()
    old = t

    for pat, rep in REPL:
        def sub(m):
            s = m.group(0)
            s = re.sub(r"Camera: (?:Tracking Shot|Arc Shot)[^,]*, ", "", s)
            s = re.sub(r"(?:tracking|arcing|arc-ing)[^.]*?\.?", "", s)
            return rep.split(r"\1")[0] + (m.group(1) + rep.split(r"\1")[1]
                                          if r"\1" in rep else "")
        t = re.sub(pat, sub, t)

    # ⛔ Push In 最多 1 次：多了就替换成 Static
    n_push = t.count("Push In")
    if n_push > 1:
        # 把第 2 处之后的 Push In 段整体换成 Static（只换机位短语）
        idx = t.find("Push In")
        idx2 = t.find("Push In", idx + 1)
        head, tail = t[:idx2], t[idx2:]
        tail = tail.replace("Camera: Push In with small amplitude at fast speed, ",
                            "Camera: Static Shot, ", 1)
        tail = re.sub(r"(pushing (?:straight )?in on)",
                      r"locked off on the same framing, the camera does not move and only \1",
                      tail, count=1)
        t = head + tail

    if t == old:
        print("  seg%02d  无改动（可能已经是定版机位）" % seg)
        return False
    io.open(p, "w", encoding="utf-8").write(t)
    return True


def report(seg):
    p = os.path.join(SEGD, "seg%02d_prompt.txt" % seg)
    t = io.open(p, encoding="utf-8").read()
    m = re.search(r"\[Shot 1\].*?(?=\n\noverall_soundscape:)", t, re.S)
    body = m.group(0) if m else t
    cams = re.findall(r"Camera: ([A-Z][a-zA-Z ]+?) with", body)
    shots = re.findall(r"^\[Shot (\d+)\]", body, re.M)
    # 没有 Camera: 的镜头 = 纯 Static
    n = len(shots)
    stat = n - len(cams)
    bad = [c for c in cams if c.lower() in ("tracking shot", "arc shot")]
    bad += ["Whip Pan"] * t.count("Whip Pan")
    print("  seg%02d  %d刀  机位 %s  %s"
          % (seg, n, " → ".join(c.strip() for c in cams),
             ("（另 %d 刀纯 Static）" % stat) if stat else ""))
    print("          晃镜 %s   PushIn %d 次   %s"
          % (bad or "0 个 ✅", t.count("Push In"), "✅" if not bad else "❌"))
    return not bad


if __name__ == "__main__":
    segs = [int(a) for a in sys.argv[1:]] or [3, 4, 5]
    print("改前：")
    ok = True
    for s in segs:
        report(s)
    print()
    print("修改中…")
    for s in segs:
        fix(s)
    print()
    print("改后：")
    for s in segs:
        if not report(s):
            ok = False
    sys.exit(0 if ok else 1)
