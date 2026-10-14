# 21-S3-task-combination-hierarchy

- model: `claude-opus-4-8`
- elapsed_s: 64.5
- finish_reason: stop
- usage: {"prompt_tokens": 3545, "completion_tokens": 2843, "total_tokens": 6388, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 3545, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: S3-task-combination-hierarchy.png

---

# S3 分层环图审稿

## 1. 这张图现在在说什么

双层旭日/环图：内圈按每个任务涉及的 App 个数分四档（1 app 111 / 2 apps 72 / 3 apps 27 / 4 apps 5，合计 215），外圈在每档内列出最常见的两个具体 App 组合 + 一个"All other"聚合扇区。左侧图例复述这些扇区的绝对数。核心主张：Bench 的多应用任务分布，以及每档里具体是哪些 App 一起出现。底注两处诚实免责："App sets indicate coverage, not the order of agent actions"、"每个任务只计一次"。

## 2. 内容张力诊断

**数字口径直接打架，且用的是错的那一版。** 内圈写 111 / 72 / 27 / 5。硬约束现稿口径是 **109 / 74 / 27 / 5**。这张图站在了被点名的冲突口径一侧（111/72），必须改回 109/74，否则整张图从根上不可信。

**这张图回答不了本轮的核心问题。** 你问的是"怎样表达真跨信息流（取值写回）而不是最常见的 notes+kapi 组合扇区"——现在这张图恰恰只表达了**共现频次**（哪两个 App 常一起出现），完全没表达**业务依赖 / 写回方向**。而 App 组合 ≠ 执行顺序 ≠ 业务依赖，图注自己也承认这点。结果就是：读者看到"Ctrip + Notes — 4""Broadcast + Notes — 4"这类高频组合，会误以为这就是跨 App 的代表性任务，但这些很可能是 **Notes 只当信使**（把结果抄进备忘录），第二个 App 没有真实业务写入——恰好违反硬约束"第二个 App 必须发生真实业务写入，不只当信使"。

**"最常见组合"是错误的排序维度。** 顶会审稿人想验证的不是"哪个组合出现最多"，而是"有多少任务存在真正的跨 App 写回"。现在把高频 notes 组合顶到显眼位，反而稀释了论文最想证明的东西。

**信息密度极低但占了半版。** 外圈 12 个扇区里有 4 个是"All other"占位（C 97 / F 64 / I 23 / L 3），真正具名的只有 8 个组合、每个 1–4 个任务。等于用一张大环图告诉读者"绝大多数组合我没展开"。3 app / 4 app 的具名扇区细到 1–2 个任务，肉眼在环上不可读（J/K/L 是三条引线拉出来的发丝）。

**结论：内容张力不足，且答非所问。** 建议换图种 + 换排序维度。

## 3. 张力不够 → 应该改成什么

**核心：把排序维度从"共现频次"换成"跨 App 写回强度"，并引入一个 second-app-writes 标记。**

推荐主图换成**两联图**：

**(A) 保留 App-count 分布，但缩小、简化。** 就一个横向 stacked bar 或小环：109 / 74 / 27 / 5。这只是背景，不该占半版。改回合法口径 **109/74/27/5**。

**(B) 主角改为"跨 App 写回矩阵"（heatmap 或 chord）。** 只针对 2/3/4-app 的 106 个多应用任务。定义一个明确的分类维度：
- 每个多应用任务标注：第二/第三 App 是 **真实业务写入（write-back）** 还是 **仅信使（messenger-only）**。
- 用一张 App×App 有向矩阵（heatmap），行=来源 App（读取值），列=目标 App（写回值），格子颜色=有真实写回的任务数。
- 这直接可视化"取值写回"的方向性，而且把 notes-as-messenger 的格子（写入 Notes）和真正 cross-write 的格子（写入 Ctrip/Alipay/Calendar 等业务对象）在颜色/位置上区分开。

**合法数字：** 109/74/27/5（=215）；58.6% GUI / 68.4% Hybrid 若要提成功率另说，本图不涉及。
**不该用的数字：** 111/72；任何 369 口径；任何跨 benchmark 数。

**Caption 主张改成：** "在 106 个多应用任务中，第二/后续 App 均发生真实业务写入（write-back），而非仅作信使" —— 这才是撑住硬约束的主张。

## 4. 若保留环图 → 视觉逐项优化

（若因版面必须留环图，下列为止血；但我更倾向第 5 节重绘）

- **内圈数字改 109/74/27/5**，图例同步。
- **外圈加一个语义维度**：给每个具名组合扇区加一个 hatch / 边框，标记"第二 App 是否真写回"。至少让 messenger-only 组合与 write-back 组合视觉可分。
- **J/K/L 发丝扇区删掉具名引线**，4-app 只保留一个扇区 + 图例文字，不在环上标 J/K/L。
- **"All other" 措辞统一**为 "Other combinations (n=…)"，别写 "All other app sets in this group"。
- 配色四档已用色相区分，OK；但外圈明度阶梯太接近（C 与 1app 内圈几乎同色），加大内外圈明度差。
- 中心 "215 tasks" 保留，字号可略减，别抢外圈。

## 5. 顶会可投稿重绘方案（推倒重来）

**模块清单：**
1. 顶部一行小 stacked bar：App-count 分布 109/74/27/5（背景信息，1/5 高度）。
2. 主图：**App-to-App write-back 有向 heatmap**。行=source App，列=target App，格值=真实写回任务数；对角/messenger 格用灰阶或斜纹区分。
3. 右侧 colorbar + 一个 legend 区分 write-back vs messenger-only。
4. 底部一行文字统计：106 multi-app tasks, all with ≥1 genuine second-app write-back; N messenger-only edges excluded/marked。

**阅读顺序：** 顶 bar（有多少多应用任务）→ heatmap 主体（值从哪流向哪）→ legend（哪些是真写回）。

**建议英文 caption：**
> "Cross-app write-back structure of MobileGym++ Bench. Of 215 tasks, 106 span multiple apps (74/27/5 for 2/3/4 apps). The matrix shows, for each ordered app pair, the number of tasks in which a value read from the source app is written back to a business object in the target app; every multi-app task contains at least one genuine write-back, not a messenger-only step."

## 6. 必须删掉或改口的元素

- **删/改：内圈 111 / 72 → 109 / 74。** 最高优先，口径错误。
- **删：J/K/L 三条发丝引线**（不可读且信息量=1 task）。
- **改口：外圈排序不能停在"最常见组合"。** 至少 caption 里说明这是 co-occurrence frequency，不是 dependency，且要额外提供 write-back 视角。
- **改口：底注 "App sets indicate coverage, not the order of agent actions"** 保留，但需再补 "nor business dependency"。
- 不出现 mock、function/API、"tools 与 GUI 等权" 等字样（本图未犯，保持）。

## 7. 优先级

- **P0** 内圈数字改回 109/74/27/5，图例同步，消除与现稿口径冲突。
- **P0** 增加一张 write-back 视角（heatmap 或 chord），显式区分 second-app 真实写回 vs messenger-only，直接回应"真跨信息流"。
- **P1** 删除 J/K/L 发丝引线与 4-app 具名扇区，4-app 合并为单扇区 + 图例。
- **P1** caption 明确"co-occurrence ≠ dependency ≠ order"，并陈述 106 个多应用任务均含真实写回。
- **P2** 加大内外圈明度差、"Other" 措辞统一、中心字号微调。
