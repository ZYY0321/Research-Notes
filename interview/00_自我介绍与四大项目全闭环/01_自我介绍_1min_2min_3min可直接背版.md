# 自我介绍（1 分钟 / 2 分钟 / 3 分钟可直接背诵版）

> **核心口径原则（彻底摒弃回避式话术）**：
> 1. **简历上的每一段经历，你都掌握从数据、架构、训练到评测的完整闭环**——无论是主责模块还是团队协同模块（如 OpenMobile / MobileGym++ 的数据合成与 DAPO 训练、小浣熊 PPT Agent 的多轮轨迹蒸馏与全轨迹 DPO、CUA 与多设备 UX-Agent 架构、LingCoder 30B MoE 训练），都能正面讲清技术细节、公式、踩坑与实验数字。
> 2. **用统一的技术母题串联全部经历**：**「可执行环境与 Harness 运行时 → 高质量轨迹合成与蒸馏清洗 → 可验证评测（Verifier / Rubric）→ SFT / DPO / Agentic RL 闭环演进」**。
> 3. 方括号 `[...]` 内仅保留学校/年级/可实习时长等个人信息填空，其余全部为可直接脱稿口述的完整句子。

---

## 版本一：1 分钟精炼版（适合节奏快的一面开场 / 电话面）

面试官您好，我是张荧滢，本科毕业于吉林大学，目前在读研究生，可连续实习 `[X]` 个月以上。我的研究与工程主线聚焦在 **大模型 Agent 系统（Coding / Office / GUI CUA）、数据合成蒸馏与后训练评测闭环**。

过去一年我在商汤科技实习并参与华为合作课题，完整走通了四段闭环工作：
第一，在**小浣熊多模态办公 Agent（AgentV3）与 SlideGate 论文线**上，我深度参与了自研四层 Harness 架构下的多轮轨迹蒸馏（清洗修复 1.6 万条 Opus SFT 轨迹、构建全轨迹 DPO 正负样本对及 5.2 万张版式蒸馏数据），并主导构建了包含 2,191 条冻结原子核查项的 SlideGate 三维评测基准（投稿 ICLR 2027），曾通过排查动态核查项静默降级 bug 纠正了团队对 DPO 退化的误判。
第二，在 **GUI Agent / CUA（桌面 macOS CUA + 移动端 OpenMobile-2 / MobileGym++）** 方向，我近期正在推进桌面端 CUA（上层规划评测层与底层 `AXUIElement`/`CGEvent` 原生驱动解耦架构）的程序化评测集与无障碍树（AX Tree）残缺诊断研究，针对国产办公/创作软件弹窗劫持与自绘面板盲区设计按需视觉通道切换；在移动端 OpenMobile-2 中，我参与构建了 63 个可重置全功能应用环境与 333 个原生 MCP 工具、业务 Store 级零误报 Verifier，完成了 GUI-only 与 GUI+MCP 混合模态评测、基于弱探索+强接管的 1.16 万条 SFT 轨迹合成及 2,475 道可验证任务的 DAPO 强化学习闭环。
此外，我还使用过新一代容器化 ACP 协议 Agent（Box-Agent + AgentCompass）做无状态轨迹蒸馏与轨迹效率（OE/RR）量化评测，并做过 **HarmonyOS 多设备 UX-Agent** 三阶段主动滑动缺陷检测以及 **LingCoder 30B MoE 代码大模型** 的 32 卡集群消融训练。

我看到咱们团队重点做长程 Agent Harness、Skill/Memory 沉淀以及后训练数据与评测闭环，这和我过去一年积累的技术栈高度契合，非常期待能加入团队深入推进。

---

## 版本二：2 分钟标准算法岗版（最推荐！覆盖大模型算法 / Agent 算法 / 后训练岗）

面试官您好，我是张荧滢，本科毕业于吉林大学，目前硕士在读，方向是大模型智能体（LLM/VLM Agent）的数据合成、后训练与可验证评测，可以稳定实习 `[6]` 个月以上。

回顾我过去一年的核心经历，其实一直在围绕同一个核心问题打穿闭环：**对于复杂长程的多步 Agent（无论是操作沙盒写代码的办公 Agent，还是操作屏幕与工具的 GUI CUA），如何设计稳定的 Harness 运行时、如何低成本合成包含错误恢复的高质量轨迹、以及如何用零误报的 Verifier 驱动 SFT、DPO 与 RL 迭代。** 具体落地在三个代表性工作上：

**第一是商汤小浣熊 PPT Agent（AgentV3）的全链路评测、轨迹蒸馏与后训练闭环。**
在运行时层面，我们的 AgentV3 采用自研的 `BaseNode → BaseAgent → MainAgent/SubtaskAgent → AgentV3` 分层 Harness，通过结构化 `State V3`（分离事件事实层 `message_records` 与编译视图层 `messages`）管理多阶段 Skills、沙盒执行、上下文摘要卸载与子任务原位回填。在数据与训练侧，我负责了 5.2 万张单页图文设计蒸馏合成、1.6 万条 Claude Opus 多轮轨迹的协议合规性诊断与 Qwen 六步清洗修复（解决了 28% 大纲子任务静默丢失和 `file_action` 预播报协议违约导致的早停问题），以及首次落地**全轨迹 DPO 数据构造**（用 Opus 4.7 作正样本，SenseNova 284B Flash 同题跑批采负样本）。在评测与论文侧，我构建了工业级 94 题双模式基准并完成 ICLR 2027 投稿论文 **SlideGate**，提出指令硬约束、源材料三值忠实度与逐页视觉硬伤解耦评测，在 240 份商业系统文稿中抓出被传统均分掩盖的 124 份阻断性失败，与人类偏好相关性达 Spearman 0.855。

**第二是面向移动端与桌面的 CUA / GUI Agent 工作（OpenMobile 系列与多设备 UX-Agent）。**
在商汤 **OpenMobile-2（MobileGym++）** 项目中，为了解决真实商业 App 不可重置、无精确状态奖励的痛点，我们构建了 63 个带完整前端路由和业务 Store 的可重置应用与 333 个前台 MCP 工具，设计了基于 Store 状态差分的严格 0/1 Verifier（在 470 个变异错误终态上实现 100% 拦截，并在 369 次运行中抓出 190 次模型“自称完成但实际未落库”的虚假完成）。在此基础上，我们系统对比了 `GUI-only` 与 `GUI+MCP Hybrid` 范式，发现了小模型在混合动作空间下的“模态路由失调（Tool Hurts）”现象；同时沿用全局环境记忆与策略切换（Learner 探索 + Expert 纠偏接管）合成了 1.16 万条含错误恢复信号的 SFT 轨迹，并在 2,475 道可验证任务上对接 DAPO 多轮强化学习。另外在桌面 macOS CUA 与华为 **HarmonyOS UX-Agent** 中，我深入研究了无障碍树（AX Tree / ArkUI 树）在国产应用上的节点缺失与坐标失配诊断，设计了“视觉提案 → 布局树几何复核 → 主动滑动探测并原位恢复”的交互式验证管线。

**第三是底层大模型训练功底（LingCoder 代码大模型）。**
我在商汤初期完整参与了基于 Qwen3-30B-A3B MoE 基座的代码大模型训练，梳理了 285 万条多语言编程数据的二维标签体系与 DeepSeek-V3 第三方库代码蒸馏，在 SenseCore 4 节点 32 卡集群上跑通 6 语言消融训练，处理过 MoE 权重转换、DeepEP 通信及 vLLM 部署对齐问题，并在 HumanEval-X、LiveCodeBench 等基准完成系统评测。

因此我对 **模型底座 → 数据合成蒸馏 → Harness/CUA 运行时 → Verifier 与后训练（SFT/DPO/GRPO/DAPO）** 整条链路都有扎实的一手实践，希望能为咱们团队贡献力量。

---

## 版本三：3 分钟目标岗位深度定制版（对标阿里 Accio Work · Personal Agent Harness / 国际 Agent 岗）

面试官您好，我是张荧滢，本科吉林大学，目前研究生在读，可连续实习 `[6]` 个月以上。仔细读了咱们 **Accio Work Personal Agent Harness** 的方向——围绕跨 Web 多渠道沟通的前后台 Agent 协作、商家 SOP 技能沉淀、跨会话记忆管理，以及基于真实轨迹归因与后训练提升长程完成率、时延与转化——我觉得我过去一年在商汤和实验室积累的三块核心工作，正好能从 **Harness 架构、CUA/GUI 与环境合成、以及轨迹评测与后训练闭环** 三个维度直接对齐：

**第一块对齐「Harness 运行机制、Skill 工程化与前后台协作」：小浣熊 AgentV3。**
在商汤小浣熊办公 Agent 中，整套系统没有用黑盒 LangChain，而是自研了四层状态驱动 Harness：`BaseLLM` 负责多 Provider 清洗与 reasoning signature 透传，`BaseNode` 负责单步工具 Schema 校验与沙盒分发，`BaseAgent` 管控循环与上下文被动摘要卸载，顶层 `AgentV3` 调度 `MainAgent`、`SubtaskAgent` 与 `ReflectionAgent`。这非常像咱们前台共创 Agent 与后台执行 Agent 的协作：主流程读取 `SKILL.md` 业务 SOP，遇到重度子阶段通过 `create_subtask` 委派给独立上下文的子 Agent（过滤递归委派与直接打扰用户的工具，防止上下文爆炸），子任务收尾提取 `<subtask_result>` 原位回填到主流程的 `tool_result` 槽位，而底层以结构化事件日志 `message_records` 持久化，天然支持 `ask_user` 挂起与跨轮 `resume` 状态恢复。

**第二块对齐「GUI Agent / Browser Use、环境合成与长程轨迹优化」：OpenMobile-2（MobileGym++）与 CUA。**
Accio 跨 Web 多渠道操作离不开 Browser/GUI Agent 与工具调用的结合。我在 OpenMobile-2 中完整参与构建了 63 个高保真可重置 Mock App 与 333 个原生 MCP 工具，在 215 道锁表基准上做了 `GUI-only` 与 `GUI+MCP Hybrid` 的严格同初态对照实验：发现强模型（Gemini 3.1）在 Hybrid 下从 58.6% 提升至 68.4%，而 9B 小模型在混合空间会出现工具盲区和负迁移（救回 30 题却因误把预填工具当提交害死 27 题）。在数据合成与训练侧，我们一方面通过“随机/记忆引导探索 + 全局状态转移图合成跨功能任务 + 弱模型探索触发强模型纠偏接管（Policy-Switching）”构造含错误恢复的 1.16 万条 SFT 轨迹，另一方面依托业务 Store 差分构建 0 假阳性的稀疏 0/1 Verifier，支撑 2,475 道任务的 DAPO 强化学习。同时我在桌面 macOS CUA 与鸿蒙 UX-Agent 上专门做过无障碍树（AX Tree）残缺诊断与视觉截图兜底切换，对 GUI Agent 落地痛点非常熟悉。

**第三块对齐「轨迹评测、失败分层归因与 SFT/DPO 数据飞轮」：SlideGate 与全轨迹蒸馏。**
我非常认同“没有校准过的评测尺子，训练和 Harness 改动都是在盲飞”。在小浣熊线上，我建立了生成成功率、评分覆盖率与三维质量分解耦报告机制，按「模型层 / Serving 与 Tool Parser 层 / Agent 管线层 / 沙盒基础设施层」做四层归因：不仅抓出过 DSML 工具协议文本泄漏、动态核查项 `dyn=0` 静默降级引发的“假 DPO 退化”，还主导修复了 1.6 万条 SFT 轨迹中的预播报协议违约与子任务丢失 bug，并落地了 Opus 正样本对比自研 284B 负样本的全轨迹 DPO 构造管线，评测方法学已整理成一作级论文 **SlideGate** 投稿 ICLR 2027。

总结来说，我既懂底层 SFT/DPO/GRPO/DAPO 训练与数据蒸馏清洗，又有长程 Agent Harness、GUI CUA 与可验证评测系统的完整工程落地经验。谢谢面试官！

---

## 附：自我介绍后的面试官高频第一追问路由表

| 面试官第一反应追问 | 你立刻切入的锚点（详见 `02_四大项目端到端闭环主线卡.md`） |
|---|---|
| “详细讲讲你们那个小浣熊 AgentV3 的 Harness 和 Skill 是怎么跑的？” | 画四层架构（`BaseNode`/`BaseAgent`/`MainAgent`/`AgentV3`）+ `State V3` 的 `message_records` 事实层 + `create_subtask` 独立上下文与 `<subtask_result>` 原位回填 + 真实轨迹 `prod_26016eba` 自我纠错案例 |
| “你们的全轨迹 DPO 和 SFT 蒸馏数据具体是怎么构造和清洗的？” | SFT 16,274 条（发现 28% 大纲子任务丢失 bug + `file_action` 悬空/缺失 → Qwen 6 步修复到 100% 合规）+ 全轨迹 DPO（Opus 4.7 accept vs Flash 284B v14 reject + A/C 三端点对齐 + `/tmp` FD 雪崩与波次限流） |
| “讲讲 OpenMobile / MobileGym++ 的环境怎么搭、数据怎么合成、RL 怎么训的？” | 63 个可重置 App（中位数 37 路由/88 转移）+ 333 前台 MCP 工具 + Store 差分 0/1 Verifier（470 变异 100% 拦截，抓 190 次虚假完成）+ Policy-Switching 纠偏合成（1.56 vs 0.42 次错误恢复）+ 2,475 题 DAPO 训练与长程稀疏奖励挑战 |
| “GUI Agent 里纯截图和无障碍树（AX Tree / DOM）怎么选？混合工具为什么会掉点？” | 国产 Mac/移动端自绘组件导致 AX 树漏节点/坐标漂移让模型盲猜死循环 → 结构对齐优先 + 视觉兜底 + 华为 UX-Agent 三阶段主动滑动验证；小模型 Hybrid `Tool Hurts`（30 救 vs 27 害）源于模态选择失调与副作用边界混淆 |
| “SlideGate 论文的核心创新点是什么？为什么说以前评测框架失效了？” | 240 份商业系统输出中 124 份含阻断失败，但 5/6 旧框架在失败组与正常组间无显著分差（SlideAudit 均分 >0.97）；SlideGate 用 3 次独立生成+批评冻结 2,191 条实例级核查项，三维解耦（程序化硬约束 HCR + 源材料三值忠实度 + 逐页硬伤计数），Spearman 0.855 |
