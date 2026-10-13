# -*- coding: utf-8 -*-
"""把 audit_onetake 接进 audit()：用 try/except 提前跳过，
不引入不存在的 finish()。"""
import io
import os
import py_compile

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_h3_audit.py")
src = io.open(P, encoding="utf-8").read()

# ── 1. 把收尾抽成一个本文件内的函数 report() ──
old_tail = '''    print("=" * 66)
    print(" H3 提示词审计: %s" % path)
    print("=" * 66)
    for line in ok:
        print("  [ok]   %s" % line)
    for line in bad:
        print("  [!!]   %s" % line)
    print("-" * 66)
    print(" 通过 %d 项 / 失败 %d 项" % (len(ok), len(bad)))
    return len(bad)'''
new_tail = '''    return report(path, ok, bad)'''
if old_tail in src and "def report(" not in src:
    src = src.replace(old_tail, new_tail, 1)
    rep = '''def report(path, ok, bad):
    print("=" * 66)
    print(" H3 提示词审计: %s" % path)
    print("=" * 66)
    for line in ok:
        print("  [ok]   %s" % line)
    for line in bad:
        print("  [!!]   %s" % line)
    print("-" * 66)
    print(" 通过 %d 项 / 失败 %d 项" % (len(ok), len(bad)))
    return len(bad)


'''
    anchor = "def audit(path):"
    src = src.replace(anchor, rep + anchor, 1)
    print("① 收尾已抽成 report()")

# ── 2. 主流程插 onetake 分支 ──
old = '''    shots = sorted(set(re.findall(r"\\[Shot (\\d+)\\]", t)))
    chk(1 <= len(shots) <= 8, "镜头数 %d" % len(shots),
        "镜头 %s 个（官方跑酷范本 10秒6刀；>7刀每刀不足1.5秒会糊）"
        % (shots or "-"))'''
new = '''    shots = sorted(set(re.findall(r"\\[Shot (\\d+)\\]", t)))

    # ══════════════════════════════════════════════════════════
    #  ⛔⛔⛔ 2026-10-09 20:15 一镜到底分支
    #  对白戏的正确形态 = 「正文零个 [Shot N]」。
    #  旧写法「6 刀都写 Camera: Static Shot, locked off」实测**照样被切三段**
    #  （抽帧实锤 off_xs01_t01_00014：f005 钱经理近景 / f017 小唐近景）。
    #  → `[Shot N]` 标记本身就是「在这里切一刀」的指令。锁景别只能防
    #    「切了之后构图不对」，**防不住「它就是要切」**。
    #  识别到 ONE CONTINUOUS TAKE 就切专用判据 + 跳过全部多镜头检查。
    # ══════════════════════════════════════════════════════════
    if re.search(r"ONE\\s+CONTINUOUS\\s+TAKE", body_only, re.I):
        audit_onetake(body_only, t, chk)
        n_sn = len(re.findall(r"^\\[Shot \\d\\]", body_only, re.M))
        chk(n_sn == 0, "镜头数0（一镜到底）",
            "一镜到底：正文 %d 个 [Shot N] 分段（必须 0）" % n_sn)
        common_tail_checks(body_only, t, chk)
        return report(path, ok, bad)

    chk(1 <= len(shots) <= 8, "镜头数 %d" % len(shots),
        "镜头 %s 个（官方跑酷范本 10秒6刀；>7刀每刀不足1.5秒会糊）"
        % (shots or "-"))'''
if old in src:
    src = src.replace(old, new, 1)
    print("② 主流程已加 onetake 分支")
else:
    print("⛔②没匹配到")
    raise SystemExit(1)

io.open(P, "w", encoding="utf-8").write(src)
print("写回完成")
try:
    py_compile.compile(P, doraise=True)
    print("✅ 语法通过")
except Exception as e:
    print("‼", e)
    raise SystemExit(1)