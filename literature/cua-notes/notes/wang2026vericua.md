# VeriCUA（2610.26469）：让奖励 agent 学会「查什么、什么时候停」，而不是换更大的裁判

> 注意：2026-10 有两篇同名 VeriCUA，不是同一篇。本笔记是 2610.26469（清华/电子科大等，学习型主动验证）；另一篇 2610.40578（Google + 港大，agentic 验证框架）只在表里有一行。

## 一页读懂
| 项 | 内容 |
|---|---|
| 来源 | arXiv 2610.26469（2026-10-19 提交）/ venue：arXiv 预印本（正文标 "Preprint"）/ 西南交大、清华、电子科大等 / 代码 https://github.com/Jeffjeno/VeriCUA（HTTP 200） |
| 读深度 | 主文 §1–§3 全读；附录只扫目录，没读 A–I |
| 问题 | CUA 做 RL 要「任务是否完成」的奖励；只看截图的奖励看不到文件内容、隐藏设置；让 LLM 主动去环境里查（proactive verification）时，查什么、何时停靠提示词，效果不稳 |
| 它检查了什么默认假设 | 「把裁判换成更大的模型、加几条示例，奖励就更准」 |
| 发现问题的方式 | 控制变量：同一个「Judge + 冻结 Probe」循环，换 4B 到 GPT-5.4 的 Judge，一致率都卡在 68%–70%（表 1） |
| 解决方式 | 训练：Judge 先 SFT（Kimi-K2.6 的验证轨迹，按结果过滤）再在线 RL；Probe 冻结；奖励 = 判断对不对 + Probe 用得省不省 |
| 最强证据 | OSWorld/MobileWorld/WebArena-Verified 宏平均一致率：4B VeriCUA 74.08 vs few-shot GPT-5.4 68.72（表 1）；作为 Actor 的奖励，整体 Pass@4 43.93 → 47.14（表 2） |
| 品味 | A：问题（策略比规模更重要）用一张干净的控制表就讲清楚；但下游 Actor 增益只有 +3.21，且没有多种子 |

## 一段话介绍
训练 CUA 时，每条 rollout 都要有人说「成了没成」。只看截图的裁判会漏掉隐藏状态，所以出现了「主动验证」：裁判可以派一个探针（Probe）去终态环境里点点看看。VeriCUA 观察到，让裁判模型自己决定查什么、何时停，换成再大的模型也没用，原因是一项检查有没有价值，只有执行后才知道。它训练一个小 Judge：先模仿强教师的验证轨迹，再用在线 RL 学习「该查哪些点、什么时候能下结论」，Probe 保持冻结，所以差异归因到 Judge。

## 动机
原文（§1，p2）：

> "Our key observation is that a check's value is revealed by executing it, not by reading the task."

教学例子：任务要求「每页幻灯片都补上备注」，一张缺备注就足以判失败。提示型裁判去逐页对比，卡在循环里没有结论；VeriCUA 去找「缺备注的那一页」，找到就停（图 1）。

## 方法
- Judge 每轮输出 verdict ∈ {success, failure, uncertain} 和一组检查（satisfied / violated / unresolved）；uncertain 且次数 < K 时，只把未解决的检查交给 Probe（§2.2）。K=2 轮（图 5b：K=0 时 74.09，K=2 时 82.00，OSWorld）。
- **单次尝试约束**：Actor 的终态只能验证一次（探测会改状态，无法从同一终态做多次对照），所以奖励按批内「终态」做归一，不需要环境分叉（§1）。
- 奖励：判断对错 + Probe 使用效率（§2.3–2.4；具体公式我没精读）。
- 训练数据只用 OSWorld；MobileWorld、WebArena-Verified 为零样本迁移。评测每个 Actor 轨迹用「可执行评测器」的结果作标签，轨迹要求六次重放结果稳定才保留（§3.1）。

## 实验
- **表 1（宏平均 / 三个环境一致率）**：Prompted GPT-5.4 68.13、few-shot 68.72；Kimi-K2.6 69.62；Qwen3-VL-4B 的 Prompted VeriCUA 69.58；**VeriCUA-4B 74.08**（OSWorld 82.00、MobileWorld 77.50、WebArena-V 62.75）；2B 70.78；1B（MiniCPM-V-4.6）71.62，高于 Kimi-K2.6 的 69.62。每个条件 Avg@4。
- **训练阶段（图 5a）**：OSWorld 73.73（提示）→ 79.41（SFT）→ 82.00（+在线 RL）。
- **探针省钱**：比 few-shot GPT-5.4 少 47.6%–59.8% 的 Probe token（§3.2）；OSWorld 上少 56.9%。
- **行为分析（§3.3）**：33 个「轨迹里漏掉决定性证据」的 OSWorld 案例中，VeriCUA-4B 61.9% 的 Probe 动作指向相关证据，GPT-5.4 提示版 47.6%。
- **下游 Actor（表 2）**：Qwen3-VL-4B-Thinking，GRPO；整体 Pass@4：初始 43.93、ZeroGUI 奖励 45.36、提示版 VeriCUA 45.71、训练版 VeriCUA 47.14；MultiApp 留出集 17.57 → 22.97（+5.40）。
- **训练过程中的验证（§3.4 末）**：用训练版验证器时，与可执行评测一致率 81.4% vs 77.8%，假阴性率 4.6% vs 10.0%。
- 能支持：学习出来的验证策略比提示更准更省；跨环境迁移成立。支持不了：奖励已经抗钻空子——没有对抗实验。

## 局限
- 作者的局限：我没有在读到的主文里找到专门的 Limitations 节（附录没读，标「未核实」）。
- 我看到的：
  1. **钻空子**：这是「验证器自己」的方案，奖励模型的训练标签来自基准的可执行评测器，所以它的上限就是那套评测器；Actor 训练只有一次 GRPO 跑，没有看 Actor 是否学会骗 Judge（比如制造「看起来满足检查」的终态）。§3.4 报告的一致率变化只看到了「比提示版好」，没有看「随 Actor 变强是否下降」，原文说「To check whether this advantage persists as the Actor changes」，但给的是两组数字（81.4 vs 77.8），没有时间曲线。
  2. **数据泄漏**：Judge 在 OSWorld 上训练，Actor 也在 OSWorld 上训练和评测（表 2 的 ID 集是 206 个单应用任务，OOD 集是 74 个 MultiApp 任务）；Judge 的训练轨迹「与评测不相交」（§3.1），但环境与任务类型同源。
  3. 表 2 差距小（+1.4 到 +3.2），没有多种子或区间。
  4. Judge 的标签来自「六次重放稳定」的轨迹，筛掉了不稳定的任务，评测集偏向确定性高的任务。

## 品味判断
1. **问题怎么发现的？** 一次很干净的控制实验：固定验证循环，只换裁判大小，发现一致率平台期。别的团队也能做，但需要自己搭验证循环和标注好的轨迹集（414+100+100 条，含五个 Actor 的成功与失败）。
2. **最能说服审稿人的**：表 1 里 1B 模型超过 GPT-5.4——一句话推翻了「奖励模型要用大模型」。
3. **可模仿**：做奖励/评测器研究时，先做「裁判规模 × 是否 few-shot」的网格，看是否存在平台期；若有，说明瓶颈在策略而不在能力。具体实验：同一个验证循环，4 个规模的裁判，各跑 Avg@4。
4. **没比的**：Google/港大的同名论文（2610.40578）同期做同一方向，基线是 TRM、CUAJudge、OS-Themis；两篇没有互相比较。

## 和 CUA 评测 / 换路鲁棒性的关系（公开层面）
对应「动作先生效再下结论」：验证要去终态里取证据，而不是看最后一张图。这篇说明取证据的策略可以学习，但没有测换路（改变界面路径）后验证是否稳定。

## 原文摘录
- "prompted Judges ranging from 4B to GPT-5.4 all plateau at 68%-70% macro-average agreement."（摘要）
- "Our key observation is that a check's value is revealed by executing it, not by reading the task."（§1，p2）
- "A GUI verifier starts from the Actor's terminal state, the product of one stochastic execution."（§1，p2）

## 核对说明
读的是 v1 PDF（2026-10-19）。表 1、图 5、表 2 的数字对过正文。附录 A–I（含 Probe 配置、超参、局限）未读，Appendix H（训练过程中验证）只读了主文的引用段。
