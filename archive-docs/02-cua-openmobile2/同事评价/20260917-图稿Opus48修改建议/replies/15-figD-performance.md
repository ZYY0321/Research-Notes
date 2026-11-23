# 15-figD-performance

- model: `claude-opus-4-8`
- elapsed_s: 59.9
- finish_reason: stop
- usage: {"prompt_tokens": 3317, "completion_tokens": 2883, "total_tokens": 6200, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 3317, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: fig-D-performance.png

---

# 审稿意见：fig-D

## 1. 这张图现在在说什么

图分两栏。左栏"跨 benchmark 对比"，把 AndroidWorld 79.2%、MobileWorld 48.3%、MobileGym++ 60.8% 三个数放在同一根横轴上，统一标注为 Gemini 2.0 Flash / GUI-only，并画一条虚线把本工作 60.8% 拉成参照。右栏"GUI-only vs Hybrid"，用 37.7% 与 68.4% 两根柱子，配一支黄色双向大箭头写 +30.7pp，暗示加了 Hybrid 通道涨了 30 个点，还挂了"119/215 tasks invoked tools"的注。整张图想说：本 Bench 比同类难度居中且合理，Hybrid 通道带来巨大提升。

## 2. 内容张力诊断

两栏都是硬伤，且都是会被审稿人当场抓的口径错误。

- **左栏协议不可比被画成同尺**：79.2/48.3/60.8 来自不同 benchmark、不同任务集、不同 census、不同成败判定（你们看业务状态差分，别人可能看路径/页面）。把三者放同一根 0–100 横轴、还画统一虚线，等于宣称"可直接比较"。这是方法论错误，不是美化能救的。而且 60.8 这个数不在你合法锁表口径内（合法只有 GUI 58.6 / Hybrid 68.4，gpt-5.6 68.8/79.1），来源可疑。
- **右栏是拼图造假级误导**：37.7 是 Qwen 的 GUI 锁表成绩，68.4 是 Gemini 的 Hybrid 成绩。把两个不同模型的两种设定拼成一根 +30.7pp 的因果箭头，等于宣称"Hybrid 使成功率暴涨 30 点"。这既跨模型又跨通道，30.7pp 完全是伪差值。硬约束明确禁止把 Qwen 37.7 与 Gemini 68.4 拼一张对比，也禁止把 Hybrid 写成因果涨分。
- **"119/215 invoked tools"漂在图里但没解释**：调用了 tools 不等于因为 tools 才成功（预填不等于提交）。这条注在当前语境里加固了错误因果。
- **215 口径**：右栏标 215 tasks 尚可，但没体现单/双/三/四应用结构，也没提 109/74/27/5 与 111/72/27/5 的冲突口径——这张图不承担这个，但不要在此处引入新的数字。

结论：**两栏都必须推倒重画**，不是调色能过审的问题。

## 3. 重画方案（内容层）

### 左栏——两条路走一条
- **方案 A（推荐，最安全）：直接删掉跨 benchmark 柱状对比。** 换成一张 census / 难度构成图（单/双/三/四应用任务数），用你合法的分布口径讲"本 Bench 覆盖了跨 App 业务依赖"。
- **方案 B（若一定要提同类工作）：改成"不可比对照表"**，不是柱状图。表格列出 AndroidWorld / MobileWorld / MobileGym++ 的 census、observation、success criterion、tool 通道，明确写 **Protocol not directly comparable**。数字若只是文献占位，就不放成功率，只放规模/性质。绝不放同一根成功率轴。

### 右栏——同模型 paired 对照
- 只画 **同一个模型** 的 GUI vs Hybrid：Gemini 58.6% vs 68.4%（分数是 126/215 vs 147/215）。可选再画一组 gpt-5.6-sol 68.8% vs 79.1% 做第二个 model 的分面。
- **删掉 +30.7pp 大箭头**。paired 提升是 58.6→68.4，即 +9.8pp，且必须报告为**同一模型内的观测差异，不宣称因果**。
- **核心该加的是 discordant 分析**：报告 33 例 Hybrid 成功而 GUI 失败、12 例 GUI 成功而 Hybrid 失败（33/12）。这才是有信息量的证据，说明 Hybrid 不是单调更强，而是有 trade-off。可用一个 2×2 concordance 小矩阵或分组柱表达。
- caption 里明确：Hybrid 是同一 store 上的可选第二通道（plus / experimental），不是 Bench 存在的理由，两通道不完全等价。

### 合法/非法数字清单
- 可用：Gemini GUI 58.6%(126/215)、Hybrid 68.4%(147/215)、gpt-5.6 68.8/79.1、discordant 33/12。
- 禁用：79.2/48.3/60.8 同轴、37.7 vs 68.4 跨模型差、+30.7pp、369 的 57.2/68.3、Qwen×Gemini 混拼。

## 4. 视觉优化（此图先解决内容，视觉暂缓）

当前视觉本身尚可（配色克制、字号清楚），但因为内容要重画，逐项优化意义不大。仅保留可复用的：横轴 0–100 与右栏 0–80 的网格线风格、字体、留白比例可沿用到重画版。黄色双向箭头这种"因果暗示"符号在任何版本都不要再出现。

## 5. 顶会可投稿重绘方案

**模块清单（左右双栏）：**
- **(a) 左：Bench 难度构成**——横向堆叠或分组柱，x 轴任务数，四组=单/双/三/四应用（用你确定的一个合法口径，别两套并存）。
- **(b) 右：同模型 GUI vs Hybrid paired**——两个模型分面（Gemini / gpt-5.6-sol），每面两根柱 GUI vs Hybrid，柱顶标 n/215。旁附一个小 2×2 concordance 表：both✓ / GUI✓Hybrid✗(12) / GUI✗Hybrid✓(33) / both✗。

**阅读顺序**：左看 Bench 覆盖了多 App 业务依赖 → 右看同一模型加通道的成对变化及其非单调性（discordant）。

**建议英文 caption：**
> **Figure D.** (a) Task composition of MobileGym++ (215 tasks) by number of apps with real business writes. (b) Per-model paired comparison of GUI-only vs. the optional Hybrid channel on the frozen 215-task suite (Gemini: 58.6%→68.4%, 126/215 vs. 147/215). The inset concordance table (33 Hybrid-only successes, 12 GUI-only successes) shows the two channels are not strictly ordered; Hybrid is an optional second channel over the same store, not a prerequisite of the benchmark.

## 6. 必须删掉或改口的元素
- 删：左栏 79.2/48.3/60.8 同轴柱 + 60.8 虚线。
- 删：右栏 37.7% 柱（Qwen 锁表）、+30.7pp 黄色双向箭头。
- 删：60.8% 这个未在合法口径内的数。
- 改口：标题 "Performance Results" → 不要暗示单一强弱；"119/215 invoked tools" 若保留须改为中性描述且不与成功率因果绑定。
- 改口：不出现"Hybrid 涨 30 点"任何暗示。

## 7. 优先级
- **P0**：删掉右栏跨模型 37.7 vs 68.4 及 +30.7pp 箭头，改为同一模型 paired（Gemini 58.6 vs 68.4，标 n/215）。
- **P0**：删掉左栏跨 benchmark 同轴柱，改为难度构成图或明标"protocol not comparable"的对照表。
- **P1**：右栏加 33/12 discordant concordance 小矩阵，caption 声明两通道非严格有序、Hybrid 为可选第二通道。
- **P1**：全图移除 60.8% 及任何非合法口径数字，统一到 215 锁表口径。
- **P2**：沿用现有字体/网格/配色，两栏纵横轴刻度对齐，双栏宽度下保证柱顶 n/215 标签可读。
