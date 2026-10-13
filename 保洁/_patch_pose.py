# -*- coding: utf-8 -*-
"""把 POSE_LIMITS 插进全部 STYLE 变体 + 渲染链。

为什么需要这一步：6 个 STYLE 变体（STYLE / STYLE_DUSK / STYLE_NIGHT /
STYLE_NIGHT_ROOM / STYLE_NIGHT_ROOM_SMALL / STYLE_NIGHT_PRACTICAL）
都是 `VERTICAL + SOFT_LIGHT + ...` 开头。POSE_LIMITS 必须**排在 VERTICAL 之后**，
因为 VERTICAL 段里已经在讲构图（"keep faces in the upper two thirds"），
放在它前面会被后面的话稀释。

渲染链里再额外加一份做双保险 —— 万一某段走了裸 ANCHORS 分支没带 STYLE。

幂等：已插入过就跳过，不会重复插。

用法：python _patch_pose.py && python storyboard_render.py ep001
"""
import ast
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storyboard_render.py")
MARK = "POSE_LIMITS +"


def main():
    s = io.open(P, encoding="utf-8").read()
    before = s.count(MARK)
    # 1) 6 个 STYLE 变体
    n = s.count("VERTICAL + SOFT_LIGHT +")
    s = s.replace("VERTICAL + SOFT_LIGHT +", "VERTICAL + POSE_LIMITS + SOFT_LIGHT +")
    # 2) 渲染链
    old = 'desc = (style + "\\n" + NO_TEXT + "\\n" + CROWD_RULES +'
    new = 'desc = (style + "\\n" + POSE_LIMITS + "\\n" + NO_TEXT + "\\n" + CROWD_RULES +'
    chain = old in s
    if chain:
        s = s.replace(old, new)
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    ast.parse(s)   # 语法自检：写坏了立刻发现，别等到渲染时才炸
    after = s.count(MARK)
    print("STYLE 变体 %d 处已插入；渲染链 %s" % (n, "已加" if chain else "未找到"))
    print("POSE_LIMITS 出现次数：%d → %d" % (before, after))
    print("语法自检 OK")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    main()
