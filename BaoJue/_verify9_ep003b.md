# ep003 场次 3-4 / 3-5 / 3-6 审核报告

> 审核范围：`ep003_beats/scene34.json`（t110–t130 / seg65–85）、`scene35.json`（t140–t154 / seg86–100）、`scene36.json`（t160–t169 / seg101–110）。
> 抽查对象：`ep003_segs/seg65_prompt.txt` ~ `seg110_prompt.txt`，**全部 46 段逐段读取**（远超要求的 14 段），并按 `manifest.json` 下标每 3 段还原链组。
> 判据：`minimax-h3-prompt-audio`（H3 六段式 / 台词语法 / 声景正向写）+ `minimax-h3-chained-segment-drift`（首帧=上一段尾帧）+ AGENTS.md 十五、十六章。

## 总体结论（通过 / 有条件通过 / 不通过）

**有条件通过。**

- 六段式、台词语法（`[Chinese]` 无引号）、字幕词、台词预算、表演可见性、参考图在场、道具连续性、3-4 纵深一列 / 3-5 上下分层 / 3-6 纵向视线 —— **全部合格**。
- 但存在 **3 条高优先级**：① 3-4 组内第 2/3 段 Entry 把「小罗」丢了（链式，权重最高）；② 3-6 每段的自动前置 STYLE 与「曝光重锚」混进了**前几集大厅/书房的水晶吊灯、绿罩台灯**（10 段全中）；③ 3-4 空间锚点在陆蔓离场后仍写她「走在最前」。
- **条件**：先修补下述 3 条「高」，重跑对应链组（65–85、101–110）后，方可放行；否则判不通过。

---

## 高

- **seg66 / seg67 / seg68（＝ep03_t111 / t112 / t113）** 链式顺接断裂：seg65（t110）末拍 [Shot 3] 明确写「**三人在廊下排成一列：陆蔓最远、苏小满次之、小罗最近，never abreast**」，且 3-4 空间锚点也规定「小罗恒在苏小满身后、离镜头最近」；但 **seg66、seg67、seg68 的 Entry 与 refs 都把小罗整段丢掉了**（refs 里没有 `xiaoluo`），随后 **seg69（t114）Entry 又凭空写出「小罗站在苏小满左后」**。组内第 2/3 段 Entry 未逐字对上上一段最后一拍，小罗「消失又出现」。
  应改成（seg66 Entry，seg67 同法）：
  「Entry state, re-anchored to the reference images: 陆蔓 (S8) walks at the front of the deep veranda with her back to camera; 苏小满 (S1) follows half a step at her left-rear facing her back; **小罗 (S7) trails a further half step behind 苏小满 (S1), nearest to camera, his face travelling between the two women;** the blue brick floor and the corridor curb hold the bottom third of frame.」
  （并把 `xiaoluo` 补进 seg66/67/68 的 refs / subject_definitions。）

- **seg101–seg110（3-6 全 10 段）** 自动前置段与分镜正文打架：`STYLE` 段内嵌的「夜景布光」句与「曝光重锚」段都写着
  「the crystal chandelier, the table lamps and the wall sconces, or the green-shaded desk lamp and the floor lamp」／「…in the hall…in the study」——这是**前几集大厅/书房**的遗留，出租屋里只有书桌上一只旧台灯。会诱导把吊灯、绿罩台灯、书房陈设烧进这个狭小夜戏（违背 15.8 / 16.1）。
  应改成（STYLE 段）：
  「It is night indoors, but lit like a bright soft-spoken commercial: **the little room is lit by its one real practical, the old table lamp on the desk, switched on and generous, plus soft front fill** — and it behaves as a big soft source wrapped in fill, so there is no dark side on any face and no black shadow anywhere.」
  应改成（曝光重锚段）：
  「Exposure and colour must match the reference night images exactly — bright but night-balanced, **lit only by the real practical visible in the room: the lit old table lamp on the desk**.」

- **seg72–seg85（3-4 后半，＝t117–t130）** 空间锚点与正文打架：这 14 段的 `Fixed spatial set-up for the whole veranda scene` 仍硬写
  「**陆蔓 (S8) walks furthest away, back to camera, mid-ground right of centre.** 苏小满 (S1) follows half a step behind and to 陆蔓's LEFT… The three are strung out in DEPTH in that order」
  可是 t116 起陆蔓已「拂袖走了」并在 t117 Entry 明确「gone from frame」，此后画面里只有苏小满与小罗（refs 也已去掉 `luman`）。锚点仍在描述「三人在走」，极易把已离场的陆蔓画回画面。
  应改成（这些段的锚点第一句）：
  「**陆蔓 (S8) has already walked off and is out of frame down the veranda; 苏小满 (S1) and 小罗 (S7) stand in the corridor, 小罗 (S7) nearest to camera, and the handing over and snatching back of the photocopied list happens in the depth gap between them.**」

---

## 中

- **seg97（＝ep03_t151）** 链式第 3 段未对上末拍：seg96（t150）末拍 [Shot 2] 是「**上层二楼窗 + 下层苏小满，一上一下两层同框**」，seg97 Entry 却只写「苏小满站在照片墙下、指尖还朝着玻璃」，**整段丢掉了仍在窗后的陆崇**。
  应改成：
  「Entry state, re-anchored to the reference images: 苏小满 (S1) stands below the photograph wall with her upturned face at the frame and her fingertip toward the glass; **above in the upper right of frame 陆崇 (S15) still stands behind the old window looking down;** the veranda runs away from her toward the moon gate.」

- **seg72（＝ep03_t117）** 链式第 2 段动作跳了一拍：seg71（t116）末拍 [Shot 3] 是「**她的背影在廊子里一路变小、朝月洞门去，始终没回头**」（仍在画面内），seg72 Entry 却写「陆蔓 has gone from frame」，首帧会与引导尾帧对不上。
  应改成：
  「Entry state, re-anchored to the reference images: **陆蔓 (S8) is a small back receding far down the veranda toward the moon gate;** 苏小满 (S1) and 小罗 (S7) stand in the corridor, 小罗 (S7) nearer the camera; 苏小满's hands are still empty at her sides.」

- **seg86–seg94 / seg98–seg100（3-5 非揭示段）** 空间锚点越权点名不在场/未揭示的人：
  「**陆崇 (S15) stays in the upper RIGHT corner of frame behind a first-floor window… 小罗 (S7) stays at the far end of the depth axis…**」
  而这三段链之外（86–94 是沿墙行走的段落）正文里陆崇尚未揭示（t149 才出现），refs 也没有 `luchong`；锚点却要求他「恒在画面右上角」，容易把二楼的陆崇提前/全程画进每一镜。
  应改成：
  「**陆崇 (S15) appears only in the window-reveal segments, in the upper RIGHT corner of frame behind a first-floor window, looking down from a higher LEVEL, and never comes down to the ground floor; in every other shot of this scene he stays OUT of frame. 小罗 (S7) appears only in his own segment, out at the far end of the depth axis, half a body or a voice off-frame.**」

- **seg101–seg110（3-6 全段）** 参考图 `<Picture 2>` 描述「**one small curtained window on the right**」，与锚点「**The window is always at the FAR end**」及正文「the window sits far beyond her」直接矛盾；窗若被摆到右墙，就破坏了「照片→灯→夜窗」的纵向凝视轴（16.1）。
  应改成：
  「**one small curtained window at the far end of the room, in the direction she faces**」

- **seg85 → seg86（3-4 末 → 3-5 首，跨场次组）** 硬切，判**中**。边界段 seg86（t140）为链组头（下标 86，86 mod 3 = 2 → 组首），确认会走 `..._fixed.json` 无引导重建，不继承 3-4 的尾帧；此处无需改动。／ 应改成：「**无需改动（硬切 + 组头 fixed 重建，符合 15.2 / 15.9）**」

- **seg100 → seg101（3-5 末 → 3-6 首，跨场次组）** 硬切，判**中**（且跨白天→夜、跨场景）。边界段 seg101（t160）为链组头，确认走 fixed 重建。／ 应改成：「**无需改动（硬切 + 组头 fixed 重建，符合 15.2 / 15.9）**」

---

## 低

- **seg102 / 103 / 104 / 106 / 107 / 108 / 109 / 110** 声景用了「环境静了」的软否定写法：`the still night beyond the window` / `the quiet night at the window` / `the night holding still beyond the window` / `the night resting beyond the window` / `the low night beyond the window`。虽未命中 15.7 的硬禁用词表，但仍属「写这里没有声音」的思路，有压低声/人声的风险。
  应改成（以 seg106 为例，其余同法）：
  「The lamp's steady hum, one slow breath above the desk, the faint flex of the old paper, and **the building's far tick beyond the window**.」

- **seg96 / seg108** 轻微偏黑措辞：seg96 [Shot 1]「a thin film of dust on the glass **darkens his face**」；seg108 [Shot 2]「the room beyond her **stays dim**」。与「no black areas / lifted blacks」的正向锚有张力。
  应改成：seg96 →「a thin film of dust on the glass **softens his features**」；seg108 →「**the room beyond her stays warmly lit by the lamp**」。

- **全 46 段（NO_TEXT 前置段）** 反否定块里的示例句仍举着前几集的道具：`the gilt character stamped into the face of the black card`。本集 3-4/3-5/3-6 没有「黑卡」，该示例可能诱导黑卡/烫金字出现在廊下或出租屋。
  应改成：「The only text that may exist is lettering **physically printed on a real object already present in the location** (signage, a nameplate or lettering already on the set).」

- **seg100（＝ep03_t154）** 把非画内音乐写进了 `overall_soundscape`：「…and **a single piano note left hanging in the air**.」，同时 `non_diegetic_music` 又写 `A single suspended piano note, left hanging.` 同一音效出现在两处（技能 2.3：非画内音乐只放 `non_diegetic_music`）。
  应改成：soundscape 末句 →「…and **the far courtyard settling after her steps**.」（piano 只留在 `non_diegetic_music`。）

- **seg78 / seg79（3-4 待核清单特写）** 目前正文确实没写清单上印着什么字（合格），但 `NO_TEXT` 块允许「真实物品上本来就印着的字」，清单是实物，仍有被渲染出可读字的风险。
  应改成（seg79 [Shot 1] 句末追加）：
  「her fingertip travels down from that line to another entry and stops; the camera follows her finger down the sheet; **the printed entries on the sheet stay soft and illegible, with no readable lettering.**」

---

## 已核对无问题项

1. **六段式完整性**：seg65–110 共 46 段，`subject_definitions / summary / retention_analysis / detailed_description / overall_soundscape / non_diegetic_music` 六段齐全；`non_diegetic_music` 除 seg100（钢琴）、seg110（弦乐）外均为 `N/A`（对应剧本 ♪）。
2. **自动前置段在场**：STYLE（含 LIGHTING SOFT/BRIGHT 正向锚）、NO_TEXT、SPEAKERS（(S1)–(S19) 编号表）、空间锚点（3-4 廊下 / 3-5 照片墙 / 3-6 出租屋三套）、曝光重锚，**逐段均存在**（存疑处已在「高/中」列出）。
3. **链组划分**：按 manifest 下标每 3 段硬切 → 3-4 七组（65–67 / 68–70 / 71–73 / 74–76 / 77–79 / 80–82 / 83–85）、3-5 五组（86–88 / 89–91 / 92–94 / 95–97 / 98–100）、3-6 三组 + 尾段（101–103 / 104–106 / 107–109 / 110）。**除上文列出的 4 处外，其余组内第 2/3 段 Entry 均逐字对上了上一段末拍**（74–76、77–79、80–82、83–85、86–88、89–91、92–94、95–96、98–100、101–110 全部通过）。
4. **声景否定式（15.7）**：3-4/3-5/3-6 正文与 soundscape **无一条** verbatim 命中 `silence / silent / mute / muted / nothing at all / dead quiet / total hush / gone quiet / nothing but / absolute quiet / no other sound / almost nothing / no dialogue / without sound / no intelligible`。唯一的 `silent` 出现在 SPEAKERS 固定句「stays completely silent with a closed mouth」（合规，且是「明说某人闭嘴」的正确做法）。
5. **不烧字幕（15.6）**：正文**无** `subtitle / caption / lower-third / title card / on-screen text / text overlay / watermark`；这些词仅出现在被要求的 `NO_TEXT` 反否定块内。**台词一律 `[Chinese] …`，无一处被引号包裹**（全库正则检索无中文引号句）。
6. **重点① 3-4 待核清单**：seg72/73/75/78/79/81/82/84/85 只写「that line / another entry / the sheet / the page」，**没有写出清单上印着的任何字**（桥南/桥北仅出现在 `[Chinese]` 音频台词里）。
7. **重点② 3-6 照片背面**：seg106 用「a line of faded handwriting … **unreadable**」，**未把「小满一岁，大桥」写进画面**，符合要求；seg105 翻面、seg106 指尖停在字行上方的手法可见。照片**正面**内容（seg103 年轻女人抱婴儿站江边、seg104 身后大桥与旧桥墩）可以写，已写且与 3-5 照片墙对上。
8. **参考图在场（15.8）**：`luchong` 仅挂在 seg95/96（正是他出现的两段），seg86–94、97–100 均**不挂**；3-6 全段只挂 `suxiaoman` + `rental_room`，**无多余角色**；陆蔓离场后（seg72–85）refs 已去掉 `luman`。无「挂不在场角色/场景」。
9. **空间锚点（16.1）**：3-4 三人**沿纵深一列**（seg65 [Shot 3]「single file… never abreast」、seg69/70「one depth line / 陆蔓 furthest … 小罗 nearest」），无并排；3-5 照片墙恒在**画面右墙**、陆崇恒在**上层二楼窗后**（seg95/96 明写「a floor apart / upper…lower」），未见下到一楼同框；3-6 苏小满在桌前近半幅、灯与照片在中景、夜窗在远端，**无「窗/灯/人」横排**。
10. **道具连续性（0.7）**：待核清单「小罗塞给（seg72）→ 发现桥南/桥北（seg78/79）→ 被抽回（seg84）→ 空手（seg85）」连续；泛黄照片「3-5 认出旧桥墩（seg90–94）→ 3-6 台灯下对照（seg102–104）」连续；背面褪色字（seg105–106）在；`旧布包`「摊开后不再收回」按锚点保持；红绳在 3-6 由 seg107「the short red cord at her collar」接续。
11. **台词预算（16.4）**：3-4/3-5/3-6 无一段超 24 字。最长 seg78（t123「当年的病案写着，老爷子是从大桥南边巷口送医的。」）＝21 字，21/2.5＝8.4 s ≤ 10 s，余量充足。
12. **表演可见性（16.2）**：无「只有台词」的段。每段均有可见动作/表情/目光/位移（如 seg67 目光落在脚前青砖、seg74 眉头一皱、seg84 抽单子、seg100 第三步停住回望、seg108 下唇一抿等）。
13. **画面偏黑风险**：全库无 `pitch dark / in darkness / dimly lit / unlit`；`murky` 仅出现在「not murky」的负向正向锚里（合规）。仅 seg96「darkens his face」与 seg108「stays dim」两处措辞偏软（已列低）。
