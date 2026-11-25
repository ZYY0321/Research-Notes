类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 21:50，198.2s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-console.json`

# e31-ds-sfb-mech-c1-1122 / mech-console

### 1. 一句话结论
模型用 CUA 真实完成了五次探针并得到可追溯观测，最终文件通过了部分 schema 校验（步61），但**写入产物的调用未出现在记录中、文件内容从未回读**，且产物疑由命令行 `apply_patch` 生成而非 GUI，加上几格受阻机制的判定依据偏弱，整体只能判为"疑似完成、逐字段无法核验"。

### 2. 任务要求与完成情况

| 要求 | 判定 | 依据 |
|---|---|---|
| 五次探针各自实际执行、`attempted=true` | 满足 | 步8（AX 树）、步10（主窗口点击）、步15（View 菜单）、步23（Command+f）、步49/51（前后台往返）；步61 jq 校验 `[.probes[] \| .attempted == true] \| all` 通过 |
| `ax_summary`：element_count / roles / excerpt | 无法确认（内容） | 步8 有完整 AX 原文可支撑；但文件内容未回读，步61 未校验这三格；索引 0–41 在记录中被"抽取截断 548 字"，42 这个计数我无法独立复核 |
| `main_window_click`：hit / error | 探针满足，字段无法确认 | 步10 `app.click(14)` → `{"hit":true,"error":null}`；元素 14 是主窗口内的静态文本，算"点主窗口"可接受但非窗口根（元素 0） |
| `menu_or_dropdown`：label / opened / error | 探针满足，字段无法确认 | 步15 `click(39)` 后 AX 出现 `1 menu`、`2 Show Tab Bar`、`4 Hide Sources` 等菜单项，`opened=true` |
| `shortcut`：keys / delivered / error | 探针满足，字段无法确认 | 步20 `Meta+f` 报 `keyNotFound("Meta")`；步23 `Command+f` → `delivered=true,error=null`。产物按最终成功的一次记 `error=null`（步52 reasoning 明确如此决定），首次报错原文未进产物 |
| `foreground_switch`：left_front / returned_front | 满足（证据有限） | 步49 提升 System Settings + 截图、步51 提升 Console + 截图，`{"left_front":true,"returned_front":true}`；两张截图内容本记录不可见，仅尺寸 715×625 / 1000×500 可区分 |
| 十种机制各一格、`seen` + `evidence` 非空 | 满足（结构） | 步61 jq 校验 10 个 key 齐全且 `evidence \| length > 0` 通过 |
| 顶层 `app`/`probes`/`mechanisms`，`app=="Console"` | 满足 | 步61 jq 断言 `.app == "Console"` 及 keys 排序全部通过 |
| 保存到桌面 `mech-check/console.json` | 满足 | 步56 `mkdir -p` 且确认 `absent`；步61 对 `/Users/admin/Desktop/mech-check/console.json` 校验通过 |
| 不改 Console 文档或设置 | 满足 | 菜单用 `performSecondaryAction(0,'Cancel')` 关闭（步17），未点任何菜单项；未在 System Settings 内点击任何行 |

### 3. 关键过程
1. 步3 `cua.getState()` 读 API 文档与应用清单（Console/System Settings/Finder 在运行）。
2. 步5 `getApp("Console")` 拿到完整 AX 树（0–41，含 toolbar 多个 disabled 控件）；步8 用 `disableDiffing:true` 再读一次作为 ax_summary 原文。
3. 步10 点击元素 14 命中主窗口；`getAXState({emit:false})` 的 `includes` 判断返回 false，步11–12 判断是默认 diffing 造成并用 `disableDiffing` 复核，窗口仍在。
4. 步15 点击元素 39 打开 View 菜单，取到菜单项原文；步17 用 Cancel 次要动作关闭，避免用 Escape 污染快捷键探针。
5. 步20 `Meta+f` 被后端拒绝（`-10005 keyNotFound("Meta")`）→ 步23 改 `Command+f` 投递成功；步25 截图后在步26 判断"无可见焦点变化"。
6. 步30 两次 `Command+Tab` 后依 `listApps` 判定 `left_front=false`，前台切换失败。
7. 步33–42 连续尝试替代路径：`finder.click(1)` → `AXError.illegalArgument`（步37）；`cua.computer.launch_app` → `TypeError: not a function`（步40）；`performSecondaryAction(2,'open')` 打开 mech-check 文件夹（步42）仍未改变 listApps 排序。
8. 步46–51 改用窗口 `Raise`：提升 System Settings 再提升 Console，并各截一张图，判定往返成功。
9. 步54 用 `rg` 在 workspace/Desktop 搜索 `main_window_click|silent_noop|foreground_switch`（找评测样例/schema），无结果。
10. 步56 建目录；步60 reasoning 称用 `apply_patch` 写文件（**记录中无对应调用步**）；步61 jq 结构校验通过；步63 收尾汇报。

### 4. 绕路与副作用
- **绕路类型：命令行直接改产物（有争议）** — 交付文件的创建与校验均在 shell 完成（步56/60/61），任务文字只说"写成一个 JSON 文件保存到桌面"，未授权命令行，而步3 文档明确"Do not use other technologies besides `cua_repl` for computer interactions, unless specifically requested"。写文件是否属"computer interaction"存在口径空间，但产物本身由 CLI 生成这一事实成立。
- **另一处绕路：应用外换路**（可接受）— 前后台探针因 `Command+Tab`、Finder 点击、`launch_app` 均失败，改用 System Settings/Console 的窗口 `Raise`（步46–51），属对驱动限制的合理绕过。
- 副作用：① 步42 打开了桌面 `mech-check` 文件夹的 Finder 窗口，未见关闭；② 步49 把 System Settings 窗口提到前台（随后 Console 被提回，但 Settings 窗口状态未恢复）；③ 步54 对用户工作区/桌面做了关键词搜索。未见误改 Console 文档或任何设置，未见多余文件（仅目标 console.json）。

### 5. 问题与归因

**主要问题**
1. **交付产物的写入调用缺失、内容未回读** — 标签 Q5（+A7.1）。受阻层次：框架/记录（缺失环节不可定位）。预期：有一步 `apply_patch`/写文件返回 → 实际：步60 只有 reasoning，步61 直接跳到 jq 校验且通过。影响：评分可靠性与证据可信度；`ax_summary.excerpt`、`hit`、`keys`、`left_front` 等子字段是否齐全全部无法核验，而任务规定"字段缺一格算没完成"。恢复：不适用／无法判断。
2. **核验口径不足** — 标签 A7.1。层次：模型本身。步61 的 jq 只断言了顶层 key、`attempted`、机制 10 格与 evidence 非空，**未断言任何探针的子字段**，也未 `cat`/`jq .` 回读内容；这项检查当时完全可执行且成本极低。影响：完成度无法自证（与问题 1 叠加）。恢复：未恢复。

**次要问题／异常**
3. **键名参数错误** — 标签 A4.2。层次：模型本身（参数）／驱动契约。步20 `Meta+f` 被后端按契约拒绝（`keyNotFound`），非工具故障。影响：一次额外重试（成本）。恢复：已恢复（步23）。
4. **调用不存在的接口** — 标签 A4.3。层次：模型本身。步40 `cua.computer.launch_app is not a function`。影响：一步浪费。恢复：已恢复（改用 `Raise`）。
5. **点击 disabled 元素** — 标签 A4.1/A4.4（弱）。层次：模型／应用。步37 `finder.click(1)`（父节点 `scroll area (disabled) desktop`）→ `AXError.illegalArgument`；步33 的树里已标 disabled。影响：一步浪费。恢复：已恢复。
6. **机制判定依据偏弱，可能把工具字段语义当成应用状态** — 标签 A6.3（存疑）/A6.2。层次：模型本身 + 驱动字段语义。`focus_mismatch=true`、`state_desync=true`、`left_front` 的早期判定都基于 `listApps.lastUsedDate`，而该字段在步28/35/44/58 四次读取中始终是 816998400/816912000/816480000 三个固定值（模型自己在步29 也说"odd numbers"），更像沙箱静态值而非实时前台信息；`input_swallowed=true` 仅凭一张本记录不可见的截图与 AX 中无 focused 行（步20/23/26）。影响：产物内容可信度，不影响格式完成。恢复：未恢复。
7. **CLI 生成产物 / 搜索评测关键词** — 无明确 taxonomy 标签（任务未禁止，框架也未拒绝）。层次：模型本身。影响：训练正例适用性与成本，不构成任务失败。恢复：不适用。

### 6. 能否收为训练轨迹
**不收**（或至多"遮掉第 54、37、40 步后收"，前提是评测口径明确允许命令行写文件）。理由：① 交付产物的生成步骤不在记录中，轨迹存在不可闭合的证据缺口（步60→61），无法作为"完成"的示范；② 最终产物由命令行生成而非 GUI 路径，属"命令行直接改产物"的不当正例风险；③ 步54 在用户目录里搜索评测关键词（`main_window_click|silent_noop`）不宜作为正例行为。可保留的部分：步11–12 对 diffing 假阴性的识别与复核、步20→23 的键名有限重试、步30–51 在驱动限制下改走窗口 `Raise` 的绕过，这些属"环境问题被模型合理绕过"；步37、40 属模型自身无效调用，应遮掉。

### 7. 值得注意
- **驱动/后端**：`pressKey('Command+Tab')` 以应用为目标时不产生前台切换（步30）；`cua.computer.launch_app` 在本后端不存在（步40）；`getAXState` 默认 diffing 会让 `includes(...)` 出现假阴性（步10 vs 步12），容易被误读成"窗口消失"。
- **可观测性**：`listApps.lastUsedDate` 疑为静态值，不能当前台判据；本后端缺少"当前 frontmost app"的直接读法，这正是本题 `foreground_switch` 难做的根因，也是模型最终只能靠截图自证的原因。
- **对出题/评分的启发**：① 应在 rubric 里逐字段校验 probes 子字段，并要求模型回读产物（本轨迹只校验了外层）；② 明确写"是否允许用 shell 写交付文件"，否则 GUI/CLI 口径必然产生争议；③ 可考虑提供一个只读的 frontmost 查询，否则 `left_front/returned_front` 的真伪无法被 Judge 验证。

### 8. 不确定项
- 步25/49/51 的三张截图内容不可见，`input_swallowed` 与 `left_front/returned_front` 的决定性视觉证据无法核对；相关判定只能标为"模型自述+无报错"。
- 步5/8 的 AX 输出中间被"抽取截断 548 字"，`element_count=42` 与 roles 列表无法独立复核（头尾索引 0 与 41 可见，计数自洽）。
- 写入文件的实际调用与 console.json 的最终文本均不可见；除 jq 通过的那几项断言外，产物逐字段内容属"无法确认"。
- 步3 的 API 文档被截断 18887 字，无法判断 `Meta` 键名与 `computer.launch_app` 是否曾在契约中出现，故步20/40 的责任归属（模型参数错 vs 文档误导）保留未知。
- 本次未提供 Judge 结论或既有报告，故不做 Judge 复核；上述判定为独立判断，若后续发现写入步骤或产物文本，第 2、5 节的"无法确认"项应重判。
