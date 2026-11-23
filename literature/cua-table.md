# CUA / GUI Agent 文献表（2024–2026）

列同 `gui-testing-table.md`。子代理逐篇打开原文；UNVERIFIED = venue 未核实。

| 论文 | 年份·venue | 第一作者机构 | 动机（原文） | 贡献（要点） | 方法 | 关键数字 | 作者自认局限 | 一段话叙事 |
|---|---|---|---|---|---|---|---|---|
| **DigiRL** | 2024 NeurIPS | UC Berkeley | 静态演示 "fall short… due to their failure to deal with real world stochasticity" | 离线→在线 RL；可并行 Android 环境 + VLM 评估器 | 优势加权 RL + 自动课程 | 1.3B 模型 AitW 17.7%→67.2% | 只用 AitW 任务训练 | 真实 GUI 要在线 RL |
| **OSWorld** | 2024 NeurIPS D&B | 港大 | 现有基准 "lack interactive environments or are limited to specific applications" | 首个可扩展真实电脑环境，369 题 | 初始状态配置 + 执行结果评价脚本 | 人 72.36% vs 最强模型 12.24% | 无法检测潜在副作用、安全 | 离通用电脑助手还很远 |
| **AndroidWorld** | 2025 ICLR | Google DeepMind | 进步 "will be driven by realistic and reproducible benchmarks" | 116 个参数化任务，奖励来自系统状态 | 初始化/成功检查/拆除；M3A 基线 | M3A 30.6% vs 人 80%；种子间 26.3–33.2% | 界面理解、记忆、纠错差 | 用系统状态而非轨迹匹配判成功 |
| **OS-Atlas** | 2025 ICLR | 上海 AI Lab | 开源 VLM 在 "GUI grounding and OOD" 上大幅落后 | 首个多平台 grounding 合成工具；230 万截图；ScreenSpot-V2 | 合成数据预训练 + 统一动作空间 | 7B ScreenSpot 82.47 | 桌面数据缺口 | 开源动作基座 |
| **AgentTrek** | 2025 ICLR | 港大 | "scarcity of high-quality trajectory data" | 网页教程自动合成轨迹 | 教程筛选 → VLM 回放 → VLM 验收 | 10,398 条，$0.551/条 | 网站变化、只覆盖 11 类 | 用教程低成本造轨迹 |
| **ShowUI** | 2025 CVPR | NUS Show Lab | 语言代理 "limitations in perceiving UI visuals as humans do" | UI 图 token 选择；交错动作流；小而精数据 | 2B 模型 256K 数据 | grounding 75.1%；token 少 33% | 只用离线数据，RL 待做 | 小模型纯视觉 |
| **Aguvis** | 2025 ICML | 港大 | 文本表示 "limitations in generalization, efficiency, and scalability" | 纯视觉统一框架；两阶段训练 | 先 grounding 后规划推理 | 60% 错误来自 grounding | 模型常跳过规划直接点 | 不依赖闭源模型 |
| **AndroidLab** | 2025 ACL | 清华 | 已有研究 "lack systematic research for both open and closed-source models" | 138 题可复现环境；10,500 条训练轨迹 | 统一动作空间，子目标判成功 | 开源 LLM 4.59%→21.50% | 任务硬编码，只 Android | 环境+训练数据一起给 |
| **DistRL** | 2025 ICLR | 剑桥 | "limited data availability and inefficient online training" | 异步分布式 RL 框架 | 中心训练分散采集 + 优先回放 | 训练效率 3×；General 73.2% | 待扩展到更多任务 | 把在线 RL 做成系统 |
| **WebRL** | 2025 ICLR | 清华 / 智谱 | 开源模型 "lack the necessary decision-making capabilities" | WebArena 上首个 RL 基础设施 + ORM | 失败任务生成新课程 + KL 约束 | Llama3.1-8B 4.8%→42.4% | 二元奖励惩罚正确中间步 | **自进化课程** |
| **Windows Agent Arena** | 2025 ICML | Microsoft | 评测 "slow (on order of magnitude of days)" | 154 个 Windows 任务，并行 20 分钟评完 | 基于 OSWorld 改到 Windows | Navi 19.5% vs 人 74.5% | 无法提供 Windows 镜像 | 把评测做快 |
| **UI-TARS** | 2025 arXiv（UNVERIFIED） | 字节 Seed | 依赖商业模型+人工提示的框架 vs 端到端模型 | 感知、统一动作、System-2 推理、迭代反思 | 50B token 持续训练 + DPO | OSWorld 24.6；AndroidWorld 46.6 | 推理复杂会幻觉 | 原生端到端 GUI 模型 |
| **UI-TARS-2** | 2025 技术报告（UNVERIFIED） | 字节 Seed | "data scalability, multi-turn RL, the limitations of GUI-only operation, and environment stability" | 数据飞轮；多轮 PPO；**GUI+终端+文件系统混合环境** | 异步有状态 rollout；生成式 ORM | OSWorld 47.5；AndroidWorld 73.3 | **"ORM still exhibits a relatively high false positive rate"** | 工业级多轮 RL |
| **GUI-R1** | 2025 arXiv（ICLR 2026 投稿，未见录用） | 中科院深圳先进院 | SFT "demands extensive amounts of training data… struggles… to generalize" | 规则奖励 RL；3K 数据 | 统一动作空间奖励 + GRPO | 3B ScreenSpot 80.08 | 少量 SFT 反而掉点 | R1 式 GUI RL |
| **InfiGUI-R1** | 2025 arXiv（UNVERIFIED） | 浙大 | 现有代理是 "Reactive Actors" | Actor2Reasoner 两阶段 | 教师蒸馏空间推理 → 子目标奖励 RL + 纠错场景 | 3B ScreenSpot 87.5% | 未全面超过最强模型 | 从反应式到思考式 |
| **GUI-Shepherd** | 双盲稿（UNVERIFIED） | UNVERIFIED | "sparse rewards and the intractable credit assignment problem" | 首个在线 RL 中用 PRM 的长程 GUI 工作 | 52k 步级标注 → PRM → PPO 逐步奖励 | AndroidWorld 32.8→40.5（+7.7）；ORM 37.0 | 候选数 8→16 不再涨 | **过程奖励比结果奖励好** |
| **MobileWorld** | 2025 arXiv（UNVERIFIED） | 阿里通义 | AndroidWorld "approaching saturation… exceeding 90%" | 201 题；**用户交互 + MCP 工具混合任务**；确定性验证 | ask_user、mcp_call 动作；自托管后端 | agentic 最佳 51.7%，端到端 20.9% | 无法追问时编造答案；工具输出过长 | **GUI+工具混合基准已有人做** |
| **UltraCUA** | 2025 arXiv（UNVERIFIED） | 港大 / Apple | 只用 GUI 原子动作 "brittle execution chains prone to cascading failures" | 自动合成工具；17K 可验证任务；**混合动作** SFT+RL | 规划器选工具或 GUI，定位器负责点击 | 7B OSWorld 28.9%（基座 23.4%） | 对未见工具适应差 | **GUI+工具混合训练已有人做** |

## 读出的脉络与对你选题的影响
1. **环境/基准**：OSWorld、AndroidWorld 已接近饱和（MobileWorld 称 AndroidWorld 榜单 >90%），新基准都在加难度：更长、跨应用、追问用户、工具混用。
2. **训练**：SFT（OS-Atlas、Aguvis）→ R1 式规则 RL（GUI-R1、InfiGUI-R1）→ 多轮在线 RL（DigiRL、WebRL、UI-TARS-2）。卡点是**奖励**：UI-TARS-2 自认 ORM 假阳性高，GUI-Shepherd 证明过程奖励更好。
3. **混合动作空间（GUI+工具）已拥挤**：UI-TARS-2、MobileWorld、UltraCUA 都做了。你的 Tool Hurts 切片只能作为分析维度，不宜做主线。
4. **强教弱在 GUI 场景没人做**：InfiGUI-R1 用了教师蒸馏，但没研究"哪个老师好教"。结合 `ai-posttraining-table.md`，方向 A 空位仍成立。
5. **你的 verifier 经验正对准卡点**：ORM 假阳性、过程奖励都是公认难题；MobileGym++ 的确定性状态校验 + 变异负样本可以作为"可信奖励"的证据。
