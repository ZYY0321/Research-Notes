类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 21:46，168.0s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-calendar.json`

# e31-ds-sfb-mech-c1-1122 / mech-calendar

### 1. 一句话结论
五次微探针都在 `cua_repl` 内实际发出、JSON 顶层结构与 `attempted`/机制键名经 jq 自检通过（步骤 48），任务大概率可判完成；但 `main_window_click.hit`（步骤 11）与 `foreground_switch.left_front / returned_front`（步骤 34、36）都是在没有命中/前台证据的情况下直接写 `true`，产物逐字段内容也无归档可核。

### 2. 任务要求与完成情况
| 要求 | 判定 | 依据 |
|---|---|---|
| 探针1 ax_summary（element_count / roles / excerpt） | 满足 | 步骤 6、42 实际读到完整 AX（`Window: "Calendar", App: Calendar.` … `The focused UI element is 8 button Continue`）；步骤 40 按索引 0–30 推出 element_count=31、列出 roles；excerpt 为实读原文 |
| 探针2 main_window_click（hit / error） | 部分满足（hit 值依据弱） | 步骤 11 `app.click([40,480])` 返回 `{attempted:true, hit:true, error:null}`；但步骤 10 自述“For actual hit we might not know”，点击后未做任何状态/截图核验 |
| 探针3 menu_or_dropdown（label / opened / error） | 满足 | 步骤 14 点击索引 25 后 AX 出现 `0 Calendar, ID: calendar-menu` + `1 menu`，`label:"Calendar", error:null`，菜单确实展开 |
| 探针4 shortcut（keys / delivered / error） | 满足 | 步骤 17 `app.pressKey("Escape")` 无异常，`keys:["Escape"], delivered:true, error:null` |
| 探针5 foreground_switch（left_front / returned_front / error） | 无法确认（动作已做，布尔值无证据） | 步骤 34 点 System Settings 标题栏无报错即记 `left_front:true`；步骤 36 点 Calendar 无报错即记 `returned_front:true`；步骤 22 `cua.getState` 无 frontmost 字段，全程无前台归属证据，且步骤 36 的 AX 仍是 `calendar-menu` 覆盖层 |
| 五次 attempted 均为 true | 满足 | 步骤 48 jq：`[.probes[].attempted] | all(. == true)` 通过 |
| 十种机制各一格、seen + 非空 evidence | 部分无法确认 | 步骤 48 jq 校验了 10 个键名齐全与 `evidence` 为非空字符串，但未校验 `seen` 字段存在；`seen` 取值仅见步骤 43/45 推理草稿 |
| 顶层含 app/probes/mechanisms 且 app=="Calendar" | 满足 | 步骤 48 jq `.app == "Calendar"` 与 `.probes|keys` 精确匹配五键通过 |
| 保存到桌面 mech-check/calendar.json | 满足 | 步骤 44 `mkdir -p /Users/admin/Desktop/mech-check` 并确认文件 `new`；步骤 48 对该路径 jq 成功 |
| 不改 Calendar 文档或设置 | 满足（证据支持的推断） | 全程只点空白区、菜单栏与 Escape/Cancel；步骤 39 后 AX 回到 `CALMainWindow` + splash 原样，`Settings…` 本就 disabled |

### 3. 关键过程
- 步骤 3/6：`getApp("Calendar")` + `getAXState`，发现应用停在 “What’s New in Calendar” 启动页，toolbar 全部 `(disabled)`，焦点在 `8 button Continue`（后被用作 precondition 证据）。
- 步骤 9：取 Calendar 截图成功（935×598），为坐标点击定位。
- 步骤 11：探针2，点击窗口空白 `[40,480]`，无报错，直接记 `hit:true`，未做后验。
- 步骤 14：探针3，点菜单栏 `Calendar`，AX 明确显示菜单树展开，`opened` 有硬证据。
- 步骤 17：探针4，Escape 投递成功，但 AX 中菜单仍展开——模型据此标注 input_swallowed / state_desync。
- 步骤 19：`getScreenshot` 返回 `Screenshot unavailable for /System/Applications/Calendar.app.`，视觉核验通道中断，之后只靠 AX。
- 步骤 27：首次切后台尝试 `finder.click([760,500])` 失败：`Computer Use server error -10005: noWindowsAvailable`（而步骤 24 的 Finder AX 显示有 Desktop 窗口与 `mech-check` 图标）。
- 步骤 30–34：改用已开的 System Settings，点标题栏 `[350,22]` 无报错，记 `left_front:true`（无前台校验）。
- 步骤 36：点回 Calendar 记 `returned_front:true`，但 AX 仍停在 `calendar-menu`；步骤 39 用 `performSecondaryAction(1,"Cancel")` 才回到 `CALMainWindow`。
- 步骤 44–48：shell 建目录、写文件、jq 结构自检返回 `valid`；步骤 50 对外汇报完成与四项命中机制。

### 4. 绕路与副作用
- 绕路类型：**命令行直接改产物（仅限交付文件）** + 轻度**应用内换路**。JSON 产物由 `/bin/zsh` + apply_patch 写入并用 jq 自检（步骤 44、48），未用 GUI 写文件；五次探针本身全部走 `cua_repl`，没有用 AppleScript/osascript 等绕驱动。任务文字未提及命令行许可或禁止（见不确定项）。
- 换路：Finder 桌面点击被后端拒绝后改用 System Settings 窗口做“离开前台”动作（步骤 29–34），属对环境限制的合理绕过。
- 副作用：新建目录（`mech-check` 桌面上原已存在，见步骤 24 AX）与一个目标文件，属任务要求产物；把 System Settings 提到前台并点了其标题栏（无设置值变更证据）；Calendar 菜单被打开后已显式 Cancel 复位（步骤 39）。未见多余文件、误改数据或误触 `Continue`/`Quit`。

### 5. 问题与归因
1. **foreground_switch 的 left_front / returned_front 无依据写 true**
 - 标签：A7.1（未充分核验）＋ A6.3（缺依据的事实断言）；步骤 38 对外称“前后台切换动作已完成且无错误”另可关联 A7.4。
 - 预期→实际→原因：预期“点其他应用=离开前台、点回 Calendar=回到前台”；实际只拿到两次 `error:null`，`cua.getState`（步骤 22）不含 frontmost，步骤 36 AX 仍是菜单覆盖层，且切换时 Calendar 菜单处于 tracking 状态（macOS 下首个外部点击常被菜单吞掉），故“是否真的离开/返回前台”未排除相反解释。
 - 受阻层次：模型本身（兼驱动能力不足：无前台归属查询接口）。影响：产物字段与完成声明的证据可信度。恢复状态：未恢复（步骤 50 仍按完成汇报）。
2. **main_window_click.hit 以“无报错”代替命中证据**（次要）
 - 标签：A7.1（＋A6.3 轻度）。步骤 10 已自知不可知，步骤 11 仍写 `hit:true`，点击后无截图/AX 对照。受阻层次：模型本身。影响：单字段可信度（坐标 `[40,480]` 落在 935×598 窗口内，值很可能为真）。恢复：未恢复。
3. **Finder 坐标点击被后端拒绝：`noWindowsAvailable`**（异常）
 - 标签：E5（观察与执行契约不一致：AX 报有 Desktop 窗口，click 报无窗口）。受阻层次：驱动/Sky 后端。影响：切后台首选路径失效，多花 3–4 步。恢复：已恢复（步骤 30–34 换 System Settings）。
4. **菜单打开期间 Calendar 截图不可用**（异常）
 - 标签：E5。`Screenshot unavailable for /System/Applications/Calendar.app.`（步骤 19）。受阻层次：驱动/Sky 后端。影响：失去视觉核验手段，后续前台判断只能靠 AX；步骤 39 Cancel 后模型也未重试截图（关联 A7.1 轻度）。恢复：部分恢复（改用 AX 读取）。
5. **Escape 投递成功但菜单在 AX 中不消失**（观察对象，非模型错误）
 - 这是任务要体检的现象本身；机制归属（按键被菜单循环吞掉 vs AX 状态未刷新）无法从记录区分，可能同时涉及 E5；模型把它同时写进 input_swallowed 与 state_desync 两格，属可辩解但证据复用。
6. **产物内容不可逐字段复核**
 - 标签：Q5。文件内容未在记录中回读，仅有步骤 45 的草稿和步骤 48 的布尔结果；`seen` 字段存在性、`element_count=31`、各探针子字段未被 jq 覆盖。影响：评分依据可靠性与本分析覆盖面。恢复：不适用。

### 6. 能否收为训练轨迹
**遮掉第 34–36 步（foreground_switch 的无证据 `true` 记法）后收**，并同时修正第 11 步的 `hit` 记法。
- 可保留：步骤 3–17（AX 读取、窗口空白点击、菜单探针、Escape 探针）与步骤 19–34 中对 `Screenshot unavailable`、`noWindowsAvailable` 的识别与换路，这些是环境/后端问题被合理绕过的良性片段；步骤 39 的 Cancel 复位、步骤 44–48 的建目录+结构自检也是好习惯示范。
- 应遮/改：把“点击无报错”直接写成前台/命中既成事实（步骤 11、34、36）属模型自身的核验缺口，若作为正例会教出“无证据填 true”的习惯。
- 附加条件：若本任务判定不允许命令行，则步骤 44–48 的产物写入属“命令行直接改产物”，整条不宜作正例（见不确定项）。

### 7. 值得注意
- 能力面：模型对“啥都不能改”的边界把握不错（只点空白区、只用 disabled 项之外的无害菜单、用 `performSecondaryAction(…,"Cancel")` 复位），并主动做了 jq 结构自检（步骤 48），这是少见的交付前自检。
- 短板：十格机制里 seen=true 的四项有三项共用同一两个观察（Escape 不生效、noWindowsAvailable、splash+disabled toolbar），证据多样性不足；对“前台”这类不可直接观测属性缺少“写 unknown/附条件”的习惯。
- 后端/驱动：Sky 后端两处值得上报——(a) 菜单 tracking 期间 app 截图直接不可用（步骤 19）；(b) Finder 桌面 AX 可读但坐标点击返回 `-10005 noWindowsAvailable`（步骤 24 vs 27）；(c) 缺少 frontmost/activate 类 API，使 foreground_switch 这类探针天然不可验证。
- 出题/评分启发：若要考 `left_front/returned_front` 的真实性，需提供可查询前台的接口或要求模型给出可核验证据（如切换前后两个应用的截图），否则该字段只能靠自述；评分脚本也宜一并校验探针子字段与 `seen` 的存在性，而非只看键名与 `attempted`。
- 本次无 Judge 结论或既有报告可读，故不作 Judge 复核，也不补造判定。

### 8. 不确定项
1. 产物实际内容未归档，`seen` 字段、`element_count`、`roles`、各探针子字段、十条 evidence 原文均无法逐项核对；仅能依赖步骤 48 的 jq 条件（app、probes 五键、attempted 全真、mechanisms 十键、evidence 非空字符串）。若评分要求逐字段，结论可能变化。
2. 命令行写文件是否允许：案例说明称“以任务文字为准”，而任务文字既未授权也未禁止 CLI；工具文档（步骤 3）要求“computer interactions 只用 cua_repl”。按“写文件不是 UI 交互”解读则无问题，按严格解读则属绕路——此歧义直接决定第 6 节的收录结论（可关联 Q1）。
3. `left_front` / `returned_front` 的真值未知：既无前台证据支持，也无证据证伪；步骤 36 AX 仍显示菜单层既可能是“点击未生效”，也可能是“AX 未刷新”。
4. 记录中间多处由整理者截断（步骤 3、6、10、20、25、30、40、43、45 等，合计数万字），其中可能包含模型对前台/命中的进一步核验或完整 JSON 草稿；相关判断以“证据不足”处理，不据此断言模型未核验。
5. Escape 不生效与截图不可用的发生环节（应用菜单循环 / AX 刷新 / 驱动）无法从现有记录定位，E5 归因保留为“层次未完全确定”。
