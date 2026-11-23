# 04 · 热点评估：「测试强模型训练/教会小模型的能力」能不能做？怎么做才不单薄？

有人建议你做一个 **Benchmark 测试强模型训练小模型的能力（Teacher Capability / Teachability Evaluation）**。我先给你结论：**这个方向在 2025.10–2026.08 正在快速升温，而且和你手里的 CUA 数据合成经验高度契合；但千万不能做成“跑几个开源数据集看 SFT 分数高低”的纯跑分表，必须做成「机制发现 + 算法改进」才能拿去面算法岗。**

---

## 一、2025–2026 这个方向的最新顶会文献已经在做什么？

强模型自己跑分高（比如在 Benchmark 上考 90 分），**完全不等于它是一个好老师（Good Teacher）**。最近大半年刚出来的 5 篇核心论文把这个问题拆成了三个层次：

| 论文 | 时间 / 场合 | 核心发现（为什么最强模型往往不是最好的老师） |
|---|---|---|
| **In Good GRACEs: Principled Teacher Selection for Knowledge Distillation** | arXiv:2511.02833 (2025.11, Princeton/CMU/ Harvard) | **自身分数最高的模型 $\neq$ 蒸馏效果最好的老师**。作者提出用小模型（Student）在老师数据上的**梯度统计量（GRACE）**来给老师打分，不需要真跑完训练就能预测哪个老师教得好（Spearman 相关性 86%），选出来的老师比直接用最强模型多涨 **+7.4%** |
| **Find Your Optimal Teacher (PerSyn)** | ACL 2026 Main (arXiv:2510.10925) | 不同题目适合不同的老师模型。结合**学生可学性（Student Learnability）**和老师回答质量做路由（Route then Generate），发现 **95% 以上的样本路由给体型更小的老师模型反而比全用超大模型教得更好**（IFEval +8.7%，MATH +7.5%） |
| **The Signal is in the Steps (LALP)** | arXiv:2510.03988 (2025.10) | 长推理链（CoT）蒸馏时，看整条轨迹的平均困惑度没用，要看**局部每一步对学生而言是不是“自然可学”（Local Average Log Probability）**。按步级局部可学性筛老师数据，32B 学生在数学上涨 **+9.4%** |
| **Prefix Teach, Suffix Fade: Local Teachability Collapse in Strong-to-Weak On-Policy Distillation** | arXiv:2605.13643 (2026.05) | **强教弱（例如 Qwen3-30B 教 1.7B）在长轨迹后半段会发生“局部可教性坍塌（Local Teachability Collapse）”**：前面几步学生跟得上，越往后老师和学生的表征分布差得越远，继续强行对齐后半段反而伤泛化。在坍塌拐点截断释放监督，全方位吊打全轨迹蒸馏 |
| **Weak-to-Strong On-Policy Distillation** & **Trust Functions** | ICML 2026 (arXiv:2606.01000) & arXiv:2607.26246 (2026.07) | 反过来研究**弱教强 / 多弱师联合教强生**：当没有超级大模型、或者只有特定领域的弱老师时，怎么用置信度过滤（Trust Functions）或正负小模型 Logit 差来提升强学生 |

---

## 二、和你已有经验的惊人重合（你其实已经踩过这个坑了！）

翻看你自己的 `cua过程文档/参考资料-外部/智能纪要-CUA周会-0723` 和 `CUA 数据合成方法论.md`，你们组在合成 CUA 轨迹时已经亲手验证了两个极强的现象：

1. **“纯强模型自己跑出来的轨迹，反而包含大量无意义的滑动和死循环，直接拿去训小模型会污染训练集；而用『弱模型探索产生状态 + 强模型在卡壳处接管标注（Weak-explore, Strong-label，最多接管 2 次、每次至少续写 3 步）』效果好得多。”**（`0723周会` & `CUA 数据合成方法论`）
2. **“用 12k 轨迹训 Qwen3.5-9B 涨到了 73.6%，但完全同样的数据训 27B 反而掉到 52.2%（连基线都没过）。”**（`session格式复现结果.md`）

你看，外面发 ACL 2026 / ICML 2026 的论文在数学题上讨论 **Capacity Gap（能力鸿沟）** 和 **Prefix Teach, Suffix Fade（长轨迹局部可教性坍塌）**，而**你们在多步 GUI/Tool Agent 轨迹蒸馏上已经撞上了完全一模一样的现象，只是还没把它提炼成科学问题！**

---

## 三、如果你要做这个方向，怎么设计才能发顶会且对口算法岗？

记住你截图里那句非常清醒的话：**“不要把自己框死为做 benchmark，而应表述为：做评估，以及基于评估发现的问题做针对性改进——benchmark 是手段，改进是目标。”**

如果做这个题，不要做泛泛的“强模型教小模型 QA 评测”，而是直接卡在 **Agentic Teachability（多步智能体轨迹的强弱模型教学能力评估与对齐）**：

1. **为什么单轮 QA 的蒸馏结论在 Agent 上全失效？**
   - 单轮数学题只有一个静态文本输出；
   - 而在 GUI / Coding Agent 里，强模型（如 Gemini 3.1 / Opus 4.8 / Claude Sonnet）有 300 步长视野和强大的视觉/工具纠错能力，它走出来的轨迹（比如连跳 3 个隐式工具、或者靠超长 Thinking 硬猜）**超出了 7B/9B 小模型的观测与动作表征容量**——小模型模仿这种轨迹，就会出现你们看到的“学会了表面格式，但基本动作能力下降、或者一次工具都不敢调”。
2. **论文结构怎么立（既有 Benchmark 又有训练方法）**：
   - **Part 1（诊断基准 AgentTeachBench）**：固定小模型学生（如 Qwen-3B / 9B）和环境（MobileGym++ / SWE-bench 子集），评测不同强模型老师（Opus / Gemini / GPT / DeepSeek / Qwen-Max）在三种教学模式下的教学转化率：
     1. *Direct Trajectory Demonstration*（强模型自己跑通的轨迹直接 SFT）；
     2. *On-Policy Intervention / Takeover*（小模型先走，强模型在关键偏航点接管纠正 $k$ 步——就是你们的 2 次接管策略）；
     3. *Verifier / Critique Feedback*（强模型不给动作，只给过程奖励或错误归因）。
   - **Part 2（核心发现）**：证明在多步 Agent 任务中，**强模型的 Execution Score（自己做题分）与 Teaching Score（把 9B 教会分）相关性很低**，并定位出导致不可学的两个罪魁祸首：*Action-Space Mismatch（动作/工具跳步）* 与 *Suffix Teachability Collapse（长轨迹后半段分布漂移）*。
   - **Part 3（算法处方）**：提出 **Student-Aware Trajectory Rewriting / Adaptive Takeover Distillation**（让强模型根据小模型的局部策略熵/困惑度动态决定何时接管、如何把跳步拆解成小模型可消化的子步），让 9B 模型在 Hybrid CUA 上真正突破工具调用瓶颈。
