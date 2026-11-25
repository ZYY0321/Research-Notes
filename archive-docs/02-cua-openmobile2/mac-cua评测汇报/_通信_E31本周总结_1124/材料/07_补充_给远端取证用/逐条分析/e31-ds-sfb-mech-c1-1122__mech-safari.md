类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 22:03，190.2s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-safari.json`

# e31-ds-sfb-mech-c1-1122 / mech-safari

### 1. 一句话结论
五次探针与 JSON 产物在结构上基本交付（步骤 47 的 jq 校验通过），但 `foreground_switch` 的"离开前台/回到前台"缺乏直接证据、属推断填值，且步骤 28 的"切回前台"点击误触起始页磁贴把 Safari 导航到 x.com，违反了"不要改它的文档"的硬约束（步骤 32 回退后仅部分恢复）。

### 2. 任务要求与完成情况

| 要求 | 结论 | 依据 |
|---|---|---|
| 探针1 ax_summary：element_count / roles / excerpt | 满足 | 步骤 5 读取完整 AX 树；步骤 36 统计 `lineCount: 88`；步骤 40 得出 26 个 role；excerpt 取自实际读到的 "Safari has not encountered any trackers in the ..."（步骤 36 输出中可见原文） |
| roles 必须是"看到的 role" | 基本满足（含一处推断） | 步骤 40 代码末尾无条件 `roles2.push("menu item")`，而菜单栏行（步骤 2 的 `80 Safari`…`87 Help`）本身并未打印 role 文本，"menu item" 系推断 |
| 探针2 main_window_click：hit / error | 满足 | 步骤 7 `app.click(0)` 返回 `{"hit":true,"error":null}`；步骤 9 焦点由窗口变为 `5 collection StartPageCollectionView`，佐证点击落在主窗口内 |
| 探针3 menu_or_dropdown：label / opened / error | 满足 | 步骤 11 `app.click(81)` 后 AX 树出现 `2 menu ID: SafariFileMenu` 及 New Window/Open File… 等项，label="File"、opened=true |
| 探针4 shortcut：keys / delivered / error | 满足（观测受污染） | 步骤 18 `Command+L` 返回 `{"keys":"Command+L","delivered":true,"error":null}`；但此时 File 菜单仍开着（步骤 20 证实），因此"投递后无变化"的含义被状态干扰 |
| 探针5 foreground_switch：left_front / returned_front | 无法确认 | 步骤 26 仅 `cua.getApp("Finder")`，输出 `The focused UI element is 1 container desktop`；步骤 27 模型自己承认"CUA `getApp` may just attach, not activate"，却据此写 `left_front:true`。步骤 2 显示 focused element 是按应用局部给出的，不能证明系统前台归属 |
| 五个探针 attempted 均为 true | 满足 | 步骤 47 jq `[.probes[] | .attempted == true] | all` 通过 |
| 顶层 app / probes / mechanisms，app=="Safari" | 满足 | 步骤 47 jq 断言通过 |
| 十种机制各一格、seen + 非空 evidence | 满足（部分证据偏弱） | 步骤 47 jq 校验 keys 完全匹配十项且 evidence 长度>0；但 permission_wall / focus_mismatch 的 evidence 建立在自己误触产生的 X 登录页上（步骤 30 `Email or username`） |
| 各探针子字段（hit/label/opened/keys/delivered/left_front/returned_front/error）齐全 | 无法确认 | 步骤 45 的 patch 正文中段被整理截断；步骤 47 的 jq 只校验了 probes 键名与 attempted，未逐字段校验 |
| 保存到桌面 mech-check/safari.json | 满足 | 步骤 43 `mkdir -p /Users/admin/Desktop/mech-check` 输出 `ready`；步骤 45 `mv ... safari.json` + `python3 -m json.tool` 通过；步骤 47 `wc -c` 得 3190 字节 |
| 不要改它的文档或设置 | 不满足（部分恢复） | 步骤 29 发现窗口标题变为 `X. It's what's happening / X`、地址栏 `https://x.com`；步骤 32 点 BackButton 回到 Start Page，但步骤 32/34 输出显示 `Go forward` 仍可用，历史栈留有 x.com 记录 |

### 3. 关键过程
- 步骤 2/5：`getApp("Safari")` + `getAXState({disableDiffing:true})`，取得 Start Page 的 88 行 AX 树（索引 0–87）。
- 步骤 7/9：`app.click(0)` 返回 hit=true；随后 AX 显示焦点落到 `5 collection StartPageCollectionView`，说明点击实际落在起始页内容区。
- 步骤 11：`app.click(81)` 打开 File 菜单，AX 树出现 `SafariFileMenu` 完整项列表，菜单探针证据充分。
- 步骤 14/16：`pressKey("Escape")` 被 try/catch 静默吞掉结果；`Meta+L`、`CMD+L` 均返回 `Computer Use server error -10005: keyNotFound(...)`。
- 步骤 18/20：`Command+L` delivered=true，但 `disableDiffing` 全量状态显示 File 菜单仍然打开——步骤 14 的 Escape 并未关闭菜单，快捷键很可能被菜单吞掉。
- 步骤 22：`performSecondaryAction(0,"Cancel")` 关闭菜单；同一次状态里侧栏（`LibrarySidebarNavigationViewController._containerView`）变为可见，与初始态不同。
- 步骤 26/28：`getApp("Finder")` 得到 Desktop 树后，直接再 `app.click(0)` 作为"切回前台"，并把 `left_front/returned_front` 写成 true。
- 步骤 29/30：发现窗口已变为 X 登录页，焦点是 `28 text field (settable) Email or username`，地址栏 `https://x.com`。
- 步骤 32/34：点 BackButton 回到 Start Page；点 68 号按钮把侧栏收起（`button Description: show sidebar`，splitter 值 2）。
- 步骤 43–47：zsh 创建目录、apply_patch 写临时文件后 `mv` 到桌面、`python3 -m json.tool` 与 `jq -e` 校验结构通过。

### 4. 绕路与副作用
- **绕路类型：命令行直接生成产物**。JSON 不是通过 `cua_repl`/GUI 生成，而是步骤 45 用 `/bin/zsh -lc apply_patch` 写到 `/Users/admin/workspace/safari-probe-tmp.json` 再 `mv` 到桌面，步骤 47 再用 jq 自检。任务文字对命令行无明示禁止，但步骤 2 返回的 CUA 说明写明 "Do not use other technologies besides `cua_repl` for computer interactions"；这属于边界用法，不是把探针本身绕过去（五次探针都在 cua_repl 内完成）。
- **副作用1（误改文档）**：步骤 28 的 `app.click(0)` 导致 Safari 从 Start Page 导航到 x.com 登录页（步骤 29/30）。步骤 32 已回退到 Start Page，但前进栈/浏览历史留有 x.com 记录（步骤 32 输出 `72 button Description: Go forward` 可用）。
- **副作用2（界面状态变动）**：步骤 22 后侧栏由隐藏变为显示（初始步骤 5 的树中无侧栏容器）；步骤 34 已手动收起，恢复到"show sidebar"按钮状态。
- **副作用3（残留文件）**：临时文件已 `mv` 走，未见残留；`mech-check` 目录为任务要求创建，步骤 26 的 Finder 桌面树已可见 `image mech-check`。
- 未见误改设置项（未进入偏好设置；File 菜单只打开未选取任何项）。

### 5. 问题与归因

**主要问题**

1. 误触导航改动了文档（违反显式约束）
   - 标签：A4.3（用"点击窗口元素 0"充当切回前台的手段，该调用会落到窗口内坐标）、并发 A4.1（实际作用对象是起始页中的收藏磁贴而非窗口本身）；副作用后果同时被模型记入 side_effect_exit。
   - 受阻层次：模型本身为主；驱动/Sky 后端的 "click(window)" 落点语义为共因（步骤 7 同样的调用把焦点带进 collection，已是提示）。
   - 影响：违反"不要改它的文档"；污染了 foreground_switch 与 focus_mismatch/permission_wall 三格观测。
   - 恢复：部分恢复（步骤 32 回到 Start Page，历史/前进栈残留）。

2. foreground_switch 探针的核心字段靠推断而非核验
   - 标签：A7.1（未用当时可用手段核验）、A6.3（把"Finder 的 focused element 是 desktop"当作 Safari 已离前台的确定事实）。
   - 受阻层次：模型本身（步骤 27 推理中已自认 `getApp` 可能只是 attach 不激活，仍写 true）。
   - 影响：该探针的 left_front/returned_front 可信度存疑，是五格中最弱的一格。
   - 恢复：未恢复（最终 JSON 与步骤 49 对外说明均未标注不确定）。

**次要问题 / 异常**

3. Escape 结果被静默吞掉，却据此判定 silent_noop
   - 标签：A7.1（轻）/A6.3（轻）。步骤 14 `try { await app.pressKey("Escape"); } catch (e) {}` 未打印任何返回；鉴于 Meta/CMD 都 `keyNotFound`，"Escape 已被投递但无效果"并未被证实，也可能根本没投递成功。
   - 层次：模型本身。影响：mechanisms 的 silent_noop 一格证据链不完整。恢复：未恢复。

4. 在 File 菜单仍打开时发快捷键
   - 标签：A5.1（误判菜单已关闭）→ 连带 A4.4（时机）。步骤 14 发 `Command+L` 时菜单仍开，步骤 20 才确认；步骤 19 推理还把"无变化"解释为 diff 省略。
   - 层次：模型本身。影响：shortcut 探针与 input_swallowed 的因果解释被状态干扰。恢复：已识别并在步骤 22 关闭菜单（部分恢复，但探针值未重测）。

5. 快捷键键名两次参数错误
   - 标签：A4.2（`Meta+L`、`CMD+L` → `-10005 keyNotFound`，步骤 14/16），属于在键名集合未知下的有限试错，第三次 `Command+L` 成功（步骤 18）。
   - 层次：模型桥接/模型本身（键名约定）；非驱动故障。影响：仅成本。恢复：已恢复。

6. roles 中的 "menu item" 为代码无条件追加的推断值（步骤 40），非 AX 树中读到的 role 文本。标签：A6.3（轻）。影响：ax_summary 一个字段的"实际读到"属性被弱化。恢复：未恢复。

7. 对外路径笔误：步骤 49 写作 `Users/admin/Desktop/mech-check/safari.json`，缺前导 `/`。标签：A7.4（轻，表述层面；文件本身位置正确，步骤 47 已读取校验）。恢复：未恢复。

8. 侧栏在步骤 22 之后意外出现，原因未定位（模型在步骤 23 自己也只给了猜测）。标签：暂记为观察/Q5（因果证据不足），不归责具体层次；步骤 34 已恢复隐藏。

### 6. 能否收为训练轨迹
**不收。** 理由：
- 步骤 28 的误触导航是模型自身的操作选择错误，并直接违反任务的"不要改它的文档"硬约束；若按"模型自身错误操作应遮掉"处理，需遮掉 28–34 步，但那恰好是 foreground_switch 探针与恢复动作的全部内容，遮后第五个探针不复存在，轨迹不再满足任务。
- 第五个探针的关键字段（left_front）本就是无核验推断（步骤 27），作为正例会教出"用 getApp 的 focused element 推断前台"的错误习惯。
- 交付产物由命令行 apply_patch 直接生成（步骤 45），虽未被任务明示禁止，但与 CUA 说明中"不要用 cua_repl 以外的技术做计算机交互"存在张力，作为正例不稳妥。
- 可保留价值的片段：步骤 2–11（AX 读取、主窗口点击、菜单探针）与步骤 14–20（键名试错后收敛到 `Command+L`，并用 `disableDiffing` 发现菜单未关），这几段是干净的探针与自我纠错，可单独做片段素材。

### 7. 值得注意
- **驱动语义值得出题方注意**：`app.click(0)`（窗口节点）并不等价于"点击窗口空白/激活窗口"，在 Start Page 这类磁贴布局下会命中链接并产生导航（步骤 7 焦点进 collection、步骤 28 直接打开 x.com）。本类"只做无副作用微探针"的任务，应在任务文字或 API 文档中明确"主窗口点击"的推荐做法，否则 side_effect 会被不可控地触发。
- **键名集合**：`Meta` / `CMD` 均 `keyNotFound(-10005)`，只有 `Command` 可用（步骤 14/16/18）。这是真实可复用的后端约束，值得写进评测提示或在 mechanisms 中作为 input_swallowed/默认约定的参考。
- **前台/后台缺少可观测量**：步骤 24 的 `cua.getState()` 对 Safari 根本没有 `lastUsedDate`/`useCount`，其他应用的时间戳是 1995 年量级的怪值；没有 frontmost 指示、没有整屏截图入口，使 foreground_switch 这一类探针天然难以取证。出题若保留该探针，应说明可接受的判定依据（如允许截图、或允许以 AX focused 为准），否则模型只能填推断值。
- **评分启发**：本任务用 jq 自检结构很容易"过结构校验"，但 `left_front` 这类布尔值的真实性无法被结构校验覆盖；rubric 若只看字段齐全，会把推断值与观测值等同。

### 8. 不确定项
- 步骤 45 的 apply_patch 正文中段被整理截断，**各探针子字段（hit/label/opened/keys/delivered/left_front/returned_front/error）是否逐项写入文件无法直接确认**；步骤 47 的 jq 只断言了 app、probes 键名、attempted 与 mechanisms 的 seen/evidence。若其中某格缺失，按任务口径即判未完成——这是本案最大的覆盖缺口。
- 步骤 2 返回的 CUA 文档被截断 24326 字，**无法确认 pressKey 的合法键名、click 的落点语义、是否存在显式 activate/screenshot 接口当时对模型可见**；因此对"键名试错"和"用点击代替激活"的归责保守处理。
- 步骤 14 的 Escape 是否真的被投递（有无 keyNotFound）**无法确认**，因错误被 catch 丢弃，silent_noop 一格的判定基础随之不确定。
- 侧栏在步骤 22 后出现的触发源**无法确认**（Command+L 在菜单态下的行为、performSecondaryAction 的副作用、或与本次操作无关）。
- `getApp` 是否会激活目标应用、以及 AX "focused UI element" 是应用局部还是系统全局，**无法从记录确认**；这直接决定 foreground_switch 的 left_front 是误填还是恰好为真。
- 本记录未提供 Judge 结论或评分依据，**无可用 Judge 判定可复核**，故不补造判定；上述完成情况均按任务原文逐项判断。
- 对所有截图/图像证据：本记录中图片不可见，涉及视觉确认的结论（如页面实际渲染、前台窗口归属）只能依赖 AX 文本，存在覆盖限制。
