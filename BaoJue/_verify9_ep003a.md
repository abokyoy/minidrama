# ep003 场次 3-1 / 3-2 / 3-3 审核报告

- 审核对象：`保洁/ep003_beats/scene31.json`(13段)、`scene32.json`(10段)、`scene33.json`(41段) 与其渲染成品 `保洁/ep003_segs/seg01–seg64_prompt.txt`（经 `manifest.json` 下标映射）。
- 判据：`minimax-h3-prompt-audio`、`minimax-h3-chained-segment-drift` + AGENTS.md 十五/十六章。
- 覆盖：**64/64 段**全部通读正文与六段式（超出"抽查 14 段"要求）；自动前置段逐段比对。
- 链组划分（依据 `gen_worker.py` `do_group`）：按 manifest 下标每 3 段硬切，**场次一变当组头走 fixed**（`gen_worker.py:252-267`）。实际组头 = 下标 ≡1 (mod 3) 者 ∪ 场次变更段(seg14、seg24)。故：{1-3}{4-6}{7-9}{10-12}{13}{14-15}{16-18}{19-21}{22-23}{24}{25-27}{28-30}{31-33}{34-36}{37-39}{40-42}{43-45}{46-48}{49-51}{52-54}{55-57}{58-60}{61-63}{64}。

## 总体结论（有条件通过）

自动前置的 STYLE/SOFT_LIGHT/NO_TEXT/SPEAKERS/空间锚点/曝光重锚**六类俱全**，六段式无缺失，声景无禁用词，纸条未把汉字写进画面，参考图在场/降级达标，台词预算与表演可见性达标。**阻塞项只有 2 条**（1 条偏黑措辞、1 条组内链式 Entry 对不上），改完即可通过。

---

## 高

- **seg14（3-2 首帧）** — 偏黑措辞，且与自身参考图**互相打架**：`<Picture 3>` 明写门房"bright mid-morning … ceiling light switched on … reads bright"，但 Entry 却写"**dim, with only a thin line of daylight leaking in**"，直接违反"保持明亮通透、不许偏黑"，H3 会照 Entry 把整间压暗。
  应改成：「Entry state, re-anchored to the reference images: 苏小满 (S1) has just come through the gateway, 小罗 (S7) half a step behind her; they now face the second door — the narrow gatehouse room, **bright and airy in the mid-morning, its ceiling light on and daylight pouring in through the door crack and the open inner door**; a half-table stands in the middle with a white-brass teapot, a coarse porcelain tea tray and a worn visitor's ledger.」

- **seg51（组 {49,50,51} 第 3 段 → 15.9 链式断点）** — Entry 引入了一个上一段最后一拍**根本没出现**的新姿势：seg50 末拍是"苏小满 close-up 说话、只看秦律师"，期间没有任何镜头交代陆崇的手从膝上挪到小几上；seg51 Entry 却写"**one hand on the small side table beside him**"。链式首帧取自 seg50 尾帧 → 首帧就跳变。
  应改成（补在上一段末尾，使 Entry 有可见前因）—— 在 `seg50` 的 `[Shot 1]` 末尾追加：「…only at 秦律师 (S19) — she wants the rule, not a favour: [Chinese] 写着送医人的名字。 **— and at the east window, behind her eyeline, 陆崇's (S15) hand comes to rest and settles on the small side table beside his chair.**」

---

## 中

- **seg23（3-2 收尾）** — "**retreats into the shadow of the room … gone into the dark of the room**"：整段以"消失在黑里"收束，属偏黑措辞（同场 seg14 已列高，此处为同源问题的另一处）。
  应改成：「[Shot 1] Medium inside the gatehouse: 忠叔 (S18) pulls the door further open and steps back into the soft shadow at the far side of the room, head lowering; but once he is back there, his eyes still follow half a beat after the direction she walks, and **he stays softly readable against the room's shaded far corner**.」

- **跨场次组边界 seg13→seg14（3-1→3-2）、seg23→seg24（3-2→3-3）** — 判"中"。已确认两处**都会走 fixed 工作流重建**：`gen_worker.py:264-267` 对 `scene_break` 强制切 `WF_FIXED`（日志"换场次…改用 fixed 工作流，从参考图重建"），不会去套上一场尾帧。位置本身也咬合（seg13 尾"两人一前一后没入门黑" ↔ seg14 首"苏小满在前、小罗半步在后面对二门"；seg23 尾门房收场 ↔ seg24 会客厅大全景）。**无需改动**；若要更稳可把 seg24 Entry 首句写成：「Entry state, re-anchored to the reference images: **the same reception hall as the previous episode, re-lit for a bright mid-morning hearing** — the long rosewood table runs away from camera on the depth axis, both long edges filled with seated family, 苏小满 (S1) standing alone at the near head.」

---

## 低

- **seg37 Entry 措辞与上一拍时间点错位** — Entry 写"苏小满 has just looked once at 陆蔓"，而 seg36 末拍是"gaze … returns to 秦律师"。seg37 是组头（37≡1 mod 3，走 fixed），**不会真的跳变**，仅措辞不准。
  应改成：「Entry state, re-anchored to the reference images: 苏小满 (S1) stands at the near head, **her gaze back on the far head after one glance at 陆蔓 (S8)**; 秦律师 (S19) sits at the far head.」

- **seg10 summary 含声景否定词近亲** — summary 会随提示词喂给 H3，"wordless **silence**"与 15.7 的否定式同源（本段无台词，风险有限，仍建议正向化）。
  应改成：「[reference generation] Three-quarter profile, **still and wordless**: jaw set, eyes still on the dark doorway, while the steward watches from behind and does not urge her again.」

- **3-1 门洞黑组（seg01/02/03/06/10/12/13）** — "its interior **a solid black** that hides the courtyard""the **black** of the doorway catches and closes around half of her back""sink into the **black** of the doorway""eyes flick **into the dark** gateway"：门洞是全片核心锚点（剧本 0.1"门洞是黑的"），但纯黑措辞密度偏高，与"不许偏黑"轻微相抵。建议保留"深"去掉"死黑"。
  应改成（以 seg01 Entry 为例）：「…the door opening faces the lens, **its interior a deep recessed shadow that still shows a faint sliver of the bright courtyard beyond**.」

- **seg45 陆崇面部半边入影** — "half his face sits in shade and only his eyes stay lit"：戏剧性欠曝用光，与"不许偏黑"相抵（同段其余机位无问题）。
  应改成：「…the morning light presses in from behind him **so that his face reads soft and open, with only a light, gentle rim of shade along one cheek**: [Chinese] 两岁的事，你一个字不记得。」

---

## 已核对无问题项

1. **六段式完整性**：seg01–seg64 全部含 `subject_definitions / summary / retention_analysis / detailed_description / overall_soundscape / non_diegetic_music`，无缺失；retention 对每个 `<Subject n>/<Picture n>` 都给了标记（如 seg24 的 6 个标签、seg42 的 5 个）。
2. **自动前置段**：64 段全部带 ①`VERTICAL 9:16`（含"stage in DEPTH…never side by side"竖屏铁律）②`LIGHTING IS SOFT, BRIGHT AND FLATTERING`低阴影密度 ③`ABSOLUTELY NO SUBTITLES…` ④`Speaker labels are stable…(S1)…(S19)…` ⑤分场次 `Fixed spatial set-up…` ⑥`Exposure, white balance and colour … Never return a clip darker…`；与分镜正文不打架（唯一打架处见 seg14 高）。
3. **声景（15.7）**：64 段 `overall_soundscape` **无** silence/silent/mute/nothing at all/dead quiet/total hush/gone quiet/nothing but/absolute quiet/no other sound/almost nothing；检索命中的 "silent"（如 seg01/03/…）全部来自自动 SPEAKERS 段的 "stays completely silent with a closed mouth"，非声景正文。正向写法（"the room holding its breath"→本剧用 "the family's held breath"）到位。
4. **不烧字幕（15.6）**：正文无 subtitle/caption/lower-third/title card/on-screen text/text overlay/watermark 写法；检索命中的全部来自自动 NO_TEXT 段。台词一律 `[Chinese] …` **不加引号**。
5. **纸条（3-1 重点）**：seg06–seg09 与 3-3 的 seg35–seg36 **均未出现「我梦见过」汉字、未点名文字内容**；seg07 用外观描写 "**a single hand-written line sits on the white sheet, the strokes level and cool**"。全 64 段无"双引号/「」包裹汉字"的情况。
6. **参考图在场（15.8）**：3-2 只挂 `zhongshu/suxiaoman/xiaoluo/lu_gatehouse`；3-3 只挂在场角色 `qinlvshi/luman/luhang/luchong/suxiaoman/zhongshu/lu_hall/lu_hall_desk`；3-1 只挂 `suxiaoman/xiaoluo/lu_gate`。**无一个段挂不在场角色**（含"3-3 忠叔在场、不误挂缺席者"这一条）。
7. **参考图降级（15.8）**：seg24–seg64 中**凡挂 `lu_hall` 的段全部**带降级句「…use it as the **LOCATION**, furniture and layout reference **ONLY**; this beat is set in bright MORNING daylight, so **do NOT copy its night colour or its warm lamp light**…」；挂 `lu_hall_desk` 的段（seg25/29/31/45/47/63/64 等）另带"只做桌面材质与版式参考、不复制暖灯"的降级。**无缺失**。
8. **空间锚点（16.1）**：三套锚点均正确 —— 3-1「gate tower … at the far end of the depth axis, **NEVER shifted to the side and never shot at 45 degrees**」；3-2「忠叔 always INSIDE … FAR half … 苏小满 … NEAR half … facing each other **THROUGH the doorway — never side by side**」；3-3「秦律师 far/苏小满 near、**the ONLY person in the room left standing**、陆蔓陆航 RIGHT staggered in depth、陆崇 by the window、Never place any two people side by side」。正文**无**"左右并排/一字排开/横排"式调度（`side by side`/`lined up` 出现处均为**否定式锁场句**）。
9. **链式顺接（15.9）**：逐组核对 seg01→63，组内第 2/3 段 Entry 与上一段末拍**逐字咬合**（例：seg07←seg06"hand takes paper"↔"folded paper pressed into her hand"；seg19←seg18"hand still frozen on the bronze ring"；seg32←seg31"book sits pushed toward the near end"；seg58←seg57、seg59←seg58"steadied the pot"；seg63←seg62"hand flat on the table"）。**唯一对不上的点 = seg51（已列高）**。
10. **道具连续性**：① 纸条（3-1 小罗塞入→展开→对折揣兜 → 3-3 seg35 陆蔓"照纸条说" → seg36 拒绝时明写 "pushing aside **the folded paper in her pocket**"）② 红绳（3-2 seg16-17 忠叔目光由上而下钉住 → 3-3 seg54 秦律师追问 → seg55"唯一一次自己碰绳"）③ "全场不落座"（3-3 锚点 + seg24 明写 "the only person on her feet / left standing"）；三线**均连续未断**。
11. **台词预算（16.4）**：64 段**每段最多 1 句** `[Chinese]`，最长 17 字（seg29/49/63），全部 ≤24 字；manifest `over_budget` 全 false。
12. **表演可见性（16.2）**：无"只有台词"的段；台词段都配了可见动作/目光/身体位移（seg22 晃身+手松门环+缩袖、seg48 抬下巴使镜框移位、seg53 收身靠椅+手落回膝、seg64 合本+抖纸理齐+抬眼看全场）。
13. **画面偏黑检索**：`pitch dark / in darkness / dimly lit / murky / unlit` 正文**零命中**（`murky` 仅出现在自动 STYLE 段的否定句 "Absolutely NOT dark, not contrasty, not murky"）；命中 `dark`/`dim` 的实质处即上文 seg14、seg23、seg45、3-1 门洞黑组。

---

*审核员：独立子代理（只审不改）。本报告未改动任何分镜/提示词。*
