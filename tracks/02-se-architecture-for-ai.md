# 02 · 硬核软工 × AI 算法：让你真正懂软件架构、且找得到算法岗的方向

## 一、先破除你的焦虑：为什么“纯软件测试”不好找算法岗，而“SE × Coding/GUI Agent”极其抢手？

你担心“做软件测试找不到算法工作”，这个直觉是对的：**如果你的论文只是拿 GPT-4 调个 Prompt 去给 Java 函数写单元测试，或者在 Android 上随便点点看崩不崩，面大模型算法岗（Code LLM / Agent / Post-training）时会被认为没有 AI 深度。**

但反过来，2025–2026 年大模型算法岗最缺的恰恰是**懂真实软件工程架构（Repository-level Architecture、执行环境构建、状态机与静态/动态验证）的 AI 研究者**。原因很简单：
- 单函数代码生成（HumanEval）已经彻底卷完；
- 现在所有大厂（字节 Seed、阿里 Qwen-Coder、DeepSeek、智谱、月之暗面、商汤）都在卷 **Repository-level Coding Agent（SWE-bench 级别）** 和 **Full-stack / GUI 应用构建与验证（如你们把 63 个 App 做成带状态机和 333 个工具的可执行环境）**。
- **真正卡住 AI 模型的 Gap，全部来自深度的软件工程问题**：跨文件依赖图、架构腐化（Architectural Smells）、修了一个 Bug 破坏了原有设计约束、UI 渲染与底层 State Store 脱节。

---

## 二、2025–2026 既有硬核软工深度、又是纯正 AI 顶会的代表工作

下面这 6 篇工作，**每一篇的切入点（Gap）都是深度的软件工程/架构/代码质量知识，但落脚点全是大模型训练（SFT/RL）、图引导 Agent 或可信评测（ICML / ICLR / ACL / NeurIPS / ASE）**：

| 论文 | 会议 / ID | 软工深度（怎么发现的 Gap） | AI 贡献（怎么做成算法工作） |
|---|---|---|---|
| **SWE-Shield** (*Does Pass Rate Tell the Whole Story? Evaluating Design Constraint Compliance in LLM-based Issue Resolution*) | arXiv:2604.05955 (2026.04) | **测试通过 $\neq$ 代码质量好**。软件工程里有大量“设计约束”（架构分层、接口契约、状态不变式）。作者从 6 个真实仓库提取了 495 个 Issue 和 **1,787 条设计约束**，发现 LLM 修好的 Issue 里**不到一半遵守了架构设计约束**，且功能通过率与设计合规性几乎不相关 | 构建了对齐 SWE-bench-Verified/Pro 的设计约束验证体系，把“架构合规”变成了可计算的训练/评测信号 |
| **SmellBench** (*Evaluating LLM Agents on Architectural Code Smell Repair*) | arXiv:2605.07001 (ASE 2026 投稿) | 关注**架构级坏味道（Architectural Code Smells）**（循环依赖、中心化模块、职责过载），而不是改变量名这种表面重构。先用专家核验发现传统静态工具 PyExamine 报的架构问题里有 **63.1% 是假阳性** | 评测 11 种 Agent 架构重构能力：最强 Agent 只能修 47.7%，而激进的 Agent 在重构时会**新引入 140 个架构坏味道** |
| **LocAgent** (*Graph-Guided LLM Agents for Code Localization*) | ACL 2025 Long (arXiv:2503.09089) | 大仓库不是纯文本，而是**异构图**（目录 → 文件 → 类 → 函数，靠 import、调用、继承连接）。直接用 grep/向量检索会迷失在跨模块调用链里 | 把代码库解析成有向异构图，训练 Qwen-2.5-Coder-32B 在图上导航，文件级定位准确率达 **92.7%**，成本降 86%，下游 Issue 修复率 +12% |
| **SWE-Gym** & **R2E-Gym** | ICML 2025 / COLM 2025 (arXiv:2504.07164) | 真实软件工程任务需要**可复现的执行容器 + 测试预言（Verifier）** | 在可执行软件环境里用过程生成 + 混合 Verifier（执行验证 + 无执行验证）训 32B 模型与 Verifier，在 SWE-bench Verified 上拿到开源 SOTA |
| **SWE-smith** | arXiv:2504.21798 (2025.04) | 逆向运用软工的**变异测试（Mutation / Fault Injection）**：与其到处找真实历史 Issue，不如在真实仓库里自动合成“能破坏现有测试套件”的真实级缺陷 | 从 128 个仓库自动合成 **50,000 个缺陷修复训练实例**，训出 SWE-agent-LM-32B（40.2% Pass@1） |
| **Live-SWE-agent** | arXiv:2511.13646 (2025.11) | 软件工程师在修复杂系统时，会现场写调试脚本、分析工具来帮自己修代码 | 让 Agent 在运行期动态修改和进化自己的脚手架工具（Scaffold），在 SWE-bench Verified 上不靠 test-time scaling 拿到 **77.4%** |

---

## 三、结合你的积累，怎么把「软工深度」变成你自己的 AI 课题？

你手里有一个别人很难复制的经验：**你亲自带着 AI 复刻并验收了 30+ 个复杂前端/移动端应用（淘宝 38 节点 46 转移、京东、微信等），写过完整的数据绑定（`getState`）、路由栈、MCP 工具接口，还抓过大量“AI 写出的代码看着界面能跑，但底层状态没绑上、返回栈乱跳、多端数据不一致”的架构级缺陷。**

这就是一个极具辨识度的 **SE × AI** 方向：

### 选题方向：面向全栈/GUI 应用生成的「状态—界面—契约」一致性验证与修复（或强化学习）
- **软工洞察（为什么只有懂工程的人看得到）**：
  现有 Web/App 生成基准（包括各类 vibe coding 评测）只看页面能不能渲染出来、或者简单点一下崩不崩。但在真实软件架构里，**UI 组件层（View）、路由控制层（Navigation）与业务状态层（State Store / API Contract）经常发生静默脱节（Silent Desynchronization）**——也就是你在拼多多/京东复刻里总结的《数据-UI联动-根因思考》和《06-nav-rootcause-report》。
- **AI 做法（为什么它是纯正算法工作）**：
  1. **静态 AST/状态流图 + 动态 GUI Agent 探测联合 Verifier**：不仅让 Agent 看屏幕，还抽取出前端组件树与 Store 写操作的依赖图，自动生成“状态不变式检查（State Invariant Oracles）”；
  2. **把这套 Verifier 变成 RL / DPO 的密集奖励（Dense Process Reward）**：训练代码模型或 GUI Agent 在生成/修复应用时，不仅画面对，而且状态流转 100% 闭合。
- **求职对口度**：
  - 投 **Coding Agent / Code LLM 岗**：你懂 Repo 级状态流、AST 与可执行环境合成（对标 SWE-Gym / SWE-Shield）；
  - 投 **GUI Agent / CUA 岗**：你懂如何用内部业务状态构造零误报 Verifier（对标 OpenMobile-2）；
  - 投 **实验室毕业/软工顶会**：这是最标准的“全栈 GUI 应用的非崩溃功能缺陷自动判定与修复”。
