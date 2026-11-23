# GUI 测试 × 软工 × CUA 文献与方向汇报（2026-10）

> 截止 2026-10-18。用途：组会 / 导师面谈的完整文献汇报与选题讨论。
> 事实部分来自 `raw/` 下四份机械检索记录（逐条打开 arXiv / 会议页核对）和远端 [Testing-Survey](https://github.com/ZYY0321/Testing-Survey) 的 `catalog.md`。
> **“判断”“方向”两类段落是我的观点，汇报时请当作讨论稿，不是文献结论。**

## 0. 材料从哪里来

| 来源 | 篇数 | 说明 |
|---|---|---|
| 远端 Testing-Survey `catalog.md` | 37 + 3 篇综述 | 合作者细读，带 notes；本稿只引用，不复写 |
| `raw/existing-verified.md` | 97 | 之前毕设 / OpenMobile-2 / UX-Agent 调研积累，已用 arXiv API 补版本与标注场合 |
| `raw/gui-testing-gaps.md` | 37 | 远端没有的 GUI 测试论文：显示缺陷经典线、无障碍、鸿蒙、测试 Agent |
| `raw/se-ai.md` | 45（+8 背景） | 软工 × AI：测试生成、代码 Agent、架构质量、评测可信度、UI 代码生成 |
| `raw/cua-agents.md` | 40 + 通义专节 | CUA 基座、RL/验证器、基准、世界模型与混合动作空间 |

口径约定：
- “场合”只写在官网 / DOI / arXiv journal-ref 上能看到的；作者 GitHub 自称录用的标“待核”。
- 数字只抄摘要。摘要和正文冲突的（VisionDroid、GUIPilot、RedTeamCUA 等）以笔记为准，汇报时不要引用冲突数字。

---

## 1. 一页总览：三个领域其实在问同一个问题

| | GUI 测试（SE） | 软工 × AI | CUA（AI） |
|---|---|---|---|
| 生成 | 探索 / 意图 / 场景生成（GraphDroid、ScenGen、LLMDroid） | 测试生成、变异反馈（MUTGEN、AdverTest） | 任务合成、环境合成（MAI-Gym、SoftwareGym、EvoCUA） |
| **判定** | **oracle**：非崩溃缺陷、设计稿、性质（VisionDroid、GUIPilot、Kea/PropGen） | **验证器 / 奖励模型 / LLM-judge**（SWE-RM、TestJack、Bias in the Loop） | **verifier / PRM / judge**（IRA、VisCritic、StainFlow、AgentHorizon） |
| 充分性 | 覆盖、缺陷检出 | 基准有效性、污染、捷径（SWE-Bench Illusion、Shortcutting） | 基准饱和、过程评测（OSWorld-Pro、OSWorld 2.0） |

**判断**：2026 年三个领域的瓶颈都收敛到“怎么可靠地判断结果对不对”。
- SE 一侧叫 test oracle，几十年积累了性质测试、蜕变关系、差分测试、设计规格比对等方法；
- AI 一侧叫 verifier / reward，正在被 RL 规模化需求倒逼（MAI-Gym 的“执行验证的任务判定器”、SoftwareGym 的“运行时验证”本质就是 oracle）；
- 两边的证据都说明“只靠 VLM/LLM 看图判错”不够可靠：VisionDroid Precision 0.50–0.76；AgentHorizon 专门构造负例检验裁判；TestJack 发现约 34.4% 判对的试验违反任务要求；OSWorld-Pro 上 Claude Opus 5 从 83.4% 掉到 75.7%。

这是本汇报的主线，也是我们两组方向的交汇点：**UX-Agent 做的“主动验证型 oracle”（视觉提议 → 布局树复核 → 滑动探测还原），正是 CUA 训练急需的那类可执行判定器。**

---

## 2. GUI 测试：版图与新进展

### 2.1 远端已覆盖的主干（37 篇，详见 Testing-Survey）

按三问归类，汇报时每类讲 1–2 篇即可：

| 类别 | 代表作 | 一句话 |
|---|---|---|
| 探索 / 生成 | GPTDroid (ICSE'24)、LLMDroid (FSE'25)、GraphDroid (ASE'26)、TraceDroid (FSE'26)、InterDroid (ICSE'26)、BugHunter (FSE'25)、FuncDroid (ISSTA'26) | LLM 做规划，重点从“覆盖更多”转向“功能意图、跨应用、代码风险引导” |
| 非崩溃 oracle | VisionDroid、GUIPilot (ISSTA'25)、KuiTest (ICSE SEIP'25)、LDMDroid (TOSEM)、ChromaEyes (ISSTA'26)、WebTestPilot (FSE'26) | 外部规格（设计稿、数据容器、需求）比纯模型常识更稳 |
| 性质 / 规约 | Kea (ASE'24)、PropGen (ASE'26)、iPBT (ISSTA'26) | 把业务性质写成 P-I-Q，再自动生成 |
| 迁移 / 维护 / 修复 | ITeM、LLMigrate (ISSTA'25)、GUIRevive (ISSTA'26)、TUSR (FSE'26)、Web 脆弱性实证 (ASE'25) | 测试资产复用与演化 |
| 评测 / 性能 / 用户 | UI-Lens (CVPR'26)、PerFrame / GUIWatcher（SEIP）、Reca11 (ICSE'25)、PinATA (ISSTA'25) | UI-Lens 直接评“多模态模型能否看出显示缺陷” |

### 2.2 本轮补齐：显示缺陷与 UX（与 UX-Agent 最近）

经典锚点（汇报背景页必放；综述背景另加 Vision-Based Mobile App GUI Testing: A Survey，ACM CSUR 2026，arXiv 2310.13518）：

| 论文 | 场合 | 关键数字 |
|---|---|---|
| OwlEye | ASE 2020 | 4,470 张截图；P 85% / R 84%；定位 90% |
| Nighthawk | TSE 2023 | P/R 0.84；定位 AP 0.59 |
| dVermin | ASE 2022 | 字体 / 显示放大导致的截断、重叠；页面级 P/R 97% |
| ReDeCheck | ISSTA 2017 | 响应式网页布局失败 |
| SALAD | ICSE 2024 | 不同屏幕尺寸下的 reflow 无障碍问题 |

2025–2026 新工作：

| 论文 | 场合 | 做法 | 与 UX-Agent 的关系 |
|---|---|---|---|
| **Minuku** | ASE'25 Industry | 微调 VLM 学“预期显示”，查遮挡、缺失、溢出；电商部署检出 40 个新问题 | 最直接的工业竞品；纯视觉，无布局树复核 |
| **Proactive-MW** | arXiv 2604.19081 | 探索中主动触发分屏 / 折叠 / 窗口切换，SoM + MLLM 判错；相对全屏截断 +184% | “主动改变形态再判错”，和我们的主动滑动探测同一思路 |
| **RotDroid** | arXiv 2608.25425 | 构造横竖屏语义等价状态作为蜕变 oracle；94 个新缺陷，47 确认 | 蜕变关系做显示 oracle，可直接借鉴 |
| **OH-Overlap** | ASE'25 Industry | OpenHarmony 100 个应用、3,326 万个重叠实例分类；高代价遮挡作为性能缺陷 | **唯一的鸿蒙 UI 重叠实证**；关注性能，不是可见性 |
| Janus | ICSE'25 | 浏览器渲染的“视觉增量一致性” oracle；34 个缺陷 | 差分 oracle 范例 |
| ScreenAudit / TaskAudit | CHI'25 / CHI'26 | LLM 查屏幕阅读器问题；交互中才出现的无障碍错误 | UX 质量的另一维 |
| A11yScan / GenA11y / A11yArgus / DroidPalette | ICSE'25 / FSE'25 / CHASE'26 / ASE'25 | 场景驱动无障碍检测；DroidPalette 还做颜色问题**自动修复**（67.72%） | 检测 → 修复的路径 |

**判断**：
1. 显示缺陷检测已经从“截图分类”（OwlEye、Nighthawk）走到“VLM 判断”（Minuku、UI-Lens、VisionDroid），但误报仍是主要问题，没有人系统地把**结构信息（布局树）和主动交互**拿来消歧。这正是 UX-Agent 的三段式在文献中的定位。
2. “改变设备形态 / 显示配置再比较”（dVermin、Proactive-MW、RotDroid）是一条清楚的上升线，而鸿蒙的“一次开发、多端部署”天然就是这种场景，**目前没有在 ArkUI 上做的工作**。

### 2.3 鸿蒙 / OpenHarmony

| 论文 | 场合 | 内容 |
|---|---|---|
| HmTest | JCST 2025 | 白盒页面转移图 + 黑盒 RL 探索，9 个 HarmonyOS NEXT 应用 |
| HapTest | FSE Companion'25 | ArkTS 动态分析框架；20 个头部应用中 11 个发现 26 个新崩溃 |
| ATH / ITeM-HM | arXiv 2607.11245 | Android→OpenHarmony 测试迁移基准；36 个商业应用；ReSPlay 15%、ITeM 26% |
| OH-Overlap | ASE'25 Industry | 见上 |

**判断**：鸿蒙测试还处在“基础设施与崩溃”阶段，**非崩溃显示缺陷几乎是空白**；我们有华为项目的真实数据和 ArkUI 布局树访问能力，这是稀缺资源。

### 2.4 Agent 当测试员（GUI 测试与 CUA 的交界）

| 论文 | 场合 | 关键数字 |
|---|---|---|
| GUITester / GUITestBench | ACL 2026 Findings（arXiv 2601.04500） | 143 个任务、26 个缺陷；F1 48.90%（Pass@3），基线 33.35% |
| GUITestScape | arXiv 2605.29532 | 61 个应用、508 个预置缺陷；同时含交互与显示缺陷；GUIJudge 分能力诊断 |
| MemoDroid | ASE'25 | 三层记忆；覆盖提升 79–97% |
| TestWeaver | ASE'25 Industry | 美团部署：成功率 92%、每例 $0.11 |
| BugSpot / TreeMind / LTGDroid / BugRepro / AndroB2O | FSE'25 / arXiv / ASE'25 | 缺陷报告复现与基于失败的 oracle |
| SpecOps | ICSE'26 | **反过来测 GUI Agent**：5 个真实 Agent 中 164 个 bug，F1 0.89 |
| AnaDroid | ISSTA'26 | 28.4 万条工业失败脚本的根因分析 |

**判断**：最强的“Agent 测试员”在 GUITestBench 上 F1 也只有约 49%；**找缺陷对 CUA 来说仍是很难的能力**，且没有人用 RL 专门训练它（见方向 B2）。

---

## 3. 软工 × AI（选讲）

完整 45 篇见 `raw/se-ai.md`。下面挑出跟我们故事相关的。

**3.1 测试生成与测试 Agent**
- MUTGEN（TSE）：变异反馈进提示。有的测试套件覆盖率 100%，变异分数却只有 4%，说明**覆盖不等于判错能力**。
- AdverTest（ISSTA'26 待核）：测试 Agent 与变异 Agent 对抗。
- SWE-Mutation（ACL'26 Findings）：用“骗测试的变异解”评测 LLM 生成的测试。
- 测 Agent 本身：ABTest、LogicHunter、HarnessTester。HarnessTester 发现现有测试覆盖到的“依赖 LLM 输出的代码”不到一半。

**3.2 代码 Agent 的训练基础设施（可类比 GUI）**
- SWE-Gym / R2E-Gym / SWE-smith（背景）→ SWE-Stream（80,874 个验证任务）、SWE-RM（不执行测试的奖励模型）、SWE-PRM（过程反馈 +10.6pp）、Agent-RLVR。
- **判断**：代码领域已经走完“合成环境 → 验证器 → RL”这条路，GUI 正在复制（MAI-Gym、SoftwareGym）。代码侧踩过的坑可以直接搬来当研究问题，例如验证器被钻空子、测试不足导致假通过。

**3.3 架构与代码质量（实验室 SE 方向的抓手）**
- SWE-Shield：在已解决的 issue 里，完全满足设计约束的不到一半。
- SmellBench：注意有**两篇同名不同文**，2605.07001 讲架构坏味道，2606.05574 讲重构。
- SWE-CC：功能正确的补丁仍违反 43.1% 的贡献规范。
- Refactoring Runaway、OpenCodeReview、CodeRabbit 实证：CodeRabbit 的审查评论被拒绝 56.3%。

**3.4 评测可信度**
- SWE-Bench Illusion、Verified 记忆、BenchChecker（USENIX Security'26）：都在讲污染与记忆。
- Shortcutting：60–90% 的轨迹在尝试走捷径。
- TestJack：重判后约 34.4% 原本“通过”的试验违反任务要求。
- Bias in the Loop：LLM-judge 受提示线索影响。
- **判断**：这是方向 B1 的直接方法来源，即用 SE 的“判定器有效性”研究方法去审计 GUI verifier。

**3.5 UI 代码生成与视觉验证**
- ArtifactsBench、WebGen-Agent、UI2Code^N、Vision2Web、WebUIProof、WebGen-R1：生成 UI 后都靠**截图 + VLM judge + GUI Agent 测试**来验证。
- **判断**：这里的“验证”就是显示缺陷检测。UX-Agent 的判定器可以作为 UI 代码生成的奖励信号，这是一条容易被忽视的落地路径。

---

## 4. CUA：2025H2–2026 进展

### 4.1 重点：通义 OpenGCUA 与 MAI-Gym（2026-10 第三周）

**OpenGCUA: Toward a Fully Open Stack for Generalist Computer Use**
- 链接：[arXiv:2610.22200](https://arxiv.org/abs/2610.22200)，2026-10-15；[GitHub](https://github.com/Tongyi-MAI/OpenGCUA)（Apache）；[项目页](https://tongyi-mai.github.io/OpenGCUA/)。署名 Alibaba Token Hub / MAI-UI Team。
- 定义“通才型 CUA”（GCUA）：由模型自己决定**怎么观察、怎么动作、怎么组织工作**，在视觉界面和程序接口之间切换。对标对象是闭源的 GPT-6 Astra computer-use。
- 核心设计是**代码执行**：中间结果决定后续操作，模型的编程能力直接用于操作电脑。
- 定位为持续开源全栈的项目，这是第一版。

**MAI-Gym**
- 链接：[arXiv:2610.20939](https://arxiv.org/abs/2610.20939)，2026-10-14。
- 评测、数据采集、在线 RL 走同一条 rollout 管线，覆盖手机、电脑、Web；接入 10 个现有基准；可扩到 2 万个并行环境。
- **自动合成可重置的模拟 App 和跨 App 世界，每个任务配执行验证的判定器**。
- MAI-Gym-9B：MobileWorld 78.4%，OSWorld-Verified 76.2%。

同组脉络：GUI-Owl / Mobile-Agent-v3（2508）→ OSWorld-MCP（2510）→ MobileWorld（2512）→ MAI-UI（2512）→ GUI-Owl-1.5（2602）→ STAMP（2605）→ Qwen-UI-Agent（2607）→ MAI-Gym + OpenGCUA（2610）。

**我们能借的灵感（判断）**：
1. **GUI 加代码的混合动作空间**被头部团队确认为主线（OpenGCUA、Qwen-UI-Agent 的 GUI/CLI 交错、OS-Helix、HybridCUA、EE-MCP），和 OpenMobile-2 的 GUI+MCP 同一方向。
2. **可重置的模拟 App 加判定器**成为 RL 基础设施的标配（MAI-Gym、SoftwareGym 合成 182 个应用、AppDeltaWorld、AutoGUIWorld）。这些判定器目前只判“任务完成”，**不判“界面是否有缺陷”**，这是我们能插进去的位置。
3. 待办：用 TokenHub 通道精读 OpenGCUA 全文，补齐动作空间、训练配方和评测数字（目前只核对了摘要）。

### 4.2 基座模型（选讲）

| 模型 | 时间 | 关键数字 |
|---|---|---|
| Qwen-CUA | 2026-08 | 纯截图 + 键鼠；OSWorld-Verified 86.2；OSWorld 2.0 binary 18.5 |
| Qwen-UI-Agent | 2026-07 | MobileWorld 82.1%、OSWorld-Verified 79.5% |
| UI-Venus-2（蚂蚁） | 2026-08 | 170+ 多语言移动应用 |
| EvoCUA（美团） | 2026-01 | 可执行验证器自动生成任务；OSWorld 56.7% |
| GUI-Owl-1.5 | 2026-02 | OSWorld 56.5、AndroidWorld 71.6、OSWorld-MCP 47.6 |
| Step-GUI | 2025-12 | 校准步级奖励；AndroidWorld 80.2% |
| UI-TARS-2 / OpenCUA / ScaleCUA | 2025H2 | 背景 |

**判断**：OSWorld-Verified 已经到 80% 以上，接近饱和。新的竞争点转向长程任务（OSWorld 2.0 中人类中位完成时间约 1.6 小时）、过程正确性（OSWorld-Pro）、安全（MobileWorldSafety，攻击成功率 40.4–66.9%）、鲁棒性（AndroidReality）和稳定性（GraceBench）。

### 4.3 RL、验证器、过程奖励

- IRA：交互式奖励 Agent，调用工具从执行后的环境状态取证。GUI-RewardBench 准确率 86.9%。
- VisCritic：比较动作前后的截图，判断动作是否成功。
- StainFlow、Adaptive-Group PRM：分阶段过程奖励。
- GSAR：把目标状态中的 UI 元素作为奖励锚点。
- WM-R1：用世界模型代替真实环境做 rollout。
- AgentHorizon（ServiceNow）：1,373 个任务，检验 11 个裁判能否区分成功轨迹与“完成了相近指令”的轨迹。
- **判断**：这批工作在重新发明测试 oracle。IRA 的“取证后判定”就是基于状态的 oracle，VisCritic 就是前后差分 oracle。几乎都没有引用 SE 测试文献，这是我们 SE 背景的切入优势。

### 4.4 世界模型、记忆、混合动作空间

- 世界模型：LGWM（AUC 0.987，每次判定 17ms）、AppDeltaWorld（把下一屏预测为可执行 HTML）、AutoGUIWorld（不部署真实软件，直接生成 GUI 场景）。
- 记忆：DeltaReplay（复用成功轨迹，最多 +25.0pp）、STAMP。
- 混合动作空间：OSWorld-MCP（o3 在 15 步预算下从 8.3% 提到 20.4%）、EE-MCP（MCP 与 GUI 混合策略）、HybridCUA（OSWorld 53.6%）、OS-Helix。
- UX 评估 Agent：Avenir-UX（用 SUS、SEQ、出声思考法评 UX；摘要无数字）。

---

## 5. 方向建议

两组方向共用同一个核心资产：**能主动验证的 GUI 判定器**。A 组把它做深，B 组把它卖给 CUA。

### A 组：从 UX-Agent 出发（SE 场合，可快速出成果）

**A1. 鸿蒙显示缺陷基准 + 结构与交互协同的主动 oracle**（推荐作为近期论文）
- 问题：VLM 判显示缺陷误报高（VisionDroid P 0.50–0.76），工业方案 Minuku 只用视觉；鸿蒙上没有任何显示缺陷基准。
- 做法：把 UX-Agent 三段式整理成方法，即视觉提议 → ArkUI 布局树复核 → 滑动 / 展开探测并还原；配套发布鸿蒙截断、遮挡、溢出基准，标出真缺陷和“滑动后可见”类假阳性；对比 VisionDroid、Minuku 式纯 VLM、OwlEye 式分类器和 UI-Lens 上的模型。
- 新意：首个 ArkUI 显示缺陷基准；把“主动交互消歧”作为 oracle 的一部分。
- 场合：ISSTA / ASE / ICSE SEIP（有华为背景，SEIP 很合适）。
- 风险：数据披露需要华为同意；需要做好开源替代集（OpenHarmony 开源应用）。

**A2. 多形态蜕变 oracle：一次开发、多端部署下的显示一致性**
- 问题：dVermin（字体放大）、Proactive-MW（分屏 / 折叠）、RotDroid（横竖屏）证明“改变显示配置再比较”很有效，但它们分散在 Android 上，各管一种变化。
- 做法：在鸿蒙多设备、折叠屏、字体缩放、深色模式下定义统一的**内容可见性蜕变关系**（同一语义内容在不同配置下应可达且可读），用布局树对齐跨配置控件。
- 场合：ICSE / FSE。A1 的数据可复用。

**A3. 检测 → 修复闭环：ArkUI 布局缺陷自动修复**
- 依据：DroidPalette 已经做颜色无障碍修复（67.72%），UI2Code^N 和 WebGen-R1 已有“渲染—看—再改”的闭环。
- 做法：把 A1 的判定器当修复 Agent 的验证器，修复截断和溢出（改约束、改换行、改尺寸），修完重渲染复核。
- 价值：一头连 SE 的程序修复，一头连 AI 的奖励信号（为 B 组铺路）。

### B 组：更偏 AI（CUA / 后训练，适合求职叙事）

**B1. 测试级验证器：用 SE oracle 方法构造和审计 GUI RL 奖励**（推荐作为主线）
- 问题：GUI RL 的判定器要么是规则（MAI-Gym、SoftwareGym 的执行验证），要么是 VLM judge；AgentHorizon、OSWorld-Pro、TestJack 都表明判定器会被糊弄或系统性偏差。
- 做法：
  1. 审计：参考 TestJack、Shortcutting 的方法，量化现有 GUI verifier 的假通过率和可被钻空子程度（在 MAI-Gym 开源环境上）。
  2. 构造：引入 SE 的状态取证、蜕变关系和差分 oracle，组成多证据验证器，并加上“界面缺陷”维度（UX-Agent 判定器）。
  3. 证明：用它做在线 RL 的奖励，对比 IRA、VisCritic 的下游成功率和奖励钻空子程度。
- 为什么是我们：SE 背景加上 CUA 训练经验（OpenMobile-2），两边文献都熟。
- 场合：NeurIPS / ICLR（偏 AI），或者把审计部分拆出来投 ISSTA / FSE。

**B2. RL 训练的 GUI 测试 Agent：在注入缺陷的合成 App 里学会“找 bug”**
- 问题：最好的 Agent 测试员 F1 约 49%（GUITestBench），GUITestScape 有 508 个预置缺陷但只用于评测；合成 App 平台（MAI-Gym、SoftwareGym、AppDeltaWorld）只训练“完成任务”。
- 做法：在可重置的模拟 App 中用变异算子注入功能与显示缺陷（借鉴 MUTGEN、AdverTest 的变异思想），奖励为“发现并正确报告缺陷”；评测在 GUITestBench / GUITestScape 和真实鸿蒙应用上进行。
- 亮点：把测试变成一种可验证的 RL 任务，因为注入的缺陷自带标准答案，天然是 RLVR。
- 风险：工程量大；建议在 MAI-Gym 开源后基于它做，不自己搭平台。

**B3. 移动端 GUI + 代码 / MCP 混合动作的选择与信用分配**
- 依据：OpenGCUA、Qwen-UI-Agent、HybridCUA、EE-MCP 都在桌面端，移动端只有 MAI-UI、OSWorld-MCP 的部分工作；OpenMobile-2 已有 GUI+MCP 经验。
- 研究问题：什么时候该走 GUI、什么时候该调工具 / 写代码；长轨迹中混合动作的信用分配。
- 适合放进求职叙事，作为 OpenMobile-2 的延续。

**B4（SE 场合的备选）. CUA 的可靠性测试**
- 依据：SpecOps（ICSE'26）、AndroidReality、GraceBench、MobileWorldSafety。
- 用蜕变扰动测试 GUI Agent 的稳定性，这是 SE 实验室最容易接受的“AI 方向”。

### 推荐组合（判断）

- **近期（1–3 个月）**：A1。数据和系统都有，最快成稿，满足实验室要求。
- **主线（3–9 个月）**：B1。判定器是 A1 的成果，直接复用；叙事是“SE oracle 让 CUA 的 RL 奖励更可信”，同时对 SE 和 AI 岗位都成立。
- **加分项**：B2 作为 B1 的应用实验；B3 作为求职材料里 OpenMobile-2 的延续。
- 需要和导师确认：华为数据能否用于论文；实验室对投 AI 会议的态度。

---

## 6. 汇报结构建议（约 30–40 分钟）

1. 动机：三领域同一瓶颈（第 1 节表）—— 3 分钟
2. GUI 测试版图：三问 + 远端 37 篇速览 —— 8 分钟
3. 显示缺陷与鸿蒙专题：经典到 VLM，空白在哪里 —— 7 分钟
4. Agent 当测试员 / 测 Agent —— 4 分钟
5. 软工 × AI：验证器和评测可信度 —— 5 分钟
6. CUA 进展 + 通义 OpenGCUA / MAI-Gym —— 7 分钟
7. 方向 A / B 与推荐组合 —— 6 分钟

必读精讲清单（12 篇）：VisionDroid、GUIPilot、OwlEye、Minuku、Proactive-MW、OH-Overlap、GUITestScape、SpecOps、TestJack、IRA、MAI-Gym、OpenGCUA。

---

## 7. 待核实 / 待补

- [ ] OpenGCUA 全文精读（动作空间、训练、评测数字）——用 TokenHub one-shot。
- [x] GUITester：已核实为 ACL 2026 Findings。
- [ ] AdverTest 的 ISSTA'26：去 researchr 确认。
- [ ] VisionDroid 场合：examples 写的是 TSE / ICSE'26，远端笔记写“未确认录用”，以远端为准，再查一次。
- [x] 旧 97 篇已逐条核对（`raw/existing-verified.md`）：1 处编号写错（毕设《文献综述.md》把 2310.13518 写成 LLM Agent 综述，实际是 Vision-Based Mobile App GUI Testing: A Survey，现为 ACM CSUR 2026），19 处与仓库记载不一致（多为“写 arXiv、现已录用”，另有 CoMEM 的 NeurIPS'25、OS-Symphony 的 ACL'26 Main 查无录用），11 处改名（如 OpeFlo→Avenir-UX、SimuWoB→ScaleWoB）。旧文档未改动，引用时以核对表为准。
- [ ] 2026-04 以前的 97 篇中，与本稿主线相关的（毕设表中的 GUI Agent 论文）是否需要进入汇报背景页。
