# SE 背景的 AI 方向文献表：代码智能体 / 可执行环境 / 测试即奖励（2024–2026）

列同 `gui-testing-table.md`。子代理逐篇打开原文；UNVERIFIED = venue 未核实。

| 论文 | 年份·venue | 第一作者机构 | 动机（原文） | 贡献（要点） | 方法 | 关键数字 | 作者自认局限 | 一段话叙事 |
|---|---|---|---|---|---|---|---|---|
| **SWE-bench** | 2024 ICLR | Princeton | "Language models have outpaced our ability to evaluate them effectively" | 2,294 个真实 issue；训练集；SWE-Llama | issue+仓库 → 补丁 → 跑测试 | Claude 2 BM25 下 1.96% | 只 Python；只靠测试 "insufficient to guarantee reliable performance" | 用真实工程当评测 |
| **SWE-bench Verified** | 2024 OpenAI 博文 | OpenAI | 部分题 "hard or impossible to solve" 导致低估 | 人工三重标注筛出 500 题；Docker 评测 | 93 名开发者标注 | 61.1% 测试可能误判有效解；68.3% 被滤掉 | 数据污染；过滤 "overzealous" | **测试本身就是不可靠 oracle** |
| **SWE-agent** | 2024 NeurIPS | Princeton | LM agent 是 "a new category of end users"，需要专门接口 | 提出 ACI（智能体-计算机接口） | 精简动作 + 护栏 + 每步反馈 | SWE-bench 12.5%（RAG 3.8%） | ACI 设计靠人工 | **接口设计 = 软件架构问题** |
| **OpenHands** | 2025 ICLR | UIUC | 如何让 agent 在复杂系统中安全改代码 | 开放平台：沙箱、多 agent、基准集成 | 事件流 + Docker 沙箱 | Lite 26.0%，$1.10/题 | 多模态、复杂任务弱 | 通用 agent 平台 |
| **Agentless** | 2025 FSE | UIUC | "do we really have to employ complex autonomous software agents?" | 固定三阶段流程；Lite- 清洗集 | 分层定位 → 多补丁 → 复现测试选择 | Lite 32.00%，$0.70；Verified 50.8%（Claude 3.5） | 训练数据泄漏 | **简单流程打败复杂 agent** |
| **SWE-bench Multimodal** | 2025 arXiv（ICLR 2025 据 README，UNVERIFIED） | Stanford / Princeton | SWE-bench "uses only Python… lacking visual elements" | 617 个带图的 JS 前端任务 | 同协议迁到前端库 | 最佳 12.2% | 更多语言/模态待做 | **前端/GUI 修复是短板**——和你的 GUI 背景直接相关 |
| **SWE-Gym** | 2025 ICML | UC Berkeley | "the first environment for training SWE agents" | 2,438 可执行任务；训 agent + verifier | 测试标轨迹成败 → SFT + ORM | Verified 32.0%（verifier +11.4） | 环境多样性有限；自改进 "modest" | 先有训练场才有训练 |
| **R2E-Gym** | 2025 arXiv（COLM 2025，UNVERIFIED） | UC Berkeley | 难点是 "scalable curation of execution environments" 和测试时算力 | 从 commit 合成环境；混合 verifier | 执行型 + 非执行型 verifier 重排 | 32B Pass@1 34.4%；混合 Best@26 51% | "less than 20% of tests can effectively differentiate" | **生成测试大多没区分力** |
| **SWE-smith** | 2025 NeurIPS D&B | Stanford | 训练数据 "at most 1,000s… from 11 or fewer GitHub repositories" | 5 万实例、128 仓库；SWE-agent-LM-32B | 自动把测试打坏 → 写 issue | 总成本 $1,360；Verified 40.2% | 只 Python；只做 SFT | 便宜地造 bug |
| **SWE-RL** | 2025 NeurIPS | UIUC / Meta | R1 只做竞赛题，首个真实 SE 上的 RL | 用 PR 补丁相似度做奖励 | 27.3 万 PR + GRPO | Llama3-70B Verified 41.0%（SFT 36.2） | 相似度≠语义等价 | 真实软件演化数据做 RL |
| **DeepSWE** | 2025 Together AI 博文 | Agentica / Together | 长程多步 agent 的 RL "remains a challenging and open problem" | 纯 RL 训 Qwen3-32B，全开源 | R2E-Gym 4.5K 任务 + 改进 GRPO + 测试奖励 | Pass@1 42.2%；TTS 59% | SWE-smith/SWE-Gym 上 RL 不涨 | 多轮 RL 能训出强 coding agent |
| **SWE-bench-Live** | 2025 NeurIPS D&B | Microsoft | SWE-bench "not been updated… restricted to only 12 repositories" | 可持续更新、抗污染基准；自动建环境 | agent 自动搭 Docker + 多次验证 | 1,890 题；最佳 19.25%（Verified 上 43.20%） | 多文件编辑 "never solved" | **Verified 分数被高估一倍** |
| **LocAgent** | 2025 ACL | Yale | 难以 "navigate complex codebases… across hierarchical structures and multiple dependencies" | 代码异构图 + 多跳搜索 | 文件/类/函数 + 调用/继承边 | 文件级定位 92.7%；成本降 86% | 只 Python | **代码依赖图 = 架构知识** |
| **RepoGraph** | 2025 ICLR | UIUC | 现有方法 "overlook the need for repository-level code understanding" | 行级仓库图插件 | k-hop 子图检索 | 4 个系统平均相对 +32.8% | 上下文膨胀 | 仓库是图不是文件堆 |
| **RLEF** | 2025 ICML | Meta FAIR | LLM "struggle to improve code iteratively" | 执行反馈多轮 RL | 公开测试反馈 + 私有测试奖励 + PPO | 70B CodeContests 27.4→40.1 | 只单题，需测试用例 | 让模型真正读报错 |
| **SWT-Bench** | 2024 NeurIPS | ETH Zurich | "test generation remains relatively unexplored" | 复现测试基准；测试过滤补丁 | fail-to-pass 判定 | SWE-agent+ 18.5%；精度翻倍 | 只 Python，污染风险 | 写测试 ≠ 修代码 |
| **CURE** | 2025 NeurIPS | 芝加哥大学 / Princeton | 测试生成训练 "rely heavily on ground-truth code solutions" | 编码器与测试器共同进化 RL | 同一模型交替写码与写测试 | 测试准确率 +25.1% | 只竞赛题，仍依赖金标测试 | **测试器即奖励模型** |
| **SWE-Bench Illusion** | 2026 ICSE-SEIP | Purdue | 需区分 "generalizable problem-solving ability from memorized patterns" | 记忆检测诊断任务 | 不给仓库猜文件路径；5-gram 复现 | o3 不看仓库猜对 76%，外部仓库 53% | 资源有限只测部分模型 | **基准分数含记忆** |

## 读出的脉络
1. **主线 = 环境 + verifier**：SWE-bench → SWE-Gym/R2E-Gym/SWE-smith（造可执行环境）→ SWE-RL/DeepSWE（RL）。和 CUA 完全同构：瓶颈都是可执行环境和可信奖励。
2. **测试是不可靠的 oracle**：Verified 发现 61.1% 测试可能误判；R2E-Gym 发现 <20% 生成测试有区分力；Illusion 和 Live 显示分数有记忆和高估。**"如何判断 agent 真的做对了"是 SE 人的天然优势**。
3. **SE 知识直接变成方法**：ACI（接口设计）、LocAgent/RepoGraph（依赖图）、Agentless（流程设计）都是把架构理解变成 agent 能力。
4. **和你的交叉点**：SWE-bench Multimodal 证明前端/GUI 修复最弱（12%）；你的 GUI + verifier 背景在"GUI 代码修复 + 视觉验证"上有独特位置，可作为方向 A 之外的备选。
