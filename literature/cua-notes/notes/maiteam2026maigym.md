# MAI-Gym：把评测、造环境、在线 RL 放进同一条 rollout 管线，并测「克隆应用里训的，能不能搬到真应用」

## 一页读懂
| 项 | 内容 |
|---|---|
| 来源 | arXiv 2610.20939（2026-10-14 提交；PDF 首页日期 2026-10-16）/ venue：arXiv 预印本 / Alibaba Token Hub（MAI-UI Team）/ 代码 https://github.com/Tongyi-MAI/MAI-Gym（HTTP 200）；摘要称放出框架、合成技能、mock 应用、2,000 个验证任务、模型权重 |
| 读深度 | 主文 §1、§3.4、§4 全读；附录只扫目录和 A.7 标题 |
| 问题 | GUI 在线 RL 缺两样东西：能大规模并行、评测与训练行为一致的基础设施；以及状态自洽、可重置的多样任务 |
| 它检查了什么默认假设 | 「评测用的 agent 实现和训练用的 agent 实现是同一个」——作者认为常常不是，所以分数可能随 harness 变（§1：measured performance can depend on the harness as well as the model） |
| 发现问题的方式 | 对比现有 GUI gym 的覆盖（表 1）：有的只做基础设施，有的只造数据 |
| 解决方式 | 资源 + 训练：开放平台、49 个 mock 应用、任务和验证器合成流水线、MAI-Gym-9B |
| 最强证据 | 在 12306 克隆应用里 RL，真机真应用成功率 28.8% → 48.1%（52 个配对任务，§4.3.4，图 9） |
| 品味 | A：把「克隆里训，真应用上测」做成了正式实验，并且自己写出「克隆内提升 36.5 点、真应用只提升 19.2 点，差距从 7.7 拉大到 25.0」 |

## 一段话介绍
MAI-Gym 是阿里通义团队的开放平台：一条 rollout 管线同时服务 10 个已有榜单的评测、数据收集和在线 RL，能撑到 2 万个并行环境实例。在此之上，用编码 agent 造 mock 应用（7 个是真应用的克隆，如 12306、滴滴、美团；42 个是凭空发明的新应用），按「人设 + 场景」生成跨应用的初始世界（邮件、表格、日历互相有关联），再生成任务和验证代码，在活环境里跑通才收。用它训出 9B 模型 MAI-Gym-9B，在 MobileWorld 78.4、OSWorld-Verified 76.2。

## 动机
作者在 §1 讲了两个难点：GUI 实例不能像代码沙箱那样共享，每次尝试要独占一台手机/电脑；真应用有交易类操作，不能让策略在里面练几千次。原文：

> "Earlier synthesis either relies on model judges whose false positives a policy can learn to exploit [38,39] or verifies with code only in simplified applications [21,40]."（§3.4.3，p12）

## 方法（资源构成）
- 任务形式 x = (E, s0, g, V)：环境、初始状态、目标、验证器（§3.4）。
- 验证器合成流程（§3.4.3）：先写含「内部答案上下文」的规格 → 两次独立调用分别生成 golden code（直接把环境置为完成态）和 verifier code，互不读对方 → reward audit 对照规格检查缺失条件 → 在活环境按「初始 0 / golden 后 1 / 重置后 0」跑一遍 → 再让几个模型真去做，人工看轨迹查可执行性、难度、**reward-hacking 风险**。**在线 RL 的奖励只来自验证器执行**，模型只参与建任务和审核。
- 训练：Qwen3.5-9B → SFT 热身（混合移动/桌面）→ 联合 RL（§4.1）。对比 GRPO 与 SAO（§4.3.6）。
- 窗口式历史（K=10, O=2）：训练输入 token 从 566,375 降到 86,855，更新时间 2166s → 811s（表 6）。

## 实验
- **主表 4**：MobileWorld 78.4（基座 18.0）、OSWorld-Verified 76.2（基座 41.8）；AndroidWorld 75.9、MobileGym 46.5、OSWorld 2.0 3.7/11.3、MacAgentBench 41.3、MyPCBench 15.2。文中称这两个榜单「没有用任何基准任务训练」（Task OOD），但**环境是见过的**。
- **SFT 与 RL 分账（图 6）**：SFT 热身贡献大头——Task-OOD 平均 29.9 → 66.4；联合 RL 再把 Cross Avg 从 44.1 提到 50.5。RL 在 MobileWorld 加 14.1、OSWorld-Verified 加 7.8。
- **联合 RL vs 合并专家（表 7）**：Joint 78.4/76.2，最好的合并（50/50）76.4/73.7。
- **合成任务数量（图 8）**：500 / 1k / 5k 任务，MobileWorld 69.2 → 73.5 → 78.4，OSWorld-Verified 69.7 → 70.9 → 76.2。
- **克隆到真应用（§4.3.4）**：12306 克隆 36.5 → 73.1；真机真应用 28.8 → 48.1（52 个配对任务）。
- 能支持：在大量合成任务上做 RL 确实在榜单上有增益，克隆训练能部分迁移。支持不了：RL 本身是主因（SFT 分走大头）；SFT 数据的来源和与榜单环境的关系——我读到的部分没有给出细节，标「未核实」。

## 局限
- 作者承认：「Transfer remains incomplete: the clone–real gap widens from 7.7 to 25.0 percentage points, so clone gains do not fully predict real-app performance」（§4.3.4，p18）。我没有在读到的部分找到单独的「Limitations」节。
- 我看到的：
  1. **钻空子**：这篇是少有的把 reward-hacking 风险写进验证流水线的（让模型真去做、人工查轨迹），但没有给出被发现的利用案例数量或比例；golden code 自己「直接置完成态」，只证明验证器能判 1，不证明验证器判得对「只做了一半」的状态（作者也承认，p12）。
  2. 验证器由 LLM 写，规格也由 LLM 写，两次「独立调用」可能是同一个模型家族，错误可能相关；没有给人工审计的一致率。
  3. **数据泄漏**：训练在 MobileWorld/OSWorld 的**环境**里进行（只是任务不同），所以「Task OOD」成绩偏乐观；Env OOD 五个榜单上增益小得多（OSWorld 2.0 仅 3.7/11.3）。
  4. 52 个配对任务做真机迁移，样本小，没有多种子区间。

## 品味判断
1. **问题怎么发现的？** 对已有 GUI gym 做了一张覆盖表（表 1）：基础设施型的只覆盖一个平台、数据型的不放训练代码。换一个团队要同时有手机云、编码 agent 流水线和训练框架，门槛在组织资源，不在想法。
2. **最能说服审稿人的**：图 9：同一批任务在克隆和真应用上前后对比，并且作者自己把差距拉大的事实写进正文。
3. **可模仿**：任何「在模拟/克隆环境里训」的论文，都该留一小批真环境配对任务，报告「克隆内提升 / 真环境提升 / 差距变化」三个数。
4. **没比的**：Trace2World（arXiv 2610.30792，同一批作者）对「克隆是否忠实」做了更细的审计；MAI-Gym 的克隆靠测试员人工对屏幕（A.7.1），没有给定量一致率。

## 和 CUA 评测 / 换路鲁棒性的关系（公开层面）
它的「评测与训练同一 harness」直接对应「同一画面同一动作空间」的可比性；克隆应用与真应用的差距提示：路径/界面细节不同会让增益缩水。

## 原文摘录
- "Because no benchmark task is used in training, these scores measure how well the policy solves new tasks in environments it has trained in."（§4.2，p14）
- "Because golden code sets the completed state directly, it does not show that an agent can solve the task through the GUI."（§3.4.3，p12）
- "Transfer remains incomplete: the clone–real gap widens from 7.7 to 25.0 percentage points ..."（§4.3.4，p18）

## 核对说明
读的 v1 PDF。表 4、表 6、表 7、图 6/8/9 的数字对过正文；附录 A.7（mock 应用）、A.4–A.5（超参）没读。GitHub 链接 HTTP 200，未下载权重核对。「2,000 个验证任务」来自摘要，我没有在 repo 里数过。
