# ep004 分镜 H3 审核报告

- 审核对象：`保洁/ep004_beats/scene41a.json`(9段)、`scene41b.json`(11段)、`scene42.json`(36段)、`scene43.json`(27段)、`scene44.json`(21段)，共 **104 段**。
- 判据：`minimax-h3-prompt-audio`、`minimax-h3-chained-segment-drift` 规范 + 用户本轮指定的 12 条。
- 审核方式：全量通读 5 个 JSON 全部 104 段正文，并用脚本复核台词字数、时间戳递增、参考图上限、曝光/声景禁用词、六段式拼装词量。
- 本报告**未改动任何 JSON**。

## 总评

**需整改。** 104 段中 **11 段严重**、**59 段一般**、**34 段通过**。

12 条里 **4 条完全干净**，可以确认：

| 条目 | 结论 |
|---|---|
| 2 台词格式 | **零违规**。45 段台词全部为 `[Chinese] 原文`，**全 104 段无一处引号**（含中文引号/「」），无漏标 `[Chinese]`。 |
| 4 声景压人声 | **零违规**。按 silence/silent/mute/nothing at all/dead quiet/total hush/gone quiet/nothing but 逐段检索，104 段 **0 命中**。 |
| 5 曝光压暗 | **零违规**。按 12 个禁用词逐段检索 shots/summary/soundscape/music 四字段，**0 命中**。 |
| 11 参考图数量 | **零违规**。最多 4 张（t33），无一超 6；`retention` 键与 `refs` **104 段全部一致**，无悬空槽位。 |

问题集中在**第 8/9 条（空间锚点与首尾接续）**——这正是用户明确投诉过的镜头切换 bug。共 **9 处道具/人物瞬移**，全部集中在道具线上：手电（t81、t83）、文件（t101、t103、t104）、工牌（t25）、人物（t12、t16、t33、t37、t38）。第 10 条时间戳格式与第 3 条语速预算各有一类系统性问题。

---

## 严重问题（会导致生成失败或画面错误，必须改）

### S1 · ep04_t12 · shots · 医生被同时放在远端和近景前景，自相矛盾且违反 4-1b 锚点

**问题**：本段 Entry 写「医生 (S11) at the far end in profile」，但 `[Shot 1]` 写成「Medium **at the near end** with 医生 (S11) **in the foreground** and 苏小满 (S1) behind him」。同一段里医生既在远端又在近景前景；且 `summary` 补了一句「stacked along the depth, **him nearer the lens**」——这与自动前置的 `ANCHOR_41_CORR`（"医生 (S11) is ALWAYS at the FAR end of the corridor, at its bright end... 苏小满 (S1) is ALWAYS at the NEAR end"）正面冲突。H3 会把两人叠在一处或镜像。

**建议改法**（替换 Entry 与 Shot 1）：

> Entry state, re-anchored to the reference images: 苏小满 (S1) stopped in the NEAR half of the corridor, a little left of centre, facing down the corridor; 医生 (S11) at the FAR end in profile, one hand in his white coat pocket, facing back towards her; the whole length of the floor between them stays open and readable.
>
> [Shot 1] Medium from the NEAR end of the corridor with 苏小满 (S1) in the near half of frame and the man in the far half: 医生 (S11) keeps the profile and the pocketed hand at the far end, and she stands facing him with her hands at her sides, both of them lit evenly by the fluorescents overhead.

---

### S2 · ep04_t16 · shots · 医生又被写进近景前景，违反 4-1b 锚点

**问题**：Entry 写「医生 (S11) **in the foreground** with his back partly to the lens」，`[Shot 1]` 写「Over-shoulder with 医生 (S11) in the foreground and 苏小满 (S1) behind him」。这让医生跑到近景、女孩跑到他身后，与锚点的「医生永远在远端、女孩永远在近端」完全对调。

**建议改法**（替换 Entry 与 Shot 1）：

> Entry state, re-anchored to the reference images: 苏小满 (S1) in the NEAR half of the corridor facing down its length, 医生 (S11) still at the FAR end facing her; she has just answered him and he has not moved.
>
> [Shot 1] Reverse on 苏小满 (S1) from the FAR end of the corridor, with 医生 (S11)'s white-coated shoulder small and out of focus at the edge of frame: she lifts her eyes to him and says, her voice not raised, every word landing, [Chinese] 医生，我外婆的病，没招谁没惹谁。

---

### S3 · ep04_t25 · shots · 工牌位置从近端跳到远端他手边

**问题**：t24 结尾工牌被「啪」拍在**近端**桌面（t24 Shot 2 明写「at the near edge of frame the girl's hands hang open and do not reach for it」），t23 里钱经理也是从远端**走到近端**来撕的工牌。t25 Entry 却写「钱经理 (S3) at the **FAR** end of the long table **with one hand beside the badge**」。工牌与他的手同时从近端瞬移回远端，且这一段没有任何走回去的动作。

**建议改法**（替换 Entry）：

> Entry state, re-anchored to the reference images: 钱经理 (S3) still at the NEAR side of the long table where he came round to her, one hand flat on the wood beside the work badge he has just slapped down; 苏小满 (S1) at the NEAR end facing him, hands at her sides, the badge face-up on the table between them.

---

### S4 · ep04_t33 · shots/refs · 同事与小唐凭空出现，t22–t32 全程从未在场

**问题**：这是本集最典型的用户投诉 bug。t22 的入场是「苏小满 (S1) has just come through the door」，`refs` 只有 `suxiaoman/qianjingli/office_pano`——**门后没有任何人**。t23–t32 逐段复核，同事一次都没出现过。t33 Entry 突然写「**behind her and nearer the lens a few colleagues stand staggered in depth**」，Shot 1 又点名小唐 (S4)。t33 是**组内第 3 段、承 t32 尾帧**，等于上一帧门口空无一人、下一帧凭空站了三个人。

**建议改法**（二选一，推荐 A）：

**A. 在 t22 入场时就建立门后有人**（改动最小，且让 t33 的接缝自然）——把 t22 的 Entry 与 Shot 1 改为：

> Entry state, re-anchored to the reference images: 苏小满 (S1) has just come through the door at the NEAR end of the office, with a few of her cleaning-team colleagues already standing staggered in depth just inside the door behind her; 钱经理 (S3) stands at the FAR end of the long table with his hands empty, facing the near end.
>
> [Shot 1] Medium from the door: 苏小满 (S1) steps in and stops at the NEAR end of the long table, her back to the door and her face to the far end; navy work shirt, grey-blue apron, low ponytail, and a work badge clipped to her chest; behind her the colleagues stay still in the doorway, a little left of centre and out of focus.

同时把 t33 的 refs 从 `suxiaoman/xiaotang/qianjingli/office_pano` 保持不变即可（4 张，未超限）。

**B. 若不想改 t22，则 t33 改为镜头转向门口方向、并说明他们此前一直在画外**：

> Entry state, re-anchored to the reference images: 苏小满 (S1) at the near end of the long table with her back to the door, 钱经理 (S3) at the near side of the table; the door area behind her is out of frame.
>
> [Shot 1] Medium turning past 苏小满 (S1)'s shoulder towards the door end: the colleagues who have been waiting just inside the door since she came in now come into frame, staggered in depth, several of them laughing low; 小唐 (S4) is among them, in a cleaning uniform, shoulders hunched, one hand over her mouth.

---

### S5 · ep04_t37 + ep04_t38 · shots · 钱经理在 t37 跳回远端、t38 又跳回近景前景

**问题**：t29–t32 钱经理一直「comes round from the far end of the long table **to its near side**, leaning towards 苏小满」，t33 仍是「钱经理 (S3) at the near side of the table」。t37 Entry 却写「钱经理 (S3) at the **far end**」——中间没有任何走回动作。t38 承 t37 尾帧，Entry 又写「钱经理 (S3) **in the near foreground**」。连续两段来回跳，把 OTS 的过肩关系彻底打乱，最容易生成两人同框并排。

**建议改法**（替换 t37 的 Entry）：

> Entry state, re-anchored to the reference images: 苏小满 (S1) at the near end of the long table, the stack of claim forms in front of her; 钱经理 (S3) still at the near side of the table opposite her, close enough that only the table's short end separates them.

替换 t38 的 Entry：

> Entry state, re-anchored to the reference images: 钱经理 (S3) at the near side of the long table in the near foreground with his back partly to the lens; 苏小满 (S1) just behind him beyond that same table end, one hand on the table edge, facing him.

---

### S6 · ep04_t81 · shots · 手电从货架瞬移回她手里

**问题**：t73–t80 手电一直被明确放在货架上（t73「the torch lies on the shelf where her hand left it」、t80「the tube light and the torch keep the box and her face both plainly visible」）。t81 Entry 突然变成「苏小满 (S1) standing half a pace back from the bottom shelf **with the torch in her hand**」，Shot 1 还写「its beam **sliding along the concrete floor**」。t81 是**承 t80 尾帧的链式段**，等于上一帧手电躺在架上、下一帧它已经在她手里扫地面——这正是用户投诉的「东西凭空出现」。

**建议改法**（在 t80 的 Shot 2 末尾补上捡手电的动作，让 t81 有前因）：

> …her gaze comes off the box and back ahead, her jaw stays set, and the aisle around her stays open and evenly lit; **and her right hand comes down to the shelf and closes round the torch lying on it.**

（t81 的 Entry 保持现状即可成立。）

---

### S7 · ep04_t83 · shots · 她已带手电出门，手电却又回到货架上

**问题**：t82 全程手电在她手里（「her torch beam bouncing along the concrete」「the torch in her hand」），两人**已跨过门槛走进院子**。t83 Entry 却写「**the torch lies on the shelf** where it was put down, still throwing its beam across the corner」，Shot 1 也写「the torch lies on the shelf… still throwing its beam」。手电在她走出门之后又自己回到了货架上。t83 承 t82 尾帧，首帧直接穿帮。

**建议改法**（替换 t83 的 Entry 与 Shot 1 首句）：

> Entry state, re-anchored to the reference images: the tin box on the bottom shelf of the storage room after the two of them have gone out; the torch has gone with them and the shelf corner is lit only by the ceiling tube.
>
> [Shot 1] Close on the bottom shelf of the storage room: the tin box sits quietly between the scatter of old nails and the coil of old rope, and the clean hand-print in the dust around it has begun to settle back over; the shelf corner is now lit by the ceiling tube alone from above, and the whole aisle, floor and walls stay open and clearly readable to the doorway.

---

### S8 · ep04_t101 · shots · 文件从心腹手里凭空回到桌面

**问题**：t87 陆崇把文件推给心腹，t88 起文件一直在心腹手里（t88「lets it hang at his side」、t89「the document hangs straight and still at his side」、t92「the document stays at his side」）。t101 Entry 却写「the desk top with **the document and the old photograph lying on it**」，Shot 2 又写「the two of them lying side by side on the wood」。t101 承 t100 尾帧，文件在上一帧还挂在他手上，下一帧就平躺在桌上。

**建议改法**（把文件改成仍在他手里，镜头不拍桌面）：

> Entry state, re-anchored to the reference images: 陆崇 (S15) seated back behind the desk with the old photograph lying in front of him, the green-shaded lamp lit; 心腹 (S16) standing half a pace back from the desk with the document still held down at his side, its top edge just in frame.
>
> [Shot 1] Close on the desk top: the old photograph lies where it has lain all along under the green-shaded lamp, and the wood around it is bare; the ceiling fixture adds a second even source so the print is fully readable and every surface stays clear.

---

### S9 · ep04_t103 · shots · 文件位置同 S8，且 Shot 1 有一句语义倒错

**问题**：同 S8，t103 也写「the document and the old photograph **lying on the desk**」。此外 Shot 1 结尾一句写成了「so nothing in this room is left **with every surface still readable**」——「nothing … left with every surface readable」意思变成了「没有任何东西是可读的」，与作者意图（全部可读）相反。这类否定句 H3 极易照字面反着执行。

**建议改法**（替换 Entry 与 Shot 1）：

> Entry state, re-anchored to the reference images: the green-shaded desk lamp lit on the desk beside the old photograph and a bare patch of wood where the file used to lie, the study's ceiling light on above it.
>
> [Shot 1] Close on the green-shaded desk lamp: its glow falls across the edge of the old photograph and the bare wood beside it, and the study's ceiling light layers down from above it; the wall behind, the bookcase edge and the desk surface are all lit at once, so **every surface in this room stays clearly readable**.

---

### S10 · ep04_t104 · shots · 文件位置同 S8

**问题**：Shot 2 写「the last of the lamp's warm pool lies across **the document and the photograph** on the desk」，文件又回到桌面，与 t88–t92 的持有状态冲突。t104 是全剧集最后一帧，这一帧错会让整集以错误道具收尾。

**建议改法**（替换 Shot 2）：

> [Shot 2] At 06.000, The closing hold: the two of them stay exactly as they are in a fully lit room, the clock ticking on the far wall, and the last of the lamp's warm pool lies across the old photograph and the bare wood on the desk, while the document still hangs down at 心腹's side.

---

### S11 · ep04_t94 · shots · 回溯动作「一直在敲」前段从未建立

**问题**：Shot 1 写「the fingers **had been tapping** the wood without any rhythm, and now they stop」。但 t91–t93 三段的正文里，陆崇的手一直是「hands on the wood / hands flat on the wood」静置，从没有敲过。t94 是**组头（idx≡1 mod 3，走 fixed 工作流，从参考图重建）**所以不会真跳帧，但 H3 会照「had been tapping」在首帧就凭空给一段无前因的敲击，且这与 ep003 审核中已修掉的 seg51「Entry 引入上一段没出现过的姿势」是同一类错误。

**建议改法**（替换 Shot 1 首句，不提无前因的过去式）：

> [Shot 1] Close on 陆崇 (S15)'s hand on the desk: the fingers have gone still against the wood, the pads pressed down onto the surface, and the faintest tremble stops in them as they settle; the green-shaded lamp's warm light lies along the knuckles and the ceiling fixture fills the rest, so the whole hand and the desk grain around it are clearly readable.

---

## 一般问题（影响质量，建议改）

### M1 · 时间戳格式与全剧不一致（影响 t01–t104 全部 104 段）· 建议统一改

**问题**：`ep001/ep002/ep003` 用的是 `At 00:05.000,`（**MM:SS.mmm**），`ep004/ep005` 用的是 `At 05.200,`（**SS.mmm**，缺分钟位）。104 段各 1 个时间戳，全部缺 `00:` 前缀。这与用户第 10 条要求的 `At MM:SS.mmm,` 不符，也与本项目自己的构建脚本注释（`_build_ep004_beats.py:26` 明确写 `"""shots: [(拍号, 'MM:SS.mmm' 或 None, 画面文字), ...]"""`）矛盾。

**建议改法**：把每段 `[Shot 2] At 05.200,` 统一改成 `[Shot 2] At 00:05.200,`（正则 `At (\d\d\.\d\d\d),` → `At 00:$1,`）。递增性与「首镜不带 At」两条本身 **104 段全部正确**，只需补分钟位。

---

### M2 · 7 段台词的时长塞不进 Shot 1 的镜头切点（t41/t49/t54/t61/t63/t70/t92）

**问题**：语速预算按 2.5–3.2 字/秒算，这些段虽然**字数都在 26 以内**（第 3 条合格），但台词全在 Shot 1 里说，而 Shot 2 的切点比台词最短需时还早：

| 段号 | 字数 | 台词最短需时 | Shot 2 切点 | 差 |
|---|---|---|---|---|
| ep04_t61 | 25 | 7.8s | 05.800 | 超 2.0s |
| ep04_t49 | 26 | 8.1s | 07.600 | 超 0.5s |
| ep04_t92 | 18 | 5.6s | 05.600 | 零余量 |
| ep04_t41 | 23 | 7.2s | 07.000 | 超 0.2s |
| ep04_t54 | 23 | 7.2s | 07.000 | 超 0.2s |
| ep04_t63 | 23 | 7.2s | 06.600 | 超 0.6s |
| ep04_t70 | 23 | 7.2s | 07.000 | 超 0.2s |

台词会被切断或被压缩到口型不合。

**建议改法**（二选一，推荐各自把切点往后推）：

- 把超时的 `[Shot 2] At 0X.XXX,` 推迟，例如 t61 改 `At 08.600,`、t49 改 `At 09.000,`、t63 改 `At 08.000,`、t41/t54/t70 改 `At 08.000,`；
- 或把台词拆到 Shot 2 里说（在 Shot 1 末尾只留「她开口」）。

---

### M3 · 40 段声景含 quiet / stillness / still air 等近亲词（建议正向化）

**问题**：104 段**无一条命中硬禁用词**（这一条是干净的），但 40 段用了 `the room's quiet` / `the study's still air` / `the study's stillness` / `The quiet of her coat settling` / `then quiet` 一类写法。功能上它们在告诉 H3「这里是静的环境音」，与「不要压人声」的意图相反。

**建议改法**（各段替换示例，直接可用）：

- t22「the office's daytime quiet」→ `the office's daytime room tone, the blind's edge ticking faintly against the frame`
- t26/t28/t31/t35/t37/t40/t44/t47/t49/t50/t51「the room's quiet」→ `the room's air and the building's daytime hum, her own voice the only sound in it`
- t53「The room's quiet」→ `The room's air, his uneven breath close to the lens`
- t08「The quiet of her coat settling」→ `The soft settle of her coat fabric, a page lying flat in the shut ledger, the corridor's morning air`
- t75「then quiet」→ `then nothing more from inside the tin, her held breath, the tube's hum`
- t84–t104「the study's still air」→ `the study's low air, the clock on the far wall, the lamp's hum`
- t84「the study's stillness」→ `the study's low room tone, a clock ticking on the far wall`

---

### M4 · 6 段触及「实物上的字」，其中 2 段措辞会让 H3 去渲染可读文字（t36 / t101 / t103 已在上，t17/t68 需处理）

**问题**：第 6 条允许实物上本来就有的字入画（铁盒钢印、报销单打印字、夹板排期表都算合规）。但**「legible / printed rows are both legible」这类措辞会驱使 H3 生成清晰可读的文字**，一旦字形渲染出来就是烧字。

- t17「a printed roster of names and dates runs down the page in neat rows… his thumb comes to rest on one particular line」——「roster of names and dates」偏向可读人名。
- t85/t101「the document's **printed rows are both legible**」——直接要求"可读"。
- t36「its top line **names** a third-floor carpet replacement at thirty-six thousand」——「names … at thirty-six thousand」等于要求画面出现可读金额。
- t68「the two stamped characters catch the light along their edges… stay **legible** as stamped depressions」——钢印合规，但 "legible" 仍可能被渲染成印刷体汉字。

**建议改法**（把「可读」改成「有形状但读不出」，保留剧情信息）：

- t17 Shot 1：`a printed grid of ruled rows and columns runs down the page, the type too small and soft to resolve into any readable word, and his thumb comes to rest on one particular row and stays there, pressing the paper slightly`
- t36 Shot 1：`the top sheet's printed columns run across the page in neat rows, a ruled line at the top carrying figures that stay small and soft on the paper rather than readable, and the sheet lies under the stack corner nearest 苏小满 (S1)`
- t68 Shot 1：`…and the torch beam falls straight across them from above and the ceiling tube fills the strokes so the two marks stay what they are — shallow depressions pressed into the metal, their shapes clear but reading as struck metal, not printed type`
- t85 / t101 Shot 2：`the print's surface and the document's ruled rows are both clear on the wood, the type on both too small to resolve into readable words`
- t103（已给替换句，见 S9）

---

### M5 · 4-4 全场 21 段写「天花板灯 / ceiling fixture」，与参考图里的落地灯不一致

**问题**：`SCENES['lu_study']`（`storyboard_render.py:253`）对该参考图的描述是「The desk lamp and a **floor lamp** are both switched on」，图里没有描述天花板灯；但 t84–t104 共 21 段反复写「the study's ceiling light is on / the ceiling fixture」。自动前置的 `ANCHOR_44_STUDY`（`:607`）也写了 ceiling light，两边互相矛盾，H3 会在图外凭空加一盏顶灯。

**建议改法**（21 段统一替换，`ceiling light` / `ceiling fixture` → `floor lamp`）：

- 「the green-shaded desk lamp on the desk is switched on and the study's ceiling light is on as well」→ `the green-shaded desk lamp on the desk and the floor lamp behind the armchair are both switched on`
- 「the ceiling light keeps the whole upper frame open」→ `the floor lamp behind the chair keeps the whole upper frame open`
- t89 Shot 2「his face is evenly lit from the front by the ceiling fixture」→ `his face is evenly lit from the front by the floor lamp behind him`

---

### M6 · 3 段配乐连续（t93 / t95 / t97）建议只留一处

**问题**：这三段连号，每段都挂一条「A low string entry/note, held…」，第四集尾部会变成连续弦乐垫底，掩盖 `STYLE` 要求的对白空间；t20/t31/t45/t49/t56/t68/t75/t78/t83/t98/t104 单条使用没有问题。

**建议改法**：保留 t93 一条，其余两条改 `N/A`：
- t95 `music` → `N/A`
- t97 `music` → `N/A`

（若需要保留情绪递进，改成 t97 保留、t95 改 `N/A`，避免两条描述雷同。）

---

### M7 · t15 声景直接写「四秒不说话」，把最该听见人声的段压掉

**问题**：`soundscape` 写「a distant monitor beep, **four full seconds of her not speaking**, the fluorescents」。虽然 t15 本就是「她不说话」的沉默段，但这句是在**声景字段**里显式命令 H3 生成四秒无人声，正是第 4 条想避免的效果。

**建议改法**（改为她能听见的环境与人声气息，不写「不说话」）：

> Her slow even breathing, the corridor air moving past her, a distant monitor beeping and then falling off, the steady hum of the fluorescents above her.

---

### M8 · t52 `refs` 缺 suxiaoman（她本人入画）· 建议补

**问题**：t52 Shot 1 写「it swings closed **behind 苏小满 (S1)** and the handle settles」，她本人虽已转身但**在画面内**，而 `refs` 只有 `qianjingli/office_pano`。第 11 条要求「只放本段真的在场的人与场景」——反过来也要求在场的人都挂上。少了她，H3 会自己生成一个后脑勺和一个素色外套，与前 51 段累积的脸/发型/服装脱钩。

**建议改法**：`refs` 改为 `["suxiaoman", "qianjingli", "office_pano"]`（3 张，未超限），`retention` 同步加 `"suxiaoman": "fully_preserved"`。

---

### M9 · t02 入场说笔在胸前口袋，Shot 2 笔已经在手里

**问题**：Entry 写「the ballpoint pen **clipped in her chest pocket** are visible」，紧接着 Shot 2 就写「**the tip of her pen** comes to rest and stays there, not touching the paper」。笔从口袋瞬移到手里，跨了 t01→t02 的链式接缝。

**建议改法**（替换 Entry 末句，统一成「笔已在手里」）：

> …her pale uniform and white nursing shoes visible, a ballpoint pen in her right hand resting against the open ledger; the counter edge still cuts the bottom third.

---

### M10 · t05 承接 t04 时手的落点变了（悬空 → 搭在台面）

**问题**：t04 结尾是「the hand at the counter edge **does not move**」，Entry 也写「right hand **hovering above** the counter edge」；t05 Entry 直接变成「hand now **resting on** the counter edge」。悬空变成搭上，是一个可见的状态跳变，t05 承 t04 尾帧。

**建议改法**（替换 t05 Entry 首个分句，保持悬空）：

> 护士长 (S20) behind the counter, her palm flat on the ledger; 苏小满 (S1) on the near side of the counter, her right hand still hovering just above the counter edge without touching it, facing in.

---

### M11 · t58 声景把光束写成会「刮擦」金属

**问题**：`soundscape` 写「the soft scrape of a **torch beam** crossing metal shelving」。光束不会刮擦物体，这个动作用词会让 H3 生成一条不存在的物理动作/声音。

**建议改法**：

> The fluorescent tube humming overhead, a faint breath of night air coming in through the open doorway, and her shoe sole turning on the concrete at the near end of the aisle.

---

### M12 · t61 台词内出现未注册人名「陆总」，可能触发一个新的说话人

**问题**：`[Chinese] 陆总说了。…` 中的「陆总」在本剧的角色表里是 `陆崇 (S15)`，但 `SPEAKERS_EP['ep004']` 的编号列表里只有 `陆崇 (S15)`，没有「陆总」这个称谓。H3 的对话语法按 (S#) 解析，这里的「陆总」是台词内容而非标注，风险较低；但若模型把它当成一个待发声的说话人，会多出一段不属于任何编号的男声。

**建议改法**（把称谓换成与角色表一致的写法）：

> [Chinese] 陆先生说了。桥下那年的旧东西，你挨着找找，看有没有能对上的。

---

### M13 · t101 有一处重复字 `the the`

**问题**：「**the the** wood grain runs clean around them」。虽不影响生成，但属明显笔误。

**建议改法**：`the wood grain runs clean around them`。

---

### M14 · 词量：shots 正文普遍偏薄（49 段低于 120 词）

**问题**：第 12 条要求 `detailed_description` 有 350–500 英文词量级。拼装后（含自动前置的 STYLE / NO_TEXT / SPEAKERS / 空间锚点 / 曝光重锚，804–977 词）每段总计 **900–1216 词**，已远超 500；但**分镜正文自身**只有 84–239 词，均值 123。最薄的 10 段：

| 段号 | 词量 | 段号 | 词量 |
|---|---|---|---|
| ep04_t63 | 84 | ep04_t43 | 96 |
| ep04_t72 | 85 | ep04_t69 | 96 |
| ep04_t47 | 86 | ep04_t28 | 97 |
| ep04_t92 | 94 | ep04_t32 | 97 |
| ep04_t13 | 96 | ep04_t90 | 97 |

**建议改法**：这 10 段每段补 1 个具体可拍的元素（一个前景物体、一处材质、一个既有道具的落点），例如 t63 补货架分区上的旧标签纸边、t72 补他鞋尖在混凝土上的位置，**不要补抽象形容词**。

---

## 已核对无问题项

1. **说话人编号（第 1 条）**：45 段有台词，每句台词所在的 Shot 块内**均含 (S#) 标注**（脚本逐块校验，0 例外）。跨段编号全部稳定：苏小满 S1、钱经理 S3、小唐 S4、小罗 S7、医生 S11、陆崇 S15、心腹 S16、护士长 S20，与 `SPEAKERS_EP['ep004']` 声明的编号表**完全一致**，无同一人换号。
2. **台词格式（第 2 条）**：见总评表，零违规。
3. **语速预算（第 3 条）**：45 段台词字数 2–26 字，**无一超过 26 字上限**；最长的 t49（26 字）与 t61（25 字）本身合规，只是与镜头切点的时间冲突已单列为 M2。
4. **声景压人声（第 4 条）**：硬禁用词 0 命中（详见总评表）。
5. **曝光压暗（第 5 条）**：12 个禁用词在 shots/summary/soundscape/music 四字段中 0 命中。全文 `shadow` 仅出现 12 次，且全部是 `soft and open` / `unshadowed wood` / `no shadow gathering` 这类正向或否定式安全写法。
6. **画面文字（第 6 条）**：104 段**无任何**字幕 / caption / lower-third / title card / watermark / on-screen text 叠加文字；出现的字全部是实物字（铁盒钢印、报销单打印行、夹板排期表、文件夹排期表），符合豁免。需处理的只有 6 段的措辞（M4）。
7. **音乐（第 7 条）**：90 段写 `N/A`，14 段有配乐。其中 t20/t31/t45/t49/t56/t68/t75/t78/t83/t98/t104 为单条使用，**无重复堆叠**；只有 t93/t95/t97 连号需合并（M6）。
8. **时间戳（第 10 条）**：「第一镜不带 At、后续镜带 At」104 段全部正确，且**每段只有 1 个时间戳**，递增性天然满足；唯一问题是格式缺 `00:` 分钟位（M1）。
9. **参考图（第 11 条）**：见总评表，零违规。人物段只挂真在场者（t20 只挂苏小满、t31 只挂苏小满、t42 只挂钱经理，均因另一人明确写出画）；唯一缺挂是 t52（M8）。
10. **四组场景锚点自洽性**：4 段锚点（`ANCHOR_41_NURSE` / `ANCHOR_41_CORR` / `ANCHOR_42_OFFICE` / `ANCHOR_43_STORE` / `ANCHOR_44_STUDY`）在本集的落地情况——
    - **4-1a 护士站**：9 段全部守「护士长恒在台后远端、女孩恒在台前近端、两人绝不并排」，逐段核对无误。
    - **4-1b 走廊**：11 段守「医生恒在远端、女孩恒在近端」，**唯 t12、t16 破例**（S1/S2）。
    - **4-2 办公室**：36 段守「钱经理恒在远端、女孩恒在近端、t29 允许他绕到近侧一次」，**唯 t25、t37、t38 破例**（S3/S5）。
    - **4-3 杂物间**：27 段守「女孩恒在货架前中景偏左、小罗恒在其后靠门、画面左中景+右近景错落」，道具线（手电 / 铁盒 / 灰手印）追踪为：手电在她手（t60–t72）→ 放上货架（t73–t80）→ 应为她捡起（t81–t82）→ **t83 却又回货架**（S6/S7 是唯一两处断点，其余道具状态全部逐段咬合）。
    - **4-4 书房**：21 段守「陆崇恒在桌后远端、心腹恒在桌前近端」，文件线（t87 推 → t88–t92 持在手里）仅在 t101/t103/t104 破例（S8/S9/S10）。
11. **六段式拼装完整性**：104 段经 `storyboard_render.render()` 实跑，`subject_definitions / summary / retention_analysis / detailed_description / overall_soundscape / non_diegetic_music` 六段**无一缺失**，无渲染异常。

---

## 逐段检查表

| 段号 | 说话人 | 台词字数 | 声景 | 曝光 | 文字 | 锚点 | 结论 |
|---|---|---|---|---|---|---|---|
| ep04_t01 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t02 | — | — | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t03 | 苏小满 S1／护士长 S20 | 12 | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t04 | 苏小满 S1／护士长 S20 | 3 | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t05 | 苏小满 S1／护士长 S20 | 18 | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t06 | 苏小满 S1／护士长 S20 | 6 | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t07 | 苏小满 S1／护士长 S20 | 7 | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t08 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t09 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t10 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t11 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t12 | — | — | 合格 | 合格 | 合格 | ✗ 医生被推到近景前景，自相矛盾且违锚点 | **严重** |
| ep04_t13 | 苏小满 S1／医生 S11 | 12 | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t14 | 苏小满 S1／医生 S11 | 13 | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t15 | — | — | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t16 | 苏小满 S1／医生 S11 | 13 | 合格 | 合格 | 合格 | ✗ 医生被推到近景前景，违 4-1b 锚点 | **严重** |
| ep04_t17 | — | — | 合格 | 合格 | 注意 | ✓ | 整改 |
| ep04_t18 | 苏小满 S1／医生 S11 | 10 | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t19 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t20 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t21 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t22 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t23 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t24 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t25 | 苏小满 S1／钱经理 S3 | 12 | 合格 | 合格 | 合格 | ✗ 工牌在 t24 拍于近端，t25 却在远端他手边 | **严重** |
| ep04_t26 | 苏小满 S1 | 3 | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t27 | 苏小满 S1／钱经理 S3 | 14 | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t28 | 苏小满 S1／钱经理 S3 | 14 | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t29 | 苏小满 S1／钱经理 S3 | 12 | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t30 | 苏小满 S1／钱经理 S3 | 14 | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t31 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t32 | 苏小满 S1／钱经理 S3 | 15 | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t33 | — | — | 注意 | 合格 | 合格 | ✗ 同事与小唐凭空出现（t22–t32 从未在场） | **严重** |
| ep04_t34 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t35 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t36 | — | — | 注意 | 合格 | 注意 | ✓ | 整改 |
| ep04_t37 | 苏小满 S1／钱经理 S3 | 11 | 注意 | 合格 | 合格 | ✗ 钱经理无交代回到远端 | **严重** |
| ep04_t38 | 苏小满 S1／钱经理 S3 | 18 | 注意 | 合格 | 合格 | ✗ 钱经理又跳回近景前景（承 t37 链式） | **严重** |
| ep04_t39 | 苏小满 S1／钱经理 S3 | 5 | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t40 | 苏小满 S1／钱经理 S3 | 16 | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t41 | 苏小满 S1／钱经理 S3 | 23 | 注意 | 合格 | 合格 | ✓ 台词超时 | 整改 |
| ep04_t42 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t43 | 苏小满 S1／钱经理 S3 | 5 | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t44 | 苏小满 S1／钱经理 S3 | 11 | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t45 | 苏小满 S1／钱经理 S3 | 16 | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t46 | 苏小满 S1／钱经理 S3 | 7 | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t47 | 苏小满 S1／钱经理 S3 | 9 | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t48 | 苏小满 S1／钱经理 S3 | 23 | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t49 | 苏小满 S1／钱经理 S3 | 26 | 注意 | 合格 | 合格 | ✓ 台词超时 | 整改 |
| ep04_t50 | 苏小满 S1／钱经理 S3 | 14 | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t51 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t52 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t53 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t54 | 钱经理 S3 | 23 | 注意 | 合格 | 合格 | ✓ 台词超时 | 整改 |
| ep04_t55 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t56 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t57 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t58 | — | — | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t59 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t60 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t61 | 苏小满 S1／小罗 S7 | 25 | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t62 | 苏小满 S1／小罗 S7 | 6 | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t63 | 苏小满 S1／小罗 S7 | 23 | 合格 | 合格 | 合格 | ✓ 台词超时 | 整改 |
| ep04_t64 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t65 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t66 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t67 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t68 | — | — | 合格 | 合格 | 注意 | ✓ | 整改 |
| ep04_t69 | 苏小满 S1 | 2 | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t70 | 苏小满 S1／小罗 S7 | 23 | 合格 | 合格 | 合格 | ✓ 台词超时 | 整改 |
| ep04_t71 | 苏小满 S1／小罗 S7 | 5 | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t72 | 苏小满 S1／小罗 S7 | 8 | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t73 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t74 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t75 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t76 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t77 | 苏小满 S1／小罗 S7 | 2 | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t78 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t79 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t80 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t81 | — | — | 合格 | 合格 | 合格 | ✗ 手电从货架瞬移回她手里 | **严重** |
| ep04_t82 | — | — | 合格 | 合格 | 合格 | ✓ | 通过 |
| ep04_t83 | — | — | 合格 | 合格 | 合格 | ✗ 她已带手电出门，手电却回到货架上 | **严重** |
| ep04_t84 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t85 | — | — | 注意 | 合格 | 注意 | ✓ | 整改 |
| ep04_t86 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t87 | — | — | 合格 | 合格 | 合格 | △ 天花板灯≠参考图的落地灯 | 整改 |
| ep04_t88 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t89 | 陆崇 S15／心腹 S16 | 12 | 合格 | 合格 | 合格 | △ 天花板灯≠参考图的落地灯 | 整改 |
| ep04_t90 | 陆崇 S15／心腹 S16 | 10 | 合格 | 合格 | 合格 | △ 天花板灯≠参考图的落地灯 | 整改 |
| ep04_t91 | 陆崇 S15／心腹 S16 | 5 | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t92 | 陆崇 S15／心腹 S16 | 18 | 注意 | 合格 | 合格 | ✓ 台词超时 | 整改 |
| ep04_t93 | — | — | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t94 | — | — | 合格 | 合格 | 合格 | △ 回溯动作「一直在敲」前段从未建立 | 整改 |
| ep04_t95 | 陆崇 S15／心腹 S16 | 11 | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t96 | 陆崇 S15／心腹 S16 | 4 | 合格 | 合格 | 合格 | △ 天花板灯≠参考图的落地灯 | 整改 |
| ep04_t97 | — | — | 合格 | 合格 | 合格 | ✓ | 整改 |
| ep04_t98 | 陆崇 S15／心腹 S16 | 8 | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t99 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t100 | — | — | 合格 | 合格 | 合格 | △ 天花板灯≠参考图的落地灯 | 整改 |
| ep04_t101 | — | — | 注意 | 合格 | 注意 | ✗ 文件从心腹手里回到桌面 | **严重** |
| ep04_t102 | — | — | 注意 | 合格 | 合格 | ✓ | 整改 |
| ep04_t103 | — | — | 注意 | 合格 | 注意 | ✗ 文件位置同 t101，且语义倒错 | **严重** |
| ep04_t104 | — | — | 注意 | 合格 | 合格 | ✗ 文件位置同 t101 | **严重** |

---

*审核员：独立审核（只审不改）。本报告未改动任何分镜 JSON；`_audit_ep004.py` 为本次审核的取数脚本，可复跑复现全部数字。*
