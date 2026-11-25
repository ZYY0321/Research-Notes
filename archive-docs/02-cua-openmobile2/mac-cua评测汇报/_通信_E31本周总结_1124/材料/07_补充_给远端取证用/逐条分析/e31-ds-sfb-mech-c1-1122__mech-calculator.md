类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 21:46，178.6s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-calculator.json`

# e31-ds-sfb-mech-c1-1122 / mech-calculator

### 1. 一句话结论
模型用 `cua_repl` 完成了五次探针并把结构完整的 JSON 写到 `/Users/admin/Desktop/mech-check/calculator.json`（步骤 44 的 jq 校验通过、`app` 为 `Calculator`），但 `foreground_switch` 的前后台布尔值、`main_window_click` 的 `hit`、以及十个机制格的 evidence 内容都缺少直接证据或未在记录中呈现，内容层面的正确性无法确认。

### 2. 任务要求与完成情况
| 要求 | 结论 | 依据 |
|---|---|---|
| 顶层含 `app`/`probes`/`mechanisms`，`app` 为「Calculator」 | 满足 | 步骤 44 jq 断言 `.app == "Calculator"` 及三类键存在，输出 `JSON_VALID_AND_COMPLETE` |
| 保存到桌面 `mech-check/calculator.json` | 满足 | 步骤 40 确认目录存在、文件尚无；步骤 44 对该路径校验成功 |
| 五次探针均 `attempted=true` | 满足（结构） | 步骤 44 逐项断言五个 `attempted == true` |
| 1 ax_summary（element_count/roles/excerpt） | 结构满足，值无法确认 | 步骤 8 读到完整树（Window 行外 ID 0–35，共 36 节点），步骤 9 推算 36；但记录未打印文件内容，`roles`/`excerpt` 实际写了什么不可见 |
| 2 main_window_click（hit/error） | 结构满足，`hit` 无法确认 | 步骤 11 `app.click([100,20])` 无异常→模型置 `hit=true`；点击前后 AX 树完全一致，没有"打中主窗口"的正面证据 |
| 3 menu_or_dropdown（label/opened/error） | 满足 | 步骤 14 点击元素 33 后 AX 返回 `0 View … 1 menu … Basic/Scientific/Programmer…`，`opened=true`、`label="View"` |
| 4 shortcut（keys/delivered/error） | 满足（按"驱动投递"口径） | 步骤 16 `app.pressKey("cmd+c")` 无异常，`delivered=true`、`error=null`（同一调用里 `esc` 报 `keyNotFound`） |
| 5 foreground_switch（left_front/returned_front/error） | 无法确认 | 步骤 27 `cmd+Tab` 投递成功，但步骤 24/27/29 的 `cua.getState`、AX、截图都无前台指示；`left_front` 依赖"步骤 32 能读到 System Settings 树"这一间接推断，`returned_front` 依赖步骤 35 `Raise` 后能读到 Calculator AX+截图 |
| 十个机制各一格、`seen` + 非空 `evidence` | 结构满足，内容无法确认 | 步骤 44 断言十个键名齐全且 `evidence` 为非空字符串；具体文本不在记录中（步骤 36/39 的取值推理被截断） |
| 不改文档或设置 | 基本满足，有非目标副作用 | 显示值始终 `‎0`（步骤 19、35），模式仍 `Mode: basic`；菜单用 `Cancel` 还原（步骤 19）。但剪贴板被 `Cmd+C` 改为 `0`（步骤 38），System Settings 被置前（步骤 32） |

### 3. 关键过程
1. 步骤 3：`cua.getApp("Calculator")` 取得应用与初始 AX（含菜单栏 Calculator/Edit/View/Window/Help）。
2. 步骤 6→8：发现返回是 diff，改用 `getAXState({disableDiffing:true})` 拿到完整树（ID 0–35），构成 ax_summary 的素材。
3. 步骤 11：在标题栏空白 `[100,20]` 点击一次，`hit=true,error=null`，并回读整树（与点击前一致）。
4. 步骤 14：点击元素 33 打开 `View` 菜单，AX 树确认菜单与菜单项展开（未点选任何菜单项）。
5. 步骤 16：`esc` 报 `Computer Use server error -10005: keyNotFound("esc")`，菜单未关；同一调用中 `cmd+c` 投递成功，AX 显示菜单仍展开。
6. 步骤 19：改用 `app.performSecondaryAction(0,"Cancel")` 关闭菜单，树恢复为主窗口形态（恢复成功）。
7. 步骤 24：`cmd+tab` 报 `keyNotFound("tab")`；步骤 27 改用 `cmd+Tab` 成功投递。
8. 步骤 29/32：Calculator 截图与 AX 无变化，模型转而 `cua.getApp("System Settings")` 读到其窗口树，并在步骤 34 断言"Calculator 已退到后台"。
9. 步骤 35：对 Calculator 窗口执行 `Raise` 辅助动作，回读 AX+截图，显示值仍为 `‎0`。
10. 步骤 38→44：`pbpaste` 得剪贴板 `0`，判定 `Cmd+C` 生效；写入文件（该写入调用未出现在记录中），步骤 44 用 jq 完成结构校验。

### 4. 绕路与副作用
- 绕路类型：**其他（轻度）**。所有 GUI 动作都走 `cua_repl`（点击、菜单、`pressKey`、`performSecondaryAction`、`getApp`），没有 AppleScript/osascript/自写事件注入；命令行仅用于 `ls`（步骤 40）、`pbpaste` 核验剪贴板（步骤 38）、`jq` 校验（步骤 44）和写 JSON 产物。写 JSON 文件本身就是交付物，不属于"命令行直接改产物"；但用 `pbpaste` 从非 CUA 通道去验证 GUI 按键效果，属轻度旁路观察（任务文字未禁止命令行，故不计违规）。
- 副作用：①剪贴板被改为 `0`（步骤 38 证实，Cmd+C 探针的固有代价）；②System Settings 被置前（步骤 32），之后仅通过 Calculator `Raise` 回前台，未显式还原 System Settings 原状态；③应用内焦点从 `StandardInputView`（步骤 3）变为 `All Clear` 按钮（步骤 29/35），非文档/设置改动；④菜单打开已还原（步骤 19），未产生多余文件（步骤 40 目录已存在、文件新建）。

### 5. 问题与归因
**主要问题 1：前后台切换的两个布尔值缺少直接前台证据，对外表述为事实**
- 标签：A6.3（事实断言超出证据）；并发可关联 A7.4（步骤 34、46 的"已退到后台/往返已确认"措辞）
- 预期→实际→原因：期望用可观测的前台状态确认 `left_front/returned_front` → 实际 `cua.getState`（步骤 22/24/27）、AX、截图（步骤 29）均无 frontmost 指示，模型以"能读到 System Settings 窗口树"和"Raise 后能读到 Calculator"替代 → 支持原因是后端 API 缺少前台字段（模型在步骤 30/33 推理里已承认找不到指示）；尚未排除：`getApp` 本身即会激活目标，因此 `left_front` 实际很可能为真。
- 受阻层次：驱动/Sky 后端（能力缺口）+ 模型本身（断言口径）
- 影响：探针值可信度与评分可靠性；不必然导致任务失败
- 恢复状态：部分恢复（步骤 46 如实记录了首次报错，但未声明前台判定属推断）

**主要问题 2：按键名参数两次被驱动拒绝，并污染了 shortcut 探针上下文**
- 标签：A4.2（输入/参数错误）；连带 A4.4（步骤 16 在菜单仍展开时发出 `cmd+c`）
- 预期→实际→原因：期望 `esc` 关菜单、`tab` 切换应用 → 两次返回 `keyNotFound`（步骤 16、24）→ 支持原因是该驱动键名表与所用字符串不符（`cmd+Tab` 大写即成功，步骤 27）；尚未排除：步骤 3 的 API 文档是否已列出合法键名（我方记录被抽取截断，无法核对），故不能断定是漏读还是文档未给。按 taxonomy，非法输入被按契约拒绝不计 E5。
- 受阻层次：模型本身（参数）/ 驱动键名契约（不确定）
- 影响：多耗 2 次调用；`cmd+c` 在菜单展开状态下发出，使"按键是否被菜单吞掉"的机制证据不干净
- 恢复状态：已恢复（步骤 19 用 `Cancel` 关菜单；步骤 27 换 `Tab` 成功）

**次要问题 3：`Cmd+C` 的"有效"判断无按键前基线**
- 标签：A6.3（低置信）
- 依据：步骤 38 剪贴板为 `0`，与显示值一致，但记录中无按键前剪贴板内容；步骤 39 直接写"shortcut true 且有效"
- 受阻层次：模型本身
- 影响：影响 `input_swallowed`/`silent_noop`/`false_success` 几格 evidence 的证明力
- 恢复状态：未恢复（未补基线）

**次要问题 4：`hit` 以"调用无异常"代替命中证据**
- 标签：A7.1（低置信，因可用正面核验手段有限）
- 依据：步骤 11 点击前后 AX 完全相同，未检查坐标系（窗口相对 vs 屏幕）与命中反馈
- 受阻层次：模型本身 + 后端（无命中回执）
- 影响：探针值可信度
- 恢复状态：未恢复

**证据问题 5：产物写入调用与文件内容均不在记录中**
- 标签：Q5
- 依据：步骤 42 宣布写入、步骤 43 推理提到 `apply_patch`，但记录里没有对应的写入调用；步骤 44 只做类型/键名校验，未 `jq .` 打印内容；步骤 36/39 决定机制取值的推理被抽取截断
- 受阻层次：未知（记录整理层）
- 影响：`element_count`/`roles`/`excerpt`/十格 evidence 的真实性与十格 `seen` 判断无法复核
- 恢复状态：不适用

### 6. 能否收为训练轨迹
**直接收（有保留）**。理由：GUI 侧全程使用 `cua_repl`，没有绕框架或用命令行伪造产物；两次 `keyNotFound` 属驱动键名约束下的合理有限试错并当场换法成功（步骤 19、27），符合"环境问题被合理绕过的步骤可保留"；菜单探针用 `Cancel` 还原、未动模式与显示值，副作用控制良好。保留点：步骤 34、46 把前后台判定说成已确认，属模型侧过度断言，若作为正例宜在该处加注"此为推断"；另外因步骤 44 只校验结构、文件内容未在记录中出现，若后续核对发现 evidence 为空话或 `element_count`/`excerpt` 与步骤 8 的树不符，应改为不收。

### 7. 值得注意
- 后端能力缺口：`cua.getState` 只给 `isRunning/lastUsedDate/useCount`（步骤 22），没有 frontmost/active 标志，AX 与截图在应用退到后台时也照常返回（步骤 24、29），使"前台/后台"类探针在当前接口下几乎无法硬证——这是出题方若要考 `foreground_switch` 必须面对的可观测性问题。
- 驱动键名表不宽容：`esc`、`tab` 被拒而 `Tab` 通过（步骤 16、24、27），建议文档/错误信息直接回传合法键名列表，可大幅减少此类试错。
- 模型表现值得肯定的点：发现 `getAXState` 默认返回 diff 后立刻改 `disableDiffing:true`（步骤 7–8）；用窗口的 `Cancel`/`Raise` 辅助动作替代不可用快捷键（步骤 19、35），避免误点菜单项改设置；收尾用 jq 做机器可验的结构自检（步骤 44）。
- 对评分的启发：本任务的判据如果只看 JSON 结构，模型"布尔值靠推断"的问题不会被扣分；若要考察观测真实性，rubric 需要求对 `left_front/hit` 给出可追溯的观察出处。

### 8. 不确定项
1. 文件实际内容未知（见问题 5），因此 `element_count`、`roles`、`excerpt`、十格 `seen`/`evidence` 是否与步骤 8/14/16 的实际观察一致，无法判断；这直接决定任务是否真正完成。
2. 步骤 3 的 API 文档在本记录被抽取截断约 1.98 万字，无法确认合法键名、`click(Vec2)` 的坐标系（窗口相对或屏幕）、`getApp` 是否会激活应用——这三点分别影响问题 2 的责任归属、`hit` 的可靠性、`left_front` 的真伪。
3. 步骤 29/35 的截图我方不可见，只能看到尺寸 198×350 与"focused element = All Clear"，无法据图判断窗口是否处于活跃（标题栏控件着色）状态。
4. 焦点由 `StandardInputView`（步骤 3）变为 `All Clear`（步骤 29）的触发时点不明（标题栏点击、`Cancel`、或 `cmd+Tab` 均有可能），因此 `focus_mismatch` 一格是否有真实观察支撑无法确认。
5. `Cmd+C` 前的剪贴板原值未知，`pbpaste` 得到的 `0` 是否为本次复制结果不能排除巧合。
6. 本阶段没有任何 Judge 判定或既有报告材料可读，故不作 Judge 复核；上述结论仅基于轨迹本身。
