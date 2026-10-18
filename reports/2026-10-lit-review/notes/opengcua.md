# OpenGCUA: 面向"通用计算机使用代理"的全开源技术栈报告

## 开会速记

- 阿里团队给"计算机使用代理(CUA)"提出一个新的统一定义——**GCUA(通用计算机使用代理)**：模型在每一步自主决定"观察什么、怎么动作、怎么组织工作"，并证明现有的GUI-only代理、CLI代理、多代理分工系统、以及作者自己之前的GUI+CLI批量动作代理(Qwen-UI-Agent)都只是这个框架里"预先固定了某些决策"的特例。
- 核心设计是让模型把GUI点击(pyautogui)、Shell命令(bash())、Accessibility树操作写成**一段可执行Python程序**（而不是预先列好的动作列表），并让模型自己决定何时要截图、如何维护任务状态——称为"harness-to-model decision transfer"。
- 证据是**经验性消融实验**，不是新训练模型：在OSWorld-v2的82任务离线子集上，对GPT-6 Astra、Claude Opus 5等8个前沿模型，完整OpenGCUA配置相比"GUI-only批量动作"基线，平均partial score提升19.6分、步数减少53.0%。
- 在4个真实macOS任务的小规模探索中，发现不同模型real-device执行效率差异巨大(Qwen3.8-Max推理token是GPT-6 Astra的19.4倍但完成更少)，但作者自己说明这只是"4任务、多为单次运行"的探索性证据，不能当稳定排名。
- 本文不检测UX/显示缺陷，其oracle是任务完成度评测脚本；但其"代码执行+结构化观测做可执行校验"和"按需截图"的harness设计思路，对我们UX-Agent的布局树复核/滑动探测时机设计，以及OpenMobile-2的GUI+MCP混合动作空间设计，有方法论参考价值。

## 一页读懂

| 维度 | 内容 |
|---|---|
| 旧方法哪里不够 | 现有CUA研究多把问题框定为"GUI-only"操作(截图+鼠标键盘)，而前沿系统(如GPT-6 Astra)已转向GUI+Shell+代码执行+API混合，但闭源，模型权重、prompt、real-device harness、执行轨迹均不公开，社区无法复现、对比设计选择(Sec 1)。 |
| 本文新增 | (1) 提出GCUA形式化定义(Eq 1)，把GUI/CLI/多代理/GUI+CLI批量动作代理统一为该框架特例(Table 1)；(2) 提出"harness-to-model decision transfer"机制(按需截图、todo任务状态、intent标注)；(3) 公开OpenGCUA实现、prompt、8个前沿模型的评测轨迹；(4) 发布preliminary的real-device harness与Cross-Device SDK。 |
| 输入/输出 | 输入=任务指令+系统prompt+交互历史(模型自选的screenshot/AX tree+程序执行输出)；输出=模型每步生成的一段Python代码(可混合pyautogui/bash()/AX操作/API调用，含循环分支)，由harness执行、把stdout/stderr/screenshot等反馈返回模型，循环至模型调用terminate()。 |
| 怎样验证 | OSWorld-v2(v2.1) 82任务离线子集，8个前沿模型，对比GUI-only batched基线与OpenGCUA全配置，并做code execution、harness-to-model decision transfer各组件消融；另在4个真实macOS任务上用preliminary real-device harness比较模型效率与完成度。 |
| 结论边界 | 本次release不含训练模型，只是用现有前沿模型做agent设计的经验性验证(Sec 5.1)；real-device结果仅4任务、多为单次选定运行，作者自己说明"characterize the evaluated configurations rather than establish a general model ranking"(Sec 4.3.3)；不涉及显示类(UX)缺陷检测，oracle是任务级评测脚本。 |

> catalog.md 建议记录行：OpenGCUA | 2026 | llm | preprint | execute | method/harness/empirical | desktop | hybrid(llm-prompt) | spec | OSWorld-v2 82任务 | 全配置较GUI-only batched基线partial score+19.6分/步数-53.0%(8模型)

## 一段话介绍

这篇报告研究的不是"GUI缺陷检测"问题，而是"计算机使用代理应该如何设计执行机制"这一GUI(及程序化接口)任务执行问题：作者认为计算机使用正从"只用鼠标键盘操作GUI"转向"GUI+Shell+API混合、甚至直接写代码"，但前沿闭源系统(GPT-6 Astra等)不可复现，因此提出"通用计算机使用代理(GCUA)"的统一定义——模型在每一步自己决定观察什么、怎么动作、怎么组织工作——并构建一套开源的OpenGCUA harness，让现有前沿模型可以使用代码执行(把GUI操作、Shell命令写成同一段Python程序)和"harness-to-model decision transfer"(模型自己决定何时截图、如何记录任务状态)。证据主要来自OSWorld-v2基准上对8个前沿模型的批量消融实验(任务完成分数、步数、token消耗)，以及在4个真实macOS任务上的探索性real-device对比；论文没有训练新模型，评价的是"agent执行设计"本身而非UX/显示缺陷检测能力。

## 关键术语与阅读前提

- **CUA (Computer-Use Agent，计算机使用代理)**：通过视觉或程序化接口操作计算机完成任务的智能体，原文的研究对象(Sec 1)。
- **GCUA (Generalist Computer-Use Agent，通用计算机使用代理)**：本文新定义的一类CUA，由模型在每步做"观察/动作/组织"三项决策(Sec 2.1)，可链接 ../glossary.md 的"agent"条目补充理解。
- **AX Tree (Accessibility Tree，无障碍树)**：操作系统/应用暴露的控件层级结构(角色、名称、值)，可直接按元素操作、无需坐标(Sec 2.1)。类比我们UX-Agent中的"ArkUI布局树"。
- **batched actions (批量动作)**：模型一次调用生成固定的多个动作序列(如作者此前Qwen-UI-Agent的做法)，与code execution相对，是"没有控制流的程序"(Sec 2.3)。
- **code execution (代码执行)**：模型把GUI操作、Shell命令写成一段带循环/分支/变量的Python程序，由harness一次性执行(Sec 2.3, 3.1)。
- **harness-to-model decision transfer**：把原本由harness固定规则决定的工作流决策(如"每步后截图")转移给模型自己判断(Sec 3.2)。
- **OSWorld-v2**：桌面计算机使用任务基准，本文使用其v2.1版82任务离线子集（排除需联网的26个任务）(Sec 3.3.1, Appendix A)。
- **partial score / success(完成率)**：评测器给出的0–100分部分完成度，及归一化分数>0.999999记为完全成功(Appendix A)。
- **cache hit rate (缓存命中率)**：输入token中由提示缓存命中服务的比例，用于衡量上下文管理效率(Table 4)。

## 动机

作者在引言中指出：目前大量文献把CUA研究问题设定为"模型通过截图+鼠标键盘能多好地操作GUI"(Sec 1, 引用Qin et al. 2025; Lu et al. 2026)。但前沿系统(如GPT-6 Astra)已经把GUI交互和Shell命令、Accessibility树访问、其他工具结合起来，OpenAI甚至在文档中建议"把GUI操作写成代码，和程序化操作合并到同一次模型输出里"(Sec 1, 引用OpenAI 2026b)。这些系统面向用户自己的真实计算机，其中"共享控制、与后台窗口交互、需求不断变化"等挑战是基准测试没有完全覆盖的(Sec 1)。于是问题从"模型操作GUI界面的能力如何"变成"系统用任何有效手段在真实计算机上完成工作的能力如何"。但GPT-6 Astra等前沿实现"largely closed"——模型权重、完整prompt设置、real-device harness、设备控制SDK和执行轨迹都不可得，限制了社区复现、比较不同设计、研究设计选择对任务完成和成本影响的能力(