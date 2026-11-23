# How Benchmarks Mis-Score CUAs：重新审 150 条被判失败的轨迹，15.3% 的「失败」判错了

## 一页读懂
| 项 | 内容 |
|---|---|
| 来源 | arXiv 2607.28367（2026-07-30 提交）／venue：arXiv 预印本／Georgia Tech 等多校与 Lenovo／未见代码或数据链接 |
| 读深度 | 全文（arXiv HTML，正文 §1–§7 + Limitations；附录只扫了引用列表） |
| 问题 | 基准分数到底多大程度反映 agent 能力，多大程度是打分流程的噪声 |
| 它检查了什么默认假设 | 「判失败 = agent 真的失败」；「脚本 oracle 是客观的」 |
| 发现问题的方式 | 重审公开轨迹：从 5 个基准抽 150 条被判 FAIL 的轨迹，两个 LLM 加两组人类独立重判 |
| 解决方式 | 诊断：一个四阶段可靠性框架 + 三层失败分类 + 设计建议；无新数据集、无新方法 |
| 最强证据 | 150 条里 15.3% 的 FAIL 判错（10.7% 是评测器误杀，4.7% 是题本身坏了）（§4.4，Table 2） |
| 品味 | A（审计部分）：做法简单、可复制，且给出了「判错」和「真失败」之间的分层；但只审了失败样本，没审成功样本 |

## 一段话介绍
很多 CUA 基准靠脚本检查最终状态或答案字符串。这篇论文说：分数是一条流水线的输出，题可能过时、轨迹可能缺关键截图、检查器可能不认可另一种合理解法。作者从 OSWorld-Verified 和 AgentRewardBench 里抽了 150 条已经被判失败的公开轨迹，让两个视觉 LLM 和两组人类各自重判，发现约每 7 条里就有 1 条「失败」是判错的。剩下真失败的 122 条里，最大的一类不是点错位置，而是点了没反应还在重复。

## 动机
> "A score is the output of a pipeline in which tasks can be stale, trajectories can omit decisive visual evidence, evaluators can reject valid alternatives, and aggregate reports can hide the cause of failure."（Abstract）

## 方法（审计构成）
- **抽样**（§4.1）：固定随机种子 20260717 分层抽样。OSWorld-Verified 取 3 个已发布 agent 运行里各 20 条零分轨迹；WebArena、WorkArena、VisualWebArena、AssistantBench 来自 AgentRewardBench，每个约 23–25 条，只取累计奖励为 0 的。158 条中 8 条用于校准，余 150 条分析（57 OSWorld + 93 Web）。没有新跑任何 agent。
- **两阶段标注**（§4.2）：
  - 阶段 1，每条 FAIL 标成：真失败 / 评测器误杀（结果其实满足任务但检查器拒绝）/ 题坏了（不可行、参照状态过期、环境或框架挡住）/ 不清楚。
  - 阶段 2，只对真失败做过程诊断，分三层：规划与规格（T1）、执行与落点（T2）、核验与反馈（T3）。
- **谁来标**：GPT-5.5 和 Claude Sonnet 两个视觉 LLM 都看完整轨迹（含截图）；所有 LLM 不一致的 74 条加 30 条一致的抽样，共 104 条，由两组人类盲标，人类多数票定最终标签（§4.2）。
- 一个例子（§4.4）：OSWorld 有一道查电池百分比的题，但 /sys/class/power_supply 是空的，题在发布的虚拟机镜像上根本做不了。

## 实验
- **主结果（Table 2，分母是每个基准被抽的 FAIL 数）**：
  - 全体 150 条：真失败 122，评测器误杀 16，题坏 7，不清楚 5。「判错」= 误杀 + 题坏 = 15.3%（95% Wilson 区间 [10.4, 22.0]）。
  - 分基准：WebArena 21.7%（n=23），AssistantBench 21.7%（n=23，全是题坏：搜索引擎挂了、验证码），OSWorld 17.5%（n=57），VisualWebArena 13.0%，WorkArena 0.0%（0/24）。
- **真失败的诊断**（n=122）：核验与反馈类 39.3%（其中「重复做没有变化的动作」单项 29.5%，是最大一类）；规划类 35.2%；执行与落点类只有 13.9%。例：一条 WorkArena 轨迹点了 27 次「ALL RESULTS」，页面一直显示 No Results。
- **标注者一致性**：两个 LLM 对阶段 1 判定 κ=0.71，对阶段 2 诊断只有 κ=0.41；人类两组之间 κ=0.59；人类和 LLM 两两 κ 在 0.19–0.32（104 条的压力集）。
- **截图的作用**：去掉截图后，Codex 的 12 个判定、Claude 的 13 个判定被翻转，两者能发现的评测器误杀分别从 14 降到 8、从 10 降到 6（§4.4）。

**能支持的结论**：评测器误杀和题坏的比例不可忽略；在真失败里，「看不到动作没生效」比「点错了」更常见。
**支持不了的结论**：
- 每个基准只有 23–57 条，作者自己说区间很宽，不应当当作各基准的校准估计（Limitations）。
- 只审了被判 FAIL 的样本，**成功样本里的假阳性完全没估计**（§4.1，Limitations）。
- 诊断类别之间的细分一致性只有中等（κ=0.41），分类占比要谨慎引用。

## 局限
- 作者承认（Limitations）：只覆盖 5 个基准的公开轨迹；每基准样本小；只测误杀不测假阳性；文献筛选没有 PRISMA 式记录；§6 里「用脚本扫重复动作+屏幕不变」的零成本探针只是构想，没有用人工标签验证。
- 我看到的：
  1. 人类标注者 4 个人的「判错率」分别是 13.5%、7.7%、20.2%、13.5%（§4.4），范围 7.7%–20.2%；最终 15.3% 在这个范围里偏上，说明数字依赖谁来标。
  2. 轨迹来自已有公开发布，agent 版本较早，对 2026 年新模型是否仍成立没有检验。

## 品味判断
1. **问题怎么发现的**：把「评测可靠性」当成被测对象，用别人公开的数据重审。没有任何新算力。换一个团队完全能做，门槛是标注人力和分类设计。
2. **最能说服审稿人的**：Table 2 把每个基准的误杀和题坏分开列，加上具体案例（电池题、WebArena 答案被字符串匹配拒绝）。
3. **可模仿的实验**：
   - 取一个现成基准的零分轨迹，按固定种子分层抽样；
   - 先判「评测器对不对」，再判「agent 为什么败」，两步分开，避免把评测器错误算成 agent 错误；
   - 用两个不同厂商的 LLM 先预标，只把不一致的送人审，省人力。
4. **没比的**：没有检验作者在 §6 提出的「重复动作 + 画面不变」探针；也没有同 OSWorld 2.0 这类新基准的评测器做同样审计（只在讨论里联系）。

## 和 CUA 评测 / 换路鲁棒性的关系（公开层面）
「重复动作而画面不变」占真失败的近三成，说明动作是否生效的检查是诊断中很实用的一环；Tier 3 的定义也给出了把「动作没生效」和「方案没有备选」区分开的边界规则（§4.3）。

## 原文摘录
- "15.3% of FAIL verdicts are wrong: 10.7% are evaluator false negatives and 4.7% are broken tasks."（Abstract）
- "Because every sampled unit was released as FAIL, the audit estimates false negatives among recorded failures but not false positives among successes."（§4.1）
- "Repetition is Tier 1 when the agent cannot develop an alternative strategy; it is Tier 3 when the agent has a viable plan but fails to notice that an action had no effect."（§4.3）

## 核对说明
读的是 arXiv HTML 全文文本，读了 §1–§7 和 Limitations，附录和引用列表没细读。Table 2 的数字按行抄出，但上半部分分基准列的数字（GF/EFN/Broken/Unclear）与下半部分的诊断表被抓取后排版错位，我按表头和正文交叉核对了总数（122+16+7+5=150）。
