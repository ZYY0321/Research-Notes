# 03 · CUA（Computer-Use Agent）与智能体自进化：全局文献与你的直接 Gap

## 一、2025–2026 CUA 与自进化（Self-Evolving）全景图

你现在在公司深度参与 **OpenMobile-2 / MobileGym++**（63 个应用、333 个工具函数、215 道锁表评测题、11,643 条 SFT 轨迹、2,475 道带 Verifier 的 RL 题）。你不是“外行看热闹”，你已经站在这个方向的核心基建上了，只是之前忙着赶工程和锁表，没时间抬头看外面的论文怎么包装同一件事。

把 2025–2026 的代表工作按**它们到底解决了什么问题**排成一张表：

| 类别 | 代表论文 | 核心机制 | 关键指标 / 发现 | 和你们工作的直接对照 |
|---|---|---|---|---|
| **原生端到端 CUA + 多轮 RL** | **UI-TARS** (arXiv:2501.12326)<br>**UI-TARS-2** (arXiv:2509.02544, ByteDance Seed) | 纯截图输入 + 数百台 VM 数据飞轮 + 反思修正轨迹 + 稳定化多轮 RL + **GUI 与文件系统/终端混合沙盒** | OSWorld **47.5**（1代 24.6），AndroidWorld **73.3**（1代 46.6），WindowsAgentArena **50.6** | UI-TARS-2 走向了 **GUI + Terminal/File 混合**；你们做的是 **移动端 GUI + 前台 App 原生 MCP 工具混合** |
| **开源桌面 CUA 底座** | **OpenCUA** (NeurIPS 2025, arXiv:2508.09123) | 跨 3 大 OS、200+ 应用的 AgentNet 标注基建 + **带反思的长 CoT（State–Action）合成** | OpenCUA-72B 在 OSWorld-Verified 上达 **45.0%** | 证明了“长反思 CoT + 动作”对 CUA 泛化至关重要，但你们在 `01-任务构造与判定` 里发现**长 thinking 在 23 道题上直接撑爆上下文**——这就是现成的 Gap |
| **超长程真实任务与批量调用** | **OSWorld 2.0** (arXiv:2606.29537, 2026.06) | 108 个人类中位耗时 1.6 小时的长工作流；引入 batched tool calls | Opus 4.7 平均调 **318 次工具**（1.0 仅约 30 次）；500 步上限下 Opus 4.8 完成率仅 **20.6%**（局部得分 54.8%） | 揭示了长程 CUA 的真正死穴：**步数一长，焦点丢失、状态漂移、局部做对但终态失败** |
| **小样本 R1 式强化学习** | **UI-R1** (arXiv:2503.21620)<br>**GUI-R1** (arXiv:2504.10458)<br>**InfiGUI-R1** (arXiv:2504.14239) | 用规则动作奖励 + GRPO；InfiGUI-R1 先蒸馏空间推理，再在**子目标引导 + 错误恢复场景**上做 RL | UI-R1 仅用 136 个任务训 3B 追平 76K SFT 的 7B；GUI-R1 用 3K 数据跨 5 平台超 13M 数据的 OS-Atlas | 回答了为什么你们 `0903周会` 里“直接拿 1,000 条轨迹上 Gym++ 跑 RL 没涨点”：**缺子目标/过程锚点与错误恢复场景构造** |
| **结构感知合成与锚点奖励** | **SEE** (arXiv:2607.18046)<br>**GSAR** (arXiv:2608.22847) | SEE 先建 **UI 状态转移图**再合成无死循环的 14.8 步长轨迹；GSAR 自进化合成环境/任务/目标状态，用 **Goal-State-Anchor Rewards** 做轨迹验证（>90% 准确率） | 解决真实 App 乱点死循环、以及离线轨迹没有规则奖励的问题 | 你们的 Mock App **天然就有完整的路由转移图（中位数 37 routes / 88 transitions）和精确 Store 状态**，比他们在黑盒真机上硬猜转移图强得多 |
| **多轮 Agent RL 的崩溃机理** | **RAGEN** (arXiv:2504.20073, Stanford/Northwestern) | 提出 StarPO，系统研究多轮 Agent RL 为什么训着训着就崩 | 发现 **Echo Trap（回声陷阱）**：奖励方差断崖与梯度尖峰，模型退化成浅层套路或幻觉思考 | 直接解释了你们周会里遇到的“RL 死循环、不 reset、长轨迹训不动” |
| **自我造环境 Self-Play** | **SPADE** (arXiv:2608.19197)<br>**Simia** (arXiv:2511.01824) | 同一个模型既当**环境设计师**（写可执行 `reset()/step()` 环境）又当解题 Agent，用基于提示的遗憾度（regret）卡在能力边界出题 | 30B 模型跨 8 个基准平均 **+5.3**，ACEBench-Agent **+13.9** | 这就是把你这几个月“半人工+AI 造 Mock 环境和 Verifier”变成**全自动闭环（Self-Play Environment Synthesis）**的顶会形态 |

---

## 二、从你自己的实验记录里挖出来的 3 个高价值 Gap（全是有数据支撑的真问题）

你在 `cua过程文档` 里记下的现象，很多外面的人根本拿不到这种一手的消融对照。最值得做成你个人一作论文的有三个点：

### Gap A：GUI + MCP Hybrid 里的「工具盲区、工具负迁移与模态路由」
- **你手里已有的硬事实（来自 `0904-Qwen与Gemini-case分析` 与 `MCP调用统计`）**：
  - 在 215 道官方题上，Gemini 3.1 从 GUI-only 的 **58.6% (126/215)** 涨到 Hybrid 的 **68.4% (147/215)**，工具救回 33 题，但**工具反而害死 12 题（Tool Hurts = 12）**；且 306 个候选工具里有 **199 个从头到尾一次都没被调用过**。
  - 更扎心的是小模型：`Qwen3.5-9B-mcp-ep2` 在 GUI-only 上 37.7%，上 Hybrid 只有 39.1%（**工具救 30 题，害死 27 题，净增仅 +3 题**）；而纯 GUI 训出来的 9B 在 Hybrid 协议下**调用 App 工具次数为 0**，成绩反而从 38.6% 掉到 35.3%。
- **为什么这是一个极好的 AI 论文题**：
  大家都以为“给 GUI Agent 加上 API/MCP 工具就一定更快更准”，但你的真实数据证明：**小模型在混合动作空间里会出现严重的模态选择失调（Modality Routing Collapse）——要么完全不敢调工具，要么乱调工具导致状态错位（比如预填类工具不落库，模型以为做完了直接交卷）**。
- **怎么做**：
  研究 **Hybrid Action Space 下的动作等价性感知与自适应模态路由（或 Counterfactual Credit Assignment）**：在同一状态节点上对比“走 5 步 GUI”与“调 1 次 MCP 工具”的状态转移代价与副作用边界，专门解决 `Tool Hurts` 的 27 个失败模式。

### Gap B：稀疏终态 Verifier 下的「状态里程碑分解（State-Milestone Credit Assignment）」
- **你手里已有的硬事实（来自 `01-任务构造与判定` 与 `02-训练约束`）**：
  - 你们的 Verifier 是查业务 Store 的严格 0/1 终态判定（470 个变异错误终态 100% 拦截，假阳性为 0），而且在 369 次运行里**抓到了 190 次“模型自称完成了，但实际 Store 没过”的虚假完成（Hallucinated Completion）**。
  - 但直接拿这个 0/1 奖励去训 RL，在跨 App 和长链路题上“未取得效果提升”（0903 周会），因为第 19 步填错一个字段导致最终 0 分，模型不知道前 18 步其实是对的。
- **怎么做**：
  利用你们可控环境天然具备的 **Store Diff 日志** 和 **UI 路由图**，不改变终态 Verifier 的 0 误报属性，自动把终态 `verify(final_state)` 反解成可验证的**中间状态锚点（Sub-state Anchors，参考 GSAR + InfiGUI-R1）**，专门做 **False-Completion Penalty + Milestone GRPO/DAPO**。

### Gap C：从你的「人工+AI 造 Mock App 与 Verifier」走向「Self-Play 可执行环境与任务合成」
- **你手里已有的硬事实**：
  你完整走通了 63 个 App 的 UI 复刻、Store 绑定、以及 470 个负样本变异审计（Mutation Audit），并且清楚知道自动出题最大的坑是：**“改了题面，Verifier 不会自动跟着改”** 以及 **“31 道复杂终态题造不出自动正例 fixture”**。
- **怎么做**：
  对标 **SPADE (2026.08)** 和 **SWE-smith (2025.04)**，做 **Verifier-First 的逆向任务合成（Inverse Task Synthesis from State Mutations）**：先在 Mock App 的 Store 上做受控的状态迁移/注入，再反向生成必然可解、且自带正负样本 Fixture 的双模态任务。
