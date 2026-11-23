# AgentHorizon：评测"自动判官"（LLM Judge）能否在跨应用、长时程的电脑操作轨迹上正确判断任务是否完成

## 开会速记

- 这是一篇**评测基准论文（benchmark）**：作者录制了166小时、三个操作系统上的真人桌面操作轨迹，构造"配对"任务（同一对指令互换轨迹即得负例），测试11个LLM判官（judge）能否判断一条看似完整的长轨迹是否真的满足指令。
- 证据强度：最强的"代理判官"（GPT-5.5 + Codex 工具框架）在最难子集 AH 上也只有 **80.9% 平衡准确率**；多数判官在"接受有效轨迹"与"拒绝貌合神离轨迹"之间表现割裂（如 Table 2 中 Pos/Neg 准确率差距很大）。
- 关键发现：给判官工具（agentic/带harness）**不是总能提升效果**——同一模型换个执行框架（harness）结果可能反向变化，且"Bad Side Effect"（完成了目标但带来副作用）这类错误的召回率全线最低。
- 和我们的关系是**间接但有价值**：论文不检测显示类缺陷，但它关于"长轨迹judge容易被表面完整性欺骗、需要主动检索关键证据"的发现，直接呼应 UX-Agent 里"截图候选→布局树/滑动复核"这种不能只信表面截图的设计思路；其判官评测方法论也可为我们评价候选复核模块的可靠性提供参照。
- 局限：论文只覆盖"近似但不匹配指令"这一类微妙错误，不建模循环、崩溃、漂移等常见agent失败；未做独立人工标注者间一致性检验；语料仅英文，只有截图+动作日志、无完整应用状态。

## 一页读懂

| 维度 | 内容 |
|---|---|
| 旧方法不够在哪 | 现有computer-use基准（WebArena、OSWorld等）靠人工脚本逐任务校验（URL、数据库记录、文件内容），对"有多种合法结果"的任务难以指定规则；用LLM做判官（如AgentRewardBench）只验证过网页agent，且其负例来自agent真实执行失败，没有专门研究判官在**长时程、跨多应用桌面任务**上是否会被"看起来完整但违反指令细节"的轨迹欺骗（原文 Sec 1, Sec 2）。 |
| 本文新增 | 一个基于"配对指令+人工录制轨迹+指令互换造负例"方法构造的基准 AgentHorizon，含三个disjoint子集（AH/AH-S/AH-D），并对11个judge模型在"直接判官"与"5种agent harness下的代理判官"两种设定下做评测（原文 Sec 1, Sec 3, Sec 4）。 |
| 输入/输出 | 输入：一条指令 + 一条轨迹（截图序列+桌面动作日志，最长达300步）；输出：success布尔值、confidence、mistake_type（失败时）、reasoning（原文 Sec 4, Appendix A.4 Figure 4）。 |
| 怎样验证 | 在AH（528项）、AH-S（683项）上用balanced accuracy、class-specific accuracy、mistake-type recall(MT%)评测11个judge×多种harness组合；另做消融（去掉instruction/screenshots/action log）验证各信息源的必要性（原文 Sec 3.4, Sec 4, Appendix B.4）。 |
| 结论边界 | 结论局限于"近似但不匹配指令"这一类微妙失败模式，不代表对agent常见失败（循环、崩溃、停滞、逐渐漂移）的判官能力评价；难度划分依赖于特定三模型splitter配置；未做独立人工标注者间一致性（inter-annotator agreement）；语料仅英语，覆盖112个桌面应用、三种操作系统（原文 Sec 5 "Limitations"）。 |

具体方向论文条目应在 [catalog](../catalog.md) 补一行同口径记录。

## 一段话介绍

论文研究的问题是：当computer-use agent完成一个跨多应用、上百步的桌面操作任务后，怎样自动判断这条轨迹是否真正满足了用户指令，而不是被"看起来顺利走完全程"的假象欺骗。作者的解法不是提出新的判官模型，而是先构造一个专门暴露这种"貌合神离"错误的基准：让人工标注者为每对相近指令各录一条真实桌面操作轨迹，指令与轨迹正常匹配给出正例，把指令和轨迹互换给出负例（负例轨迹本身执行连贯，只是和配给它的指令不符）。随后用这套基准测试11个LLM在两种使用方式下——直接把全部截图+动作喂给模型一次性判断，或作为"代理判官"在5种agent执行框架（harness）里用工具主动检索轨迹——的判断准确率，并辅以消融实验看哪些信息对判断必要。证据是：最好的代理判官（GPT-5.5+Codex）在最难子集上平衡准确率为80.9%，工具访问并不总能提高准确率，且所有判官对"目标达成但带来副作用"这类错误的识别召回率都明显偏低。

## 关键术语与阅读前提

- **Trajectory（轨迹）**：一次人工或agent在桌面上完成任务的截图+动作序列记录，是本文judge的判断对象。
- **Direct judge（直接判官）**：把整条轨迹（截图+动作日志）一次性塞进一次chat-completion调用让模型打分，不借助工具（原文 Sec 4）。
- **Agentic judge（代理判官）**：把LLM装进一个agent harness（如Claude Code、Codex、Gemini CLI、OpenHands、OpenCode）里，让它通过工具调用主动打开/筛选截图和动作记录后再给出判决（原文 Sec 4, Appendix A.4）。
- **Agent harness（执行框架/脚手架）**：承载代理判官工具调用的外部运行环境，不同harness在截图选择、上下文管理、工具暴露方式上不同（原文 Sec 4）。
- **Paired construction / swapping（配对构造/互换）**：先构造两条closely related但requirement不同的指令A、B及其各自录制的轨迹，匹配组合为候选正例，互换组合为候选负例（原文 Sec 3.2, Figure 3）。
- **Mistake type（失败类型）**：Critical Mistake（核心目标未完成）、Bad Side Effect（目标完成但产生未请求的额外影响）、Misunderstanding（对参数/约束的合理但错误解读，无外部危害）（原文 Table 5）。
- **Balanced accuracy（平衡准确率）**：正例准确率与负例准确率的平均，全猜一类得50%（原文 Sec 3.4）。
- 相关术语可对照 ../glossary.md 中oracle/judge条目；本文属于判官（oracle）评测，非探索/生成方法论文。

## 动机

作者指出，现有computer-use基准（WebArena、VisualWebArena、WorkArena、OSWorld等）依赖脚本逐任务校验某个固定属性（最终URL、数据库记录、文件内容），这种方式确定性强、可重复，但当一个任务存在多种合法结果（比如电子表格记录顺序不同、logo设计不要求像素级匹配参考图）时就难以预先写出规则（原文 Sec 1）。替代方案是用LLM充当判官，但先前专门针对判官的工作（如AgentRewardBench）主要评测web agent轨迹，其失败样本来源于agent真实执行失败；本文关心的是桌面端长时程、跨多应用任务中，判官是否能定位"哪些细节才决定任务真的成功"——文中Figure 1给出一个具体例子：在一条115步的Inkscape–GIMP录制轨迹中，指令要求最终logo含三角形装饰，但执行过程中某一步画成了五角形，随后的重新上色、导出都正常进行，使整条轨迹表面上完整顺畴，只有逐步核实"形状是否按指令绘制"才能发现这个偏差（原文 Sec 1, Figure 1）。

## 贡献

原文摘要与引言中明确给出的贡献（按作者表述归纳）：

1. **（benchmark）** 提出AgentHorizon：由1,373个指令–轨迹对组成的基准，取自166小时、覆盖Windows/Linux/macOS三系统的人工录制轨迹，用"配对指令+互换构造负例"的方式天然得到难以区分的近似失败样本（原文 Abstract, Sec 3）。
2. **（benchmark设计）** 把数据划分为三个不相交子集：AgentHorizon(AH，最难，用于测试前沿judge)、AgentHorizon-Simple(AH-S，较简单)、AgentHorizon-Development(AH-D，专留给判官调优/训练，不参与主评测)，并给出可复现的难度划分流程（用三个强开源模型集成+阈值18/24判对）（原文 Sec 3.3, Appendix A.3）。
3. **（empirical）** 在直接判官与5种agent harness代理判官两套设定下，评测11个LLM judge模型，量化tool-use对不同模型的异质影响、不同harness对同一模型的影响、以及各类mistake type的识别召回率差异（原文 Sec 4, Table 2, Table 7, Table 8）。
4. **（empirical/消融）** 通过去除instruction、screenshots、action log的消融实验，证明单靠轨迹本身（无指令）无法判断成功与否，截图信息对判断质量有重要贡献（原文 Appendix B.4, Table 9）。

需要注意：本文没有提出新的judge模型或训练方法，贡献类型集中在benchmark与empirical，不构成method类创新。

## 方法

整体上本文的"方法"是指基准构造流程 + 判官评测协议，而非agent测试方法本身，下面按模板五点改写：

1. **输入表示**：每个基准条目由一条自然语言指令 + 一条人工录制的轨迹组成，轨迹表示为逐步截图（原始录制，评测时direct judge会降采样至512×332像素，部分开源模型将4帧合并为2×2拼图以控制上下文）加结构化的动作记录（点击、文本输入、滚动、应用切换等）（原文 Sec 3.1, Appendix B.1）。不涉及源码或控件树，只有截图与动作日志（原文 Sec 5 "Limitations"明确指出这是局限）。
2. **判官如何处理输入**：direct judge在一次chat-completion调用里接收完整的（降采样）截图+动作序列，一次性输出判决；agentic judge被部署进一个agent harness（Claude Code / Codex / Gemini CLI / OpenHands / OpenCode），模型按照固定prompt（Appendix A.4, Figure 4）先从磁盘读取轨迹的markdown描述和JSON结构化记录，再按需调用工具打开具体步骤的截图文件，自主决定检索哪些证据。
3. **动作选择与执行者**：代理判官的"动作"是工具调用（读取某个trajectory markdown/json文件、打开某张截图），由各自的agent harness执行并把结果返回给模型，模型可反复调用工具直至形成判决，没有与真实GUI环境的交互（研究对象是录制好的轨迹，而非实时执行）。
4. **判定依据**：输出为JSON格式的success布尔值、reasoning（引用是core objective / parameters / constraints哪一层未满足）、confidence、mistake_type（失败时三选一）（原文 Appendix A.4, Figure 4的prompt模板）。真值（ground truth）来自标注团队的独立质量复核+证据复核+仲裁流程（Sec 3.2, Appendix A.1）。
5. **终止与产物**：模型给出一次性的JSON判决后即终止（无多轮迭代机制在评测协议层面体现）；最终产物是判决结果，与benchmark里的参考标签用balanced accuracy、class-specific accuracy、mistake-type recall等指标打分（Sec 3.4）。

**一个完整例子**（来自原文Figure 2）：任务7eb6defc类似场景外，Figure 2给出一个NetBeans+WordPress的195步轨迹，指令要求"用plugin-release-1.3.0.md一个文件生成WordPress发布文章"，但录制轨迹额外把changelog.md里的Added/Changed/Fixed内容也并入已发布的文章（第165步出现，第195步再次确认），真值标签为success=false、mistake_type=Bad Side Effect；而Claude Opus 4.7判官认为success=true、高置信度，其verbatim理由只核对了"类别与四个标签是否设置、是否预览发布"，没有发现这个未请求的额外合并（原文 Figure 2正文说明）。

## 核心技术 / 综述主题详解

本文属于方法论文结构中的"评测协议+基准设计"，下面展开各模块。

**配对构造机制**：标注者先写出两条closely related但在某个决定任务成败的要求上不同的指令A_instr、B_instr，各自独立录制轨迹A_traj、B_traj。匹配组合(A_instr,A_traj)/(B_instr,B_traj)作为候选正例，互换组合(A_instr,B_traj)/(B_instr,A_traj)作为候选负例（原文 Sec 3.2, Figure 3）。去除语义等价指令对后剩425对完整pair，对应850条录制、1,700个候选条目。

**审核流程**：候选正例先过质量复核，再过证据复核，仲裁后462个候选里保留135个，最终正例集合为523项（原文 Sec 3.2）。候选负例由vendor逐一核实录制是否确实不满足互换后的指令，覆盖全部850项，耗费212.5个contributor-hours，全部保留，构成最终1,373项评测集（523正、850负）（原文 Sec 3.2, Table 4）。

**失败类型taxonomy**：Critical Mistake（核心目标未达成，需重做）、Bad Side Effect（目标达成但产生成本/风险/暴露/清理负担，比如发错频道、多发布不该发布的内容）、Misunderstanding（对参数/约束理解有偏差但无外部伤害，局部修正即可恢复）（原文 Table 5, Appendix A.2给出具体判定边界与典型恢复方式）。

**难度划分**：用三个强开源模型（Qwen 3.5 122B-A10B、Inkling、Kimi K2.7 Code）各自作为agentic judge对每项产生8次判决（共24次），若一项中与参考标签一致的判决数≤18，归入更难的AH子集，否则归入AH-S（原文 Sec 3.3, Appendix A.3）。作者同时在Sec 5指出三个不同模型定义的难度划分之间排名相关系数ρ=0.963–0.975，说明该难度定义相对稳健（而非对单一splitter模型的过拟合）。

**评测指标**：balanced accuracy（正负例准确率平均）、class-specific accuracy（单独看正/负例准确率，用于区分"误拒有效轨迹"vs"误收不匹配轨迹"两种错误模式）、mistake-type recall（某失败类别中judge同时预测失败且类型正确的比例）、MT%（综合指标）、以及per-trajectory成本/运行时间（原文 Sec 3.4, Appendix B.1 Table 6）。

**消融用于支撑论点**：Table 9显示，去掉instruction后balanced accuracy接近随机（47.8%–49.8%），去掉screenshots只留末帧+动作日志则降至57.7%，用于支撑"判官必须同时看指令和充足视觉证据才能正确判断"这一核心论点（原文 Appendix B.4）。另外Discussion提到Qwen 3.6 27B在不给指令时把98.9%的匹配与互换轨迹都判为成功，直接证明"轨迹本身看起来都很完整，成功与否离不开指令"（原文 Sec 5）。

**交付前检验（自评）**：读者据此笔记可以说清楚——论文做了什么（构造配对基准+多judge/harness评测协议）、研究价值在哪（揭示长时程轨迹judge容易被表面完整性欺骗，尤其对Bad Side Effect类错误召回率低）、证据支持到哪（Table 2/7/8/9的具体数字，而非仅"做了基准"这类标签式描述）。

## 实验

**实验目的**：(1) 比较不同模型、不同使用方式（direct vs agentic）、不同harness在判断任务成功与否上的准确率差异；(2) 定位判官具体在哪类失败（Critical/Bad Side Effect/Misunderstanding）上表现差；(3) 验证指令、截图、动作日志各自对判断的必要性。

**数据**：评测集来自AgentHorizon基准（AH 528项：227正、301负；AH-S 683项：234正、449负；AH-D 162项不参与主评测），来源与真值构造见上文"方法"部分（原文 Table 1）。

**比较对象**：评测11个模型——6个闭源（Claude Opus 4.7、Claude Haiku 4.5、Gemini 3.1 Pro、Gemini 3.1 Flash Lite、GPT-5.4 mini、GPT-5.5）和5个开源权重模型（Qwen 3.6 27B、Qwen 3.6 35B-A3B、Qwen 3.5 9B、Gemma 4 31B、Gemma 4 26B-A4B），开源模型用vLLM在H100上自托管（原文 Sec 4）。代理判官使用Claude Code、Codex、Gemini CLI、OpenHands、OpenCode共5种harness，部分模型额外在多个harness上重复评测以做对照（原文 Sec 4, Appendix B.3）。

**环境/预算**：Appendix B.1 Table 6给出各主代理判官配置的平均input tokens、工具调用次数、图像数、每轨迹美元成本（例如GPT-5.5+Codex平均513,556 input tokens、18.6次工具调用、11.9张图像、每轨迹$0.4035；开源自托管行无边际API费用）。

**指标**：balanced accuracy（正负例准确率均值，百分比）；class-specific accuracy（正例/负例各自准确率，分母固定为该类总数，缺失/格式错误输出计为错误）；mistake-type recall（Table 7中分母为273个Critical Mistake、232个Bad Side Effect、339个Misunderstanding，统计判官同时判对失败且类型正确的比例）。

**主要结果（Table 2）**：
- 最佳代理判官：GPT-5.5 + Codex，AH平衡准确率80.9%（Pos 71.8% / Neg 90.0%），AH-S平衡准确率92.6%。
- 次之：Gemini 3.1 Pro + Gemini CLI 77.7%（Pos 65.6 / Neg 89.7），Claude Opus 4.7 + Claude Code 76.0%（Pos 76.7 / Neg 75.4）。
- 最佳开源代理判官：Qwen 3.6 27B + OpenCode 70.4%（Pos 75.3 / Neg 65.4）。
- 直接判官一侧：Qwen 3.6 27B（direct，2×2拼图预处理）达77.6%，比其OpenCode代理判官结果高7.2个百分点；而GPT-5.5 direct只有68.6%，远低于其Codex代理判官的80.9%——说明工具访问对不同模型效果相反（原文 Sec 4.1）。

**harness对比（Table 8，同prompt同输入条件下）**：GPT-5.5从Codex切到OpenCode，balanced accuracy下降3.7个百分点（80.9%→77.2%）；Qwen 3.6 27B从OpenCode切到Codex小幅提升1.2个百分点（70.4%→71.6%），切到OpenHands则大幅下降20.4个百分点（70.4%→51.2%）。Gemini 3.1 Flash Lite跨4种harness的balanced accuracy也有明显差异（46.1%–52.1%）。

**mistake-type recall（Table 7，全量基准上，denominators为273/232/339）**：Bad Side Effect类的recall在所有主代理判官配置上都远低于其他两类，例如GPT-5.5+Codex为Critical 77.7% / Bad Side Effect仅24.1% / Misunderstanding 72.9%；Gemma 4系列模型在Bad Side Effect上recall为0.0%。

**消融（Table 9，ablation study）**：去掉instruction（保留全部截图+动作日志）balanced accuracy为49.0%；去掉instruction且动作日志只留最终步，balanced accuracy 47.8%–49.1%，均接近随机（50%水平）；去掉screenshots但保留instruction+动作日志，balanced accuracy为57.7%，明显劣于保留截图的配置；两者都去掉则49.8%。结论是：指令缺失使任务"是否成功"本身无定义（两类轨迹看起来同样完整），截图提供判断所需的重要证据。

**新缺陷**：本文不是面向agent本身找新bug，而是面向judge模型的失败案例分析（Sec 4.2举了三个Claude Opus 4.7误判实例，均为"judge相对ground truth判错"而非"agent新发现的产品bug"），不涉及报告/确认/修复流程。

**原文数字一致性**：Table 3给出vendor汇报的总工时7.15小时/任务、总计6,077.5小时，原文特别注明"交付总工时超过最初1,960小时预估，因为校准引入了额外的复核轮次"（即作者自己标注了估算与实际的差异，未做"悄悄修正"）。

## 局限

**论文承认的（Sec 5 "Limitations"段）**：
- 配对设计只聚焦于"微妙的近似失败"（near-miss errors），不代表agent失败的完整分布（如循环、崩溃、停滞、逐渐漂移），"instruction-free controls不应被用来建模一般性agent失败"。
- 难度划分依赖所选的splitter模型配置、provider与模型版本，其他划分方式用于评估对单个splitter的稳健性，而非孤立的模型效应。
- AH-D虽排除了pair-aware的最终development set，但"早期试点暴露"限制了关于"完全未见过的评测数据"的说法。
- 未收集独立的人工标注者间一致性（inter-annotator agreement）；原始与复核标签之间的相关性只衡量复核阶段间的一致性，不代表独立标注者间的一致性。
- 语料仅限英语，覆盖有限的应用集合与三种操作系统；评测只提供截图和动作日志，而非完整的应用状态。
- Ethics statement另指出：该基准只评测agent是否遵从指令，不考虑安全层面（即是否执行的是本身危险的任务），高分不代表可以直接部署到生产环境。

**我们的观察**：
- 原文Table 7显示Bad Side Effect recall系统性偏低（多个模型甚至为0.0%），这与我们UX-Agent目前以"候选→复核"流程验证显示类缺陷的思路有相似风险：若复核模块（如布局树核查）只核对"主要目标是否达成"而不主动检查是否引入了额外的、未被要求的副作用（如遮挡/溢出发生在不相关区域），也可能被判官/复核逻辑忽略——但这是我们基于论文发现做的类推，论文本身未涉及UI显示缺陷场景，此处标注为推断而非原文结论。
- 论文方法论上对judge可靠性的评测很细（balanced accuracy+class-specific+mistake-type recall三层指标），这套评测分层思路可供我们在评价"截图候选→布局树复核"链路的误判类型（漏报 vs 误报 vs 分类错误）时参考，但论文未提供任何可直接复用的桌面UI显示缺陷检测方法或工具。

## 和我们课题的关系

### 与 UX testing 的关系

AgentHorizon不检测UI/UX显示缺陷（文字截断、遮挡、重叠、溢出等），其判官面对的是"指令是否被正确执行"这一功能/副作用层面的问题（Critical Mistake / Bad Side Effect / Misunderstanding），与我们UX-Agent关注的截图层面文字截断候选生成、ArkUI布局树复核、主动滑动探测这类显示问题在问题定义上是**不同维度**的（原文 Table 5的三类失败都与显示缺陷无关）。但论文提供两点间接价值：(1) 其核心发现——"看似完整/连贯的轨迹可能掩盖判断所需的关键细节，判官倾向于被表面一致性误导"（Figure 2的NetBeans+WordPress例子，Claude Opus 4.7因"整体逻辑连贯"而漏判Bad Side Effect）——可以类推提醒我们：UX-Agent用截图提出的文字截断候选也可能因为"截图整体看起来排版正常"而被下游复核环节误判为无缺陷，强调复核阶段不能只看表层一致性，需要像论文中agentic judge一样主动检索/验证具体证据（这与我们已有的"布局树复核+主动滑动探测"设计思路方向一致，论文可作为该设计必要性的间接佐证，而非直接证据来源，因为论文场景、指标、模型均不同）。(2) 论文Appendix B.4的消融实验（去掉instruction或screenshots后判断接近随机）提示：候选验证环节若缺少足够的上下文信息（如布局树结构、滑动后的页面状态），单靠静态截图可能不足以稳健判断，这对我们"截图候选 + 布局树复核 + 主动滑动还原"的多信息源设计提供了方法论上的类比支持，但不是该设计的直接实验证据。该论文不能解决我们任务中遮挡、重叠、溢出等显示缺陷的检测本身，也不提供任何可直接套用的显示缺陷oracle。

### 与 GUI testing 的关系

本文为GUI/computer-use agent测试链条中的**oracle评测（eval判官质量）**环节提供证据与方法论参考，不涉及测试生成、探索、执行、充分性或维护。具体地：(1) 它系统性地质疑了"用LLM作为自动oracle判断长轨迹任务成功与否"这一越来越常见做法的可靠性，给出量化证据（最佳判官balanced accuracy仅80.9%，且工具/harness选择对结果影响不稳定），这对任何打算用LLM-as-judge自动打分GUI/agent轨迹的评测流程（包括我们团队若用LLM复核UX-Agent候选）都是一个需要谨慎对待的警示性证据，而非已验证的改进方案。(2) 论文的"配对指令+互换轨迹"构造思路，为如何系统性地制造"貌似成功但实际违反约束"的负例提供了一个可借鉴的基准构造范式，若我们未来需要构造UX缺陷检测的负例/困难样本集，该方法论值得参考，但目前仅是待核查的问题假设，并非我们已验证的创新点。

## 原文摘要关键句（节选）

"A trajectory, composed of long sequences of screenshots and actions, may appear complete, but in reality violates constraints from the instruction or introduces an unwanted side effect."
— Abstract，所读版本 https://arxiv.org/html/2610.11050。

中文说明：这句话限定了本文研究的核心问题范围——不是agent执行失败（如崩溃、卡死），而是"表面完整但实际违反指令约束或带来副作用"的这一类微妙错误，这也是后续配对构造、三类mistake taxonomy设计的出发点。

## 原文摘录

> "By recording trajectories for closely related instructions, we can construct negative tasks by simply swapping the instructions. This paired design evaluates judges on their ability to distinguish a truly successful trajectory from one that completed a similar (but incompatible) request."
> — Abstract，所读版本 arxiv.org/html/2610.11050。

> "We find that our best agentic judge, GPT-5.5, achieves 80.9% balanced accuracy on the AH subset. We find that tool-use improves certain models but results in worse performance for open-weight models."
> — Abstract，所读版本同上。

> "An item is assigned to AgentHorizon (AH) if at most 18 of these verdicts agree with the reference label. Otherwise, it is assigned to AgentHorizon-Simple (AH-S)."
> — Sec 3.3，所读版本同上。

> "Even with the instruction provided, the Bad Side Effect failure type shows the lowest exact recall across all the primary judges on the full reviewed corpus."
> — Sec 5 Discussion，所读版本同上。

> "Our paired design analysis focuses specifically on subtle near-miss errors rather than the full distribution of agent failures (e.g., loops, crashes, stalls, and gradual drift)."
> — Sec 5 Limitations，所读版本同上。

## 所读版本与核对范围

所读版本为 https://arxiv.org/html/2610.11050（HTML全文版，v1，2026年10月8日提交，cs.AI分类）。本次通读覆盖正文Sec 1–6全部内容，以及Appendix A（基准构造细节、标注流程、mistake taxonomy、难度划分、prompt模板、数据集统计）与Appendix B（计算资源、mistake-type recall表、多harness对照表、消融表）。视觉核对了Table 1–9的关键数字（子集划分、主结果表、harness对照表、mistake-type recall表、消融结果表）以及Figure 1/2的文字说明。未对照正式出版版本（本论文为arXiv preprint），未做任何复现实验，所有数字均直接摘自原文正文与附录表格，未发现原文内部数字自相矛盾之处（Table 3中作者自己说明了总工时超预估的原因，已在"实验"部分注明）。

## 书目与分类（记录用）

<details>
<summary>展开标题、作者、版本和标签</summary>

- title: AgentHorizon: Evaluating Agentic Judges for Long-Horizon Computer-Use Tasks
- authors: Xing Han Lù, Dheeraj Vattikonda, Sina Hajimiri, Fatemeh Pesaran Zadeh, Parishad BehnamGhader, Ghazwa Darwiche, Amirhossein Kazemnejad, Christopher Pal, Alexandre Drouin, Siva Reddy
- year: 2026（arXiv提交时间标注为2026年10月8日，疑似未来日期/预印本时间戳，原文未做解释）
- era: llm
- venue: arXiv preprint
- venue_type: preprint
- url: https://arxiv.org/abs/2610.11050
- pdf_url: https://arxiv.org/html/2610.11050
- version: v1
- code_url: https://github.com/ServiceNow/agenthorizon
- institution: ServiceNow Research; McGill University; Mila – Quebec AI Institute; ÉTS Montréal; Seoul National University; Université Laval; Polytechnique Montréal
- aka: AgentHorizon
- door: gui
- question: eval
- contribution_type: benchmark
- platform: desktop
- method: hybrid
- oracle_type: llm-judge
- bug_type: functional
- benchmark: AgentHorizon (AH / AH-S / AH-D)
- baselines: 11个judge模型（6闭源：Claude Opus 4.7/Haiku 4.5、Gemini 3.1 Pro/Flash Lite、GPT-5.5/5.4 mini；5开源：Qwen 3.6 27B/35B-A3B、Qwen 3.5 9B、Gemma 4 31B/26B-A4B），5种agent harness（Claude Code、Codex、Gemini CLI、OpenHands、OpenCode）
- headline_result: 最佳代理判官GPT-5.5+Codex在AH子集上balanced accuracy为80.9%
- one_liner: 用配对指令+互换轨迹构造的长时程桌面任务基准，揭示LLM判官易被表面完整的轨迹误导，且工具/harness访问对准确率影响不稳定
- use_in_survey: 原文未给出（本文非综述）
- concepts: paired construction, swapping, agentic judge, direct judge, agent harness, mistake taxonomy (Critical Mistake/Bad Side Effect/Misunderstanding), balanced accuracy, mistake-type recall
- priority: should
- read_depth: full
- owner: ZYY0321(AI辅助)
- status: extracted

</details>