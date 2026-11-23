# GUITester: 面向探索式GUI测试的缺陷发现多智能体框架

## 开会速记

- 本文指出现有GUI agent（UI-TARS、GUI-Owl、MAI-UI等）做探索式缺陷发现时存在两个系统性缺陷："目标导向掩蔽"（把真实bug当障碍绕过去）和"执行偏差归因"（把系统bug误判为自己点错了）。
- 作者构建了首个交互式探索测试基准GUITestBench：12个Android应用、26个真实缺陷、143个任务，并设计了Defect-Oriented/Exploration-Oriented两种任务和配套的规则/LLM裁判评测法。
- 提出GUITester：四智能体框架（Planner/Executor/Monitor/Reflector），核心是把"主动探测边界行为"（PEM）和"异常捕获与归因解耦"（HRM）分开做。
- 证据强度：在自建的143任务benchmark上，最佳基线F1仅33.35%（Pass@3），GUITester达48.90%，提升明显；但论文自己承认该benchmark规模小（26个缺陷），且存在假阳性（超时误判、Monitor领域知识不足）。
- 和我们关系：该工作检测的是**功能/交互类缺陷**（点击无响应、跳转错误、任务结果错误），论文明确把"重叠元素、文字截断、错位"等显示类缺陷列为未覆盖的future work，与我们UX-Agent关注的显示缺陷（文字截断/遮挡/重叠/溢出）互补而非重叠；但其"主动探测边界行为"(PEM) 和"异常归因、防止误报"(HRM) 的设计思路对我们主动滑动探测、候选复核环节有参考价值。

## 一页读懂

| 维度 | 内容 |
|---|---|
| 旧方法不够在哪 | 现有MLLM驱动GUI agent（UI-TARS、GUI-Owl、MAI-UI、Mobile-Agent-V3）为"任务成功率"优化，遇到异常倾向于找替代路径绕过（目标导向掩蔽）或把异常归为自己操作失误（执行偏差归因），导致探索式缺陷发现能力接近为零；已有测试自动化工作（AUITestAgent、GUIPilot、ProphetAgent、Temac）依赖预定义测试用例，不处理无预设意图的探索式测试；已有benchmark（GTArena）只评静态场景，不覆盖真实app的动态交互。 |
| 本文新增什么 | (1) GUITestBench：首个交互式探索缺陷发现benchmark；(2) GUITester：PEM（主动嵌入测试意图探测边界行为）+ HRM（异常捕获与归因解耦，防止误判/误报）的四智能体框架。 |
| 输入/输出 | 输入：defect-agnostic的导航任务描述（目标g）、当前GUI截图观测o、历史h；输出：动作序列a_t，以及最终缺陷报告（GUI_BUG判定+定位）。 |
| 怎样验证 | 在自建GUITestBench（143任务/26缺陷/12 app）上，用Recall/Precision/F1（规则匹配+LLM裁判Claude-4-Sonnet）对比6个开源GUI agent baseline + Mobile-Agent-V3，在Pass@1/Pass@3两种设置下比较GUITester与baseline；并在真实发布版app（ESPN、Fox News、Booking.com、Harbor Freight、Pinterest等）上做案例研究。 |
| 结论边界 | 仅在自建143任务规模的benchmark上验证，未做跨benchmark/跨平台泛化验证；仅覆盖交互类缺陷（ONR/UTR/NLE），不处理视觉布局类缺陷（重叠、错位、文字截断——原文第7节Limitations明确列为future work）；存在假阳性（超时误判、Monitor领域知识边界问题，见Appendix F）。 |

## 一段话介绍

论文研究的问题是：能否让GUI agent在没有预定义测试脚本/oracle的情况下，像人工探索式测试那样自主发现软件缺陷。作者发现现有agent因训练目标是"完成任务"，天然倾向于绕过异常（目标导向掩蔽）或把系统缺陷误判为自己的操作失误（执行偏差归因），因此几乎无法胜任这一任务。为验证并解决这一问题，作者先构建了GUITestBench——一个基于GitHub真实issue收集的26个缺陷、合成出143个导航任务的交互式基准，用规则匹配+LLM裁判的方式评估agent是否真正触发并报告了目标缺陷；然后提出GUITester框架，用Planner-Executor模块主动在导航子任务中插入测试意图子任务去探测边界行为，用Monitor-Reflector模块把"是否异常"和"异常归因于谁"两个判断解耦，防止agent用成功偏向掩盖缺陷或误判归因。证据来自在该benchmark上与6个主流开源GUI agent（UI-TARS系列、GUI-Owl、MAI-UI、Mobile-Agent-V3）的对比实验，以及在真实发布的商业App上的小规模案例验证。

## 关键术语与阅读前提

- **MLLM（多模态大语言模型）**：本文GUI agent的基础模型形式，接收截图等视觉输入生成动作。
- **Goal-Oriented Masking（目标导向掩蔽）**：论文定义的核心挑战1——agent为最大化任务成功率，倾向于把功能性异常视为"可绕过的障碍"而非"应报告的缺陷"（原文Introduction）。
- **Execution-Bias Attribution（执行偏差归因）**：核心挑战2——agent系统性地把触发失败归因于自己的操作误差（如坐标点偏），而非软件缺陷本身（原文Introduction）。
- **PEM（Planning-Execution Module，规划执行模块）**：GUITester的第一大模块，用于主动嵌入"测试意图"子任务。
- **HRM（Hierarchical Reflection Module，层级反思模块）**：GUITester的第二大模块，负责异常捕获（Monitor）与归因（Reflector）解耦。
- **ONR / UTR / NLE**：原文采用自GTArena（Zhao et al. 2024）的三种故障模式：Operation No Response（操作无响应，仅适用于UI缺陷）、Unexpected Task Result（任务结果与预期不符）、Navigation Logic Error（导航逻辑错误）。
- **UI defects vs UX defects**：论文定义UI缺陷源于单个组件实现错误（如点击失败），UX缺陷源于多组件交互流程的设计缺陷，无法归因到单一组件（原文§3.1.1，引用Baltes and Dashuber 2024的UX debt概念）。
- **Pass@1 / Pass@3**：评测协议——Pass@1是三次独立运行取平均分，Pass@3是三次运行中至少一次检测成功即记为成功（原文§5.1）。
- Agent角色：Planner/Executor/Monitor/Reflector——四个具体角色，均为GUITester架构组成部分（原文§4, Fig. 4）。

## 动机

作者在Introduction中以Figure 1为例说明两个核心障碍：当遇到一个"Clear Completed"按钮无法清除已完成任务的缺陷时，现有方法either (a) 自主寻找替代路径绕过缺陷（目标导向掩蔽），either (b) 如GUI-Owl那样把系统级渲染失败误解读为"点击位置没对齐"的执行误差，导致该缺陷在日志中被错误归为瞬时执行错误（Execution-Bias Attribution，原文Introduction, Fig.1描述）。原文还指出，探索式测试本身缺乏显式oracle，要求agent区分"自己操作失误"和"真正软件缺陷"（原文Introduction引Copche et al. 2023关于oracle缺失的论述）。另外原文提到：已有测试自动化工作仍依赖预定义测试用例，探索式测试（无预设意图地自主导航发现潜在缺陷，如monkey testing）仍是人工测试中最耗时、难以规模化但未被GUI agent触及的部分（原文§2 Related Works, Test Automation段）。已有benchmark如GTArena仅评估静态场景能力，未能捕捉真实应用的动态特性（原文§2 Benchmarks for GUI Testing段）。

## 贡献

原文按作者列出三条贡献（原文Introduction末尾）：

1. 定义并明确了MLLM驱动探索式GUI测试中的"任务成功偏向"（task-success bias）和"归因模糊性"（attribution ambiguity）两个挑战（问题贡献）。
2. 引入GUITestBench，一个包含多样化真实GUI缺陷的交互式评测框架（benchmark贡献）。
3. 提出GUITester，一个具备主动缺陷探测和层级反思能力的多智能体框架，显著提升缺陷发现率（方法贡献）。

需注意：贡献2虽称为benchmark，其构建流程（合成任务+规则/LLM裁判）同时包含评测方法论设计；贡献3的"显著提升"结论仅建立在同一自建benchmark的实验之上（见"实验"节）。

## 方法

GUITester整体是一个四智能体循环系统，由Planner分解任务并主动插入测试意图、Executor执行具体GUI动作、Monitor在每步后判定执行状态、Reflector在失败时负责归因并反馈给Planner调整后续规划。

**1. 输入是什么/怎样表示？** 输入是一个defect-agnostic的导航目标g（自然语言任务描述），当前环境观测o（截图）以及历史上下文h（原文§4.1.1公式）。不涉及源码分析或控件树输入，Monitor/Executor/Reflector均基于视觉截图观测工作。

**2. 中间模块怎样处理？**
- **Planner**：将导航目标g分解为子任务序列{s1,...,sn}=Planner(g,o,h)，每个子任务是导航子任务或"测试意图"（test intent）。Planner设计了三种测试意图模式（Appendix Fig.6）：Alternative Paths（探索同一功能的不同入口）、Boundary Conditions（测试边界输入，如空值或特殊字符）、State Validation（验证UI元素响应性和状态转换）。由Qwen3-VL-Plus驱动。
- **Executor**：接收子任务si、当前观测ot及子任务内动作历史，生成动作at=Executor(si,ot,{at'}t'<t)，采用现成GUI agent模型（UI-TARS、GUI-Owl等）作为backbone，通过链式思维推理生成动作；采样温度设为0.1以保证行为稳定（原文§5.1）。
- **Monitor**：在每个动作后观察环境响应，判定ct=Monitor(si,ot,at,ot+1)∈{DONE, FAIL, CONTINUE}，只负责捕获异常不负责归因；由GPT-4o驱动。FAIL会终止当前子任务并触发Reflector；CONTINUE允许Executor继续；DONE让Planner推进到下一子任务。

**3. 动作怎样选择、失败如何反馈？** 当Monitor判定FAIL，Reflector接收子任务si、执行轨迹τ={(ot',at')}和当前观测ot，输出归因结果r=Reflector(si,τ,ot)，由Qwen3-VL-Plus驱动。关键设计是"Visual Attribution"：在截图上标注交互点（原文引用Wu et al. 2025/Lu et al. 2024的坐标可视化思路），帮助Reflector区分"操作本身无效（如点错位置）"与"真实缺陷（如按钮确实无响应）"。归因后的反馈（Reflection Feedback）：若归因为agent自身导航错误，Reflector给Planner生成纠正建议用于后续规划；若是测试意图子任务失败，则无论归因结果如何都不影响后续规划，允许agent从当前状态继续探索（防止反复在同一处卡住）。

**4. 判定依据来自哪里？** 判定依据全部来自Monitor对环境截图前后状态变化的比较（是否符合该子任务预期结果）以及Reflector对完整执行轨迹τ（动作+观测序列）的回溯分析，不依赖源码或控件树的显式spec。

**5. 何时停止/最终产物？** Algorithm 1描述完整工作流：当Planner.GetLatestSubtask()返回空（所有子任务完成）则返回NOOP终止；或达到MaxSteps/重试上限后reset重新规划。最终产物是动作序列与沿途报告的GUI_BUG判定（文字形式的缺陷报告，附带定位的子任务/截图）。

一个完整例子（原文Appendix G.1）：在Fox News app，PEM生成一个针对搜索框的边界条件测试意图，输入特殊字符"@#$%"；正常搜索功能应拒绝或返回"无结果"，但该app却接受并返回了不相关的"Politics"内容；HRM正确将此判定为GUI缺陷而非执行错误（Monitor检测到实际结果与预期不符，Reflector未将其归为agent自身操作失误）。

## 核心技术 / 综述主题详解

本文是方法论文，核心主张有两条，分别对应PEM和HRM两个模块，实验设计直接服务这两条主张：

**主张1：主动嵌入测试意图（PEM）能提升探索场景下的缺陷暴露率。** 原文观察到agent导航倾向走最短路径，可能漏过隐藏在特定交互情境中的缺陷；PEM通过在导航子任务间穿插测试意图子任务（不打断任务完成）来增加暴露（原文§4.1.1）。该主张对应表2中"Analysis Across Task Types"实验：baseline在Defect-Oriented设置下有一定检测能力，但到Exploration-Oriented设置性能大幅下降，说明其检测能力难以在自主探索中被激发；而GUITester在两种设置下表现相对一致，作者将此归因于PEM的测试意图嵌入主动驱动Executor去探测边界行为而非被动等待遇到缺陷（原文§5.2.2，并引用Appendix Fig.15的搜索框边界测试案例为证据）。

**主张2：异常捕获与归因解耦（HRM）能同时减少漏报（绕过）和误报（错误归因）。** Monitor只负责"是否异常"而不判断"谁的错"，防止agent像baseline那样靠重复尝试、超时终止来掩盖缺陷；Reflector事后用可视化标注的交互点来区分agent操作失误和系统缺陷。该主张对应表2"Analysis on Defect Complexity"：Single-Action缺陷上GUITester提升显著，作者解释是因为HRM中Monitor在每步后立即捕获状态异常、Reflector在agent继续前完成归因，使瞬时缺陷不会被漏判或误判；Multi-Action缺陷上提升相对较小，因为触发这类缺陷还需要精确的多步导航能力，对规划和执行提出更高要求（原文§5.2.2）。

案例研究部分（§5.3，Fig.5 ESPN App）具体体现了HRM的归因能力：同一条轨迹中，agent误点"Connect or Cast"弹窗外部导致弹窗意外关闭（HRM正确归因为agent自身错误，触发自我纠正），而"Learn More"按钮确实无响应（HRM正确识别为真实GUI缺陷）；作者据此主张这种归因准确性对降低真实场景中的误报率是关键能力。

## 实验

**RQ1：现有GUI agent在探索式GUI测试场景中的表现如何？**
- 数据：GUITestBench全部143个任务（26个真实缺陷、12个Android应用、5个领域，来自公开GitHub issue）。
- 对比对象：GUI-Owl-7B/32B、MAI-UI-8B、UI-TARS-7B/72B/1.5-7B、Mobile-Agent-V3（均通过prompt wrapping加入测试意图，使其具备缺陷报告能力，见Appendix C）。
- 评测设置：三次独立运行；Pass@1为三次平均，Pass@3为三次中至少一次成功；判定用规则匹配（single-action缺陷）+ LLM裁判Claude-4-Sonnet（multi-action缺陷）。
- 指标：Recall=检测到缺陷的任务数/总任务数；Precision=检测到缺陷的任务数/声称有缺陷的任务数；F1为二者调和平均（原文§3.2.2公式）。
- 结果：所有baseline在Pass@1下F1均低于25%，最佳UI-TARS-1.5-7B为22.95%；Pass@3下提升到33.35%（原文§5.2.1），但仍有超70%缺陷未被检出。UI缺陷上baseline有一定检出能力，UX缺陷上几乎为零（只有UI-TARS-1.5-7B非零：UX-UTR F1=12.95%，UX-NLE F1=18.38%，均为Pass@1数字，原文§5.2.1）。
- 结论边界：能支持"现有agent在该benchmark规模下探索式缺陷发现能力很弱"，不能外推到该benchmark之外的其他应用/平台（原文未做跨数据集验证）。

**RQ2：GUITester解决这些挑战的有效性如何？**
- 结果（表1）：以UI-TARS-72B为Executor，Pass@3整体F1从19.55%（baseline）提升到43.70%（GUITester）；以UI-TARS-1.5-7B为Executor，Pass@3整体F1从33.35%提升到48.90%（最佳结果）。
- 按任务类型/缺陷复杂度分解（表2）：Defect-Oriented与Exploration-Oriented上GUITester表现相对一致，而baseline在Exploration-Oriented下大幅下降；Single-Action缺陷上GUITester提升显著，Multi-Action缺陷上提升相对较小。
- 案例研究（§5.3, Appendix G）：在发布的真实App（ESPN v8.6.0、Fox News v5.17.2、Booking.com v62.1.2、Harbor Freight v2.5.1、Pinterest v13.46.1，均为2025年11-12月版本）上定性展示GUITester能检出的具体缺陷实例，但原文未报告这些案例研究的定量指标（检出率/误报率等），属于小规模定性验证。
- 新缺陷：论文在真实发布App上检测到的这些缺陷（ESPN、Fox News等）属于论文声称"新发现"的案例展示，但原文未说明是否已向厂商报告/确认/修复，仅作定性case study呈现。

## 局限

**论文承认的（原文§7 Limitations，详细分析见Appendix F）：**
1. **Wait-or-Miss Dilemma**：真实环境存在网络波动、服务器延迟等噪声，agent偶尔把6-7秒的慢加载页面误判为缺陷；简单延长等待时间会降低测试效率，且有些真实缺陷表现为毫秒级瞬时故障，延长等待反而会错过它们。
2. **Monitor能力边界**：Monitor准确检测缺陷依赖对"预期状态"的预测，但其领域知识和对应用行为的假设有限（例如不了解UFC是MMA的子类目，将正确跳转误判为导航逻辑错误；或错误假设视频页面应包含文章内容）。
3. **动作空间小、测试范围窄**：现有GUI agent的动作空间为自主导航设计，缺乏真实测试所需的更丰富交互（如原文举例：交易类App中用户常用的图表缩放手势，现有GUI agent均不支持）。
4. **缺陷覆盖范围窄**：本工作聚焦交互类缺陷（interactive defects），但GUI还可能以其他方式失效，如元素重叠、文字错位、标签截断（overlapping elements, misaligned text, truncated labels）；原文明确指出扩展覆盖此类布局问题将使质量保障更全面，并列为未来工作方向之一。

**我们的观察：**
- 原文§7明确将"overlapping elements, misaligned text, truncated labels"列为当前未覆盖、留给未来工作的缺陷类型，这直接说明GUITester当前方法不处理我们关注的显示类缺陷（文字截断/遮挡/重叠/溢出），两者问题定义不重叠。
- Appendix F中报告的两类误报（超时误判、Monitor领域知识边界导致误归因）说明HRM的归因准确性存在边界，这一局限对我们设计UX-Agent的候选复核/误报抑制机制有参考价值，但原文未给出误报率的具体数字，只有案例描述（原文未给出）。
- GUITestBench规模（26缺陷/143任务/12 app）相对较小，论文本身未讨论这一规模是否足以支撑"existing agents fail"这类较强结论的统计显著性（原文未给出统计检验）。

## 和我们课题的关系

### 与 UX testing 的关系

GUITester检测的缺陷类型（ONR操作无响应、UTR任务结果异常、NLE导航逻辑错误，以及被归为"UX缺陷"的交互流程设计缺陷如Booking.com键盘未自动收起、Pinterest选项菜单意外关闭）与我们UX-Agent当前聚焦的**显示类缺陷**（文字截断、遮挡、重叠、溢出）在问题定义上基本不重叠：论文的"UX defect"概念（引用Baltes and Dashuber 2024）指的是多组件交互流程/任务流的设计缺陷（如"保存文件后文件未出现在目录中"），而非视觉渲染层面的显示异常；原文§7 Limitations第4点明确承认"overlapping elements, misaligned text, truncated labels"（重叠、错位、文字截断）未被本工作覆盖，并列为future work方向——这恰恰说明GUITester不检测我们关心的UX缺陷类型，两者是互补而非竞争关系。

间接价值体现在三方面：(1) **主动探测设计思路可借鉴**：PEM中"Boundary Conditions"测试意图（主动输入边界值/特殊字符去触发潜在异常，如Fox News特殊字符搜索案例）与我们UX-Agent当前"主动滑动探测并还原"复核文字截断候选的思路在方法论层面相似——都是用主动操作去暴露/验证静态观察无法确认的异常，可以作为我们扩展探测策略（如主动触发不同分辨率/字体大小/旋转等边界条件以暴露隐藏的截断/溢出）的参考。(2) **归因解耦思路可借鉴**：HRM把"是否异常"和"归因于谁（agent错误 vs 真实缺陷）"分离的设计，与我们用ArkUI布局树复核截图候选（区分"截图看起来截断"是真实布局问题还是识别误判）在结构上类似，可供我们在候选复核环节的误报抑制逻辑参考。(3) **它不能解决**：论文完全没有涉及静态截图的显示缺陷识别（无文字截断检测oracle、无布局树分析），也未讨论ArkUI/鸿蒙平台，对我们直接复用的部分有限。

### 与 GUI testing 的关系

本文为GUI测试的**生成（generate）与执行（execute）环节**贡献了一个新范式：把"探索式测试"从人工monkey testing扩展为由多智能体agent主动完成，关键创新在于把"导航（追求任务完成）"和"验证（判断是否存在缺陷）"解耦为独立模块（PEM负责主动生成测试意图/探测路径，HRM负责oracle判定与归因）。对于oracle维度，本文提出的oracle机制是"Monitor预测预期状态+对比实际状态"（基于视觉观测的隐式oracle，而非预定义断言或spec），这为无预设测试用例场景下的oracle设计提供了一种可操作方案，但其oracle质量受限于Monitor对领域知识的掌握（原文Appendix F已承认存在假阳性）。在评测维度，本文贡献了GUITestBench这一新benchmark及其配套的规则匹配+LLM裁判评测方法，可作为探索式GUI测试agent能力评测的参照，但其规模（143任务/26缺陷）相对较小，尚不能视为充分性验证的标准基准。论文提出的"扩展动作空间以支持更丰富测试交互（如缩放手势）"属于原文列出的待核查future work方向，不是已验证的创新点。

## 原文摘要关键句（节选）

> "To address these, we first introduce GUITestBench, the first interactive benchmark for this task, featuring 143 tasks across 26 defects."
> — Abstract，所读版本（https://arxiv.org/html/2601.04500）

中文解释：这句限定了本文benchmark贡献的具体规模边界——GUITestBench是"首个"交互式探索缺陷发现基准，但规模仅为143个任务、26个缺陷，是小规模的概念验证性基准，而非大规模工业级benchmark，后续所有实验结论都建立在这一规模之上。

## 原文摘录

> "Goal-Oriented Masking, where agents prioritize task completion over reporting anomalies, and Execution-Bias Attribution, where system defects are misidentified as agent errors."
> — Abstract，所读版本。

> "This work focuses on interactive defects. However, GUIs can fail in other ways: overlapping elements, misaligned text, truncated labels. Expanding defect coverage to include such layout issues would enable more comprehensive quality assurance."
> — §7 Limitations，所读版本。

> "GUITester achieves an F1-score of 48.90% (Pass@3) on GUITestBench, outperforming state-of-the-art baselines (33.35%)."
> — Abstract，所读版本。

> "UI defects typically manifest as immediate visual anomalies that can be identified through single-frame analysis, while UX defects cannot be attributed to any specific operation and require the agent to comprehend the entire interaction sequence to identify defects."
> — §5.2.1 RQ1，所读版本。

## 所读版本与核对范围

所读来源为arXiv HTML版本 https://arxiv.org/html/2601.04500（2026年1月8日提交，v1）。实际读到全文正文（Abstract、§1-§6 Conclusion、§7 Limitations）及全部附录（Appendix A-G，包括Algorithm 1工作流、Table 1/2主实验表、Table 3/4 prompt设计、Fig.5-18所有案例图的文字描述）。已核对表1、表2的所有数字（Pass@1/Pass@3下各defect类型Recall/F1）与正文叙述一致。未对照正式会议/期刊版本（原文未给出venue信息，当前为preprint），未进行代码复现（原文提供GitHub链接但本次笔记未运行代码）。

## 书目与分类（记录用）

<details>
<summary>展开标题、作者、版本和标签</summary>

- title: GUITester: Enabling GUI Agents for Exploratory Defect Discovery
- authors: Yifei Gao, Jiang Wu, Xiaoyi Chen, Yifan Yang, Zhe Cui, Tianyi Ma, Jiaming Zhang, Jitao Sang
- year: 2026
- era: llm
- venue: 原文未给出（arXiv preprint）
- venue_type: preprint
- url: https://arxiv.org/abs/2601.04500
- pdf_url: https://arxiv.org/html/2601.04500
- version: v1 (2026-01-08)
- code_url: https://github.com/ADaM-BJTU/GUITestBench
- institution: Beijing Jiaotong University; Hithink Research; Nanyang Technological University
- aka: GUITester; GUITestBench
- door: gui
- question: execute, oracle
- contribution_type: benchmark, method
- platform: android
- method: multi-agent, llm-prompt
- oracle_type: llm-judge
- bug_type: functional, display（后者仅限交互流程层面的UX缺陷，不含视觉布局缺陷）
- benchmark: GUITestBench（本文构建，143任务/26缺陷/12应用）
- baselines: UI-TARS (7B/72B/1.5-7B), GUI-Owl (7B/32B), MAI-UI (8B), Mobile-Agent-V3
- headline_result: GUITester (UI-TARS-1.5-7B) 在GUITestBench上Pass@3整体F1=48.90%，优于最佳baseline UI-TARS-1.5-7B的33.35%
- one_liner: 提出多智能体框架GUITester，通过解耦导航与验证（主动测试意图探测+异常归因分离）解决GUI agent探索式缺陷发现中的掩蔽与误归因问题，并构建配套基准GUITestBench
- use_in_survey: 原文未给出（非综述）
- concepts: Goal-Oriented Masking, Execution-Bias Attribution, PEM, HRM, ONR/UTR/NLE, Pass@1/Pass@3
- priority: should
- read_depth: full
- owner: ZYY0321(AI辅助)
- status: extracted

</details>