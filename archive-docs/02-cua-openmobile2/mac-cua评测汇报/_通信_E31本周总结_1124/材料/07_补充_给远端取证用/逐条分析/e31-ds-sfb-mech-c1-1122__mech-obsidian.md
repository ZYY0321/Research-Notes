类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 22:00，226.2s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-obsidian.json`

# e31-ds-sfb-mech-c1-1122 / mech-obsidian

### 1. 一句话结论
模型用 CUA 完成了全部五次探针并把 JSON 写到了 `/Users/admin/Desktop/mech-check/obsidian.json`（步骤 33、36 jq 校验 `app=="Obsidian"`、5 探针 `attempted` 全 true、`mechanisms` 10 格），任务主体大概率完成；但十个机制格的 `evidence` 内容和 `ax_summary` 字段值在轨迹中没有留证，且 `silent_noop` 这类判断建立在被 `catch(e){}` 吞掉的 Escape 调用上（步骤 13、16），证据可靠性有缺口。

### 2. 任务要求与完成情况

| 要求 | 判定 | 依据 |
|---|---|---|
| 不改 Obsidian 文档或设置 | 满足 | 全程停留在 starter 页（步骤 5/8/20/25/30 AX 均为 `app://obsidian.md/starter.html`）；菜单用 `performSecondaryAction(0,"Cancel")` 关闭而非执行命令（步骤 20）；`cmd+z` 在无文档状态发送（步骤 25） |
| 探针1 ax_summary 读 AX 摘要 | 满足（读取动作）；字段值无法确认 | 步骤 3、5 返回完整 AX 树（0–24 共 25 个节点、含 `standard window`/`HTML content`/`button`/`pop up button`/`menu bar`）；但文件内 `element_count`/`roles`/`excerpt` 实际写了什么未见 |
| 探针2 main_window_click（hit/error） | 满足 | 步骤 8 `app.click([400,600])` 无异常，写入 `{"hit":true,"error":null}` |
| 探针3 menu_or_dropdown（label/opened/error） | 满足 | 步骤 11 点 `File` 后 AX 变为 `0 File / 1 menu / 2 Open Vault… / 6 Close Window`，输出 `{"label":"File","opened":true,"error":null}` |
| 探针4 shortcut（keys/delivered/error） | 满足 | 步骤 25 `cmd+z` 输出 `{"keys":"cmd+z","delivered":true,"error":null}`（步骤 23 `Meta+z` 报 `keyNotFound("Meta")` 后换键名） |
| 探针5 foreground_switch（left_front/returned_front/error） | 满足（returned 证据充分，left 证据偏弱） | 步骤 28 `getApp("Finder")` 返回 `Window: "Desktop", App: Finder`；步骤 30 回到 `Window: "Obsidian"`，输出 `{"left_front":true,"returned_front":true,"error":null}`。`getApp` 是否等于“切到后台”在工具说明中未明示 |
| 五次 attempted 都为 true | 满足 | 步骤 36 `[.probes[] | .attempted] | all` → `true` |
| 十种机制各一格、seen + evidence 不为空 | 无法确认 | 步骤 36 只校验了 `mechanisms | length == 10` 与 10 个键名；evidence 是否非空、内容是否为“实际观察到的一句”未校验，文件内容未打印 |
| 顶层 app/probes/mechanisms，app 为「Obsidian」 | 满足 | 步骤 36 jq 输出 `"app": "Obsidian"` 与 5 个 probe 键、10 个 mechanism 键 |
| 保存到桌面 mech-check/obsidian.json | 满足 | 步骤 33 建目录成功；步骤 36 jq 对该绝对路径读取成功 |

### 3. 关键过程
1. 步骤 3：`cua.getApp("Obsidian")` 返回 starter 页 AX 树（`Version 1.12.7`、`Quick start`/`Create`/`Open`/`Sign in`、`pop up button English`、菜单栏 19–24）——确认无 vault 打开。
2. 步骤 5：`getAXStateAndScreenshot` 取状态+2 张截图（800×650），作为 ax_summary 素材。
3. 步骤 8：点击窗口空白 `[400,600]`，状态不变，记录 `hit:true`。
4. 步骤 11：点击元素 20（`File`），AX 切到菜单树，`opened:true`。
5. 步骤 13：`pressKey("Escape")` 包在 `try{...}catch(e){}` 中且未打印异常；AX 仍为 File 菜单。
6. 步骤 16：再点 `[400,620]` 仍未收起菜单，异常同样被静默吞掉。
7. 步骤 18：再次 `app.click(20)` → `Computer Use server error -10005: 20 is an invalid element ID`（菜单打开后索引已重排）。
8. 步骤 20：`performSecondaryAction(0,"Cancel")` 成功关闭菜单，状态回到 starter 页。
9. 步骤 23→25：`Meta+z` 报 `keyNotFound("Meta")`，改 `cmd+z` 投递成功。
10. 步骤 28→30：`getApp("Finder")`（Desktop/Finder，桌面上可见 `mech-check` 图标）→ `getApp("Obsidian")` + 点击 `[700,80]` 回前台；步骤 33/36 建目录、写文件并 jq 校验。

### 4. 绕路与副作用
- 绕路类型：**无**（五次探针全部经 `cua_repl` 完成；仅产物落盘用 `/bin/zsh -lc mkdir -p` 与文件写入+`jq` 校验，属正常交付手段，任务未限制命令行，且写文件不是 UI 交互）。
- 副作用：未见误改数据或误触功能——菜单以 `Cancel` 退出未执行任何项（步骤 20）；三次空白点击后状态仍为 starter 页（步骤 8/16/30）；`cmd+z` 无文档可改（步骤 25）。桌面 `mech-check` 目录为任务要求路径，且步骤 28 显示该图标此前已存在，`mkdir -p` 无额外影响。

### 5. 问题与归因

**主要问题 1：机制格判断所依赖的关键反馈被自己吞掉，未排除驱动键名不支持这一解释**
- 标签：A7.1（未充分核验）；伴随 A4.3（调用方式：`catch(e){}` 不输出异常，使“应用无响应”和“驱动拒绝按键”不可区分）
- 定位：步骤 13 `try { await app.pressKey("Escape"); } catch(e) {}`；步骤 16 同样写法；步骤 14 reasoning 自述 “Could be key naming issue or app pressKey sends…”；步骤 21 reasoning “Escape did nothing … input_swallowed maybe seen? … We need evidence exact”；步骤 31 reasoning 可见片段显示最终按 `silent_noop` 为 true 处理
- 受阻层次：模型本身（观测方法）；是否同时存在驱动键名契约问题（对比步骤 23 `keyNotFound("Meta")`）未知
- 影响：不影响探针 1–5 的交付，但影响 `silent_noop`/`input_swallowed` 两格 evidence 的可信度与评分可靠性
- 恢复：未恢复（全程未用 `esc` 等合法键名复测，也未打印 Escape 的返回/异常）

**主要问题 2：产物内容缺少可核验记录，完成声明略超已验证范围**
- 标签：Q5（证据记录缺失）；A7.4 轻度（步骤 38 声称“10 种受阻机制均有 `seen` 和 `evidence`”，而步骤 36 的 jq 只验证了键数与键名，未验证 evidence 非空）
- 定位：步骤 34–35 仅有 reasoning 提到要 `apply_patch`，记录中没有写文件调用本身；步骤 36 jq 条件为 `.app=="Obsidian" and (.probes|length==5) and ([.probes[]|.attempted]|all) and (.mechanisms|length==10)`
- 受阻层次：框架/记录整理（写入调用未登记）+ 模型本身（校验口径不足）
- 影响：分析者无法核验 `ax_summary` 的 `element_count`/`roles`/`excerpt`、各机制 evidence 文本；证据可信度下降，不等于任务未完成
- 恢复：部分恢复（jq 验了结构层，未验内容层）

**次要问题 3：沿用菜单打开前的元素索引**
- 标签：A5.3（沿用过期引用）
- 定位：步骤 17 reasoning 已看到新树 `0 File / 1 menu …`，仍执行步骤 18 `app.click(20)` → `-10005: 20 is an invalid element ID`
- 受阻层次：模型本身；该报错是驱动按契约拒绝，不计 E5
- 影响：1 次无效调用的成本，无状态破坏
- 恢复：已恢复（步骤 20 `Cancel` 成功关闭菜单）

**次要问题 4：`Meta+z` 键名被拒**
- 标签：不计错（A4.2 的“首次合理试探”排除项）；记录为观察
- 定位：步骤 21 reasoning “The docs don't specify”，步骤 23 `keyNotFound("Meta")`，步骤 25 立即改 `cmd+z` 成功
- 受阻层次：驱动/Sky 后端键名契约文档不足
- 影响：一步成本；最终 `keys` 字段为真实成功投递的 `cmd+z`，合规
- 恢复：已恢复

### 6. 能否收为训练轨迹
**遮掉第 17–18 步后收。** 理由：
- 步骤 1–16、19–38 展示了合规的探针设计（只读 AX、空白点击、菜单用 `Cancel` 退出、无文档时发 `cmd+z`）、遇 `keyNotFound` 的正确换键恢复（步骤 23→25）、以及产物结构自检（步骤 36），属可保留的正面示例。
- 步骤 17–18 是模型自身错误操作（明知 AX 已重排仍用旧索引 20），应遮掉。
- 步骤 13、16 的 `catch(e){}` 静默吞异常是不良观测范式，若保留建议在训练标注中明确标记为反例写法；若按“模型自身错误应遮”的严格口径，可一并遮掉这两步的代码片段。
- 不属于“绕框架/命令行直接改产物”的不当正例：探针均由 `cua_repl` 执行，命令行只用于建目录、写交付文件和校验。

### 7. 值得注意
- 模型能力：对“菜单打开后 AX 索引重排”的恢复路径（改用 `performSecondaryAction(0,"Cancel")`，步骤 20）处理得体，没有去点 `Close Window`/`Close All` 这类破坏性菜单项，符合“不改文档/设置”的约束。
- 驱动/后端：`pressKey` 键名空间未在工具说明中给出，`Meta+` 直接 `keyNotFound`（步骤 23）；菜单打开状态下窗口内坐标点击未能收起菜单（步骤 16），这两点都容易让 agent 把驱动限制误读成“应用静默无效”。
- 对出题/评分的启发：本题要求 evidence “不要空着”，但没有要求 agent 打印最终文件内容，导致十个机制格无法离线复核。建议 rubric 或任务文字要求最后 `cat`/`jq .` 输出完整 JSON，并要求 `mechanisms[*].evidence` 必须引用一次具体调用返回（如报错原文），否则 `permission_wall=true`（仅因 starter 页存在 `Sign in` 按钮，步骤 3）这类“界面上看到墙，但未实际撞墙”的判定会难以裁定。

### 8. 不确定项
1. 文件实际内容未见：`ax_summary` 的 `element_count`（推测为 25，对应步骤 5 的节点 0–24）、`roles` 列表、`excerpt` 原文，以及 10 条 evidence 文本均无法核验（写入调用未登记，步骤 36 jq 未打印内容）。若 evidence 有空串或 `roles` 含未出现的 role，则会由“满足”转为不满足。
2. 步骤 37 reasoning 自述 “Roles include menu item inferred. Fine.” 提示 `roles` 可能含推断而非“实际看到的 role”（AX 文本中菜单项行如 `2 Open Vault…, ID: itemSelected:` 并未标出 role 词）。这只是证据支持的怀疑，不能据此断定 A6.3。
3. `pressKey("Escape")` 是否抛出 `keyNotFound` 无法判断（步骤 13 异常被吞），因此 `silent_noop` 究竟是应用侧静默无效、还是驱动未投递，机制未知。
4. `left_front:true` 依据 `getApp("Finder")` 返回 Finder/Desktop 状态（步骤 28），但 `getApp` 是否必然把目标应用置前、Obsidian 是否真的退出前台，工具说明未明确，属弱证据。
5. 步骤 6、21、31 的 reasoning 有大段抽取截断（合计约 1.5 万字以上被整理省略），模型对十个机制 seen 值的完整判定理由我只能看到片段（如 `…ssion_wall true (Sync sign-in)`、`state_desync false`、`side_effect_exit false`），这是记录整理方式所致，不构成框架异常。
6. 步骤 8/16/30 的点击坐标是否落在空白区，仅由“AX 状态未变”间接支持；截图我无法查看，无法排除点击命中了非交互文本。
