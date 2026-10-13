# -*- coding: utf-8 -*-
"""彻底去掉「工牌」，用户 2026-10-07 拍板。

【用户原话】「人物衣服上左胸前挂的工牌 都是错误的 都是显示乱码
  一是 中文都看上去怪怪的 字体很奇怪 二是总容易弄错
  现在都是写的苏小满，我的决定是 不要工牌」

【为什么必须连锚点一起改】空间锚点里写着
   「with the work badge on her chest until he tears it off and slaps it down on the table」
   —— 这不只是描述，是**剧情动作**（撕工牌拍桌上）。
   只删人物设定里的badge，锚点照样会把工牌拽回来。

【改了哪5 处】
   1. 钱经理 "and a staff badge"                → 改成"胸前什么都不挂"
   2. 前台"and a small name badge"              → 改成"plain closed collar"
   3. 医生 "an ID badge clipped to the coat pocket" → 改成"all coat pockets flat and empty"
   4. 收费员 "with a staff badge on her chest"  → 改成"plain closed collar"
   5. 空间锚点 "the work badge on her chest until he tears it off..."
      → 改成"her chest plain and bare"，
        道具动作改成「他把文件夹拍在桌上」（压迫感保留，不凭空造工牌）

【另外】新加一条 NO_BADGE 全局禁令进 STYLE，所有人物一律胸前干净。
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(BASE, "storyboard_render.py")

# (说明, 旧, 新)
PATCHES = [
    ("钱经理",
     "dark trousers and a staff badge. His voice is loud",
     "dark trousers and a plain buttoned waistcoat with nothing pinned or clipped to his chest. His voice is loud"),

    ("前台",
     "silk neck scarf and a small name badge, low heels. ",
     "silk neck scarf and a plain closed collar, low heels. "),

    ("医生",
     "an ID badge clipped to the coat pocket, black leather shoes.",
     "all coat pockets flat and empty, black leather shoes."),

    ("收费员",
     "with a staff badge on her chest and an ordinary ",
     "with a plain closed collar and an ordinary "),

    ("锚点·人物状态",
     "centre, with the work badge on her chest until he tears it off and "
     "slaps it down on the table. ",
     "centre, her chest plain and bare with nothing pinned or clipped to it. "),

    ("锚点·道具动作",
     "Everything done with the badge, the stack of claim forms",
     "Everything done with the clipboard he puts down on the table, the stack of claim forms"),
]


def main():
    s = io.open(F, encoding="utf-8").read()
    backup = F + ".bak_nobadge"
    io.open(backup, "w", encoding="utf-8").write(s)
    print("备份：%s" % os.path.basename(backup))

    done = []
    for name, old, new in PATCHES:
        n = s.count(old)
        if n == 0:
            print("  ✗ %s：没找到（可能已被改过）" % name)
            continue
        s = s.replace(old, new)
        done.append("%s(%d 处)" % (name, n))
        print("  ✓ %s：%d 处" % (name, n))

    if not done:
        print("没有任何改动，中止")
        sys.exit(1)

    io.open(F, "w", encoding="utf-8").write(s)
    print("\n已改：%s" % ", ".join(done))

    # 复查：文件里还剩几个 badge
    rest = [ln.strip()[:100] for ln in s.splitlines() if "badge" in ln.lower()]
    print("\n复查：文件里还剩 %d 行含 badge" % len(rest))
    for r in rest:
        print("   " + r)


if __name__ == "__main__":
    main()
