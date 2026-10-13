# 第四轮复核 A（seg14–seg81）

## 结论：不通过（12 条待修）

核对依据：`minimax-h3-prompt-audio/SKILL.md`、`AGENTS.md` 15.1 / 15.5 / 15.6，以及本轮 ANCHOR_12 站位规则。
场景空间锚点：门在 LEFT，百叶窗+高柜在 RIGHT，深色木桌横贯房间中部；苏小满（S1）恒定在桌子**近侧**、背朝门；钱经理（S3）本该恒定在桌子**远侧**（远离门、背窗），全片只离桌一次（掏兜，seg18）。

---

## 待修清单

| # | seg | 严重度 | 问题 | 应改成 |
|---|---|---|---|---|
| 1 | seg42 | 高 | **违反 ANCHOR_12「只离桌一次」。** Entry 里钱经理还在远侧，Shot 1 却写他 `comes out from behind the desk, crosses the few steps to 周总监 … stops at his LEFT shoulder`——这是掏兜（seg18）之后的**第二次离开远侧**，且一直停在靠近门的房间中部（seg43 还在他左肩旁）。规则要求：苏小满离场（seg75）之前，钱经理绝不允许出现在房间中部。 | 让钱经理**始终留在桌子远侧不动**，改成周总监自己走到桌边（钱经理隔着桌子汇报）。Shot 1 直接替换为：<br>`[Shot 1] Medium: 钱经理 (S3) does not leave the far side of the desk — he stays planted behind it, one hand flat on the wood, turns his shoulders toward the door, ducks his head at 周总监 (S6) in an ingratiating bow and speaks across the room; 周总监 (S6) begins walking in toward the desk.`<br>同时把 Entry 里 `钱经理 (S3) comes out from behind the desk…` 删除，改为 `钱经理 (S3) stays on the FAR side of the desk.` |
| 2 | seg43 | 中 | 承接 seg42 的错误：Entry `钱经理 (S3) stands at 周总监's (S6) LEFT shoulder holding the card up` + Shot 1 `钱经理 trails a step behind him and stops in his shadow`，把他继续留在离桌的中部。 | Entry/Shot 1 改为钱经理守在远侧、由周总监走到桌上取卡：<br>`Entry: …钱经理 (S3) stands on the FAR side of the desk holding the card up; 苏小满 (S1) on the near side…`<br>`[Shot 1] Medium: 周总监 (S6) crosses to the desk and takes the card out of 钱经理's (S3) hand as he goes; 钱经理 (S3) stays where he is on the FAR side of the desk and does not follow.` |
| 3 | seg20 | 中 | **违反「对折的纸单从不停留在桌面上」。** Shot 2 写她把对折纸单抽出来 `laying it flat; the fold opens under her palm`——纸单被摊平放到桌面上了，与「一直在她兜里或手里」矛盾（且与 seg73「since she snatched it back」的设定打架）。 | 让纸单全程不离手：<br>`[Shot 2] At 00:03.000, extreme close-up on her hand drawing a single folded paper form halfway out of her pocket and holding it cupped in her palm, still folded.`<br>`[Shot 3] At 00:05.600, a man from the doorway puts his head and shoulder into frame from the LEFT and leans in toward her hand; 苏小满 (S1) closes her hand over the form and shoves it straight back down into her pocket in one quick movement, and the man straightens up again.` |
| 4 | seg41→42 | 中 | **黑卡凭空从桌面跳到他手里。** seg40 结尾卡在桌面（`The card on the desk`），seg41 全程未提卡，seg42 Shot 3 钱经理却 `lifts the black card up between them`——拾卡动作没有交代。 | 在 seg41 结尾补一个明确动作，或在 seg42 补上：<br>`[Shot 4] … As the crowd shuffles apart, 钱经理 (S3) picks the black card up off the desk and closes it in his fist.` |
| 5 | seg14 | 中 | **桌面道具与「桌面开场是空的」冲突，且道具凭空消失。** Shot 2 `the desk lamp jumps and the white enamel mug rocks on the bare desktop` 把台灯和搪瓷缸放上了桌；但 seg20 Entry 又写 `The desk surface carries nothing yet — it is a bare dark-topped desktop`，之后这两件道具**再未出现**（seg79/81 的桌面只剩灰尘印）。 | 二选一：① 删掉台灯/搪瓷缸，与「开场空桌」对齐——Shot 2 末改为 `…slams his open palm flat onto the desktop; the bare dark desktop carries nothing but his palm.`；② 若保留它们作为固定陈设，则 seg20/49/73/79/81 都要一致提及（`the enamel mug and the desk lamp still on the far corner`），不能只在 seg14 出现一次。 |
| 6 | seg65 | 中 | **钱经理朝房间中部迈步。** Shot 2 `he takes one step toward 小罗 (S7)`，而 小罗 正站在房间中部——钱经理离开远侧走向中部，违反「苏小满没离场前不得出现在房间中部」。seg66 Entry `钱经理 has stopped beside the chair` 也未把他拉回远侧。 | 起身但脚不离远侧：<br>`[Shot 2] At 00:06.200, wide: 钱经理 (S3) gets the rest of the way out of the chair so fast that its metal legs shriek across the tile, but he stops dead at the far edge of the desk and does not leave it, both hands coming up and his mouth already open.`<br>seg66 Entry 相应改为 `钱经理 (S3) is still at the far side of the desk beside his chair.` |
| 7 | seg76 | 低 | Entry `钱经理 (S3) is left standing in the middle-left of the room where 苏小满 (S1) walked past him, a few steps away from the desk`——既与 seg74 的「still on the far side」无动作衔接地跳变，措辞又暗示他在苏小满**还在离场时**就已站到中部（落在规则禁区内）。 | 明确她走完他才动，且先守在桌边：<br>`钱经理 (S3) is still at the far side of the desk where he leaned to watch her go, a few steps from the desk; the room is emptying.`（他移动到中部只能发生在 seg75 她完全出门之后。） |
| 8 | seg17 | 低 | Shot 3 `钱经理 (S3) motionless in the middle background` 措辞可被读成「房间中部」，与他的远侧锚点不符；同句 `the two women at either end of the room's axis with the desk between them` 方位含混，易被渲染成左右并排的横屏双人。 | 明确纵深前后排 + 把他钉回远侧：<br>`[Shot 3] At 00:08.600, wide: the two women staged one behind the other along the room's depth axis — 小唐 (S4) nearer the door, 苏小满 (S1) nearer the desk — with 钱经理 (S3) motionless behind the desk, back to the window, watching them like a spectator, arms folded.` |
| 9 | seg14 | 低 | 首句残缺：`ce images exactly — bright, clean, warm daylight…`，句首被截断，Entry state 不完整（疑似 dump 截断）。 | 补全为完整句：`Match the reference images exactly — bright, clean, warm daylight, luminous skin, open shadows.` |
| 10 | seg63 | 低 | Shot 2 `four men in dark tailored suits follow him and fan out into a loose line against the LEFT wall`——`fan out into a line` 可被读成横向一字排开，违反 9:16 竖屏的纵深调度要求。（seg70 `standing in a line along the LEFT wall` 同理，需一并收紧。） | 改为沿墙纵深错位排布：<br>`…four men in dark tailored suits follow him and take up a staggered line along the LEFT wall, one behind another, receding into the depth of frame.`<br>seg70 Shot 2 改为 `four men in dark suits standing one behind another along the LEFT wall, receding down the room, the office motionless behind them.` |
| 11 | seg45/48/49/53/55/57 | 低 | 这些段的 Entry state **漏写钱经理（S3）**，而相邻段（seg44/46/50/54/58）他都在场，属连续性交代缺口，容易让 H3 把他从画面上抹掉。 | 每段 Entry 补一句：`钱经理 (S3) stands on the FAR side of the desk, back to the window, saying nothing.` |
| 12 | seg81 | 低 | Shot 3 `the pen tray` 是**全片首次出现**（前 67 段从未建立此物），属「凭空出现」的道具。 | 删除或复用已有物件：`[Shot 3] At 00:05.800, insert on the desk: the scuff marks in the dust and the empty space where the black card lay.` |

---

## 已确认正确的要点

- **A 站位顺接（主体无误）：** 除上表 #1/#2/#6/#7 外，逐段比对 68 段的 `[Shot]` 结尾与下一段 Entry state，苏小满（S1）、钱经理（S3）、小唐（S4）、周总监（S6）的方位均能对上，未发现画面跳变。
- **苏小满（S1）零漂移：** 全片恒定在桌子**近侧**、背朝门，从未换位（seg14→seg74）；seg74 才转身走向 LEFT 门，seg75 穿过门框离场，符合「她离场前」的规则窗口。
- **ANCHOR_12 主链路正确：** seg18「掏兜」是唯一一次离桌（绕到近侧）；seg19–22 在近侧经过「心虚/摆上桌/还有/黑卡」；seg23「拿来」把卡交给钱经理后 **Shot 5 立即绕回远侧**；seg24–seg41、seg44–seg64、seg67–seg74、seg77–seg80 均恒定在远侧（seg68 还显式写明 `stays on the far side`）。
- **黑卡连续性（除 #4 外完整）：** seg22 出兜 → seg23 交钱经理 → seg32 拍上桌 → seg34 拾起 → seg35 放桌 → seg43 转周总监 → seg51 拾起 → seg58 放回桌 → seg66 小罗拾起 → seg69 放桌 → seg73 入兜，段段接得上，转手节点有交代。
- **钥匙 / 圆珠笔：** seg20 由苏小满自己摆上桌 → seg21/31/49/58 一直在桌 → seg73 收进兜，无凭空消失。
- **手机：** seg51 从兜掏出 → seg52 放桌免提 → seg58 拾起关屏放回兜，闭环完整。
- **D 台词引号：** 全部台词均为 `[Chinese] …` 后直接写原文，**全片无任何引号包裹**（`"…"`、`「」`、`''` 均未命中），不会触发 H3 烧字幕。
- **E 声景反向词：** 所有 `overall_soundscape` 均未出现 `silence / silent / no dialogue / without sound / mute / no intelligible`。（`She is silent`、`Nobody else speaks` 等只出现在 `[Shot]` 表演描述里，属 H3 要求的「明说其他人闭嘴」，是**正确**写法，不算错。）
- **G 画面文字：** 全片未出现 `subtitle / caption / lower-third / title card / text overlay / watermark / 字幕` 等词。
- **F 竖屏调度：** 绝大多数镜头用「前后交叠 / 过肩 / 前景压边」纵深调度，未发现「一排人横向铺开」的调度（仅 #10 两处措辞需收紧）。
- **non_diegetic_music：** 每段均有值（配乐或 `N/A`），无留空，不会让 H3 乱加配乐。

---

*仅生成本报告，未修改 `_dump_scene12.txt` 或其他任何文件。*
