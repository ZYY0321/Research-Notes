# 14-figC-bench-overview

- model: `claude-opus-4-8`
- elapsed_s: 61.1
- finish_reason: stop
- usage: {"prompt_tokens": 3305, "completion_tokens": 2697, "total_tokens": 6002, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 3305, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: fig-C-bench-overview.png

---

# fig-C 审稿意见

## 1. 这张图现在在说什么

三联图描述 215 题基准的结构：(a) 横向条形图给每题涉及的 App 个数（1/2/3/4 app）；(b) 饼图把同一分布换成百分比；(c) 棒棒糖图给最高频的十几个 App 及其领域配色。整体想说"benchmark 规模大、跨 App 占比高、覆盖多领域"。

## 2. 内容张力诊断

**核心问题：三块面板里有两块在讲同一个分布，第三块又暴露了会被审稿人抓住的软肋。**

- **(a) 和 (b) 完全冗余**：条形图和饼图是同一组数字 111/72/27/5 的两种画法，占了三分之二版面却只传递一个信息。顶会审稿人会立刻觉得"信息密度低、在凑版面"。
- **数字口径打架（致命）**：图里 111/72/27/5，正文口径是 109/74/27/5。1-app 差 2、2-app 差 2，合计仍是 215，说明这是两版数据没对齐。审稿人只要翻正文就抓到，直接质疑数据可信度。**必须先定死一个口径。**
- **"App 个数 ≠ 真跨 App" 完全没表达**：这是你自己点出的最关键主张——第二个 App 必须发生真实业务写入，不能只当信使。现在的图把"2 apps"直接等同于"跨 App 任务"，恰恰误导。审稿人会问：这 72（或 74）里有多少第二个 App 真写了 store？图完全答不了。
- **(c) 会反噬**：Notes 39、Kapi 23 主导，且都是 Productivity 蓝。审稿人一眼看到"高频集中在记事/草稿类"，会怀疑跨 App 只是"把结果记到 Notes"这种伪依赖，正好坐实你担心的 notes/kapi 主导。
- **标题 "48 apps"** 与环境 census（可安装 64）也需确认是否是同一口径；若 48 是 Bench 实际动用的 App 数要写清"used in bench"，别让人和 64 打架。

结论：**信息重复 + 数字打架 + 没回答"真跨"，张力不够，需重构。**

## 3. 张力不够 → 应该改成什么

**把"三个同分布"压成一个，腾出的版面回答"真跨 App"和"领域覆盖"。**

建议三面板改为：

**(a) 单一堆叠条 / 分组条：App 个数 × 是否真跨**
- 保留 1/2/3/4 app 一个维度（条形图，删饼图）。
- 每根 2+/3+/4 app 的条按"第二 App 真写入 store" vs "仅信使/读取"二次拆分，用深浅或纹理区分。这直接可视化你的核心定义：`apps involved` ≠ `business dependencies`。
- 合法数字用正文定死口径（109/74/27/5 或 111/72/27/5，二选一），别再出现两版。

**(b) 领域覆盖矩阵 / 分组条（替换饼图）**
- 七个领域 × 任务数（或 × 单/跨拆分），一眼看出"不是只有 Productivity"。这才是新增信息，不与 (a) 重复。

**(c) 高频 App → 改成"跨 App 边"或降权**
- 若保留高频条，把它排序后只标 top 几个，并加一句注明"frequency ≠ dependency"；或者更好：换成**跨 App 依赖的 App-pair 热力/弦图/桑基**，展示第二 App 真正写入的对象分布，正面反驳"都是 Notes 兜底"。
- 若 Notes/Kapi 确实高，就诚实展示但配上"真写入 vs 信使"的比例，把它从弱点变成证据。

不该用的数字：不要在同一图里混 111 和 109；不要引入 64/48 之外未定义的 app 计数。

Caption 主张（英文见 §5）应显式写"multi-app tasks require genuine cross-app business writes, not app count"。

## 4. 视觉元素优化（若沿用当前布局也要改的）

- (a) 条形已 OK，数值标签贴近条尾即可；y 轴 "1 app…4 app" 保留，字号可略增。
- (b) 若坚持保留饼图：中心 "215 tasks" 与切片百分比信息重复，且 "tasks" 灰字太淡近乎不可读——但建议直接删饼图。
- (c) 图例方块压在 "Kapi/Notes" 数值标签上（23、39 被挡），**必须移出绘图区**，放右侧或底部单行。
- (c) 领域配色只有 Productivity 蓝出现多次、其余色几乎不出场，配色浪费；且 Finance 蓝 与 Productivity 蓝 太接近，Alipay/Kapi 难分。换成色相差更大的定性色板。
- 数值标签 "Slack13" "Kapi23" 数字紧贴 App 名和棒棒糖头，留 2–3px 间距。
- 总标题 "MobileGym++" 若非正式名请统一；副标 "48 apps" 需标"used in benchmark"。

## 5. 顶会重绘方案

**模块清单（三面板，横排）**
1. **Panel A — Task complexity**：分组/堆叠条，x=task count，y=1..4 apps，每条按 `genuine cross-app write` / `single-app or messenger-only` 双色拆分。
2. **Panel B — Domain coverage**：七领域 × 任务数条形，可再叠单/跨。
3. **Panel C — Cross-app dependency structure**：App-pair 弦图或 top-k 依赖边，显示"第二 App 写入哪些业务对象"，附注 frequency≠dependency。

**阅读顺序**：A（题有多复杂 + 多少是真跨）→ B（覆盖哪些领域）→ C（跨到哪、写了什么），逐层深入，无重复分布。

**建议英文 caption**：
> **Figure C. Benchmark composition of the 215-task suite.** (a) Task complexity by number of apps involved, split by whether the secondary app performs a genuine business-state write versus acting only as a messenger; (b) coverage across seven domains; (c) cross-app dependency structure among the most frequently involved apps. App count alone does not imply a cross-app dependency—only tasks with a real secondary write are counted as cross-app.

## 6. 必须删掉或改口的元素

- **删饼图 (b)**：与 (a) 完全冗余。
- **改口数字**：111/72/27/5 与正文 109/74/27/5 二选一，全稿统一。
- **图例移出绘图区**，不得遮挡数值。
- **标题 "48 apps"** 标明口径，别与 census 64 混。
- (c) 若保留，必须加 "frequency ≠ dependency" 注，避免被读成 Notes 主导。

## 7. 优先级

- **P0**：统一 111/109 口径，全稿一致——数字打架是拒稿级信号。
- **P0**：删饼图，用腾出的版面加入"真跨 App 写入 vs 信使"拆分（Panel A 二次分色）。
- **P0**：图例移出，解除对 Kapi/Notes 数值的遮挡。
- **P1**：把 (c) 换成或补成跨 App 依赖结构（弦图/pair），正面回应 notes/kapi 主导质疑。
- **P1**：新增/替换领域覆盖面板，避免三块讲同一分布。
- **P2**：更换定性色板拉开 Finance/Productivity 蓝，标题命名与 "used in benchmark" 口径统一。
