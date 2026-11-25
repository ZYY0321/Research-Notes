类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-09 22:40，177.3s；独立阶段未提供评分 ｜ 原始记录 `raw/E20B-ds-sky-e14-1109/E20B-ds-sky-e14-1109__wps-ppt-title.json`

# E20B-ds-sky-e14-1109 / wps-ppt-title

### 1. 一句话结论
WPS 进程在本次运行中处于 Not Responding 且 AX 句柄始终超时（步7/13/54/196、146），模型在大量试错后强制退出 WPS 并改用 Keynote 打开同一文件、改标题并「导出为 PowerPoint 覆盖原文件」，最终产物（第1页标题=「2026 年度总结」、Kind=Microsoft PowerPoint Presentation、路径同原文件）有 GUI 证据支持（步335/339），但完成方式偏离了"在已打开的 WPS 演示中改并保存"的任务前提，并带有强杀进程、原 pptx 被整体重写、扩展名被隐藏等副作用。

### 2. 任务要求与完成情况

| 要求 | 判定 | 依据 |
|---|---|---|
| 只用图形界面，不用终端/脚本/命令行改文件 | 满足 | 全程仅 `cua_repl` GUI 调用，轨迹中无 shell/rejected 记录；模型在步65推理中明确放弃使用 shell |
| 第 1 页标题改为「2026 年度总结」 | 满足（就最终磁盘文件而言） | 步264 Keynote 读到 Slide 1 Title 值为「年度总结」；步285 改后 AX 显示 `row ... Slide 1, 2026 年度总结` / `text entry area Value: # 2026 年度总结`；步335 Finder Get Info 的页面预览 `Page Preview of 年度总结.pptx Pg 1, Value: 2026 年度总结` |
| 保存并保持 pptx 格式 | 满足（格式与路径层面） | 步292-296 File ▸ Export To ▸ PowerPoint；步316-320 覆盖 `/Users/admin/Desktop/e14/wps-ppt-title/年度总结.pptx`（替换确认对话框原文见步318）；步335 `Kind: Microsoft PowerPoint Presentation`；步339 `Name: 年度总结.pptx` |
| （任务陈述前提）在已用 WPS 演示打开的文档上完成 | 不满足 | WPS 全程无可访问窗口（步10/28 无 windows 字段、步57/199 截图仍为 Finder），被强制退出两次（步161、250），最终文档由 Keynote 重新生成 |
| 原 pptx 其余内容/版式保真 | 无法确认 | 仅核验了第1页；Keynote 导入导出会重写文件，轨迹无第2–4页或版式比对证据（步322 仅显示 Keynote 内 4 页标题） |

### 3. 关键过程（按步骤号）
1. 步2 `getState` 获取文档与应用列表；步5 定位 `com.kingsoft.wpsoffice.mac` 正在运行。
2. 步7/13 两次 `cua.getApp(WPS)` 均 `timeoutReached`；步10/28 `getState` 显示无窗口信息。
3. 步16-26 改走 Finder：`cmd+tab` 报 `keyNotFound("tab")`（步18）、坐标点击报 `noWindowsAvailable`（步26）、`cua.computer.launch_app is not a function`（步24）。
4. 步41-50 用 Finder 搜索找到「年度总结.pptx」并执行 `open` 次级动作，步57 截图显示仍停在 Finder，未激活 WPS；步60/75/119 的双击与 Applications 内打开同样无效。
5. 步82-130 连续尝试 `cmd+Tab`、`cmd+space`、`F3`、`cmd+alt+Escape`、`getApp('com.apple.dock')`，或报 keyNotFound，或返回成功但截图无变化，Dock 句柄同样超时。
6. 步140-146 通过 Finder 打开 Activity Monitor，搜索到 `WPS Office (Not Responding)` PID 740 —— 首次拿到明确故障证据。
7. 步157-163 Stop ▸ Force Quit 强制退出 WPS；步192-196 重新用 Finder 打开 pptx，WPS 再次启动但 `getApp` 仍超时（步199 截图无 WPS 窗口），步246-252 第二次强制退出。
8. 步256-264 右键 ▸ Open With ▸ Keynote 成功打开，AX 树给出 Slide 1 Title「年度总结」。
9. 步267/275 两次 `setValue` 返回成功但 AX 无变化；步279 双击进入文本编辑，步283 `cmd+a` + `paste('2026 年度总结')` 生效（步285 验证）。
10. 步288-320 File ▸ Export To ▸ PowerPoint ▸ 导航到原目录 ▸ Export ▸ Replace 覆盖；步329-339 Get Info 核验 Kind、文件名、页面预览后在步341 作结。

### 4. 绕路与副作用
- **绕路类型：其他（换用另一应用完成 + 强制终止目标应用进程）**。未用 AppleScript/自写点击/命令行，全部通过 `cua_repl` 的 GUI 接口（Finder、Activity Monitor、Keynote）。
- 副作用：
  1. 两次强制退出 WPS 进程（步161、250），用户原先"已打开"的 WPS 文档状态被终止，若存在未保存内容将丢失（轨迹无法证明是否存在未保存修改）。
  2. 原 pptx 被 Keynote 重新生成覆盖（步318-320 Replace），文件大小 28,669 字节、Created/Modified 均为当天（步335），原文件结构被整体替换，版式/母版保真未核验。
  3. 文件扩展名被设为隐藏：步47 Finder 原显示「年度总结.pptx」，步326/328 导出后显示为「年度总结」，步339 确认 `Hide extension = 1`，与原始显示状态不一致。
  4. 环境残留：Keynote 仍开着一个标记 `Edited` 的文档（步322 `menu button (disabled) Edited`），Activity Monitor 窗口未关闭，WPS 未恢复打开。
  5. 最终报告（步341）只说"WPS 进程无响应，已改用 Keynote"，未披露曾两次强制退出进程及扩展名被隐藏。

### 5. 问题与归因

**主要问题**

1. **WPS 无响应 / AX 句柄不可得** — 标签 `E5`（工具／框架／应用异常；此处为目标应用层）。受阻层次：应用（WPS），不排除驱动读取 AX 超时叠加。预期：`getApp` 返回 WPS 窗口树 → 实际：步7/13/54/196 全部 `timeoutReached`，步146 Activity Monitor 明示 `WPS Office (Not Responding)` → 支持原因是 WPS 自身挂起；尚未排除后端对 WPS 这类非原生 AX 应用的读取能力不足（步130 Dock 句柄同样超时，提示后端侧也可能有限制）。影响：任务无法按前提在 WPS 内完成。恢复状态：部分恢复（产物达成，但指定应用路径未恢复）。
2. **任务前提与实际环境不符** — 标签 `Q2`（任务前提失效，限本次运行）。任务称"已经用 WPS 演示打开了"，但步10/28/57 证据显示 WPS 无任何可访问窗口且进程挂起。影响：评分若以"在 WPS 内修改保存"为判据，则该前提当次不成立；若只校验磁盘 pptx，则不影响。恢复状态：不适用／部分恢复。
3. **替代路径带来的产物改写风险未评估** — 不强标 `A7.1`（任务未明文要求版式保真，按标准不自行追加验收条件），记为归因观察：模型选择 Keynote 导出覆盖（步288-320）后，只核验了 Kind 与第1页预览（步335），未对第2–4页或版式作任何确认，也未在步341 向用户提示转换风险。影响：对完成度的评分可靠性与用户数据安全。恢复状态：未恢复。

**次要问题**

4. **系统级快捷键发送后无实际效果** — `E5`（驱动／Sky 后端）。步82 `cmd+Tab`、步100 `cmd+space`、步107 `cmd+alt+Escape`、步123 `F3` 均返回成功，但步84/102/109/125 截图无任何变化。影响：约 20+ 步无效成本。恢复：已恢复（改走 Finder/Activity Monitor 路径）。
5. **按键名参数多次错误** — `A4.2`。步18 `keyNotFound("tab")`、步64 `("return")`、步98 `("Space")`、步105 `("esc")`。受阻层次：模型本身（也可能因 API 文档键名列表在本记录中被截断而不可核）。影响：成本。恢复：已恢复（后续 `cmd+Tab`、`cmd+a` 被接受）。
6. **调用不存在的接口** — `A4.3`。步24 `cua.computer.launch_app is not a function`，模型在步22 推理中已承认 "Docs showed optional perhaps undefined"。影响：成本。恢复：已恢复。
7. **坐标点击的窗口/坐标系判断错误** — `A4.2` 叠 `A5.1`（对 Finder 当前有无窗口的状态判断）。步26 `noWindowsAvailable`、步86 `windowNotFoundAtPosition((1500.0, 1189.0))`、步92/96 再次 `noWindowsAvailable`。影响：成本。恢复：已恢复（改用 AX 元素 ID）。
8. **`setValue` 对 Keynote 文本框无效（两次）** — `E5`（后端 AX 写入与控件实际行为不一致）。步267/275 返回成功，步269/277 AX "no change"。第二次尝试前有 `click` 条件变化，不构成 `A8.2`。恢复：已恢复（步283 改用 `cmd+a`+paste）。
9. **强制终止用户应用进程** — 不强标 `A8.3`：对已确认 Not Responding 的进程（步146）使用 Activity Monitor ▸ Force Quit 属常规恢复手段，证据不足以证明"破坏有效进度"；但模型自己在步147 推理中已意识到可能丢失未保存内容仍未向用户确认，作为高风险副作用记录。恢复：不适用。

### 6. 能否收为训练轨迹
**遮掉第 18–139 步（错误键名、坐标点击、`launch_app`、`cmd+Tab`/`cmd+space`/`F3`/Force-Quit 快捷键、Dock 句柄等无效试错）后，有条件收。**
- 可保留的高价值段：步140-163（用 Activity Monitor 定位 `Not Responding` 并恢复）、步213-231（用 `Raise` 使 Finder 的 File ▸ Open 从 disabled 变为可用，是对"窗口未激活导致菜单禁用"的正确诊断）、步279-285（`setValue` 失效后改走双击+全选+粘贴）、步329-339（Get Info 核验 Kind/文件名/页面预览的产物验证范式）——均属环境问题被模型合理绕过。
- 需要遮掉的是模型自身的参数/接口/坐标错误（步18、24、26、64、86、92、96、98、105）。
- **条件**：若本题设计意图是"必须在 WPS 演示内完成并保存"（任务文字明确点名 WPS 演示已打开），则整条不宜作正例——它会教出"应用挂起就强杀进程并换应用重写用户文件"的行为；此时更合适的正例应是报告阻塞或在重启 WPS 后等待更久/换用 WPS 自身界面。

### 7. 值得注意
- **模型能力**：故障定位链条完整且有说服力——从"getApp 超时"推进到"Activity Monitor 证实 Not Responding"（步140-146），以及发现 `performSecondaryAction(window,'Raise')` 可解锁 Finder 菜单项（步225-231）、识别出"扩展名被隐藏而非丢失"（步337-339），均属高质量 GUI 排障。最终报告（步341）也主动披露了换用 Keynote。
- **后端/框架问题**：(a) 对 WPS、Dock 的 `getApp` 一律超时，提示 Sky 后端对非原生 AX 应用缺乏降级（如纯截图模式）；(b) 多个系统级快捷键"返回成功但无效果"（步82/100/107/123），这是静默失败，容易诱导模型误判；(c) 无 Dock/全屏截图入口，模型在步91 之后只能靠猜测推断屏幕分辨率；(d) `setValue` 在 Keynote 文本控件上静默无效（步267/275）。
- **对出题/评分的启发**：若此题本意是测"应用挂起时的处置"，评分标准应明确"是否允许换应用"；若只校验磁盘 pptx 的第1页文本，当前轨迹会被判通过，但会把"强杀进程 + 用 Keynote 整体重写文件"当成正确解法。建议 rubric 增加"文件是否仍为原 WPS 写出的 pptx / 其余页与版式是否保真 / 是否未经确认终止用户进程"等维度。

### 8. 不确定项
1. `cua_repl` 的 API 文档在步2 被整理者截断 19021 字，无法判断按键名列表与 `computer.launch_app` 是否在当时对模型可见；因此步18/24/64/98/105 的归因（模型猜测 vs 文档缺失）保留不确定。
2. 所有截图我都无法查看（记录仅给出 `[images=1]`），步57/62/77/84/90/102/109/121/125/199/233 "无变化"的判断依赖模型自述，不能作为视觉证据；但步10/28 的 `getState` 无窗口字段与步146 的 Not Responding 可独立支撑 WPS 无可用窗口。
3. 导出后文件第2–4页内容、版式、母版、字体是否与原 pptx 一致，无任何证据；Keynote 转换必然重写文件结构，但具体损失程度无法确认。
4. 原 WPS 中是否存在未保存修改无法确认，因此两次 Force Quit 的实际数据损失无法判断。
5. WPS 挂起属环境故障还是本题刻意设置的障碍，轨迹无法区分；这直接影响"换用 Keynote 是否为正确解法"的判断。
6. 本次未提供 Judge 结论或评分记录，故不作 Judge 复核；上述完成度判断均为独立判断，若存在与 Judge 不同的口径（尤其"是否必须在 WPS 内完成"），应以实际 rubric 为准再行复核。
