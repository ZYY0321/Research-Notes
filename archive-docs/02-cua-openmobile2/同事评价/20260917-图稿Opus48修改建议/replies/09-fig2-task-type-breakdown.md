# 09-fig2-task-type-breakdown

- model: `claude-opus-4-8`
- elapsed_s: 69.7
- finish_reason: stop
- usage: {"prompt_tokens": 3657, "completion_tokens": 3019, "total_tokens": 6676, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 3657, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: fig-2-task-type-breakdown.png

---

# fig-2 审稿意见

## 1. 这张图现在在说什么

左 (a) 是一根 lollipop 条形，列出 17 个「semantic task tag」在 215 个 bench 任务中的出现次数，按三类（higher-order reasoning / action execution / constraint-search）着色。右 (b) 是一个 3×4 热力图，行是 S1/S2/S3 三档「task scope」（single session 40 / multi-session 111 / deep workflow 64），列是每个任务涉及的 App 数（1–4），格子里是任务计数。整体想说明「这个 Bench 覆盖了多样的任务语义，并且在 scope 与 App 广度两个维度上分布很广」。

## 2. 内容张力诊断

**对 Bench 三大主张（长程 / 跨 App 商业写入 / 可验终态），这张图几乎没有张力，还引入了口径冲突。**

- **(a) 的 tag 是内部标签，审稿人零先验。** 「Multi-entity output」「Format constraint」「Cross-app state」这些是你团队打的 tag，不是社区共识的任务类型。审稿人看不出这些 tag 是否互斥、是否穷尽、一个任务能带几个 tag。而且总和明显 > 215（19+17+9+…），说明是多标签，但图里没说明——读者无法判断这根条形代表的是覆盖度还是重叠度。**它证明不了「长程」，也证明不了「可验终态」。**

- **(b) 的 S1/S2/S3 与正式分层打架，这是硬伤。** 你自己指出 S1/S2/S3（single session / multi-session / deep workflow）≠ 论文正式分层（单 App / 真跨 App / 信使）。同一篇论文出现两套三分法，审稿人第一反应是「哪个是真的」。更糟的是：行的 111 与你 Bench census 的 109 单应用 / 74 双 / 27 三 / 5 四是**完全不同的切法**，热力图列（App 数 1/2/3/4）的边际和应该等于 109/74/27/5，但这里列边际是 111/72/27/5——**又撞上那个 111/72 vs 109/74 的口径冲突**。这张图把两处已知冲突同时暴露在一张图里。

- **最关键的三个卖点一个都没画：**
  - 「跨 App 商业写入」——图里只有「App 数」，但 App 个数 ≠ 业务依赖，第二个 App 是不是真发生 store 写入（还是只当信使），这张图完全区分不出。这恰恰是你最想立的点。
  - 「可验终态」——完全没有维度体现终态差分校验（成功判据是业务状态差分，不看路径）。
  - 「长程」——用 tag「Long-horizon search 3」来代表长程，反而显得长程任务只有 3 个，自伤。scope 的 session 数才是长程的合法度量，但被 tag 冲淡了。

**结论：(a) 建议整块换掉；(b) 概念对但口径必须重做。**

## 3. 应该改成什么统计

把这张图从「任务语义多样性」重定位为「Bench 三主张的结构证据」。

**左栏（换掉 tag lollipop）→「跨 App 是否真写入」堆叠条：**
- X 轴：App 数（1 / 2 / 3 / 4），边际和必须严格等于 **109 / 74 / 27 / 5**（用锁定的 census 口径，别再出现 111/72）。
- 每根条内部堆叠拆分：**「第二/第三 App 真实业务写入」vs「仅信使（无写入）」**。这是唯一能直接支撑「App 个数 ≠ 业务依赖，我们要求真实写入」的统计。
- Caption 主张：多 App 任务中绝大多数要求下游 App 发生真实 store 写入。

**右栏（保留热力图思路，但改轴、修口径）：**
- 行：改成能代表「长程」的合法量——建议 **交互步数分箱**（如 ≤10 / 11–30 / 31–60 / >60 actions）或 **子目标/session 数**，而不是内部 S1/S2/S3。
- 列：保持 App 数（1–4）。
- 若必须用正式分层，就直接用 **单 App / 跨 App-写入 / 跨 App-信使** 三档，和主文分层对齐，不要再造 S1/S2/S3 第三套名字。
- 格子数：边际必须能对上 215 与 109/74/27/5。

**可加一个小 inset 或第三面板证「可验终态」：** 直方图/条形展示每个任务的**可验证终态断言数量分布**（每题几条业务状态差分断言）。这才是「可验终态」的直接证据，比 tag 有力得多。

**不该用的数字：** 111/72、369 系列、任何跨 benchmark 的 79.2/48.3/60.8。这张图只谈构成，不谈成功率。

## 4. 视觉元素优化（若保留 (b) 结构）

- **热力图数值对比度失衡**：52 那格深蓝配深色数字，可读性差；浅格（0/2/3）配深字 OK，但深格数字应转白并加粗。统一规则：底色亮度低于阈值用白字。
- **色标**：连续蓝 colorbar 对「计数分布」够用，但 0 与空白难分，给 0 格加一条极浅灰描边或直接标「0」（已标，保留）。
- **行标签**：`S1 Single session (40 tasks)` 两行排版可以，但把 S1/S2/S3 这个编号删掉（见第 6 节），只留语义名。
- **(a) 图例位置**：目前压在条形区右下，和「Cross-source join」等条形争空间；若保留任何 lollipop，图例移到坐标区外。
- **两栏字号**：轴标题字号 OK，双栏宽度下 tag 文字（左）偏挤，若换成堆叠条会缓解。

## 5. 顶会可投稿重绘方案

**模块清单（左→右阅读）：**
1. **Panel (a) — Business-write dependency**：X=App 数(1/2/3/4)，堆叠 = 真实写入 / 信使；顶部标注每档任务数（109/74/27/5）。
2. **Panel (b) — Horizon**：热力图，行=交互步数分箱（长程证据），列=App 数；或换成每题步数分布小提琴图。
3. **Panel (c) — Verifiability**：条形/直方图，每题可验证终态断言数分布。

**阅读顺序**：先看「大多数任务要跨 App 且下游真写入」→ 再看「步数长、真长程」→ 最后「每题都有多条可自动校验的终态断言」。三个主张一图闭环。

**建议英文 caption：**
> **Figure 2. Structural evidence for the three benchmark claims.** (a) Across the 215 tasks (109/74/27/5 by app count), most multi-app tasks require a genuine business-state write in the downstream app rather than using it as a messenger. (b) Task length spans short to long-horizon interactions. (c) Every task ships multiple auto-checkable terminal-state assertions on the business store. All counts use the simulated App world with a fixed task set; success is judged by business-state diffs, not screenshots or paths.

## 6. 必须删掉或改口的元素

- **删除 S1/S2/S3 命名**：一篇论文不能有第三套三分法。与主文分层统一，或改成中性的步数/session 分箱。
- **修正列边际 111/72 → 109/74**（或反之），全篇一个口径，不能两张图打架。
- **(a) 的内部 tag 全部撤下**（除非把它降级为附录补充材料，并明确标注「多标签、总和 > 215、非互斥」）。
- **删掉「Long-horizon search 3」这类会自伤的 tag 呈现**（让长程显得只有 3 题）。
- 全图不得出现 mock；如有文字说明用 simulated。

## 7. 优先级

- **P0**：统一分层口径，删除 S1/S2/S3，热力图列边际改为锁定的 109/74/27/5，消除 111/72 冲突。
- **P0**：左栏换成「App 数 × 真实写入 vs 信使」堆叠条，直接支撑「跨 App 商业写入」主张。
- **P1**：新增/替换「可验证终态断言数分布」面板，为「可验终态」提供直接证据。
- **P1**：热力图行改为步数/session 分箱，让「长程」有合法度量而非靠 tag。
- **P2**：修深格数字为白字加粗、图例移出坐标区、0 格加描边。
