# MAI-Gym：面向移动与桌面环境的GUI智能体评测与在线RL训练统一平台

## 开会速记

- 这是一篇**基础设施/系统论文**，不是检测缺陷的方法论文：它把GUI智能体的"评测—数据收集—在线RL训练"三件事用同一条rollout路径和同一套agent harness统一起来，解决评测分数依赖harness实现、GUI环境扩展困难的问题。
- 核心新增两块：①可扩展执行基座（10个基准、最高2万并发环境实例、窗口化历史复用KV cache）；②自动化环境与任务合成（可复位的"仿造App"、跨App连贯世界、可执行验证的任务校验器）。
- 证据强度：训练出的MAI-Gym-9B在MobileWorld(78.4%)、OSWorld-Verified(76.2%)上达到10B以下开源GUI智能体SOTA，并有消融（联合RL vs 专家合并、任务规模扩增、算法对比）支持部分设计选择；最亮眼的是"仿造App训练→真实手机App迁移"实验（28.8%→48.1%，52个任务）。
- 和我们的关系是**间接的基础设施/训练范式参考**：论文做的是任务完成型智能体的RL训练环境，不检测显示缺陷（文字截断/遮挡/重叠/溢出），但其"仿造环境+可执行校验器"思路和GUI+CLI混合动作设计对我们的UX-Agent环境搭建、CUA训练经验（OpenMobile-2）有参考价值。
- 局限：论文自己承认"重复多轮诊断-合成循环"未被评测；克隆到真机的迁移差距（7.7→25.0个百分点）说明仿真环境与真实场景仍有gap，这点对我们用仿真/模拟环境做显示缺陷验证也是一个警示。

## 一页读懂

| 维度 | 内容 |
|---|---|
| 旧方法不够在哪 | 现有GUI gym分两类：基础设施型（如BrowserGym、WebGym、MobileGym、SCALECUA）只覆盖单一平台，开源训练代码的并行规模最多数百环境；数据型（CUA-Gym、Gym-Anything、GUI-Genesis、PhoneWorld）合成新App和任务但不发布训练代码或跑通现有基准的方式。评测和训练各自维护独立agent实现，容易"漂移"导致分数依赖harness而非模型本身（原文引用[Wu et al., 2026]）。 |
| 本文新增 | （1）跨移动/桌面/网页的统一rollout路径与agent harness，支持10个基准评测、在线RL训练，可并行2万环境实例；（2）自动化合成仿造App（真实App克隆+全新App）与跨App连贯世界，生成经执行校验的任务verifier；（3）失败驱动的任务合成（基于诊断报告定向生成任务）。 |
| 输入/输出 | 输入：可执行任务 x=(E, s0, g, V)（环境、初始状态、自然语言指令、校验器）；智能体观测为截图+命令行输出；输出为GUI动作（click/type/drag等）、CLI命令（shell）、以及终止动作(terminate)。 |
| 怎样验证 | 在10个基准（3移动+4计算机+3网页）上单命令评测；用GRPO在合成任务池上做在线RL训练出MAI-Gym-9B，在7个基准上对比开源/闭源基线；做了基础设施效率、联合训练vs专家合并、任务规模扩增、仿造App到真实App迁移、全新App学习、GRPO vs SAO算法对比等消融实验。 |
| 结论边界 | 结果仅在MAI-Gym自建的仿造环境/基准任务及作者选定的基线上得到；真实App迁移实验样本量小（52个任务/一个App12306），且作者自己指出克隆与真实App的差距在RL后反而从7.7pp扩大到25.0pp，说明迁移不完全；论文未评测"诊断-合成"循环多轮迭代的效果（原文明确声明"this paper does not yet evaluate repeated rounds"）。 |

具体方向论文条目请在 [catalog](../catalog.md) 中补充同口径一行（本工具当前环境无法直接写入，留待合作者同步）。

## 一段话介绍

这篇论文研究的问题是：如何把"可验证奖励的在线强化学习"这一在数学/代码领域已经成功的范式，规模化地用到移动/桌面/网页GUI智能体训练上。作者指出两个障碍——GUI环境本身难以并发扩展和维护一致，以及现实任务需要分布在多个App/文件中的连贯证据而非孤立样例数据。解决方案是搭建一个开源一体化平台MAI-Gym：用单一的rollout路径同时服务评测、数据收集、在线RL训练，保证三者看到的是同一个agent实现；并提供自动化的App与任务合成流水线，构造可复位的"仿造App"（真实App克隆+全新App）和跨App连贯世界，用"先定需求再写校验器、再做执行验证"的方式产出可信赖的任务verifier。证据评价方式是：用该平台训练出一个9B参数的统一移动+桌面智能体（MAI-Gym-9B），在7个公开基准上与多个开源/闭源基线对比任务成功率，并做了基础设施吞吐/效率、训练方案（联合训练vs专家合并、任务规模、算法）消融，以及一个"仿造App训练迁移到真实手机App"的小规模实测。

## 关键术语与阅读前提

- **可验证奖励的在线RL（Online RL with verifiable rewards）**：通过代码或规则自动判定任务是否完成来给奖励，而非依赖人工标注；本文把GUI任务也构造成这种可验证形式。参见 ../glossary.md 中RL相关条目（如有）。
- **Rollout**：智能体在一个任务实例中从初始状态到终止的一次完整尝试，产生轨迹τ和终端奖励r（原文2.3节）。
- **Harness（智能体外壳/脚手架）**：策略模型与环境之间的代码层，负责构建上下文、调用策略、解析输出、执行动作（原文2.2节）。
- **GRPO（Group Relative Policy Optimization）**：一种用组内归一化优势代替学习值函数的RL算法，本文训练主配方（引用Shao et al., 2024，公式3）。
- **Oracle/verifier（校验器）**：判定任务是否成功的机制，本文中既可以是读取应用/系统状态的代码，也可以是VLM judge（原文2.1节）。
- **Task OOD / Env OOD**：Task OOD指训练环境出现过但测试任务未在训练中出现；Env OOD指整个评测环境都未在训练中出现（原文4.1节定义）。
- **仿造App（mocked app）**：自包含、后端可复位的应用，分"真实App克隆"（如12306、建行App克隆）和"全新App"（未见过的全新界面）两类（原文3.4.1节）。
- 这些术语多为RL/GUI-agent训练领域通用概念，与我们UX-Agent更关注的"显示缺陷oracle"概念体系不完全重合，阅读时需注意本文的"成功判定"针对任务完成而非显示正确性。

## 动机

作者指出两个根本性挑战（原文Introduction第2段起）：

1. **GUI环境扩展与一致性难题**：与代码sandbox不同，一个GUI实例不能被并发尝试共享，因为智能体操作整屏并改变设备文件/设置；每次尝试需要独立的手机/电脑/浏览器实例并从已知初始状态开始，且在实例被重置前要做大量基于截图的模型调用。大规模训练需要同时运行数千个这样的实例。由于平台和基准各不相同，评测和训练往往各自维护独立的agent实现并逐渐"漂移"，导致测得的性能既取决于模型也取决于harness本身（原文引用[Wu et al., 2026]，Introduction第1段末）。
2. **现实任务的多样性与状态连贯性**：现实GUI工作流往往依赖分布在多个应用和文件中的信息（原文举例：回复一封邮件时需要附件发票里的总额，要求邮件、附件、发票内容在环境中一致存在）。但现有任务合成方法常依赖孤立输入文件或多任务共享的样例数据（Table 1），限制了生成任务的多样性与真实感。此外，涉及真实交易的应用对训练来说不安全或不现实，而评测对陌生界面的适应能力又需要全新的应用。

（教学例子，非论文案例）类比我们的场景：若要测试鸿蒙某办公App的"添加会议"功能是否正确读取了邮件中的日期信息，也需要邮件、日历、备忘录中的日期保持一致——这正是论文所说"跨App连贯世界"要解决的问题类型，但论文解决的是任务完成型RL训练数据问题，不是显示缺陷检测问题。

## 贡献

按作者原文四条列出（Introduction末尾"To sum up, our contributions are fourfold"）：

1. **统一可扩展的GUI智能体评测与在线RL平台**（贡献类型：harness/infrastructure）——统一移动/桌面/网页的评测、数据收集、在线RL训练，共享环境接口与agent harness，支持10个基准，验证可扩展到2万并行环境实例（Section 3）。
2. **面向可扩展GUI学习的自动化应用与任务合成**（贡献类型：method+benchmark构造流程）——自动合成可复位仿造App与基于连贯环境状态的跨App挑战任务，流水线构造相互关联的应用数据、生成经执行验证的任务校验器，并支持失败驱动的任务生成（Section 3.4）。
3. **10B参数以下最强的开源GUI智能体**（贡献类型：empirical/模型发布）——发布MAI-Gym-9B，统一移动与桌面的智能体，在MobileWorld上78.4%、OSWorld-Verified上76.2%，为10B以下开源GUI智能体中的新SOTA，优于UI-Venus-2-9B、SCALECUA-Qwen3.5-9B，甚至优于更大的GUI-Owl-1.5-32B（Section 4）。
4. **面向可复现GUI研究的开放资源**（贡献类型：开放资源）——发布框架（含评测harness与在线RL训练代码）、合成技能、49个仿造App及配套任务、2000个经执行测试校验器的任务（MobileWorld和OSWorld各1000个）、及模型权重。

需注意：贡献1、2属于harness/方法工程贡献，贡献3属于经验性（empirical）结果，不能把"有实现、做了实验"等同于"提出了新的oracle或新的缺陷类型"——本文没有涉及显示缺陷检测这一问题类型。

## 方法

整体设计思路：MAI-Gym把GUI智能体的"评测、数据收集、在线RL训练"三种工作负载都接到**同一条rollout路径**和**同一套agent harness**上，再在这条路径之上叠加**环境管理器**统一管理多平台环境，最后用**诊断→合成→再训练**的闸道式闭环来扩充任务池。下面按模板五个问题展开：

**1. 输入是什么、怎样表示？**
可执行任务定义为 x=(E, s0, g, V)（原文式1）：E是环境（Android设备/桌面VM/浏览器），s0是初始状态（应用记录、文件、账户、设置等，被视为任务的一部分：相同指令在不同s0下可有不同正确结果），g是自然语言指令，V是校验器。智能体的观测o_t是截图+命令行输出（原文Table 2），不是源码或控件树——论文没有使用控件树/布局树作为输入模态（原文未给出控件树相关内容）。

**2. 中间模块怎样处理，模型具体收到什么？**
在每一步t，harness基于指令、交互历史、当前观测o_t构建上下文c_t，调用策略模型得到输出y_t，解析成动作并执行（原文2.2节）。历史管理用"窗口化"策略（K=10步一窗，重叠O=2步）：窗口内新截图/文本只做追加，窗口边界处旧截图被替换为占位符但文字保留，这样prompt前缀只在每K-O步变化一次而非每步变化，从而让推理引擎可复用KV cache（Section 3.2，Figure 3a）。

**3. 动作怎样选择、由谁执行、失败如何反馈？**
动作空间混合GUI动作（click、double_click、long_press、type、hotkey、open、drag、system_button、wait）和CLI动作（cli_command执行shell命令）、API调用(api_call)、交互控制动作（ask_user、terminate）（Appendix A.3, Table 9）。一步可以是一批有序动作（GUI+CLI混合批处理）。命令执行失败时返回错误信息作为反馈，而不是直接结束episode（原文2.2节）。动作由policy采样y_t∼π_θ(·|c_t)产生，由rollout worker通过环境管理器的step(h,a)操作实际执行（Appendix A.2, Table 8）。

**4. 判定依据来自哪里、哪些观察能支持判断？**
校验器V检查最终状态s_T，有时也检查轨迹τ，用二值准则b_j(s_T,τ)∈{0,1}及权重w_j计算：reward r=Σw_jb_j/Σw_j（部分分），success S=Π_{j∈C} b_j（要求集合C中所有准则都满足）（原文式2）。准则的判定可以来自读取应用/系统状态的代码，也可以来自VLM judge（原文2.1节，MAI-Gym两者都支持）。任务合成时还引入"黄金代码（golden code，直接把环境设为完成态）"与"校验器代码"独立生成、再做reward audit比对，并在初始-完成-重置三态上执行验证（verifier必须在初始态得0、黄金代码执行后得1、重置后再得0），此外让多个模型实际通过智能体接口尝试任务、人工复核轨迹的可执行性、难度、指令清晰度和reward-hacking风险（Section 3.4.3，Figure 5b-c）。

**5. 何时停止，最终产物是什么？**
单次rollout在terminate动作或达到步数上限时结束（原文2.3节）。RL训练目标是在任务池𝒳上最大化期望终端奖励J(θ)（原文式）；GRPO用组内归一化的优势A_i（原文式3），策略自适应任务采样（policy-adaptive task sampling）会根据任务历史成功率动态调整该任务被采样的尝试预算（成功率0~0.8之间的任务给满组8次，从未解决/已精通η=0.8以上的任务给4/2次小预算，Section 3.5）。最终产物是训练好的MAI-Gym-9B checkpoint，以及平台本身（框架代码、合成技能、49个仿造App、2000个任务、模型权重）。

**完整流程串联示例（来源：原文Figure 1和Section 3整体叙述）**：诊断模块（agent-driven diagnosis，用Claude Code/Codex分析失败轨迹）发现模型在某类任务上弱→任务生成器参考诊断报告，结合跨App世界构造出针对性新任务→经"需求先行、双路独立生成golden code与verifier、执行验证"流水线确认任务可靠→新任务进入任务池，供下一轮在线RL训练使用→重新评测，形成评测-诊断-合成-再训练闭环（Figure 1底部），但论文明确说明本文未评测该闭环的多轮迭代效果。

## 核心技术 / 综述主题详解

本文是方法/系统论文，核心技术模块按原文组织如下：

**(a) 系统架构（Section 3.1）**：两个设计选择——①所有工作负载（评测/数据收集/RL训练）共享一条rollout路径和一套harness，避免"同一模型在不同harness下分数不同"的漂移问题（原文举例：训练副本保留最近5张截图、评测副本保留10张，就会评测出一个与训练时不同的智能体）；②智能体只通过环境管理器（暴露5个操作：request instances/observe/reset/step/evaluate）接触环境，环境适配器负责把这些操作翻译成各环境的原生API，部署后端负责在Kubernetes/Docker或已有设备上托管实例。消融证据：原文表5（环境效率表）、表6（窗口化vs逐步历史对比，训练更新时间从2166.4秒降到810.9秒）支持这一架构设计主张。

**(b) 规模化可靠执行（Section 3.2）**：三个具体技术点——①可靠的任务重置（移动端用ReDroid让每台手机作为普通容器直接跑在host kernel上，避免嵌套虚拟化；每次重置恢复/data快照；重置耗时中位数：Android 165秒、桌面VM 37秒、浏览器6秒，见原文4.3.1节Table 5）；②快速规模化配置（异步配置、warm pool预热、截图通过对象存储传输而非控制消息，实测2万并行实例、1000个新实例在移动端328.4秒/桌面端88.9秒就位）；③高效多轮推理（窗口化历史复用KV cache，详见上文方法部分）。

**(c) 评测与诊断（Section 3.3）**：一条命令跑完10个基准（Table 3列出了具体的benchmark、任务数、最大步数、指标），report pass@n和pass^n；dashboard能把分数精确定位到每个任务/每次尝试/每一步截图（回答"舰队是否健康""哪些任务解释了分数""某次尝试在哪里出错"三个问题）；"agent-driven diagnosis"把失败轨迹分析工作交给Claude Code/Codex等coding agent，在动作级、轨迹级、知识需求级三个层面对比成功/失败尝试，产出报告驱动后续任务合成。

**(d) 环境与任务合成（Section 3.4）**：
- *环境合成*：仿造App分真实App克隆（7个，涵盖12306、建行、滴滴、美团、点评、抖音、小红书，由coding agent照搬真实App主流程、搭建可复位后端，人工测试员对比克隆与真实App的界面截图核验，Appendix A.7.1）和全新App（42个，HTML5模板，确定性状态机，无真实参照，用于研究适应陌生界面的能力，共840个任务3196个检查点，Appendix A.7.2）。
- *跨App世界构造*：先定义persona（用户身份角色目标）和scenario（时间线、事件、约束），再生成共享人物/事件/事实的互联文件和应用记录（如项目简报、预算表、邮件线程、日历条目描述同一个项目的不同部分），任务指令基于该世界的证据生成（而非孤立导航指令），Figure 5a给出流程图。
- *任务与校验器合成*：详见上文方法第4点，核心主张是"先定需求、再独立生成golden code与verifier代码、最后执行三态验证"以降低reward hacking风险（Section 3.4.3）。

**(e) 在线RL训练（Section 3.5）**：训练后端基于slime（Megatron-LM训练+SGLang生成），支持GRPO/DAPO/GSPO/REINFORCE++/SAO/PPO多种算法，主配方用GRPO。三项针对GUI轨迹特性的具体设计：策略自适应任务采样（上文已述）、窗口化打包训练（每个历史窗口变成一条因果训练序列，只对窗口内新步骤算loss，避免重复编码同一截图）、训练-rollout一致性检查（比较trainer和rollout的log-probability，用k3估计量监控KL divergence，捕捉多模态处理错位等故障）。

交付前检验自评：合作者据此笔记可以说清楚——论文做的是GUI智能体RL训练基础设施+任务/环境自动合成，不是显示缺陷检测方法；其证据支持"平台可扩展到2万并行实例"和"用该平台训练出的9B模型在部分基准上达到同尺寸SOTA"，但"克隆训练迁移到真实App"的证据样本量很小（52个任务）且作者自己指出迁移不完全。

## 实验

**4.1 实验设置（训练MAI-Gym-9B）**
- 从Qwen3.5-9B出发，两阶段：①SFT warm-up（覆盖移动和桌面的混合GUI+CLI指令数据，原文未给出具体样本量）；②RL阶段：在合成的5000个任务（混合MobileWorld和OSWorld环境）上用GRPO联合训练移动和桌面，奖励仅来自代码校验器，用策略自适应任务采样+K=10,O=2窗口化历史。训练用512个GPU、峰值2万并发环境，训练约96小时（原文4.1节）。
- 评测7个基准：MobileWorld、AndroidWorld、MobileGym（移动，3个）；OSWorld-Verified、OSWorld 2.0、MacAgentBench、MyPCBench（计算机，4个）。其中MobileWorld和OSWorld-Verified是Task OOD（环境在训练中出现但任务未出现），其余5个是Env OOD（整个环境在训练中未出现过）。
- 指标：各基准用自己的原生指标（Table 3列出，如成功率/部分分），汇总时用未加权平均（Mobile Avg、Computer Avg、Cross Avg、Task-OOD Avg、Env-OOD Avg）。
- 基线分三组：前沿闭源模型（Claude Opus 4.8、GPT-5.5、Qwen3.8-Max）及开源Qwen3.8-27B；GUI agent模型（GUI-Owl-1.5-8B/32B、UI-Venus-2-9B、SCALECUA-Qwen3.5-9B、EvoCUA-1.5-32B、CUA-GYM两个规格、Qwen-CUA）；基座模型Qwen3.5-9B（衡量整套训练方案的增益）。基线中8项结果是作者自己跑的（Qwen3.8-Max在MacAgentBench/MyPCBench上，Qwen3.8-27B和Qwen3.5-9B在MacAgentBench上，两个GUI-Owl尺寸在MyPCBench和OSWorld 2.0上），其余来自已发表报告/排行榜。

**4.2 主结果（Table 4）**
- Task OOD：MobileWorld 78.4%、OSWorld-Verified 76.2%，是同尺寸开源GUI agent中最高分，比UI-Venus-2-9B高3.2和5.4个百分点，比GUI-Owl-1.5-8B高40.2和23.3个百分点；也超过更大的GUI-Owl-1.5-32B、EvoCUA-1.5-32B、CUA-GYM-35B-A3B/397B-A17B（OSWorld-Verified上）；在MobileWorld上超过Claude Opus 4.8(69.2%)、GPT-5.5(62.4%)、Qwen3.8-Max(77.8%)。
- Env OOD：AndroidWorld 75.9%、MobileGym 46.5%（partial score）；OSWorld 2.0为3.7/11.3（binary/partial）、MacAgentBench 41.3%、MyPCBench 15.2%，均领先同尺寸开源模型。
- SFT warm-up vs 联合RL增益拆解（Figure 6）：SFT warm-up把Task-OOD Avg从29.9提升到66.4，Env-OOD Avg从18.8提升到32.3，提供了大部分提升；联合RL进一步把Cross Avg从44.1提升到50.5（Mobile Avg+8.7pp，Computer Avg+4.2pp），两个Task OOD基准各+14.1和+7.8pp，Env-OOD Avg+4.2pp，且RL在全部5个Env OOD基准上都有提升——支持"联合训练在两个领域都有正向迁移"而非顾此失彼。

**4.3 分析实验**
- 基础设施效率（4.3.1，Table 5/6）：1000个环境就位时间移动端328.4秒（估计比串行KVM方式快≥6×）、桌面端88.9秒、浏览器94.2秒；未计分的中断（unscored aborts）比例1.2%-1.9%；窗口化历史相比逐步历史，prefix cache命中率从42.5%升到85.9%（+102.1%），每轨迹训练输入token数从566375降到86855（-84.7%），训练更新时间从2166.4秒降到810.9秒（-62.6%），但rollout步/秒从2.3降到1.9（-18.9%）——是效率权衡而非全面占优。
- 联合RL vs 专家合并（4.3.2，Table 7）：联合RL达78.4%(MobileWorld)/76.2%(OSWorld-Verified)，优于最佳合并配置（50/50合并76.4%在MobileWorld，30/70合并74.8%在OSWorld-Verified），且没有单一合并权重能在两个领域都领先。
- 任务规模扩增（4.3.3，Figure 8）：训练任务从500扩到5000，MobileWorld成功率69.2%→78.4%，OSWorld-Verified 69.7%→76.2%，rollout预算保持不变，说明更多样化的合成任务带来泛化提升。
- 克隆到真实App迁移（4.3.4，Figure 9）：12306场景52个配对任务，克隆内成功率36.5%→73.1%，真实App（物理手机）成功率28.8%→48.1%（增益19.2pp）；但克隆-真实的差距从训练前7.7pp扩大到训练后25.0pp，作者明确指出"迁移不完全，克隆增益不能完全预测真实App表现"。
- 全新App学习（4.3.5）：训练252个任务，在62个留出任务上单次尝试、60步预算评测，RL把成功率从25.8%提升到45.2%，耗尽步数预算的尝试从27次降到5次，平均轨迹步数从33.3降到16.4——RL仅用verifier奖励，无该App的示范数据。
- GRPO vs SAO（4.3.6，Figure 10）：两者早期任务成功率相近，SAO在展示区间末端略低于GRPO；SAO降低了采样等待时间，但额外的critic计算（每次actor更新对应两次critic更新）抵消了这一优势，作者得出"在测试配置下SAO相比GRPO没有明显的总训练时间优势"。

**新缺陷/bug报告**：本文不是缺陷检测论文，没有"报告/确认/修复"意义上的bug记录；其"成功率"衡量的是任务完成正确性，不是显示缺陷的发现（原文未给出相关bug统计）。

## 局限

**论文承认的**：
- Section 3.3明确说明"MAI-Gym支持重复运行诊断-合成-再训练这一循环；本文尚未评测重复多轮的效果"（"this paper does not yet evaluate repeated rounds"）。
- Section 4.3.4明确指出克隆到真实App的迁移不完全："Transfer remains incomplete: the clone–real gap widens from 7.7 to 25.0 percentage points, so clone gains do not fully predict real-app performance."

**我们的观察**：
- 论文的校验器既支持代码判定也支持VLM judge（原文2.1节），但主要实验奖励"仅来自代码校验器"（4.1节："with rewards from their code verifiers only"），VLM judge路径在实证部分未见展开评测，原文未给出其判定准确率或误报率的量化数据。
- 窗口化历史设计在效率上是权衡取舍（cache命中率提升但rollout吞吐略降），论文没有报告这一取舍对最终任务成功率的独立消融（即窗口化历史本身对最终success rate的影响，与算法/任务规模等因素解耦开），原文未给出。
- 真实App迁移实验仅覆盖1个App（12306）、52个任务，样本规模较小，作者自己也未声称该结果可推广到其余6个真实App克隆（CCB、滴滴、美团、点评、抖音、小红书），原文未给出其余克隆的迁移实验结果。

## 和我们课题的关系

### 与 UX testing 的关系

MAI-Gym本身**不检测UX/显示缺陷**：其校验器V判定的是"任务是否被正确完成"（文件内容、应用状态、计算值是否符合要求），不涉及文字截断、遮挡、重叠、溢出这类纯视觉呈现问题的判定逻辑。但对我们的UX-Agent有以下间接价值：

1. **环境/候选生成侧**：论文"仿造App+跨App连贯世界"的构造思路（先定persona/scenario再生成互联文件和应用记录，Section 3.4.2）与我们"截图提出文字截断候选→ArkUI布局树复核→主动滑动探测"流程中"主动探测环境以暴露更多页面状态"的目标有相似精神——都是为了系统性地构造出能触发目标问题的状态，而非依赖零散样例。但论文解决的是任务完成型RL的数据稀缺问题，我们面对的是显示缺陷的候选发现与复核问题，两者的"目标状态"定义完全不同（论文是"达成某个最终状态"，我们是"某个UI元素呈现异常"）。
2. **动作空间与执行侧**：论文的GUI+CLI混合动作空间（Table 9：click/type/drag + cli_command + api_call + terminate）与我们CUA训练经验里OpenMobile-2的"GUI+MCP混合动作"设计思路一致——都是让智能体能用非GUI通道（命令行/MCP工具调用）更高效地完成部分子任务。这对我们后续若要扩展UX-Agent的"主动滑动探测"为更通用的"主动探索能力"（例如结合ArkUI相关工具接口而非纯触屏操作）有工程参考价值，但论文没有专门讨论过显示类问题的探测策略。
3. **不能解决的问题**：论文的verifier机制（代码读取应用/系统状态、VLM judge）是为任务级功能正确性设计的，没有涉及如何定义"截断/遮挡/重叠/溢出"的oracle，也没有涉及截图层面的视觉候选提出方法；这部分仍需我们自己的方法（文字截断候选提出+布局树复核）来解决，论文不能替代。

### 与 GUI testing 的关系

论文为GUI测试/自动化中的以下环节提供了可参考的系统设计（而非直接提出测试方法）：

- **探索/生成（generate/explore）**：任务合成流水线（世界构造→任务生成→verifier合成→执行验证）提供了一种"自动构造大量、多样、有连贯初始状态任务"的工程范式，可供我们思考如何自动化生成"触发显示缺陷的页面场景"这一类似问题（但论文面向功能任务而非显示缺陷）。
- **执行（execute）**：共享rollout路径+环境管理器的架构（统一5个操作：request/observe/reset/step/evaluate）为"评测环境与训练环境保持一致"提供了工程蓝图，这对我们若要把UX-Agent训练成RL智能体（而不仅是规则/流水线式检测）具有直接参考价值。
- **Oracle**：论文支持代码校验器和VLM judge两类oracle机制并存，这提示我们在UX-Agent的"ArkUI布局树复核"之外，也可以考虑用VLM judge做辅助判定，但论文没有给出两者在display类问题上的对比数据（这是论文范围之外、需要我们自己验证的假设，非论文已验证的结论）。
- **评测（eval）**：论文强调"harness漂移导致评测分数不等于模型真实能力"的问题（引用[Wu et al., 2026]），这对我们在报告UX-Agent检测效果时也是一个提醒——若候选提出、布局树复核、滑动探测三个模块的实现细节在"离线评测"和"在线使用"时不一致，也可能导致评测结果失真，值得在我们自己的实验设计中检查。
- 论文未涉及GUI测试的充分性（adequacy）或维护（maintain）问题，原文未给出相关内容。

## 原文摘要关键句（节选）

> "We introduce MAI-Gym, an open all-in-one platform that unifies GUI agent evaluation, data collection, and online RL training across mobile, computer, and web environments."
> — Abstract，所读版本（https://arxiv.org/html/2610.20939）正文开头。

这句话限定了论文的核心范围：它是一个**统一基础设施平台**，覆盖评测、数据收集、在线RL训练三种工作负载，跨移动/计算机/网页三类平台，而不是一个具体的缺陷检测算法或测试oracle设计。

## 原文摘录

> "Online reinforcement learning (RL) with verifiable rewards has driven rapid progress in mathematics, coding, and tool use... but scaling this success to GUI agents remains challenging due to the high cost of interactive environments and the scarcity of realistic training tasks."
> — Abstract，所读版本正文开头。

> "Bringing this success to GUI agents presents two fundamental challenges. First, GUI environments are expensive to scale and difficult to maintain consistently... Second, realistic GUI learning requires diverse tasks grounded in coherent and resettable environment states."
> — Sec 1 (Introduction)，所读版本正文。

> "The pipeline runs each verifier on a live instance through an initial–completed–reset sequence: the verifier must score 0 on the initial state, 1 after the golden code runs, and 0 again after reset."
> — Sec 3.4.3 (Task and Verifier Synthesis)，所读版本正文。

> "Transfer remains incomplete: the clone–real gap widens from 7.7 to 25.0 percentage points, so clone gains do not fully predict real-app performance."
> — Sec 4.3.4 (Clone Training Transfers to the Real App)，所读版本正文。

> "MAI-Gym supports running this loop repeatedly; this paper does not yet evaluate repeated rounds."
> — Sec 3.3 (Evaluation and Diagnostics)，所读版本正文。

## 所读版本与核对范围

所读版本：https://arxiv.org/html/2610.20939（HTML全文，arXiv:2610.20939v1 [cs.AI]，2026年10月14日）。实际阅读范围：正文Introduction至Conclusion（第1–6节）全部内容，附录A.1–A.7全部内容（dashboard说明、环境接口契约、动作空间、超参数、训练配置YAML结构、合成任务示例、仿造App说明），以及Related Work（第5节）和Contributions（第7节）。视觉核对了文字描述对应的关键表格数值：Table 1（gym对比表）、Table 3（基准列表）、Table 4（主结果）、Table 5/6（基础设施效率）、Table 7（联合RL vs专家合并）。未能对照正式发表版本（本论文在arXiv，未知是否有会议/期刊版本），未做任何复现实验，所有数字均来自原文文本，未做改写或修正。

## 书目与分类（记录用）

<details>
<summary>展开标题、作者、版本和标签</summary>

- title: MAI-Gym: An Open All-in-One Platform for GUI Agent Evaluation and RL Training across Mobile and Computer Environments
- authors: Panrong Tong, Quyu Kong, Pengxiang Li, Tianyu Xia, Hanzhang Zhou, Lei Wang, Chenglin Cai, Long Li, Long Chen, Jianan Zhang, Zhengwen Zeng, Xu Zhang, Gongjie Zhang, Yue Wang, Steven Hoi, et al.（Alibaba Token Hub, Alibaba Group / MAI-UI Team）
- year: 2026（arXiv提交标注为2026年10月14日，原文页眉另标注arXiv:2610.20939v1 [cs.AI] 14 Oct 2026，存在与arXiv编号惯例不一致之处，保留原文标注，不替作者修正）
- era: llm
- venue: arXiv preprint
- venue_type: preprint
- url: https://arxiv.org/abs/2610.20939
- pdf_url: https://arxiv.org/html/2610.20939
- version: v1
- code_url: https://github.com/Tongyi-MAI/MAI-Gym
- institution: Alibaba Group (Tongyi MAI-UI Team)
- aka: MAI-Gym
- door: gui
- question: generate, execute, eval
- contribution_type: harness, method, empirical
- platform: multi（android, desktop, web）
- method: rl, hybrid
- oracle_type: spec, llm-judge（代码校验器为主，兼容VLM judge）
- bug_type: 原文未给出（非缺陷检测论文，衡量任务成功率而非bug类型）
- benchmark: MobileWorld, AndroidWorld, MobileGym, OSWorld-Verified, OSWorld 2.0, MacAgentBench, MyPCBench, WebVoyager, OnlineMind2Web, WebArena（共10个，论文Table 3列出其中7个用于主实验）
- baselines: Claude Opus 4.8, GPT-5.5, Qwen3.8-Max, Qwen3.8-27B, GUI-Owl-1.5-8B/32B, UI-Venus-2-9B, SCALECUA-Qwen3.5-9B, Qwen-CUA, EvoCUA-1.5-32B, CUA-GYM-35B-A3B/397B-A17B, Qwen3.5-9B（基座）
- headline_result: MAI-Gym-9B在MobileWorld达78.4%、OSWorld-Verified达76.2%，为10B以下开源GUI智能体SOTA；仿造App训练迁移真实12306 App任务成功率从28.8%提升到48.1%
- one_liner: 开源一体化GUI智能体评测/RL训练平台，统一harness+自动化环境任务合成，训练出10B以下开源SOTA的MAI-Gym-9B
- use_in_survey: 可作为"GUI agent在线RL训练基础设施"类别的代表工作，对比BrowserGym/WebGym/MobileGym/SCALECUA等
- concepts: executable task, verifier, agent harness, rollout path, GRPO, window-wise history, mocked app, cross-app world, policy-adaptive task sampling
- priority: should
- read_depth: full
- owner: ZYY0321(AI辅助)
- status: extracted

</details>