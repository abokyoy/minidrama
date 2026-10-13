# -*- coding: utf-8 -*-
"""第二轮去工牌：光靠禁令治不住，必须**改服装设计让工牌无处可挂**。

【为什么第一轮不够】
2026-10-07 第一轮：重画参考图 + 加全局禁令「no name badge, no lanyard...」，
结果是工牌**从大块变小块**，但还在，而且名字会串（钱经理戴上苏小满的名字）。
→ **禁令是被执行了的（尺寸变了 = 听懂了），但模型的先验仍在补全**
  「中国保洁/职员角色 → 胸口必须挂东西」。
→ 这是 diffusion 的典型行为：**「不要X」不能消灭 X 的先验，只能降低概率。**

【这一轮的做法：从物理上消灭挂点】
不是再说"不要"，而是让**画面里根本没有能挂东西的位置**：
1. 苏小满 / 小唐 / 阿芳：**外面套一件敞开的深色长款工装外套/罩衫**
   （housekeeping coat）—— 厚重的翻领挡住整个胸口，物理上挂不了工牌。
2. 钱经理：**外面套一件敞开的黑色西装外套**（不进扣子），
   翻领盖住马甲和衬衫那片最容易挂牌的位置。
3. 周总监 / 张总等本来就是西装（有翻领），保持。

【关键：把禁令措辞从「不要X」改成「这里什么都没有，因为被X挡住了」】
给出**原因**而不是**否定**，模型更愿意照做。

幂等：已改过的再跑报 MISS。
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(BASE, "storyboard_render.py")

PATCHES = [
    # ── 苏小满：加长款工装外套 ──
    ("苏小满 (S1)",
     'a 25-year-old female cleaner. Preserve her exact face, small lean build, "\n'
     '   "centre-parted black hair in a low practical ponytail, plain dark-navy housekeeping shirt with rolled "\n'
     '   "sleeves, a worn grey-blue apron over navy trousers, black cloth shoes and a small keyring at her waist. "',
     'a 25-year-old female cleaner. Preserve her exact face, small lean build, "\n'
     '   "centre-parted black hair in a low practical ponytail, plain dark-navy housekeeping shirt with rolled "\n'
     '   "sleeves, a worn grey-blue apron over navy trousers, black cloth shoes and a small keyring at her waist, "\n'
     '   "and a heavy dark-navy housekeeping coat worn OPEN over the top with wide flat lapels. "'),

    # ── 小唐 ──
    ("小唐 (S4)",
     'a 22-year-old female cleaning-team colleague. Thin, pale, narrow shoulders, "\n'
     '   "shifty sidelong eyes, light-grey work uniform, hair tied back.',
     'a 22-year-old female cleaning-team colleague. Thin, pale, narrow shoulders, "\n'
     '   "shifty sidelong eyes, light-grey work uniform, hair tied back, and a heavy charcoal-grey "\n'
     '   "housekeeping coat worn OPEN over the top with wide flat lapels covering her whole chest.'),

    # ── 阿芳 ──
    ("阿芳 (S5)",
     'a 45-year-old female cleaning-team colleague. Round face, short dark hair, plain and "\n'
     '   "kind, deep-blue work uniform.',
     'a 45-year-old female cleaning-team colleague. Round face, short dark hair, plain and "\n'
     '   "kind, deep-blue work uniform with a heavy dark-blue housekeeping coat worn OPEN over the top, "\n'
     '   "its wide flat lapels covering her whole chest.'),

    # ── 钱经理：加敞开的黑西装外套 ──
    ("钱经理 (S3)",
     'white shirt with a dark grey waistcoat, "\n'
     '   "dark trousers and a plain buttoned waistcoat with nothing pinned or clipped to his chest.',
     'white shirt with a dark grey waistcoat, "\n'
     '   "dark trousers, and a black suit jacket worn OPEN over the top with broad satin lapels "\n'
     '   "falling over the waistcoat and covering his whole chest.'),
]


def main():
    s = io.open(F, encoding="utf-8").read()
    if not os.path.exists(F + ".bak_coat"):
        io.open(F + ".bak_coat", "w", encoding="utf-8").write(s)
        print("备份：storyboard_render.py.bak_coat")

    done = []
    for name, old, new in PATCHES:
        if new in s:
            print("  – %s：已是新版，跳过" % name)
            continue
        if old not in s:
            print("  ✗ %s：没找到原文（需人工核对）" % name)
            continue
        s = s.replace(old, new, 1)
        done.append(name)
        print("  ✓ %s：已加外套" % name)

    if not done:
        print("\n没有改动")
        sys.exit(1)

    io.open(F, "w", encoding="utf-8").write(s)
    print("\n已改：%s" % ", ".join(done))


if __name__ == "__main__":
    main()
