# 个人研究主线与文献库（2026–2027）

这不是给软件测试组交差的共享仓库，而是面向**算法工程师求职 + 顶会论文产出**的个人研究台账。

- **实验室共享仓（组内明面交差 + 合作）**：`../testing-survey/`（对应 GitHub `ZYY0321/Testing-Survey`）
- **华为合作 UX-Agent 工程仓**：`/Users/zhangyingying/UX-Agent`（已软链至 `../ux-agent/`）
- **个人主仓库（算法主线 + 长期积累）**：本目录 `/Users/zhangyingying/Desktop/research-lab/my-research`（对应 GitHub `ZYY0321/Research-Notes`）
- **历史全量材料入口**：`../archive/`

---

## 一、核心矛盾怎么解：一套底座，两套叙事

你现在的纠结是：**实验室是软工/测试背景，但你想找算法岗（Agent / Post-training / Code & GUI Foundation Models），不想做纯传统软件测试工具，同时又想具备真正硬核的软件工程与系统架构理解。**

解法不是同时做两件毫不相干的事，而是**做同一个技术内核（Executable Environment + Verifier / World State + Agent RL / Distillation），对外拆成两套叙事**：

| 维度 | 给实验室/软工方向的叙事（SE Venue: ICSE / FSE / ASE / ISSTA） | 给算法岗简历/AI 顶会的叙事（AI Venue: ICLR / NeurIPS / ACL / ICML） |
|---|---|---|
| **研究对象** | GUI / Web / Repo 系统的**非崩溃功能缺陷、显示/UX 缺陷与设计约束违背** | GUI Agent / Coding Agent 的 **Verifier 构造、Process Reward 与自进化训练** |
| **你已有的重资产** | **华为 HarmonyOS `UX-Agent`**（5 类设备多屏态 + 视觉/ArkUI 布局树/主动滑动恢复三阶段截断检测）+ 63 个可重置 Mock App + SlideGate | OpenMobile-2 / MobileGym++ 的 11.6k SFT 轨迹、2,475 个可验证 RL 任务、DAPO 训练管线 |
| **核心科学问题** | **Active Interactive Oracle（怎么知道没崩但显示/功能错了）**：当单张静态截图存在不可消解歧义（真截断 vs 可滚动边缘）时，如何联合布局树几何约束与可逆微操作（Probing & Restore）做零误报判定 | **Scalable Verification & Credit Assignment**：稀疏 0/1 奖励下如何给长程轨迹做归因、去噪与强弱模型蒸馏 |

---

## 二、四个研究方向的取舍与 Gap 清单

详细文献与精读见：
- [01-UX与测试部融合：你在 Testing-Survey 里的切入点](tracks/01-ux-testing-and-qa.md)
- [02-硬核软工×AI：让你既懂架构又能面的算法方向](tracks/02-se-architecture-for-ai.md)
- [03-CUA与自进化：接住你手头 OpenMobile-2 的主战场](tracks/03-cua-and-self-evolution.md)
- [04-强模型教小模型（Teachability & Distillation）：热点评估与新题](tracks/04-teacher-student-distillation.md)
- [一年学习与产出路径（2026.10 – 2027.09）](roadmap-2026-2027.md)

---

## 三、历史项目全量文档归档（`archive-docs/`）

你的 4 大历史与在研项目核心文档（共 561 份 Markdown / Word / 文本与设计说明）已全部按专题归档入库，可直接跨项目检索与复用：

| 目录 | 归档内容 | 关键文档索引 |
|---|---|---|
| [`archive-docs/01-ux-agent/`](archive-docs/01-ux-agent/) | **华为 HarmonyOS 多设备 UX 检测系统 (`UX-Agent`)** | `design-specs/GUIAgent多设备UX检测系统-核心算法与代码对照详细设计说明书.md`（V2.0 视觉提案 + ArkUI 布局树静态复核 + 主动滑动与原位恢复）、`acceptance-specs/`（功能/模型性能验收说明与测试报告）、`docs/test-set/`（5 类设备单双三屏测试集与运行日志） |
| [`archive-docs/02-cua-openmobile2/`](archive-docs/02-cua-openmobile2/) | **商汤 OpenMobile-2 / MobileGym++（过程文档 + 2026-11-18 终稿/代码摘录）** | [`论文终稿_OpenMobile2/`](archive-docs/02-cua-openmobile2/论文终稿_OpenMobile2/)（正式 tex + ArXiv PDF + `A_appendix` 训练超参）、[`核心代码摘录/`](archive-docs/02-cua-openmobile2/核心代码摘录/)（Verifier/状态契约/mac-cua runtime）、会议交接与 `0907-RL对接/`；完整工程仍在仓外 `mobilegym-mock-tooluse` / `CUA/mac-cua` |
| [`archive-docs/03-slidegate-and-lingcoder/`](archive-docs/03-slidegate-and-lingcoder/) | **M集群：SlideGate 幻灯片审校、AgentV3 全链路蒸馏 & LingCoder 代码工作流** | `gui-5d025-2-full-handover/`（**2026-11-16 完整评测与训练蒸馏机交接包**：AgentV3 四层编排源码与 `State V3` 文档、1.6万条 SFT 六步清洗脚本、全轨迹 DPO 构造与排障、5.2万张图文版式蒸馏、SlideGate ICLR 2027 定稿 LaTeX 与 Rebuttal 全文）、`训练配置和启动指南.md`（LingCoder 30B MoE 32卡消融） |
| [`archive-docs/04-prior-thesis-and-reviews/`](archive-docs/04-prior-thesis-and-reviews/) | **本科毕设、RealEval/SPA-Bench 论文草稿与个人复盘** | `thesis/毕设/`（GUI Agent 架构与技术研究、开题/答辩/文献综述）、`thesis/realbench草稿/`（RealEval / MobileBench-v2 / 轨迹级非二元评测草稿）、`internship-timeline/`（商汤实习全时间线） |

> **安全与体积过滤说明**：为防止密钥泄露及仓库膨胀，已自动排除含账号密码/Token/远程连接码的 5 个敏感文件（`GITHUB账号.md`、`茶思屋ToDesk连接.md`、`给AI.md`、`2026-09-24__anon-repo-checklist.md`、`其他说明.txt`），以及 >5MB 的原始外部论文 PDF 和 `48ti附件汇总` 中的原始大图/PPTX 附件。

---

## 三（续）、求职面试全栈备战库（[`interview/`](interview/) · 2026-11 重构定稿）

面向**大模型算法 / Agent Harness / GUI CUA / Agentic RL 后训练**岗位的完整背诵与技术深挖体系（入口见 [`interview/README.md`](interview/README.md)）：
- **[`interview/00_自我介绍与四大项目全闭环/`](interview/00_自我介绍与四大项目全闭环/)**：1/2/3 分钟脱稿自我介绍 + 四大项目（AgentV3 & SlideGate、OpenMobile-1&2 / MobileGym++、macOS CUA & 鸿蒙 UX-Agent、LingCoder 30B MoE）端到端全闭环主线卡（拒绝回避式口径）。
- **[`interview/01_项目架构与蒸馏训练硬核深挖/`](interview/01_项目架构与蒸馏训练硬核深挖/)**：源码级拆解 AgentV3 编排与 Box-Agent ACP 容器、五条数据蒸馏与 SFT/全轨迹 DPO 清洗构造、SlideGate 评测与 ICLR 2027 论文、CUA/OpenMobile/UX-Agent/LingCoder 硬核细节。
- **[`interview/02_公开面经真题总表与逐题详解/`](interview/02_公开面经真题总表与逐题详解/)**：还原 20+ 场大厂真实面经题单，收录 **85 道高频真题（`Q01`–`Q85`）** 并逐题给出完整可背答案。
- **[`interview/03_算法与大模型手撕极简题库/`](interview/03_算法与大模型手撕极简题库/)**：极简四要素（标题+题面+思路+代码）排版——**35 道 C++ LeetCode 高频真题 + 12 道 PyTorch/Python 大模型与 RL（GRPO/DAPO/GSPO/DPO/AgentLoop/GQA/RoPE/OPD/LoRA/BPE）手撕题**。
- **[`interview/04_2025历史刷题资料解压精选与2026升级对照/`](interview/04_2025历史刷题资料解压精选与2026升级对照/)**：2025 历史压缩包与 `刷题.docx` 解压纯文本及 2026 演进对照表。
- **[`interview/05_无GitHub与远程ClaudeCode同步协作指南.md`](interview/05_无GitHub与远程ClaudeCode同步协作指南.md)**：无 GitHub 机器离线/SSH 克隆回传方案与远程 Claude Code 实时可视化审阅工作流。

---

## 三点五、UX-Agent 里两条和论文有关的线（2026-10-27）

阅读入口：[reports/2026-10-ux-agent/00_先看这个.md](reports/2026-10-ux-agent/00_先看这个.md)。桌面「研究方向」里有同名软链 `UX-Agent调研和实践`。

- **UX 截断检测**：文献位置在 10 月 20 日汇报（`研究方向/1020汇报/`），算法对照在 [tracks/01-ux-testing-and-qa.md](tracks/01-ux-testing-and-qa.md)，10 月 14 日工程快照在 `archive-docs/01-ux-agent/`。
- **开合探索**：10 月 22 日文献调研和 10 月 22–27 日点评试点（E0–E4）原先只在工程仓 `explore-research/`，已复制到 `reports/2026-10-ux-agent/`。Testing-Survey 仍只放论文笔记。

## 四、对话记录

我说过的话按原文记在 [`log/user-messages.md`](log/user-messages.md)，每次对话追加，新会话先读这里。

## 五、AI 协作分工约定（省钱且不翻车）

1. **机械搜索、拉表、仓库盘点、论文元数据抓取**：交给子 Agent（`grok-4.7-high-fast`），严格限制**只列事实、原文数字、链接与章节位置，禁止主观判断和选题建议**。
2. **判断论文好坏、抓 Method/Eval 的漏洞、定研究 Gap、改论文叙事与实验设计**：由主 Agent 负责把关。
