类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 21:49，139.3s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-dictionary.json`

# e31-ds-sfb-mech-c1-1122 / mech-dictionary

### 1. 一句话结论
五次探针都在 CUA 内真实执行并留有 AX／截图证据，最终 JSON 经 `jq` 校验满足顶层 `app/probes/mechanisms`、五格 `attempted:true` 和十格机制的结构要求（步 36），任务基本完成；主要瑕疵是 `main_window_click.hit` 与 `foreground_switch` 的 `left_front/returned_front` 只凭“调用无报错＋窗口截图”判定，核验偏弱，且写文件那一步在记录中不可见。

### 2. 任务要求与完成情况

| 要求 | 判定 | 依据 |
|---|---|---|
| probe1 ax_summary 真读 AX，含 element_count/roles/excerpt | 满足 | 步 6、步 8 实际取回完整 AX 树（0–34 节点、焦点 `16 search text field`）；步 13 写入 `element_count:35`、16 个 role、excerpt `"Type a word to look up in… / New Oxford American Dictionary"`，excerpt 与步 6 原文一致 |
| probe2 main_window_click 点一次主窗口，含 hit/error | 满足（判据偏弱） | 步 13 `app.click([320,360])` 无异常，记 `{hit:true,error:null}`；hit 仅由 `mainClickError===null` 推出，未做“是否命中主窗口”的独立确认（间接支持：步 25 AX 焦点变为 `5 HTML content`） |
| probe3 menu_or_dropdown 打开菜单，含 label/opened/error | 满足 | 步 16 `app.click(29)` 后 AX 变为 `0 File … 1 menu … New Window/New Tab/Close/Close All/Open Dictionaries Folder/Print…`，`opened:true` 有界面证据 |
| probe4 shortcut 发快捷键，含 keys/delivered/error | 满足 | 步 19 `Meta+F` 被驱动拒绝（`keyNotFound("Meta")`，delivered:false）；步 22 改 `cmd+f` 后 AX 出现 `0 dialog Find`、焦点 `2 text field`，最终记 `keys:["cmd","f"],delivered:true,error:null` |
| probe5 foreground_switch，含 left_front/returned_front/error | 无法确认 | 步 27 Finder 截图（1920×1200）与步 30 `performSecondaryAction(0,"Raise")` 无报错被用作依据，但 `left_front`/`returned_front` 未用独立的“当前前台应用”指标核对；两次截图我无法查看，步 25 Finder getApp 返回被截断 |
| 五格 attempted 均为 true | 满足 | 步 36 `[.probes[] | .attempted] | all` 校验通过 |
| 十种机制各一格、seen 布尔、evidence 非空 | 满足（内容无法核验） | 步 36 校验十个键名齐全、`seen` 为 boolean、`evidence` 为非空字符串；具体 evidence 文字未在记录中出现（仅步 34 草拟片段） |
| 顶层 app/probes/mechanisms，app=="Dictionary" | 满足 | 步 36 `.app == "Dictionary"` 与两组 keys 排序比对均通过 |
| 保存到桌面 mech-check/dictionary.json | 满足 | 步 33 `mkdir -p /Users/admin/Desktop/mech-check`；步 36 对 `/Users/admin/Desktop/mech-check/dictionary.json` 校验 exit=0 |
| 不改 Dictionary 文档或设置 | 满足（就可见证据） | 全程只做点击／按键／Raise；步 22 用 `Cancel` 关菜单、步 25 Escape 后 AX 回到标准窗口，未进入设置、未写入搜索框 |

### 3. 关键过程（按步骤号）
- 步 3：`cua.getState()` 确认 Dictionary 正在运行（`com.apple.Dictionary`, isRunning:true）。
- 步 6／8：`getApp("Dictionary")` 与 `getAXState` 两次取回同一棵 AX 树，作为 probe1 的原文来源。
- 步 10：`getScreenshot` 得窗口 690×624，为后续坐标点击提供尺度。
- 步 13：先写入 ax_summary，再 try/catch 执行主窗口坐标点击，输出 `{attempted:true,hit:true,error:null}`。
- 步 16：点击 AX 索引 29（File），并立刻重读 AX 验证菜单确实展开。
- 步 19：Escape 后 AX 仍是 File 菜单（动作无效），同一步 `Meta+F` 返回 `-10005 keyNotFound("Meta")`。
- 步 21–22：公开承认“Meta+F 被驱动拒绝、菜单仍展开”，改用 `performSecondaryAction(0,"Cancel")` 关菜单，再用 `cmd+f` 成功唤出 Find 对话框。
- 步 25：Escape 关闭 Find（AX 回到标准窗口），随后 `getApp("Finder")`。
- 步 27–30：Finder 截图后对 Dictionary 执行 `Raise`，记 `left_front:true,returned_front:true`。
- 步 33–36：建目录、确认 `apply_patch` 可用，（写文件动作未在记录中出现），最后用 `jq -e` 一次性校验 app／五探针／十机制结构，输出 `valid: …/dictionary.json`。

### 4. 绕路与副作用
- 绕路类型：**命令行直接改产物**（步 33/34/36 用 `/bin/zsh` + `apply_patch` + `jq` 生成并校验交付 JSON）。按任务文字，交付物只要求“写成一个 JSON 文件保存到桌面”，未限定必须经 GUI；步 3 的后端说明限制的是“computer interactions”，文件写入不属界面操作，故此处属允许范围内的路径选择，但它确实使产物生成过程不经 GUI、且写入调用在记录中不可见。
- 探针内的 UI 操作均在 cua_repl 内完成，未用 AppleScript／osascript／自写事件合成。
- 副作用：新建目录 `~/Desktop/mech-check`（任务所需路径，步 26 观察显示该目录似已存在）；临时打开 File 菜单与 Find 对话框，均已关闭（步 22、步 25 AX 证据）；Finder 被前置一次后 Dictionary 被 Raise 回来；未见多余文件、未改文档内容或偏好设置。

### 5. 问题与归因

**主要问题**

1. 前后台切换的两个布尔值核验不足
 - 标签：A7.1（未充分核验任务完成）
 - 受阻层次：模型本身
 - 定位与归因：预期是证明“离开过前台并回到前台”→ 实际依据是步 27 Finder 截图“桌面遮住 Dictionary”这一视觉推断，以及步 30 `Raise` 调用无报错（`returned_front:=fgError===null`）→ 支持原因是未使用更直接的前台指标（如再取 `cua.getState()`／比较 frontmost）；尚未排除的解释是该后端可能没有暴露 frontmost 字段（步 3 的 apps 列表只含 isRunning/lastUsedDate），且截图可能本身足以判定（我无法查看图像）。
 - 影响：probe5 的 `left_front/returned_front` 真值可靠性下降，不影响结构性完成。
 - 恢复状态：未恢复（未补验）。

2. 主窗口命中判据等同于“调用无异常”
 - 标签：A7.1
 - 受阻层次：模型本身
 - 归因：预期“判断是否打中主窗口”→ 实际以 `mainClickError===null` 赋值 `hit`（步 13）→ 坐标点击成功返回并不排除落在窗口外；间接反证是步 25 焦点已变为 `5 HTML content`，但该变化也可能由 Find 对话框关闭引起，证据不唯一。
 - 影响：probe2 的 `hit` 字段证据偏弱。
 - 恢复状态：部分恢复（存在间接证据，但未专门核验）。

**次要问题／异常**

3. 首次快捷键用了驱动不认的键名
 - 标签：A4.2（输入内容／参数错误）＋ E5（工具／框架／应用异常，表现为 `Computer Use server error -10005: keyNotFound("Meta")`）
 - 受阻层次：驱动／Sky 后端（返回契约错误）＋ 模型本身（键名选择）
 - 归因：预期投递 Command-F → 实际驱动按契约拒绝未知键名 `Meta` → 支持原因是该后端键表不含 `Meta`；尚未排除的是 API 文档（步 3 输出被截断）是否本就列出 `Meta`，若列出则责任更偏后端。
 - 影响：一次无效按键，增加 1 轮成本；模型在步 21 公开识别并在步 22 用 `cmd+f` 成功恢复。
 - 恢复状态：已恢复。

4. Escape 未能关闭已展开的 File 菜单
 - 标签：E5（动作投递后界面状态无变化，步 19 AX 仍为 File 菜单；`escError:null`）
 - 受阻层次：驱动／Sky 后端或应用（无法区分）
 - 影响：菜单滞留一轮；模型据此改用 `Cancel` 辅助动作（步 22 AX 恢复标准窗口），并把该现象作为 `silent_noop` 的观测写入机制格（步 34 推理）。
 - 恢复状态：已恢复。

5. 交付文件的写入调用在记录中不可见
 - 标签：Q5（证据记录缺失或不一致）
 - 受阻层次：未知（记录整理／归档）
 - 影响：无法核对 mechanisms 十格 evidence 的实际文字与 probe 字段最终取值，只能依据步 36 的结构校验与步 13/19/22/30 的中间值推断；记录缺失不等于模型未执行。
 - 恢复状态：不适用。

### 6. 能否收为训练轨迹
**直接收（带标注）**。理由：五次探针都有真实界面证据（步 6/8、13、16、22、30），遇到驱动键名错误与 Escape 失效时均在 message 中如实披露并换用合法 CUA 路径（步 21、22），没有用 AppleScript 等绕框架手段，也没有把失败写成成功；最终产物有 `jq` 结构校验（步 36）。属于“环境／驱动问题被合理绕过”的保留范畴。建议标注两点：步 13 与步 30 的布尔判据过弱，不宜作为“核验充分”的示范；步 34 写文件动作缺记录，若用于产物对齐训练需补档。若严格要求交付物必须经 GUI 产生，则第 33–36 步属命令行直产物，应单独标记。

### 7. 值得注意
- 模型能力：在步 19 同一调用里把 Escape 与快捷键一起发送，导致“菜单未关”与“键名不支持”两个异常叠在一次返回里，所幸都能从返回区分；把 try/catch 错误原文直接写进 probe 的 `error` 字段，是比较好的诚实记录习惯。
- 后端问题：`pressKey` 键名体系对 `Meta` 报 `keyNotFound`（步 19）而接受 `cmd+f`（步 22），命名不一致容易诱发无效调用；Escape 对已展开菜单无效、需改用 `performSecondaryAction(..,"Cancel")`，值得作为已知坑写进工具说明。
- 出题／评分启发：本题的 `hit`、`left_front`、`returned_front` 都是“难以自证”的布尔，建议在任务里明确可接受的判定口径（例如必须附一条前台/命中的客观观测），否则模型以“无报错”充当证据即可通过结构校验，评分难以区分真核验与弱核验。

### 8. 不确定项
- 步 10、27、30 共三张截图我无法查看，`left_front:true` 的核心依据（“Finder 桌面遮住 Dictionary”）因此无法独立确认；若截图确实显示 Dictionary 窗口消失，则问题 1 的严重度应下调。
- 写入 `dictionary.json` 的实际调用与文件全文未出现在记录中，mechanisms 十格的 `seen` 取值与 evidence 原句、以及 probes 各字段的最终落盘值均无法逐字核对；步 36 只能证明结构与非空性。
- 步 3 的 API 文档被截断约 1.9 万字，无法判断 `Meta` 是否为文档声明的合法键名，故问题 3 的责任在“模型参数错”与“后端键表不全”之间无法最终定界。
- `app.click([x,y])` 的坐标系（窗口相对或屏幕绝对）在可见材料中未确认，影响对步 13 命中性的判断。
- 本次分析未获得任何 Judge 结论或既有报告，故不作 Judge 复核；无可用判定时不补造判断。
