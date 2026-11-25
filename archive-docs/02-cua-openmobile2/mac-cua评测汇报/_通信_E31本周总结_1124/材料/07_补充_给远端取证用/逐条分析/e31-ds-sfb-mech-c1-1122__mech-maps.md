类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-22 21:55，175.2s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-mech-c1-1122/e31-ds-sfb-mech-c1-1122__mech-maps.json`

# e31-ds-sfb-mech-c1-1122 / mech-maps

### 1. 一句话结论
模型在 Sky 后端多处异常（坐标点击 `windowNotFoundAtPosition`、菜单卡死无法关闭、截图不可用）的条件下，仍依次尝试了五个探针并用命令行写出结构完整、字段齐全的 `~/Desktop/mech-check/maps.json`（第 45、47 步 jq 校验通过），交付要求基本满足；主要残余问题是前台切换两个布尔值缺少直接证据，以及 Maps 被留在 View 菜单常开状态未恢复。

### 2. 任务要求与完成情况

| 要求 | 结论 | 依据 |
|---|---|---|
| JSON 顶层含 `app`／`probes`／`mechanisms` | 满足 | 第 45 步 apply_patch 后 jq 输出三个顶层键；第 47 步 `jq -e` 校验 `VALID` |
| `app` 必须为「Maps」 | 满足 | 第 45 步输出 `"app": "Maps"`；第 47 步校验含 `.app == "Maps"` |
| 五次探针 `attempted` 均为 true | 满足 | 第 47 步 `([.probes[] | .attempted] | all)` 通过 |
| ax_summary：element_count／roles／excerpt（实际读到原文） | 满足（roles 部分无法确认） | excerpt `button Description: Hide Sidebar, Help: Toggle sidebar, ID: toggleItemIdentifier` 确实出现在第 10 步返回；`element_count: 53` 由第 16 步树索引 0–52 推得；roles 中 `image`、`element` 在本记录可见片段中未出现（第 16 步输出被整理截断） |
| main_window_click：hit／error | 满足 | 第 13 步实际发起 `app.click([160,300])`，返回 `{"attempted":true,"hit":false,"error":"Computer Use server error -10005: windowNotFoundAtPosition((608.0, 406.0))"}`，与 JSON 一致；任务允许 hit 为 false |
| menu_or_dropdown：label／opened／error | 满足 | 第 18 步 `app.click(50)`（菜单栏 View）后 AX 树根为 `0 View, ID: com.apple.menu.view` 且含 21 项菜单项；第 20 步置 `opened=true`，error null |
| shortcut：keys／delivered／error | 满足 | 第 20 步 `app.pressKey("cmd+f")` 未抛错，JSON 记 `delivered: true` |
| foreground_switch：left_front／returned_front／error | 无法确认（字段已填且无报错） | 第 38 步 `cmd+Tab` 后能读到 `App: System Settings` 树，第 40 步切回后读到 Maps 树；但 `left_front=true` 是第 40 步代码直接赋值，`returned_front` 仅凭 AX 串含 `App: Maps.` 推断，期间 `getScreenshot` 返回「Screenshot unavailable」（第 29 步），无前台性直接证据 |
| 十种机制各一格，seen + 非空 evidence | 满足 | 第 45 步十格齐全；第 47 步校验 `(.mechanisms|keys|length)==10` 且 evidence 长度 >0 |
| 不改 Maps 的文档或设置 | 基本满足（有争议） | 仅点了通知页 `Not Now`（第 10 步）与 Custom Routes 的 `Continue`（第 16 步）；第 25 步曾试点 `Snap to North` 但因 element ID 失效未生效 |
| 保存路径 桌面/mech-check/maps.json | 满足 | 第 43 步建目录、第 47 步 `ls -l /Users/admin/Desktop/mech-check/maps.json`（2902 字节） |

### 3. 关键过程
1. 第 3 步 `cua.getApp("Maps")`：首帧 AX 为通知授权 sheet（`Get Notified when Friends Share Their ETAs`），仅有 Not Now／Enable Notifications 与菜单栏。
2. 第 7 步 `getAXStateAndScreenshot` 取全量树＋截图（480×600，2 图），确认主窗口被 sheet 遮挡。
3. 第 10 步点 `Not Now` 清遮挡，拿到真正主窗口树（toolbar、Hide Sidebar、3D、Look Around(disabled) 等）。
4. 第 13 步 main_window_click 探针：点 `[160,300]` 返回 `windowNotFoundAtPosition((608.0, 406.0))`，同时出现第二个首启 sheet「Introducing Custom Routes」。
5. 第 16 步点 `Continue` 关闭介绍页，得到含搜索框、Library、Compass 等的完整树（索引至 52）。
6. 第 18 步点 View（元素 50）→ 菜单打开（AX 根变为 View 菜单）；同时 `nodeRepl.emitImage received an unsupported value`，截图通道开始失效。
7. 第 20 步 `Escape` 后发 `cmd+f`：均无抛错，但 AX 仍停在 View 菜单，模型据此判定 input_swallowed（第 21–22 步）。
8. 第 23、25、29、31、33 步连续恢复尝试：`performSecondaryAction`／`click(14)` 报 `element ID is no longer valid`；`getScreenshot` 报 `Screenshot unavailable for /System/Applications/Maps.app`；`esc`／`cmd+.` 报 `keyNotFound`；重新 `getApp` 后菜单依旧。
9. 第 36→38→40 步 foreground_switch：`cmd+tab` 报 `keyNotFound("tab")`，改用 `cmd+Tab` 成功，读到 System Settings 树，再切回读到 Maps（菜单仍开）。
10. 第 43–47 步：`mkdir -p` 建目录、`apply_patch` 写 JSON、`jq` 美化与结构断言，输出 `VALID: all required probes/mechanisms present`。

### 4. 绕路与副作用
- 绕路类型：**其他**。五次 GUI 探针全部通过 `cua_repl`（getApp/getAXState/click/pressKey）完成，未用 AppleScript、osascript 或自写事件合成；命令行仅用于创建目录、写入报告 JSON、jq 校验（第 43、45、47 步）。任务文字未禁止命令行且交付物本身是桌面 JSON 文件，故不视为「命令行直接改产物」规避 GUI；若按更严口径把写交付文件也算 CLI 绕路，则归该类。
- 副作用：
  - 第 10 步点掉 Maps 通知授权提示（`Not Now`）、第 16 步点掉 Custom Routes 介绍页——属首启引导，但「Not Now」涉及通知授权选择，与「不要改设置」存在轻微张力，模型事前公开说明（第 9、15 步）。
  - 第 25 步为关菜单而选择功能项 `Snap to North`（会改地图朝向），因 element ID 失效未生效，属潜在误触。
  - 轨迹结束时 Maps 的 View 菜单仍保持展开（第 40–41 步 AX 证据），未恢复。
  - 新增 `~/Desktop/mech-check/` 目录与 `maps.json`（任务要求），无多余文件。

### 5. 问题与归因

**主要问题**

1. 菜单打开后进入不可恢复状态，且截图通道失效
 - 标签：E5（工具／框架／应用异常）
 - 受阻层次：驱动或 Sky 后端
 - 依据：第 18／20 步 `nodeRepl.emitImage received an unsupported value`；第 23／25 步 `The element ID is no longer valid`（刚读到的同一棵树内的 ID）；第 29 步 `Screenshot unavailable for /System/Applications/Maps.app`；第 20／31 步 `Escape` 投递成功但 AX 无变化。
 - 影响：丧失视觉核验能力（shortcut、foreground_switch 只能用 AX 文本间接判断）；消耗第 21–41 步约十余步预算；Maps 遗留菜单常开。
 - 恢复：未恢复（多路径尝试均失败，模型按"任务未要求恢复"继续交付）。
 - 说明：模型的恢复尝试每次都变更条件（不同按键名、secondary action、点菜单项、重取 app、切前台），属合理有限重试，不构成 A8.2。

2. 主窗口坐标点击被解释到 (608.0, 406.0) 并报无窗口
 - 标签：E5（坐标／窗口定位层不一致）；是否另有模型侧坐标选择偏差无法区分，暂不加 A4.2
 - 受阻层次：驱动或 Sky 后端（也可能为窗口几何／缩放映射，未知）
 - 依据：第 13 步传入 `[160,300]`（该点在第 10 步 1024×768 截图的侧栏区域内），服务端报 `windowNotFoundAtPosition((608.0, 406.0))`。
 - 影响：main_window_click 的 hit=false；任务允许该值，对交付无致命影响。
 - 恢复：不适用／未恢复（模型第 17 步明确决定保留失败结果，不再改用元素点击重试）。

**次要问题**

3. foreground_switch 两个布尔值核验不足
 - 标签：A7.1（未充分核验任务完成）；程度轻，受 E5 截图不可用限制
 - 受阻层次：模型本身（叠加后端限制）
 - 依据：第 40 步代码 `foregroundProbe.left_front = true;` 为直接赋值；`returned_front` 由 `returnedState.includes('App: Maps.')` 推断，而读取某应用 AX 树并不证明其在前台；无 frontmost 查询或截图佐证。
 - 影响：JSON 该探针字段的证据强度弱于其他四项；不影响字段完整性。
 - 恢复：不适用。

4. 以功能性菜单项作为关菜单手段
 - 标签：A4.1（操作对象选择偏差，轻微）
 - 受阻层次：模型本身
 - 依据：第 24–25 步推理与代码选择 `app.click(14)`（Snap to North）以关闭菜单。
 - 影响：潜在改动地图朝向（与"体检不改状态"的意图相悖）；实际因 element ID 失效未生效。
 - 恢复：已恢复（无实际状态变化）。

5. 探针对象状态自记一度与观察不一致（自造反复）
 - 标签：A5.1（当前控件状态记录错误，立即自纠）
 - 依据：第 18 步输出 `{"attempted":true,"label":"View","opened":false,...}`，而同一返回的 AX 树显示菜单已展开；第 20 步才改为 `opened=true`。
 - 影响：仅过程一致性，最终 JSON 正确。
 - 恢复：已恢复。

### 6. 能否收为训练轨迹
**遮掉第 25 步后收**。理由：第 3–20、26–47 步是在后端异常下的合理探测与交付，环境问题（E5 坐标定位、菜单卡死、截图不可用）被模型以差异化重试、如实记录原始错误原文、并最终完成结构校验的方式合理应对，符合"环境问题被模型合理绕过的步骤可保留"；命令行只用于写报告文件与校验，任务文字未禁止，不属不当正例。第 25 步以功能菜单项（Snap to North）作为关闭菜单的手段，属模型自身不恰当操作选择，建议遮掉；若训练口径要求前台判定必须有视觉／frontmost 证据，可同时弱化第 40 步的 `left_front = true` 直接赋值片段。

### 7. 值得注意
- Sky 后端在原生菜单打开期间表现出成组异常：`emitImage unsupported value`、同帧 element ID 立即失效、`Screenshot unavailable`、`Escape` 投递成功但无效果——这一组合会让任何依赖截图核验的 macOS 任务失去视觉证据，值得作为后端缺陷单独跟踪。
- 按键名契约不一致：`cmd+f` 可用，`esc`/`cmd+.`/`cmd+tab` 报 `keyNotFound`，而 `cmd+Tab` 可用（第 31、36、38 步）。文档未暴露键名表，模型靠试错发现，属可改进的接口可发现性问题。
- 坐标点击的窗口定位（第 13 步 160,300 → 608,406 且报无窗口）提示窗口相对坐标／屏幕坐标换算或多显示区域处理存疑。
- 对出题/评分的启发：本题以"attempted 必须 true、失败也要如实记录 error 原文"设计，很好地把后端异常与模型诚实度解耦；但 `left_front/returned_front` 这类布尔在截图不可用时无可验证手段，建议题面补充可接受的核验口径（如允许以 AX 可读性或 frontmost 查询为准），否则评分无法区分"如实推断"与"无依据填真"。
- 本次未提供 Judge 结论或既有报告，故无 Judge 复核；不补造判定。

### 8. 不确定项
1. `roles` 中的 `image`、`element` 以及 `element_count: 53`：第 16 步树在本记录中被整理截断（「抽取截断 6395 字」），可见片段未出现这两个 role，无法确认是否确为实际读到——属记录可见性限制（Q5 性质，整理方式所致，不归因框架）。
2. foreground_switch 是否真的发生了"离开前台／回到前台"：无截图、无 frontmost 字段，仅有 AX 树可读性与第 38 步输出末尾的「Selected / 用户正在看的内容」提示作间接旁证，无法确证。
3. 菜单在切走再切回后仍"展开"：既可能是真实的 UI 残留（模型记为 side_effect_exit），也可能是后端 AX 快照陈旧（更接近 state_desync／E5）。两种解释均无法凭现有文本区分，故模型把 `state_desync` 记为 false 不能判定为错误。
4. `default_trap` 的 evidence 提到 Enable Notifications 为"蓝色主按钮"：AX 树无颜色信息，应来自第 7 步两张截图，但本分析看不到图像，无法核验是否属无依据断言。
5. 第 13 步新出现的「Introducing Custom Routes」sheet 与那次失败点击之间是否有因果（点击是否部分生效）无法判断；错误文本仅说明未找到窗口。
6. 点击通知页 `Not Now` 是否构成任务禁止的"改设置"，取决于验收口径；记录中无后续权限状态证据。
