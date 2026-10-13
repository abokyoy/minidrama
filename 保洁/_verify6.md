# 第六轮复核（seg82–seg104）

## 结论：不通过（16 条待修：高 3 / 中 5 / 低 8）

**本轮关键前提（链组划分）**：`gen_worker.py` 中 `GROUP = 3`，链式只存在于组内——
临床：`(82,83,84) (85,86,87) (88,89,90)`，办公：`(91,92,93) (94,95,96) (97,98,99) (100,101,102) (103,104,105)`。
所以**组内相邻对**（82→83、83→84、85→86、86→87、88→89、89→90、91→92、92→93、94→95、95→96、97→98、98→99、100→101、101→102、103→104、104→105）的 Entry 必须等于上一段尾帧（否则第一帧跳变，判高）；
**跨组相邻对**（84→85、87→88、90→91、93→94、96→97、99→100、102→103）组头用 `WF_FIXED` 另起首帧、不继承尾帧，但观众仍会看到前后不连贯，判中。
以下逐条据此定级。

---

## 待修清单

| # | seg | 严重度 | 问题 | 应改成（可直接替换的英文原文） |
|---|---|---|---|---|
| 1 | 83→84 | **高** | 组内链式跳变：seg83 尾帧是"两人都在走廊"（Shot 3 `At 00:09.400, wide down the corridor: the two of them standing…`），但 seg84 Entry 写 `苏小满 is alone in the corridor` —— 医生 S11 凭空消失；且手上的对折纸单从 seg83 的 `in her fist` 直接变成 Entry 里的 `in her trouser pocket`，道具也跳变。 | Entry 改为：`Entry state, re-anchored to the reference images: 苏小满 (S1) stands in the corridor facing the ward door on the RIGHT with the folded form closed in her fist; 医生 (S11) is still beside her and is already turning back toward the ward door; the bench and the wall are on the LEFT.`<br>[Shot 1] 改为：`[Shot 1] Medium: 医生 (S11) goes back in through the ward door on the RIGHT and it settles shut behind him; 苏小满 (S1) crosses to the LEFT wall, pushes the folded form down into her trouser pocket on the way, lets her back settle against the wall just beside the bench, takes out her phone and dials with her thumb, holding the screen up close.` |
| 2 | 91→92 | **高** | 组内链式跳变：seg91 通篇 `the office is spotless and empty of anybody else`（Shot 1–4 无人），而 seg92 Entry 第一帧就是 `钱经理 (S3) is leaning against the doorframe on the LEFT, arms crossed` —— 钱经理凭空出现在首帧。※不能改 seg92 加"进场"镜头：92 三句台词 12+5+9=26 字≈10.4 s，本身就是满的，没有位置再塞一个进场拍。**须在 seg91 结尾给他一个可见的入场**。 | seg91：`[REFS]` 末尾加 `qianjingli`（并补对应 `<Subject>` 描述）；Entry 里 `the office is spotless and empty of anybody else` 改为 `the office is spotless and empty of anybody else at the top of the beat`；在 `[Shot 4]` 之后新增：`[Shot 5] At 00:09.200, rack focus off the box onto the open LEFT door: 钱经理 (S3) now stands in the doorway with his arms crossed, a shoulder against the doorframe, watching her. Nobody speaks in this whole beat.` |
| 3 | 98 | **高** | 声景否定写法：`then a very quiet room with only breathing in it` —— `only … in it` 等同于禁用清单里的 `nothing but …`，会把整段（含 Shot 1 的吼声与"说咱们公司…"台词）人声一起压掉。 | `overall_soundscape` 改为：`Loud indignant shouting, a hand slapping the desk, then the room left holding its breath under the ceiling lights.` |
| 4 | 94（连带 95） | 中 | 位置/几何自相矛盾：94 Entry 写 `苏小满 stands one step inside the LEFT doorway`，但同一段 Shot 2/3 是 `the pen lying on the desk behind her` / `reaches back across the desk toward the pen` —— 桌子在"房间正中"，站在门口够不到桌对侧的笔。且 seg93 结尾她还在桌边（Shot 4 `the box still in her arms` 于桌近侧），93→94 属跨组，观众会看到她从桌边"瞬移"到门口。固定空间规则本就规定 `苏小满 always on the NEAR side of the desk with her back to the LEFT door`。 | 94 Entry 改为：`Entry state, re-anchored to the reference image: 苏小满 (S1) stands on the NEAR side of the desk with her back to the LEFT door, the cardboard box in her arms; 钱经理 (S3) stands in the doorway in front of her, holding the printed resignation form out toward her; the corridor is visible beyond the door.`<br>95 Entry 第三句相应改为：`苏小满 (S1) stands on the NEAR side of the desk with the cardboard box on one hip and her right hand still back over the desk;` |
| 5 | 100 | 中 | 参考图漏挂在场人物：Shot 4 `wide and held` 明确含 `苏小满 (S1) watches all of it from the LEFT doorway`，但 `[REFS]` 只有 `zhangzong / qianjingli / office_mid / office_pano`，没有 suxiaoman → 画面里的人没有参考脸，会被画错。 | `[REFS]` 加入 `suxiaoman`：`[REFS] zhangzong / qianjingli / suxiaoman / office_mid`（并补 `<Subject>`）。 |
| 6 | 101 | 中 | 参考图漏挂在场人物：Shot 4 `hold on the two of them in the doorway with 钱经理 (S3) small in the background`，钱经理在画面里，但 `[REFS]` 只有 `zhangzong / suxiaoman / office_mid / office_pano`，没有 qianjingli → 背景人物会被画错。 | `[REFS]` 加入 `qianjingli`：`[REFS] zhangzong / suxiaoman / qianjingli / office_mid`（并补 `<Subject>`）。 |
| 7 | 88 | 中 | 声景否定写法：`and then the room seems to go quieter` —— 同禁用清单的 `gone quiet`，属"声音变小/消失"的否定式，可压掉"值不值，我说了算"这句人声。 | `overall_soundscape` 改为：`A light warm voice, the quilt rustling, the oxygen mask hissing, the monitor beeping, and under it only the ceiling lights and the window.` |
| 8 | 89 | 中 | 声景否定写法：`a pause with nothing in it` —— `nothing in it` 属否定式（近 `nothing at all`），有压人声风险。 | `overall_soundscape` 改为：`A faint slow voice, the room holding its breath, then a low urgent question, the oxygen hissing, the monitor beeping steadily.` |
| 9 | 91 | 低 | 声景措辞：`A quiet office in the afternoon:` 属"整间房安静"的旧写法；本段已列出 `the ceiling lights, the wall clock, distant corridor footsteps…`，前半句是冗余且略带否定。 | `overall_soundscape` 改为：`The office in the afternoon: the ceiling lights, the wall clock, distant corridor footsteps, a computer fan, the papery click of a book being set down.` |
| 10 | 101 | 低 | 声景措辞：`one soft careful voice in the sudden quiet` —— `the sudden quiet` 系房间级"变静"描述，可收紧为正向。 | 末句改为：`… slow careful footsteps across tile, one soft careful voice coming through the room.` |
| 11 | 102 | 低 | 声景措辞：`the office very quiet around it` —— 房间级 quiet（近 `dead quiet`），建议改正向。 | 末句改为：`… a shuffling half bow, then only the clock and the lights.` |
| 12 | 85 / 86 / 94 | 低 | `summary` 以 `Silent beat:` 开头（三段均无台词）。summary 也是 H3 输入，`Silent` 可能连带压掉环境声。 | 三段 summary 的 `Silent beat:` 统一改为 `Wordless beat:`。 |
| 13 | 99 | 低 | 道具归因错：Entry 写 `the blank resignation sheet 张总 (S10) threw down is lying face up on the desktop`，但这张辞工单是 **seg96 Shot 1 钱经理 `drops the form onto the desk`** 丢下的（97 张总只是戳桌）。 | Entry 改为：`…; the blank resignation sheet 钱经理 (S3) dropped on the desktop earlier is lying face up on it.` |
| 14 | 101 | 低 | Entry 出现无来源动作：`holding the cardboard box, half turned to leave` —— seg100 尾帧她只是 `watches all of it … without a flicker`，没有任何转身准备走的动作；101 又是链内的下一段，首帧必须等于 100 尾帧。 | 101 Entry 前半改为：`Entry state, re-anchored to the reference image: 苏小满 (S1) stands in the LEFT doorway of the office holding the cardboard box; 张总 (S10) is at the desk in the middle of the room; 钱经理 (S3) is behind the desk.`（删去 `half turned to leave`；若确要她准备走，须在 seg100 给她一个可见的移重心动作） |
| 15 | 83 / 84 / 86 / 87 | 低 | 场景参考图越挂（15.8）：83/84/86 的镜头全在走廊，病房内景未入画，却挂了 `hospital_ward`；87 全在病房内，走廊未入画，却挂了 `hospital_corridor`（82 因病房门口暖光入画可保留 ward）。 | 83/84/86 的 `[REFS]` 删去 `hospital_ward`；87 的 `[REFS]` 删去 `hospital_corridor`。 |
| 16 | 92 / 93 / 100 | 低 | （观察项）台词时间窗虽均 ≤10.0 s，但**相邻句起点早于上一句终点**，存在重叠：seg92 首句 12 字≈4.8 s（0→4.8），次句却 `At 00:04.000`（重叠约 0.8 s）；seg93 次句 10 字≈4.0 s（3.6→7.6），三句 `At 00:07.000`（重叠约 0.6 s）；seg100 次句 7 字≈2.8 s（2.4→5.2），三句 `At 00:04.200`（重叠约 1.0 s）。按 2.5 字/秒会撞词。 | 在不改台词的前提下：seg92 Shot 2 起点后移至 `At 00:05.000`、Shot 3 后移至 `At 00:07.200`（92 三句合计 ≈10.4 s 已超时长，需换段处理）；seg93 Shot 3 后移至 `At 00:08.000`；seg100 Shot 3 后移至 `At 00:05.400`。若实际语速快于 2.5 字/秒可忽略。 |

---

## 已确认正确的要点

1. **竖屏 9:16**：seg82–104 全部 23 段都含 `VERTICAL 9:16 PORTRAIT FRAME` 样板，且含 `stage the action in DEPTH, front-to-back, and never spread people out left-to-right` / `upper two thirds of the frame` / `one strong foreground element along the bottom edge`；正文调度均为纵深/过肩（如 seg98 Shot 2 三人按"门侧—桌前—门口"纵深排布），无"一字排开一排人"。
2. **零字幕**：23 段全部含 `ABSOLUTELY NO SUBTITLES, NO CAPTIONS, NO LOWER-THIRDS, NO TITLE CARDS, NO WATERMARKS … Any spoken line is AUDIO ONLY`；正文无 `subtitle / caption / lower-third / title card / text overlay / watermark / 字幕` 类词。表单/书封的印刷字属"真实物品上的字"，合规。
3. **台词无引号**：seg82–104 全文不含 `"` `"` `"` `「` `」`，所有台词都是 `[Chinese] 原文`，不会被烧成字幕。
4. **台词时间窗**：全部 20 句均满足 `起始 + 字数/2.5 ≤ 10.0`。最紧的三处 seg92 Shot 3（6.4+3.6=10.0）、seg97 Shot 2（3.4+6.4=9.8）、seg82 Shot 2（1.6+8.0=9.6）都符合。
5. **医院傍晚曝光**：seg82–90 曝光锚点均为 `dusk, but still bright and clean … the ceiling fluorescents clearly on`；VERTICAL 段均为 `Late-afternoon dusk … must still read BRIGHT … no murky corners`，**没有**正午日光措辞（`glowing natural window light` 仅出现在办公室段 91–104，办公戏为日戏，正确）。病房参考图自述 `warm late-afternoon sun banding across the floor`，与 dusk 一致。
6. **参考图人物在场性（15.8）**：医院段只挂在场者——外婆仅出现在 87–90、医生仅出现在 82–83；办公室段钱经理自 92、张总自 95 才挂；seg97/99 未挂不在画面的苏小满，处理正确。（唯 100/101 漏挂，见待修 5、6。）
7. **纸箱传递连贯**：seg91 在桌上（`sits on the desk`）→ seg93 Shot 1 她 `lifts the box to her chest` → seg94–104 全程抱在怀里 / 挎胯，链内没有凭空出现或消失。
8. **链式顺接已修好的关键点**：seg97→98 已按 15.9 修正——98 Entry 写 `钱经理 is still on the door side of the desk, half a step in front of where 张总 left him`，并在 Shot 2 才给他可见的"绕桌退回远侧"。其余逐拍对得上的链内对：82→83、85→86、86→87（`walks toward the ward door` → `in the ward doorway and steps in`）、88→89（bent over 床边 + 红绳）、89→90、92→93、94→95（box on hip + right hand still back over the desk）、95→96、97→98、98→99、100→101、101→102、103→104、104→105。
9. **新场次入场（G）**：seg82 为医院首段，医生 S11 是**从病房门内走出**（`comes out through the ward door`）建立，非凭空；苏小满作为主角在场景开始时已立于走廊，属正常场次开场。seg91 为"新的一天、同一办公室"，她在桌边打包，亦属正常开场。（seg92 钱经理的凭空出现见待修 2。）
10. **声景其余均正向**：除待修列的 3/7/8/9/10/11 外，seg82/83/84/85/86/87/90/92/93/94/95/96/97/99/100/103/104 都是"列具体可听之声"的正向写法（如 seg90 `then the corridor's fluorescent hum swallowing everything`、seg104 `a stillness with real weight in it, the clock and the lights`）。
11. **防抢台词的"闭嘴"样板不是声景问题**：`Anyone not given a numbered line stays completely silent with a closed mouth.` 是全剧统一的角色行为约束（防止无关角色乱说话），不属 `overall_soundscape` 否定写法，应保留。
