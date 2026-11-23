# 16-figE-tool-usage

- model: `claude-opus-4-8`
- elapsed_s: 56.9
- finish_reason: stop
- usage: {"prompt_tokens": 3257, "completion_tokens": 2600, "total_tokens": 5857, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 3257, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: fig-E-tool-usage.png

---

# fig-E 审稿意见

## 1. 这张图现在在说什么

左侧棒棒糖图列出 Hybrid 轨迹中调用次数 top 15 的 app-native 工具（broadcast·search shows 44 次居首），按七领域配色；右侧汇总栏给出 406 次总调用、3995 次 GUI 动作、110 种被用工具、306 种可用工具、119/215 任务用了 ≥1 工具。整体是一张"工具调用排行榜 + 规模面板"。

## 2. 内容张力诊断

**这张图目前讲的是"哪个工具被调最多"，但论文想讲的是"工具是按每个 App 的业务对象稀疏设计的、且 GUI-only 仍是一等公民"。二者错位。**

- **排行榜会误导。** 你自己已承认调用次数被失败重试拉高——那么 top1 的 44 次到底是"这个动机常见"还是"这个操作难、反复重试"，图上分不出来。审稿人可能读成"某工具超常被依赖"，与稀疏设计主张相悖。
- **catalog 与本次调用混在一个面板。** 306 available vs 110 used 是设计侧统计，406 invocations 是运行侧统计，你自己声明"不是同一证明"，但右栏把它们竖排在一起，视觉上就是同一把尺子。
- **3995 GUI actions 这个数被埋没了。** 这恰恰是最该突出的：GUI 动作 ≈ 10× 工具调用，406/(406+3995)≈9% 的动作才是工具——这直接支撑"GUI-only 一等公民、工具是可选第二通道"。现在它只是右栏第二行小字。
- **119/215 只说了 55% 任务碰过工具**，反过来 45% 任务纯 GUI 完成，这条对主张更有力，但没被强调。
- **数字口径无冲突**（都是 Hybrid 侧运行统计），但 x 轴标题"215 Hybrid trajectories"与 119/215 并列时，容易让人以为 44 次分布在 215 条里——需要说明是跨全部 Hybrid 轨迹累计。
- **工具命名 `broadcast·search shows` 是查询类、`kapi·prepare bill draft` `calendar·prepare event` 是草稿类**——这正是"查询/定位/草稿为主、预填不等于提交"的证据，但图上完全没利用这个语义分层。

结论：**排行榜撑不住"稀疏、按动机设计"的主张，需要换轴。**

## 3. 张力不够——改成什么

把"调用排行榜"改成"**按 App 组织的稀疏工具目录 + 动作预算对比**"两块：

**面板 A（替代排行榜）：分组条形，按 App 分面，动作类型分层。**
- 纵轴按 App 分组（broadcast / notes / wechat / alipay / ctrip …），每个 App 下列出其工具。
- 用**动作动机类别**填色而非领域：query / locate / draft(prepare) 三类——直接展示"查询定位草稿为主"。
- 长度可以保留调用次数，但**必须标注"counts include retries; not a preference signal"**，或改用"被用于多少条 distinct 任务"（去重后不受重试放大），这个数更诚实。

**面板 B（最该突出的对比，替代右栏堆叠数字）：动作预算分解。**
- 一根 100% 堆叠横条：GUI actions 3995 (91%) vs tool invocations 406 (9%)。caption 点明工具是可选第二通道。
- 一根横条：pure-GUI tasks 96/215 (45%) vs tasks with ≥1 tool 119/215 (55%)。

**catalog 单独一句注释，不进主图坐标系**："306 tool types available across 64 apps; 110 used in this Hybrid run. Availability and usage are separate accountings."

- **合法数字**：406 / 3995 / 110 / 306 / 119/215 均可，但要分区呈现；建议补 distinct-task 计数替代原始调用数。
- **不该用**：不要拿这张图去和 GUI-only 成功率比、不要暗示工具调用越多越好。
- **caption 主张**：工具稀疏、按 App 业务对象设计、GUI 仍是主通道。

## 4. 若张力基本成立——视觉优化（在保留排行榜前提下）

- 棒棒糖点大小统一，末端数字改为右对齐、留 2px 间距。
- 领域图例挪到面板外顶部横排，别压在数据区。
- `tencent meeting·calc part` 等中点分隔符 `·` 与 App 名混淆，建议 `broadcast — search shows` 或加轻底纹分组。
- 右栏 5 个大数用分隔线明确切成"运行侧 / 设计侧"两组。
- x 轴到 55 有空白，收到 ~48。

## 5. 顶会重绘方案（推荐推倒重来）

**模块清单**
1. 顶部一行标题：Tools are a sparse, motive-designed second channel.
2. **B-动作预算**（最上，最抢眼）：两根 100% 堆叠条 → GUI 91% / tool 9%；pure-GUI 45% / with-tool 55%。
3. **A-按 App 稀疏目录**：小提琴/分组点，纵轴 App，色=query/locate/draft，长度=distinct tasks（不是原始调用）。
4. 底部脚注：catalog 306/110 说明 + "counts exclude nothing but include retries; see text"。

**阅读顺序**：先看 B（工具只占 9%、45% 任务零工具）→ 再看 A（用的工具都是查询/定位/草稿、每 App 稀疏）→ 脚注（可用 vs 已用是两回事）。

**建议英文 caption**：
> *App-native tools form a sparse, per-app second channel in Hybrid runs: only 9% of actions are tool calls (406 vs 3,995 GUI actions) and 45% of tasks use no tool at all. Used tools are dominated by query/locate/draft intents (drafts are pre-fills, not submissions); raw call counts include retries and do not indicate preference.*

## 6. 必须删掉或改口的元素

- **删/降级"总调用排行榜"作为主图**——排行榜诱导"多即好"，与稀疏主张冲突。
- **右栏 306 available 与 406 invocations 不能竖排在同一列**，须视觉分区并加"separate accounting"字样。
- x 轴或 caption 加"counts include retries"，否则 44 次会被误读。
- 不要出现"tools ≈ GUI"或"300+ tools 同权"暗示；不要用 mock。

## 7. 优先级

- **P0**：新增/上移"GUI 91% vs tool 9% + 45% 纯 GUI 任务"预算面板，作为读图第一眼。
- **P0**：主排名的长度轴改为 distinct-task 计数，或在图内显著标注"includes retries, not preference"。
- **P0**：把 306 available 从 406/110 运行统计中视觉隔离，注明"availability ≠ usage"。
- **P1**：条形填色由领域改为 query/locate/draft 动机类别，展示"按业务对象设计"。
- **P1**：图例移出数据区，工具名分隔符统一，x 轴收窄。
- **P2**：按 App 分面组织左图，凸显"每 App 稀疏"。
