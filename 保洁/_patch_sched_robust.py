# -*- coding: utf-8 -*-
"""给 run_segment 加异常兜底：任何一步炸了都要把片退回 pending，
⛔ 绝不能让它卡在 running（卡在 running = 永远不会被 next_pending 捡起来
= 那一链永远卡住 = GPU 空转）。

2026-10-09 20:10。
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scheduler.py")
src = io.open(P, encoding="utf-8").read()

# ── 1. 插 back_to_pending 函数（放在 ensure_comfy 之前） ──
if "def back_to_pending(" not in src:
    anchor = "def ensure_comfy():"
    fn = (
        'def back_to_pending(sid, why=""):\n'
        '    """把片退回 pending。⛔ 卡在 running 的片永远不会被 next_pending 捡起来。"""\n'
        '    led = L.load()\n'
        '    v = L.S(led, sid)\n'
        '    v["status"] = L.ST_PENDING\n'
        '    v["out"] = None\n'
        '    v["run_epoch"] = None\n'
        '    v["started_at"] = None\n'
        '    hist = v.get("history") or []\n'
        '    hist.append("退回pending: " + why)\n'
        '    v["history"] = hist[-8:]\n'
        '    L.save(led)\n'
        '    log("  ↩ seg%02d 已退回 pending（%s）" % (sid, why))\n'
        '\n'
        '\n'
    )
    assert anchor in src, "找不到 ensure_comfy"
    src = src.replace(anchor, fn + anchor, 1)
    print("① 已插入 back_to_pending()")

# ── 2. ensure_comfy 调用包 try ──
old = ('    ensure_comfy()\n'
       '    env = dict(os.environ)')
new = ('    try:\n'
       '        ensure_comfy()\n'
       '    except SystemExit:\n'
       '        back_to_pending(sid, "ComfyUI 起不来")\n'
       '        raise\n'
       '    except Exception as e:\n'
       '        log("‼ seg%02d 启 ComfyUI 异常：%r" % (sid, e))\n'
       '        back_to_pending(sid, "启 ComfyUI 异常 %r" % (e,))\n'
       '        return "error"\n'
       '    env = dict(os.environ)')
if old in src:
    src = src.replace(old, new, 1)
    print("② ensure_comfy 已包 try")
else:
    print("⛔② ensure_comfy 那段没匹配到 —— 需人工看")

# ── 3. 提交 subprocess 包 try ──
old = ('    p = subprocess.run([sys.executable, "-u", DRIVER, "--qjob=" + jf, "--qsubmit"],\n'
       '                       capture_output=True, text=True, encoding="utf-8",\n'
       '                       errors="replace", timeout=900, env=env, cwd=HERE)\n'
       '    out = (p.stdout or "") + (p.stderr or "")')
new = ('    try:\n'
       '        p = subprocess.run([sys.executable, "-u", DRIVER, "--qjob=" + jf, "--qsubmit"],\n'
       '                           capture_output=True, text=True, encoding="utf-8",\n'
       '                           errors="replace", timeout=900, env=env, cwd=HERE)\n'
       '    except Exception as e:\n'
       '        log("‼ seg%02d 提交进程异常：%r" % (sid, e))\n'
       '        back_to_pending(sid, "提交进程异常 %r" % (e,))\n'
       '        return "error"\n'
       '    out = (p.stdout or "") + (p.stderr or "")')
if old in src:
    src = src.replace(old, new, 1)
    print("③ 提交 subprocess 已包 try")
else:
    print("⛔③ 提交那段没匹配到 —— 需人工看")

# ── 4. 提交失败也退回 pending ──
old = ('        log("!! seg%02d 提交失败：%s" % (sid, out[-600:]))\n'
       '        return "error"')
new = ('        log("‼ seg%02d 提交失败：%s" % (sid, out[-600:]))\n'
       '        back_to_pending(sid, "提交失败")\n'
       '        return "error"')
if old in src:
    src = src.replace(old, new, 1)
    print("④ 提交失败已退回 pending")
else:
    print("⛔④ 提交失败那段没匹配到")

io.open(P, "w", encoding="utf-8").write(src)
print("写回完成")

# ── 5. 语法自检 ──
import py_compile
try:
    py_compile.compile(P, doraise=True)
    print("✅ 语法自检通过")
except Exception as e:
    print("‼ 语法错误：", e)