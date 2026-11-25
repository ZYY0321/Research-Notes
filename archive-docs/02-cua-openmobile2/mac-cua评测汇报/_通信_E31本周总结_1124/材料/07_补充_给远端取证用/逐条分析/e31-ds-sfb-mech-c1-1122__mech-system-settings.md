类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 22:06，142.9s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-system-settings.json`

# e31-ds-sfb-mech-c1-1122 / mech-system-settings

### 1. 一句话结论
模型用 `cua_repl` 完成了五次探针并用 `jq` 校验了桌面 `mech-check/system-settings.json` 的顶层结构、五探针 `attempted` 与十机制字段（步骤50 exit=0），任务要求在结构层面可判为满足；但**实际写文件的调用在记录中缺失**，JSON 正文（excerpt/roles/evidence 等语义内容）无法核验，这是本案最大的证据限制。

### 2. 任务要求与完成情况

| # | 要求 | 判定 | 依据 |
|---|---|---|---|
| 1 | probe1 ax_summary：读 AX 摘要，给 element_count / roles / excerpt | 满足（结构）／内容无法确认 | 步骤6 `getAXStateAndScreenshot` 返回完整 AX 树；步骤9 统计出 90 行编号，步骤11 显示末行是重复的 `15 row (selected)`，步骤12 推理改用唯一索引 89；步骤50 jq 校验 `element_count` 为 number、`roles` 为 array、`excerpt` 为非空 string。写入的具体数值与原文片段未在记录中出现 |
| 2 | probe2 main_window_click：对主窗口点一次，给 hit / error | 满足 | 步骤13 `app.click([600,30])` 未抛错，输出 `{mainWindowHit: true, mainWindowClickError: null, windowStillPresent: true}` |
| 3 | probe3 menu_or_dropdown：打开一个菜单，给 label / opened / error | 满足 | 步骤16 `app.click(86)`（View），AX 变为 `0 View ... 1 menu` 加 46 个菜单项；步骤18 置 `menuOpened=true` |
| 4 | probe4 shortcut：发一个快捷键，给 keys / delivered / error | 满足 | 步骤26 `app.pressKey('Command+f')`，返回末行 `The focused UI element is 3 search text field (settable)`，可支持"已投递" |
| 5 | probe5 foreground_switch：切后台再切回，给 left_front / returned_front / error | 基本满足（left_front 证据偏间接） | 步骤39 `finder.pressKey('Command+n')` 打开 "Recents" 窗口、步骤41 Finder 截图成功（920×436），支持 System Settings 让出前台；步骤44 `app.performSecondaryAction(0,'Raise')` 后 AX 回到 `0 standard window ID: main` 且焦点行为搜索框。没有对"System Settings 确已离开前台"的直接视觉证据（步骤21 其截图不可用） |
| 6 | 五探针 attempted 全为 true | 满足 | 步骤50 jq `([.probes[] | .attempted == true] | all)` 通过，且五个动作在步骤6/13/16/26/39+44 均实际发生 |
| 7 | 十种机制各一格，seen 布尔 + evidence 非空 | 满足（结构）／evidence 真实性无法确认 | 步骤50 jq 校验十个键名齐全、`seen` 为 boolean、`evidence` 为非空 string；正文未显示，无法逐句比对是否"实际观察到的一句" |
| 8 | 顶层 app / probes / mechanisms，app = "System Settings" | 满足 | 步骤50 jq `.app == "System Settings"` 与 `.probes | keys` 断言通过 |
| 9 | 保存到桌面 `mech-check/system-settings.json` | 满足 | 步骤47 `mkdir -p /Users/admin/Desktop/mech-check` 成功；步骤50 jq 直接读该绝对路径且 exit=0 |
| 10 | 不改 System Settings 的文档或设置 | 满足 | 全程只有：点击标题栏区域、打开/取消 View 菜单、Command+f 聚焦搜索框（未输入文本）、Raise；步骤23/44 的 AX 仍是 `15 row (selected) General`，无面板切换或开关变更 |

### 3. 关键过程
1. 步骤3 `cua.getApp("System Settings")` 初始化并拿到完整 AX 树与菜单栏（84–88）。
2. 步骤6 读 AX+截图（715×625），步骤9/11/12 自查发现编号行里有 `Selected:` 段造成的重复计数，修正为唯一索引。
3. 步骤13 完成点击探针并回读 AX 确认主窗口仍在。
4. 步骤16 以 AX 索引点开 View 菜单，确认 `1 menu` 与菜单项列表（opened 有硬证据）。
5. 步骤18 `pressKey('Escape')` 未报错但菜单仍开（`backToWindow: false`）——这是"动作静默无效"的直接观察。
6. 步骤21 `app.getScreenshot()` 返回 `Screenshot unavailable for /System/Applications/System Settings.app.`，模型改用 AX 作为唯一观测通道。
7. 步骤23 `performSecondaryAction(1,'Cancel')` 成功收起菜单（`backToWindow: true`），恢复干净状态。
8. 步骤26 Command+f 投递成功（焦点落到搜索框）。
9. 步骤33/36 两次前台切换尝试失败：`finder.click([500,400])` 报 `...noWindowsAvailable`，`cua.computer.launch_app` 报 `TypeError: ... is not a function`；步骤39 改用 Finder 的 `Command+n` 取得真实前台窗口，步骤44 关闭临时窗口并 Raise 回 System Settings。
10. 步骤47+50 建目录并用 jq 做字段/类型/键名完整性校验，输出 `JSON valid: ...`；步骤52 对外声明 silent_noop / unreachable_target / input_swallowed 为 seen=true，其余 7 项 false。

### 4. 绕路与副作用
- **绕路类型：命令行直接写产物（但任务未禁止命令行，按任务文字属允许范围）**。产物生成与校验走 `/bin/zsh -lc`（步骤47、50），UI 观测与动作全部走 `cua_repl`，未使用 AppleScript/osascript/自写点击等绕框架手段。
- 次要绕路：**应用外换路**——因 `launch_app` 不存在、Finder 无窗口可点，改用 Finder `Command+n` 制造前台窗口来实现 foreground_switch（步骤38–39）。
- 副作用：
  - 在 Finder 新建了一个 "Recents" 窗口（步骤39），步骤44 已点 `44 close button` 关闭，Finder 回到无标准窗口的 Desktop 状态（已恢复）。
  - System Settings 搜索框被 Command+f 聚焦（步骤26），未输入内容，无数据改动。
  - View 菜单被打开过（步骤16），步骤23 已取消。
  - 新建目录 `~/Desktop/mech-check`（步骤47）；步骤29 Finder 桌面已见 `image mech-check`，`mkdir -p` 对已存在目录无害。
  - 无多余文件、无误改设置记录。

### 5. 问题与归因

**主要问题（影响证据可信度，非任务完成）**
1. **产物写入步骤在记录中缺失，JSON 正文不可核验**
 - 标签：Q5（证据记录缺失或不一致）
 - 受阻层次：未知（记录/归档环节；步骤48 推理计划用 `apply_patch`，但轨迹中步骤47 之后直接跳到步骤50 的 jq 校验，且步骤47 的 `ls` 显示目录当时为空 `total 0`）
 - 归因：预期动作=写入 JSON → 实际结果=文件确实存在且通过 jq（步骤50 exit=0），说明写入发生过 → 支持原因是该次工具调用未进入本记录；尚未排除的解释包括整理时未收录 `apply_patch` 调用。
 - 影响：无法核对 excerpt 是否为"实际读到的原文"、roles 是否与 AX 一致、十条 evidence 是否为实际观察句、各布尔值（尤其 `shortcut.delivered`、`foreground_switch.left_front`）与观测是否一致。
 - 恢复状态：不适用（记录问题，非运行异常）

**次要问题／运行异常**
2. **Escape 键投递后菜单未关闭、无任何错误**
 - 标签：E5（工具／框架／应用异常）
 - 受阻层次：驱动或 Sky 后端 / 应用（macOS 菜单跟踪循环）——证据不足以区分
 - 归因：预期=Escape 关闭 View 菜单 → 实际=步骤18 `menuCloseError: null` 但 `backToWindow: false`，AX 仍显示菜单展开 → 支持原因是按键未进入菜单跟踪循环；未排除应用侧忽略该键。
 - 影响：仅增加 2 步成本；模型改用 `Cancel` 二级动作成功恢复（步骤23）。
 - 恢复状态：已恢复
3. **System Settings 截图不可用**
 - 标签：E5
 - 受阻层次：驱动或 Sky 后端（`Screenshot unavailable for /System/Applications/System Settings.app.`，步骤21）
 - 影响：foreground_switch 的 `left_front` 缺少直接视觉确认，只能依赖 Finder 侧证据；模型改用 AX 继续（合理回退）。
 - 恢复状态：部分恢复（改用替代观测，视觉证据未取得）
4. **Finder 坐标点击被拒：`noWindowsAvailable`**
 - 标签：E5
 - 受阻层次：驱动或 Sky 后端（按应用窗口裁剪坐标域）
 - 影响：切后台首选路径失效，花 2 步换路（步骤33→39）。
 - 恢复状态：已恢复
5. **`cua.computer.launch_app` 不存在**
 - 标签：E5（API 契约与模型预期不一致；也可视为模型对不确定接口的一次试探）
 - 受阻层次：框架/模型桥接 — 步骤34 推理本就标注"mac 可能不支持"，属有限探索，按标准不计为 A4.3 错误
 - 影响：1 步成本
 - 恢复状态：已恢复
6. **`left_front` 判定依据偏间接**
 - 标签：暂不定错（最接近 A7.1，但未达"必要且当时可执行的检查未做"门槛，因 System Settings 截图不可用）
 - 受阻层次：驱动或 Sky 后端限制
 - 影响：该字段的真值可靠性略弱于其他字段
 - 恢复状态：不适用

说明：未对模型加 A1/A2/A6 类标签——步骤12 的计数自查、步骤26 的焦点取证、步骤23 的恢复均显示理解与观察无可证实偏差；最终声明（步骤52）范围限于"已保存并通过结构校验 + 三项 seen=true"，与步骤50 证据相符，不构成 A7.4。

### 6. 能否收为训练轨迹
**倾向：遮掉写文件环节的空洞后收（或在补齐写文件调用记录后直接收）。**
理由：
- 步骤18–23（Escape 静默无效 → 改用 Cancel）、步骤21（截图不可用 → 转 AX）、步骤33–39（坐标点击被拒、API 不存在 → 用 Finder `Command+n` 换路）都是**环境/驱动问题被模型合理绕过**，正是值得保留的高价值片段。
- 步骤9→12 的自我计数纠偏是良好的观测严谨性示例，应保留。
- 产物只走 CLI 生成是任务允许的，不属于"绕框架改产物"的不当正例；但**写入调用在本记录中不可见**，若作为"产物质量"监督信号使用会训练到无法验证的内容，故建议对缺失段落做遮挡或补档后再用。
- 未发现模型自身错误操作需要遮掉的步骤。

### 7. 值得注意
- **模型能力**：在"只能用 AX、无截图"的降级条件下仍完成五类探针，且每个布尔结论都尽量挂到可观察信号（`1 menu` 节点、`The focused UI element is 3 ...`、`0 standard window ID: main`），探针设计意识较强。
- **Sky 后端/驱动**：三处值得报 bug —— (a) `pressKey('Escape')` 在菜单跟踪态下静默失效且不报错；(b) 系统自带 app（`/System/Applications/System Settings.app`）截图不可用；(c) 无标准窗口的应用（Finder 桌面）坐标点击报 `noWindowsAvailable`，使"切后台"这类系统级操作缺少一等 API（`launch_app` 在 mac 不存在）。
- **对出题/评分**：本题的 10 个机制格恰好被驱动自身的缺陷"喂"出了真实样本（silent_noop / unreachable_target / input_swallowed），说明这类体检题有效；但评分若要校验 evidence 的真实性，必须在归档中强制保留写文件调用的 patch/内容，否则只能校验结构、无法校验语义。
- 另建议题面明确"left_front 可接受的证据等级"，否则在截图不可用的 app 上该字段天然只能间接取证。

### 8. 不确定项
1. **JSON 正文全部未知**：element_count 最终写 89 还是 90、roles 列表内容、excerpt 原文、10 条 evidence 文本、`shortcut.delivered` 与 `foreground_switch.left_front` 的取值，均只有类型级证据（步骤50），无内容级证据。若其中任一 evidence 为空泛套话或与观察不符，完成判定可能从"满足"降级。
2. **写文件所用通道未知**：步骤48 计划 `apply_patch`，但实际调用未记录；无法确认是否符合"命令行以任务文字为准"的授权边界（按任务文字应属允许）。
3. **被整理截断的内容**：步骤3/6/13/16/23/26/33/39/44/45 均有「抽取截断」段，其中步骤45 截断约 8194 字，可能含模型对 10 个机制的逐条判断依据与写文件前的最终组装逻辑——这部分视为看不到，故对"evidence 是否源自实际观察"无法判断。
4. **System Settings 是否真的离开前台**：无直接证据（其截图不可用），仅由 Finder 前台窗口与截图成功间接支持。
5. **Escape 失效的发生层**：无法区分驱动按键投递、macOS 菜单事件循环还是应用忽略，归因保留为"驱动或后端/应用，未定"。
6. **Judge 复核**：本次材料未提供任何 Judge 判定或既有报告，无法执行复核环节，也不补造判定；上述结论均为独立判断。
