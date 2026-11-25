类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 22:00，354.9s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-numbers.json`

# e31-ds-sfb-mech-c1-1122 / mech-numbers

### 1. 一句话结论
轨迹在没有使用 AppleScript/osascript 等绕框架手段的前提下完成了五次探针并写出 `/Users/admin/Desktop/mech-check/numbers.json`（步骤 203 校验：`app=Numbers`、5 个探针 `attempted` 全 true、10 个机制 evidence 非空），交付结构成立；代价是大量驱动内省与反复试探（约 200 步），且 `shortcut.keys` 记为 Command+Z 与实际调用 `super+z` 的证据存在张力，另遗留一个 Finder 窗口未披露。

### 2. 任务要求与完成情况

| 要求 | 结论 | 依据 |
|---|---|---|
| 不改 Numbers 文档/设置 | 满足 | 全程只做点击标题栏(12)、开 File 菜单(14)、Cmd+Z(37)、菜单取消(35/188/192)；未点 Create/Cancel 模板、未新建文档；步骤 192/198 最终仍停在模板选择器 |
| 文件路径 桌面 `mech-check/numbers.json` | 满足 | 步骤 200 `mkdir -p /Users/admin/Desktop/mech-check`；步骤 203 对该路径 `json.tool` 校验通过 |
| 顶层含 `app`/`probes`/`mechanisms`，`app` 为「Numbers」 | 满足 | 步骤 203 输出 `app= Numbers`、`probes=[5 项]`、`mechanisms= 10` |
| 1 ax_summary（element_count/roles/excerpt 为实读） | 满足 | 步骤 6 全量 AX 树；步骤 194 解析得 `count=60`、21 个 role、excerpt 取自树中真实文本「All Templates…Education」 |
| 2 main_window_click（hit/error） | 满足（判据偏弱） | 步骤 12 `app.click([512,10])` 无异常、窗口树仍在，记 hit=true/error=null；"命中"由"未抛错+窗口仍在"推断，无像素级命中证据 |
| 3 menu_or_dropdown（label/opened/error） | 满足 | 步骤 14 点击菜单栏 50，AX 变为 `0 File, Secondary Actions: Cancel, Pick` + 完整 File 菜单项 |
| 4 shortcut（keys/delivered/error） | 部分满足 | 步骤 37 `app.pressKey('super+z')` 无异常→delivered=true；但 keys 写成 ["Command","Z"]，而步骤 53/55 显示 `super+Tab` 只产生 Tab 效果（焦点由 collection 移到 `44 button Cancel`），修饰键是否真被投递存疑 |
| 5 foreground_switch（left_front/returned_front/error） | 满足 | left_front：步骤 148 `app.click(49)`（前台时步骤 14 可点）返回 `cannotClickOffscreenElement`；步骤 160 Finder 应用菜单可点，确认前台已非 Numbers。returned_front：步骤 182 经 Finder `performSecondaryAction(51,'open')`，步骤 186/190 `app.click(50)` 成功打开 File 菜单 |
| 五次 attempted 均 true | 满足 | 步骤 203 `attempted={...: True ×5}` |
| 十种机制各一格、evidence 非空且为实际观察 | 结构满足，内容无法确认 | 步骤 203 `mechanisms=10`、`empty_evidence=[]`；但 JSON 正文未出现在记录中（步骤 201 草稿被整理截断），十条 evidence 是否字字对应实际观察无法核验 |

### 3. 关键过程（按步骤号）
- 步骤 2/6：取得 Numbers（模板选择器，`Window: ""`），用 `disableDiffing:true` 拿到完整 AX 树 0–59 号元素，构成 ax_summary 的原始材料。
- 步骤 12：点击标题栏 [512,10]，无异常、焦点仍为 `30 collection` → main_window_click。
- 步骤 14：点击菜单栏 `50 File`，AX 显示菜单展开且 `New…/Save/Export` 多项 disabled（无文档）→ menu_or_dropdown，同时成为 precondition 机制的观察来源。
- 步骤 16–22：`pressKey('Escape')` 返回 ok 但菜单未关（18 再查仍是菜单树），点击标题栏(20)也未关，截图返回 `Screenshot unavailable`(22) → 后被用作 input_swallowed/silent_noop 类证据。
- 步骤 35：改用 `performSecondaryAction(0,'Cancel')` 成功关菜单（恢复动作有效）。
- 步骤 37：`pressKey('super+z')` 投递成功、AX 前后完全一致 → silent_noop 证据。
- 步骤 24–76、128–132：用 shell 读 `@oai/cua` 文档、`strings` 驱动二进制、枚举 `cua.computer` 方法（61/63），确认 mac 端无 `launch_app`/`activate_window`（41/73），拿到 PressKey 键名契约（69）。
- 步骤 135–139、156：经 System Settings「About」对话框与「Hide System Settings」改变前台；步骤 160 验证 Finder 成为前台。
- 步骤 162–182：Finder → Go → Applications（168）→ 翻页定位 `51 image Numbers`（180）→ `performSecondaryAction(51,'open')`。
- 步骤 186/190：以"菜单栏可点击性"作为前台判据，确认 Numbers 回到前台；198 用 Numbers 菜单「Show All」把 System Settings 恢复显示；200/203 建目录、写文件并结构校验。

### 4. 绕路与副作用
- 绕路类型：**其他（框架内省）+ 命令行写产物**。模型未用 AppleScript/osascript/System Events（步骤 153 明确拒绝用 `lsappinfo` 判定前台，理由是"只用 CUA 做 GUI 观察"），GUI 动作全部走 `cua_repl`；但用 shell 大量读取 SDK 文档与 `strings /Applications/CuaDriverLocal.app/...`（步骤 59）寻找隐藏能力。JSON 产物通过命令行/补丁写盘——任务本身要求的是"写一个 JSON 文件"，属于正常非 GUI 交付路径，不算改产物作弊。
- 副作用：
 1. 打开并遗留 Finder「Applications」窗口（步骤 168；步骤 199 明确决定不关闭），Finder 最近文件夹记录被改动（步骤 166 可见 Recent Folders）。
 2. 曾隐藏 System Settings（156），已用 Show All 恢复（198，`settings.getScreenshot` 成功）。
 3. 曾打开/关闭 System Settings「About」对话框（137/139），已恢复。
 4. Numbers 内焦点被改到 `44 button Cancel`（55），后回到 `30 collection`（188/192）；未产生文档。
 5. 最终说明（205）只声明"Numbers 文档和设置未改动"，未披露 Finder 窗口残留。

### 5. 问题与归因

1. **shortcut.keys 与实际调用不一致的风险** —— 标签 A6.3（低置信，另可关联 A7.3 字段准确性）；受阻层次：模型本身 / 驱动键映射不明。预期：`super+z` 即 Command+Z → 实际：步骤 53/55 的 `super+Tab` 只产生 Tab 效果，提示 super 修饰可能未生效，模型自己也在推理中怀疑（步骤 56/76），仍在产物中写 `["Command","Z"]` 并在 205 对外称"Command-Z 已投递"。影响：单字段事实可信度；不影响 `attempted/delivered` 口径的成立。恢复状态：未恢复（未改用 `Super_L+z` 复测后更新字段）。
2. **驱动/后端层多处"调用成功≠状态生效"** —— 标签 E5（部分可能属设计限制）；层次：驱动或 Sky 后端。证据：Escape 投递成功菜单不关（16/18）、`click([512,10])` 不关菜单（20）、菜单打开时 `Screenshot unavailable`（22）、后台 `settings.click([400,15])` 不激活应用（51）、`getApp('Dock')` → `server error -10005: timeoutReached`（133）、`finder.scroll(31,…)` → `windowNotFoundAtPosition((1796.0,1463.0))` 但状态确实滚动了（176）、`performSecondaryAction(51,'open')` 返回 ok 但前台切换有延迟（182 vs 186）。步骤 60 驱动字符串提到"background key events never reach a native app's menus"，说明其中一部分可能是既定限制而非故障。影响：探针成本剧增、前台判据反复重建。恢复状态：已恢复（改用 `performSecondaryAction Cancel`、Hide/Show All、Finder 打开应用）。
3. **已证实无效的 Raise 复用** —— 标签 A8.2（边界）；层次：模型本身。步骤 47 已显示 `performSecondaryAction(0,'Raise')` 不改变前台，146、158 仍重复两次（158 前有"Settings 已隐藏"的条件变化，不能完全算无条件重复）。影响：成本。恢复状态：已恢复（改走 Finder 路径）。
4. **低收益内省反复** —— 标签 A3.3（边界）；层次：模型本身。步骤 69 已拿到 `PressKey.d.ts` 的键名契约后，128–132 仍做全仓 rg、59 做二进制 `strings`，返回空或大段无关输出（30/128 输出被整理者标注数十万字截断）。影响：上下文与时间成本，不影响结果正确性。恢复状态：不适用。
5. **前台判据一度误定** —— 标签 A5.1（边界，自纠）；层次：模型本身。步骤 145 把 `cannotClickOffscreenElement` 直接当作"Numbers 在后台"的充分证据；步骤 184/185 出现反例（Finder 元素同样报 offscreen）后，改用"菜单栏项是否可点击"重建判据（186/190），结论最终有独立支撑（148 vs 14/190）。恢复状态：已恢复。
6. **残留副作用未披露** —— 无明确 taxonomy 标签（最接近 A7.1 的边界：对自身改动范围的收尾核验不足）；层次：模型本身。影响：环境整洁度与报告完整性，不违反任务的"不改 Numbers 文档/设置"。恢复状态：未恢复。
7. **产物写入动作缺记录** —— 标签 Q5；层次：框架/记录整理。步骤 200（mkdir）与 203（校验）之间没有出现实际写文件的工具调用，JSON 正文也未在记录中呈现。影响：十条 mechanisms 的 evidence 是否"实际观察到的一句"无法核验，只能确认结构合规。恢复状态：不适用。

主要问题：没有可证实导致任务不达标的主因；对结果可靠性影响最大的是 7（产物内容不可核验）与 1（keys 字段事实性）；2/3/4 主要影响成本。

### 6. 能否收为训练轨迹
**遮掉第 59、128–132 步后收**（并建议对 24–33 做压缩保留）。理由：
- 可保留：步骤 16–35（按键被吞 → 改用 `performSecondaryAction Cancel`）、135–160（前台切换受阻 → 换路验证）、162–190（Finder 打开应用并用"菜单栏可点击性"验证前台）属于**环境受阻被模型合理绕过**，而且全程未离开 `cua_repl` 做 GUI 操作，是本类"机制体检"任务的高质量正样本；步骤 153 主动拒绝用 `lsappinfo` 旁路观察，示范价值高。
- 建议遮掉：步骤 59（`strings` 驱动二进制）与 128–132（已拿到键名契约后再做全仓搜索），这类"去读框架实现/二进制"既是低收益噪声，也可能教出绕过工具契约的习惯。
- 不构成"绕框架或命令行直接改产物"的不当正例：JSON 是任务要求的文件交付，用文件 API 写盘合理。
- 保留时需打标：`shortcut.keys` 字段（步骤 37 与 53/55 的冲突）应标注为不可直接作为正确示范。

### 7. 值得注意
- 模型能力：在没有 `activate_window`/`launch_app`（41/73）的 mac 端，模型自行构造了可证伪的前台判据（菜单栏项可点击性），并在反例出现后替换判据（185→186），状态推理可用；对"不要用 osascript"的边界把握较严（153）。
- 框架/后端：mac CUA 缺少"前台/frontmost"查询与应用激活原语，是本类任务的结构性缺口；`pressKey` 的 `super` 别名与 `Super_L` 的实际修饰行为未在文档中澄清（69 只说明 keysym 风格），`cannotClickOffscreenElement` 这类错误码语义过载（既可能是后台也可能是元素不可见），`windowNotFoundAtPosition((1796.0,1463.0))` 暴露了元素坐标超出屏幕的换算问题（176）。
- 对出题/评分：若希望验收"keys 真的被投递为组合键"，应在任务里要求给出可验证的副作用或要求回显驱动实际键名；若希望验收 evidence 的真实性，建议要求每格 evidence 附带来源（如 AX 原文片段或错误码原文），否则只能校验结构。另建议在任务中明确"是否允许为完成前台切换而动用第三方应用"，本轨迹为此隐藏了 System Settings 并打开了 Finder 窗口。

### 8. 不确定项
- JSON 正文未进入记录，十条 mechanisms 的 `seen` 判断与 evidence 文本、以及各探针子字段（hit/error/label/opened/keys/delivered/left_front/returned_front）的具体取值无法逐项核对；只能确认步骤 203 校验的结构性事实。对结论的影响：交付"满足"目前建立在结构校验 + 推理草稿之上，若评分检查字段取值，可能出现与本结论不同的判定。
- 记录在多处被整理者截断（步骤 2 的工具文档、约 78–128 之间的长段、步骤 193/201 的草稿内容），被截掉的部分我按"看不到"处理；其中可能包含对 shortcut 字段取舍、机制取值的进一步论证。
- 图片内容我无法查看（步骤 8/22/49/51/53/77 等的截图只计数），因此"主窗口点击是否真的命中窗口""交通灯颜色是否指示激活态"只能依赖模型文字与 AX 返回，像素判断（步骤 142 的 PIL 采样）也只能看到数值输出。
- `super+z`/`Super_L+Tab` 是否被驱动按 Command 投递、以及 Cmd+Tab 是否被驱动有意拦截（步骤 60 的字符串提示"Do not use … tab-switch shortcuts"），现有记录不足以判定，归因保留在"模型本身 / 驱动"之间未定。
- 本阶段没有可用的 Judge 结论或既有报告可复核（材料中未提供），因此不作 Judge 复核判断，也不补造判定。
