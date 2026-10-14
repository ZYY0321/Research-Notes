# 17-figF-app-freq-all

- model: `claude-opus-4-8`
- elapsed_s: 65.1
- finish_reason: stop
- usage: {"prompt_tokens": 4629, "completion_tokens": 2766, "total_tokens": 7395, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 4629, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: fig-F-app-freq-all.png

---

# fig-F 审稿意见

## 1. 这张图现在在说什么
一张横向排序条形图，列出 48 个 App 在 215 条 Bench 任务中的出现频次，从 notes(39) 到 meiyou(1) 降序排列，条色按七大领域编码。x 轴明确标注"一个任务可跨多个 App"，因此这是"任务-App 关联次数"而非任务数。它传达的是：Bench 覆盖广、但分布极不均，头部（notes/kapi/calendar/wechat）吃掉大量任务、尾部一长串单次 App。

## 2. 内容张力诊断
**这是一张诚实但低张力的附录图，放正文浪费版面。**

- **它证明不了论文核心主张。** 论文卖点是"可控 simulated 世界 / GUI-only 一等公民 / 跨 App 真实业务写入 / 成败看业务状态差分"。这张图只回答"哪个 App 出现多"，跟这些主张全都不搭边。审稿人 10 秒内得到的信息是"notes 很多"，无法推进任何论证。
- **口径隐患。** 标题写 N=215，与你锁定的 Bench 215 口径一致，这点没问题。但"48 Apps"要注意：这是 Bench 里被任务触及的 App 数，不是环境 census 的可安装 64，也不是训练侧 110+。图上没混淆，但 caption 必须防止读者把 48 当成环境规模或安装总数。
- **单/双/三/四应用结构完全丢失。** 你手上真正有张力的数字是 109 单 / 74 双 / 27 三 / 5 四（注意现稿另有 111/72/27/5 的冲突口径——本图没体现，但相关图必须统一）。"一个任务可跨多个 App"这句话在图里只是脚注，而它恰恰是 Bench 最值钱的属性，却没被可视化。
- **48 vs 64 的"未覆盖差"没说。** 有 16 个可安装 App 在 Bench 里出现 0 次？还是 48 就是 Bench 设计范围？这个 gap 不交代，长尾图反而显得覆盖不全。
- **头部 App 的高频可能被误读成"Bench 偏向工具类"**，而没有配合"跨 App 依赖"来说明这些高频 App 是不是真在被写入、还是只当信使。

## 3. 若张力不够——正文该换成什么
**正文不要放这张全 48 长条，改放一张"跨 App 结构"图；本长条降级进附录。** 具体三选一（推荐前两个组合）：

**(A) 任务复杂度堆积条（正文首选，最省版面最直接）**
- 单一分组竖条或水平条：单应用 109 / 双 74 / 三 27 / 四 5，按你确定的**唯一**口径。
- 叠加一个"其中第二 App 发生真实业务写入"的比例（如果你有这个数），直接支撑"App 个数 ≠ 业务依赖"这一主张。
- caption 明说：多应用任务要求第二个 App 真实写入，非信使。

**(B) 跨 App 对热力/桑基（正文次选，视觉张力最高）**
- 若要展示"哪些 App 组合成对"，用 App×App 对称热力图（按领域排序块状聚类），或 source→target 桑基（前置 App → 发生写入的 App）。
- **关键：桑基/热力必须区分"读取/信使"与"真实写入"两类边**，否则又变成单纯共现，撑不住"真实业务写入"主张。
- 若你没有"哪一端写入"的标注，就别做桑基，退回 (A)。

**(C) 领域堆积覆盖条（可作 A 的补充）**
- 七领域 × 任务数堆积，配一行小字标注"Bench 触及 48/可安装 64/训练侧 110+"三个数分层，杜绝混用。

**不该用的数字：** 不要在此图任何位置出现 369、57.2/68.3、79.2/48.3/60.8、Qwen 37.7 等成功率/跨 bench 数字——这是分布图，混入成功率会制造第二把尺子。

**合法可用：** 215 及其 109/74/27/5 拆分（口径先自查统一）、48 触及数、64/110+ 作为分层脚注。

## 4. 若保留此图（附录）——视觉逐项优化
- **数据标签冗余**：40+ 个数字贴条尾，中低段密集重叠。建议只标 ≥5 的条，尾部靠网格线读即可；或加淡竖网格线（现在只有很浅的几条）。
- **领域色序未聚类**：条按频次排，颜色跳动大，视觉噪声高。可加一个右侧 domain 侧栏色带，或提供第二版按领域分组的排列。当前 legend 在右下大片留白区，位置尚可但可上移填补空白。
- **y 轴标签字号偏小且 App 名混中英拼音**（xianyu/tbsg/fanqiexiaoshuo），对英文审稿人不友好，建议加一列英文功能标注或统一命名。
- **标题 "MobileGym++"** 与你正文 Bench 命名要一致，别一处 Bench 一处 MobileGym++。
- **x 轴到 50 但最大仅 39**，右侧空 20%，可截到 42–45 让条更长更易读。
- 竖向 48 行太长，双栏里会被压扁到不可读——这也是它不该进正文的实际原因之一。

## 5. 顶会重绘方案（正文替换）
**模块清单：**
1. 主图：任务复杂度堆积条（1/2/3/4-app：109/74/27/5，口径统一后）。
2. 内嵌/并排：七领域覆盖堆积条 + 三层规模脚注（Bench 触及 48 / 可安装 64 / 训练 110+，互不混用）。
3. 可选右侧小热力：Top-15 App 跨 App 共现，写入边加粗/深色区分信使边。

**阅读顺序：** 左"任务大多不止一个 App 且要求真实写入" → 中"覆盖七领域" → 右"跨 App 依赖具体成对结构"。

**建议英文 caption：**
> *Figure F. Task composition of the simulated Bench (215 tasks). Most tasks span multiple apps (109/74/27/5 for 1/2/3/4 apps); every multi-app task requires a genuine business-state write in the secondary app, so app count does not equal business dependency. Tasks touch 48 apps drawn from the 64 installable apps in the simulated world (training apps, 110+, are a disjoint set). Per-app frequency is deferred to the appendix.*

## 6. 必须删掉或改口的元素
- 删：正文里这张全 48 长条 → 移附录。
- 改口：标题/命名统一，别 Bench 与 MobileGym++ 混用。
- 防混：任何位置出现 48 时都要标明它是"触及数"，与 64/110+ 分层，避免读成环境规模。
- 若做桑基/热力：删掉不区分读写的纯共现边表达。
- 全程禁用 "mock"，用 simulated；本图目前无此问题，重绘时保持。

## 7. 优先级
- **P0**：正文换成任务复杂度堆积图（109/74/27/5），先自查并锁定唯一口径（现稿 109 vs 111 冲突必须消解），caption 点明"多应用=第二 App 真实写入"。
- **P0**：本长条降级附录，caption 标清 48 触及 / 64 可安装 / 110+ 训练三层不混用。
- **P1**：附录长条只保留 ≥5 的数据标签、x 轴截到 ~45、加淡网格线、legend 上移补白。
- **P2**：若有"写入端"标注，追加 Top-15 跨 App 共现热力（区分写入/信使边）；否则不做桑基。
