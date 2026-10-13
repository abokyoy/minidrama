# -*- coding: utf-8 -*-
"""给_h3_audit.py 加「一镜到底」分支。

⛔⛔⛔ 2026-10-09 20:15 第六次打回后的根因认识：
  之前我把「一镜到底」实现成「6 刀都写 Camera: Static Shot, locked off」，
  成片照样被模型切成三段（抽帧 f005 钱经理近景 / f017 小唐近景）。
  → **`[Shot N]` 这个标记本身就是「在这里切一刀」的指令**。
     景别锁死只能防「切了之后构图不对」，**防不了「它就是要切」**。

  ✅ 正确形态：正文里**一个 `[Shot N]` 都不出现**，开头写
     `ONE CONTINUOUS TAKE, <景别>, camera locked off for all ten seconds:`
     后面是一整段连续动作流。约束段再明说 `no cuts at all`。

  → 审计器原来硬要 `[Shot 1]`、硬要机位标注、硬数切点，
     一镜到底的写法全部报假红。**校验器本身也会骗人**（第7 次）。
     本补丁加 ONETAKE 分支：识别到就换判据集。
"""
import io
import os
import py_compile

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_h3_audit.py")
src = io.open(P, encoding="utf-8").read()

# ──1. 定义一镜到底的判据集合 ──
helper = '''

# ══════════════════════════════════════════════════════════════════
#  一镜到底（ONE CONTINUOUS TAKE）专用判据集
#  ⛔ 2026-10-09：对话戏的正确形态是「正文零个 [Shot N]」。
#    旧写法「6 刀都写 Static Shot」实测仍被模型切成三段 ——
#    [Shot N] 标记本身就是切镜指令，锁景别防不住「它就是要切」。
# ══════════════════════════════════════════════════════════════════
ONETAKE_HEAD = re.compile(
    r"ONE CONTINUOUS TAKE,\\s*"
    r"(medium-wide three-shot|medium two-shot|medium three-shot|"
    r"medium close-up|medium shot|wide shot|two-shot|three-shot)\\s*", re.I)


def audit_onetake(body_only, txt, chk):
    """一镜到底模式的判据。返回检查项数由外部统计。"""
    m = ONETAKE_HEAD.search(body_only)
    chk(bool(m), "一镜到底开头（ONE CONTINUOUS TAKE, 景别）",
        "正文必须以 `ONE CONTINUOUS TAKE, <景别>, camera locked off for all ten seconds:` 开头")
    if m:
        sz = m.group(1)
        # 景别必须出现在整个正文里，且前后一致（同一段里不能换词）
        allsz = re.findall(
            r"medium-wide three-shot|medium two-shot|medium three-shot|"
            r"medium close-up|medium shot|wide shot", body_only)
        from collections import Counter
        cnt = Counter(x.lower() for x in allsz)
        top, n = cnt.most_common(1)[0] if cnt else ("-", 0)
        chk(n == 1 or (len(cnt) == 1),
            "一镜到底景别只写一次且不换词",
            "景别词全文出现 %s（出现多次会让模型以为要换景别 = 要切）" % dict(cnt))

    # 核心：正文里绝不能有 [Shot N]
    ns = re.findall(r"^\\[Shot \\d\\]", body_only, re.M)
    chk(not ns, "正文零个 [Shot N]（=不切镜）",
        "一镜到底模式下正文出现 %d 个 [Shot N] —— ⛔这个标记本身就是切镜指令"
        % len(ns))
    chk(not re.search(r"At \\d\\d:\\d\\d\\.\\d\\d\\d", body_only),
        "一镜到底无切点时间戳",
        "⛔ 出现 `At MM:SS.mmm` = 明确告诉模型这里切一刀，应删掉")

    # 相机必须锁死
    chk("locked off" in body_only.lower(), "相机锁死 locked off",
        "开头必须写 `camera locked off for all ten seconds`")
    # 约束段必须明说不切
    chk(re.search(r"no cuts at all|never cuts", body_only, re.I),
        "约束段明写 no cuts",
        "⛔ 约束段必须明说 `one single unbroken take with no cuts at all` "
        "（旧写法 `use hard cuts only` 是在鼓励剪切，与一镜到底直接矛盾）")
    # ⛔ 不能出现鼓励切镜的措辞
    bad = [w for w in ("hard cut", "hard cuts", "cut to", "cuts to",
                       "multiple shots", "shot changes")
           if w in body_only.lower()]
    chk(not bad, "无鼓励切镜的措辞",
        "⛔ 一镜到底里出现 %s —— 这些词在命令模型切镜头" % bad)
    # 三个人必须全程可见且位置不变
    chk(re.search(r"stay visible in the same", body_only),
        "人员全程同位",
        "必须写 `the same N people stay visible in the same N places at the same size`")
'''
if "def audit_onetake(" not in src:
    # 插在 def chk 之前或文件靠前位置
    anchor = "def main("
    if anchor in src:
        src = src.replace(anchor, helper.strip() + "\n\n\n" + anchor, 1)
    else:
        src = src.replace("def chk(", helper.strip() + "\n\n\ndef chk(", 1)
    print("① 已插入 audit_onetake()")

io.open(P, "w", encoding="utf-8").write(src)
print("写回完成")
try:
    py_compile.compile(P, doraise=True)
    print("✅ 语法自检通过")
except Exception as e:
    print("‼ 语法错误：", e)