# GUITestScape：面向探索式GUI测试的开放集（open-set）、过程感知评测基准与评测器

## 开会速记

- 这篇论文做了两件事：(1) 建了一个名为 GUITestScape 的基准，61 个真实 Android App、508 个预置缺陷，第一次把"显示缺陷"（渲染/布局异常）和"交互缺陷"放进同一个探索式 GUI 测试评测里；(2) 提出 GUIJudge，一个把"发现缺陷"拆成 Reach（到达）→Trigger（触发）→Detect（识别）三阶段分别打分的评测器，而不是像以往那样只看"最终是否报出了预设缺陷"这一个终局判断。
- 证据强度：GUIJudge 在人工标注子集（覆盖 91.57% 场景）上相对最强 baseline 评测器把 Detect 阶段 Recall 从 73.21% 提到 97.12%、F1 从 81.19% 提到 93.95%，消融显示"轨迹检索"和"分类型验证器"两个设计都显著有用；但基准化实验显示现有模型（通用模型+GUI专用agent模型）在 Detect 阶段都很弱，最好的 Seed-1.8 也只有 40.55% Recall，说明"触发后识别缺陷"是当前瓶颈，而把 GUIJudge 的验证器直接插进 agent 工作流（不重训）能把 UI-TARS-1.5-7B 的 Recall 从 7.48% 拉到 57.02%。
- 和我们的关系：论文的 Display Defect Verifier（逐状态截图判断内容渲染/布局异常）在问题设定上和我们 UX-Agent 的"截图提候选→布局树复核"思路同构，可以参考它的 prompt 设计、证据要求（evidence/location_hint）和过程分解（Reach/Trigger/Detect）来设计我们自己的候选验证与评测协议；它不直接提供检测算法或数据集给我们用，只是方法论/评测范式上的参照。
- 平台仅 Android，原文明确承认未覆盖 web/desktop/跨应用工作流，也不评测"测试设计"阶段（任务生成、边界条件设计），只评测"给定导航任务后"的执行阶段能力。

## 一页读懂

| 维度 | 内容 |
|---|---|
| 旧方法哪里不够 | 作者指出两个问题（§1）：①现有探索式GUI测试基准几乎只覆盖交互缺陷，忽略显示缺陷（渲染错误、元素缺失、布局错位）；②现有评测协议依赖预定义缺陷标注的"闭集"校验，且把整个测试过程压缩成单一终局判断，无法区分"没到达场景""到达但没触发""触发但没识别"这几种性质不同的失败模式。 |
| 本文新增什么 | GUITestScape：61个App、508个预置缺陷（显示+交互两类）的交互式基准，每个缺陷实例化为含可复位场景（resettable scenario）、状态级测试依据（state-level test basis）、多入口导航任务（multi-entry navigation tasks）的评测用例；GUIJudge：把缺陷发现拆成 Reach/Trigger/Detect 三个可独立诊断的能力维度，并用"轨迹检索器+缺陷类型专用验证器"的两阶段流水线实现开放集、过程感知评测。 |
| 输入/输出 | GUITestScape 输入：Android App + 导航任务 g；GUIJudge 输入：agent 的测试轨迹 τ、agent 的缺陷报告 ρ、导航任务 g、状态级测试依据 B；输出：(Reach, Trigger, Detect) 三个判定结果（Trigger 对显示缺陷记为 ⊥，不适用）。 |
| 怎样验证 | RQ1：GUIJudge 判断本身是否可靠（人工标注集，对比 GUITester 评测器、规则评测器、三个 LLM-as-Judge 模型，并做两项消融）；RQ2：用 GUIJudge 对8个通用/GUI专用模型做 Pass@1/Pass@3 基准测试；RQ3：把 GUIJudge 的验证器嵌入三个 agent 的工作流，看 Detect 性能变化。 |
| 结论边界 | 结论局限于：①移动端 Android（原文未覆盖 web/desktop/跨应用）；②只评测"执行阶段"（给定导航任务后到达/触发/识别），不评测"测试设计阶段"（任务生成、边界条件设计、探索策略规划）；③状态级测试依据的构建仍部分依赖人工（§Limitations）。 |

具体方向论文，已在 [catalog](../catalog.md) 补一行同口径记录（原文未给出具体表格内容，此处仅说明应补充，不代表已操作）。

## 一段话介绍

这篇论文研究的是"探索式GUI测试"（exploratory GUI testing）场景下如何更可靠地评测 MLLM agent 的测试能力：agent 没有预定义脚本，必须自己在App中导航并发现缺陷。作者认为现有评测存在两个缺口——只看交互类缺陷、忽视显示类缺陷；以及只做"最终是否报对了预标注缺陷"的闭集终局判断，无法区分不同失败原因。他们的解法是构建一个同时含显示和交互缺陷、带可复位场景与状态级测试依据的基准（GUITestScape），并设计一个把测试过程拆成 Reach/Trigger/Detect 三阶段、用"轨迹检索+分类型验证器"做判断的评测器（GUIJudge）。证据上，作者用人工标注子集验证 GUIJudge 本身的判断准确性（Recall/F1 显著超过几个 baseline 评测器），再用 GUIJudge 去跑多个现成模型，发现 Detect 阶段是普遍瓶颈，并通过把验证器插入 agent 流程（无需重训）证明这一瓶颈可被模块化缓解。

## 关键术语与阅读前提

- **Exploratory GUI testing（探索式GUI测试）**：agent 无预定义测试脚本，自主导航App并通过交互发现缺陷（§1）。参见 ../glossary.md 对应条目。
- **Display defect vs Interaction defect（显示缺陷 vs 交互缺陷）**：显示缺陷指渲染界面本身存在的视觉异常（无需交互即存在，如乱码、布局错位），分为 Content Rendering（CR，内容渲染异常，如乱码、图标破损）和 Element Layout（EL，空间布局异常，如重叠、对齐错误）；交互缺陷是动作与应用响应交互产生的异常，沿用 GUITester 的三类：Operation No Response（ONR，操作无响应）、Unexpected Task Result（UTR，任务结果与预期不符）、Navigation Logic Error（NLE，导航逻辑错误）（§3.1）。
- **Closed-set vs Open-set evaluation（闭集 vs 开放集评测）**：闭集评测只能对照预定义缺陷标注打分，无法扩展到未标注异常；开放集评测（GUIJudge 的目标）不依赖固定标注集，可对轨迹中实际出现的证据做判断（§1）。
- **Reach / Trigger / Detect（到达/触发/识别）**：GUIJudge 定义的三个独立可诊断能力维度：Reach——agent 是否正确理解任务并导航到缺陷暴露所需的前置状态；Trigger——agent 在到达相关上下文后是否执行了使缺陷暴露的交互（仅适用于交互缺陷）；Detect——agent 是否在缺陷暴露后识别出异常并正确报告（§4.1）。
- **State-level test basis（状态级测试依据）**：基于目标App业务逻辑给出的、描述"前置条件已满足的状态""缺陷已被触发的状态""异常证据可验证的状态"的规范，不强制唯一动作轨迹，只固定状态级检查点（§3.2.2）。
- **Resettable scenario（可复位场景）**：为保证跨次运行一致性，固定并在每次评测前恢复的App初始状态（含预置数据、系统设置）（§3.2.1）。
- **Multi-entry navigation task（多入口导航任务）**：针对同一缺陷从不同功能入口、不同引导程度构造的多条导航任务，用于检验agent测试能力是否能泛化到不同交互路径（§3.2.3）。
- **Trajectory Retriever（轨迹检索器）**：GUIJudge 流水线第一阶段，依据状态级测试依据定位轨迹中与缺陷相关的片段，并给出 Reach 判定（§4.2.1）。
- **Pass@1 / Pass@3**：常见的多次采样评测指标，原文未给出具体定义文字，但从表格看应为单次/三次采样取结果的评测协议（§5.3，Table 4、5）。

## 动机

作者在 §1 明确给出两个"现有方法遇到障碍"的论证：

1. **Display-defect blindness（显示缺陷盲区）**：现有基准（引用 Gao et al. 2026b 的 GUITestBench、Ahmed et al. 2026 的 SpecOps）"几乎只关注交互缺陷"，而显示缺陷（渲染错误、元素缺失、布局错位）"往往对用户体验有最直接的影响"，但检测它们需要开放式视觉异常检测能力，这是面向交互的评测从未考察的能力（§1）。
2. **Closed-set evaluation（闭集评测）的两个限制**：原文指出"现有协议依据预定义缺陷标注来校验agent报告"，第一，评测无法扩展到未标注的缺陷，因为标注集之外的任何异常都没有参照；第二，打分把整个测试过程压缩成单一终局判断，混淆了性质不同的失败模式——"agent可能从未到达缺陷场景，也可能到达却未能触发缺陷，又或者触发了异常却未能识别出来"，导致能力完全不同的agent被拉平到相近分数（§1）。

教学例子（非论文原文案例，用于帮助理解）：假设一个鸿蒙设置页面，某控件文字被截断——如果评测只问"agent最终是否报出了这个预标注的截断缺陷"，就无法区分"agent根本没滑到这个页面"和"滑到了页面但没注意到截断"这两种本质不同的失败原因；这正是本文想用 Reach/Trigger/Detect 拆分来解决的问题类型。

## 贡献

按作者在 §1 末尾列出的三条（原文编号为列表项，非显式序号1/2/3）：

- **贡献一（benchmark）**：提出 GUITestScape，一个覆盖61个真实Android应用、508个跨显示和交互类型预置缺陷的交互式基准。
- **贡献二（method/problem formulation）**：提出三阶段能力分解（Reaching, Triggering, Detection），将探索式GUI测试拆解为三个可独立诊断的维度。
- **贡献三（method）**：提出 GUIJudge，一个支持超越预定义缺陷标注的开放集、过程感知评测器。

贡献类型区分：贡献一属于 benchmark（具体数据+场景构建），贡献二属于方法论/问题分解（problem/method），贡献三属于 method（评测器实现）。原文未声称做了 empirical study 意义上独立的大规模实证调研，RQ2的"模型基准测试"更接近用自建benchmark做的一次评测性实验，而非独立的 empirical 贡献类别。

## 方法

整体思路：GUITestScape 先把真实缺陷"包装"成可控、可复位、可判定的评测用例；GUIJudge 再在这些用例上，先从agent完整轨迹里"捞出"与缺陷相关的片段，再用两个分类型验证器分别判断显示/交互证据是否成立，从而产出 Reach/Trigger/Detect 三个判定。

1. **输入是什么、怎样表示**：GUITestScape 的每个评测用例包含——目标App、可复位场景（defect-relevant初始条件，如预置数据和系统设置）、状态级测试依据 B（含 precondition 描述、trigger 判定标准、evidence 判定标准）、多条导航任务 g。GUIJudge 的输入是 agent 产生的完整测试轨迹 τ（截图+动作序列，附带 XML 摘要用于Display Verifier辅助判断）、agent 自己提交的缺陷报告 ρ、任务 g、测试依据 B（Algorithm 1, Appendix A.1）。
2. **中间模块怎样处理，模型具体收到什么**：
   - Trajectory Retriever：逐步扫描轨迹 τ，用 LLM 判断每一步是否匹配 B_precondition（Match函数，对应 Table 6 的 prompt，仅做"页面状态匹配"，不要求文本完全一致，只要核心UI结构/控件/内容基本一致即判 matched=true）；一旦匹配即标记 Reach=True，并继续向后搜索匹配 B_evidence 的步骤，若找到则记录该段子轨迹为 defect-relevant segment（Algorithm 1 行1-13）。
   - Display Defect Verifier：对每个检索到的片段中的每个状态（截图+XML）独立调用（对应 Table 7 的 prompt），输出 has_defect、defect type（DD.ContentRendering 或 DD.ElementLayout）、evidence（仅限截图中直接可见的事实）、location_hint。模型收到的是单张截图+XML摘要，不做跨状态推理。Trigger 对显示缺陷直接设为 ⊥（不适用）。
   - Interaction Defect Verifier：对每个片段，重置历史 H，按时间顺序遍历所有状态转移 (o_t, a_t, o_{t+1})，每加入一个转移后，模型收到 g（任务）、B（测试依据）、累积历史 H、当前转移 (o_t, a_t, o_{t+1})（对应 Table 8 的 prompt），判断该转移是否暴露 ID.OperationNoResponse / ID.NavigationLogicError / ID.UnexpectedTaskResult 三类之一。该 prompt 明确要求"只判断当前步骤""不要把agent自己的操作失误（如点错目标、hit=false）当作App缺陷"。
3. **动作怎样选择、由谁执行、失败如何反馈**：动作本身由被测试的 agent（如 UI-TARS、Seed-1.8 等）自主执行完成探索，GUIJudge 不参与动作选择，只是事后（或嵌入式）评测者。RQ3实验中，GUIJudge 的验证器被"集成进 agent 的工作流"（integrating into workflows），让 agent 保留原有导航能力的同时获得额外的缺陷识别支持（§5.1, §5.4），但原文未详细说明集成的具体接口机制（是事后还是实时注入），此处"怎样嵌入"原文未给出细节。
4. **判定依据来自哪里，哪些观察能支持bug报告**：Display Verifier 的判定依据是单张截图中"直接可见的事实"（evidence字段要求"only directly visible facts"）；Interaction Verifier 的判定依据是当前状态转移前后截图+任务目标+测试依据+累积交互历史的综合推理。两类验证器一旦判定 has_defect=true，再用 Consistent(ρ, r) 函数比较agent自己上报的缺陷描述与验证器判定结果是否一致，一致才标记 Detect=True（Algorithm 1 行18-22, 30-34）。
5. **何时停止，最终产物是什么**：轨迹检索在遍历完整条轨迹 τ 后停止（可能收集多个片段）；最终产物是三元组判定 (Reach, Trigger, Detect)，供下游 Recall/F1 指标计算使用（Algorithm 1 行35）。

一个完整例子（来自 Appendix C.3，论文原文案例）：任务要求agent在"任务"App中打开搜索框，输入"Exercise"，点击键盘搜索键。预期后置状态应为按关键词过滤后的列表，但实际后置状态与前置状态完全相同（仍是未过滤的完整列表）。因为agent的动作本身正确执行（hit=true），但界面未产生可观察效果，Interaction Verifier 将该转移分类为 ID.OperationNoResponse（§C.3）。

## 核心技术 / 综述主题详解

本篇是方法论文，核心技术是"三阶段能力分解 + 两阶段评测流水线"的设计，以下展开各模块设计及其与实验主张的对应关系。

**Reach/Trigger/Detect 的设计动机与字段**：作者在 §4.1 明确给出设计理由——"发现缺陷分三个阶段展开：agent必须先到达缺陷位置，然后通过交互触发缺陷，最后识别出异常结果。任何阶段的中断都会使这一进程停止，缺陷未被报告。"这一分解直接对应 §1 提出的"闭集终局评测混淆失败模式"问题，是论文的核心问题重构（reframing）。

**Trajectory Retriever 的必要性（对应消融实验）**：论文论证"探索性轨迹中缺陷相关时刻与大量无关导航交织，容易导致端到端判断中的证据稀释"（§4.2）。消融实验（Table 1，"w/o Retrieval"行）显示去掉检索器后，整体 Detect Recall 从 97.12% 降到 76.92%，F1 从 93.95% 降到 74.23%；作者进一步分析（§5.2）指出性能下降在 ONR 上最小、在 UTR 上最大，因为 ONR 通常由单一动作在相对固定条件下触发，证据易于定位，而 UTR 往往需要跨状态比较和延迟结果验证，证据更分散、更难定位——这一分析直接支持了"评测可靠性受限于证据定位质量"这一主张。

**分类型验证器的必要性（对应消融实验）**：论文论证显示和交互缺陷依赖根本不同形式的证据，因而设计两个独立验证器而非统一验证器。消融（Table 1，"w/o Typed Verifiers"行）显示用统一验证器替代分类型验证器后，整体 F1 从 93.95% 降到 87.05%，且跨缺陷类型的性能方差增大。作者归因于"显示缺陷通过界面状态中的视觉异常来评估，而交互缺陷通过动作结果与任务预期的一致性来评估"，这两种评估证据形式不同（§5.2）。

**与 LLM-as-Judge / 规则评测器 / GUITester 评测器的对比**：GUI-Tester 和规则评测器在显示缺陷上标记"–"（不支持该类型，Table 1），说明它们结构上无法处理显示缺陷；三个通用 LLM-as-Judge（Claude-4.6、GPT-5.4、Gemini-3.1-Flash）虽然能处理两类缺陷，但"跨缺陷类别表现不稳定"（§5.2），例如 Claude-4.6 在 EL 上 Recall 仅 14.67%，远低于其 CR 上的 66.67%（Table 1）。GUIJudge 在所有缺陷类型（CR/EL/NLE/ONR/UTR）的 Detect 阶段都取得最优或接近最优表现。

**显示/交互缺陷判断的 GUI 实例**（Appendix C，论文原文案例，用于说明机制如何落地）：
- EL 案例（C.1）：音乐App设置列表中"外观设置"和"本地音乐路径"两行图标明显大于其他行，破坏统一的图标尺寸/文字起始对齐，因异常在单一渲染状态内完全可见，Display Verifier 无需交互推理即可识别。
- CR 案例（C.2）：菜谱App设置弹窗中第三个选项渲染为一行乱码占位方块，表明字体/编码故障。
- NLE 案例（C.4）：社交图片App中，点击举报弹窗左上角"X"本应仅关闭弹窗并返回图钉详情页，实际却返回主界面，执行了完整导航重置而非弹窗关闭。
- UTR 案例（C.5）：股票资讯App中，将新闻页语言切换为中文后，语言指示标从EN变为ZH（提示设置已接受），但实际新闻标题、导航标签、正文内容仍完全为英文，后置状态与任务意图矛盾。

**交付前检验自评**：没读过原文的合作者可据此理解——论文做了"把评测过程拆成到达/触发/识别三段"这一核心设计，并用消融和跨baseline对比给出了具体数字支持（而非只是提出概念），证据支持到"GUIJudge本身判断可靠性"和"分类型验证器+检索器确有贡献"这两层，但对"是否能真正提升下游GUI测试agent的探索策略"仅在RQ3通过模块化插入验证器间接验证，未改进agent的导航/探索策略本身。

## 实验

实验组织为三个RQ，均基于人工标注集或GUITestScape全量场景。

**RQ1（GUIJudge本身是否可靠）**：
- 数据：人工标注的评测子集，覆盖 GUITestScape 中 91.57% 的缺陷场景（§5.1）。
- 对比对象：GUITester 的混合评测器、一个规则评测器、三个 LLM-as-Judge 模型（GPT-5.4、Claude-4.6-Sonnet、Gemini-3.1-Flash），以及两项消融（去掉轨迹检索器、去掉分类型验证器，仅替换为统一验证器）。
- 指标：Recall、F1，均按百分数（Recall 反映缺陷发现能力，F1 防止过度激进报告带来的虚高分）。
- 结果（Table 1）：GUIJudge 在 Reach 阶段 F1 为 97.87%，Trigger 阶段 F1 为 97.12%；Detect 阶段整体 Recall 为 97.12%、F1 为 93.95%，相对最强 baseline 评测器（Recall 73.21%、F1 81.19%）分别提升 +23.91 个百分点（Recall）和 +12.76 个百分点（F1）。
- 消融：去掉轨迹检索器后 Detect Recall 降至 76.92%、F1 降至 74.23%；去掉分类型验证器（统一验证器替代）后 F1 从 93.95% 降至 87.05%。
- 能支持的结论：GUIJudge 的判断相对已有评测方案更可靠，且检索器与分类型验证器两个设计模块都对性能有实质贡献。支持不了的结论：该结果不能说明 GUIJudge 的判断在所有未标注场景（真正开放集、无人工对照）下同样可靠，因为验证集本身仍是"人工标注"的91.57%子集，并非完全无参照的开放环境验证。

**RQ2（现有模型在GUITestScape上的表现）**：
- 数据：GUITestScape 全量508个预置缺陷/384个导航任务，模型以 Pass@1 和 Pass@3 两种采样协议评测（Table 2为Pass@1汇总，Table 4/5为Appendix中按故障模式细分的Pass@1/Pass@3结果）。
- 对比模型：通用模型（GPT-5.4、Gemini-3.1-Pro、Qwen-3-VL-Plus、Seed-1.8）与GUI专用agent模型（UI-TARS-1.5-7B、GUI-Owl-1.5-8B/32B、MAI-UI-8B）。
- 结果：Pass@1下整体最佳为 Seed-1.8，Detect阶段 Recall 40.55%、F1 51.05%（Table 2）；多数模型从Trigger到Detect阶段性能大幅下降，例如 UI-TARS 的F1从Trigger阶段72.45%（原文正文直接给出此数字，§5.3）降到Detect阶段28.08%。通用模型在Trigger→Detect的性能下降幅度明显小于agent模型（如Seed-1.8从89.18%降到64.33%，相比UI-TARS从72.45%降到28.08%）。
- 能支持的结论：当前模型（无论通用还是GUI专用agent）在"触发缺陷后识别缺陷"这一环节是主要瓶颈；GUI专用agent模型更擅长任务导向的到达/触发，但在异常识别上弱于通用模型。支持不了的结论：由于缺乏对"为何通用模型更擅长异常识别"的机制性实验（如可解释性分析），此处的"holistic interface understanding"解释是作者的推断（§5.3），并非经过独立验证的因果结论。
- 新缺陷：本实验未报告新发现、未知的真实App缺陷（即未做"报告/确认/修复"式的新bug实证），GUITestScape的508个缺陷均为预先从issue tracker/bug report收集的已知缺陷（§3.1）。

**RQ3（验证器集成是否能提升agent的测试能力）**：
- 设置：把 GUIJudge 的分类型验证器集成进 UI-TARS-1.5-7B、Seed-1.8、Gemini-3.1-Pro 三个agent的工作流中，不重新训练其导航策略（§5.1, §5.4）。
- 结果（Table 3）：UI-TARS-1.5-7B 整体Recall从7.48%升到57.02%（+49.54个百分点）、F1从11.66%升到69.07%（+57.41个百分点）；Gemini-3.1-Pro Recall升至61.27%（+24.85）、F1升至71.07%（+24.88）；Seed-1.8 Recall升至70.97%（+30.42）、F1升至79.48%（+28.43）。
- 能支持的结论：缺陷识别能力可以与导航能力解耦，通过模块化方式（插入验证器）在不重训的情况下显著提升；支持不了的结论：该实验未说明集成后的"端到端运行成本/延迟"变化，也未验证该验证器在GUITestScape之外App上的泛化能力。

## 局限

**论文承认的**（见原文"Limitations"章节，位于Conclusion之后）：
1. App专属测试依据的提取：GUITestScape相对闭集评测大幅降低构建成本，但可靠的缺陷判断仍需App专属的预期行为/界面结构标准，目前这些标准通过可复位场景和状态级测试依据提供，其构建"仍部分依赖人工"。
2. 测试设计能力的评测边界：GUITestScape评测的是探索式GUI测试的"执行阶段"（给定导航任务后能否到达、触发、识别缺陷），尚未评测上游的测试设计能力，如生成测试任务、设计边界条件、规划更广覆盖的探索策略。
3. 平台与工作流覆盖范围：当前仅聚焦移动端Android应用，虽覆盖显示和交互两类缺陷，但未覆盖web、desktop或更复杂的跨应用工作流，这些场景可能涉及不同的交互模式、环境依赖和缺陷表现形式。

**我们的观察**：
- 论文的"人工标注集覆盖91.57%场景"用于验证GUIJudge本身的可靠性，这本质上仍是对照人工真值的"闭集式"校验，作者并未在真正完全无标注的开放场景下独立验证GUIJudge的判断准确率，这与论文标题强调的"open-set evaluation"存在一定张力（基于§5.1描述，非作者原话，为我们的推断）。
- RQ2中"通用模型优于GUI专用agent模型"的解释（"holistic interface understanding" vs "任务意图跟随优化"）属于作者给出的定性归因（§5.3），原文未提供消融实验或可解释性分析支撑这一归因，建议谨慎引用为确定性结论。

## 和我们课题的关系

### 与 UX testing 的关系

我们的 UX-Agent 任务是在鸿蒙应用上做显示缺陷检测：从截图提出文字截断候选，再用 ArkUI 布局树复核，并通过主动滑动等操作探测与还原候选。本文的 Display Defect Verifier（§4.2.2, Table 7）在问题设定层面与我们高度相关——它同样是"仅凭单张截图（辅以XML摘要）做开放式视觉异常判断"，覆盖 Content Rendering（含"文字被遮挡、裁剪或截断导致不完整或不可读"，见 Table 7 prompt 原文列出的defect type描述）和 Element Layout（含重叠、错位、尺寸异常等）。这意味着：

- 论文给出的缺陷分类体系（CR/EL）和对应的prompt设计（要求evidence必须是"directly visible facts"、location_hint给出位置），可以作为我们候选验证环节提示词设计的参考基准，尤其是"仅凭可见证据判断、不臆测隐藏状态"这一约束与我们布局树复核的"证据优先"原则是一致的方向。
- 论文的 Reach/Trigger/Detect 分解主要针对需要"交互触发"的缺陷（尤其交互缺陷），而显示缺陷在该框架下 Trigger 被设为⊥（不适用），即显示缺陷被当作"无需触发、仅需到达该状态即可判断"的类型（Algorithm 1, §4.2.2）。这提示：我们当前的"主动滑动探测"环节，在GUIJudge框架下更接近于帮助"Reach"到可观察截断的状态，而非"Trigger"一个潜在的隐藏缺陷——这和我们任务里"滑动是为了让候选区域完全可见/还原真实状态"的定位是吻合的，但论文并未探讨遮挡、重叠、溢出等我们课题同样关注的其他显示缺陷子类型的专门处理逻辑，这部分内容原文未给出，需我们自行设计。
- 论文不提供可直接复用的检测算法或模型权重（仅给出prompt文本），也没有鸿蒙/ArkUI相关内容，因此对我们而言主要是评测范式和问题分解框架上的参照，而非可直接迁移的技术组件。GUITestScape的场景构建方法（resettable scenario + state-level test basis）也可能为我们后续做实验评价（例如构造可复位的鸿蒙测试场景、定义"候选是否真实为截断"的状态级判据）提供可借鉴的设计思路。

### 与 GUI testing 的关系

本文主要贡献在于 evaluation（oracle/eval）维度：

- 为 GUI 测试评测提供了一个新的**问题分解框架**（Reach/Trigger/Detect），把以往粗粒度的"缺陷检出 yes/no"终局评测，拆成可独立诊断的三段式评测，这对任何做探索式GUI测试agent开发/评测的工作都有参考价值。
- 提供了一个新的**基准构建方法论**：用"可复位场景+状态级测试依据+多入口导航任务"三要素组合把真实缺陷工程化为可重复评测的用例，这一方法论比具体508个缺陷实例更具迁移价值。
- GUIJudge 的分类型验证器本质上是一种**基于LLM的oracle**（oracle_type: llm-judge），其设计（仅凭直接可见证据判断、禁止臆测隐藏状态、将agent操作失误与app缺陷严格区分）对我们在构建或评价任何"LLM-as-judge"式判定器时都有直接参考价值。
- RQ3揭示"缺陷识别能力可以与导航能力解耦，通过模块化验证器注入提升"，这是一个**待核查的问题假设**（非我们已验证的创新点），它暗示在GUI测试agent设计上，"探索策略"和"异常判断"可以分离优化，这对我们后续是否要把候选验证模块设计为可插拔组件、独立于探索策略优化，提供了一个值得参考但尚未被我们自己验证的设计思路。

## 原文摘要关键句（节选）

"Existing benchmarks focus almost exclusively on interaction defects, leaving display defects outside the evaluation frame... evaluation protocols are bound to predefined defect annotations, collapsing the testing process into a single end-state judgment that conflates qualitatively distinct failure modes."
— Abstract，所读版本（HTML，无PDF页码）。

中文解释：这句话限定了本文要解决的问题范围——不是提出一个新的GUI测试执行方法，而是指出现有"评测"本身存在两个结构性缺口（缺陷类型覆盖不全、评测粒度过粗），因此本文的核心产出是基准和评测器，不是新的测试agent本身。

## 原文摘录

> "We identify two fundamental challenges: (1) Display-defect blindness... (2) Closed-set evaluation."
> — Sec 1，所读版本（HTML，无PDF页码）。

> "GUITestScape collects 508 preset defects from 61 real-world Android applications across 5 major categories. We consolidate these defects into 82 resettable scenarios, annotate each with state-level test basis, and expand them into 384 navigation tasks."
> — Sec 3.3，所读版本（HTML，无PDF页码）。

> "At the Detect dimension, GUIJudge improves overall Recall from 73.21% to 97.12% (+23.91%) and overall F1 from 81.19% to 93.95% (+12.76%) over the strongest baseline evaluator."
> — Sec 5.2，所读版本（HTML，无PDF页码）。

> "Removing trajectory retrieval reduces overall Detect Recall from 97.12% to 76.92%... This is because ONR defects are typically triggered by a single action under relatively fixed verification conditions, making their evidence straightforward to localize; UTR defects, by contrast, often require cross-state comparison and delayed outcome verification."
> — Sec 5.2，所读版本（HTML，无PDF页码）。

> "Integrating GUIJudge's verifiers into existing agents significantly boosts their detection performance without retraining."
> — Sec 5.4 / Abstract，所读版本（HTML，无PDF页码）。

## 所读版本与核对范围

所读版本为 arXiv HTML 全文页面（https://arxiv.org/html/2605.29532），该页面标注 "arXiv:2605.29532v1 [cs.SE] 28 May 2026"。本次阅读为 full：通读了正文 Abstract、§1 Introduction、§2 Related Works、§3 GUITestScape、§4 GUIJudge、§5 Experiments（含RQ1/RQ2/RQ3）、§6 Conclusion、Limitations，以及附录 Appendix A（GUIJudge workflow算法与三个prompt原文）、Appendix B（Pass@1/Pass@3补充表格Table 4、5）、Appendix C（五个案例C.1-C.5）。视觉核对了正文Table 1、2、3及附录Table 4、5中的关键数字。由于所读为HTML版本，不含PDF印刷页码，本笔记中的原文位置统一用章节号（Sec/Appendix编号）标注，未与正式出版版本或其他PDF版本对照，亦未做任何复现实验。图1-10为论文插图，原文未提供可引用的图内文字内容细节，笔记中仅转述图题说明。

## 书目与分类（记录用）

<details>
<summary>展开标题、作者、版本和标签</summary>

- title: GUITestScape: Towards Open-set Evaluation on Exploratory GUI Testing
- authors: Xiaoyi Chen, Yifei Gao, Yang Xu, Xingxing Song, Yi Zhang, Jitao Sang
- year: 2026（原文页眉标注日期为"28 May 2026"，具体以arXiv正式记录为准，原文未进一步说明）
- era: llm
- venue: arXiv preprint
- venue_type: preprint
- url: https://arxiv.org/html/2605.29532
- pdf_url: 原文未给出独立PDF链接（所读为HTML版本）
- version: v1
- code_url: 原文未给出
- institution: Beijing Ji