# 10-fig3-tool-coverage

- model: `claude-opus-4-8`
- elapsed_s: 61.0
- finish_reason: stop
- usage: {"prompt_tokens": 4870, "completion_tokens": 2773, "total_tokens": 7643, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 4870, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: fig-3-tool-coverage.png

---

# fig-3 审稿意见

## 1. 这张图现在在说什么

左图 (a) 用横向条形图展示 40 个 App 各自声明的候选工具类型数量（2–8 个），按域配色，声称"40 apps expose tools, ≥2 shown"。右图 (b) 用堆叠条形对比"Tool-active tasks"（119 题，76% solved）与"GUI-only tasks"（96 题，59% solved），配文字承认工具"help but leave a large residual of failures"。整体想传达：工具生态覆盖广，且工具可用性与更高成功率相关但非捷径。

## 2. 内容张力诊断

**右图 (b) 是致命问题，必须重做。** 你自己已经点破：锁表口径是**同一 215 题的 paired 协议**（GUI 58.6% = 126/215，Hybrid 68.4% = 147/215）。但 (b) 把任务**切成两群**（119 tool-active / 96 GUI-only），画出 76% vs 59%。这是两个根本不同的东西：

- paired 协议 = 同一批题在两种通道下各跑一遍，看配对差分（+9.8pp）。
- 现在的图 = 把题按"是否有工具可用"分成两组，比较组间成功率。

后者几乎必然被读成"给了工具就涨 17pp"的**因果错觉**，而且 76/59 这两个数字**在你的合法数字清单里根本不存在**——90/119 和 57/96 是新造的、来源不明的切分，与 58.6/68.4 对不上。这属于"发明数字"+"把选择效应画成因果"，双重红线。

**左图 (a) 相对安全但有两处要修：**
- 标题"40 apps expose tools"与正文"约 52 apps 暴露 tools"**打架**。图只画了 ~40 个 App（≥2 才显示），但把"≥2 shown"混进"expose tools"的口径，读者会以为只有 40 个暴露工具。必须澄清：暴露工具的总数 vs 图中因阈值可见的数量。
- "Candidate tool types defined for the app"是**声明的类型数**，不是实际暴露/可调用数。右侧文字已诚实说明这是 declared types 而非 call frequency——好，但要保证 X 轴标签、标题、caption 三处口径一致，别让读者以为这是"工具被调用了多少"。

## 3. 张力不够——右图 (b) 必须换掉

右图有两条合法出路，**二选一或都放**，但绝不能保留现在的分群对比：

**方案 A（推荐）：paired slopegraph / paired 差分**
- 展示同一 215 题在 GUI-only vs Hybrid 两通道下的配对结果。
- 主体：两点 + 连线（斜率图），GUI 58.6% (126/215) → Hybrid 68.4% (147/215)，Δ=+9.8pp。
- 或更诚实：2×2 混淆矩阵——both solve / both fail / GUI-only solve / Hybrid-only solve。这直接暴露"工具救回了多少题、又弄丢了多少题"，比单一斜率更有信息量，且天然反因果夸大。
- caption 用词："paired evaluation on the same 215 tasks; Hybrid provides an optional second channel on the same store."

**方案 B：工具覆盖 ≠ 成功率，用 availability 描述而非成绩单**
- 如果你想保留"覆盖"叙事，就在右图画**工具可用性分布**（例如按任务分：0 个可用工具 / 有工具可用的题数），纯描述，不叠成功率。成功率的对比全部交给锁表主表。

**不该用的数字（重申）：** 76%、59%、90/119、57/96、369 系列的 57.2/68.3、Qwen 37.7 与 Gemini 拼图、跨 benchmark 的 79.2/48.3/60.8。

**该用的合法数字：** GUI 58.6% (126/215)、Hybrid 68.4% (147/215)；若引 gpt-5.6-sol 则 68.8/79.1，且必须与 Gemini 分开、同一锁表来源。

## 4. 视觉元素优化（主要针对可保留的左图 a）

- **配色**：8 个域用 8 种色，其中蓝/浅蓝（Finance/Productivity）过近，Travel 红与图例难分。建议 Productivity 换更冷的青灰，或用色相跨度更大的定性色板（Set2/Tableau 10）。色盲安全需自查。
- **数值标签**：条尾数字（8/7/6…）字号偏小且与轴刻度冗余；可保留但减淡，或直接靠色带长度即可。
- **图例位置**：Domain 图例塞在条形中段（Weather 附近）会与短条重叠，视觉噪音。移到左图右上角空白或 (b) 下方。
- **纵轴排序**：现在按数量降序，好。但同域 App 分散，读者难感知"哪个域工具更密"。可选：按域分组再组内排序，加域分隔或域标签带。
- **X 轴上限**：现在到 8 刚好卡满，留 0.5 单位余量给数字标签，避免"8"顶到边。

## 5. 顶会可投稿重绘方案

**模块清单（左右双栏）：**
- **(a) Tool-catalog breadth**：保留横条，修口径与配色。X 轴 = "Declared candidate tool types per app"。标题改为反映真实覆盖总数。
- **(b) Paired GUI-only vs Hybrid outcome**：换成 2×2 配对矩阵或 slopegraph（同 215 题）。

**阅读顺序：** 先左（生态有多少工具可用、按域分布）→ 再右（在同一批题上，多给一条工具通道带来多少配对增益、又有多少题反而丢了）。

**建议英文 caption：**
> *(a) Declared candidate tool types per app across seven domains; tools are per-app business-object actions on the same store, sharing the action slot with clicks (apps exposing tools: N; only those with ≥2 types shown). (b) Paired evaluation of Gemini 3.1 on the same 215 tasks: GUI-only 58.6% (126/215) vs. Hybrid 68.4% (147/215), Δ=+9.8pp. Hybrid is an optional second channel, not a prerequisite for solving tasks; the confusion cells show tasks solved only under one channel.*

## 6. 必须删掉或改口的元素

- **删**：右图现有的 tool-active(119) / GUI-only(96) 分群及 76%/59% 全部数字。
- **删**：右侧文字段"tool-active tasks are solved at 76% versus 59%"——这句就是因果错觉源头。
- **改口**：(a) 标题"40 apps expose tools"→ 与正文 ~52 对齐，明确区分"暴露工具总数"与"图中≥2 可见数"。
- **改口**：任何暗示"GUI 与 tools 等价 / 工具是涨分主因"的措辞。工具 = optional second channel。
- **保留**：右侧关于 declared types vs call frequency 的说明——这段是诚实的，很好。

## 7. 优先级

- **P0**：右图 (b) 整体推倒，改为同 215 题的 paired 展示（slopegraph 或 2×2 矩阵），只用 58.6%/68.4%（126/147），删除 76/59 及 119/96 分群。
- **P0**：删除右侧"76% versus 59%"因果句，改为 paired Δ 与"optional channel"表述。
- **P1**：统一 (a) 的工具覆盖口径（~52 暴露 vs 40 可见），标题与正文一致。
- **P1**：修配色，拉开 Finance/Productivity/Travel 三色相，图例移出条区。
- **P2**：X 轴留标签余量；条尾数字减淡；考虑按域分组排序增强"域内工具密度"可读性。
