# 19-F5-apps-per-task

- model: `claude-opus-4-8`
- elapsed_s: 54.4
- finish_reason: stop
- usage: {"prompt_tokens": 3555, "completion_tokens": 2580, "total_tokens": 6135, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 3555, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: F5-benchmark-task-statistics.png

---

# 审稿意见：F5 Benchmark Task Statistics

## 1. 这张图现在在说什么

这张图用两个面板讲同一件事：MobileGym++ Bench 有 215 个任务、48 个 app，按“每个任务涉及几个 App”分层——111 单应用 / 72 双 / 27 三 / 5 四（(a) 条形图），以及同一分布的占比（(b) 环形图）。副标题强调“one shared task manifest”，底注说明“每个任务只计一次”“app count 衡量覆盖，严格跨 app 需业务关系”。核心是一张**任务复杂度分布图**，用 App 个数当复杂度代理。

## 2. 内容张力诊断

**对 Bench 主张来说太弱，而且数字口径打架。**

- **数字冲突（致命）**：图内写 111/72/27/5，你明确说正文是 109/74/27/5。同一张 paper-ready 图与正文冲突，审稿人一眼抓到就质疑数据可信度。必须锁死一个口径。这里显然应回到 109/74/27/5=215。111/72 那版是废稿。
- **同一分布画两遍**：(a) 条形和 (b) 环形是完全相同的数据，占了半页却只传达一个一维分布。信息密度极低，(b) 应删。
- **App 个数 ≠ 业务依赖（核心弱点）**：整张图把“App 个数”当卖点，但你的硬约束里最关键的主张是——跨 App 时第二个 App 必须发生**真实业务写入**，不能只当信使；且**成败看业务状态差分、同一 checker、GUI-only 是一等公民**。当前图完全没有体现这些，反而底注一句“app count measures coverage”几乎是在自我承认这个维度不重要。审稿人 10 秒内看到的是一张“我们的任务涉及多个 app”的饼图，撑不住“可执行用户目标 + 真跨写入 + 统一判定”的贡献。
- **48 apps 与环境 census 混淆风险**：标题写“48 apps”，但你的 census 是可安装 64 / 新构造 35。48 是什么集合？若是 Bench 实际用到的子集，必须标清楚，否则和 64、和训练 110+ 三个数字读者会自己乱拼。
- **“executable tasks”没有被证明可执行**：图里反复写 executable / manifest，但没有任何元素展示“可执行”与“被判定”这两件事。

## 3. 应该改成什么展示（张力不够，需重做主图逻辑）

把主张从“App 个数分布”换成**三段式证据**：目标是可执行的用户意图 → 跨 App 有真实写入 → 同一 checker 判业务差分。

建议改成一个 2×2 或左右结构：

**(a) 任务复杂度分布（保留，但只保留条形，删环形）**
- 数字锁 109/74/27/5=215。
- y 轴改成语义标签更好：`Single-app`、`2-app`、`3-app`、`4-app`，右侧数字。
- 合法数字：只用 215 口径，绝不出现 369/57.2 等。

**(b) 跨 App 中“真实写入”比例（新增，这是关键卖点）**
- 在 74+27+5=106 个多 App 任务里，标出“第二/第三个 App 发生业务写入（非纯信使）”的比例。这是把“App 个数”升级成“业务依赖”的唯一合法证据。用堆叠条：writer app vs. reader-only。
- caption 明确：App count ≠ business dependency；we require downstream write.

**(c) 判定协议（新增，一等公民 GUI + 同一 checker）**
- 一个小示意：observation = pixels + a11y tree（agent 读不到 store）→ action（GUI click / app-native tool，同一动作槽、写同一 store）→ **business-state diff checker**（成败看状态差分，不看截图/路径）。
- 强调正式题都有纯 GUI 路径；tools 是可选第二通道，不写成因果涨分。

**(d) 领域覆盖（可选，替换掉环形图占的空间）**
- 七个领域 × 任务数的小条形，说明覆盖广度，比重复的环形有信息量。

不该用的数字：111/72、369 的 57.2/68.3、Qwen 37.7 拼 Gemini、跨 benchmark 79.2/48.3/60.8。本图不涉及成功率，别引入。

## 4. 若保留当前风格的视觉优化（次要）

- 配色、字号、留白都干净，条形+数字右对齐清晰，这部分工艺没问题。
- 环形中心“215 manifest tasks”做得好看，但内容冗余。
- (a) 的条形建议加轻微网格或统一末端对齐参考线，方便读长度。
- 副标题“48 apps”需加脚注解释与 64/110+ 的关系。

## 5. 顶会可投稿的重绘方案

**模块清单（左→右阅读）**
1. 顶部标题：`Bench215: executable, cross-app tasks with a shared state-diff checker`
2. (a) 复杂度条形：109/74/27/5（single→4-app）
3. (b) 多 App 任务中真实写入占比（堆叠条：writer vs. messenger-only）
4. (c) 判定管线示意：pixels + a11y → action (GUI / app-native tool, same slot, same store) → business-state diff checker；标注 GUI-only is first-class
5. 底部一行：215 tasks · seven domains · one shared checker

**阅读顺序**：多深（a）→ 跨 App 是否真依赖（b）→ 如何统一判定（c）。

**建议英文 caption**：
> *Bench215 comprises 215 executable tasks spanning single- to four-app goals (a). Beyond app count, cross-app tasks require a genuine business-state write in the downstream app rather than message passing (b); all tasks—GUI-only by default, with app-native tools as an optional second channel on the same store—are graded by a single business-state-diff checker on the simulated app world (c).*

## 6. 必须删掉或改口的元素

- **删** (b) 环形图（与 (a) 完全重复）。
- **改** 111/72 → 109/74/27/5，与正文对齐。
- **改** 标题/副标题避免只讲 App 个数；加入“executable + cross-app write + shared checker”。
- **改** “48 apps”标注清楚集合，勿与 64 census / 110+ 训练集混。
- **删/改** 底注“app count measures coverage”这种自贬式说明，替换为对业务写入的正面陈述。
- **勿**出现“mock”，用 simulated；勿宣称 GUI 与 tools 完全等价。

## 7. 优先级

- **P0**：把 111/72 改为 109/74/27/5，消除与正文的口径冲突。
- **P0**：删除重复的环形图 (b)，腾出版面给“真实写入”和“统一 checker”两个新证据模块。
- **P1**：新增“多 App 任务中真实业务写入占比”堆叠条，把 App 个数升级为业务依赖。
- **P1**：新增判定管线示意，标注 GUI-only 一等公民、同一 state-diff checker、agent 读不到 store。
- **P2**：为“48 apps”加脚注区分 census(64)/训练(110+)；可用七领域覆盖小条替换空位。
