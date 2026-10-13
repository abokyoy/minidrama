# -*- coding: utf-8 -*-
"""清掉**分镜源文件**里残留的工牌描述（`storyboard_render.py` 之外的第二层）。

【为什么还要清这一层】
`storyboard_render.py` 只管人物设定和空间锚点，
但**每一段的分镜正文（`shots` / `_lean_shots`）也可能有工牌**。
2026-10-07 实测：xs001_seg01 里就有
    「his charcoal waistcoat swinging and his staff badge bouncing」
—— 这是动作描述，渲染器改不到，模型照样会画工牌。

【怎么找的】按集扫 `*_beats/*.json` 里含 `badge` 的行，逐条人工确认后替换。
不要用正则乱改 —— 「badge」在不同上下文含义不同，
本项目实测都属于「胸前挂的那块」，才统一改成「nothing pinned to it」。

幂等：已改过的文件再跑会报 MISS，属正常。
"""
import glob
import io
import json
import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

# (旧, 新) —— 都已人工核对上下文，确认是"胸前挂的那块"
PAIRS = [
    # ⚠️ 上下文原样抄自 scene11.json（含前导 "of the desk, "），
    #    上一版凭印象少写了开头几个词 → 匹配不上、"没有文件需要改"。
    #    **教训：替换对必须从文件里grep 出来抄，不能凭记忆写。**
    ("his charcoal waistcoat swinging and his staff badge bouncing",
     "his charcoal waistcoat swinging and nothing pinned to his chest"),
    ("his staff badge bouncing",
     "nothing pinned to his chest"),
    ("with a staff badge on her chest",
     "with nothing pinned to her chest"),
    ("the work badge on her chest",
     "her chest plain and bare"),
]


def patch_text(t):
    n = 0
    for old, new in PAIRS:
        if old in t:
            n += t.count(old)
            t = t.replace(old, new)
    return t, n


def main():
    files = sorted(glob.glob(os.path.join(BASE, "*_beats", "*.json")))
    changed = {}
    for f in files:
        src = io.open(f, encoding="utf-8").read()
        new, n = patch_text(src)
        if not n:
            continue
        # 解析→改→写回（保证 JSON 合法），再逐字段改一次以防跨字段漏改
        try:
            d = json.loads(new)
        except Exception as e:
            print("  ✗ %s 改后 JSON 非法，跳过：%s" % (os.path.basename(f), e))
            continue
        total = n
        def walk(o):
            if isinstance(o, str):
                return patch_text(o)[1]
            if isinstance(o, list):
                return sum(walk(x) for x in o)
            if isinstance(o, dict):
                return sum(walk(v) for v in o.values())
            return 0
        total = walk(d)
        if not total:
            continue
        shutil.copy2(f, f + ".bak_nobadge")
        io.open(f, "w", encoding="utf-8").write(
            json.dumps(d, ensure_ascii=False, indent=1))
        changed[os.path.relpath(f, BASE)] = total

    if not changed:
        print("没有文件需要改（可能已清过）")
        return
    print("已改：")
    for k, v in changed.items():
        print("   %-34s %d 处" % (k, v))
    print("\n复查各源文件 badge 残留：")
    left = 0
    for f in files:
        s = io.open(f, encoding="utf-8").read()
        c = s.lower().count("badge")
        if c:
            print("   ✗ %s 还有 %d 处" % (os.path.basename(f), c))
            left += c
    print("   总残留 = %d %s" % (left, "✓" if left == 0 else "← 需人工看"))
    sys.exit(0)


if __name__ == "__main__":
    main()
