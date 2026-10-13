# ep002 场次 2-1 / 2-2 审核报告

> 审核对象：`ep002_beats/scene21.json`(t01–t14)、`scene22.json`(t20–t72)，以及渲染成品 `ep002_segs/seg01–seg67_prompt.txt`。
> 判定依据：`minimax-h3-prompt-audio`、`minimax-h3-chained-segment-drift` 两技能判据 + `AGENTS.md` 十五/十六章硬性规则。
> 抽读成品：seg01/03/05/07/12/14/15/18/21/29/37/49/62/67（14 个全读或读分镜区），其余 53 段用脚本对 67 段全量核查（六段式、前置段、声景、台词、引号、标签、锚点）。
> 链组划分以 `gen_worker.py:42 GROUP=3` + `ep002_segs/manifest.json` 的实际切分为准（下方逐组列出）。

## 总体结论

**有条件通过**：六段式、前置段、声景否定式、台词预算/时间窗、引号烧字幕、表演可见性、参考图在场、全篇维度锚点均无问题；但存在 2 条高危（纸箱锚点自相矛盾、t20 首帧跳变）与 3 条中等（跨场次链组、summary/声景弱否定措辞）需在**不改台词、只改锚点/Entry/声景/分组**的范围内修掉后再生成。

---

## 高（会导致成片废掉）

- **seg04–seg14（t04–t14，共 11 段）** — 渲染器自动前置的「空间锚点」段与分镜正文**正面打架**：锚点逐段写着 苏小满「**holding the cardboard box in both arms**」，但纸箱在 t03 就已经**放下在她右脚边**，t04–t14 的 Entry 全部写着 “the box rests at her right foot / at her foot”，且 16.1 明文规定「纸箱放下后不许再抱起来」。H3 会照正面措辞执行 → 后 11 段纸箱重新回到她怀里，道具线断裂。
  - 应改成（把锚点那句里的抱箱动作删掉，只留位置；纸箱状态交给每段 Entry / shots 承载）：
    - 原：`苏小满 (S1) stands at the NEAR head of the table, half a step to its left, holding the cardboard box in both arms, facing 陆蔓.`
    - 改：`苏小满 (S1) stands at the NEAR head of the table, half a step to its left, facing 陆蔓.`
    - （紧随其后的 `The cardboard box stays in 苏小满's (S1) arms until she sets it down ...; after that it is never picked up again.` 保留即可，它已经把 t03 的放下动作交代清楚。）
  - 修复落点：`storyboard_render.py:333` 的 2-1 锚点模板，或逐段覆写 seg04–seg14。

- **seg15 / t20** — 这是链组 4 = `[t13, t14, t20]` 的**第 3 段**（组内链式，首帧取自 t14 尾帧），但 Entry 与上一段尾拍对不上：seg14(t14) 尾拍是「苏小满**站着**、刚转头看佣人搬来的椅子」，seg15(t20) 的 Entry 却直接写 `苏小满 (S1) is now seated on the low wooden chair ...`。组内生成时首帧 = t14 尾帧（站姿），提示词却要求坐姿 → 第一帧就跳变。
  - 应改成（Entry 承接站姿，并在本段内补一个**可见**的坐下动作）：
    - 原：`苏小满 (S1) is now seated on the low wooden chair at the NEAR head of the long rosewood table, back to the door, seat facing the FAR head, both hands resting in her lap;`
    - 改：`苏小满 (S1) still stands at the NEAR head of the long rosewood table, her head turned to the low wooden chair the steward has just set down beside her; she then sits down onto it in one slow visible movement, back to the door, seat facing the FAR head, and her hands come to rest in her lap;`
    - `[Shot 1]` 开头补一句可见的落座动作（如 `she lowers herself onto the chair and settles`），再进入「陆蔓翻开文件夹」。

---

## 中

- **链组 22 = `[t72, t80, t81]` 跨场次** — manifest 里 t72（2-2 结尾，陆家会客厅·夜）与其后的 t80/t81（2-3 市一院·次日）落在同一链组，t80 会拿 **t72 的尾帧当首帧**，夜里会客厅直接接到次日医院，场景/时间双跳变（虽然 t80 已出本次 2-1/2-2 审核范围，但边界由 t72 触发，必须在生成前修掉）。
  - 应改成：分组改为**场景边界优先**——把 2-3 首段 t80 强制作为新链组组头，用 `04_ref2v_4step_sla_ganloss_fixed.json` 从参考图从零重建，不与 t72 同组。
    - 具体落点：`gen_worker.py` 的 `manifest[g0:g0+GROUP]` 切片改为按 `scene` 字段断组（或让 `storyboard_render.py` 在写 manifest 时按场景补一个 0 段作为占位，使场景首段正好落在 `idx % 3 == 0`）。

- **seg07 / t07 的 `summary`** — 含 15.7 明令禁用短语 **`nothing at all`**。虽不在 `overall_soundscape`（本段也无台词，风险低于声景），但同样是喂给 H3 的正面文本，且原文语义其实想表达「她不做任何回应」。
  - 应改成：
    - 原：`Silent beat: the cleaner turns a level, unreadable look on the laughing young master for two full seconds and gives the room nothing at all.`
    - 改：`Silent beat: the cleaner turns a level, unreadable look on the laughing young master for two full seconds, holding her face completely still.`

- **seg32 / t37 的 `overall_soundscape`** — `the quiet of the whole room settling` 是「房间静下来」的否定式味道（接近 15.7 的 `gone quiet`），本段又有 陆蔓 台词，有把人声一起压低的风险。
  - 应改成：
    - 原：`A low older voice stopping short, the chandelier's hum, the clock, and the quiet of the whole room settling.`
    - 改：`A low older voice stopping short, the chandelier's hum, the clock, and the whole room leaning in on her words.`

---

## 低

- **seg03 / seg05 / seg08 / seg14 挂 `lu_hall_desk`（2-1 段）** — 该场景图是「桌面俯拍：青瓷茶盏 + 菲林文件夹 + 钢笔 + 印泥盒」，用于 t05/t08 取茶盏是对的；但 t03（纸箱落地）和 t14（搬椅子）里桌面不是主体，把这张含**2-2 专属道具（文件夹/钢笔/印泥盒）**的图挂进 2-1，有提前把协议道具画到 2-1 桌面上的风险。
  - 应改成（给这几段加 ref_notes 降级，不改正文）：
    - 原：`<Picture n>: a close framing of the polished dark rosewood table top ... Use for the table surface, prop and light-direction reference only.`
    - 改：`<Picture n>: a close framing of the polished dark rosewood table top ... Use as the table-surface material and light-direction reference ONLY; do NOT introduce the folder, the pen or the seal-paste dish into this scene — in 2-1 the table top is bare apart from the celadon tea cup.`

- **含 `Silent` 一词的 summary（t03/t07/t12/t14/t20/t28/t32/t34/t40/t51/t52/t54/t58/t61/t62/t64/t67/t68 等 18 段）** — 这是「无台词段」的命名习惯，且这些段确实没有 `[Chinese]`，实测不影响（声景行都干净），但为消除 H3 对 `silent` 的潜在敏感，建议统一换词。
  - 应改成：把 summary 开头的 `Silent beat:` / `Silent wide:` / `Silent close beat:` / `Silent opening beat` 统一替换为 `Wordless beat:` / `Wordless wide:` / `Wordless close beat:` / `Opening wordless beat`。

- **seg18 / t23 的 `overall_soundscape`** — `the far wall's stillness behind her lifted hand`，`stillness` 属弱否定。本段有台词。
  - 应改成：`..., the chandelier's hum, the clock, and a low shift of silk from the far head as she lifts her hand.`

- **seg10 / seg38 的 `overall_soundscape`** — `the seated family holding still`，属「动作静止」而非「无声」，在 15.7 允许区间内，但可换成更正向的写法：
  - 应改成：`..., and the seated family leaning in.`

- **个别 Entry 只写了单个人物，未复述上一段尾拍的主体（seg05 Entry 只写陆蔓，而上段尾拍是陆航；seg06 Entry 写陆航+苏小满，而上段尾拍是茶盏特写）** — 不构成矛盾（下一段第一拍本就是切到另一主体），但 15.9 要求 Entry 等于上一段最后一拍，建议补全以防首帧不稳。
  - 应改成（例 seg05）：
    - 原：`陆蔓 (S8) sits at the far head seat with her hands folded on the table edge and her eyes on the near end; the celadon teacup stands at her right hand.`
    - 改：`陆航 (S14) still sits on the sofa arm having just looked the cleaner over, 苏小满 (S1) stands at the near end hands at her sides, and 陆蔓 (S8) sits at the far head with her hands folded on the table edge and her eyes on the near end; the celadon teacup stands at her right hand.`

- **2-2 锚点里的 `陆航 (S14) still perches on the sofa arm ...` 出现在 t21–t50 等陆航并不挂参考图、也不在画面里的段** — 只是场景常量描述，风险低；若要更稳，可在纯特写段（t34/t52/t58/t67/t68）把这句删掉，避免 H3 把陆航塞进特写背景。

---

## 已核对无问题项

- **六段式完整性**：67/67 段均含 `subject_definitions / summary / retention_analysis / detailed_description / overall_soundscape / non_diegetic_music` 六段，无缺段、无空段（`non_diegetic_music` 均为配乐描述或 `N/A`）。
- **自动前置段**（逐尾句校验 67/67）：`STYLE`（`VERTICAL 9:16 PORTRAIT`…`natural 24fps motion blur.`）、`SOFT_LIGHT`（`LIGHTING IS SOFT, BRIGHT AND FLATTERING`…`no gloom, no muddy darker corners`）、`NO_TEXT`（`ABSOLUTELY NO SUBTITLES`…）、`SPEAKERS`（`Speaker labels are stable`…）、`空间锚点`（2-1 版 / 2-2 版，按场次正确切换）、`曝光重锚`（…`Never return a clip darker or more contrasty than the reference images`）全部在齐且完整；除上述「纸箱」一句外，前置段与分镜正文不打架。
- **渲染保真**：`segNN` 的 `Entry + [Shot…]` 与 beats 的 `shots` 字段 **67/67 逐字一致**，渲染器未改字、未错位。
- **链式顺接（逐组核查）**：g0 t01-03 ✓、g1 t04-06 ✓、g2 t07-09 ✓、g3 t10-12 ✓、g4 t13-t14 ✓ / **t14→t20 ✗（见高 2）**、g5 t21-23 ✓、g6 t24-26 ✓、g7 t27-29 ✓、g8 t30-32 ✓、g9 t33-35 ✓、g10 t36-38 ✓、g11 t39-41 ✓、g12 t42-44 ✓、g13 t45-47 ✓、g14 t48-50 ✓、g15 t51-53 ✓、g16 t54-56 ✓、g17 t57-59 ✓、g18 t60-62 ✓、g19 t63-65 ✓、g20 t66-68 ✓、g21 t69-71 ✓、**g22 跨场次（见中 1）**。除 t20 外，全部相邻段 Entry 与上一段尾拍的位置/朝向/手中物一致。
- **声景否定式**：67 段 `overall_soundscape` **均无** `silence/silent/mute/nothing at all/dead quiet/total hush/gone quiet/nothing but/absolute quiet/no other sound/almost nothing` 等禁用式（仅 seg32 有弱化措辞，见中 3）。
- **不烧字幕**：67 段 + 两 beats 文件均无 `subtitle/caption/lower-third/title card/on-screen text/text overlay/watermark` 词（NO_TEXT 段自身的「NO SUBTITLES」除外）；台词**零引号**（ASCII `"`、弯引号、`「」『』` 全部为 0 命中）——`[Chinese]` 后直接跟汉字。
- **台词预算（16.4）**：无一段超过 24 字；最长 22 字（seg37/t42「第二，从今天起…」、seg44/t49「那我今晚…」）。**时间窗**（字数/2.5 + 起始 ≤ 10.0 s）全部通过，最晚结束 9.2 s（seg18/t23「找到她，江边的老宅，归她。」@5.2s）。
- **表演可见性（16.2）**：所有含 `[Chinese]` 的段，正文均有可见的动作/表情/目光/身体位移（手、指、眼、下巴、脊背、落座、起身、推纸、按印、摩挲红绳等），无「只有台词」的段。
- **参考图在场（15.8）**：逐段比对 `refs` 与 `subject_definitions`——**无不存在的角色参考图**；`luhang` 仅出现在他确实在场的 t01、t04、t06、t07、t12、t28、t51、t62；纯苏小满/陆蔓的段（t02、t09、t11、t16 等）未挂 `luhang`。`lu_hall` 与 `lu_hall_desk` 无张冠李戴（仅上述 2-1 提前注入风险，已列低）。
- **空间锚点（16.1）**：全篇「陆蔓恒在 FAR half、苏小满恒在 NEAR half」，同框均为 over-the-shoulder / front-to-back；**无「左右并排 / 一字排开」**（唯一 `either side of` 出现在 seg48/t53，指的是**桌面上两只手**，非两个人）；旁支沿东墙 `one behind another`（纵深排列）符合竖屏铁律。
- **道具连续性（16.1/0.6）**：纸箱 t03 落地后各段 Entry 均为 "box … at her right foot"（除锚点句，见高 1）、t20/t72 仍 "on the floor beside the table leg"；红绳 t08–t11 索要→掩护、t71–t72 摩挲收束；协议锚点显式声明 `the document never leaves the table`，行程为 翻开→推→翻看→再推→转回→添字→递笔→签押→按印→收起，连续；印泥盒 t67 打开、t68 留红指印，位置在桌面前半幅。
- **画面偏黑（2026-10-03 用户口径）**：分镜正文**零** `pitch dark/in darkness/dimly lit/murky/unlit/deep shadow/underexposed` 等压暗硬描述；且 STYLE 段自带 `Absolutely NOT underexposed, not dark, not murky, not crushed, not contrasty` 与曝光重锚段 `Do NOT inherit the tone, grain, contrast or darkness of any previous clip` 的反向保护。
