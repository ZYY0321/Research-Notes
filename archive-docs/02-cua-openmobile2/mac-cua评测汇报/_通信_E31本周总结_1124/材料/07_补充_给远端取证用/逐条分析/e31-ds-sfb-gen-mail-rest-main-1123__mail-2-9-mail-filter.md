类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-24 02:40，118.4s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-gen-mail-rest-main-1123/e31-ds-sfb-gen-mail-rest-main-1123__mail-2-9-mail-filter.json`

# e31-ds-sfb-gen-mail-rest-main-1123 / mail-2-9-mail-filter

### 1. 一句话结论
模型全程只用 `cua_repl` 在 Mail 内完成了 View > Filter → 仅 Flagged 的设置（步骤 56/58 窗口标题 "Inbox – Primary · Filter by: Flagged (2 messages)"），任务目标达成；过程中因按键未进入已打开菜单而误切邮箱、误选邮件导致一封未读变已读，但模型自行发现并恢复（步骤 60–63）。

### 2. 任务要求与完成情况
| 要求 | 判定 | 依据 |
|---|---|---|
| 在已打开的 Mail 内，用 View > Filter 过滤当前列表 | 满足 | 步骤 9/41/50/54 点击菜单栏 View（`Mail.menuBar.viewMenu`）；步骤 23 在 View>Filter 子菜单按 Return 启用过滤（标题变为 "Filter by: Unread"）；步骤 52 点击子菜单项 Flagged；步骤 56 点击 Unread 取消该条件 |
| 只显示标记旗标的邮件 | 满足 | 步骤 56/58/63 AX 标题 "Filter by: Flagged (2 messages)"，与侧栏 "row (selectable) 2, Description: Flagged" 的计数一致；步骤 58、63 另有截图返回（本记录看不到图像内容） |
| 成品由该应用自己交出，不用别的程序生成 | 满足 | 全部动作均为 `cua_repl` 对 Mail 的 AX 操作，无 shell/文件写入记录 |
| 不用 AppleScript/osascript 驱动，不结束或重启 Mail 进程 | 满足 | 记录中无 shell、rejected 条目，无 quit/kill 相关调用 |
| 「能用终端就先用终端，终端做不成再用界面」 | 无法确认是否符合期望 | 轨迹中无任何终端尝试或跳过理由的公开说明（步骤 1–2 直接选择 GUI）；但该要求是改 Mail 视图过滤状态，在禁用 AppleScript 前提下终端无可行路径，直接走 GUI 可成立 |
| 用一两句说明方法与题面外改动 | 满足 | 步骤 65：说明用 View > Filter、关闭"未读"保留"Flagged"、并说明中途已读状态已恢复 |

### 3. 关键过程（按步骤号）
1. 步骤 3/5/7：`getApp("Mail")`、`getAXState({disableDiffing:true})` 取得完整 AX 树，确认菜单栏节点与侧栏（Inbox 1 未读、Flagged 2）。
2. 步骤 9：点击 View 菜单（索引 112），返回树根变为 "View" 菜单，Filter 子菜单项当时多为 disabled（过滤未启用）。
3. 步骤 11：直接 click 子菜单父项 "Filter"（19）→ 菜单关闭、无状态变化。
4. 步骤 13/17/19：`pressKey('ArrowDown')`、`'down'` 报 `keyNotFound`，`'Down'` 成功（菜单首项被选中）。
5. 步骤 21/23：Down×3 + Right 进入 Filter 子菜单，Return 启用过滤 → 标题变 "Filter by: Unread (1 message)"。
6. 步骤 25–27：再次"点击 View + 连按 Down"失败，AX 显示 View 菜单为根但无任何项被选中，窗口标题先后变为 "Inbox — Mail"、"Drafts — Mail"。
7. 步骤 37–39：取消菜单后发现侧栏选中已被误切到 Drafts（"Filter by: Unread (1 draft)"），点击行 5 恢复为 Inbox。
8. 步骤 43–47：继续尝试 Down/'f'/`performSecondaryAction(19,'Pick')`，菜单被关闭并出现消息行被选中（步骤 48 "24 row (selected)"）。
9. 步骤 50–52：改用"点击 View 打开菜单后直接对子菜单项做 AX click"，click(24) 生效 → "Filter by: Unread or Flagged (2 messages)"。
10. 步骤 54–58：同法 click(23) 取消 Unread → "Filter by: Flagged (2 messages)"，并取 AX+截图确认。
11. 步骤 60–63：通过 Message 菜单 click(17) "Mark as Unread" 把被预览读过的邮件改回未读（步骤 63 侧栏 Inbox 恢复 "1"，选中行二级动作变为 "Read"）。

### 4. 绕路与副作用
- 绕路类型：**无**（未用 AppleScript/JXA、未自写点击合成、未用命令行生成或修改产物；全部经 `cua_repl` 的 AX click / pressKey）。
- 副作用：
  - 侧栏邮箱选中被误切到 Drafts（步骤 37），步骤 39 已恢复 Inbox。
  - 邮件列表中一封原本未读的邮件被选中预览后变为已读（步骤 48/52 可见消息行被选中，步骤 59 模型自述发现），步骤 63 已通过 Message > Mark as Unread 恢复。
  - 过滤条件在中间态一度为 "Unread or Flagged"（步骤 52），最终已收敛为仅 Flagged。
  - 未发现多余文件、删除或发送邮件等不可逆改动。

### 5. 问题与归因
1. **菜单打开状态下按键未进入菜单，落到主窗口造成误改**
   - 预期：View 菜单已打开（AX 根为 "View"，步骤 25/41/43），`pressKey('Down')` 应在菜单内移动高亮 → 实际：AX 中无任何项被选中，且主窗口侧栏选中从 Inbox 变为 Drafts（步骤 37）、消息行被选中（步骤 48）。
   - 标签：E5（工具/驱动与观察不一致：AX 报告菜单为根，但键事件被送往窗口）；模型侧在不确认按键是否生效时连发多次按键并触发误改，另记 A4.4（相邻状态未就绪即连续按键）为次要。
   - 受阻层次：驱动/Sky 后端（主要，键事件路由）；模型本身（次要，盲发按键）。
   - 影响：额外约 20 步探索成本 + 两处状态误改（邮箱选中、邮件已读）。
   - 恢复状态：已恢复（步骤 39 恢复 Inbox；步骤 63 恢复未读；最终过滤结果正确）。
2. **`pressKey` 键名不被接受**（步骤 13 `keyNotFound("ArrowDown")`、步骤 17 `keyNotFound("down")`，步骤 19 `'Down'` 成功）
   - 标签：A4.2（参数值不符接口要求），但本记录中 API 文档正文被截断，无法确认当时是否已给出合法键名表；属有信息增益的有限试探，不计为实质错误。
   - 受阻层次：模型桥接/模型本身（未知）；影响：2 步成本；恢复：已恢复。
3. **`app.getScreenshot()` 返回 "Screenshot unavailable for /System/Applications/Mail.app"（步骤 31）、菜单打开时 `getAXStateAndScreenshot` 未返回图像（步骤 35）**
   - 标签：E5（工具观察获取异常）。受阻层次：驱动/Sky 后端。影响：模型一度无法用截图核对菜单可见状态，增加试错；恢复：已恢复（步骤 58/63 正常返回图像）。
4. **`performSecondaryAction(19,'Pick')` 未达预期且附带选中消息（步骤 47–48）**
   - 标签：A4.3（对该目标采用的调用方式不适用），次要；受阻层次：模型本身。影响：疑为"预览致已读"副作用的来源之一（也可能来自步骤 43/45 的误投按键，证据不足以区分）；恢复：已恢复（步骤 63）。
5. **终端优先要求未见尝试或公开说明**
   - 标签：无法定性（A1.3 证据不足）；本任务在禁用 AppleScript 下终端无可行路径，直接用 GUI 可成立，故不计错，仅列为不确定项。

主要问题：第 1 项（驱动键事件路由不一致 → 误改状态 + 成本）；其余为次要，均不影响最终交付。

### 6. 能否收为训练轨迹
**遮掉第 25–48 步后收。**
- 保留 1–24：正确的 AX 勘察 + 经 View > Filter 启用过滤，是良好示范；步骤 13–19 的键名试探也可保留（环境/接口信息缺失下的合理探索）。
- 建议遮掉 25–48：这段是在未确认菜单是否接管键盘时反复盲发按键与 `Pick`，直接造成邮箱误切到 Drafts、邮件被误选变已读，属模型自身操作偏差，不宜作为正例。
- 保留 49–65：改为"打开菜单后直接对子菜单项做 AX click"是本案例最有价值的可复用路径；步骤 60–63 主动恢复未读、步骤 65 如实说明方法与改动，均为正面示范。
- 不涉及绕框架或命令行改产物，不属于"不当正例"。

### 7. 值得注意
- 驱动层：AX 树已把 View 菜单作为根（表明菜单打开），但 `pressKey` 有时被路由到主窗口，造成"看似菜单导航、实为列表导航"的误操作（对比步骤 19/21 成功 与 25/43 失败）——这是后端键事件焦点处理的可复现隐患，建议在菜单打开态验证按键目标或优先使用 AX click。
- 菜单项的 AX `click` 在菜单已打开时可直接命中未可见展开的子菜单项（步骤 52/56 生效），而对子菜单父项 click（步骤 11）或 `performSecondaryAction(...,'Pick')`（步骤 47）均不可靠，值得写进技能/提示。
- 出题与评分：Mail 启用 Filter 的默认条件是 Unread，评分若只看"过滤已启用"会漏判"Unread or Flagged"这一中间态；本例应以窗口标题 "Filter by: Flagged" 为判据。另外"预览导致已读"是此类邮件任务常见的隐性副作用，可作为"是否额外改动"的考察点（本例模型主动恢复）。
- `getScreenshot` 对系统应用返回 unavailable，而 `getAXStateAndScreenshot` 可用，接口能力不一致值得文档化。

### 8. 不确定项
- 步骤 5/58/63 的截图内容本记录不可见，最终"仅显示 2 封旗标邮件"的视觉确认依赖 AX 标题与侧栏计数，图像层面无法由我核对。
- 步骤 3 的 API 文档正文被抽取截断 26658 字，无法确认 `pressKey` 合法键名、`click` 对菜单项的语义是否已在文档中说明，因而步骤 13/17/47 是否属"违反已知契约"无法判定。
- "邮件由未读变已读"的具体触发点（步骤 43/45 的误投按键 vs 步骤 47 的 `Pick`）无法从现有记录区分；模型在步骤 59 的自述不能单独作为证据。
- 初始邮件读/未读的完整快照只在截断文本之外，步骤 63 的"恢复"以侧栏 Inbox 计数回到 1、选中行二级动作变为 "Read" 推断，未逐封核对。
- 无 Judge 结论或既有报告可供复核（材料中未提供），本阶段不补造判定；也未登记证据编号，故不填写 `evidence_refs`。
