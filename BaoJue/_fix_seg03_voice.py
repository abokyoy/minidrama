# -*- coding: utf-8 -*-
"""重写 seg03：台词被苏小满抢说（2026-10-09 22:17 用户打回）。

⛔⛔⛔ 病根是两条写法叠加，不是「写错了谁说」：
  提示词里归属写得完全正确 —— `小唐 (S3) speaks: [Chinese] 没看清。`
  但成片里这句话被**苏小满**说了。

  为什么？两条自己写的东西在反向推：
  ① `his eyes locked on 苏小满 (S2) … and not on 小唐 (S3)` 出现 **2 次**
     → 钱经理的视线两次钉在苏小满身上
  ② `and not on 小唐 (S3)` 是**否定句**
     → 我反复念叨「不要看小唐」= 反复把小唐推进注意力中心
        （否定句实体化，已在「凭空多个男人」「走廊是空的」上踩过 6 次）

  净效果：模型判定「画面焦点 = 苏小满」→ 把唯一的台词给了她。
  **说话人归属写对了也会被「谁在画面中心」抢走。**

✅ 正确写法（改 4 处）：
  1.⛔ 删光 `and not on 小唐` 这类否定（全部改成正面描述）
  2. 钱经理的视线改成「看桌面上的文件夹」这种中性正面描述，
     不再看任何一方（他的视线不参与焦点竞争）
  3. 小唐的台词**紧贴她的动作**，中间不插别人
  4. 用正面表述锁死唯一说话人：`the only mouth that moves in frame`
     —— ✅这是可观测的正面描述，不是否定句
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "xs001_segs", "seg03_prompt.txt")
s = io.open(P, encoding="utf-8").read()
o = s

BODY = (
    "ONE CONTINUOUS TAKE, medium three-shot on 钱经理 (S1), 苏小满 (S2) and 小唐 (S3) in "
    "the middle of the room, framed from the knees up, camera locked off for all ten seconds: "
    # 小唐先出场，动作和台词紧贴在一起，中間不插别人
    "小唐 (S3) stands beside the grey sofa at frame right in left profile facing left towards "
    "the desk, and she lowers her eyes to the floor and keeps her head bowed away from the desk "
    "the entire time; her fingers curl tight around the sofa's wooden arm and her jaw sets "
    "trembling; she is the only person in frame whose mouth moves, and it opens wide enough to "
    "shape every syllable as she answers in a small thin nervous voice high in her throat: "
    "小唐 (S3) speaks, her mouth opening wide as she answers, [Chinese] 没看清。 "
    # 钱经理：视线改成中性正面描述（不参与焦点竞争），并明写嘴不动
    "钱经理 (S1) is behind the L-shaped desk with his body square to the desk and his head "
    "tilted down towards the folder lying flat on the wood in front of him; his lips stay "
    "pressed shut and his jaw does not move. "
    # 苏小满：明写嘴不动
    "苏小满 (S2) stands at the near left corner of the desk in right profile facing right "
    "towards him, both feet flat on the tile, her hands still at her sides and her chin level; "
    "her lips stay pressed shut and her jaw does not move. "
    "The framing never changes once: the same three people stay visible in the same three "
    "places at the same size from the first frame to the last, and the open doorway at "
    "frame left shows only the corridor wall beyond it."
)

i = s.find("ONE CONTINUOUS TAKE")
j = s.find("\n\n", i)          # 一镜到底整段结束（下一个空行）
assert i >= 0 and j > i, "定位失败"
s = s[:i] + BODY + s[j:]

# ⛔ 清掉站位段里所有 "not on 小唐" 否定句
for bad in (" and not on 小唐 (S3) beside the sofa",
            " and not on 小唐 (S3)",
            ", not on 小唐 (S3)"):
    if bad in s:
        s = s.replace(bad, "")
        print("删否定句: %s" % bad)

# 站位段里钱经理的视线也改成中性
s = s.replace(
    "his body square to the desk and his head turned to the right, his eyes locked on 苏小满 (S2) "
    "at the near left corner of that desk",
    "his body square to the desk and his head tilted down towards the folder lying flat on the "
    "wood in front of him", 1)

io.open(P, "w", encoding="utf-8").write(s)

print("=" * 52)
print("seg03 已重写：%d -> %d 字符" % (len(o), len(s)))
print("-" * 52)
for k in ("not on 小唐", "eyes locked on", "nobody", "the only person in frame whose mouth moves",
          "[Shot"):
    print("  %-38s %d" % (k, s.count(k)))