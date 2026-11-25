类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 21:52，190.9s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-font-book.json`

# e31-ds-sfb-mech-c1-1122 / mech-font-book

### 1. 一句话结论

模型在 cua_repl 内完成了五次探针并把结果写成了 `/Users/admin/Desktop/mech-check/font-book.json`（步105 jq 校验 `app=="Font Book"`、五个探针键齐全、`attempted` 全为 true、`mechanisms` 长度 10 均返回 `true`），但写文件的那次调用与文件正文未出现在记录中，探针子字段与十格 `seen/evidence` 无法核对；过程中出现多次"调用返回成功但状态未变"的驱动层现象（Escape 关不掉菜单、Raise/click 切不回前台），`returned_front=true` 的证据与步97 冲突且未再核验。

### 2. 任务要求与完成情况

| 要求 | 判定 | 依据 |
|---|---|---|
| 不改 Font Book 文档或设置 | 满足 | 仅做点击/按键/菜单打开；步93 打开应用菜单（含 `Settings…`）后步99 `performSecondaryAction(0,"Cancel")` 收起，未执行任何菜单项 |
| 探针1 ax_summary（element_count / roles / excerpt） | 无法确认 | 确有真实读取：步3、步8 `getAXState({disableDiffing:true})` 返回完整树（索引 0–198，含 `standard window All Fonts – 361 typefaces`、`menu bar` 等），步9 推理推出 199 个元素；但 JSON 内三个子字段的实际取值不可见，步105 的 jq 只校验了 `attempted` 与顶层结构 |
| 探针2 main_window_click（hit / error） | 部分可确认 | 步11 `app.click(0)`（索引 0 即主窗口）返回 `{"hit":true,"error":null}`；无截图可视核对（步37 `Screenshot unavailable for /System/Applications/Font Book.app`），"打中主窗口"只有驱动无报错这一弱证据 |
| 探针3 menu_or_dropdown（label / opened / error） | 满足 | 步14 点击 `196/194 File` 返回 `{"label":"File","opened":true,"error":null}`，步16 AX 树根节点变为 `0 File ... 1 menu ... 2 New Window ...`，菜单确实展开 |
| 探针4 shortcut（keys / delivered / error） | 满足（效果受污染） | 步19 `pressKey("cmd+f")` 返回 `{"keys":"cmd+f","delivered":true,"error":null}`；但步21 AX 仍是 File 菜单、搜索框未获焦，按键是在菜单打开状态下发出的 |
| 探针5 foreground_switch（left_front / returned_front / error） | 部分满足 | `left_front`：步67 在 Finder 打开 `mech-check` 文件夹（步69 Finder 窗口 `focused UI element is 31 collection`），步71 Font Book AX 不再报告 focused element；`returned_front`：步93 点击 Font Book 菜单栏项后步95 应用菜单展开，但步97 Finder 仍报 `The focused UI element is 31 ...`，未解决矛盾即记为 true |
| 五次 attempted 均为 true | 满足 | 步105 `[.probes[].attempted] | all` 为 `true` |
| 十种机制各一格、seen + evidence 非空 | 无法确认 | 步105 仅校验 `.mechanisms | length == 10`，未校验每格是否含 `seen`/`evidence` 及 evidence 是否非空；文件正文不可见 |
| JSON 顶层含 app/probes/mechanisms，app=="Font Book" | 满足 | 步105 jq 表达式包含该条件，exit=0、输出 `true` |
| 路径 桌面 mech-check/font-book.json | 满足 | 步102 `mkdir -p /Users/admin/Desktop/mech-check`，步105 jq 对该路径读取成功 |

### 3. 关键过程（按步骤号）

1. 步3 `cua.getApp("Font Book")` 取得应用与初始 AX 树；步6 `getAXState()` 返回"无变化"，步8 加 `disableDiffing:true` 拿到完整树（0–198）——这是 ax_summary 的真实来源。
2. 步11 对 AX 索引 0（主窗口）点击，`hit:true, error:null`，完成探针 2。
3. 步14 点击 File 菜单、步16 用 AX 复核菜单已展开，完成探针 3（并明确不执行任何菜单命令）。
4. 步19 在菜单仍开的状态下发 `cmd+f`，`delivered:true`；步21 复核发现菜单未关、搜索未聚焦，模型在步23 对外解释为"一次可见的输入被吞现象"。
5. 步24/26/28 连续尝试 `escape`、`esc`、`Escape`：前两次 `keyNotFound`，第三次无报错但步30 菜单依旧展开；步32 `click(0)` 也无效；步39 改用 `performSecondaryAction(0,"Cancel")` 才在步41 恢复主窗口树（元素变为 0–200）。
6. 步46/48 `cmd+tab` 报 `keyNotFound("tab")`，`cmd+Tab` 投递成功但步50 `cua.getState()` 无任何变化，前台未切换。
7. 步55–67 改走 Finder：步57 `finder.click(1)` 返回 `AXError.illegalArgument`；步59–65 排查 `Buffer instanceof Uint8Array` 为 false 并最终 `emitImage` 成功，但图像为 1920×1200 全白、无诊断价值；步67 用桌面 `mech-check` 图标的 `open` 辅助动作把 Finder 推到前台。
8. 步71 据 Font Book AX 不再报 focused element 判定 `left_front`；步74/82 `Raise` 与 `click(0)` 均返回成功，但步80/88 Finder 仍持有焦点——模型在步90 对外承认"未真正回到前台"。
9. 步91 `cua.computer.launch_app` 返回 `is not a function`；步93 点击 Font Book 菜单栏条目后菜单展开（步95），据此记 `returned_front:true`，步99 Cancel 收起菜单。
10. 步102 建目录，（步103/104 推理提到 apply_patch，但该调用本身未在记录中出现）步105 jq 部分校验通过，步107 收尾声明。

### 4. 绕路与副作用

- **绕路类型：无（GUI 部分全程 cua_repl）+ 产物写入走命令行/补丁工具**。五次探针全部由 `cua_repl` 的 `app.click` / `pressKey` / `performSecondaryAction` / `getAXState` 完成；步45 推理中模型明确否决了"用 shell 查 frontmost"的做法（"a shell would be GUI observation and specifically forbidden"），这与系统提示一致，是正确取舍。步102/105 的 shell 仅用于建目录与校验，JSON 落盘属任务要求的交付物、任务未限制工具，不属"命令行直接改产物"的不当类型。
- **副作用**：
  1. 步67 打开了桌面 `mech-check` 的 Finder 窗口（步69 标题 `mech-check`），轨迹结束前未关闭，Finder 侧留有多余窗口。
  2. 步102 `mkdir -p` 对已存在目录（步55 Finder 桌面已见 `image mech-check`）无害，但说明目录原本可能已存在。
  3. 步93 打开过 Font Book 应用菜单（含 `Settings…`），仅打开后取消，无设置变更证据。
  4. 步41 后元素数由 199 变为 201，步42 推理自称"dynamic extra lock image"；是否为步11 点击导致选中/界面变化，证据不足（见第 8 节）。

### 5. 问题与归因

**主要问题**

1. **产物内容不可核验，交付是否"字段缺一格"无法判定**
   - 标签：Q5（证据记录缺失）
   - 层次：框架/记录整理
   - 说明：步103/104 推理提到 `apply_patch`，但记录中没有这次调用及其文件正文；步105 的 jq 只断言顶层键、五个探针键、`attempted` 全真、`mechanisms` 长度为 10，未触及 `element_count/roles/excerpt/hit/label/opened/keys/delivered/left_front/returned_front` 与每格 `seen/evidence`。
   - 影响：评分可靠性与证据可信度；无法确认任务"字段缺一格算没完成"这条是否满足。
   - 恢复状态：不适用（记录层问题）。

2. **最终核验与完成声明超出已验证范围**
   - 标签：A7.1（未充分核验任务完成）；A7.4 边缘（不单独计）
   - 层次：模型本身
   - 说明：任务把"字段缺一格"写成失败条件，`cat`/完整 jq 校验当时可执行且成本极低（步105 已在用 jq），模型只做部分断言，步107 即称"JSON 结构及十个机制字段已校验通过"。
   - 影响：若某格字段缺失或 evidence 为空，不会被发现。
   - 恢复状态：未恢复。

3. **`returned_front` 结论与当时可见反馈冲突且未再核验**
   - 标签：A7.1；A5.1（当前窗口/焦点状态判断）
   - 层次：模型本身（叠加驱动层焦点可观测性不足）
   - 说明：步97 `finder.getAXState()` 明确仍为 `The focused UI element is 31 collection ...`；步98 推理自判"Finder AX reports stale focus perhaps"，随后以"应用菜单能展开"为据写 true。macOS 菜单栏确实只展示前台应用菜单，所以这是有依据的推断，但与直接反馈的矛盾未被解决、也未在 JSON 的 `error` 中留下说明（内容不可见）。
   - 影响：探针 5 的字段可信度。
   - 恢复状态：无法判断。

**次要问题 / 运行异常**

4. **合法调用返回成功但状态未变（驱动与反馈不一致）**
   - 标签：E5（工具/框架/应用异常）
   - 层次：驱动或 Sky 后端（也不能排除菜单模态与 AX action 语义差异）
   - 证据：步28 `pressKey("Escape")` 返回 `{"error":null}` 而步30 菜单仍开；步32 `click(0)` 同样无错无效；步48 `cmd+Tab` 投递成功而步50 `getState()` 完全未变；步74 `Raise`、步82 `click(0)` 均 `returned_front:true` 而步80/88 焦点仍在 Finder。
   - 影响：成本（约 20 步用于关菜单与切前台）、并直接污染 shortcut 与 foreground 两格字段的可信度。
   - 恢复状态：部分恢复（菜单经步39 Cancel 收起；前台经步93 菜单栏点击疑似恢复但未证实）。

5. **观察手段不可用**
   - 标签：E5
   - 层次：驱动或 Sky 后端
   - 证据：步37 `Screenshot unavailable for /System/Applications/Font Book.app`；步65 Finder 截图为 1920×1200 全白；步59/61 `Buffer` 跨 realm 导致 `instanceof Uint8Array` 判定失败、`emitImage(Buffer.from(shot.data))` 报 `Received undefined`。
   - 影响：无法用视觉核对 `hit` 与前台状态，被迫全程依赖 AX 文本。
   - 恢复状态：部分恢复（步63/65 自行定位并成功 emit，但图像无信息）。

6. **shortcut 探针在菜单模态下发出，效果不可分辨**
   - 标签：A4.4（操作时机不当）
   - 层次：模型本身
   - 说明：步17 推理已预见"While menu open, maybe menu remains?"，仍在步19 发送 `cmd+f`；步21 证实未生效。好处是拿到了一条"输入被吞"的观察，代价是该探针无法区分"驱动投递失败"与"菜单吞键"。替代解释：模型可能是故意把它作为机制探测。
   - 影响：探针 4 与机制格 `input_swallowed` 的解释力。
   - 恢复状态：未恢复（未在菜单关闭后补发一次同键验证）。

7. **按键名/API 的试错**
   - 标签：A4.2（输入参数错误，属合理有限探索，不计为错误）
   - 层次：驱动契约未文档化（大小写敏感）+ 模型猜测
   - 证据：步24/26 `keyNotFound("escape")`/`("esc")`、步46 `keyNotFound("tab")`、步57 `AXError.illegalArgument`、步91 `cua.computer.launch_app is not a function`。
   - 影响：仅成本。
   - 恢复状态：已恢复（分别换 `Escape`、`cmd+Tab`、换路径）。

### 6. 能否收为训练轨迹

**不直接收；建议"补全产物证据后，遮掉步 59–65 与步 91 再收"。**

- 可保留：步3–21（探针 1–4 的真实执行与 AX 复核）、步24–41（驱动失效后的有限试错 + 用 `performSecondaryAction("Cancel")` 正确恢复，属"环境问题被模型合理绕过"）、步46–57、步67–99（前台切换的多路径绕行与步90 的诚实报告）。
- 建议遮掉：步59–65（Buffer/emitImage 的框架噪声调试，与任务无关且图像无信息）、步91（凭猜测调用不存在的 `cua.computer.launch_app`）。
- 不收的前提性理由：写入 JSON 的那次调用与文件正文不在记录中（Q5），无法确认这是"字段齐全、evidence 非空"的合格正例；步105 的部分校验 + 步107 的概括声明若作为正例学习，会固化"部分 jq 断言即宣布全量校验通过"的习惯。

### 7. 值得注意

- **模型能力**：对"delivered（驱动投递）/ 实际生效"的区分意识清楚（步22、步23 对外说明），在步45 主动拒绝用 shell 做 GUI 观察，步90 坦白"Raise 与点击返回成功但焦点仍在 Finder"，诚实度较好；弱点在收尾核验，任务已把"字段缺一格=失败"写明，却没做全字段 `cat`/jq 检查。
- **驱动/Sky 后端**：三类问题值得报给后端——(a) `pressKey` 键名大小写敏感且无可发现的键表（`escape`/`esc` 失败、`Escape` 成功；`tab` 失败、`Tab` 成功）；(b) `Escape`、`click`、`Raise`、`cmd+Tab` 返回 `error:null` 却无任何状态变化，无法区分"未投递"与"被应用忽略"；(c) 系统应用截图不可用（`Screenshot unavailable for /System/Applications/Font Book.app`）、Finder 截图全白，桌面 CUA 缺少"当前前台应用"的一等观测量，使 `foreground_switch` 这类探针天然难以取证。
- **出题/评分启发**：这类"机制体检"任务若要求 10×2 格字段齐全，评分侧应直接读取并逐字段校验产物；同时 `foreground_switch` 在当前后端缺少前台判据，建议题面给出可用的判定方式，否则 `returned_front` 只能靠推断，评分难以稳定。

### 8. 不确定项

1. JSON 正文完全不可见（写文件的调用未进入记录），因此 `element_count=199`、`roles`、`excerpt`、各探针子字段、十格 `seen/evidence` 是否齐全且非空，均无法核验；这决定"是否完成"的最终判定，我只能给"部分满足/无法确认"。
2. 步11 `app.click(0)` 落点未知（无截图），"打中主窗口"仅凭无报错；是否连带点中字体网格并改变选中项不可确认——步41/52 出现的 `Selected: 5 row` 与元素数 199→201 的变化（步42 自称"extra lock image"）可能是界面动态内容，也可能与该点击有关。
3. 步28 `Escape` 与步74 `Raise` 的"成功但无效"究竟属驱动未真正合成事件、菜单模态屏蔽，还是 AX action 语义与前台切换无关，现有记录无法区分；因此 E5 的层次归因保留不确定。
4. `returned_front` 是否真实成立：步95 的应用菜单展开支持"已在前台"，步97 的 Finder 焦点支持相反结论，二者未被进一步区分。
5. 步3、步8、步41、步78 等返回文字均被整理者截断（如"…[抽取截断 25222 字]…"），被截部分视为不可见；`roles` 的真实完整集合、`emitImage` 之外可能的额外提示，均无法据此评价。
6. 本次为独立阶段，未读取任何 Judge 结论或既有报告；上述判定仅基于轨迹与步105 的产物校验输出。
