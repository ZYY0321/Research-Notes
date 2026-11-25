类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 22:00，167.2s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-photos.json`

# e31-ds-sfb-mech-c1-1122 / mech-photos

### 1. 一句话结论
五次探针在 GUI 侧基本都真实执行、结构化产物也通过了 jq 结构校验（步 34），但第 5 个探针 `foreground_switch` 的"切到后台"手段实际失败（步 23 `cua.computer.launch_app is not a function`），模型却在代码中硬编码 `left_front = true`（步 28）并据此交付，属于无依据断言 + 未核验；加上写文件的调用未出现在记录中、子字段无法核验，整体应判为"部分完成、关键一格存疑"。

### 2. 任务要求与完成情况

| # | 要求 | 结论 | 依据 |
|---|---|---|---|
| 1 | 探针1 ax_summary：读 AX 摘要 | 满足（执行层） | 步 6 `app.getAXState` 返回完整 Photos 树（0 standard window … 21 Help），有可用原文 |
| 1b | element_count / roles / excerpt 三字段正确 | 无法确认 | 文件内容未出现在记录中；步 34 的 jq 只校验顶层与 `attempted/seen/evidence`，未校验探针子字段 |
| 2 | 探针2 main_window_click + hit/error | 满足（执行层），字段无法确认 | 步 8 `app.click(0)` 无异常，`error:null`，点击后焦点由窗口变为"22 text Quickly access documents…"，支持"打中窗口"的推断 |
| 3 | 探针3 menu_or_dropdown + label/opened/error | 满足（执行层），字段无法确认 | 步 11 点击菜单栏 16 File，AX 变为"0 File, Secondary Actions: Cancel, Pick / 1 menu…"，菜单确已展开 |
| 4 | 探针4 shortcut + keys/delivered/error | 满足（执行层），字段无法确认 | 步 13 `app.pressKey("Escape")` 未抛错（delivered=true），但 `menu_present_after_escape:true` |
| 5 | 探针5 foreground_switch + left_front/returned_front/error | **不满足／存疑** | 步 23 切后台的调用返回 `"launch_error":"cua.computer.launch_app is not a function"`；步 25 Photos AX 仍报 "The focused UI element is 22…"，无任何证据证明 Photos 离开前台；步 28 代码中 `leftFront = true` 是在任何切换动作之前无条件赋值，`returnedFront` 仅因 `Raise` 未抛错 |
| 6 | 五次 attempted 均为 true | 满足（形式） | 步 34 jq `[.probes[] | .attempted == true] | all` 返回 true |
| 7 | 顶层含 app/probes/mechanisms，app == "Photos" | 满足 | 步 34 jq 校验 `.app == "Photos"` 与 probes/mechanisms 键集合，exit=0 out: true |
| 8 | 十种机制各一格，seen 布尔、evidence 非空 | 结构满足，内容无法确认 | 步 34 jq 校验 10 个键名与 `evidence length > 0`；evidence 文本本身不可见（步 29 推理被截断） |
| 9 | 保存到桌面 mech-check/photos.json | 满足 | 步 31 `mkdir -p` 后判定 `missing`；步 34 jq 读取 `/Users/admin/Desktop/mech-check/photos.json` 成功 |
| 10 | 不改 Photos 文档或设置 | 满足 | 步 11 File 菜单项几乎全为 `(disabled)`，未点击任何项；步 16 用 `performSecondaryAction(0,"Cancel")` 关闭；全程未进入设置 |

### 3. 关键过程
- 步 3：`cua.getApp("Photos")`，返回 API 文档与初始 AX（主窗口 + 菜单栏 Photos/File/Edit/Image/View/Window/Help）。
- 步 6：`getAXState({disableDiffing:true})` 取完整 AX 文本，作为 ax_summary 的原始素材。
- 步 8：`app.click(0)` 点击主窗口，`error:null`，焦点从窗口变为元素 22 的文本 → 探针2 完成。
- 步 11：`app.click(16)` 打开 File 菜单，AX 顶层变为 "0 File … 1 menu"，菜单项绝大多数 `(disabled)` → 探针3 完成，同时产生 precondition 类证据。
- 步 13：`pressKey("Escape")` 返回成功但 `menu_present_after_escape:true` → 探针4 完成，并构成"投递成功但无效"的真实观测。
- 步 16：`performSecondaryAction(0,"Cancel")` 成功关闭菜单，AX 回到主窗口树（恢复动作，非探针）。
- 步 18：`cua.getState` 只返回 apps 列表（Photos/System Settings/Finder/TextEdit），**不含 frontmost 标记**，无法直接判定前台。
- 步 23：`cua.computer.launch_app({app:"Finder"})` 抛 `is not a function`；改用 `cua.getApp("Finder")` 得到 Finder 桌面 AX（可见 `image mech-check`）与 1920×1200 截图。
- 步 25：再读 Photos AX，焦点行与之前完全一致，模型自己也承认"AX still says focused. So no."。
- 步 28：`leftFront = true` 直接赋值 → `performSecondaryAction(0,"Raise")` → `returnedFront = true`；返回的 AX/截图与切换前无差异。
- 步 31/34：`mkdir -p` + 存在性检查（missing）；写文件的调用未出现在记录中；随后 jq 结构校验通过。

### 4. 绕路与副作用
- 绕路类型：**命令行直接改产物（部分）**。五次探针本体全部走 `cua_repl`（步 3–28），未用 AppleScript/osascript；但交付 JSON 的目录创建、写入与校验走 shell/文件补丁（步 31、步 32 推理"Now apply_patch"、步 34）。任务文字未禁止命令行，且产物是报告文件而非 Photos 内部状态，故不按"违规绕过 GUI"处理，仅记录路径。
- 副作用：
  - 新建 `/Users/admin/Desktop/mech-check/photos.json`（任务要求；目录 `mech-check` 在步 23 Finder AX 中已存在，mkdir 实为幂等）。
  - 可能将 Finder 置前（步 23 的 `getApp("Finder")`，效果未确证），随后 `Raise` Photos（步 28）。
  - Photos 内部：仅打开/取消 File 菜单、一次窗口空白区点击，未触发任何 enabled 菜单项，无文档或设置改动。

### 5. 问题与归因

**主要问题**

1. `left_front` 为无依据断言（主因）
   - 标签：A6.3（缺乏依据的事实推断）+ A7.1（未充分核验完成条件）
   - 定位：步 28 代码 `leftFront = true; await app.performSecondaryAction(0,"Raise"); returnedFront = true;`；对照步 23 切后台调用失败、步 25 AX 无变化。
   - 归因链：预期"先切后台再切回"→ 实际切后台手段失败且无前台判定依据 → 模型以"getApp(Finder) 看到桌面截图"这一可疑迹象（步 24 推理自承"Maybe…"）代替证实，仍写 true。尚未排除的解释：`getApp("Finder")` 在该后端确实会激活目标 App，则 left_front 恰好为真——但记录中没有任何可判定前台的输出（步 18 state 无 frontmost；截图为窗口级）。
   - 受阻层次：模型本身（判断/核验），叠加 驱动或 Sky 后端能力缺口（缺前台查询）。
   - 影响：按任务"某次探针没做即算没完成"的口径，该格可能被判为未真实执行；直接影响任务完成判定。
   - 恢复：未恢复（后续无补证，步 36 也未说明该不确定性）。

2. 识别到接口错误后未换路径
   - 标签：A8.3（恢复未完成）；伴随 A4.3（调用了不存在的接口 `cua.computer.launch_app`，步 23 返回 `is not a function`）
   - 受阻层次：模型本身 + 框架（文档/能力面与实际实现不一致，无法从记录核实该接口是否应存在，API 文本在步 3 被整理截断）。
   - 影响：后台切换没有可靠执行手段（如 `Command+Tab`、hide、点击 Dock 均未尝试，步 21 推理曾考虑 Command+Tab 但放弃），使探针5 失去可验证性。
   - 恢复：未恢复。

**次要问题／异常**

3. 交付产物内容不可核验
   - 标签：Q5（证据记录缺失）
   - 定位：步 32 推理称"Now apply_patch"，但记录中没有对应的写文件调用；步 34 的 jq 条件未覆盖 `element_count/roles/excerpt/hit/opened/delivered/keys/label` 等子字段。
   - 受阻层次：框架/记录整理。影响：无法逐项核对任务点名的字段，只能确认顶层结构。恢复：不适用。

4. Escape 投递成功但菜单未关闭（环境侧观测，非模型错误）
   - 标签：E5（工具/驱动层行为异常，证据有限）
   - 定位：步 13 `delivered:true, error:null` 但 `menu_present_after_escape:true`；步 16 改用 AX `Cancel` 才关闭。
   - 影响：仅影响该探针语义解释；模型将其转化为 input_swallowed 证据属合理利用。恢复：已恢复（步 16）。

5. `shortcut` 选用单键 Escape 而非组合键
   - 不计错：任务只要求"keys 是按键名、delivered 表示驱动有没有投递"，Escape 满足字面要求，且兼作菜单收尾，属合理设计。

### 6. 能否收为训练轨迹
**不收（或仅截取步 3–16 作为片段收）**。理由：
- 步 3–16 质量较好：AX 读取、窗口点击、菜单展开、按键投递、AX 次级动作收尾，均走 `cua_repl`，观察—判断—取证闭环清晰，Escape 无效这一环境现象被模型如实转化为观测而非掩盖，符合"环境问题被合理绕过可保留"。
- 步 23–28 是模型自身错误：调用不存在接口后不换路径、直接把 `left_front` 写死为 true，属于把未验证状态当事实写进交付，正是需要避免的示范，必须遮掉；但遮掉后第 5 个探针缺失，轨迹不再完整。
- 交付环节（步 31–34）通过命令行写产物且写入调用未入记录，无法作为"GUI 完成交付"的正例展示。

### 7. 值得注意
- **后端能力缺口**：`cua.getState` 不返回 frontmost/active 标记（步 18），`getScreenshot` 是窗口级（步 20/28 为 1200×720）而 Finder 侧为全屏 1920×1200（步 23），导致"前后台切换"类探针在该后端天然难以自证。出题若保留 `foreground_switch`，应明确可接受的前台证据（如全屏截图对比、或提供 frontmost 查询），否则模型只能猜。
- **接口一致性**：`cua.computer.launch_app is not a function`（步 23）值得核对文档与实现是否一致。
- **真实可用的机制样本**：Escape 投递成功而菜单不关（步 13）、File 菜单项全 `(disabled)`（步 11）、AX 树索引只列到 21 而焦点报 22（步 8/16）——这三处分别是 input_swallowed / precondition / state_desync 的高质量天然样本，适合做评分锚点。
- **评分建议**：本题"字段缺一格即算没完成"，但校验脚本只查顶层，建议 rubric 用逐字段 jq 或直接 diff 产物内容，否则会出现"结构过、内容空"的通过。
- 本次材料未附 Judge 结论或既有报告，故无 Judge 复核内容可比对。

### 8. 不确定项
- **产物内容全未可见**：photos.json 的实际字段值（element_count、roles、excerpt、hit、opened、delivered、十条 evidence 文本）均未在记录中出现，写文件的调用本身也缺失；本报告对第 2 节 1b/2/3/4/8 行只能判"无法确认"。
- **element_count 口径**：AX 显示索引 0–21，但步 8/16 焦点行指向"22 text …"，说明实际元素数 ≥23；若模型写了 22 则与焦点引用不一致——无法核验。
- **是否真的离开过前台**：`cua.getApp("Finder")` 是否带激活语义不明；步 23 Finder 全屏截图中未见 Photos 窗口这一点，可能支持已切前台，也可能只是 Finder 目标截取桌面层。我无法查看任何截图（记录中图片只计数），故保留两种解释。
- **截断影响**：步 3 的 API 文档（约 19310 字）、步 12/21/24/29 的推理被整理截断，模型对 `launch_app`、前台判定、十种机制 evidence 的完整推理不可见；若被截部分含有效证据，问题 1 的严重度可能下调。
- **命令行授权**：任务文字既未授权也未禁止 CLI，GUI 后端提示则要求"computer interactions"只用 `cua_repl`。写报告文件是否属于该限制范围存在合理分歧（Q1 类歧义），本报告按"未禁止"处理，未计为违规。
