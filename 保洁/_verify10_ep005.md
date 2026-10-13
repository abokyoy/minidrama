# ep005 分镜 H3 审核报告

审核对象：`ep005_beats/scene51.json`（55 段）、`scene52.json`（23 段）、`scene53a.json`（22 段）、`scene53b.json`（17 段），共 **117 段**（t01–t117）。

## 总评

**需整改。**

| 项 | 数值 |
|---|---|
| 总段数 | 117 |
| 发现问题段落数 | 55（47%） |
| 严重问题条数 | 12 类 / 覆盖 44 段 |
| 一般问题条数 | 4 类 / 覆盖 33 段 |
| 通过段数 | 62（53%） |

**两条特殊铁律的执行情况：**

- **5-2 门口（t56–t78）`ref_notes.car_interior` 降级字段：✅ 完全达标。** 16 个含 `car_interior` 的段（t58、t60、t61、t62、t63、t64、t65、t66、t67、t68、t69、t70、t71、t72、t73、t74）**全部**带有 `ref_notes.car_interior`，措辞统一且正确：`USE IT AS THE EXACT POSITION AND PROP REFERENCE ONLY` + 明确否定 `the amber night lighting visible in the image must NOT be reproduced`。**无需整改。**
- **5-3a 出租屋文字铁律（t79–t100）：⚠️ 主体达标，3 处措辞需改。** 全 22 段都写了 `no writing of any kind` / `none of the words go into the frame` 这类显式禁令，屏光跳动的写法正确。但 t89、t93 出现了「协议上的某一行」「那一行文字」这类**把文字实体当叙事对象提及**的措辞（见严重问题 #8），t86 的 `cell`（字符格）也需换词。

**核心结论：空间锚点自洽（第 8 条）是本集最大的系统性缺陷。** 5-1 有 12 段（t44–t55）的 Entry state 与 Shot 正文**自相矛盾**——Entry state 写 `苏小满…the only person on her feet`，但 t44 起陆崇已起身站立，t45/t46/t51/t52/t54 的正文明确写 `陆崇 (S15) standing at the far head`。这会让 H3 在每段重新生成时把陆崇重新坐回椅子，「陆崇站起来」这个本场的关键动作点被抹掉。5-2 的 t64/t65/t70 与 5-3b 的 t104/t107 存在同一类**景深自相矛盾**（同句里既说 A 在 foreground，又说 B 比 A 更近）。5-3a 的手机位置链在 t81、t88–t100 有 13 段断裂。

其余方面质量明显偏高：40 句台词**全部**为 `[Chinese] 原文` 格式、**无一例带引号**、**无一例漏 `[Chinese]` 标签**；40 句全部有 `(S#)` 前缀标注且编号跨镜头稳定（S15/S8/S19/S1/S18）；时间戳 117 段**全部**首镜无 `At`、后续严格递增；refs 全部 ≤6 张；`music` 仅 t117 有配乐（本集收尾）、其余 116 段全 N/A，符合规范。

---

## 严重问题（会导致生成失败或画面错误，必须改）

### #1 t98｜shots｜邻居台词**完全没有 (S21) 标注**

**问题**：本集铁律规定邻居是 (S21)、只在楼下画外、始终不出脸。但 t98 是邻居唯一一次开口，格式是：

```
[Shot 2] At 05.000, The neighbour's voice calls up from below: [Chinese] 小满！楼下有个老头，等你俩钟头了！
```

全 4 个 JSON 里 `(S21)` 出现 **0 次**——编号从未被建立过。H3 拿到没有编号的台词会当成旁白/字幕处理，把字烧进画面，或分配给已在场的 S1。这是**会导致画面出现文字**的严重故障。

**建议改法**（可直接替换 `[Shot 2]` 整行）：

```
[Shot 2] At 05.000, A neighbour's voice (S21) calls up the stairwell from below, off frame and never seen: [Chinese] 小满！楼下有个老头，等你俩钟头了！
```

同时在 t98 的 `summary` 末尾补一句编号声明，避免 H3 在 summary 阶段丢失该编号：
把 `she is alone in the frame and the neighbour is never seen.`
改为 `she is alone in the frame and the neighbour is never seen; the neighbour is only ever heard from downstairs and is numbered (S21).`

---

### #2 t44–t55（12 段）｜shots｜Entry state 与正文**自相矛盾**：陆崇已站起，但锚点仍写「苏小满是全场唯一站着的人」

**问题**：t01–t55 的 Entry state 模板里每段都含 `苏小满 (S1) standing at the NEAR head half a step left, the only person on her feet`。但：

- t44 正文：`陆崇 (S15) rises from the presiding chair`（站起）
- t45 正文：`陆崇 (S15) stands at the far head`
- t46 正文：`苏小满…finally back to 陆崇 (S15) standing at the far head`
- t47 正文：`finally settles on 陆崇 (S15) standing at the far head`
- t51 正文：`past the far head where 陆崇 (S15) is standing`
- t52 正文：`Reverse on 陆崇 (S15)…he stands without moving`
- t54 正文：`at the far head 陆崇 (S15) stands`

即 t44–t55 这 12 段，Entry state 说「她是他唯一站着的」，Shot 正文说「他也站着」。H3 的 detailed_description 前半段（Entry state）和后半段（Shot）打架，站立人数在每段都不可解析。**「陆崇站起来」是本场的动作高点，被这个矛盾抹平。**

**建议改法**：把 t44–t55 这 12 段的 Entry state 里那句
`standing at the NEAR head half a step left, the only person on her feet;`
统一替换为：

```
standing at the NEAR head half a step left, the only person standing in the near half; 陆崇 (S15) is on his feet at the far head from the moment he rises and stays on his feet to the end of the scene;
```

（t01–t43 保持 `the only person on her feet` 不变，那 43 段陆崇确实坐着。）

---

### #3 t64、t65、t70｜shots｜5-2 景深自相矛盾：同一句里既说陆蔓在前景，又说苏小满比她更近

**问题**：5-2 铁律是「陆蔓恒在车内（中景偏右），苏小满恒在车窗外（近半幅中轴偏左），隔一扇车窗前后对视，严禁左右并排」。但三段的 over-the-shoulder 写法把两人前后关系写反了：

- t64：`陆蔓 (S8) is in the foreground inside the car and 苏小满 (S1) is outside the window a step nearer the camera`
- t65：`陆蔓 (S8) stays in the foreground inside the car`
- t70：`陆蔓 (S8) remains in the foreground inside the car`

「in the foreground」和「a step nearer the camera」不能同时成立——若陆蔓在前，苏小满不可能更靠近镜头。H3 会随机挑一个，导致两人一会儿前后一会儿左右，**正是用户投诉过的镜头切换 bug**。

**建议改法**：
- t64 把 `陆蔓 (S8) is in the foreground inside the car and 苏小满 (S1) is outside the window a step nearer the camera`
  改为 `陆蔓 (S8) is inside the car in the middle-ground right of centre and 苏小满 (S1) is outside the window in the near half a little left of centre, so 苏小满 (S1) is the nearer of the two and 陆蔓 (S8) is the further, the two of them staggered along the car's depth and never side by side`
- t65 把 `陆蔓 (S8) stays in the foreground inside the car`
  改为 `陆蔓 (S8) stays inside the car in the middle-ground right of centre, further from the camera than 苏小满 (S1)`
- t70 把 `陆蔓 (S8) remains in the foreground inside the car`
  改为 `陆蔓 (S8) remains inside the car in the middle-ground right of centre, further from the camera than 苏小满 (S1)`

---

### #4 t104、t107｜shots｜5-3b 景深自相矛盾，且 t107 把忠叔的眼睛放前景、苏小满的领子放后面

**问题**：5-3b 铁律是「忠叔恒在台阶上路灯下（中景偏右、更远一档），苏小满恒在台阶下（近半幅中轴偏左、更近一档），台阶上下前后对望，严禁左右并排」。

- t104：`忠叔 (S18) stands in the foreground under the lamp and she is a step nearer the camera`——「foreground」与「a step nearer」直接矛盾。
- t107：`the depth of the shot has his old eyes in front at one side of frame and her collar behind`——把忠叔的眼睛放**前面**、苏小满的领子放**后面**，等于说苏小满在忠叔之后，比他更远，与「苏小满更近一档」完全反了。

**建议改法**：
- t104 把 `忠叔 (S18) stands in the foreground under the lamp and she is a step nearer the camera, so the two of them overlap in depth up the steps and are never side by side`
  改为 `忠叔 (S18) stands up on the steps under the lamp in the middle-ground right of centre, further from the camera, and 苏小满 (S1) is at the foot of the steps in the near half a little left of centre, nearer the camera, so the two of them overlap in depth up and down the steps and are never side by side`
- t107 把 `the depth of the shot has his old eyes in front at one side of frame and her collar behind, and one downward line of sight pins the two of them together`
  改为 `the depth of the shot has 忠叔 (S18)'s old eyes further away at one side of frame and 苏小满 (S1)'s collar nearer the camera below them, one downward line of sight running from the far eyes to the near collar, and the two of them are never side by side`

---

### #5 t39｜shots｜Entry state 出现 `the whole room silent`——「silent」属声景压人义词

**问题**：`silent` 在 `soundscape` 里会压掉人声，但这里出现在 **Entry state**（会进 detailed_description）。虽不在 soundscape 字段，仍是同一风险词，且用户明确要求「措辞必须彻底避开这些短语本身」。

**建议改法**：t39 Entry state 里 `the whole room silent, 苏小满 (S1) standing at the near head`
改为 `the whole room holding its breath, 苏小满 (S1) standing at the near head`

---

### #6 t52｜shots｜`says nothing at all` 撞「声景压人声」词表

**问题**：`nothing at all` 是用户列出的 8 个禁用词之一，原文：`[Shot 2] At 05.000, He stays standing and says nothing at all.` 另有 Entry state 的 `陆崇 (S15) standing at the far head, silent` 中的 `silent`。两处都要改。

**建议改法**：
- `[Shot 2] At 05.000, He stays standing and gives the line no answer at all; his mouth stays closed and the pause is the answer the room gets.`
- Entry state 的 `陆崇 (S15) standing at the far head, silent` 改为 `陆崇 (S15) standing at the far head, not answering`

---

### #7 t79、t80｜summary + shots｜`dim` / `dims` 撞曝光压暗词表（子串命中）

**问题**：`dim` 是用户列出的曝光禁用词，且规则明确「连否定句也算违规，措辞必须彻底避开这些短语本身」。实际命中 4 处：

- t79 summary：`a small bright patch on the dimmer tabletop`
- t80 summary：`her face brightens and dims with them`
- t80 shots：`her face brightens and dims with them`（Shot 1）
- t80 shots：`Her face keeps brightening and dimming with the bars`（Shot 2）

**建议改法**：
- t79 summary：`cold white light from the screen throws a small bright patch on the dimmer tabletop`
  → `cold white light from the screen throws a small bright patch on the tabletop, the rest of the wood staying a clear step below the screen in brightness`
- t80 summary / Shot 1：`her face brightens and dims with them`
  → `her face brightens and drops back with them`
- t80 Shot 2：`Her face keeps brightening and dimming with the bars`
  → `Her face keeps brightening and dropping back with the bars`

---

### #8 t89、t93｜summary + shots｜5-3a 文字铁律：把「协议上的那一行」「那一行文字」当叙事对象提及

**问题**：这是本集两条特殊铁律之一。t79–t100 的写法整体正确（显式写 `no writing of any kind`），但两处仍在**点名文字实体**：

- t89 summary：`her other hand comes over from beside the screen and presses down on one particular line of it — the line itself is never shown`
- t89 shots：`presses down on one particular line of it — the line itself is never shown`
- t93 summary：`that line of text is not one character left`
- t93 shots：`that line of text is not one character left; the frame gives the empty lit surface and the blinking cursor and no writing of any kind`

`line of it`、`that line of text` 会让 H3 意识到「纸上有行文字」并尝试渲染。即使后半句写了 never shown，模型也可能先画出模糊字形再被否定，净效果是画面出现文字。

**建议改法**：
- t89 summary：`and presses down on one particular spot of it — that spot is never shown, only the paper around it and the mark her finger makes`
- t89 shots：`and presses down on one particular spot of it — the spot itself is never shown, and the frame gives only the paper around it and the mark her finger makes, with the phone's cold light lying across the sheet`
- t93 summary：`that line of text is not one character left`
  → `the input field is completely empty, not one mark left in it`
- t93 shots：`the cursor blinks on and off again — that line of text is not one character left; the frame gives the empty lit surface and the blinking cursor and no writing of any kind`
  → `the cursor blinks on and off again on a completely empty input field; the frame gives the empty lit surface and the blinking cursor and no writing of any kind, with the table top and her thumbs at the bottom third`

---

### #9 t81、t88–t100（13 段）｜shots｜5-3a 手机位置链断裂，「上一段最后一拍 ≠ 下一段第一拍」

**问题**：这是用户明确投诉过的镜头切换 bug 类型。5-3a 逐段状态链：

| 段 | 状态 | 问题 |
|---|---|---|
| t79 | 手机在苏小满手里 | OK |
| t80 | 手机在她手里，光打脸上 | OK |
| **t81** | `the phone lying on the table with its light moving` | **断裂**：t80 结束在她手里，t81 突然平放在桌上，无放下动作 |
| t82–t87 | 又回到手里 | 又一次无 pickups 动作的跳变 |
| t88 | 停在半空 | — |
| **t89** | `her other hand comes over from beside the screen` | 暗示手机在桌上，但 t88 她还举着 |
| **t91** | `the phone on the table with 苏小满 (S1)'s thumb deleting` | 断裂：t90 她手仍在半空 |
| t94 | 扣下 | OK |
| t95–t97 | `the phone now face down on the table` | OK |
| **t98** | `the phone picked up off the table and pushed into her jacket pocket` | OK，但 t98 Entry state 仍写 `on the table top the photocopy of the agreement and her mobile phone, which starts in her hand` |
| t99 | `the table with the phone's place now empty` | OK |
| t100 | 跑出房间 | OK |

另外 Entry state 模板在 t94–t100 这 7 段都还写着 `her mobile phone, which starts in her hand`，但 t95 之后手机已经面朝下在桌上、t98 之后在口袋里——**模板与实际状态直接矛盾**。

**建议改法**：
- t81 shots：`Close from above on the phone's screen lying on the table`
  → `Close from above on the phone's screen, now flat on the table where her hands have just set it down, her thumbs resting beside it`
  并在 t81 的 Entry state 尾部加 `the phone now lying flat on the table with her thumbs resting beside it`
- t82 Entry state 尾部加 `the phone flat on the table, her hands back off it`
- t83 Entry state 尾部 `苏小满 (S1) seated on the bed's edge at the near side of the table, holding the phone in both hands`
  → `苏小满 (S1) seated on the bed's edge, having picked the phone back up off the table and now holding it in both hands`
- t89 shots：`her other hand of 苏小满 (S1) comes over from beside the screen`
  → 改为 `the phone lies flat on the table in front of her, and her other hand comes over from beside it and presses down on one particular spot of the photocopy`
- t91 Entry state 尾部改为 `the phone still lying flat on the table with her thumb working in its input area`
- t94–t100 这 7 段的 Entry state 模板句
  `on the table top the photocopy of the agreement and her mobile phone, which starts in her hand`
  统一替换为
  `on the table top the photocopy of the agreement lying flat, and the mobile phone whose position is given at the end of this entry state`
  再各自在段末写明实际位置：t94/t95/t96/t97 写 `the phone lying face down on the table`；t98 写 `the phone picked up off the table and pushed into her jacket pocket`；t99/t100 写 `the phone in her jacket pocket, the table top clear of it`

---

### #10 t05｜shots｜Entry state 写协议复印件「face down at first」，与 t05/t14 的手印正面描述冲突

**问题**：t05 Entry state 尾部写 `one kraft folder, several loose pages and one photocopy, face down at first`，但同一段 Shot 1 写 `lying on top of them is one photocopy of an agreement whose corner is furry and whose lower right corner carries a pale red thumbprint`——**手印可见 = 正面朝上**。t14 同样写手印在 lower right。t05 的 `face down at first` 会让 H3 在第一帧把复印件背面朝上，t14 的特写就接不上。

**建议改法**：t05 Entry state 尾部
`on the table top, one kraft folder, several loose pages and one photocopy, face down at first`
→
`on the table top, one kraft folder with its mouth open, several loose pages showing their edges, and one photocopy lying face up on top of them with a pale red thumbprint at its lower right corner`

---

### #11 t43｜shots｜材料被移动，与 t55「全程原封不动」铁律冲突

**问题**：5-1 铁律要求材料「从推到长案中央到本场散掉，全程原封不动、无人翻开」。但 t43 写 `the file at the centre of it shifts inside its own open folder`，summary 更写 `the file at the centre shifts in its own tray`——**出现了「tray」（托盘）这个本场不存在的道具**，而且材料被拍击震得移了位。t55 收尾却写 `still exactly where they were pushed`，与 t43 的位移矛盾。

**建议改法**：
- t43 summary：`the file at the centre shifts in its own tray`
  → `the file at the centre of the long table stays exactly where it was pushed and does not move`
- t43 Shot 1：`the cups on the table jump and the file at the centre of it shifts inside its own open folder without anybody opening it`
  → `the cups on the table jump and ring, and the file at the centre of it stays put, its open mouth and the thumbprint on its top sheet undisturbed, and nobody's hand goes near it`
- t43 Shot 3：`The cups stop rocking; the file lies where the jolt left it, still closed.`
  → `The cups stop rocking; the file lies exactly where it was pushed, still closed, and nobody has touched it.`

---

### #12 t61｜shots｜车窗降下缺施动者，与 t72 的「手指按下升降开关」因果倒置

**问题**：5-2 的第一个动作点是 t61 车窗降下。但 t60 结尾陆蔓是 `she does not move yet`、`lets her lids drop back half a fraction`——**手没动**。t61 玻璃就自己降下来了，画面里没有人操作。而 t72 才写 `her hand lifts off the window edge and presses the window control on the door`——升降开关在**升窗**时才第一次被触碰。两个动作点共用一个开关，但降窗时开关没被碰过，逻辑上说不通，H3 也无法判断谁在动。

**建议改法**：
- t61 Shot 1 开头插入操作动作，把
  `Close on the car window: the glass comes down slowly, its top edge retreating inch by inch`
  改为
  `Close on the car window: 陆蔓 (S8)'s fingers come down onto the window control on her door and stay pressed, and the glass starts down slowly, its top edge retreating inch by inch`
- t60 Shot 2 改为
  `[Shot 2] At 05.000, She holds the look for a beat, lets her lids drop back half a fraction, and her hand starts down towards the window control on her door.`
- t72 Shot 1 保持现状即可（升窗时再次按同一个开关，前后呼应）

---

## 一般问题（影响质量，建议改）

### #1 t86｜shots｜`cell`（字符格）措辞有渲染字符的风险

**问题**：t85 写 `the input area lights up one cell at a time`，t91 写 `the line of light in the input area retreats one cell at a time`。`cell` 指字符格，在 5-3a 文字铁律下属于危险词。

**建议改法**：
- t86 Shot 1：`each key makes the screen's cold white light jump and the input area lights up one cell at a time`
  → `each key makes the screen's cold white light jump and one small square of light in the input area comes on and then another`
- t91 Shot 1：`the line of light in the input area retreats one cell at a time and the screen flickers with every cell that goes`
  → `one small square of light in the input area goes out and then the next one, and the screen flickers with every square that goes`

---

### #2 t15、t25、t32、t39、t45、t54 等 20 段｜refs｜镜头正文里出现的人物未放进 refs

**问题**：refs 只放本段真的在场的人与场景，但多段的 Shot 正文提到了未登记的人物。实测清单：

- 5-1：`t06`(苏小满)、`t15`(陆蔓/陆航)、`t16`(陆崇)、`t18`(陆蔓)、`t24`(苏小满)、`t25`(陆崇/陆航)、`t30`(苏小满)、`t32`(苏小满/陆崇)、`t38`(陆崇)、`t39`(苏小满/陆崇)、`t45`(陆崇/陆蔓/陆航)、`t46`/`t47`/`t48`(陆崇)、`t49`(秦律师)、`t50`(苏小满)、`t54`(陆崇/陆航)
- 5-2：`t62`、`t63`(苏小满；t63 另有陆崇仅在台词里可不管)、`t69`(苏小满)、`t75`(苏小满/陆蔓)
- 5-3b：`t102`、`t103`、`t105`、`t106`、`t109`、`t110`、`t114`、`t115`、`t116`、`t117`

多数是「视线/反打对象」型提及（如 t18 陆崇不承认东侧的陆蔓），但 H3 的 ref2v 会按 refs 决定谁被渲染，正文点名却不在 refs 的人物容易被丢弃或错配。

**建议改法**（举例，逐段核对后补齐即可）：
- t45 refs 从 `["lu_hall"]` 改为 `["luchong", "luman", "luhang", "lu_hall"]`
- t54 refs 从 `["lu_hall"]` 改为 `["luchong", "luhang", "lu_hall"]`
- t32 refs 从 `["lu_hall"]` 改为 `["luchong", "suxiaoman", "lu_hall"]`
- t39 refs 从 `["lu_hall"]` 改为 `["luchong", "suxiaoman", "lu_hall"]`
- t25 refs 从 `["lu_hall"]` 改为 `["luchong", "luhang", "lu_hall"]`
- t15 refs 从 `["lu_hall"]` 改为 `["luman", "luhang", "lu_hall"]`
- t16 refs 从 `["luman", "lu_hall"]` 改为 `["luchong", "luman", "lu_hall"]`
- t24 refs 从 `["luchong", "lu_hall"]` 改为 `["luchong", "suxiaoman", "lu_hall"]`
- t30 refs 从 `["luman", "lu_hall"]` 改为 `["luman", "suxiaoman", "lu_hall"]`
- t06 refs 从 `["luchong", "lu_hall"]` 改为 `["luchong", "suxiaoman", "lu_hall"]`
- t49 refs 从 `["suxiaoman", "lu_hall"]` 改为 `["suxiaoman", "qinlvshi", "lu_hall"]`
- t50 refs 从 `["qinlvshi", "lu_hall"]` 改为 `["qinlvshi", "suxiaoman", "lu_hall"]`
- t46/t47/t48 refs 从 `["suxiaoman", "lu_hall"]` 改为 `["suxiaoman", "luchong", "lu_hall"]`
- t38 refs 从 `["suxiaoman","luman","luhang","lu_hall"]` 追加 `luchong`（5 张，仍 ≤6）
- t62/t63/t69 refs 追加 `suxiaoman`；t75 refs 从 `["lu_gate"]` 改为 `["luman","suxiaoman","lu_gate"]`
- 5-3b：`t102`/`t105`/`t106`/`t109`/`t114` refs 追加 `suxiaoman`；`t103`/`t110`/`t116`/`t117` refs 追加 `zhongshu`；`t115` refs 追加 `suxiaoman`

（补完后仍全部 ≤6 张，无超限风险。）

---

### #3 5-1 多数段（t01–t43）｜shots｜语速超预算 3.2 字/秒

**问题**：全 40 句台词的总字数都在 26 字以内（最大 23 字，t08/t13），**总预算合规**。但按「句起点到下一镜起点」的窗口算瞬时语速，有 20 句超过 3.2 字/秒，H3 会把字念成快读：

| 段 | 字数 | 窗口 | 语速 |
|---|---|---|---|
| t35 | 21 | 4.0s | **5.25** |
| t63 | 21 | 4.0s | **5.25** |
| t08 | 23 | 4.5s | **5.11** |
| t13 | 23 | 4.5s | **5.11** |
| t67 | 20 | 4.0s | **5.00** |
| t11 / t33 | 22 | 4.5s | **4.89** |
| t27 | 19 | 4.0s | **4.75** |
| t112 | 18 | 4.0s | **4.50** |
| t48 / t49 | 17 | 4.0s | **4.25** |
| t16 / t18 / t43 / t46 / t51 | 14–16 | 3.5–4.0s | **4.00** |
| t22 | 12 | 3.5s | 3.43 |
| t05 | 10 | 3.0s | 3.33 |
| t98 | 14 | 4.0s | 3.50 |

**建议改法**（把台词前移并拉长窗口，不改文字内容）。以 t35 为例，`[Shot 2] At 05.000` 改 `[Shot 2] At 03.500`，`[Shot 3] At 09.000` 改 `[Shot 3] At 09.500`，21 字 / 6.0s = 3.5 字/秒，仍偏高则再把 Shot 3 后移。同法处理：
- t63：`At 05.000` → `At 03.500`（21 字 / 5.5s ≈ 3.8，建议 Shot 3 后移到 10.000）
- t08 / t13：`At 05.000` → `At 03.000`（23 字 / 6.5s ≈ 3.5）
- t67：`At 05.000` → `At 03.500`
- t11 / t33：`At 05.000` → `At 03.500`
- t27：`At 04.500` → `At 03.500`
- t112：`At 05.000` → `At 03.500`
- t48 / t49：`At 05.000` / `At 04.500` → `At 03.500`
- t16 / t18 / t43 / t46 / t51：`At 04.500` / `At 05.000` → `At 03.000`
- t98：14 字 / 4.0s = 3.5，`At 05.000` → `At 04.000`（14 字 / 5.0s = 2.8）

---

### #4 全部 117 段｜shots｜detailed_description 词量普遍不足 350–500 词

**问题**：实测 `shots` 字段词数为 **195–312 词，均值 238 词**，**117 段全部低于 350 词下限**。当前写法把「Entry state 锚点模板 + 2 个镜头」压得太紧，镜头缺可供 H3 发挥的空间（缺机位运动、缺景深变化、缺前景遮挡关系、缺光比落点）。例如 t01 只有 278 词、t10 只有 212 词、t71 只有 195 词（本集最低）。

**建议改法**：每段在保持 Entry state 与前两镜内容不变的前提下，**在最后一句之后追加 1 个镜头**（`[Shot 3] At 08.000,`），补 130–180 词的可拍内容：具体机位（如 `the camera slides two inches along the table's depth`）、前景元素入画（如 `a chair back crosses the near edge of frame`）、光在材质上的落点（如 `the window light picks the rim of the porcelain`）、以及人物微动作的落幅（如 `her thumb settles against the cup handle and stays`）。注意追加镜头时：
- 首个镜头**不带** `At`，后续镜头必须带且严格递增；
- 追加镜头的台词窗口不要新增台词，保持总字数 ≤26；
- 追加内容不得触碰 12 条禁用词（声景压人声 8 词、曝光压暗 12 词）。

优先补写词数最低的段：`t71`(195)、`t52`(201)、`t70`(200)、`t68`(202)、`t56`(216)。

---

## 逐段检查表

说明：
- **说话人**：`S#` 为该段台词的标注编号；`—` 表示该段无台词。`S15`=陆崇、`S8`=陆蔓、`S1`=苏小满、`S19`=秦律师、`S18`=忠叔。
- **台词字数**：该段 `[Chinese]` 台词的汉字总数（预算 ≤26，全部合规）。
- **声景**：查 8 个压人声词（silence/silent/mute/nothing at all/dead quiet/total hush/gone quiet/nothing but）。
- **曝光**：查 12 个压暗词（含子串，否定句同样算）。
- **文字**：画面是否出现文字风险（协议字句、屏上字句）。
- **锚点**：空间锚点自洽（人物位置/朝向/持物/材料状态的跨段连续）。
- **结论**：`通过` / `一般` / `严重`。

| 段号 | 说话人 | 台词字数 | 声景 | 曝光 | 文字 | 锚点 | 结论 |
|---|---|---|---|---|---|---|---|
| t01 | — | 0 | OK | OK | OK | OK | 通过 |
| t02 | — | 0 | OK | OK | OK | OK | 通过 |
| t03 | — | 0 | OK | OK | OK | OK | 通过 |
| t04 | — | 0 | OK | OK | OK | OK | 通过 |
| t05 | S15 | 10 | OK | OK | OK | X 材料（face down 冲突） | 严重 |
| t06 | — | 0 | OK | OK | OK | X refs | 一般 |
| t07 | — | 0 | OK | OK | OK | OK | 通过 |
| t08 | S15 | 23 | OK | OK | OK | OK（语速 5.11） | 通过 |
| t09 | — | 0 | OK | OK | OK | OK | 通过 |
| t10 | — | 0 | OK | OK | OK | OK | 通过 |
| t11 | S15 | 22 | OK | OK | OK | OK（语速 4.89） | 通过 |
| t12 | — | 0 | OK | OK | OK | OK | 通过 |
| t13 | S15 | 23 | OK | OK | OK | OK（语速 5.11） | 通过 |
| t14 | — | 0 | OK | OK | OK | OK | 通过 |
| t15 | — | 0 | OK | OK | OK | X refs | 一般 |
| t16 | S8 | 14 | OK | OK | OK | X refs | 一般 |
| t17 | — | 0 | OK | OK | OK | OK | 通过 |
| t18 | S15 | 16 | OK | OK | OK | X refs | 一般 |
| t19 | — | 0 | OK | OK | OK | OK | 通过 |
| t20 | S15 | 10 | OK | OK | OK | OK | 通过 |
| t21 | — | 0 | OK | OK | OK | OK | 通过 |
| t22 | S19 | 12 | OK | OK | OK | OK | 通过 |
| t23 | — | 0 | OK | OK | OK | OK | 通过 |
| t24 | — | 0 | OK | OK | OK | X refs | 一般 |
| t25 | — | 0 | OK | OK | OK | X refs | 一般 |
| t26 | — | 0 | OK | OK | OK | OK | 通过 |
| t27 | S15 | 19 | OK | OK | OK | OK（语速 4.75） | 通过 |
| t28 | — | 0 | OK | OK | OK | OK | 通过 |
| t29 | — | 0 | OK | OK | OK | OK | 通过 |
| t30 | — | 0 | OK | OK | OK | X refs | 一般 |
| t31 | S1 | 4 | OK | OK | OK | OK | 通过 |
| t32 | — | 0 | OK | OK | OK | X refs | 一般 |
| t33 | S1 | 22 | OK | OK | OK | OK（语速 4.89） | 通过 |
| t34 | — | 0 | OK | OK | OK | OK | 通过 |
| t35 | S1 | 21 | OK | OK | OK | OK（语速 5.25） | 通过 |
| t36 | — | 0 | OK | OK | OK | OK | 通过 |
| t37 | S1 | 6 | OK | OK | OK | OK | 通过 |
| t38 | S1 | 11 | OK | OK | OK | X refs | 一般 |
| t39 | — | 0 | **X silent** | OK | OK | X refs | 严重 |
| t40 | — | 0 | OK | OK | OK | OK | 通过 |
| t41 | — | 0 | OK | OK | OK | OK | 通过 |
| t42 | — | 0 | OK | OK | OK | OK | 通过 |
| t43 | S15 | 16 | OK | OK | OK | X 材料（文件位移＋tray） | 严重 |
| t44 | — | 0 | OK | OK | OK | X 锚点（唯一站着者矛盾） | 严重 |
| t45 | — | 0 | OK | OK | OK | X 锚点＋refs | 严重 |
| t46 | S1 | 16 | OK | OK | OK | X 锚点＋refs | 严重 |
| t47 | — | 0 | OK | OK | OK | X 锚点＋refs | 严重 |
| t48 | S1 | 17 | OK | OK | OK | X 锚点＋refs | 严重 |
| t49 | S1 | 17 | OK | OK | OK | X 锚点＋refs | 严重 |
| t50 | — | 0 | OK | OK | OK | X 锚点＋refs | 严重 |
| t51 | S1 | 16 | OK | OK | OK | X 锚点 | 严重 |
| t52 | — | 0 | **X silent＋nothing at all** | OK | OK | X 锚点 | 严重 |
| t53 | — | 0 | OK | OK | OK | X 锚点 | 严重 |
| t54 | — | 0 | OK | OK | OK | X 锚点＋refs | 严重 |
| t55 | — | 0 | OK | OK | OK | X 锚点 | 严重 |
| t56 | — | 0 | OK | OK | OK | OK | 通过 |
| t57 | — | 0 | OK | OK | OK | OK | 通过 |
| t58 | — | 0 | OK | OK | OK | OK（car_interior 降级 OK） | 通过 |
| t59 | S1 | 3 | OK | OK | OK | OK | 通过 |
| t60 | — | 0 | OK | OK | OK | OK（降级 OK） | 通过 |
| t61 | — | 0 | OK | OK | OK | X 降窗无施动者 | 严重 |
| t62 | S8 | 6 | OK | OK | OK | X refs（降级 OK） | 一般 |
| t63 | S8 | 21 | OK | OK | OK | X refs（降级 OK） | 一般 |
| t64 | — | 0 | OK | OK | OK | X 景深（前景矛盾） | 严重 |
| t65 | S1 | 9 | OK | OK | OK | X 景深（前景矛盾） | 严重 |
| t66 | — | 0 | OK | OK | OK | OK（降级 OK） | 通过 |
| t67 | S8 | 20 | OK | OK | OK | OK（降级 OK） | 通过 |
| t68 | — | 0 | OK | OK | OK | OK（降级 OK） | 通过 |
| t69 | S8 | 7 | OK | OK | OK | X refs（降级 OK） | 一般 |
| t70 | S1 | 5 | OK | OK | OK | X 景深（前景矛盾） | 严重 |
| t71 | — | 0 | OK | OK | OK | OK（降级 OK） | 通过 |
| t72 | S8 | 9 | OK | OK | OK | OK（降级 OK） | 通过 |
| t73 | — | 0 | OK | OK | OK | OK（降级 OK，t73 升窗正确） | 通过 |
| t74 | S8 | 7 | OK | OK | OK | OK（降级 OK） | 通过 |
| t75 | — | 0 | OK | OK | OK | X refs | 一般 |
| t76 | — | 0 | OK | OK | OK | OK | 通过 |
| t77 | — | 0 | OK | OK | OK | OK | 通过 |
| t78 | — | 0 | OK | OK | OK | OK | 通过 |
| t79 | — | 0 | OK | **X dim** | OK | OK | 严重 |
| t80 | — | 0 | OK | **X dim（3 处）** | OK | OK | 严重 |
| t81 | — | 0 | OK | OK | OK | X 手机位（手→桌无动作） | 严重 |
| t82 | — | 0 | OK | OK | OK | X 手机位 | 严重 |
| t83 | — | 0 | OK | OK | OK | X 手机位（桌→手无动作） | 严重 |
| t84 | — | 0 | OK | OK | OK | OK | 通过 |
| t85 | — | 0 | OK | OK | OK | OK | 通过 |
| t86 | — | 0 | OK | OK | X cell | OK | 一般 |
| t87 | — | 0 | OK | OK | OK | OK | 通过 |
| t88 | — | 0 | OK | OK | OK | X 手机位 | 严重 |
| t89 | — | 0 | OK | OK | X 协议行 | X 手机位 | 严重 |
| t90 | — | 0 | OK | OK | OK | X 手机位 | 严重 |
| t91 | — | 0 | OK | OK | X cell | X 手机位 | 严重 |
| t92 | — | 0 | OK | OK | OK | X 手机位 | 严重 |
| t93 | — | 0 | OK | OK | X 那行文字 | X 手机位 | 严重 |
| t94 | — | 0 | OK | OK | OK | X 手机位（Entry 模板） | 严重 |
| t95 | — | 0 | OK | OK | OK | X 手机位（Entry 模板） | 严重 |
| t96 | — | 0 | OK | OK | OK | X 手机位（Entry 模板） | 严重 |
| t97 | — | 0 | OK | OK | OK | X 手机位（Entry 模板） | 严重 |
| t98 | **缺 S21** | 14 | OK | OK | OK | X 手机位＋编号 | 严重 |
| t99 | — | 0 | OK | OK | OK | X 手机位（Entry 模板） | 严重 |
| t100 | — | 0 | OK | OK | OK | X 手机位（Entry 模板） | 严重 |
| t101 | — | 0 | OK | OK | OK | OK（忠叔上台阶/苏小满下台阶正确） | 通过 |
| t102 | S18 | 2 | OK | OK | OK | X refs | 一般 |
| t103 | — | 0 | OK | OK | OK | X refs | 一般 |
| t104 | S1 | 11 | OK | OK | OK | X 景深（前景矛盾） | 严重 |
| t105 | — | 0 | OK | OK | OK | X refs | 一般 |
| t106 | S18 | 7 | OK | OK | OK | X refs | 一般 |
| t107 | — | 0 | OK | OK | OK | X 景深（前后颠倒） | 严重 |
| t108 | — | 0 | OK | OK | OK | OK | 通过 |
| t109 | S18 | 6 | OK | OK | OK | X refs | 一般 |
| t110 | — | 0 | OK | OK | OK | X refs | 一般 |
| t111 | — | 0 | OK | OK | OK | OK | 通过 |
| t112 | S18 | 18 | OK | OK | OK | OK | 通过 |
| t113 | — | 0 | OK | OK | OK | OK | 通过 |
| t114 | S18 | 10 | OK | OK | OK | X refs | 一般 |
| t115 | — | 0 | OK | OK | OK | X refs | 一般 |
| t116 | — | 0 | OK | OK | OK | X refs | 一般 |
| t117 | — | 0 | OK | OK | OK | X refs | 一般 |

---

## 附：合规项确认（无需整改）

| 检查项 | 结果 |
|---|---|
| **5-2 `ref_notes.car_interior` 降级字段** | ✅ 16/16 段（t58、t60–t74）全部存在，措辞统一且含 `must NOT be reproduced` 的明确否定 |
| **台词格式 `[Chinese] 原文`** | ✅ 40/40 句全部合规 |
| **台词带引号** | ✅ 0 例（无引号污染） |
| **漏 `[Chinese]` 标签** | ✅ 0 例 |
| **(S#) 标注完整性** | ⚠️ 39/40 句有标注；仅 t98 邻居缺 (S21)（见严重 #1） |
| **说话人编号跨镜头稳定性** | ✅ S15 陆崇 / S8 陆蔓 / S14 陆航 / S1 苏小满 / S19 秦律师 / S18 忠叔 全程一致，无编号漂移 |
| **邻居不出脸** | ✅ t98 summary 与 shots 均写 `the neighbour is never seen`，仅画外 |
| **台词总字数 ≤26** | ✅ 40 句全部合规（最大 23 字：t08、t13） |
| **时间戳格式** | ✅ 117 段首镜均无 `At`；后续镜头全部为 `At MM:SS.mmm,` 且严格递增 |
| **refs ≤6 张** | ✅ 最大 4 张（t38、t64、t65），补齐后仍 ≤6 |
| **retention 与 refs 对应** | ✅ 每段 retention 键与 refs 完全一致，取值仅 `weak_reference` / `fully_preserved` |
| **music 字段** | ✅ 116 段 N/A，仅 t117（本集收尾）有配乐 |
| **5-1 秦律师与苏小满前后交叠** | ✅ t01/t04/t22 均写 `she overlaps him in depth`、`never lined up beside each other`，无左右并排 |
| **5-1 陆崇主位在远端** | ✅ 全 55 段一致 `FAR head`，未越轴 |
| **5-1 陆蔓东侧中段 / 陆航东墙窗台更远更高** | ✅ t03/t15/t25/t40/t42 均保持深度递进 |
| **5-2 车窗降下在 t61 / 升起在 t73** | ✅ 位置正确（但 t61 缺施动者，见严重 #12） |
| **5-3a 屏光跳动写法** | ✅ t79–t93 全部显式写 `no writing of any kind` / `none of the words go into frame` |
| **5-1 协议复印件只给形状与手印** | ✅ t05/t14/t55 均写手印位置与 `printing ... too small to read`，未点明字句内容 |
