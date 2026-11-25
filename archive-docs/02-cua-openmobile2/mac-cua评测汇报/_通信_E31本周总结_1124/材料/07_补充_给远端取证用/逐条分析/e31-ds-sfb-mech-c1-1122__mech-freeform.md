类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 21:51，153.4s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-freeform.json`

# e31-ds-sfb-mech-c1-1122 / mech-freeform

### 1. 一句话结论
模型用 `cua_repl` 完成了五次探针并写出结构完整、通过自检的 `~/Desktop/mech-check/freeform.json`（步骤 35、38），交付形式满足全部硬性要求；主要瑕疵是 `main_window_click` 的 `hit=false` 与 `foreground_switch` 的前后台判定属于推断而非直接核验，观测准确性存疑。

### 2. 任务要求与完成情况

| 要求 | 结论 | 依据 |
|---|---|---|
| 不改文档或设置 | 满足（有残余不确定） | 全程只做一次画布点击（步骤 11）、打开并用 Cancel 关闭应用菜单（步骤 16、22），未点 Continue、未进 Reset Identifier/Settings；步骤 22 树恢复为 WelcomeWindow 原状 |
| 探针1 ax_summary（element_count / roles / excerpt） | 满足 | 步骤 8 全树索引 0–24 共 25 个元素，JSON 写 `element_count:25`；roles 取自同一输出（sheet/button/text/scroll area/unknown/image/menu bar）；excerpt `"Welcome to Freeform"` 为步骤 8 原文第 3 行 |
| 探针2 main_window_click（hit / error） | 满足字段，内容无法确认 | 步骤 11 `app.click([400,300])` 未抛错，`mainClickError=null`；`hit:false` 仅凭"AX 树与焦点未变"（步骤 12、15）推断，无"点击被模态 sheet 拦截"的直接证据 |
| 探针3 menu_or_dropdown（label / opened / error） | 满足 | 步骤 16 点击元素 16 后树变为 `0 Freeform` + `1 menu`，含 About/Hide/Quit 等真实菜单项，JSON 记 `label:"Freeform", opened:true` |
| 探针4 shortcut（keys / delivered / error） | 满足 | 步骤 19 `app.pressKey("Escape")` 未抛错，JSON 记 `keys:["Escape"], delivered:true`；任务只要求"按键名"，单键可接受 |
| 探针5 foreground_switch（left_front / returned_front / error） | 满足字段，内容部分可确认 | 步骤 28 返回 `Window:"Desktop", App: Finder`、1920×1200 全屏截图；步骤 31 返回 Freeform WelcomeWindow 树。但"离开过前台"依赖 `cua.getApp` 是否激活应用，未用独立方式验证 |
| 五次 attempted 均为 true | 满足 | 步骤 38 python 断言 `all(...attempted is True)`，输出 `schema check passed` |
| 十种机制各一格、seen + 非空 evidence | 满足 | 步骤 38 断言十个键名完全匹配且 `evidence` 非空；步骤 35 可见 permission_wall/state_desync/side_effect_exit 等条目 |
| 顶层 app/probes/mechanisms，app=「Freeform」 | 满足 | 步骤 38 断言 `d['app']=='Freeform'` 与 probes/mechanisms 键序通过 |
| 保存到桌面 mech-check/freeform.json | 满足 | 步骤 35 `mkdir -p /Users/admin/Desktop/mech-check` 后写入，`python3 -m json.tool` 通过，`wc -c` 2529 |

### 3. 关键过程
- 步骤 3：首次 `cua.getApp("Freeform")`，拿到 API 文档与初始 UI 状态（含 WelcomeWindow 与菜单栏）。
- 步骤 6：`getAXStateAndScreenshot` 返回"树无变化"，只给出焦点元素，信息不足。
- 步骤 8：改用 `getAXState({disableDiffing:true})` 拿到完整树（0–24），成为探针1 的数据来源。
- 步骤 11：探针2，`app.click([400,300])` 无报错；步骤 12 模型对截图尺寸（480×600 与 sheet 位置）明显困惑。
- 步骤 13：`cua.getState()` 只返回应用清单，无窗口层级信息，无法据此判定命中。
- 步骤 16：探针3，点击 AX 元素 16 成功展开 Freeform 菜单。
- 步骤 19：探针4，`pressKey("Escape")` 未报错但菜单仍在打开状态——被模型如实记为 input_swallowed/state_desync 证据（步骤 21、32）。
- 步骤 22：用 `performSecondaryAction(1,"Cancel")` 关闭菜单，状态回到 WelcomeWindow。
- 步骤 25→28：`cua.computer.launch_app` 报 "is not a function"，立即改用 `cua.getApp("Finder")` 完成后台切换；步骤 31 再 `getApp("Freeform")` 回前台。
- 步骤 35、38：zsh heredoc 写 JSON 并用 `python3 -m json.tool` + 自写断言做 schema 自检，两次 exit=0。

### 4. 绕路与副作用
- 绕路类型：**无**（五次 GUI 探针全部通过 `cua_repl`；JSON 文件写入与校验用命令行，但任务原文只要求"保存到桌面 mech-check/freeform.json"，未限定 GUI，产物本身就是文件，不构成"命令行直接改产物"的绕路；步骤 34 提到一次沙箱拒绝后按规则重提并执行成功）。
- 副作用：未观察到多余文件（仅 `mech-check/freeform.json`，桌面已存在 mech-check 目录见步骤 28 `image mech-check`）；未误触 Continue/Reset Identifier/Quit；菜单以 Cancel 退出。残余风险见第 8 条（AX 树始终未暴露画布，画布上若有极小改动无法从树确认）。

### 5. 问题与归因

**问题1（主要）：`hit=false` 与 message 中"observed miss"的结论缺少直接核验**
- 标签：A7.1（未充分核验任务完成条件之一）；同一事件亦可对应 A6.3（步骤 15 把推断表述为"observed"），按同事件不重复计影响。
- 归因：预期"判定点击是否打中主窗口" → 实际只取得"无异常 + AX 树/焦点未变"（步骤 11、12）→ 支持原因是模态 sheet 下 AX 只暴露 sheet 与菜单栏（步骤 8），`cua.getState` 不给窗口层级（步骤 13）；尚未排除的解释是点击确实落在主窗口空白处、本就无状态变化（此时 `hit` 应为 true）。
- 受阻层次：驱动/Sky 后端（无窗口命中反馈）+ 模型本身（未尝试其他判别手段，如点击标题栏、对比前后截图像素、使用 sheet 的 `Raise` 次级动作）。
- 影响：影响观测准确性与该格可信度，不影响字段完整性与交付。
- 恢复状态：未恢复（直至交付仍沿用该推断）。

**问题2（次要）：调用不存在的 `cua.computer.launch_app`**
- 标签：A4.3（操作方式/接口不当）或 E5（文档契约与实现不一致）——因步骤 3 的文档正文被整理记录截断 19519 字，无法确认 `launch_app` 是否出现在当时文档中，责任层归为"未知"。
- 影响：浪费 1 次 GUI 调用；步骤 28 立即改用 `getApp` 达到同样效果。
- 恢复状态：已恢复。

**问题3（次要）：前后台判定证据较弱**
- 标签：A7.1（弱核验，程度低于问题1）。
- 归因：预期"证明离开过前台并回到前台" → 实际以 `getApp("Finder")` 返回 Desktop 树/1920×1200 截图、`getApp("Freeform")` 返回 Freeform 树为据（步骤 28、31）→ 未排除 `getApp` 只是附着而非激活的解释；但 Finder 返回全屏桌面观察对"Freeform 非最前"构成一定支持。
- 受阻层次：驱动/Sky 后端（无 frontmost 查询）+ 模型本身。
- 恢复状态：部分恢复（有间接证据，未独立确认）。

**非错误项**：步骤 19 Escape 未生效后，模型没有反复重按，而是改用次级动作关闭菜单（步骤 22），属合理恢复，不计 A8.2；步骤 6 的"无变化"返回后改用 `disableDiffing`（步骤 8）属合理探索。

### 6. 能否收为训练轨迹
**直接收（建议在标注中降权第 11–15 步的 `hit` 判定）。** 理由：GUI 探针全部走 `cua_repl`，无 AppleScript/自写点击/窗口列表读写等绕框架行为；命令行仅用于任务本身要求的文件产出与自检，属允许范围；`launch_app` 不可用（步骤 25）与 Escape 无效（步骤 19）均属环境/驱动侧阻碍且被合理绕过或如实记录，可保留；唯一模型侧瑕疵是 `hit=false` 的弱证据推断（步骤 11–15），它不是错误操作而是结论置信度问题，若按"模型自身错误应遮掉"的严格口径，可只遮步骤 15 的那句"observed miss"表述，不必遮整段操作。

### 7. 值得注意
- 机制体检这类题的真实价值点被跑出来了：Escape 被驱动接受但菜单不关（步骤 19 前后树完全一致），是很干净的 input_swallowed/state_desync 样本；模态 sheet 下 AX 树只暴露 sheet + 菜单栏（步骤 8、11、22、31），是 unreachable_target 的真实来源。
- 后端能力缺口：`cua.getState()` 在 macOS 只返回应用清单、无窗口层级（步骤 13），`cua.computer.launch_app` 不存在（步骤 25），`getApp` 是否带激活语义不明——这三点直接导致 `hit`/`left_front` 只能靠推断。出题或评分若要判这两格的真假，应先提供可查询 frontmost/窗口命中的接口，否则该字段天然不可验证。
- 截图尺寸在应用间差异很大（Freeform 480×600 对 Finder 1920×1200，步骤 11、28），模型据此产生过明显困惑（步骤 12），值得在 prompt 或后端说明中澄清截图是窗口级还是屏幕级。
- 正面习惯：步骤 38 自写断言逐项校验 app 名、probes 键序、attempted、十机制与 evidence 非空，是"字段缺一格算未完成"类任务的好范式；但该断言未校验各探针内部字段（element_count/roles/hit/keys 等），覆盖并不完整。

### 8. 不确定项
- 无法看到任何截图（本分析只能读文字返回），`main_window_click` 是否真被模态 sheet 拦截、Finder 是否真为最前、画布上是否出现任何视觉变化，均无法从图像核实。
- 步骤 3 的 API 文档正文被整理记录截断 19519 字，`launch_app`、`pressKey` 键名语法、`getApp` 的激活语义是否有文档说明不可确认，故问题2 的责任层留"未知"。
- 步骤 35 heredoc 中部被截断 944 字，silent_noop…default_trap 六格的 `evidence` 原文看不到，只能依据步骤 32/36 的推理摘要与步骤 38 的"非空"断言；其中 `precondition` 一格模型自述"是推断"（步骤 36），该格 evidence 是否为"实际观察到的一句"无法核验。
- 步骤 34 提到的沙箱拒绝事件在记录中没有对应 `rejected` 条目，被拒命令原文与拒绝原因不可见（Q5 性质的记录不完整），不影响最终产物结论。
- 本次材料未提供 Judge 判定或已有报告，故不作 Judge 复核，也不补造判定。
