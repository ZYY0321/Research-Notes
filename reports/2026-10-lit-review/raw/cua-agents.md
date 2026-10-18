# CUA / GUI Agent 文献检索记录

检索日：2026-10-18。范围：2026-01 至 2026-10，另收少量 2025 年标志性工作。

核对方式：每条纳入论文的 arXiv 号、标题、摘要、首发时间取自 `https://export.arxiv.org/api/query`（`published` 为 v1 的 UTC 时间，下表只保留日期）。机构取自对应论文 TeX 源文件的作者栏，或已打开的会议论文首页。关键数字只抄**当前 arXiv 摘要**原文；正文或会议 PDF 中的不同数字单独标出，不混入摘要数字。

场合列：只在打开过会议/期刊官方页面时填写会议名，否则写「arXiv预印本」。

---

## 通义 / Tongyi-MAI：2026-10-14 至 2026-10-18

找到的对应发布是 **OpenGCUA**，不是一篇标题页写着「通义实验室」四字的新模型卡。论文署名机构是 **Alibaba Token Hub, Alibaba Group**，脚注写 **MAI-UI Team**。代码仓库在 GitHub 组织 **Tongyi-MAI**。同一组的前序论文 MAI-UI（arXiv:2512.22047）标题页写的是 Tongyi Lab, Alibaba Group。

### OpenGCUA

| 项 | 内容 |
| --- | --- |
| 名称 | OpenGCUA: Toward a Fully Open Stack for Generalist Computer Use |
| 简称 | Open Generalist CUA (OpenGCUA) |
| arXiv | https://arxiv.org/abs/2610.22200 （2610.22200v1） |
| 首发时间 | 2026-10-15（API：`2026-10-15T16:51:35Z`，至检索日仍为 v1） |
| GitHub | https://github.com/Tongyi-MAI/OpenGCUA （仓库创建时间 `2026-10-15T09:03:56Z`；页面标注 Apache License 2.0） |
| 项目页 | https://tongyi-mai.github.io/OpenGCUA/ |
| 作者 | 论文与 API 均以 Hanzhang Zhou, Long Li, Quyu Kong, Lei Wang, Panrong Tong 等为作者；通讯作者 Yue Wang。机构栏：Alibaba Token Hub, Alibaba Group |
| 场合 | arXiv预印本 |

本次发布包含的组件（论文摘要 + GitHub README「What we open in this version」）：

1. 技术报告（本 arXiv）。论文引言写明：**这次发布还不包含训练好的专用 GCUA 模型**。
2. OSWorld 集成示例：reference screenshot-action agent 与 code-action agent。
3. 8 个模型的评测轨迹。摘要写 “all eight evaluated models, including GPT-6 Astra and Claude Opus 5”。GitHub README 列出的 8 个名字是：GPT-6 Astra、Claude Opus 5、Gemini 3.8 Flash、GLM-5.3-Flash、Qwen3.8-Max、Qwen3.8-Flash、Kimi K3、DeepSeek-V4.1-Flash。
4. macOS 真机 harness（preliminary）：菜单栏应用，在用户自己的 Mac 上跑 agent。
5. Cross-Device SDK（preliminary）：计算机、浏览器、手机的一套编程接口。

论文定义的做法（摘要原文口径）：generalist computer-use agent 由模型选择如何观察、行动和组织工作；代码执行让中间结果决定后续操作；并提出 harness-to-model decision transfer，把一部分观察和任务状态决策从固定 harness 规则移到模型。

摘要中的数字（原文）：

- OSWorld-v2 上，完整配置提升全部 8 个被评模型的任务分数，包括 GPT-6 Astra 与 Claude Opus 5。
- mean partial score **+19.6 points**。
- 相对 batched GUI-only execution，reported steps per task 平均减少 **53.0%**。
- 真机 harness 下的 **four real macOS tasks**：选定的 Qwen3.8-Max 运行所用 reported reasoning tokens 是 GPT-6 Astra 的 **19.4 times**。

引言（非摘要）另写、且已在 arXiv HTML 中读到的数字：相对 GUI+CLI，把 GUI 操作写成代码再与程序化操作结合，mean partial score **+6.1 points**，steps per task **−14.8%**；on-demand observation 使两个模型的 cache hit rate 提高 **10.5** 与 **14.4** 个百分点；Qwen3.8-Max 的总 output tokens 是 GPT-6 Astra 的 **5.7 times**。这些数字不在摘要里。

### 同一窗口的配套论文：MAI-Gym

- 标题：MAI-Gym: An Open All-in-One Platform for GUI Agent Evaluation and RL Training across Mobile and Computer Environments
- arXiv：https://arxiv.org/abs/2610.20939 ，首发 **2026-10-14**（API：`2026-10-14T21:06:01Z`）
- 署名：Alibaba Token Hub, Alibaba Group；脚注 MAI-UI Team。arXiv 作者列表首位 Panrong Tong
- GitHub：https://github.com/Tongyi-MAI/MAI-Gym
- 权重：https://huggingface.co/Tongyi-MAI/MAI-Gym-9B 。该模型卡 News 写 “[2026-10] MAI-Gym is released with the paper, project website, and MAI-Gym-9B model weights. Framework source code is coming soon.”
- 项目页：https://tongyi-mai.github.io/MAI-Gym/
- 摘要数字：十个已有基准；**20,000** parallel environment instances；MAI-Gym-9B 在 10B 以下开源 GUI agent 中，**78.4% on MobileWorld**，**76.2% on OSWorld-Verified**；仿真购票 App 上的 RL 迁到真机，任务成功率从 **28.8%** 到 **48.1%**；释放 synthesis skills、mocked apps、**2,000** verified tasks 和 checkpoint。

该文在下面主表类别 2 中有一行，此处不重复计数。

### 中文媒体与模型托管（检索日 2026-10-18）

用「OpenGCUA」「MAI-Gym」检索机器之心、量子位、新智元、知乎：**没有打开到这两篇的专题报道**。知乎上新智元账号命中的是中科院自动化所的 **MobileGym**（浏览器内安卓仿真），不是 MAI-Gym。

打开过的英文/转载页：

- https://aicoder.com/zh/news/news-20261017-alibaba-tongyi-mai-opengcua-mai-gym-computer-use （URL 含 20261017；页面相对时间写「1 天前」）
- https://ailookout.news/blog/alibaba-opengcua-open-computer-use-stack-lifts-eight-models-on-osworld-v2/ （页面写 Published 17 Oct 2026，并称技术报告于 15 October 2026 上 arXiv）
- https://www.xukangr.com/ai-daily/2026-10-17-opengcua-open-computer-use/ （页面写发布于 2026-10-17）
- https://paper.dou.ac/p/2610.22200v1 （页面写发布日期 2026-10-15）

本次检索**没有打开到** ModelScope 上的 OpenGCUA 模型页。论文自己也写了这次不发布训练好的 GCUA 模型。

### 同组更早的 CUA/GUI 发布（日期已核对，便于对照）

| 日期 | 名称 | arXiv | 署名机构 |
| --- | --- | --- | --- |
| 2026-07-30 | Qwen-UI-Agent | https://arxiv.org/abs/2607.28227 | Alibaba Token Hub；脚注称是 MAI-UI 的延续 |
| 2026-05-28 | STAMP | https://arxiv.org/abs/2605.29324 | 第一作者北京交通大学；脚注：实习于 Tongyi AI Lab |
| 2026-02-15 | Mobile-Agent-v3.5 / GUI-Owl-1.5 | https://arxiv.org/abs/2602.16855 | Tongyi Lab, Alibaba Group |
| 2025-12-26 | MAI-UI | https://arxiv.org/abs/2512.22047 | Tongyi Lab, Alibaba Group |
| 2025-12-22 | MobileWorld | https://arxiv.org/abs/2512.19432 | 第一作者单位 Tongyi Lab, Alibaba Group |
| 2025-10-28 | OSWorld-MCP | https://arxiv.org/abs/2510.24563 | 第一作者 Peking University 与 Tongyi Lab |
| 2025-08-21 | Mobile-Agent-v3 / GUI-Owl | https://arxiv.org/abs/2508.15144 | Tongyi Lab, Alibaba Group |

---

## 主表（40 行）

列：简称、完整标题、arXiv/链接、首发日期、机构(第一作者)、场合、类别、核心做法、关键数字。

类别：1 = 原生 GUI/CUA 基础模型与技术报告；2 = GUI agent 的 RL、过程奖励、验证器、自演化/任务合成；3 = 2026 评测与安全/长程基准（含少量 2025 安全基准）；4 = GUI+API/MCP/CLI、记忆、世界模型、软件测试或 UX 评估。

### 类别 1

| 简称 | 完整标题 | arXiv/链接 | 首发日期 | 机构(第一作者) | 场合 | 类别 | 核心做法 | 关键数字 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OS-Helix | OS-Helix: Unifying GUI Interaction and Code Execution in Native Computer-Using Agents | https://arxiv.org/abs/2610.22234 | 2026-10-15 | University of Science and Technology of China；Shanghai AI Laboratory（Bowen Yang） | arXiv预印本 | 1 | 端到端训练一个动作空间里同时包含 GUI 动作和代码执行的多模态 computer-using agent。用 application–artifact composition 构造可验证的 Ubuntu 任务，SFT 冷启动后再在真实桌面环境做在线 RL；RL 使用按动作步而不是按 token 聚合重要性权重的 Step-balanced GSPO。 | OSWorld-Verified 上，OS-Helix-27B 与 OS-Helix-35B-A3B 相对匹配的 Qwen3.5 hybrid baseline 的相对提升为 35.0% 与 33.7%；OS-Helix-27B-RL 再提升 42.9%，达到 66.44% success。摘要还写在 WindowsAgentArena 上有跨平台迁移。 |
| UI-Venus-2 | UI-Venus-2 Technical Report | https://arxiv.org/abs/2609.00028 | 2026-08-27 | Venus Team, Ant Group | arXiv预印本 | 1 | 面向手机、Web、桌面的通用 GUI agent，统一闭环 reasoning-action。同时扩大环境、用 deep-research 管线做功能锚定的指令生成，并用 trace/sample 级评估器、视觉关键点与多模型投票产生 RL 信号；另加安全执行机制。代码与模型链接见论文：https://github.com/inclusionAI/UI-Venus | 摘要写环境覆盖 more than 170 multilingual mobile apps 以及原生桌面操作系统。摘要没有给出任务成功率。 |
| Qwen-CUA | Qwen-CUA: Native Computer Use for (almost) Everything | https://arxiv.org/abs/2608.02352 | 2026-08-03 | 论文作者栏为 Qwen Team & Xlang Lab；arXiv 作者列表首位 Dunjie Lu（列在 core contributors） | arXiv预印本 | 1 | 397B-A17B 的原生 computer-use agent：只看截图，用键盘和鼠标动作，不用 DOM、无障碍元数据或任务专用 API。支架最多保留 20 张活动截图，并用可验证奖励与轨迹切片做训练；另训练超过一万亿参数的 Qwen-CUA-Max。 | 八个基准上超过 Qwen3.7。OSWorld-Verified 86.2；OSWorld 2.0 的 binary/partial completion 为 18.5/48.4。Qwen-CUA-Max 为 87.6 与 21.2/53.3。RedTeamCUA attack success 相对 Qwen3.7 从 36.6 降到 16.4。训练侧：nearly 100,000 vCPUs，约 40,000 个可验证任务。 |
| Qwen-UI-Agent | Qwen-UI-Agent Technical Report: Toward Next-Generation Real-World Centric Foundation GUI Agents | https://arxiv.org/abs/2607.28227 | 2026-07-30 | Alibaba Token Hub, Alibaba Group（作者栏为 MAI-UI Team；arXiv 首位作者 Hanzhang Zhou）。脚注写本文是 MAI-UI 的延续 | arXiv预印本 | 1 | 覆盖手机、电脑、Web 和 DeepSearch 的基础 GUI agent。统一动作空间把 GUI 与 CLI 交错，并在单轮生成 batched actions。用 agent 构造任务与环境，在线 RL 训练超过 100 回合的轨迹，并用超过 10,000 个并发环境做 rollout。 | 手机：82.1% MobileWorld，92.2% MobileWorld-Real，97.5% AndroidDaily。电脑：79.5% OSWorld-Verified，OSWorld-v2 的 partial-progress score 40.0%。浏览器与定位：73.6% WebArena，81.5% ScreenSpot-Pro。 |
| Mobile-Agent-v3.5 / GUI-Owl-1.5 | Mobile-Agent-v3.5: Multi-platform Fundamental GUI Agents | https://arxiv.org/abs/2602.16855 | 2026-02-15 | Tongyi Lab, Alibaba Group（Haiyang Xu）。开源链接 https://github.com/X-PLUG/MobileAgent | arXiv预印本 | 1 | 介绍 GUI-Owl-1.5：instruct/thinking 变体，尺寸 2B/4B/8B/32B/235B，覆盖桌面、手机、浏览器等。摘要列出 Hybird Data Flywheel、统一思维合成（强调 Tool/MCP、记忆、多智能体），以及多平台环境 RL 算法 MRPO。 | 摘要原文：OSWorld 56.5，AndroidWorld 71.6，WebArena 48.4；ScreenSpotPro 80.3；OSWorld-MCP 47.6，MobileWorld 46.8；GUI-Knowledge Bench 75.5。并写 open-source models 上 20+ GUI benchmarks 的 SOTA。与 HTML 正文的基准名称差异见文末口径注。 |
| EvoCUA | EvoCUA: Evolving Computer Use Agents via Learning from Scalable Synthetic Experience | https://arxiv.org/abs/2601.15876 | 2026-01-22 | Meituan（Taofeng Xue）。合作单位含 Fudan University、Tongji University、HKUST | arXiv预印本 | 1 | 原生 computer-use 模型。用可执行验证器自动生成任务，用数万个异步沙箱 rollout 收集经验，再按能力边界做迭代学习：强化成功例程，并把失败轨迹经错误分析与自我修正变成监督。 | OSWorld success rate 56.7%。摘要写其超过 OpenCUA-72B（45.0%）和 UI-TARS-2（53.1%）。后两个数字是 EvoCUA 摘要的转述，与那两篇自身摘要的基准名称/数字并不相同，见文末口径注。 |
| MAI-UI | MAI-UI Technical Report: Real-World Centric Foundation GUI Agents | https://arxiv.org/abs/2512.22047 | 2025-12-26 | Tongyi Lab, Alibaba Group（Hanzhang Zhou） | arXiv预印本 | 1 | 2B、8B、32B、235B-A22B 的基础 GUI agent 家族。自演化数据管线把用户交互和 MCP 工具调用纳入导航数据；按任务状态做端云协同；并用在线 RL 扩大并行环境数和上下文长度。 | ScreenSpot-Pro 73.5%，MMBench GUI L2 91.3%，OSWorld-G 70.9%，UI-Vision 49.2%；AndroidWorld 76.7%；MobileWorld 成功率 41.7%。并行环境从 32 到 512 为 +5.2 points；环境步数预算从 15 到 50 为 +4.3 points。端云协同使端侧性能提高 33%，云端模型调用减少 over 40%。 |
| Step-GUI | Step-GUI Technical Report | https://arxiv.org/abs/2512.15431 | 2025-12-17 | 论文作者栏为 GELab-Team, StepFun；arXiv 作者列表首位 Haolong Yan。论文给出的链接：https://opengelab.github.io/ ，https://github.com/stepfun-ai/gelab-zero | arXiv预印本 | 1 | 用 Calibrated Step Reward System 把模型生成轨迹校准成训练信号，并据此训练 4B/8B 的 Step-GUI。另提出分层的 GUI-MCP，以及基于日常手机使用的 AndroidDaily 基准。 | 标注：>90% annotation accuracy，成本低 10–100x。8B：AndroidWorld 80.2%，OSWorld 48.5%，ScreenShot-Pro 62.6%（摘要原文拼写）。AndroidDaily：3146 个静态动作、235 个端到端任务；8B 的 static 89.91%，end-to-end 52.50%。 |
| ScaleCUA | ScaleCUA: Scaling Open-Source Computer Use Agents with Cross-Platform Data | https://arxiv.org/abs/2509.15221 | 2025-09-18 | 第一作者 Zhaoyang Liu。ICLR 2026 会议 PDF 将其标为 HKUST 与 Shanghai AI Laboratory；TeX 标题页机构行写 Shanghai AI Laboratory。代码：https://github.com/OpenGVLab/ScaleCUA | ICLR 2026（https://iclr.cc/virtual/2026/oral/10006584 与 proceedings 摘要页） | 1 | 用自动 agent 与人类专家的闭环管线，做覆盖 6 个操作系统、3 类任务的计算机使用数据，并在该数据上训练可跨平台操作的开源 CUA。 | 相对基线 +26.6（WebArena-Lite-v2）、+10.7（ScreenSpot-Pro）。94.4%（MMBench-GUI L1-Hard），60.6%（OSWorld-G），47.4%（WebArena-Lite-v2）。 |
| UI-TARS-2 | UI-TARS-2 Technical Report: Advancing GUI Agent with Multi-Turn Reinforcement Learning | https://arxiv.org/abs/2509.02544 | 2025-09-02 | 论文作者栏为 ByteDance Seed；arXiv 作者列表首位 Haoming Wang，全文作者表在 Contributions | arXiv预印本 | 1 | 原生 GUI 中心 agent。包含数据飞轮、稳定的多轮 RL、把文件系统和终端并进 GUI 环境的混合环境，以及大规模 rollout 沙箱。 | Online-Mind2Web 88.2，OSWorld 47.5，WindowsAgentArena 50.6，AndroidWorld 73.3。15 个游戏的 mean normalized score 59.8，摘要写 roughly 60% of human-level performance。摘要还写在 LMGame-Bench 上与 OpenAI o3 等前沿模型有可比性，但没有给出该基准的分数。 |
| Mobile-Agent-v3 / GUI-Owl | Mobile-Agent-v3: Fundamental Agents for GUI Automation | https://arxiv.org/abs/2508.15144 | 2025-08-21 | Tongyi Lab, Alibaba Group（Jiabo Ye）。开源链接 https://github.com/X-PLUG/MobileAgent | arXiv预印本 | 1 | 基础模型 GUI-Owl，加通用框架 Mobile-Agent-v3。云端虚拟环境覆盖 Android、Ubuntu、macOS、Windows，并用自演化轨迹生产；另有异步环境 RL 与在线 RL 算法 TRPO。 | GUI-Owl-7B：AndroidWorld 66.4，OSWorld 29.4。Mobile-Agent-v3：AndroidWorld 73.3，OSWorld 37.7。TRPO 在线 RL：OSWorld 34.9。摘要写 GUI-Owl 在十个桌面/手机 GUI 基准的开源端到端模型中为 SOTA。 |
| OpenCUA | OpenCUA: Open Foundations for Computer-Use Agents | https://arxiv.org/abs/2508.09123 | 2025-08-12 | XLANG Lab, The University of Hong Kong（Xinyuan Wang）。会议 PDF 的机构标记同时列出 Moonshot AI、Stanford、University of Waterloo、CMU 等合作者 | NeurIPS 2025（https://neurips.cc/virtual/2025/poster/119771 ，页面标题为 Spotlight Poster） | 1 | 开源 CUA 框架：人类演示标注设施；跨 3 个操作系统、200+ 应用与网站的 AgentNet；把演示转成带反思长 CoT 的 state–action 对。 | OpenCUA-72B 在 OSWorld-Verified 上平均成功率 45.0%，摘要写此为当时开源模型 SOTA。 |

### 类别 2

| 简称 | 完整标题 | arXiv/链接 | 首发日期 | 机构(第一作者) | 场合 | 类别 | 核心做法 | 关键数字 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MAI-Gym | MAI-Gym: An Open All-in-One Platform for GUI Agent Evaluation and RL Training across Mobile and Computer Environments | https://arxiv.org/abs/2610.20939 | 2026-10-14 | Alibaba Token Hub, Alibaba Group（作者栏为机构名；arXiv 首位作者 Panrong Tong）。脚注 MAI-UI Team | arXiv预印本 | 2 | 把手机、电脑、Web 上的 GUI agent 评测、数据采集和在线 RL 放在同一套 rollout 管线里，并自动合成可重置的仿真 App、跨应用世界和经执行验证的任务。用该平台训练统一的 9B 手机/电脑 agent。 | 支持 ten established benchmarks；20,000 个并行环境实例。MAI-Gym-9B：MobileWorld 78.4%，OSWorld-Verified 76.2%（摘要写为 10B 参数以下开源 GUI agent 中的 SOTA）。仿真购票 App 的 RL 迁到物理手机：28.8% 到 48.1%。释放 2,000 个已验证任务。 |
| Adaptive-Group PRM | Adaptive-Group Process Rewards for GUI Agents | https://arxiv.org/abs/2610.17710 | 2026-10-13 | Beijing Institute of Technology；BIGAI（Zirui Shang） | arXiv预印本 | 2 | 按子目标把 GUI 轨迹动态分成语义组，在动作级和组级估计过程奖励，再用全部组的上下文修正组级判断，并把该过程奖励加到 GRPO 的结果优势上。 | 摘要只写在过程奖励基准和下游 RL 上有效。摘要没有给出 OSWorld 或其他基准的分数。 |
| SoftwareGym | SoftwareGym: Scaling Computer-Use Agent Training with Diverse Synthesized Software Environments | https://arxiv.org/abs/2610.12611 | 2026-10-08 | Shanghai Jiao Tong University（Tian Jin；与 Wenhao Wang 同等贡献，后者单位 Zhejiang University） | arXiv预印本 | 2 | 自动合成带多样界面、可执行功能和运行时验证的 GUI 软件环境，并用这些环境里收集的轨迹训练 CUA。另建 SoftwareGym-Bench。 | 合成 182 个应用、十二个类别，GUI task pass rate 均值 91.5%。SoftwareGym-Bench 为 120 个任务。所得模型在严格域外的 OSWorld 上 Pass@3 从 41.39% 到 56.97%，SoftwareGym-Bench 上 40.0%。 |
| WM-R1 | WM-R1: Training GUI Agents to Reason and leverage World Models with Reinforcement Learning | https://arxiv.org/abs/2608.27508 | 2026-08-27 | East China Normal University（Yu Han）。代码 https://github.com/genalyu/WM-R1 | arXiv预印本 | 2 | 用世界模型代替真实 Android 环境产生全部 rollout 的状态转移，并把世界模型放进思考过程，使 agent 在提交动作前推理后果。奖励同时看任务成功、轨迹效率和世界模型使用。 | 摘要写整理了 2000 个困难任务，并写在 Android 手机基准上显著超过仅 GRPO 的基线和推理时模拟方法。摘要没有给出这些基准的成功率。 |
| GSAR | GSAR: Goal-State-Anchor Rewards for Mobile GUI Agents with Self-Evolving Data Synthesis | https://arxiv.org/abs/2608.22847 | 2026-08-24 | Wuhan University（Long Zhang）；合作者含 Xiaomi Inc. | arXiv预印本 | 2 | 自演化数据合成在任务执行中产生多个环境、任务和目标状态；再把成功目标状态里与任务相关的 UI 元素标成锚点，在 RL 中当作奖励信号。 | 离线轨迹验证 accuracy over 90%，摘要写其最接近基于规则的方法。摘要写在 AndroidWorld 和作者自建基准上表现强，但没有给出这两处的成功率。 |
| IRA | Interactive Reward Agent: GUI Task Evaluation via Environment-State Verification | https://arxiv.org/abs/2607.25904 | 2026-07-28 | Beijing Institute of Technology；BIGAI（Chenrui Shi） | arXiv预印本 | 2 | 交互式奖励 agent：先提出任务完成条件，再调用系统工具、应用工具和 GUI 工具，从执行后的环境状态取证并验证。另建 GUI-RewardBench，并把 IRA 用作 GUI agent 的 RL 奖励。 | GUI-RewardBench：321 条 GUI 任务轨迹、10 类 Ubuntu 桌面应用；IRA accuracy 86.9%。用于 RL 时 OSWorld success rate 34.0%。 |
| VisCritic | VisCritic: Visual State Comparison as Process Reward for GUI Agents | https://arxiv.org/abs/2606.24525 | 2026-06-23 | City University of Hong Kong（Jiachen Qian） | ECCV 2026（https://eccv.ecva.net/virtual/2026/poster/4958 ）。arXiv comment 仍写 “ECCV 2026 submission”，会议虚拟页面标题为 Poster | 2 | 用孪生视觉 Transformer 直接比较动作前后截图，再由 Action-Aware Critic Head 同时判断动作成功、任务进展和错误类型。批评器训练数据从已有轨迹弱监督生成，不另加人工标签。 | 摘要写在五个基准上的实验与离线分析表明，VisCritic 可作为即插即用增强并 generally improving benchmark metrics。摘要没有给出这五个基准的名称或分数。 |
| StainFlow | StainFlow: Entity-Stain Tracking and Evidence Linking for Process Rewards in GUI Agents | https://arxiv.org/abs/2606.07027 | 2026-06-05 | Beihang University（Haojie Hao） | arXiv预印本 | 2 | 过程奖励模型。用可视觉核对的任务实体及其 “stain” 浓度/状态把轨迹分成阶段，再按触发实体检索相关步骤，组成局部证据窗口来核对关键节点。 | AndroidWorld 与 OGRBench：在线 RL 成功率相对提高 3.2%，轨迹完成判断准确率相对提高 1.8%（摘要用 relatively improves）。 |

### 类别 3

| 简称 | 完整标题 | arXiv/链接 | 首发日期 | 机构(第一作者) | 场合 | 类别 | 核心做法 | 关键数字 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GraceBench | How GUI Agents Fail: GraceBench for Execution Stability Diagnosis | https://arxiv.org/abs/2610.19900 | 2026-10-14 | Institute of AI for Engineering, Tongji University（Ridong Zhang）。项目页 https://iaie-physicalai.github.io/GraceBench | arXiv预印本 | 3 | 把手机应用的可达交互空间表示成 UI Transition Graph，并用视频锚定的轨迹对齐做步骤级稳定性诊断，指标包括偏离率、循环负担率和恢复能力，而不只看最终成功。 | 169 个任务、10 个应用、10 个 UTG、2,909 个规范 GUI 状态、3,116 条观察到的转移、3,718 条轨迹。GPT-5.6 Sol 的成功率最高但恢复能力最低；51.24% 的成功运行仍含偏离或循环。 |
| AgentHorizon | AgentHorizon: Evaluating Agentic Judges for Long-Horizon Computer-Use Tasks | https://arxiv.org/abs/2610.11050 | 2026-10-08 | ServiceNow Research；McGill University；Mila（Xing Han Lù） | arXiv预印本 | 3 | 用 166 小时人类录制轨迹构造计算机使用任务，并通过互换相近指令制造负例，检验自动裁判能否区分成功轨迹和完成了相似但不兼容请求的轨迹。分为 AH、AH-S、AH-D。 | 1,373 个任务（指令–轨迹对），三个操作系统，轨迹最长含 up to 300 张截图和动作。评了 11 个裁判、5 种 agent harness。最好的 agentic judge GPT-5.5 在 AH 子集上 balanced accuracy 80.9%。 |
| OSWorld-Pro | OSWorld-Pro: Process-based Evaluation for Computer Use Agents | https://arxiv.org/abs/2609.24890 | 2026-09-21 | NVIDIA（Zhilin Wang） | arXiv预印本 | 3 | 在 OSWorld 式任务上增加过程评测：用超过 67,000 条人工标注支撑子目标，再用与人类对齐的 LLM-Judge 判断子目标是否完成，以区分键盘错误和点击错误等过程失败。 | over 300 tasks，over 2800 subgoals。摘要写 Claude Opus 5 在 OSWorld-Pro 上 only 75.7%，对比 OSWorld 上 83.4%。 |
| MobileWorldSafety | MobileWorldSafety: Benchmarking GUI Agent Safety Against Environmental Injection Attacks in Android Apps | https://arxiv.org/abs/2608.17659 | 2026-08-18 | Shanghai Artificial Intelligence Laboratory（Sujin Chen） | arXiv预印本 | 3 | 在真实 Android 应用上建 142 个风险任务。每个任务有可编程核验的最终状态风险指示，先规则判定，再由 LLM judge 处理含糊情形，以区分安全失败和能力失败。 | 六个 agent（通用 agent 与专用 GUI agent）的 attack success rates 从 40.4% 到 66.9%。 |
| AndroidReality | AndroidReality: How Far Are Mobile Agents from the Real World? | https://arxiv.org/abs/2608.07775 | 2026-08-07 | Arizona State University（Xiaoou Liu） | arXiv预印本 | 3 | 按 MDP 把真实界面变化分成状态、转移、动作三类扰动，在 AndroidWorld 上注入可控扰动做鲁棒性评测，并提出免训练的 Test-Time Introspective Recovery。 | 摘要没有给出扰动前后的成功率。摘要写评测显示明显的鲁棒性差距和四类反复出现的错误。 |
| OSWorld 2.0 | OSWorld 2.0: Benchmarking Computer Use Agents on Long-Horizon Real-World Tasks | https://arxiv.org/abs/2606.29537 | 2026-06-28 | 论文作者栏为 XLANG Lab and Collaborators；arXiv 首位作者 Mengqi Yuan | arXiv预印本 | 3 | 108 个长程计算机使用工作流，覆盖日常与职业任务，并针对流式交互、动态环境、跨源推理、隐状态和视觉空间精度。任务带真实输入材料和有状态用户资料，另有安全报告。主指标是 500 步时的二元完成。 | 人类中位完成时间 about 1.6 hours。Claude Opus 4.7（maximum thinking）平均 318 次工具调用，对比 OSWorld 1.0 的 about 30。Claude Opus 4.8（maximum thinking、batched tool calls）完成 20.6% 任务，partial score 54.8%。GPT-5.5 plateaus near 13%。 |
| MacAgentBench | MacAgentBench: Benchmarking AI Agents on Real-World macOS Desktop | https://arxiv.org/abs/2606.22557 | 2026-06-21 | Shanghai Jiao Tong University；Shanghai AI Laboratory（Yikun Fu）。代码 https://github.com/JetAstra/MacAgentBench | arXiv预印本 | 3 | macOS 基准：676 个任务、25 个应用，近 60% 同时涉及 GUI 和 CLI。用确定性规则评测，并对多应用任务做多检查点部分分和能力标注。 | 三个框架、16 个模型。最好配置是 OpenClaw 上的 Claude Opus 4.6，Pass@1 73.7%；摘要写该优势主要来自 skill library 而不是框架设计。 |
| MyPCBench | MyPCBench: A Benchmark for Personally Intelligent Computer-Use Agents | https://arxiv.org/abs/2606.16748 | 2026-06-15 | Carnegie Mellon University（Lawrence Keunho Jang）。发布页 https://mypcbench.com | arXiv预印本 | 3 | 在带 17 个仿真真实网站和完整桌面栈的 Linux 环境中，用单一人物（Michael Scott）的个人数据评测 computer-use agent。184 个任务来自 OpenClaw 社区的真实请求，统一使用 computer+bash 工具面。 | 六个闭源/开源权重模型中，最好的 Claude Opus 4.6 fully solves 55.4% of the tasks，摘要写它是唯一超过 50% 的模型。 |
| MobileWorld | MobileWorld: Benchmarking Autonomous Mobile Agents in Agent-User Interactive and MCP-Augmented Environments | https://arxiv.org/abs/2512.19432 | 2025-12-22 | Tongyi Lab, Alibaba Group（Quyu Kong）；合作单位含 HKUST (GZ)、University of Florida | arXiv预印本 | 3 | 201 个任务、20 个应用的在线手机基准，强调长程、跨应用、模糊用户指令，以及 agent–用户交互和 MCP 增强任务。用开源替代品和后端数据库做可复现核验，并配 planner–executor 框架以支持用户交互和 MCP 调用。 | 平均完成步数 27.8 vs. AndroidWorld 的 14.3；多应用任务比例 62.2% vs. 9.5%。最好的 agentic framework 与端到端模型成功率分别为 51.7% 与 20.9%。摘要另写近期 agent 在 AndroidWorld 上 achieving over 90% success rates，作为该基准饱和的动机，不是 MobileWorld 的分数。 |
| RedTeamCUA | RedTeamCUA: Realistic Adversarial Testing of Computer-Use Agents in Hybrid Web-OS Environments | https://arxiv.org/abs/2505.21936 | 2025-05-28 | The Ohio State University（Zeyi Liao）。项目页 https://osu-nlp-group.github.io/RedTeamCUA/ | ICLR 2026（https://iclr.cc/virtual/2026/poster/10006548 ；该页同时写 Poster，并写 Oral presentation: Oral Session 6E。OpenReview 条目写 ICLR 2026 Oral） | 3 | 混合沙箱把 VM 操作系统和 Docker 网站平台接在一起，用于间接提示注入测试。可配置对抗场景，并可把测试直接初始化到注入点，使对抗评测与导航能力脱钩。据此构造 RTC-Bench。 | 当前 arXiv 摘要：RTC-Bench 864 个例子。Claude 3.7 Sonnet \| CUA 的 ASR 42.9%；Operator 的 ASR 7.6%；Attempt Rate 最高 92.5%；摘要写最强的 Claude 4.5 Sonnet \| CUA 在端到端设置中 ASR 最高为 60%。ICLR 会议 PDF 正文的端到端数字不同，见文末口径注。 |

### 类别 4

| 简称 | 完整标题 | arXiv/链接 | 首发日期 | 机构(第一作者) | 场合 | 类别 | 核心做法 | 关键数字 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LGWM / RSWT | Right Screen, Wrong Transition: World Models as Verifiers for GUI Agents | https://arxiv.org/abs/2610.11942 | 2026-10-08 | Nanyang Technological University（Jiaming Zhang）。项目页 https://jiamingzhang.netlify.app/lgwm/ | arXiv预印本 | 4 | 无解码器、以动作为条件的世界模型 LGWM，直接预测下一屏的表示而不是文本、代码或图像，并用向量比较做转移验证。训练数据为 1.85M 条真实 GUI 转移，无语义标注。诊断集 RSWT-BENCH 让同一凭据屏同时出现在合法转移和被劫持转移中。 | 免训练分数：0.987 AUC，17 ms per decision；摘要写约高于生成式 GUI 世界模型十个 AUC 点，延迟低三个数量级以上。残差方向区分有害与良性违规：0.953 AUC。 |
| DeltaReplay | DeltaReplay: Task-Relative Memory Reuse for Mobile GUI Agents | https://arxiv.org/abs/2610.11707 | 2026-10-08 | Tsinghua University（Yudong Bai） | arXiv预印本 | 4 | 把成功轨迹存成转移图。复用时把每条边上的动作拆成与任务无关的操作和任务相关参数，再按新任务和当前屏幕决定照做、替换参数后执行，或交给基础 agent。 | 相对同一骨干的基础 agent，AndroidWorld 与 SPA-Bench 上的任务成功率最多提高 10.3 与 25.0 个百分点。 |
| AutoGUIWorld | AutoGUIWorld: Image Generators as Visual World Models for GUI Agent | https://arxiv.org/abs/2610.01215 | 2026-10-01 | 论文作者栏为 Hunyuan AI Data Team；arXiv 作者列表首位 Cheng Yang | arXiv预印本 | 4 | 不部署真实软件：按操作系统、外观和界面状态采样初始 GUI 场景，规划器给出原子动作及其预期视觉后果，图像生成器逐帧改截图，再做动作定位和转移过滤，合成训练轨迹。 | 79,266 条带空间标注的步骤样本，覆盖 Ubuntu、Windows、macOS、Chrome。用这些轨迹微调 Qwen3.5-35B-A3B 后，OSWorld 平均任务分从 33.0% 到 40.8%，ScienceBoard 任务成功率从 14.0% 到 32.2%。 |
| HybridCUA | HybridCUA: Learning to Orchestrate GUI and CLI for Computer-Use Agents | https://arxiv.org/abs/2609.38008 | 2026-09-29 | Zhejiang University（Tongbo Chen）。代码 https://github.com/ZJU-REAL/HybridCUA | arXiv预印本 | 4 | 构造纯 GUI、纯 CLI 和交错 GUI/CLI 三类轨迹，得到 HybridCUA-8K（5K 混合轨迹、3K 已验证 RLVR 任务）。先 SFT，再用鼓励选择性、可靠使用 CLI 的奖励做 RL。 | HybridCUA-9B 在 OSWorld 上 accuracy 53.6%，比基座高 14.8 个百分点；WindowsAgentArena 提高 4.0 个百分点。 |
| AppDeltaWorld | AppDeltaWorld: Transition-Grounded Delta Code World Model for Mobile GUI Agents | https://arxiv.org/abs/2608.05891 | 2026-08-06 | Nanyang Technological University（Weikai Xu） | arXiv预印本 | 4 | 把下一屏预测成受动作转移约束的可执行 HTML 更新，而不是自由图像或文本：检索应用的 Level-1 HTML，生成 Level-2 可执行 HTML，再插入视觉素材并用浏览器渲染。也用作闭环 SFT 和测试时 RL 的训练环境。 | 作为世界模型，在 CMGUIBench-500 的 Code2World 评测上保真度最高（摘要未给绝对分数）。作为训练环境，AppDeltaAgent 在 AndroidLens 上达到 SOTA，并在 MobileGym 与 MobileWorld 上有 consistent gains（摘要未给后两者的分数）。 |
| STAMP | STAMP: Training Explicit Memory for Mobile GUI Agents in Controllable and Scalable Virtual Environments | https://arxiv.org/abs/2605.29324 | 2026-05-28 | 第一作者 Junyang Wang：Beijing Jiaotong University；脚注写实习于 Tongyi AI Lab。通讯作者 Haiyang Xu 的单位为 Tongyi AI Lab, Alibaba Group | arXiv预印本 | 4 | 在可控虚拟环境里把确定性记忆变量注入合成任务，从而规定必须记什么、何时写入、何时取出，并用环境奖励做在线 RL，训练显式记忆。评测用作者新建的 Memory-World。 | 摘要写 Stamp-GUI 在 GUI 专用模型中达到 SOTA，并在 Memory-World 上设下 new high watermark。摘要没有给出 Memory-World 的准确率或成功率。 |
| EE-MCP | EE-MCP: Self-Evolving MCP-GUI Agents via Automated Environment Generation and Experience Learning | https://arxiv.org/abs/2604.09815 | 2026-04-10 | University College London（Tiantian He）。合作单位含 Huawei Noah's Ark Lab、The Chinese University of Hong Kong、Peking University | arXiv预印本 | 4 | 把 MCP 与 GUI 的选择写成混合策略学习。自动管线做环境生成与校验、轨迹收集、按缺口合成任务和过滤训练。经验库积累从轨迹对比中得到的规则，推理时使用，不需再微调。 | 三个桌面应用：蒸馏在 MCP-dominant 任务上 pass rate 77.8%（+17.8pp）；经验库在 GUI-intensive 任务上 +10.0pp。 |
| SpecOps | SpecOps: A Fully Automated AI Agent Testing Framework in Real-World GUI Environments | https://arxiv.org/abs/2603.10268 | 2026-03-10 | Purdue University（Syed Yusuf Ahmed） | ICSE 2026（https://conf.researchr.org/details/icse-2026/icse-2026-research-track/250/SpecOps-A-Fully-Automated-AI-Agent-Testing-Framework-in-Real-World-GUI-Environments ；ACM DL：https://dl.acm.org/doi/full/10.1145/3744916.3787778 ，页面写 Published 11 September 2026） | 4 | 用四个专职 LLM agent 分别做测试用例生成、环境搭建、执行和校验，在真实 GUI 环境里测基于 GUI 的 AI agent，平台包括 CLI、Web 应用和浏览器扩展。 | 五个真实 agent。识别 164 个 true bugs，F1 score 0.89。每项测试成本 under 0.73 USD，运行时间 under eight minutes。 |
| Avenir-UX | Avenir-UX: Automated UX Evaluation via Simulated Human Web Interaction with GUI Grounding | https://arxiv.org/abs/2604.09581 | 2026-02-25 | University College London（Wee Joe Tan；author note 写 Work done at UCL Nexus Labs）。代码 https://github.com/Onflow-AI/Avenir-UX | arXiv预印本 | 4 | UX 评估 agent：用 GUI grounding 而不是 DOM 解析，在真实网页上端到端操作，并按用户行为画像做 SUS、逐步 SEQ 和同步 Think Aloud，再生成 UX 报告。 | 摘要没有给出 SUS、SEQ 或任务成功率数字。 |
| OSWorld-MCP | OSWorld-MCP: Benchmarking MCP Tool Invocation In Computer-Use Agents | https://arxiv.org/abs/2510.24563 | 2025-10-28 | Peking University；Tongyi Lab, Alibaba Group（Hongrui Jia）。数据与环境：https://osworld-mcp.github.io | arXiv预印本 | 4 | 在真实环境中同时评测计算机使用 agent 的 MCP 工具调用、GUI 操作和决策。用自动代码生成加人工校验构造工具。 | 158 个工具、7 个常用应用。MCP 工具提高任务成功率的例子：OpenAI o3 在 15 步从 8.3% 到 20.4%；Claude 4 Sonnet 在 50 步从 40.1% 到 43.3%。最强模型的工具调用率仍 Only 36.3%。 |

主表行数：类别 1 为 12 行，类别 2 为 8 行，类别 3 为 10 行，类别 4 为 10 行，合计 **40**。OpenGCUA 只在文首专节，不计入这 40 行。MAI-Gym 计入类别 2。

---

## 摘要与已读正文/会议 PDF 的数字口径差异

只记录已经打开过的文本，不判断哪一处更可信。

1. **GUI-Owl-1.5（2602.16855）**。API 摘要写：56.5 on OSWorld，71.6 on AndroidWorld，48.4 on WebArena；另有 ScreenSpotPro 80.3，OSWorld-MCP 47.6，MobileWorld 46.8，GUI-Knowledge Bench 75.5。已打开的 arXiv HTML 正文另写 OSWorld-Verified、AndroidWorld、VisualWebArena 上的 56.5%、71.6%、46.6%，以及 ScreenSpot-Pro 80.3%。主表采用摘要。
2. **EvoCUA 摘要中的他引数字**。EvoCUA 摘要写 OSWorld 56.7%，并写 OpenCUA-72B 为 45.0%、UI-TARS-2 为 53.1%。UI-TARS-2 自身摘要写的是 OSWorld 47.5。OpenCUA 自身摘要写的是 OSWorld-Verified 45.0%，基准名称与 EvoCUA 摘要中的 “OSWorld” 不同。
3. **RedTeamCUA**。当前 arXiv 摘要写 Claude 4.5 Sonnet \| CUA 的端到端最高 ASR 为 60%。已打开的 ICLR 2026 proceedings PDF 正文写：Claude 4.5 Opus \| CUA 与 Claude 4.6 Opus \| CUA 的 ASR 分别为 83% 与 50%。ICLR 虚拟会议页摘要则写 “concerning ASRs of up to 50%”。三处文本不一致。主表关键数字采用当前 arXiv 摘要。

---

## 检索过但未纳入 / 无法核实

### 厂商计算机使用系统卡

- **Anthropic Claude computer use**：打开的是产品文档与 2024 年研究博客，不是 2026 年 arXiv 论文。https://www.anthropic.com/research/developing-computer-use （页面日期 Oct 22, 2024）；https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool （文档写 `computer_toolset_20260801`）。未纳入主表。
- **OpenAI Operator / Computer-Using Agent**：打开的是系统卡 PDF，不是 arXiv。https://cdn.openai.com/operator_system_card.pdf ，封面日期 January 23, 2025。本次检索没有打开到 2026 年 OpenAI computer-use 的 arXiv 论文。未纳入主表。
- **Google Gemini computer use / Project Mariner**：本次检索没有打开到对应 arXiv 论文。未纳入，不记录二手博客中的分数。

### 被点名但没有单独论文页的基准

- **OSWorld-Verified**：在 OpenCUA、Qwen-CUA、MAI-Gym、Qwen-UI-Agent 等摘要里作为基准名称出现。本次没有找到一篇标题就是 OSWorld-Verified 的独立论文，因此没有单独成行。OSWorld 初版论文早于本检索窗口，未纳入。

### 中文媒体

- 机器之心、量子位、新智元、知乎：用 OpenGCUA 与 MAI-Gym 检索，未打开到这两项的专题。知乎/新智元命中的 MobileGym 是另一项工作，未纳入本表。

### arXiv API 检索命中、但未抄摘要、未纳入主表

下列条目来自 2026-10-18 对 `export.arxiv.org` 的标题/摘要检索，只保留了 API 返回的 id、日期和标题。没有逐篇打开 abs 页面抄摘要，所以不进入主表。原因是把主表控制在约 40 篇，并优先保留用户点名的基础模型、RL/过程奖励、2026 基准，以及 GUI+MCP/CLI、记忆、世界模型和测试/UX。

- 2610.22280，2026-10-15，LEASH: Uncertainty-Aware Weak-to-Strong Escalation and Oversight for Computer-Use Agents
- 2610.20390，2026-10-14，STP-GUI: Spatially-Aware Token Pruning for Efficient Web-GUI Agents
- 2610.20100，2026-10-14，Task-State Governance: A Virtual Machine for Verifiable and Recoverable GUI Agent Execution
- 2610.19128，2026-10-13，CLASHarness: Benchmarking Multi-Agent Conflict in Computer Use via a Controllable and Verifiable Generation Pipeline
- 2610.18508，2026-10-13，Towards Safe Autonomy for Computer Use
- 2610.17928，2026-10-13，Learning How to Remember: Memory Modality Selection for GUI Agents
- 2610.19100，2026-10-13，GroundGUI: GUI Grounding by High-Quality Data and Distillation-to-Reinforcement Learning
- 2610.16778，2026-10-12，PrivacyGuard: Source-Linked Sanitization and Locally Resolvable PII References for Cloud GUI Agents
- 2610.16720，2026-10-12，Learn from Move: the Next Step for GUI Agents
- 2610.14228，2026-10-09，Latent World Action Model for GUI Agents
- 2610.14157，2026-10-09，OpenMobile-2: Building Versatile Mobile Agents with Scalable Environments and App-Native Tools
- 2610.05861，2026-10-05，Imagine to Act: High-Fidelity Data Synthesis via Image Editing World Model for Scalable GUI Agent Training
- 2610.03818，2026-10-02，Control OSWorld: An AI Control Environment for GUI Computer Use Agents
- 2610.02320，2026-10-01，DeskForge: Dense Supervision from Desktop Environments for Computer-Use Agents
- 2610.01787，2026-10-01，Not All Experience Belongs in the Weights: Component Routing for Self-Improving GUI Agents
- 2610.01215 已纳入（AutoGUIWorld）。同日未纳入的还有 2610.00948，GUI-HARVEST: Self-Improving GUI Agents through Evidence-Driven Harness Evolution
- 2609.40253，2026-09-30，ComputerSD: Online Self-Distillation from Real-Time Feedback for Computer-Use Agents
- 2609.39903，2026-09-30，OSWorld-Science: A Benchmark of Computer Use Agents for Learning and Using Scientific Software
- 2609.36939，2026-09-29，SCA: Spatial Credit Assignment for Reinforcement Learning of GUI Agents
- 2609.32750，2026-09-26，CUA-Sandbox: Efficient Environments for Computer-Use Agent Reinforcement Learning
- 2609.22000，2026-09-18，RecreationWorld: Scalable and Verifiable Environments for Hybrid Computer-Use Agents
- 2609.16635，2026-09-15，EchoPath: Execution-Level Replayable Memory for GUI Agents
- 2609.16251，2026-09-14，CADWorld: Computer-Use Benchmark for Long-Horizon Computer-Aided Design
- 2609.07712，2026-09-07，APPSim-Bench: Bridging Real-world Apps and Reproducible Evaluation for Mobile GUI Agents
- 2608.24174，2026-08-25，Task-Adaptive Rubrics for GUI Reward Modeling
- 2608.06477，2026-08-06，StepJack: Benchmarking Computer-Use Agent Safety Against Multi-Step Indirect Prompt Injection
- 2608.03327，2026-08-04，Screenshots or Tools? Eliciting Tool Use and Managing Multimodal Context in Hybrid GUI-MCP Computer-Use Agents
- 2606.31612，2026-06-30，What Memory Do GUI Agents Really Need? From Passive Records to Active Task-Driving States
- 2606.11042，2026-06-09，Workflow-GYM: Towards Long-Horizon Evaluation of Computer-use Agentic tasks in Real-World Professional Fields
- 2606.04627，2026-06-03，MIRAGE: Mobile Agents with Implicit Reasoning and Generative World Models
- 2605.29532，2026-05-28，GUITestScape: Towards Open-set Evaluation on Exploratory GUI Testing
- 2604.15093，2026-04-16，OpenMobile: Building Open Mobile Agents with Task and Trajectory Synthesis
- 2602.11724，2026-02-12，WebTestPilot: Agentic End-to-End Web Testing against Natural Language Specification by Inferring Oracles with Symbolized GUI Elements
- 2602.09082，2026-02-09，UI-Venus-1.5 Technical Report（主表收了更晚的 UI-Venus-2，未收 1.5）
- 2508.10833，2025-08-14，UI-Venus Technical Report: Building High-performance UI Agents with RFT（主表收了 UI-Venus-2，未收这一篇）

API 检索里还有一批标题含 mobile agent、但主题是无线传感网、水下追踪、交通或材料器件的条目（例如 2610.11992、2604.09587、2603.29426）。它们不是 GUI/CUA 论文，未纳入。
