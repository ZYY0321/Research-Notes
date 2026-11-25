类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 21:47，197.9s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-activity-monitor.json`

# e31-ds-sfb-mech-c1-1122 / mech-activity-monitor

### 1. 一句话结论

模型在截图不可用、部分 API 与文档不符的条件下完成了五次探针并把结构完整、`app` 正确的 JSON 写到 `/Users/admin/Desktop/mech-check/activity-monitor.json`（步骤64 jq 校验 `true`），交付基本满足硬性要求；过程中出现一次由 AX 差分观察引发的"菜单已关闭"状态误判（步骤15–29），模型自行诊断并恢复（步骤31–37），但产物写入动作本身没有留下记录、mechanisms 的 evidence 文本不可核验。

### 2. 任务要求与完成情况

| 要求 | 判定 | 依据 |
|---|---|---|
| 不改 Activity Monitor 的文档或设置 | 满足 | 全程只读 AX、打开 `View`/应用菜单后用 `Cancel` 收起（步骤37、57），未点选任何菜单项；仅焦点由 `outline 2` 变为 `scroll bar 22`（步骤37），非设置变更 |
| 探针1 ax_summary：element_count / roles / excerpt | 部分满足（roles 存疑） | 步骤6 AX 树索引 0–53 → `element_count: 54` 可核；`excerpt: "Processes (showing 0-19 of 100 items)"` 与步骤6 原文一致；但 roles 含 `"menu bar item"`，步骤6 中 48–53 行只显示名称无 role 文本，步骤7 reasoning 自述 "menu bar items no role text maybe AX menu bar item inferred"，即该项为推断而非"实际看到的 role" |
| 探针2 main_window_click：hit / error | 满足（判据弱） | 步骤9 `app.click(0)`（元素 0 = `standard window`）返回 `{hit:true,error:null}`；hit 仅以"无异常"判定，未读点击前后 AX 对比（对照步骤34 可见 click 返回 ok 仍可能无效果） |
| 探针3 menu_or_dropdown：label / opened / error | 满足 | 步骤12 `click(51)` 后 AX 显示 `0 View ... 1 menu`，确认展开，`label:"View", opened:true, error:null` |
| 探针4 shortcut：keys / delivered / error | 满足（有省略） | 步骤18 `Command+F` → `{delivered:true,error:null}`；但步骤15 `Meta+F` 的 `keyNotFound("Meta")` 未体现在 JSON 或最终说明，步骤58 reasoning 明确"Do not mention invalid Meta key" |
| 探针5 foreground_switch：left_front / returned_front / error | 满足（error 字段存疑） | left_front 依据步骤48 Finder 自身菜单实际展开；returned_front 依据步骤54 `Raise` 后 Activity Monitor 应用菜单展开；但过程中有 `launch_app is not a function`（步骤40）、`AXError.illegalArgument`（步骤45），步骤57 变量里 error 为 illegalArgument，最终 JSON 写 `null`（步骤58 reasoning 讨论后取 null） |
| 五次探针 attempted 均为 true | 满足 | 步骤64 jq `[.probes[] \| .attempted == true] \| all` 通过 |
| 十种机制各一格，seen + 非空 evidence | 结构满足／内容无法确认 | 步骤64 jq 验证 10 个 key、`seen` 为 boolean、`evidence` 为非空字符串；evidence 的具体文本未在任何输出中打印，无法核对是否"实际观察到的一句" |
| 顶层 app/probes/mechanisms，app = 「Activity Monitor」 | 满足 | 步骤64 输出 `"app": "Activity Monitor"`，`.probes` 五键、`mechanism_count: 10` |
| 保存到桌面 mech-check/activity-monitor.json | 满足 | 步骤60 目录就绪（`MISSING` 表示文件原不存在）；步骤64 jq 对该绝对路径读取成功 |

### 3. 关键过程

1. 步骤3 `cua.getState()` 确认 Activity Monitor 在运行；步骤6 `getApp` 一次拿到完整 AX 树（0–53，焦点 `outline 2`），作为探针1 的原始证据。
2. 步骤9 `app.click(0)` 命中主窗口元素，返回 `hit:true,error:null`，完成探针2。
3. 步骤12 `click(51)` 打开 `View`，AX 树整体切换为菜单结构，完成探针3。
4. 步骤15 先发 `Escape`（无 try/catch、无报错），再发 `Meta+F` 被驱动拒绝：`keyNotFound("Meta")`；步骤18 改 `Command+F` 投递成功，但两次 AX 均返回 "no change"。
5. 步骤20 模型对外称"该应用界面没有可见变化"——此时实际上 `View` 菜单仍开着，差分"no change"恰恰说明状态未变（仍为菜单态）。
6. 步骤21/24/26/29：`Command+Tab`、`getState`、截图（`Screenshot unavailable for ... Activity Monitor.app`）、`Command+H` 均无法确认前台变化。
7. 步骤31 改用 `getAXState({disableDiffing:true})` 强制重读，发现 `View` 菜单仍展开；步骤32–33 自行归因"Escape 没关掉菜单，所以前台切换未生效"。
8. 步骤34 `click(0)` 点菜单标题仍未关闭（返回 ok）；步骤37 改用 `performSecondaryAction(0,"Cancel")` 成功回到主窗口树。
9. 步骤40 `cua.computer.launch_app` 不存在；步骤43/45 转向 Finder，桌面容器点击报 `AXError.illegalArgument`；步骤48 点 Finder 菜单栏项成功，作为"离开前台"证据；步骤51–54 `Cancel` + `Raise` + 打开应用菜单，作为"回到前台"证据。
10. 步骤60 shell 建目录并确认文件原不存在；写入动作未出现在记录中（步骤62 reasoning 提及 apply_patch）；步骤64 jq 一次性校验结构与必填值，输出 `true`。

### 4. 绕路与副作用

- 绕路类型：**命令行直接改产物**（步骤60 `mkdir -p`、步骤62 reasoning 所述 apply_patch 写 JSON、步骤64 jq 校验）。任务文字未禁止命令行、交付物本身就是磁盘文件，故按"以任务文字为准"不构成违规；但 CUA 预置提示要求 UI 交互仅用 `cua_repl`，若出题意图是全程 GUI 产出，则此路径属绕路。
- 另有**应用内换路**（非改设置）：`pressKey` 关菜单失效后改用 AX 次级动作 `Cancel`/`Raise`（步骤37、51、54）；`launch_app` 缺失后改用 Finder 菜单栏点击实现前台切换（步骤48）。
- 副作用：未见多余文件（`mech-check` 目录在步骤43 Finder 桌面已存在，`mkdir -p` 无新建；步骤60 确认目标文件原本 MISSING）；未修改任何 Activity Monitor 设置；残留的是焦点由 `outline` 变为 `scroll bar 22`（步骤37、57），以及一次把 Finder 带到前台后再 Raise 回来（步骤48–54）。

### 5. 问题与归因

**主要问题**

1. 状态误判：把 AX 差分 "no change" 当作"Escape 已关闭 View 菜单、界面无变化"
   - 标签：A5.1（当前控件/窗口状态判断错误），附带 A2.2（对 "There has been no change in the accessibility tree" 的语义误读）
   - 预期→实际→原因：预期 Escape 关菜单、`Command+F` 聚焦搜索框 → 实际菜单一直开着、后续 `Command+Tab`/`Command+H` 均无效（步骤21、29）→ 支持原因：步骤15/18/29 的默认差分输出掩盖了"仍是菜单态"这一事实，模型按"无变化=已回主窗口"推进；尚未排除的解释是 Escape 本身未被投递（步骤15 未捕获返回值）。
   - 受阻层次：模型本身（判据选择）+ 驱动/Sky 后端（差分观察 + 按键静默无效）
   - 影响：步骤20 的对外陈述不准确；步骤21–31 约 5 步额外成本
   - 恢复状态：已恢复（步骤31 `disableDiffing` 重读 + 步骤37 `Cancel`）

2. 产物写入动作无记录
   - 标签：Q5（证据记录缺失）
   - 影响：无法核验 JSON 的写入方式与写入时内容；mechanisms 的 10 条 evidence 文本从未在任何返回中打印，只能确认"非空字符串"（步骤64）；因此"evidence 是实际观察"这一项无法核验
   - 受阻层次：框架/记录整理（本记录的抽取截断与步骤缺失）
   - 恢复状态：不适用（产物存在性与结构已由步骤64 间接证实）

**次要问题／运行异常**

3. `keyNotFound("Meta")`（步骤15）：A4.2（按键名参数不被驱动支持）+ E5（驱动键名契约）。受阻层次：驱动/Sky 后端；影响仅一次重试；步骤18 改 `Command+F` 后已恢复。属合理有限试探，不作错误计重。
4. `cua.computer.launch_app is not a function`（步骤40）：E5（工具/框架契约与实现不一致，步骤40 reasoning 称 "despite docs"；文档正文被抽取截断，是否确实承诺该方法无法确认）。影响：前台切换改道 Finder，增加 ~4 步。已绕过。
5. `Screenshot unavailable for /System/Applications/Utilities/Activity Monitor.app.`（步骤26）：E5。影响：全程无视觉核验手段，`hit`、`left_front` 等只能靠 AX 与菜单展开间接判断，证据强度下降。未恢复（能力缺失）。
6. 点击返回成功但无效果（步骤34 `click(0)` 未关菜单；步骤21/29 `Command+Tab`/`Command+H` 无状态变化）：E5（驱动/应用层静默无效，亦即任务所列 silent_noop / false_success 现象本身）。对任务是有效观测素材，不计模型错误。
7. `finder.click(1)` → `AXError.illegalArgument`（步骤45）：A4.1 轻度（点到 `scroll area (disabled) desktop` 的容器）+ E5。首次尝试、立即换路（步骤48），不计重。
8. 交付透明度：`foreground_switch.error` 写 `null`（步骤57/58 讨论后决定）、`Meta+F` 失败未在 JSON 与步骤66 说明中体现（步骤58 reasoning 明确决定不提）。标签：A7.1 轻度（对"error 同上"的口径未作保守披露）。是否构成 A7.4 取决于验收方把 error 理解为"该探针最终一次调用的报错"还是"该探针过程中的任一报错"；按前者口径不成立。恢复状态：未恢复（已交付）。
9. roles 含未在原文出现的 `"menu bar item"`（步骤7 reasoning 承认推断，步骤64 输出含该项）：A6.3 轻度。影响：ax_summary 中一项非直接观察；其余 role 词是否全部出自原文，因步骤6 中间 1316 字被抽取截断而无法核验。

### 6. 能否收为训练轨迹

**遮掉第 20–29 步后收**（并对第 9 步的 `hit` 判据加注）。

- 可保留的正面片段：步骤6 一次性取全树、步骤12 用 AX 结构确认菜单真展开、步骤31 主动 `disableDiffing` 破除差分盲区、步骤34→37 从失效的 click 改用 AX 次级动作、步骤40→48 在 API 缺失后换路、步骤64 用 jq 对照任务硬性条件自检——这些都是"环境受阻被合理绕过"的良性样本。
- 建议遮掉的是步骤20（基于误判的对外陈述"界面没有可见变化"）及步骤21–29 建立在"菜单已关"错误前提上的 `Command+Tab`/截图/`Command+H` 尝试；若需保留步骤31 的发现过程，可只遮步骤20 的陈述并对 21–29 加失败标注。
- 另一项扣分理由：JSON 实际写入调用不在记录内（见问题2），关键产出动作不可学；若要作为"写文件"类正例，需补齐该步。
- 命令行写产物这一点本身不构成"不当正例"（任务文字未禁止、交付物即文件），但若该题意在考察纯 GUI 产出，则整条轨迹不宜作正例。

### 7. 值得注意

- **框架/Sky 后端**：①`getAXState` 默认差分返回 "There has been no change..." 在"动作本应改变状态但没改变"的场景极易被读成"已恢复到预期状态"，建议差分输出附带当前根节点摘要；②`pressKey` 键名空间不统一（`Meta` 被拒、`Command` 接受），且 `Escape`/`Command+Tab`/`Command+H` 在菜单打开时静默无效；③文档中出现而实现缺失的 `cua.computer.launch_app`（步骤40）；④系统应用 `Screenshot unavailable`（步骤26）使视觉核验彻底不可用，对需要"打中/前台"判定的题型影响很大。
- **模型能力**：会用"打开菜单→读 AX 结构"而非"调用无异常"来证明 opened（步骤12）、会主动用 `disableDiffing` 自查（步骤31）、会用 jq 把任务硬性条件逐条编码校验（步骤64），诊断链条清晰；弱点是把"驱动无异常"直接等同于"动作生效"（步骤9 的 hit），以及倾向在交付里省略中间失败（步骤58 reasoning）。
- **对出题/评分的启发**：本题的 `hit`、`left_front`/`returned_front`、`error` 三处判据在截图不可用时只能间接取证，建议在任务里明确"hit 以什么证据判定""error 记录最终一次还是全过程"；mechanisms 的 evidence 若要真评，需要求把 evidence 原文回显到对话中，否则只能验非空、无法验真实性。

### 8. 不确定项

1. mechanisms 十格的 `seen` 取值与 evidence 文本从未在返回中打印，仅步骤58/61 的 reasoning 片段（且被抽取截断）暗示约 7 项 seen=true；evidence 是否均为实际观察句无法确认——这是本次最大的覆盖限制，直接影响"是否真完成"判断。
2. JSON 的实际写入调用（apply_patch 或等价命令）不在记录内，写入方式与写入瞬间内容无法核验；仅能以步骤64 的 jq 结果反推产物合规。
3. 步骤6 AX 树中间被抽取截断 1316 字，无法逐一核对 roles 列表中 `value indicator`、`increment arrow button` 等是否确实出现在原文；`element_count: 54` 基于索引 0–53 连续的假设。
4. `Escape`（步骤15）究竟是未被投递还是投递后被菜单吞掉，记录不足以区分；这决定该现象应归 input_swallowed 还是 silent_noop。
5. 步骤48"Finder 菜单可展开 ⇒ Activity Monitor 已离开前台"是间接推断（macOS 点击菜单栏通常先激活应用），无截图或 frontmost 字段直接证实；`cua.getState().apps` 顺序在整条轨迹中始终不变（步骤21、24、40、45、48），不能作为前台判据。
6. `launch_app` 是否真在该版本 API 文档中承诺，因文档正文被抽取截断 18866 字而无法确认，故 E5 的"契约不一致"仅为证据支持的推断。
7. 本次未获得 Judge 判定或既有报告，故不作 Judge 复核结论，也不补造判定；上述完成度判断仅基于轨迹内证据。
