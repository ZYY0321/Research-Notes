# 12-figA-domain-sunburst

- model: `claude-opus-4-8`
- elapsed_s: 61.9
- finish_reason: stop
- usage: {"prompt_tokens": 4670, "completion_tokens": 2697, "total_tokens": 7367, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 4670, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: fig-A-domain-sunburst.png

---

# fig-A 领域旭日图审稿

## 1. 这张图现在在说什么

内层是 7 个领域（按 task appearances 加权：Finance 41 / Social 47 / Shopping 53 / Travel 30 / Entertainment 41 / Productivity 105 / Lifestyle 33），外层把这些领域拆成 48 个具体 app 的楔形，中心标注"48 apps / 215 tasks"。它想一次性说三件事：Bench 覆盖多少 app、分几个领域、各领域任务分布是否均衡。

## 2. 内容张力诊断

**核心问题：这张图不能在 10 秒内让审稿人相信论文的核心主张，因为它把三个不同量纲搅在一起，还漏掉了本 benchmark 最能打的差异化维度。**

- **口径混用（P0）**：中心大字"48"是 app 数（Bench 覆盖侧），紧挨着"215 tasks"是任务数，内层扇区面积却是 task appearances（一个多 App 任务在多个领域各记一次），外层又是 app。三个量纲叠在一个图里，审稿人算不清 41+47+53+30+41+105+33=350 ≠ 215，会怀疑数据错误。实际上 350 是"任务×领域出现次数"，但图上完全没解释，这是致命的读图歧义。

- **48 vs 64 的红线（P0）**：中心只写 48，观众极易把"48"读成环境规模。你明确要求：Bench 覆盖 48 app，环境可安装 64。当前图完全没有 64 这条线，等于主动放弃了"64 可安装 / 35 新构造"这个环境侧卖点，还留下被误读成"环境只有 48"的风险。

- **内外层同义、信息浪费（P1）**：外层每个楔形就是"这个 app 出现的任务数"，内层是这些楔形之和。除了颜色分组，外层没有提供领域之外的任何新结构。旭日图的价值本应是"外层比内层多一层维度"，这里外层退化成内层的明细，视觉预算花在了 label 拥挤上。

- **最该说的没说（P0）**：本 benchmark 的真正张力是 **任务组合复杂度**（109 单 / 74 双 / 27 三 / 5 四，跨 App 真实业务写入），以及 **GUI-only 是一等公民**。这张图完全没体现"单/双/三/四 App"这层结构，也没体现跨 App 依赖。ScienceBoard/OSWorld 那类图之所以有说服力，正是因为内层给"任务类型/组合数"，外层给"具体环境组合"。当前图把宝贵的环形版面用在了"app 名字列表"上。

- **215 与其它口径的潜在冲突（P1）**：现稿口径应为 109/74/27/5=215。若正文别处出现 111/72/27/5，需统一，别让这张图和表格打架。

**结论：内容张力不够。建议换图种。**

## 3. 应该改成什么

**换成"分层任务结构环图/旭日图"，让内外层承担不同维度：**

推荐方案 A（旭日，但重新定义两层语义）：
- **内层 = 任务组合复杂度**：4 段，Single-App (109) / Two-App (74) / Three-App (27) / Four-App (5)。这是你的独家结构，一眼看出"大多数正式题是多 App"。
- **外层 = 领域构成**：在每个复杂度环段内，按参与领域上色，展示"双 App 任务里哪些领域组合最常见"。
- **中心文字改为双数字并列**：`215 tasks` 主字，副行 `48 apps covered · 64 installable`，把 48/64 的关系一次讲清、且明确 48 是覆盖不是规模。

推荐方案 B（若只想讲覆盖，用更朴素的图）：
- 分面条形：左面 7 领域 × app 数（bar），右面 7 领域 × task appearances（bar），并在图注写明"appearances 因多 App 任务重复计数，∑=350≠215"。旭日的美观代价太高，条形更诚实。

**合法数字**：215（=109+74+27+5）、48 覆盖、64 可安装、35 新构造、7 领域。领域 task appearances 若用，必须标注是"appearance 计数（多 App 任务重复计）"。
**不该用的数字**：任何锁表成功率（58.6/68.4 等）不属于这张覆盖图；不要出现 300+ tools 与 GUI 同权的暗示。

**caption 主张**：强调"覆盖 7 领域、48/64、且多数正式题需跨 App 真实业务写入"。

## 4. 若张力基本成立时的视觉优化（作为备用，若你坚持保留当前旭日）

- 中心文字层级：把"48 apps / 215 tasks"改成两行等重，删去误导。加入 64。
- 外层 label 拥挤：只标每领域最大的 2–3 个 app，其余进图注/附录表，避免"maoyan/broadcast"叠字。
- 内层扇区加"appearance 计数"脚注，消除 350≠215 的疑问。
- 领域配色：Productivity(浅蓝)与 Social(绿)在外层浅色化后区分度不足，建议提高外层明度阶梯或加细描边。
- legend 数字（41/53/… ）改为标注"task appearances"，别让读者误以为是 app 数。

## 5. 顶会可投稿重绘方案（推倒重来）

**模块清单**
1. 中心：`215 tasks` 主 + `48 apps · 64 installable (35 newly built)` 副。
2. 内环：Single 109 / Two 74 / Three 27 / Four 5（复杂度）。
3. 外环：各复杂度段内按参与领域配色的组合构成。
4. 底部 legend：7 领域颜色。
5. 角标小字注明 GUI-only 为一等公民（"every formal task has a pure-GUI path"）。

**阅读顺序**：中心（规模与覆盖）→ 内环（多 App 是主体）→ 外环（领域如何组合）→ legend。

**建议英文 caption**：
> *Task composition and domain coverage of our simulated App-world benchmark: 215 tasks span 48 covered apps (of 64 installable, 35 newly built) across 7 domains; the inner ring shows single- vs. multi-app structure (109/74/27/5), and the outer ring the domain make-up of each. Every formal task admits a pure-GUI solution.*

## 6. 必须删掉或改口的元素

- 删：孤立的中心"48"（易被读成环境规模）→ 改为 48 covered · 64 installable。
- 改：legend 中"(41)(53)…"必须标注为 task appearances，否则读成 app 数。
- 删/注：内层若保留 appearances，必须脚注"多 App 任务重复计数"。
- 全文一致性：确认 109/74/27/5，若正文有 111/72/27/5 统一之。
- 禁：图上任何 mock 字样（用 simulated）、任何成功率数字。

## 7. 优先级

- **P0** 中心改双行数字，明确"48 covered / 64 installable"，消除环境规模误读。
- **P0** 换图语义：内环改为单/双/三/四 App 复杂度（109/74/27/5），把独家结构讲出来。
- **P0** 消除 350≠215 歧义：appearances 加脚注或改用不重复计数。
- **P1** 外环改为领域组合而非 app 明细，避免内外层同义与 label 拥挤。
- **P1** legend 数字标注量纲，统一 215 内部口径。
- **P2** 配色明度阶梯与细描边，提升外环可区分度。
