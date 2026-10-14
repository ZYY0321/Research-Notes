# 纯 AI 方向文献表：后训练 RL / 自进化 / 强教弱 / 奖励模型（2024–2026）

列同 `gui-testing-table.md`。子代理逐篇打开原文抽取；UNVERIFIED = venue 未在 OpenReview/DBLP/会议页核实。

## 关键结论：teachability 基准目前没有
检索 "teachability / teacher capability benchmark / TeacherBench"，**没有找到**"按强模型把小模型权重训练得多好来打分"的公开基准。最近邻：
- TeachBench（arXiv 2601.21375）、EducationQ（ACL 2025）：测**对话教学**，学生是模拟代理，不更新权重；
- Small Models Struggle（Findings ACL 2025）：只提出现象 "Small Model Learnability Gap"，没有教师排行；
- DED（arXiv 2508.09883）：内部用 "smoke test" 选教师，发现 "benchmark scores alone do not determine an effective teacher model"，但没做成基准。

→ 方向 A 的空位是真实的，且已有两篇论文给出动机证据（榜单分数高的教师不一定教得好、小模型学不动强教师的长轨迹）。都局限在数学 CoT；**多步 Agent/GUI 轨迹上完全没人做**。

## 表

| 论文 | 年份·venue | 第一作者机构 | 动机（原文） | 贡献（要点） | 方法 | 关键数字 | 作者自认局限 | 一段话叙事 |
|---|---|---|---|---|---|---|---|---|
| **DeepSeek-R1** | 2025 Nature | DeepSeek-AI | 依赖人工推理轨迹 "slows scalability… performance is inherently capped by the human-provided exemplars" | 纯 RL 激发推理；R1 多阶段流程；蒸馏小模型 | GRPO + 只看答案对错的规则奖励；cold-start→RL→拒绝采样 SFT→RL | R1-Zero AIME24 15.6%→77.9% | "dependable reward models are difficult to construct for certain tasks" | 不需要人教推理，只给对错奖励 |
| **DAPO** | 2025 NeurIPS | 字节 Seed / 清华 AIR | 可扩展 RL 的配方 "remains a myth" | 四项技巧 + 开源 verl 代码与数据 | Clip-Higher、动态采样、token 级损失、超长惩罚 | Qwen2.5-32B AIME24 50（朴素 GRPO 30） | "only single-turn RL is considered" | 把 GRPO 的坑一个个拆开 |
| **Dr. GRPO** | 2025 COLM | Sea AI Lab / NUS | 批判性审视 R1-Zero 的基座与 RL 两部分 | 基座本已有 "Aha"；GRPO 有长度偏置；Dr. GRPO | 去掉长度与标准差归一化 | 7B AIME24 43.3%，8×A100 27 小时 | 自反思关键词检测可能误判 | R1-Zero 的增益一半来自预训练 |
| **VAPO** | 2025 arXiv（UNVERIFIED） | 字节 Seed | 有价值模型的方法 "possess a higher performance ceiling" | 首个超过无价值模型方法的 PPO 框架；长度自适应 GAE | 价值预训练 + 解耦 GAE + DAPO 技巧 | AIME24 60.4，5,000 步 | 后期熵更低，"may hinder exploration" | 价值模型能做更细的信用分配 |
| **RAGEN / StarPO** | 2025 arXiv（UNVERIFIED） | Northwestern | Agent 需要 "sequential decisions, maintain memory across turns" | 轨迹级 Agent RL 框架；发现 Echo Trap；StarPO-S | 多轮 MDP；按奖励方差保留不确定 prompt | 保留 50% rollout "avoids collapse entirely" | 小规模任务、无多模态 | 多轮 Agent RL 会塌，需要过滤与整形 |
| **Absolute Zero** | 2025 NeurIPS | 清华 | 零监督 RLVR 仍 "depend on manually curated collections of questions" | 模型自己出题自己做；代码执行器验证 | proposer/solver 自博弈，三类代码推理 | Coder-7B 数学平均 23.9→39.1 | Llama3.1-8B 出现 "uh-oh moment"，安全需关注 | 零数据自进化 |
| **R-Zero** | 2026 ICLR | 腾讯 AI Seattle / WashU | 人工造题 "fundamental bottleneck" | Challenger 出边界题，Solver 解 | 两模型交替 GRPO，多数票伪标签 | 摘要 Qwen3-4B 数学 +6.49（表格数字与正文不一致） | 多轮后所有模型 "performance degradation" | 自进化会到顶后塌 |
| **SPIN** | 2024 ICML | UCLA | 能否 "improve itself without… additional human annotated data" | 自博弈微调 + 理论最优证明 | 区分人类回答与自己上一轮回答 | zephyr-7B 排行平均 +2.66% | 固定人类分布 "imposes a ceiling" | 弱模型自己跟自己比 |
| **Self-Rewarding LM** | 2024 ICML | Meta / NYU | 人类偏好奖励 "bottlenecked by human performance level" | 模型自己当裁判，迭代 DPO | 自生成回答 → 自评分 → DPO | Llama2-70B AlpacaEval2 9.94%→20.44% | 只跑三轮；回答变长 | 回答能力和评分能力一起涨 |
| **Small Models Struggle to Learn from Strong Reasoners** | 2025 Findings ACL | Univ. of Washington | "small models (≤3B) do not consistently benefit from long CoT… or distillation from larger models" | 命名 Learnability Gap；Mix Distillation | 长/短、大/小教师轨迹 1:4 混合 SFT | Qwen2.5-3B 比直接学长 CoT 高 8 分以上 | 只做数学，未测代码/多模态 | **强老师不一定好教**——方向 A 的核心动机 |
| **DED** | 2025 arXiv（UNVERIFIED） | 中兴 | 有限样本能否推高推理上限 | "benchmark scores alone do not determine an effective teacher"；教师选择方法 | 小规模蒸馏试跑选教师 + 精选 800 题 + 多轨迹 | QwQ-32B 教出的学生强于 DeepSeek-R1 教出的；AIME24 81.87% | 待扩展到更多模型与领域 | **教师榜单分≠教学效果**——方向 A 第二条证据 |
| **TeachBench** | 2026 arXiv（UNVERIFIED） | 北大 / 字节 | 现有基准 "leaving knowledge-centered teaching underexplored" | 按大纲约束的教学评测框架 | 教师只看知识点，多轮教学生代理，测前后 Pass@1 | Qwen3-235B 数学增益 7.63 | 学生是 LLM 代理，非真人 | 测对话教学，不是训练权重 |
| **EducationQ** | 2025 ACL | 华南理工 | 评测教学能力 "resource-intensive, context dependent" | 多代理教学评测；14 模型 | 教师/学生/评估三代理 | Llama3.1-70B 学习增益 11.01% | 一对一场景不全面 | 教学效果与模型规模不线性相关 |
| **ProcessBench** | 2025 ACL | 阿里 Qwen | 自动识别推理过程错误对 "scalable oversight" 重要 | 3,400 题，找最早错误步 | 人工标错误步；PRM 与批评模型对比 | o1-mini 平均 F1 87.9 | 竞赛题标签可能不准 | PRM 泛化差 |
| **GenPRM** | 2026 AAAI | 清华 | PRM 监督有限、只出标量、不能扩推理算力 | 生成式 PRM + 代码验证 | 逐步 CoT 判断 + 多数投票 | 7B Maj@8 F1 80.5 > 72B PRM 78.3 | 推理开销大，只做数学 | 让验证器也"想一想" |
| **ThinkPRM** | 2026 TMLR（UNVERIFIED） | Univ. of Michigan | 训练 PRM "requires expensive step-level supervision" | 用 PRM800K 1% 标签训练长 CoT 验证器 | 筛选与金标签一致的验证 CoT 微调 | 域外比全量判别式 PRM 高 8% / 4.5% | 过度自信、提前下结论 | 少量标签也能训出好验证器 |

## 读出的脉络
1. **RL 主线**：R1 → DAPO/Dr.GRPO/VAPO 修算法 → RAGEN 把它推到多轮 Agent，并指出会塌。多轮 Agent RL 的稳定性仍是开放问题。
2. **自进化**：SPIN、Self-Rewarding → Absolute Zero、R-Zero，都依赖可验证器（代码执行、多数票），且都报告了到顶或塌缩。**验证器质量决定自进化上限**，这正是你 MobileGym++ verifier 的价值。
3. **强教弱**：只在数学 CoT 上有现象与选教师方法，没有基准，没有 Agent 场景 → 方向 A 有空位。
