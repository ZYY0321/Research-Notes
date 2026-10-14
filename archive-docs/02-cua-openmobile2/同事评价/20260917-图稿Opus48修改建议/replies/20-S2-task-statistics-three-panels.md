# 20-S2-task-statistics-three-panels

- model: `claude-opus-4-8`
- elapsed_s: 57.5
- finish_reason: stop
- usage: {"prompt_tokens": 3540, "completion_tokens": 2534, "total_tokens": 6074, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 3540, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: S2-task-statistics-three-panels.png

---

# S2 三联统计审稿意见

## 1. 这张图现在在说什么

三联板：(a) 堆叠柱把 215 拆成 1 app（111）vs 2+ apps（104=72+27+5），(b) 双环饼把同一拆分再画一遍（内环 1app/2+，外环 1/2/3/4 app），(c) 横条给出最高频的 6 个 App（Notes 39、Kapi 23…）。顶部 census 写"215 tasks · 48 apps · 104 tasks 2+ apps (48.4%)"。底注明确"App count 只描述覆盖，不建立跨 App 业务依赖"——这条守得对。

## 2. 内容张力诊断

**致命：口径打架，直接违反硬约束。** 本图用的是 **111/72/27/5**，而现稿正式口径是 **109 单 / 74 双 / 27 三 / 5 四**。约束里已经点名这个冲突——现在这张图站在了"错误的一边"。整张图的所有百分比（51.6%/33.5%/12.6%/2.3%、48.4%）都建立在 111/72 上，一旦改回 109/74，全盘要重算。必须先冻结口径。

**census 数字也可疑：**"48 apps"——环境 census 是可安装 64（新构造 35），Bench 用到的 App 子集写成 48 需要有出处，别和 64/35/110+ 任何一个数打架。若 48 是"Bench 215 实际触及的 App 数"，要在注里说死，否则审稿人会和你其它表里的数字对不上。

**(a) 和 (b) 是同一份数据画两遍。** 堆叠柱的三段 = 双环外环的三瓣，信息 100% 冗余。这是本图最大的浪费：三联里有两联在说同一句话。

**与 F5/fig-C 的重复判断：** 你没附 F5，但"任务组成 / App 数分布"这类构成统计极可能与 F5/fig-C 的 Bench 概览重叠。**任务组成（单/多 App 分布）在正文出现一次即可。** 若 F5 已经有单/多 App 拆分，则本图 (a)(b) 两联应整体让位，只保留 (c) 或改造。

**张力本身不足：** 三联全是"我们的 Bench 长什么样"的自描述，没有任何对照轴，撑不起顶会正文的核心主张。48.4% 多 App 看似是卖点，但底注自己承认"不建立业务依赖"——那这个数就不是"跨 App 难度"的证据，只是覆盖统计，说服力被自己削掉一半。

## 3. 张力不够 → 应该改成什么

**正文最多留一联，且要换成有对照/有主张的版本。**

- **删 (a)：** 与 (b) 完全冗余，二选一，柱状不如环直观地表达占比，但环也非必要（见下）。
- **(b) 双环降级：** 单/多 App 的 4 段占比用一根**水平 100% 堆叠条**就够，别用双环——双环内外环重复同一拆分，是 OSReward 的花架子，信息密度低。
- **(c) 高频 App 保留但升级：** 单纯 top-6 频次不够。改成能体现"七领域覆盖"的对照——按 domain 分组着色，或补一句"215 任务触及 X 个 App，覆盖 7 领域"，把覆盖广度说成主张。

**真正有张力的替换方向**（把这联换成对照，而非自描述）：
- **难度 × 结果热图/散点：** 单/双/三/四 App 任务的**成功率梯度**（锁表：Gemini GUI 58.6% 总体，按 App 数分桶）。这才是"多 App 更难"的证据，比占比强十倍。数字只能用 58.6%/68.4%（Gemini）或 68.8/79.1（gpt-5.6-sol），**不得**用 369 的 57.2/68.3。
- 若无分桶成功率数据，则退而用**业务写入次数分布**（跨 App 里第二个 App 真发生写入的比例），直接回应"App 个数≠业务依赖"这一你自己立的靶。

**该用的合法数字：** 215、109/74/27/5、七领域、64 可安装、35 新构造。
**不该出现：** 369 系、Qwen 37.7 拼 Gemini、跨 benchmark 79.2/48.3/60.8。

## 4. 若保留（视觉逐项）

假设只留 (b)→堆叠条 + (c)：
- **(b) 双环→单条：** 取消内环，浪费空间；4 段水平条，2.3% 的"4 apps"贴标签在外侧引线，别塞进环里。
- **(c) 数值标签颜色：** 蓝色数字与蓝色标题混，条本身用中性灰、Notes 用主色高亮即可。
- **底注两行"one task can count toward several apps"** 很重要，保留，但字号可与主注统一。
- **census 行**的"48 apps"移到注里说清定义，别放在最显眼的副标题。

## 5. 顶会重绘方案

**模块清单（正文单联，半栏）：**
1. 一根水平 100% 堆叠条：单 109 / 双 74 / 三 27 / 四 5，段内标 n 与 %。
2. 其下叠一行小字：215 tasks · 7 domains · 48 apps touched。
3. （可选，若版面允许）右侧 mini 条：各 App 数分桶的成功率（Gemini GUI），点出难度梯度。

**阅读顺序：** 总量 → 单/多拆分 → 难度梯度。
**(a)(c) 移入附录**，(c) 高频 App 表格化即可。

**Caption（英文）：**
> "Task composition of the frozen 215-task benchmark: 109 single-app and 106 multi-app tasks (74/27/5 spanning two/three/four apps). App count reflects task coverage, not cross-app business dependency; success drops monotonically with app count (Gemini 3.1, GUI, table X)."

## 6. 必须删掉或改口

- **删** 111/72，全部改为 109/74，重算所有百分比。
- **删** (a) 堆叠柱（与 b 冗余），或删 (b)，二选一。
- **删** 双环内环（重复外环拆分）。
- "48 apps"给出定义或移入注；确认不与 64/35/110+ 冲突。
- 若 F5/fig-C 已有单/多 App 拆分，本图整联让位，只留升级后的 (c) 或难度对照。

## 7. 优先级

- **P0** 全图 111/72 改回 109/74，重算 51.6/33.5/48.4 等所有百分比——口径必须与正文一致。
- **P0** 与 F5/fig-C 去重：确认单/多 App 拆分只在正文出现一次，本图删掉重复联。
- **P1** (a)(b) 二选一，双环降为单条水平 100% 堆叠。
- **P1** 把留下的一联换成有对照的版本（按 App 数分桶的成功率梯度，只用 58.6/68.4 或 68.8/79.1）。
- **P2** (c) 按 7 领域着色或补覆盖数，"48 apps"定义写进注，其余频次统计移附录。
