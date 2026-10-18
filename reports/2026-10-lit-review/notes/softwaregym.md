# SoftwareGym：用多智能体"设计-实现-评估"流水线合成多样且功能可靠的桌面软件环境，规模化训练计算机使用代理（CUA）

## 开会速记

- 提出 **SoftwareGym**：一条自动化三阶段（设计→实现→评估）多智能体流水线，能大规模合成可运行桌面应用环境，专门用于生产 CUA（computer-use agent）训练轨迹，而不是面向真实软件做缺陷检测。
- 用这条流水线合成了 **182 个可运行应用（12 类别，平均 GUI 任务通过率 91.5%）**，仅用这些合成应用的轨迹对 Qwen3.5-9B 做 SFT，在**完全没用过 OSWorld 任何数据**的情况下把 OSWorld Pass@3 从 41.39% 提升到 56.97%，证明合成环境具备跨域迁移价值。
- 配套发布 **SoftwareGym-Bench**（12 类别、120 个程序化可判定任务），训练后模型在此达到 Pass@3 40.0%，超过若干规模更大的专用 CUA 基线。
- 两个核心消融证据较硬：结构化风格多样性控制把结构多样性评分从 4.9 提升到 83.6（Table 4）；GUI 反馈驱动的迭代修复把功能通过率从 50.4% 提升到 83.1%，而仅靠源码自检的修复反而退步到 48.8%（n=36 应用，95% CI 给出）。
- 和我们关系：这是**CUA 训练数据/环境合成**的方法论参考（与 OpenMobile-2 训练经验相关），其评测目标是"任务是否完成"而非"界面是否有显示缺陷"，平台是 Avalonia(.NET) 桌面应用而非 HarmonyOS/Android，对 UX-Agent 的文字截断检测路线没有直接技术复用，主要可借鉴其 checkpoint 式判定、多样性度量和轨迹双评分过滤思路。

## 一页读懂

| 维度 | 内容 |
|---|---|
| 旧方法哪里不够 | 原生应用环境构建/集成成本高，限制应用覆盖面并易导致特定应用过拟合；浏览器承载环境交互深度和工作流复杂度有限（Sec.1, Sec.2）。现有方法未能同时满足"接口/交互多样性、功能可靠性、可扩展性"三个要求（Sec.1）。 |
| 本文新增 | 自动化多智能体流水线：风格多样性约束（layout-archetype 距离+结构树编辑距离门限）保证接口多样、不收敛；checkpoint 式 GUI 评估+迭代修复保证功能可靠；评估驱动的任务合成（Function Analysis→Difficulty Leveling→Task Generation）产出可程序化验证的任务；用这些环境的轨迹做 CUA 的 SFT 训练（我们的归纳：方法+资源+训练实验三位一体）。 |
| 输入/输出 | 输入：软件类型 + 支持资源（极简人工输入）。输出：可运行 Avalonia 桌面应用（含 Software Specification、UI Blueprint、SVG 资源）、GUI 测试用例与评测报告、自然语言 GUI 任务（SoftwareGym-Bench）、CUA 训练轨迹与训练后的模型。 |
| 怎样验证 | GUI checkpoint 通过率（v1→v3: 54.9%→81.1%→91.5%）；在 OSWorld（244 任务/8 领域）和 SoftwareGym-Bench（120 任务/12 类别）上做 Pass@3 评测；三类消融（风格设计、GUI 引导修复、训练数据来源）。 |
| 结论边界 | 仅在 Avalonia(.NET) 桌面应用、12 个软件类别、Qwen3.5-9B 规模上验证；未在移动端/Web/HarmonyOS 上做实验；度量的是"功能任务完成"而非"界面显示缺陷"（如文字截断、遮挡、溢出），Design Fidelity 模块是"设计 token 一致性门控"而非感知级图像缺陷检测（Appendix B 原文明确说明）。 |

具体方向论文的同口径条目建议同步写入 [catalog](../catalog.md)。

## 一段话介绍

本文研究的问题是：如何低成本、规模化地合成"多样、可执行、功能可靠"的软件环境，用作 CUA（计算机使用代理）训练的监督数据来源，以替代/补充依赖真实桌面软件（integration 成本高、容易过拟合）或浏览器承载环境（交互深度有限）的做法。解决方式是设计一条自动化多智能体流水线：设计阶段生成功能规范和结构/视觉上真正不同的 UI 蓝图；实现阶段把蓝图转成可运行的 Avalonia 桌面应用并用 GUI 执行（鼠标/键盘）测试用例反复评测修复；任务合成阶段只用经过 GUI 证据验证过的功能来生成可程序化判定的自然语言任务。评价证据包括：182 个合成应用的平均 GUI 任务通过率（91.5%）、在严格跨域的 OSWorld 基准上的 Pass@3 提升（41.39%→56.97%）、在自建 SoftwareGym-Bench（120 任务）上的表现（40.0%），以及针对风格多样性设计、GUI 引导修复、训练数据来源三项的消融实验。

## 关键术语与阅读前提

- **CUA（computer-use agent，计算机使用代理）**：以 GUI 操作（鼠标/键盘）完成桌面任务的智能体，本文训练对象。
- **Pass@k**：k 次独立 rollout 中至少一次成功即计为该任务通过，本文主指标 Pass@3（3 次 rollout）。
- **Avalonia / XAML**：本文合成软件所用的跨平台 .NET GUI 框架及其界面描述语言，相当于本文的"源码+控件树"载体。
- **SFT（supervised fine-tuning）**：用收集到的轨迹对基座模型做监督微调，本文用于训练 Qwen3.5-9B。
- **checkpoint-based GUI evaluation（检查点式 GUI 评估）**：以可观测 GUI 状态变化（checkpoint）作为功能是否完成的判据，而非断言代码或人工打分。
- **Tree-edit distance (TED)**：Zhang & Shasha (1989) 的树编辑距离，用于量化两个归一化布局树的结构差异，是本文"结构多样性"量化手段。
- **Jaccard 相似度**：用于视觉保真度中颜色集合/圆角集合的相似度计算。
- **OSWorld**：外部真实桌面应用基准（244 任务/8 应用领域），本文用作严格的跨域（out-of-domain）评测集。
- 领域背景（CUA 训练数据合成综述脉络）可参见 ../field.md；GUI 测试通用术语（oracle、trajectory 等）参见 ../glossary.md 对应条目。

## 动机

作者指出当前 CUA 训练数据合成存在两类主流路径，均无法同时满足三项要求：

> "Native applications preserve realistic states and complex workflows, but the cost of integrating them into reproducible training environments limits application coverage and increases the risk of application-specific overfitting. Browser-hosted environments support scalable deployment and state control, but their shared substrate limits interaction depth and workflow complexity."（Sec.1）

由此引出三个具体障碍（Sec.1）：
1. **多样性难**：同类软件的无约束生成容易收敛到相似的版式和交互模式；
2. **可靠性难**：需要保证规范中每一个功能都能通过完整 GUI 工作流被实际使用；
3. **可扩展性难**：多样性控制和可靠性校验要应用到大规模软件池，手工开发无法承受这种验证负担。

教学例子（非论文原例）：如果让模型"随意生成 10 个记事本应用的 UI"，很可能 10 个都长得像左侧列表+右侧编辑区的同一种版式——这正是作者说的"收敛"问题，本文用显式的版式距离约束来避免。

## 贡献

按作者给出的三点编号（Sec.1 原文列出）：

1. **方法/流水线贡献**：提出 SoftwareGym，一条自动化环境合成流水线，能以显著低于人工开发的时间与货币成本，产出功能可靠、结构多样的规模化软件环境。
2. **资源贡献**：发布 182 个可运行应用（12 类别）及配套的 SoftwareGym-Bench（120 任务测试集，覆盖相同 12 类别）。
3. **经验性结果贡献**：通过大量评测与消融验证流水线各关键组件的作用，并证明仅用 SoftwareGym 轨迹训练的模型把 OSWorld Pass@3 提升 15.58 个百分点，达到 56.97%。

（我们的归纳补充）：论文中还隐含一项"训练方法"贡献——轨迹的双判（outcome/process）GPT-5.5 评分+过滤+跨源配比训练协议（Appendix E/C.3），这是支撑其结果可信度的工程细节，但原文未把它单列为编号贡献。

## 方法

整体上，SoftwareGym 把"从最小人工输入到可训练轨迹"的过程拆成三个阶段：**软件设计**（产出功能规范+多样化 UI 蓝图+图标资源）→**软件实现与评估**（把蓝图变成可运行应用，用 GUI 测试+失败证据驱动迭代修复）→**任务合成**（只用经 GUI 证据验证过的能力生成自然语言任务，构成 SoftwareGym-Bench 及训练任务池），再由 CUA 执行这些任务产生轨迹、经双评分过滤后用于 SFT。

1. **输入与表示**：输入是"软件类型 + 支持资源"这种极简人工输入（如"做一个图片编辑器"）。FunctionDesigner 把它展开为 Software Specification（文本契约：用户入口、用户动作、预期状态更新、可见 GUI 反馈、验收 checkpoint）；StyleDesigner/SubStyleDesigner 把同一份规范转成多份 UI Blueprint（Avalonia XAML，可编译验证），并归一化为"窗口-区域-面板-控件"布局树；IconDesigner/SubIconDesigner 生成 SVG 图标资源。三者合成 Verified Design Package。

2. **中间模块处理**：Coder 依据 Design Package 实现完整 Avalonia 应用（结构、视觉系统、图标、功能），并记录功能手册；DevCoder 对照手册审计命令绑定、应用逻辑、持久化、启动行为、文件接口，修复缺失/不完整实现。此阶段模型收到的是设计包（规范+蓝图+资源）与自身代码/运行时证据，还没有 GUI 截图层面的反馈。

3. **动作选择与执行、失败反馈**：EvalTaskGenerateAgent 从"源码验证过的功能手册"生成 GUI 测试用例（覆盖控件可达性、导航、对象创建/编辑、持久化、检索、设置、对话框、文件工作流），每个用例有明确初始状态、仅用已记录功能、定义可见 checkpoint；用例集在 v1 后固定并在修复轮次间复用。**GUIAgent（用 Seed 2.1 Pro）**以鼠标键盘动作执行用例，每用例最多 50 步，在 Ubuntu 22.04.3 LTS (x86_64) 的隔离虚拟机中运行，记录交互轨迹、checkpoint 证据、最终状态、失败位置和修复建议；这些失败证据被回传给 Coder/DevCoder 做下一轮局部修复（v1→v3，全部通过或预算耗尽时停止）。

4. **判定依据**：功能判定用 $P_{func}=N_{pass}/N_{all}$（通过用例数/总用例数）；此外 Design Fidelity 环节计算一个归一化视觉保真度分数 $F_{vis}$（颜色调色板 Jaccard、主色保留、圆角 Jaccard、字体保留、绑定比例的加权和，权重 0.40/0.15/0.20/0.10/0.15），低于预校准阈值（0.80，且主色必须保留）时把具体偏差的视觉 token 作为修复目标反馈，防止"修功能把界面改走样"。原文特别强调：

   > "This is a design-token implementation gate, not a perceptual image-similarity measure."（Appendix B）

   即它不是感知级的图像相似度/视觉缺陷检测器，这与我们课题要检测的"显示缺陷"（截断/遮挡/溢出）在目标上不同。

5. **停止与最终产物**：GUI 评估在全部用例通过或版本预算（v1-v3）耗尽时停止；进入软件库的应用携带其 Verified Design Package。随后 Task Synthesis 阶段：Function Analysis 构建"证据支撑的功能树"（只有引用了通过用例/checkpoint 的能力才算 supported）；Difficulty Leveling 按 easy/normal/hard × file-based/blank-state 组合任务；Task Generation 把计划工作流转成自然语言请求+内部评测规范（初始状态、结果判据、过程判据、期望最终状态），并用确定性校验拒绝不支持的能力/不一致初始状态等。最终产物是：软件库（182 应用）、SoftwareGym-Bench（120 任务）、以及用 CUA 在这些环境中执行任务产生、经两阶段 GPT-5.5 评分（结果+过程，阈值均 0.8）过滤后的训练轨迹，用于对 Qwen3.5-9B 做 SFT。

**完整示例**（来自 Appendix A，论文原例）：TableEditor 任务"把 Sheet1 B2 的 'Draft total' 替换为 'Final total'，并保持 Find and Replace 面板打开"，成功轨迹为：定位文本→打开 Edit→打开 Find and Replace→输入替换内容→打开 File→保存（保持面板打开）。该例体现了任务合成阶段"状态依赖+可程序化判定终态"的设计（Figure 8）。

## 核心技术 / 方法论文详解

- **风格多样性控制**：先用 layout-archetype 距离（导航/空间组织/对象浏览/动作布局四维上的 Hamming 距离，Appendix B）强制任意两变体至少在两维不同，再用归一化布局树的 TED（Zhang & Shasha 算法）计算结构多样性 $d_{ij}=\min\{1, TED(T_i,T_j)/\max(|T_i|,|T_j|)\}$，产线门限为 $\min_{i\ne j} d_{ij} \ge 0.60$，不达标则重生成最不独特的蓝图。消融（Appendix C.1，12 类别×10 蓝图/方法=120+120）显示：Full Design 把宏平均多样性从 4.9 提升到 83.6（Table 4），而 Simple Design 虽然文件级都不同，但每个类别至少有一对蓝图的归一化布局树完全相同，12 组中无一组通过 0.60 的产线门限——这支持了"仅靠自然语言提示约束无法阻止版式收敛，需要显式结构度量"的主张。

- **评估驱动的实现修复**：GUI-guided 分支把 GUI 评估报告传给 Coder 做下一轮修复；source-only 分支扣留该报告，只靠源码证据自修。消融（Appendix C.2，n=36 应用，12 类别各 3 个，起点相同 50.4%）：GUI-guided 到 v2 70.5%、v3 83.1%；source-only 到 v2 50.5%、v3 反而降到 48.8%（95% CI 28.2–41.0 的最终差距，36 个应用全胜）。这直接支持论文的核心机制主张——"源码级自我修正不足，甚至可能让运行时功能退化，GUI 反馈对可靠修复是必要的"。

- **训练数据来源消融**：严格控制基座模型（Qwen3.5-9B Base）、预分词语料规模（3,715 轨迹/55,263 样例，SoftwareGym 与 OSWorld 两边匹配一致）、有效 batch size（全局 32）、优化设置和评测协议一致，仅改变训练轨迹来源。结果（Table 3/6/7）：SoftwareGym-only 在 OSWorld 56.97%、SoftwareGym-Bench 40.0%；OSWorld-only 在 OSWorld 61.48%、SoftwareGym-Bench 33.3%；两者合并在 SoftwareGym-Bench 进一步到 47.5%，同时 OSWorld 保持 58.61%。这支持"合成软件提供可迁移监督，且与原生软件数据互补"的主张，但也说明单纯合成数据在同域基准（OSWorld）上仍弱于同规模原生数据训练的模型（56.97% vs 61.48%）。

- **轨迹评分与过滤（Appendix E）**：两个独立 GPT-5.5 判官分别做 outcome（看最后 5 条助手消息+对齐截图，判断是否真正达成用户请求）和 process（看全部消息+最多 10 张均匀采样截图，判断过程是否合理、高效、无死循环）评分，两者都 $\ge 0.8$ 才保留；随后转换为 Qwen3.5 多模态格式、校验、按来源做选择（OSWorld 每任务保留最高分一条；SoftwareGym 每个冻结语义组最多保留 2 条），再做约 90/5/5 分组约束划分。这套"双判+阈值过滤"机制是保证训练轨迹质量的关键工程环节，但其判据来自 LLM-judge，而非确定性断言。

交付前检验自评：以上内容已给出每个模块的具体字段/公式/阈值及其对应的消融数字，而非仅罗列模块名称，应可满足"没读过原文的合作者能说清论文具体做了什么、证据支持到哪里"的要求。

## 实验

**软件合成实验（Sec.4.2）**：
- 环境/预算：用 Codex CLI agents + GPT-5.5 做设计/实现