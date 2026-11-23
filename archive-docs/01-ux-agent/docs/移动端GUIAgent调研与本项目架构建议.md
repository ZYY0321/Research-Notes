# 移动端 GUI Agent 调研与本项目架构建议

## 1. 调研结论

移动端 GUI Agent 的核心不是把一张截图交给模型判断，而是让模型在设备环境中完成“理解目标、定位控件、执行动作、观察结果、修正计划”的闭环。现有研究和开源实现普遍把系统拆成规划或决策模型、设备动作执行器、屏幕观察、状态记忆和任务验证几个部分；不同项目的差别主要在于是否使用 UI 树、是否只看截图、是否增加反思/恢复，以及是否用轨迹数据做 grounding 或动作微调。

对本项目最重要的结论有三点。第一，页面导航和 UX 检测应是两个串联模块，导航失败不能直接进入 UX 统计。第二，探索采集与验收回放是两个阶段：探索用于生成页面知识、轨迹和缺陷标注，验收使用冻结指令复现目标页面。第三，当前仓库已有执行器、单 Agent 大脑、观察闭环和 UX 检测器，但缺少正式的目标页面 oracle、高低级指令数据契约、导航成功率统计和轨迹训练流程。

## 2. 代表性方法

### 2.1 AppAgent：探索后部署

AppAgent 将移动 Agent 分为 exploration phase 和 deployment phase。探索阶段通过自主浏览或观察人工示范，建立应用知识文档；部署阶段根据用户任务调用点击、滑动和输入动作。这个模式直接解释了本项目中“为什么要探索收数据”和“为什么验收还要根据指令到达页面”可以同时成立：探索产出知识和任务，验收回放任务并测成功率。AppAgent 官方页面说明其核心交互是简化动作空间，并使用探索或示范形成应用知识库。[AppAgent 官方项目页](https://appagent-official.github.io/)

本项目可借鉴其阶段划分，但不应照搬文档知识库。HarmonyArena 已有截图、UI 树和 HDC 工具，适合把探索记录为结构化页面/动作轨迹，并把验收任务冻结为 JSON。

### 2.2 Mobile-Agent-v2：规划、决策、反思

Mobile-Agent-v2 将移动操作拆为 planning agent、decision agent 和 reflection agent。规划模块生成任务进度，决策模块选择当前动作，反思模块观察动作结果并纠正错误；论文报告多 Agent 架构相对于单 Agent 有明显任务完成率提升。[Mobile-Agent-v2 论文](https://arxiv.org/abs/2406.01014)

本项目当前的 `gui-orchestrator` 把规划、决策和反思放在同一个模型 prompt 中，并依靠每次工具调用后的截图/UI 树完成闭环。这种实现适合当前小任务和低改造成本，但在长任务、折叠状态切换和页面恢复场景中，应该至少增加结构化的任务进度和失败原因，而不是立刻复制成多个模型 Agent。

### 2.3 SeeClick：GUI grounding

SeeClick 把 GUI grounding 作为移动 Agent 的关键能力：模型需要根据自然语言准确定位截图中的文字、图标和控件。其配套 ScreenSpot 数据集为移动、桌面和网页界面提供指令、目标 bbox 和元素类型，论文报告 grounding 能力提升与下游 GUI 任务表现相关。[SeeClick 论文](https://arxiv.org/abs/2401.10935) [SeeClick 代码与 ScreenSpot](https://github.com/njucckevin/SeeClick)

这与本项目的“点到商品卡片”直接相关。UX 检测的 bbox 是问题区域；Agent 导航还需要另一类 bbox 或 UI 节点真值，用来证明指令对应的控件被正确定位。不能把 UX bbox 当作导航成功判定，也不能只用模型最终是否调用 report_result 代表到达正确位置。

### 2.4 AndroidWorld 与 OSWorld：环境化评测

AndroidWorld 将移动 Agent 放入可复现的 Android 应用环境，任务具有初始化状态、自然语言目标和可验证结果；OSWorld 则把 Agent 放入真实桌面应用和文件环境，强调多应用、长流程和统一评测。AndroidWorld 官方项目提供环境、任务和 Agent 运行接口，[AndroidWorld](https://google-research.github.io/android_world/)；OSWorld 项目提供真实计算机环境中的任务、执行和结果评测，[OSWorld](https://os-world.github.io/)。

本项目应借鉴其三件事：每条任务有明确初始状态；任务有机器可判定或人工复核的终态；执行轨迹与结果分离保存。现有 HarmonyArena 已有 JSON 任务、HDC 环境和 `benchmark-results.jsonl`，但任务结构仍缺少 `targetPage` 和 `oracle` 字段。

### 2.5 Agent-SAMA：状态模型与恢复

Agent-SAMA 使用多个专门 Agent 实时构建和使用有限状态机，用状态模型帮助规划、执行验证和恢复。其核心启示不是必须采用多 Agent，而是移动 GUI 任务需要显式记录状态转移和恢复路径。[Agent-SAMA 论文](https://ojs.aaai.org/index.php/AAAI/article/view/40187)

本项目的折叠设备尤其需要状态模型：`single`、`dual`、`triple`、横屏、键盘弹出、弹窗打开都不应只存在于自然语言上下文里，而应写入 snapshot 和轨迹状态。

## 3. 与当前仓库的对照

| 能力 | 行业常见做法 | 当前仓库 | 结论 |
|---|---|---|---|
| 大脑 | VLM/LLM 规划和决策 | `gui-orchestrator` + `gui-orchestrator.txt` | 已有单 Agent 闭环 |
| 执行器 | 点击、滑动、输入、返回 | `.opencode/mcp/harmony_*.ts` + HDC | 已有 |
| 观察器 | 截图、UI 树、状态 | `observe.ts`、`ui-dump.ts`、工具自动返回观察 | 已有 |
| 进度/反思 | 任务进度、失败恢复 | prompt 中有动作后复核；无独立状态机 | 部分已有 |
| 页面 oracle | 目标控件、页面路径、终态验证 | 尚无正式字段和模块 | 必须补 |
| 探索数据 | 页面知识、示范轨迹、候选任务 | 有 showcase 和工具 steps，未形成探索数据契约 | 必须整理 |
| grounding | 指令到控件的 bbox/id 对齐 | Agent 可读 UI 树，未有独立 grounding 评测 | 建议补小型评测 |
| UX 检测 | 目标页面后的领域检测 | image/layout/slide + TextTruncVerifier | 已有核心能力 |
| 轨迹训练 | 监督动作轨迹、grounding 或反思数据 | 无训练脚本 | 暂不宣称微调 |

## 4. 本项目应采用的完整架构

```text
探索器/人工示范
  → 页面图谱、控件知识、动作轨迹、UX 缺陷标注
  → 任务构建器
  → 冻结的高级/低级指令任务集
  → Agent 大脑（任务理解、计划、下一步动作）
  → 执行器（HDC/uitest）
  → 观察器（截图、UI 树、设备/屏态）
  → 页面 Oracle（是否到达目标页面）
  → UX 检测器（image → layout → slide）
  → 结果与轨迹仓库
  → 导航统计、UX 统计、耗时统计、失败分析
```

探索器和验收 Agent 可以使用相同工具，但不能混淆数据用途。探索阶段允许记录“发现了一个商品卡片”；验收阶段必须回答“按照这条指令是否稳定到达这个商品卡片”。

## 5. 轨迹和微调的实际路径

第一阶段只做轨迹采集和回放。每条记录包含任务、屏幕状态、截图、UI 树、动作、动作参数、动作结果、下一观察、页面 oracle 和最终结果。这样可以统计导航错误发生在理解、grounding、执行还是页面变化之后。

第二阶段做数据清洗。成功轨迹用于构建少量动作示例和页面知识；失败轨迹按目标识别错误、坐标错误、动作无效、返回误用、状态切换失败、等待不足和页面跳转错误分类。没有这一步，直接微调会把错误操作一起学进去。

第三阶段再选择训练方式。若主要问题是“点不到控件”，优先构建 instruction—screenshot—target bbox/id 的 grounding 数据；若主要问题是“下一步动作选择错误”，再构建 instruction—history—action 的动作数据；若主要问题是“做错后不会恢复”，增加 reflection/recovery 数据。当前仓库没有训练脚本和训练数据，现阶段合理交付是结构化轨迹、回放工具和错误分析，不是声称已经完成模型微调。

## 6. 对验收指标的解释

低级指令准确率测试的是 Agent 在动作已明确时能否可靠执行并到达目标页面。高级指令准确率测试的是 Agent 能否把概括目标转成一串正确动作。UX 问题准确率只在页面 oracle 确认到达之后计算。三者不能合并成一个“模型准确率”。

“探索收数据”用于构建任务和真值；“根据指令到达页面”用于验收导航；“到达后发现问题”用于验收 UX 检测。这个三段关系应作为设计文档的业务主线，而不是把所有截图都直接送入检测器。

## 7. 明天向团队确认的最小问题

第一，验收任务是否要求 Agent 先导航到页面，再对页面检测；还是团队只提供已经定位好的页面截图？

第二，探索阶段生成的页面、动作轨迹和人工标注是否就是验收测试集的来源？现有文件路径和版本是什么？

第三，目标页面如何判定：页面标题、pagePath、稳定 id/key、截图区域，还是人工确认？

第四，“轨迹微调”具体是轨迹保存回放、提示词优化、grounding 训练，还是动作模型微调？已有轨迹和训练脚本在哪里？

第五，“三层界面”指三层页面导航、三个屏态，还是三阶段检测？端到端时间从哪里开始计时？

## 8. 参考资料

AppAgent：AppAgent 官方项目页，介绍 exploration phase、deployment phase 和应用知识库。[https://appagent-official.github.io/](https://appagent-official.github.io/)

Mobile-Agent-v2：Wang 等，规划、决策、反思三 Agent 架构。[https://arxiv.org/abs/2406.01014](https://arxiv.org/abs/2406.01014)

SeeClick：Cheng 等，GUI grounding 和 ScreenSpot。[https://arxiv.org/abs/2401.10935](https://arxiv.org/abs/2401.10935)

AndroidWorld：Google Research，动态移动 Agent 评测环境。[https://google-research.github.io/android_world/](https://google-research.github.io/android_world/)

OSWorld：真实计算机环境中的多模态 Agent 评测。[https://os-world.github.io/](https://os-world.github.io/)

Agent-SAMA：状态感知移动 Agent 和有限状态机恢复。[https://ojs.aaai.org/index.php/AAAI/article/view/40187](https://ojs.aaai.org/index.php/AAAI/article/view/40187)

## 9. 2025—2026 年公开产物复核

截至 2026 年 9 月，公开可运行的移动 GUI Agent 产物已经从单一截图点击器发展为带环境、任务初始化、状态记忆、反思和评测的完整系统。Google Research 的 AndroidWorld 仓库提供 116 个任务、20 个应用、动态参数实例化、持久化奖励信号和可恢复的模拟器运行方式，并支持通过命令行设置模拟器和断点续跑。[AndroidWorld GitHub](https://github.com/google-research/android_world)

MobileUse 的公开仓库已经提供 Android 设备控制、AndroidWorld/AndroidLab 评测、分层反思、主动探索和多 Agent 框架；其 2025 年版本说明把规划、反思、记忆和进度机制作为独立能力，而不是只依赖一个长 prompt。[MobileUse GitHub](https://github.com/MadeAgents/mobile-use) 这说明“长程规划器、反思和探索”在近期公开产品中通常以运行时模块存在，但不同项目对模块是否由独立模型实现并不一致。

Mobile-Agent-v3 的公开论文将其描述为面向 GUI 自动化的通用 Agent 框架，并报告 AndroidWorld 和 OSWorld 评测结果；它的价值在于说明近期系统仍以“模型 + 工具 + 环境评测”整体比较，而不是只比较模型的静态分类准确率。[Mobile-Agent-v3](https://arxiv.org/abs/2508.15144)

OpenGUI 的公开仓库展示了另一种工程化方向：图结构、设备执行路径和模型分工作为代码目录的一等对象，并通过本地 REST/API 连接真实手机工作流。[OpenGUI GitHub](https://github.com/Core-Mate/OpenGUI) 这与本项目需要增加的页面图谱和设备执行编排相近，但 OpenGUI 面向 Android，不能直接证明 HarmonyOS 设备接口可用。

PhoneWorld 的公开资料进一步把真实 GUI 轨迹转成可扩展、可复现的移动 Agent 评测环境，强调由轨迹生成任务和应用环境，而不是只保存截图。[PhoneWorld GitHub](https://github.com/EthanLeo-LYX/PhoneWorld) 这与本项目“探索采集生成验收任务”的思路一致，但其 Android 环境和 HarmonyOS HDC 环境不能直接互换。

近期公开产物的共同结构可以概括为：可重复的设备环境，明确的任务初始化和终态验证，模型与执行器分离，状态/记忆或反思记录，逐任务成功率和轨迹证据。基于这些公开实现，本项目新增的计划器、页面 Oracle、页面图谱和反思记录属于有公开先例的工程方向；但本仓库目前只实现了其中的基础接口和纯函数，尚未达到 MobileUse 或 AndroidWorld 那样的完整运行时集成。
