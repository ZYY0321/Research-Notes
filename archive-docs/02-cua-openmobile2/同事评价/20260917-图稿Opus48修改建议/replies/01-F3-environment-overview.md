# 01-F3-environment-overview

- model: `claude-opus-4-8`
- elapsed_s: 82.6
- finish_reason: stop
- usage: {"prompt_tokens": 4673, "completion_tokens": 3770, "total_tokens": 8443, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 4673, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: F3-environment-overview.png, 环境描述图.jpeg

---

# 审稿意见：MobileGym++ Environment Overview

## 1. 这张图现在在说什么

图分四块：左上「Commercial coverage」列七领域 + 35 new/64 installable；上中「GUI: edit the same bill」两张手机截图（1500→1580）；中「App-native tools」伪代码 + result；右「Per-app business stores」三个 store 对象；下方「Shared OS」列共享设施 + Environment APIs + Reset/inject→GUI/tool action→Read state 回路 + Agent。核心叙事：同一张账单 b010，工具打开、GUI 改金额、store 身份不变、UI 与 store 一致，环境可 reset/inspect/replay。

## 2. 内容张力诊断

**主张覆盖上是全的，但每条都"说到没说透"，10 秒内抓不住重点。**

- **回路弱是最致命的**。参考图的 `init()→predict()→eval()` 有编号①–⑧、有 Obs/Action/Monitor/States 分工、有 Complete/Incomplete 出口，读者一眼知道"评测怎么跑、成败怎么判"。你的 `Reset/inject→GUI/tool action→Read state` 是三个孤立方块，没有编号、没有 Obs/Action 标注、**没有成败判定出口**。你的核心主张"成败看业务状态差分"在图里只有右下角一个绿框 `UI and store agree`，没有和回路终点连成"这就是 eval"。审稿人抓不到"评测协议"。

- **Agent 观测约束不硬**。主张是"agent 只读像素+a11y，读不到 store"。图里 Agent 只有一个方块加双向箭头，**没有画出"Agent 看到什么 / 看不到什么"的隔离带**。而 `Read state`/`Environment APIs` 能读 store——但没有一条视觉线说清"读 store 是评测器特权，不是 agent 通道"。这恰恰是你和真机 benchmark 的关键区别，现在完全没立起来。

- **GUI 与 tools 同权的边界含糊**。图里 tools 和 GUI 是两个并列大框，箭头都指向同一 store，容易被读成"两条等价通道"。你的硬约束是：tools 与 click 占同一动作槽、写同一 store、**但不等价**（tools 以查询/定位/草稿为主，预填≠提交）。伪代码里 `write: none` 是好的一笔，但没有一个视觉标记明确说"tool 这一步没提交、真正写入靠 GUI confirm"。现在读者可能误判 tools 也能直接写业务。

- **伪代码像装饰**。三块 `</>` 代码框（Tool action / Result / Environment APIs / GUI save / State excerpt）散在五处，密度不均、无编号、和回路不咬合。参考图的代码是 `init/predict/eval` 三个函数嵌在回路里，你的代码是飘在旁边的注释。

- **跨 App / 共享 OS 像贴纸**。主张要求"第二个 App 发生真实业务写入，不只当信使"。图里 `apps.calendar.events[]` 只是列了字段，**没有一个例子显示第二个 App 被写入**。共享 OS 那栏（Contacts/Intents/Locale）是一串图标 list，和上方 store、和 b010 例子没有任何连线，确实像贴纸。

- **数字口径**：`35 new · 64 installable` 合法，与 census 一致，✓。图里没出现 215/成功率/训练侧 110，避免了打架，好。但也因此没有一处提示"这是环境 census，不是任务/成功率"，caption 里可加一句防混淆。

- **"same object"/"same record"重复三次**：截图下 Open1500/Saved1580、伪代码 Result、store 里 `1500→1580 ledger unchanged`、底部 State excerpt、右下 UI and store agree——**同一件事讲了五遍**，占了大量版面，却把"回路/隔离/跨App写入"三件更重要的事挤没了。

## 3. 张力重构建议（这张需要重画信息结构，不只是美化）

**保留双栏骨架，但把版面预算从"重复讲 b010 身份不变"转移到"评测回路 + Agent 隔离 + 跨App写入"。**

建议的四模块与对照轴：

- **A. Coverage（左窄栏）**：七领域 + `35 new / 64 installable apps`。保留，压窄。caption 明确"environment census, not the 215-task benchmark"。
- **B. Observation vs. Privileged read（新增隔离带，核心）**：画一条水平隔离线。线上方 = **Agent 能看**：Screenshot(pixels) + A11yTree。线下方 = **只有 Evaluator 能读**：business stores。Agent→Action(click / tool-call 同一槽)。用一个"锁"或"虚线墙"表明 store 对 agent 不可见。这是你区别于真机的一等主张，必须占中央显眼位。
- **C. 单个 b010 例子（收缩到一行流程）**：`tool find/open (write:none) → GUI edit 1500→1580 → confirm(commit)`。只画一次身份不变，别画五次。明确标 tool 步骤 `no commit`、GUI confirm 才 `commit`。
- **D. Task-level loop with verdict（新增，替代弱回路）**：`reset(inject config) → Agent acts (GUI/tool) → read stores → diff(target) → ✓/✗`。给编号①–⑤，终点两个出口 Pass/Fail，判定框写 `state diff on business objects, not screenshots / not path`。这直接对标参考图的 init-predict-eval-Complete/Incomplete。
- **可选 E. Cross-app 小插图**：一个任务写入 App1.orders 且 App2.calendar.events —— 两个 store 都出现 `insert/update`，标注"both apps write, not messenger"。哪怕小也要有一处真实第二写入。

不该用的数字：成功率、215 分布、训练侧 110、任何 benchmark 对照。这是环境图，只承载 census + 机制。

## 4. 视觉元素逐项优化（若沿用现结构）

- **回路加编号 + 出口**：Reset①→Action②→Read③→Diff④→Pass/Fail。终点补 ✓/✗ 两个出口。
- **箭头语义分色**：control/reset 用一色（灰虚线），data-write（GUI confirm→store）用第二色（绿实线，表"真实写入"），privileged read（store→evaluator）用第三色。现在蓝虚线/绿实线混用，`same object` 绿线和 `state read` 绿虚线语义不同却同色，要分。
- **tool "no write" 视觉标记**：`write: none` 那行加一个灰色徽标 "read/draft only, no commit"，和 GUI save 的绿色 "commit" 徽标对照。这一对是"tools 与 GUI 不等价"的唯一证据，必须显眼。
- **Agent 观测标注**：Agent 方块上方明确写 `sees: pixels + a11y tree`，`cannot read: business stores`。
- **伪代码收敛**：五个 `</>` 框合并到两个——一个"per-task evaluator (reset/read/diff)"，一个"b010 action trace"。删掉 State excerpt（和 store 框重复）。
- **共享 OS 那栏**：从 icon-list 改成"至少一条连线"接到某个 store 或 intent 例子（如 app switching→跨App），否则删掉降密度。
- **截图裁切**：两张手机截图现在信息量低（大量灰行），可裁到只保留"金额 1500 / 1580"那两行 + 顶栏，放大对比。
- **字号**：store 里中文/英文混排字号偏小，`ledger: unchanged` 是关键词应加粗。

## 5. 顶会重绘方案（推荐推倒重画信息层）

**模块清单（左→右，上→下）**
1. 左窄栏 Coverage（census）
2. 中央上：**Observation boundary** — Agent | sees pixels+a11y | acts (GUI click / tool-call, same slot)
3. 中央：**Single-object trace** b010（tool open no-commit → GUI confirm commit → 1500→1580, identity fixed）
4. 右：**Per-app stores**（含一处 cross-app write）
5. 底部横贯：**Task loop + verdict** ①reset/inject ②agent act ③read stores ④diff ⑤Pass/Fail，判定注 "diff on business state, path-agnostic"

**阅读顺序**：Coverage → Agent 只能看像素 → 动作打到 tools/GUI → GUI confirm 才写 store → 评测器读 store 做 diff 判成败。

**建议英文 caption**：
> *MobileGym++ is a resettable, simulated commercial-App world (35 new / 64 installable apps across 7 domains) hosted in a browser. Agents observe only pixels and the accessibility tree and cannot read app business stores; GUI clicks and app-native tool calls share one action slot and write the same store (tool calls query/draft only, GUI confirm commits). Each task resets state, lets the agent act, and is scored by a diff on business objects—independent of the pixel path taken.*

## 6. 必须删掉或改口的元素

- 删 `State excerpt` 框（与 store 框语义重复）。
- 删或合并 `Result · same record` 与底部 `UI and store agree`（同一断言三处）。
- 「same object」重复标注保留一处即可。
- 共享 OS icon-list 若不连线则删两项，只留和例子相关的一项。
- 全图不得出现 "mock"（现无，保持）；不得出现 API/function/tools 混称（现称 tool 一致，✓ 保持）。

## 7. 优先级

- **P0** 底部回路加编号①–⑤并补 Pass/Fail 出口，判定框注明"diff on business state, not screenshots/path"——立起评测协议。
- **P0** 加 Agent 观测隔离带：`sees pixels+a11y / cannot read stores`，store 用虚线墙隔在 evaluator 侧。
- **P0** tool 步标 `no commit / read-draft only`，GUI confirm 标 `commit`——立起"tools≠GUI 等价"。
- **P1** 删除重复的 same-record/state-excerpt，把版面还给回路与隔离；伪代码从 5 框收到 2 框。
- **P1** 加一处 cross-app 真实写入示例（App2.events 被 insert/update）。
- **P1** 箭头三色分语义：control-reset / data-write / privileged-read。
- **P2** 截图裁切放大到只显金额行；store 关键词加粗；caption 注明"census, not the 215-task benchmark"。
