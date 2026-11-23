# 18-figG-cross-app

- model: `claude-opus-4-8`
- elapsed_s: 49.8
- finish_reason: stop
- usage: {"prompt_tokens": 3551, "completion_tokens": 2277, "total_tokens": 5828, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 3551, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: fig-G-cross-app.png

---

# fig-G 审稿意见

## 1. 这张图现在在说什么

图用两组堆叠柱对比"单 App"（111 题）与"跨 App"（104 题）下 GUI vs Hybrid 的成败构成：每组内左柱 GUI、右柱 Hybrid，实心为成功、斜纹为失败，柱高等于该桶题量。标题直接把 overall GUI 37.7% / Hybrid 68.4% 写进去，柱上标了 29.8% / 61.5% 两个跨 App 成功率。意图是说"跨 App 更难、Hybrid 相对更抗跌"。

## 2. 内容张力诊断

这张图目前**不能进论文**，问题是致命级的：

- **数字是摊出来的，不是逐题统计。** 标题的 37.7% 来自 Qwen，68.4% 来自 Gemini——这正是禁令里"不要把 Qwen 37.7 和 Gemini 68.4 拼成一张对比"的那对数字，你把它拼成一张图的总标题了。这是口径打架的最严重形态：两个不同模型的成功率被当成同一把尺子的"overall"。
- **estimated distribution 本身违规。** 柱内的 success/fail 切分不是逐题真结果，是按总成功率反推的比例。审稿人一眼看出这是"编"出来的分布，直接判图不可信，进而波及全文。
- **题量口径打架。** 单 App 111 / 跨 App 104，与冻结口径 109/74/27/5 不一致（现稿另有 111/72/27/5 的冲突稿）。这里的 111 + 104 = 215 是把 74+27+5=106 硬凑成 104 的另一种口径，又是一处冲突。
- **"跨 App"未按真跨口径。** 104 里含"第二 App 只当信使"的题，没保证第二 App 有真实业务写入。分组本身不干净。
- **paired 信息全丢。** GUI 与 Hybrid 是同一批题的两个通道，本该做逐题配对（同题 GUI 失败 / Hybrid 成功 = 通道净增益）。现在画成两根独立柱，读者无法读出"Hybrid 到底救回了哪些题"，反而容易被读成因果涨分。

结论：换图种 + 换数字 + 先冻结逐题标签，缺一不可。

## 3. 应该改成什么（张力不够，重做）

**第一步——冻结逐题标签（画图前必须完成）：**
对每个锁定模型，导出每题在 GUI 通道 / Hybrid 通道下的 0/1 真实成败，落到 CSV：`task_id, group(single/cross), gui_pass, hybrid_pass`。跨 App 组只保留"第二 App 有真实业务写入"的题，其余移出或单列。

**第二步——用合法数字。** 一张图只用一个模型一把尺子：
- 主图建议 Gemini 3.1：GUI 58.6% (126/215) / Hybrid 68.4% (147/215)；
- 或 gpt-5.6-sol：68.8 / 79.1。
- **禁止** 37.7（Qwen）与 68.4（Gemini）同框；禁止 369 口径的 57.2/68.3；禁止跨 benchmark 的 79.2/48.3/60.8。

**第三步——换图种为 paired 2×2 混淆流：** 每组（single / cross）画一个 GUI→Hybrid 的转移条：
- both pass / GUI fail→Hybrid pass（净救回）/ GUI pass→Hybrid fail（回退）/ both fail。
这才是"同一 store 上第二通道"的诚实表述，能直接读出 Hybrid 净增益而不暗示因果。

**caption 主张：** "On identical tasks, Hybrid recovers N cross-app tasks that GUI-only fails, while regressions are rare; cross-app remains harder for both channels."（数字用冻结后的真实计数填）。

## 4. 视觉元素优化

内容重做前视觉优化无意义，此节从略（当前配色/斜纹本身可读，可保留到重画版）。

## 5. 顶会可投稿的重绘方案

**模块清单：**
- 顶部一行两个小面板：Single-app / Cross-app（真跨口径）。
- 每面板一根横向 paired-outcome 条：4 段 [both-pass | GUI✗→Hybrid✓ | GUI✓→Hybrid✗ | both-fail]，段上标真实计数。
- 面板右侧两行小注：GUI n/215、Hybrid n/215（同一模型）。
- 底部一行灰字标模型名 + census 口径（题量取冻结值 109/74/27/5，其中单 App 109、跨 App 106，并说明跨 App 按"第二 App 有业务写入"筛后为 m 题）。

**阅读顺序：** 模型名 → 左面板单 App 配对 → 右面板跨 App 配对 → 对比"净救回段"是否在跨 App 更宽。

**建议英文 caption：**
> "Paired per-task outcomes (Gemini 3.1, N=215) for single- vs cross-app tasks. Bars decompose GUI→Hybrid transitions on identical tasks; the green segment counts tasks recovered by the optional second channel. Cross-app tasks are restricted to those with a genuine business-state write in the second app."

## 6. 必须删掉或改口的元素

- **删标题** "estimated distribution, overall GUI 37.7% / Hybrid 68.4%"——两处违规同时存在。
- **删** 所有"按总成功率反推"的 success/fail 比例。
- **改** 题量 111/104 → 冻结口径；跨 App 标明真跨筛选后计数。
- **改** "Hybrid"任何暗示因果涨分的措辞为"optional second channel on the same store"。
- **不要**在同图混两个模型。

## 7. 优先级

- **P0** 冻结逐题 gui_pass/hybrid_pass CSV，删掉标题里的 37.7/68.4 和 estimated distribution。
- **P0** 单图只用一个模型一把尺子（首选 Gemini 58.6/68.4），题量改回冻结口径。
- **P0** 跨 App 组只保留第二 App 有真实业务写入的题，并在图注写明筛选与计数。
- **P1** 图种改为 GUI→Hybrid paired 2×2 转移条，突出"净救回"段。
- **P2** caption 按第 5 节改写，措辞去因果化。
