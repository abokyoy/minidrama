# -*- coding: utf-8 -*-
r"""让三个人物外观**明显不同** —— 修「小唐长成苏小满的脸」。

用户 2026-10-08 20:01 打回 t03_00007：
> 「这一版 两个苏小满 那个小唐 是苏小满的脸」

两条根因（都实测确认）：
  1. `<Subject 3>` 写着「It is the person shown in <Picture 3>」，
     但我**只给了 2 张参考图** → Picture 3 不存在 → 小唐没脸可用
     → 模型拿苏小满的脸来凑。
  2. 两人都是 ponytail + 灰/浅灰围裙 + black cloth shoes，区分度不够。

修法：
  · 参考图恢复 3 张（人数 = 图数，不是「越少越安全」）
  · 小唐给**可观测的差异特征**：圆脸婴儿肥 / 宽间距眼 / 短平鼻 / 小嘴 /
    短脖子窄肩 / 齐刘海下巴长的低马尾 / 天蓝色（与苏小满的深藏青区分）
  · 苏小满改成**披肩直发**（不再是马尾），进一步拉开
  · ⛔ 每句都写「与苏小满明显不同」，防止模型靠拢
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEGD = os.path.join(HERE, "xs001_segs")

NEW = {
"钱经理": (
    "<Subject 1> — 钱经理: a 45-year-old male property manager, the only man in the clip. "
    "Slightly overweight, slicked-back oily hair, round face, an ingratiating smile that flips "
    "into a scowl, white shirt buttoned up to the closed collar under a dark grey buttoned "
    "waistcoat, dark grey trousers and black leather shoes. His voice is loud, nasal and "
    "bullying, standard Mandarin. It is the person shown in <Picture 1>."
),
"苏小满": (
    "<Subject 2> — 苏小满: a 25-year-old female cleaner, the taller of the two women and the "
    "only one with hair worn fully loose. Preserve her exact face, small lean build, long "
    "centre-parted black hair worn loose and straight down past her shoulders with no tie and "
    "no bangs, plain dark-navy button-up work shirt buttoned up to the closed collar with its "
    "own small plain buttons down the front, a worn grey apron over dark navy trousers, black "
    "cloth shoes. Her face is slim with a high narrow cheekbone line and a long jaw. Her voice "
    "is low, steady and slightly hoarse, standard Mandarin. It is the person shown in <Picture 2>."
),
"小唐": (
    "<Subject 3> — 小唐: a 22-year-old female cleaning-team colleague, the shorter of the two "
    "women and visibly younger. ⛔ Her face is clearly a different face from 苏小满 (S1): a small "
    "round face with full soft cheeks, wide-set round eyes, a short flat nose, a small closed "
    "mouth, a short thin neck and narrow sloping shoulders. Her black hair is cut level with her "
    "jaw, has straight blunt bangs cut across her forehead, and is tied into one short low "
    "ponytail at the nape. She wears a pale sky-blue button-up work shirt with a pointed collar, "
    "pale sky-blue trousers and a pale sky-blue apron tied round her waist, a noticeably lighter "
    "blue than the dark navy worn by 苏小满 (S1). Her voice is small, thin and nervous. It is "
    "the person shown in <Picture 3>."
),
}


def fix(seg):
    p = os.path.join(SEGD, "seg%02d_prompt.txt" % seg)
    t = io.open(p, encoding="utf-8").read()
    n = 0
    for name, new in NEW.items():
        pat = re.compile(r"<Subject \d> — " + name + r":.*?(?=\n<Subject |\n\nsummary:)", re.S)
        if pat.search(t):
            t = pat.sub(lambda m: new, t, count=1)
            n += 1
    io.open(p, "w", encoding="utf-8").write(t)
    return n


if __name__ == "__main__":
    segs = [int(a) for a in sys.argv[1:]] or [3]
    for s in segs:
        n = fix(s)
        p = os.path.join(SEGD, "seg%02d_prompt.txt" % s)
        t = io.open(p, encoding="utf-8").read()
        pics = sorted(set(re.findall(r"<Picture (\d+)>", t)))
        # ⛔ 校验：三个人物都写了与苏小满「明显不同」
        diff = t.count("different face from") + t.count("only one with hair worn fully loose") \
               + t.count("only man in the clip")
        print("seg%02d  改 %d/3 个人物  Picture引用=%s  差异化标记 %d 处  %d 词"
              % (s, n, pics, diff, len(t.split())))
        # 提取三个人物开头的身份标识，人工核对
        for m in re.finditer(r"<Subject \d> — ([^:]+):", t):
            print("      Subject %s" % m.group(1))