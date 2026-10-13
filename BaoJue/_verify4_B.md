# 第四轮复核 B（seg105–seg129）

## 结论：不通过（7 条待修：专项 1 条 + 通用 6 条）

核对依据：`minimax-h3-prompt-audio/SKILL.md`、`AGENTS.md` 15.1（竖屏/不许横排）、15.5（9:16 画幅）、15.6（不许烧字幕），以及 `_dump_anchors.txt` 的 `ANCHOR 1-4`（即本轮所称 ANCHOR_14）、`ANCHOR 1-5`、`SPEAKERS`。
被审文件：`_dump_scene14b15.txt`（seg105–seg129，25 段：Entry / [Shot n] / overall_soundscape / non_diegetic_music / [REFS]）。
专项 #3（seg96–98）**不在本 dump 内**，按 `ep001_segs/seg96|97|98_prompt.txt` 与 `_patch_beats6.py` 的原始改法一并核对。

---

## 上述 6 条专项整改的复核结果

| # | seg | 结论(FIXED/PARTIAL/未修) | 现状摘录 |
|---|---|---|---|
| 1 | seg108 / seg110 | **FIXED** | seg108 `[REFS] suxiaoman / xiaoluo / lobby_1f / building_exterior`；seg110 `[REFS] suxiaoman / xiaoluo / lobby_1f`。两段正文均无钱经理，参考图也已不含 `qianjingli` ✓（台词/镜头里也无 S3） |
| 2 | seg109 / seg112 | **FIXED** | seg109 与 seg112 `[REFS]` 均为 `suxiaoman / xiaoluo / lobby_1f / building_exterior`，**无任何 office_\* 场景图** ✓（大堂戏只用 lobby_1f + building_exterior） |
| 3a | seg96 | **FIXED** | Entry：`钱经理 (S3) is on the near side of the desk, just in from the doorway, with the resignation form still in his hand` → 张总进门瞬间他仍在**近侧** ✓ 与 ANCHOR_14 一致 |
| 3b | seg97 | **FIXED** | Entry：`钱经理 (S3) is a step in front of him on the door side with one hand still outstretched` → 站在张总**身前一步（近侧）** ✓ |
| 3c | seg98 | **PARTIAL** | Entry：`钱经理 (S3) has backed half a step away toward the far side of the desk` —— 只"朝远侧退了半步"，**尚未到达远侧**；用户期望是"已退回远侧"。且下一段 seg99 仍写 `stands half a step back from the desk`，到 seg100 才 `on the far side`。**退位动作被拆到三段里，seg98 未到位** |
| 4 | seg114 | **FIXED** | Entry 已改为 `苏小满 (S1) already out on the paving a few paces clear of the doors…; the beat opens on one short cutaway back inside, then stays outside.`；Shot 2 已改为 `outside on the forecourt: …walks the last few paces further out into the open middle of the paving`。**无第二次"走出大楼"、状态=已站在楼外铺地** ✓（原 Entry 里的"ground-floor lobby looking back toward the lift bank"回望镜头已删）<br>⚠ 括号注：删镜头没删干净——`[REFS]` 仍带 `lobby_1f`（见通用 #6） |
| 5 | seg117 | **FIXED** | Shot 4：`the car pulls away from the kerb into the late-afternoon light with its tail lights coming on`；本段 exposure 句为日戏锚点 `bright, clean, warm daylight`；全文 grep `dusk / blue hour / twilight / golden hour` **零命中** ✓ 与同场 seg105–116 的日戏锚点一致 |
| 6 | seg117 | **FIXED** | Shot 2：`close on 小罗 (S7) as he finishes what he started, still quietly and only for her, in exactly the same voice and at the same pace as the line before: [Chinese] 陆总要谈的事，还是三天前那件。` —— 跨镜头（承 seg116 同一说话人 S7）台词已带 **same voice and pace** 衔接说明 ✓ |

---

## 通用项待修清单

| # | seg | 严重度 | 问题 | 应改成 |
|---|---|---|---|---|
| 1 | seg98 | **中** | 承专项 #3c：钱经理在 seg98 仍只"退了半步"，未落到桌子远侧，与 ANCHOR_14「张总进门后即退到远侧并此后一直留在远侧」不符。 | Entry 改为：`张总 (S10) stands at the desk with one hand flat on it; 钱经理 (S3) has retreated to the far side of the desk and stands behind it; 苏小满 (S1) is still in the LEFT doorway with the cardboard box in her arms.`（seg99 Entry 同步改为 `钱经理 (S3) stands on the FAR side of the desk, back to the window;`） |
| 2 | seg117 | **中** | 参考图与曝光锚点自相打架：`[REFS]` 带 `car_interior`，而该资产是**夜间车厢**，本段 `detailed_description` 里 `<Picture 3>: the rear cabin of a black executive sedan **at night** … Use as the exact location **and lighting** reference`，却同时套用日戏锚点 `bright, clean, warm daylight` / `late-afternoon light`。恰好又把"blue dusk"改成了日戏，等于让 H3 拿夜间图当"打光参考"，会拉暗本段。 | 在 seg117 提示词里把该图降为"仅位置/道具参考"并去掉"at night"的照明绑定：`<Picture 3>: the rear cabin of a black executive sedan, seen from the front seats looking back — a wide pale-grey leather rear bench, a central armrest, chrome door handles, amber courtesy lamps along the roof lining, tinted windows. Use as the location and prop reference only, NOT for lighting; the light through the open rear door is bright late-afternoon daylight.` |
| 3 | seg108 | **低** | Entry 与首镜时序不一致：Entry 写 `小罗 (S7) and a file of eight suited men are **already crossing** the ground-floor lobby…`，但 Shot 1–2 还在演楼外汽车依次停靠、开门下人（人尚未进大堂）。Entry 应=首镜起始状态。 | Entry 该句改为：`小罗 (S7) and a file of eight suited men are just getting out of the cars at the kerb outside and will come in across the ground-floor lobby from the glass doors on the LEFT…` |
| 4 | seg119 / seg121 | **低** | `overall_soundscape` 命中反向词族 **mute**，有压人声风险：seg119 `city traffic muted through the glass`；seg121 `muted street traffic`。 | 去掉 muted：seg119 → `low city traffic through the glass`；seg121 → `low street traffic`。 |
| 5 | seg111 / seg126 / seg128 | **低** | 声景写法逼近"无声音"的反向要求（未用关键词，但同样可能把人声压掉）：seg111 `a lobby in which nothing at all is making a sound except the air handling`；seg126 `the bright city noise drops away to nothing on the cut`；seg128 `Almost nothing but damp night air…`。 | 改为"只剩某物可闻"的正向写法：seg111 → `a lobby where only the air handling is audible`；seg126 → `the main-road hum thins out behind them on the cut`；seg128 → `Damp night air, the lantern's paper creaking, a distant car, one long breath close to the mic.` |
| 6 | seg114 / seg115 | **低** | 参考图残留：删掉了"大堂回望"镜头，但 `[REFS]` 仍挂 `lobby_1f`（seg114 `<Picture 4>`、seg115 `<Picture 4>` 仍定义为地下一层大堂"exact location reference"），而这两段的镜头里**没有任何大堂画面**（seg114＝三楼办公室门口+楼外；seg115＝纯楼外）。既属 #4 的删尾，也会给 H3 灌入无关的大堂元素。 | seg114：`sc_lobby_1f.png` → 换成三楼办公室/走廊资产（如 `sc_office_left.png`，对应 Shot 1 的"办公室门框/走廊"）；seg115：删掉 `sc_lobby_1f.png`，保留 `sc_building_exterior.png`。（对照：seg108/109/110/111/112/113 用 `lobby_1f` 是正确的，因它们确有室内大堂镜头） |
| 7 | seg109 / seg112 / seg116 | **低** | 跨镜头台词（同一说话人跨两个镜头）**缺 same voice and pace 衔接说明**：seg109 S7（Shot2 `苏小姐。又见面了。`→Shot3 `今天的事，陆总都知道。`，仅写 `adds the second half`）；seg112 S1（Shot1 `昨天，他们要搜我的兜。`→Shot2 `今天，他们要签单走人。`，仅写 `goes on without pausing`）；seg116 S7（Shot1 `上车说。`→Shot2 `您外婆在市一院，八楼。`，仅写 `goes on`）。只有 seg117 写了 same voice and pace。 | 给这三处补上：Shot 前加 `in the same voice and at the same pace, ` 再跟 `[Chinese] …`。 |

---

## 已确认正确的要点

- **专项 #1/#2 参考图已彻底纠正**：seg108/110 不含 `qianjingli`（钱经理不在场）；seg109/112 不含 `office_*`。经 `job108/109/110/112.json` 双向核对一致。
- **B 台词引号**：全片台词一律 `[Chinese] …` 后直接写原文，grep `"`、`「」`、`''`、`""` **零命中**，不会触发 H3 烧字幕。
- **C 反向词（soundscape 段内）**：除 #4 的 `muted` 外，无 `silence / silent / no dialogue / without sound / no intelligible`。seg115 的 `She is silent, waiting for the answer.` 出现在 `[Shot]` 表演描述里（该段 Shot 4 她无台词），属 H3 要求的"明说其他人闭嘴"，**正确、不算错**。
- **E 画面文字**：grep `subtitle / caption / lower-third / title card / text overlay / watermark / 字幕` **零命中**。
- **D 竖屏调度**：seg109 群像按要求写成 `the men behind him stop in the same instant and close up one behind another in file at his back, stacked in depth.` —— **纵队列成立** ✓。其余镜头多为"前后交叠/过肩/前景压边"。仅 seg108 Shot 1 的"一排车沿路缘"属道具（车）成排，非人员横排，可接受。
- **F 新场次入场**：seg108 Entry 交代了"从电梯下来"（`inside the lift coming down`）；seg114 `already out on the paving`（跨玻璃在前段完成）；seg118 `much later that night…has been in the car since it left the tower`；seg126 由"车驶入巷子"带出朱漆大门；seg105 承接办公室既有站位。**无凭空出现**。
- **A 站位/道具顺接（主体无误）**：逐段比对 25 段的 [Shot] 收尾与下一段 Entry，苏小满（S1）恒持纸箱（seg106 放下→seg106 末回交→seg107 抱起→seg117 放入座位→seg118 起置于膝上→seg126 抱出→seg127–129 抱在怀里），钱经理到 seg105 仍守桌子远侧，陆蔓（S8）seg117 首现后恒定 LEFT 后座且 seg126 不下车，小罗（S7）seg126 在门前复现——均能接上，未见画面跳变。
- **non_diegetic_music**：25 段全部有值（配乐或 `N/A`），无留空。

---

*仅生成本报告，未修改 `_dump_scene14b15.txt` 或任何其他文件。*
