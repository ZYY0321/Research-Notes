类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 22:07，219.6s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-textedit.json`

# e31-ds-sfb-mech-c1-1122 / mech-textedit

### 1. 一句话结论
五次探针都用 `cua_repl` 真实执行并有 AX 证据，JSON 已落到 `/Users/admin/Desktop/mech-check/textedit.json` 且经 `jq` 校验顶层三键、五个 `attempted=true`、十个机制键齐全（步骤 52），任务基本达成；主要瑕疵是过程中若干次工具调用形式错误（步骤 24/26/32/49）、标题栏误触重命名弹层（步骤 12→14）、以及成功写文件那一步在记录中缺失导致文件逐字段内容无法完全核验。

### 2. 任务要求与完成情况
| 要求 | 结论 | 依据 |
|---|---|---|
| 1 ax_summary：读 AX 摘要，给 element_count / roles / excerpt | 满足（roles 部分无法确认） | 步骤 3、5 实际读到 AX 树（0–52 共 53 节点）；步骤 45 以 `/^\s*\d+\s/` 程序计数得 `element_count:53`；`excerpt` 取自实读首两行 `Window: "Untitled", App: TextEdit.` / `0 standard window Untitled, Secondary Actions: Raise`。但 `roles` 18 项为手写硬编码（步骤 45 代码），AX 树中段在本记录被抽取截断，无法逐项核验「text alignment」「color well」等是否均实读到 |
| 2 main_window_click：点一次主窗口，hit/error | 满足 | 步骤 12 `app.click([280,16])` 无异常，记 `hit:true,error:null`；步骤 14 AX 变化证明点击确实作用在主窗口（标题栏） |
| 3 menu_or_dropdown：开一个菜单，label/opened/error | 满足 | 步骤 18 `app.click(47)` 后 AX 首行变为 `0 File ... 1 menu`，列出 New/Open…/Save… 等，`label:"File", opened:true` 有视图证据 |
| 4 shortcut：发一个快捷键，keys/delivered/error | 满足（口径可辩） | 步骤 28 `app.pressKey("Command+H")` 返回 `{keys:'Command+H',delivered:true,error:null}`，步骤 30 Finder 变为可读前台侧证按键生效；但前两次 `Meta+,`、`Command+,` 的报错（步骤 24、26）未保留在 `error` 字段 |
| 5 foreground_switch：切后台再切回，left_front/returned_front/error | 满足（returned_front 为间接推断） | 步骤 43 干净重做：`Command+H` 后 `finder.getAXState` 首行 `Window: "Desktop", App: Finder.` → `left_front:true`；`performSecondaryAction(0,"Raise")` 无错且 TextEdit AX 可读 → `returned_front:true`。模型自己在步骤 33/37/41 承认 AX 可读不等于前台 |
| 五次 attempted 均为 true | 满足 | 步骤 45 构造时写死 `attempted:true`，步骤 52 `probe_attempted` 返回五个 `true` |
| 十种机制各一格、seen + evidence 非空 | 部分无法确认 | 步骤 52 `(.mechanisms|keys|length)==10` 为真；步骤 49 补丁可见 default_trap / permission_wall / state_desync / side_effect_exit 的 `seen+evidence` 文本，其余 6 格文本因抽取截断不可见，且实际写入文件的那次命令未入记录 |
| JSON 顶层 app/probes/mechanisms，app=="TextEdit" | 满足 | 步骤 52 `jq -e` 返回 `true`，并输出 `"app": "TextEdit"` |
| 路径 桌面 mech-check/textedit.json | 满足 | 步骤 47 `mkdir -p /Users/admin/Desktop/mech-check`（步骤 30 Finder 桌面已显示 `mech-check`）、步骤 52 jq 对该路径读取成功 |
| 不改 TextEdit 文档或设置 | 满足（就现有证据） | 步骤 14 弹出的重命名/文档操作浮层在步骤 16 被 Escape 关闭，AX 回到原树；文档标题始终 `Untitled`，文本区未被输入；File 菜单仅打开后取消（步骤 22） |

### 3. 关键过程
1. 步骤 3/5：`cua.getApp("TextEdit")`、`getAXState` 读到完整 AX 树（0–52，焦点为 `2 text entry area`），作为 ax_summary 数据源。
2. 步骤 7/9：先用 `emitImage` 取截图失败（只回 Buffer 文本），改为 `app.getScreenshot()` 得 571×461 窗口图，用于定位点击坐标。
3. 步骤 12：对 `[280,16]` 点击，记 `hit:true`；步骤 14 AX 显示多出 `Name: Where:` / `pop up button Documents` / `text field tag editor`，即标题栏文档操作（重命名）浮层被打开——误触。
4. 步骤 16：`pressKey("Escape")` 成功收起该浮层，AX 恢复原树（证明 Escape 在该场景可投递）。
5. 步骤 18/20：点开 File 菜单成功；随后 `pressKey("Escape")` 无报错但 AX 仍是 File 菜单（`restored:false`）——同一按键在菜单场景被吞。
6. 步骤 22：改用 `performSecondaryAction(0,"Cancel")` 收起菜单，AX 回到 `standard window Untitled`，恢复成功。
7. 步骤 24/26/28：快捷键键名三次试错（`Meta+,` 报 `keyNotFound("Meta")`；`Command+,` 逗号不被接受；最终 `Command+H` 投递成功）。
8. 步骤 30/32：Finder 变为可读前台（侧证隐藏生效）；`cua.computer.launch_app` 调用报 `TypeError: ... is not a function`。
9. 步骤 36/43：改用 `performSecondaryAction(0,"Raise")` 复位，并在步骤 43 完整重做前后台切换，得 `{left_front:true,returned_front:true,error:null}`。
10. 步骤 47/49/52：建目录成功；步骤 49 apply_patch 以单行字符串传入导致 `zsh: parse error`（exit=1）；步骤 52 jq 校验通过——说明中间存在一次未被记录的成功写入。

### 4. 绕路与副作用
- 绕路类型：**命令行直接改产物（有限度）**。观测全部来自 `cua_repl` 真实探针，命令行仅用于建目录、写 JSON 报告、`jq` 校验（步骤 47、49、52）。任务文字未禁用命令行，且 CUA 侧无文件写接口，又明令「不要改它的文档」（不能借 TextEdit 存盘），因此这是可成立的交付路径，不属于用 CLI 伪造 GUI 结果。
- 未出现绕框架行为：无 AppleScript/osascript/JXA/自写点击。
- 副作用：
  1. 步骤 12 误触标题栏文档操作浮层（含 Name/Where/标签字段），有改文档名风险，步骤 16 已关闭、未留改动。
  2. 步骤 28 的 `Command+H` 使应用隐藏，与第 5 项探针语义重叠；步骤 36 Raise 复位，步骤 43 另做干净一轮。
  3. 步骤 47 `mkdir -p` 对已存在的 `mech-check`（步骤 30 桌面已见）幂等，未产生多余文件；步骤 49 失败于解析阶段，未写出半成品。
  4. 未见误改数据或触发保存/新建。

### 5. 问题与归因
1. 标题栏误触（主要操作瑕疵）
 - 标签：A4.1（操作对象/坐标偏差）。预期「点主窗口空白处一次」→ 实际点在居中的文档标题控件，打开重命名浮层（步骤 12→14）；支持原因：窗口宽 571，x=280 恰为标题中心，模型选坐标前未避开标题控件；未排除解释：该控件在 AX 中标为 `43 menu button (disabled)`，模型可能据此认为不可触发。
 - 受阻层次：模型本身。影响：在「禁止改文档」约束下引入风险与一次额外恢复步；不影响 `hit:true` 的真实性。恢复：已恢复（步骤 16）。
2. Escape 未收起 File 菜单（本案例核心机制事件）
 - 标签：E5（工具/驱动与实际效果不一致：合法调用返回成功、界面无变化）。步骤 16 证明 Escape 可投递，步骤 20 同一调用在菜单 tracking 场景无效；尚未排除「系统菜单跟踪态屏蔽合成事件」这一后端外因素。
 - 受阻层次：驱动 / Sky 后端（+ 系统菜单机制）。影响：需换 `Cancel` 二级动作恢复；同时正是任务要观测的受阻机制，被模型如实记入 `input_swallowed`。恢复：已恢复（步骤 22）。
3. 快捷键键名参数不合接口（次要）
 - 标签：A4.2。预期发送 `⌘,` → 实际两次报键名错误（步骤 24 `keyNotFound("Meta")`、步骤 26 逗号不受支持）；API 文档正文在本记录被截断，无法确认当时是否已给出键名表，故「模型凭推测取名」与「文档未提供」都未排除。
 - 受阻层次：模型本身 / 框架文档。影响：约 2 步成本；另导致最终 `shortcut.error=null` 只反映最后一次成功尝试，丢弃了前两次报错原文（与「error 是报错原文」的口径有张力，但对该次探针本身是准确的）。恢复：已恢复（步骤 28）。
4. 调用不存在的 API（次要）
 - 标签：A4.3。`cua.computer.launch_app` → `TypeError: ... is not a function`（步骤 32）。受阻层次：模型本身。影响：一次无效调用并把 error 暂存进 `fg`，后由步骤 43 重做覆盖。恢复：已恢复。
5. apply_patch 调用形式错误（次要）
 - 标签：A4.3。把补丁正文当单行 shell 字符串传入，`zsh:53: parse error`（步骤 49，exit=1），步骤 50 自述需用 heredoc。受阻层次：模型本身。影响：一次失败写入；未产生残留文件。恢复：已恢复（步骤 52 证明文件已存在且通过校验）。
6. 证据缺口
 - 标签：Q5。成功写入 JSON 的那次命令未出现在记录（步骤 49 失败 → 步骤 52 已能读到文件）；步骤 49 补丁正文与多处 AX 输出被抽取截断。受阻层次：记录/归档。影响：只能确认 jq 实际检查的那几项（app 值、五个 attempted、mechanisms 键数为 10），无法逐字段核验各探针子字段与十格 evidence 文本。恢复：不适用。
7. 前台回归核验强度不足（次要，存争议）
 - 标签：倾向 A7.1 但依据不足。`returned_front:true` 仅以 Raise 无报错 + TextEdit AX 可读支撑（步骤 36、43），模型自己三次承认这不等于前台（步骤 33/37/41）；而 `cua.getState` 无前台字段（步骤 38）、`getScreenshot` 只给单应用窗口（步骤 34、40），当时是否存在更强可执行核验无法确定。影响：该布尔值为推断而非直接观测。恢复：无法判断。

### 6. 能否收为训练轨迹
**遮掉第 32 步与第 49 步后收**（可选再遮第 7 步）。理由：
- 保留：步骤 3–6、12–22、43–45、52 是高价值内容——真实 AX 读取、误触后用 Escape 恢复、菜单按键被吞后改用二级动作 Cancel 恢复、前后台切换重做、以及用 jq 自校验交付格式，属于「环境/驱动问题被模型合理绕过」。
- 遮掉：步骤 32（臆造 `cua.computer.launch_app`）、步骤 49（apply_patch 调用形式错误）属模型自身调用错误且无探测价值；步骤 7 的 `emitImage` 误用可一并遮。
- 步骤 12 的误触建议保留（含完整识别+恢复链），但如作为示范轨迹，宜在注释中标明「应避开标题栏控件选点」。
- 不属「靠绕框架完成」的不当正例：GUI 观测全部来自 cua_repl；命令行只用于写报告文件与校验，而写文件无 CUA 接口替代。
- 附带限制：成功写文件的那一步缺失（Q5），若要作完整轨迹需补全该步，否则写盘环节不可学。

### 7. 值得注意
- 驱动/后端：同一 `pressKey("Escape")` 在浮层场景有效（步骤 16）、在打开的菜单场景静默无效（步骤 20），而调用仍返回成功——这是 Sky 后端在菜单 tracking 态下的「报喜不报忧」型行为，正好是本题要考的受阻机制，建议作为标准样例固定下来。
- 后端能力缺口：无全屏/合成器级截图（步骤 34、40 只拿到单应用表面）、`cua.getState` 无前台标识（步骤 38），使 `foreground_switch` 这类前台判定缺少可直接验证的指示器；出题方若要严格评 `returned_front`，宜明确可接受的证据口径，或补一个前台查询接口。
- 键名契约不透明：`Meta` 不认、`Command+,` 逗号不认（步骤 24、26），建议 API 文档给出显式键名表与标点写法。
- 机制分类重叠需在评分口径上澄清：同一「Escape 返回成功但菜单未关」观察同时可支持 `input_swallowed`、`silent_noop`、`false_success`；模型只标了 `input_swallowed`（步骤 52 `mechanisms_seen` 仅此一项）。若 rubric 期望多标或指定唯一归类，应在题面写明。
- 模型能力亮点：误触后主动识别并恢复、失败后换路（Cancel / Raise）、最后用 `jq -e` 自检交付格式，交付前自验意识较好。

### 8. 不确定项
1. 实际写入文件的命令缺失（步骤 49 失败 → 步骤 52 已可读），文件最终完整内容无法逐字核验；只能确认 jq 实查的 app 值、五个 attempted、mechanisms 键数。
2. 十格机制中仅 default_trap / permission_wall / state_desync / side_effect_exit 的 evidence 文本可见（步骤 49 截断前片段），其余 6 格 `seen`/`evidence` 是否非空、是否基于实际观察，无法确认。
3. `roles` 的 18 项为手写（步骤 45），AX 树中段被抽取截断，是否全部对应实读内容（如「text alignment」「color well」「combo box」）无法核验；若其中有未实读项，则可能触及 A6.3，但现有材料不足以认定。
4. `returned_front:true` 与 `left_front:true` 的强度：后端是否当时存在更可靠的前台判据未知，故第 5 项探针是否属「核验不足」保留未定。
5. 步骤 26 的完整返回被截断，`Command+,` 失败的确切报错原文不可见，只能依步骤 27 自述推断为逗号/键名不受支持。
6. AX 中 `43 menu button (disabled) document actions` 标为 disabled 却因点击产生浮层，属后端 AX 状态上报与实际可交互性的可能不一致；证据不足以判定是 AX 快照陈旧（E5）还是命中了另一控件（标题文本/弹出按钮）。
7. 本阶段无 Judge 结论或既有报告可对照，故不作评分复核、不补造判定；若后续存在 Judge 认定失败，建议优先核对第 2 节中「部分无法确认」的文件内容项与第 5 节 Q5。
