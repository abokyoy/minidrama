# ep002 第②层审核报告 — 场次 2-3 / 2-4 / 2-5（`_verify8_ep002b`）

> 审核员：独立子代理（只审不改）。依据：`AGENTS.md` 十五、十六章；技能 `minimax-h3-prompt-audio`、`minimax-h3-chained-segment-drift`。
> 审核对象：`ep002_beats/scene23.json`（t80–t87）、`scene24.json`（t90–t108）、`scene25.json`（t110–t121），及其成品提示词 `ep002_segs/seg68_prompt.txt … seg106_prompt.txt`。
> 抽查量：**seg68–seg106 共 39 段成品提示词全部通读**（远超要求的 12 段），并对照第①步 `文字剧本.md` 第 8–147（空间锚点）、第 460–646（场次 2-3/2-4/2-5）。

---

## 总体结论

**不通过，需整改后重渲染受影响段。**

- **硬性问题 1 处**：`seg79` 的 Entry 与上一段末拍**人物位置跳变**（15.9 权重最高，组内第 3 段）。
- **中等问题 6 处**：1 处链组内对照（同一 `seg102` 段内自相矛盾 + t117→t119 照片"手上/桌上"道具翻转）、1 处角色造型自相矛盾（陆崇外套"深藏青" vs "深墨绿"）、1 处参考图打光错位（黄昏/下午医院素材图被当成上午戏"exact lighting reference"）、1 处大厦名残留（`文字剧本.md` 仍写"万山大厦"）、2 处跨场次硬切（按规则判「中」，登记备查）。
- **低风险 5 处**：均为描述精度/参考图降级类小问题，不阻断渲染。
- 六段式、声景正向写法、无字幕词、无引号台词、无偏黑硬描述、参考图在场、空间锚点、台词预算、表演可见性等**大项全部通过**（详见末节）。

---

## 高

### H1　`seg79`（t93）Entry 与 `seg78`（t92）末拍位置跳变 —— 违反 15.9

- 组 `{77,78,79}` 内 `seg79` 是第 3 段，其 Entry 必须等于上一段最后一拍。
- `seg78`（t92 走廊让路）最后一拍画面：苏小满仍在**走廊半途**。
  > `[Shot 3] At 00:07.200, she passes a colleague holding a stack of files who half-steps back into the wall, his face turning to follow her on down the corridor. She says nothing.`
- `seg79` Entry 却已到**更衣间门帘并掀帘进入**，中间没有任何镜头交代"走到更衣间门口"。
  > `Entry state, re-anchored to the reference images: 苏小满 (S1) reaches the locker-room curtain at the near end and pushes through it.`

**应改成（把 Entry 拉回走廊末段，并在 `[Shot 1]` 前补一拍可见位移）：**

`seg79_prompt.txt` 第 18 行，原文：
```
Entry state, re-anchored to the reference images: 苏小满 (S1) reaches the locker-room curtain at the near end and pushes through it.
```
改为：
```
Entry state, re-anchored to the reference images: 苏小满 (S1) has just passed the last clerk in the corridor and walks on along the corridor's depth toward the locker-room doorway at the far end.
```
并把该段落正文第一拍改写为带位移的一拍（示例，紧接 Entry 之后）：
```
[Shot 1] Medium: 苏小满 (S1) comes down the corridor, reaches the locker-room doorway at the near end and pushes its door curtain aside.
[Shot 2] At 00:04.200, wide down the narrow locker room: rows of grey metal lockers recede on both sides with a long bench table down the middle, and 苏小满 (S1) steps through the curtain at the near edge of frame.
[Shot 3] At 00:07.200, medium: she walks to her own locker and stops in front of it, facing back toward the curtain doorway, her hand resting on the locker door with her thumb by the lock. She says nothing.
```

---

## 中

### M1　照片"在手上 / 在桌上"自相矛盾 + t117→t119 道具翻转（`seg102` 段内 + `seg103`→`seg104`）

三处互相打架：

1. `seg102`（t117）**同一段内** Entry 与 `[Shot 2]` 冲突——
   - Entry：`陆崇 (S15) sits far behind the desk, the photograph resting in his right hand, the tea cup at his right on the desk;`
   - `[Shot 2]`：`his gaze travels over the top of the cup and settles on the photograph on the desk.`
2. `seg103`（t118）Entry 仍写照片在手里：`the photograph in his other hand`。
3. `seg104`（t119）Entry 却已变成 `the photograph lying on the desk`，中间没有任何"把照片放回桌面"的镜头。
4. 且第①步 `文字剧本.md` 第 628 行明确写着"他的目光越过茶盏，落在**桌上**那张照片上"——**照片应在桌面**。

**应改成（以剧本"照片在桌面"为准，补齐一次可见的"放下照片"动作）：**

`seg102_prompt.txt` 第 20 行，原文：
```
Entry state, re-anchored to the reference images: 陆崇 (S15) sits far behind the desk, the photograph resting in his right hand, the tea cup at his right on the desk; 心腹 (S16) stands in the near half.
```
改为：
```
Entry state, re-anchored to the reference images: 陆崇 (S15) sits far behind the desk with the photograph still held in his right hand over the spread on the desk, the tea cup at his right; 心腹 (S16) stands in the near half.
```
`seg102_prompt.txt` 第 21 行（`[Shot 1]`），原文：
```
[Shot 1] Close on his hand: 陆崇's (S15) left hand lifts the tea cup up to chest height and holds it there, the steam thinning above the rim.
```
改为：
```
[Shot 1] Close on his hand: 陆崇's (S15) right hand lays the photograph back down flat on the spread, then his left hand lifts the tea cup up to chest height and holds it there, the steam thinning above the rim.
```
`seg103_prompt.txt` 第 20 行，原文：
```
Entry state, re-anchored to the reference images: 陆崇 (S15) still holds the tea cup at his chest, seated far behind the desk, the photograph in his other hand; 心腹 (S16) stands in the near half.
```
改为：
```
Entry state, re-anchored to the reference images: 陆崇 (S15) still holds the tea cup at his chest, seated far behind the desk, the photograph lying on the desk before him; 心腹 (S16) stands in the near half.
```
（`seg104`/`seg105`/`seg106` 的 Entry 已是"lying on the desk / lying open on the lacquer"，无需再改。）

### M2　陆崇外套颜色自相矛盾：`dark navy`（角色定义） vs `dark green`（同一段分镜 / 剧本）

- `seg95`–`seg106` **全部 12 段**的 `subject_definitions` 写着深藏青：
  > `<Subject 1> — 陆崇 (S15): … he wears a dark navy Chinese mandarin-collar front-buttoned jacket over a white mandarin-collar shirt, dark trousers and black cloth shoes …`
- 但 `seg95` 自己的 `[Shot 2]` 写深绿：
  > `[Shot 2] At 00:03.400, slow pull-back: 陆崇 (S15) sits far behind the desk, lean and straight-backed in a dark green high-collar jacket, …`
- 第①步 `文字剧本.md` 第 608 行亦为"一件**深墨绿**立领中式上衣"。

同一段提示词内两个颜色打架，H3 极易在不同镜头/不同段之间来回改色。

**应改成（`seg95`–`seg106` 的 `subject_definitions` `<Subject 1>`）：** 原文
```
he wears a dark navy Chinese mandarin-collar front-buttoned jacket over a white mandarin-collar shirt
```
改为
```
he wears a dark green (deep ink-green) Chinese mandarin-collar front-buttoned jacket over a white mandarin-collar shirt
```
并把 `seg95` `[Shot 2]` 的
```
lean and straight-backed in a dark green high-collar jacket
```
统一为
```
lean and straight-backed in a dark green mandarin-collar jacket
```

### M3　医院素材图的打光被当成"上午戏"的打光参考 —— 违反 15.8

2-3 是**第二天上午**（`文字剧本.md:462`），但成品提示词把**黄昏/下午**素材图标注为 "the exact location **and lighting** reference"：

- `seg68`/`seg70`/`seg71`/`seg72`/`seg73`/`seg74`/`seg75` 的 `<Picture …>`：
  > `an empty hospital corridor at dusk — … blue evening light at the far end … Use as the exact location and lighting reference.`
- `seg72`/`seg73`/`seg74`/`seg75` 的 `<Picture …>`：
  > `an empty cardiac ward room at 市一院 — … warm late-afternoon sun banding across the floor. Use as the exact location and lighting reference; …`

15.8 明确"夜间素材图不许当白天戏的打光参考"，须用 `ref_notes` 降级成 "location and prop reference only, **NOT for lighting**"。这里恰恰是反向写法。

**应改成（上述各段 `<Picture …>` 尾句）：** 原文
```
Use as the exact location and lighting reference.
```
改为
```
Use as the location and prop reference only, NOT for lighting — the scene is bright morning daylight.
```
（病房图同理；原文 `Use as the exact location and lighting reference; the room in it is empty and its contents are not copied.` → `Use as the location and prop reference only, NOT for lighting (the scene is bright morning daylight); the room in it is empty and its contents are not copied.`）

### M4　大厦名残留"万山大厦"（`文字剧本.md`）

本项目已定：她上班的大厦叫**景宸大厦**。`ep002_beats/scene23|24|25.json` 与成品提示词 `seg76`–`seg94` 均已正确使用"景宸大厦"，但第①步剧本仍残留两处：

**应改成：**
`ep002/文字剧本.md:85`，原文
```
### 0.4 万山大厦（场次 2-4）— 大堂 + 更衣间
```
改为
```
### 0.4 景宸大厦（场次 2-4）— 大堂 + 更衣间
```
`ep002/文字剧本.md:496`，原文
```
## 场次 2-4：内景 万山大厦 大堂／更衣间 上午
```
改为
```
## 场次 2-4：内景 景宸大厦 大堂／更衣间 上午
```

### B1（按规则判「中」）跨场次 2-3 → 2-4：`t87 → t90`（`seg75` → `seg76`）

- `seg75` 末拍：`she turns from the ward door and walks away from the lens back down the corridor, …`
- `seg76` Entry：`苏小满 (S1), in navy overalls … pushes the lobby's glass door open from outside and steps in.`
- 医院走廊 → 大厦大堂，人物位置/地点完全不同，属**硬切**，无中间过渡镜头。按审核口径判「中」（登记备查，不视为链式违规）。

### B2（按规则判「中」）跨场次 2-4 → 2-5：`t108 → t110`（`seg94` → `seg95`）

- `seg94` 末拍：`he bends, takes the blue bucket up in both hands … stands there facing the empty curtain without a word.`
- `seg95` Entry：`deep night in 陆崇's study; …`（且 `seg95` 为链组头，独立起链）。更衣间 → 深夜书房，硬切，判「中」（登记备查）。

---

## 低

### L1　`seg69`（t81）Entry 未承接 `seg68` 末拍的手部状态

- `seg68`（t80）末拍：`苏小满's (S1) fingers hover above it.`（手指悬在刚推回的单子上方）
- `seg69` Entry 只写 `苏小满 (S1) stands at the glass in the right half of frame`，手部状态丢失（位置一致，故降为低）。

**应改成（`seg69_prompt.txt` 第 20 行）：** 原文
```
Entry state, re-anchored to the reference images: the stamped slip lies on the ledge outside the window and 苏小满 (S1) stands at the glass in the right half of frame, with 收费员 (S17) behind the glass inside.
```
改为
```
Entry state, re-anchored to the reference images: the stamped slip lies on the ledge outside the window and 苏小满 (S1) stands at the glass in the right half of frame with her hand still lifted above the ledge, 收费员 (S17) behind the glass inside.
```

### L2　`seg70`（t82）`[Shot 2]` 写 "her shadow pools on the polished floor"，与"低阴影密度/不许压暗"略有张力

**应改成（`seg70_prompt.txt` 第 22 行）：** 原文
```
[Shot 2] At 00:04.000, closer: her right hand lowers the stamped slip to her side and her other hand hangs loose; the ceiling light falls straight down on her and her shadow pools on the polished floor under her feet.
```
改为
```
[Shot 2] At 00:04.000, closer: her right hand lowers the stamped slip to her side and her other hand hangs loose; the ceiling light falls straight down on her in a soft open pool on the polished floor, the shadow pale and full of detail.
```

### L3　`seg78`（t92 走廊段）挂 `lobby_1f`（大堂图）并标为 "exact location and lighting reference"

该段画面是**走廊**，却把大堂图当"精确地点＋打光"参考，会把大堂元素（前台、玻璃门光带）灌进走廊。

**应改成（`seg78_prompt.txt` 第 3 行尾句）：** 原文
```
Use as the exact location reference; the lobby in it is empty and its contents are not copied.
```
改为
```
Use only as a loose tone/tile reference for the same building, NOT as a location to copy; the corridor itself has no reference image.
```

### L4　`seg71`（t83）画面里出现缴费窗口，却未挂 `hospital_pay` 参考图

- `seg71` Entry：`… the cashier window behind her in the right of frame.`
- 但该段 refs 只有 `suxiaoman`、`hospital_corridor`，窗口无参考图，易与其他段的窗口造型不一致。

**应改成：** 给 `ep02_t83` 的 `refs` 补回缴费口图（或删去 Entry 中的窗口描述）。
- 方案 A：`scene23.json` 中 `ep02_t83` 的 `"refs"` 由 `["suxiaoman","hospital_corridor"]` 改为 `["suxiaoman","hospital_corridor","hospital_pay"]`。
- 方案 B（不挂图）：`seg71_prompt.txt` 第 18 行 Entry 末句 `the cashier window behind her in the right of frame.` 改为 `the corridor's right-hand wall behind her.`

### L5　2-5 STYLE 模板列举了书房里不存在的灯（吊灯/壁灯）

`seg95`–`seg106` 的 STYLE 段与曝光重锚段都写：
```
… the room is lit by its own real practical sources, all of them switched on and generous — the crystal chandelier, the table lamps and the wall sconces, or the green-shaded desk lamp and the floor lamp …
```
书房里只有台灯＋落地灯，吊灯/壁灯是大堂模板的残留，存在被误加进书房的低概率风险。

**应改成（仅保留书房实有灯）：** 原文
```
the crystal chandelier, the table lamps and the wall sconces, or the green-shaded desk lamp and the floor lamp
```
改为
```
the green-shaded desk lamp and the floor lamp
```
（曝光重锚段中 `the crystal chandelier and the table lamps and wall sconces in the hall, or the lit green-shaded desk lamp and the floor lamp in the study.` 同理简化为 `the lit green-shaded desk lamp and the floor lamp in the study.`）

---

## 已核对无问题项

1. **六段式完整性（第 1 条）**：`seg68`–`seg106` 全部 39 段均含 `subject_definitions / summary / retention_analysis / detailed_description / overall_soundscape / non_diegetic_music` 六段，无缺段（脚本逐段核验通过）。
2. **链式顺接（第 2 条，权重最高）**：逐组检查结果如下（组头 = seg68/71/74/77/80/83/86/89/92/95/98/101/104）：

| 组 | 组内第 2 段 ↔ 上一段末拍 | 组内第 3 段 ↔ 上一段末拍 |
|---|---|---|
| {68,69,70} | 69↔68 ✔（仅手部描述略松，见 L1） | 70↔69 ✔ |
| {71,72,73} | 72↔71 ✔ | 73↔72 ✔ |
| {74,75,76} | 75↔74 ✔ | 76↔75 **跨场次 t87→t90，判中（B1）** |
| {77,78,79} | 78↔77 ✔ | **79↔78 ✘（见 H1）** |
| {80,81,82} | 81↔80 ✔ | 82↔81 ✔ |
| {83,84,85} | 84↔83 ✔ | 85↔84 ✔ |
| {86,87,88} | 87↔86 ✔ | 88↔87 ✔ |
| {89,90,91} | 90↔89 ✔ | 91↔90 ✔ |
| {92,93,94} | 93↔92 ✔ | 94↔93 ✔ |
| {95,96,97} | 96↔95 ✔ | 97↔96 ✔ |
| {98,99,100} | 99↔98 ✔ | 100↔99 ✔ |
| {101,102,103} | 102↔101 ✔ | 103↔102 ✔ |
| {104,105,106} | 105↔104 ✔ | 106↔105 ✔ |

跨场次边界 2-4→2-5（t108→t110，`seg94`→`seg95`）已单列 B2。除 H1 一处组内硬跳与 B1/B2 两处规则内硬切外，其余 Entry 与上一段末拍**逐字/语义一致**。
3. **声景正向（第 3 条）**：`seg68`–`seg106` 39 段的 `overall_soundscape` **均无** silence / silent / mute / nothing at all / dead quiet / total hush / gone quiet / absolute quiet / almost nothing / nothing but / soundless / without sound 等否定式。全库检索命中的 `stays completely silent with a closed mouth` 仅存在于自动前置的 **SPEAKERS 段**（属"让非说话人闭嘴"的正向指令，不是声景否定式）。`seg100` 的 `one held breath` 属 15.7 允许的正向写法。
4. **不烧字幕（第 4 条）**：成品提示词**正文**无 subtitle / caption / lower-third / title card / text overlay / watermark / on-screen text；这些词只出现在自动前置的 `NO_TEXT` 段（"ABSOLUTELY NO SUBTITLES…AUDIO ONLY"），属正向禁止指令。beats 亦无。**台词无一被引号包裹**（`[Chinese] "…"` / `「…」` 检索均为 0）。**t110 照片**：`seg95` 只写照片的**画面内容**（`the top one showing 苏小满 sweeping … a worn red cord hanging out of her collar`），未写成"照片上印着字"；`<Picture 3>` 另注明 `the photographs in it are unreadable blanks`。
5. **参考图在场（第 5 条）**：2-3（`scene23.json`）**无** `qianjingli`/`afang`；2-4（`scene24.json`）**无** `waipo`/`luchong`/`xinfu`；2-5（`scene25.json`）**全部 12 段未挂 `suxiaoman`**（"苏小满"仅出现在 SPEAKERS 标签总表与 `seg95` 的照片内容描述中，未作为参考图）。另：`seg91`/`seg92` 在她离场后正确地下掉了 `suxiaoman`。
6. **空间锚点（第 6 条）**：
   - 2-3（`seg68`–`seg75`）：`the payment counter … set into the RIGHT-hand wall; the cardiology ward door … in the LEFT-hand wall; … 收费员 works INSIDE … 苏小满 stands OUTSIDE the glass … the counter and the ward door are NEVER laid out side by side.` ✔
   - 2-4（`seg76`–`seg94`）：`the L-shaped reception counter is mid-ground on the RIGHT … 苏小满 (S1) ALWAYS stays left of the aisle centre line, 钱经理 (S3) ALWAYS stays at the near end by the curtain; the three are NEVER lined up side by side.` ✔
   - 2-5（`seg95`–`seg106`）：`陆崇 (S15) sits behind the desk at the FAR side… 心腹 (S16) stands on the NEAR side… 陆崇 ALWAYS stays in the FAR half of frame and 心腹 ALWAYS in the NEAR half; the two are staged front-to-back across the desk… **NEVER side by side**.` ✔（明确禁止左右并排）
7. **大厦名（第 7 条）**：beats 三文件与 `seg76`–`seg94` 成品提示词**全部为"景宸大厦"**，无"万山大厦"（残留仅在 `文字剧本.md`，见 M4）。
8. **台词预算（第 8 条）**：`seg68`–`seg106` 无一段中文台词**超过 24 字**。最高为 `seg93`＝**24 字**（恰好在上限，三段分行：7/9/8 字，各行"字数/2.5＋起始 ≤ 10.0 s"均满足）；其后 `seg96`＝21、`seg101`＝21、`seg97`/`seg84` 等均低于上限。无超预算段。
9. **表演可见性（第 9 条）**：无"只有台词、没有任何可见动作/表情/目光/身体位移"的段。台词量最重的 `seg93`（t107）仍有 `[Shot 1] Close on 钱经理 (S3), one hand cupped beside his mouth, his voice kept low, his eyes flicking toward the curtain` 作为可见表演。
10. **画面偏黑风险（第 10 条）**：分镜**正文与 Entry** 内无 `pitch dark` / `in darkness` / `dimly lit` / `murky` / `unlit`/ `low-key` 等硬压暗描述。正文中出现的 `the dark lacquer`（seg95 桌面色）、`a dark waistcoat`（seg82 服装色）、`a dark green … jacket`（服装色）均为物体/服装固有色，不构成压暗。STYLE 段与曝光重锚段中的 `not murky` / `never moody` / `Absolutely NOT dark` 是**否定式保护**（正向要求），不构成问题。2-5 另用夜景增强段 `It is night indoors, but lit like a bright soft-spoken commercial … all of them switched on and generous` 做正向曝光锚定。

---

*报告结束。本报告只审不改，未改动任何 beats / 提示词。*
