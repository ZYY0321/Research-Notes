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
| [`archive-docs/02-cua-openmobile2/`](archive-docs/02-cua-openmobile2/) | **商汤 OpenMobile-2 / MobileGym++ (`cua过程文档` + `milestone文档`)** | `cua-process/`（63 Mock App 架构、333 Tools、215 锁定 Benchmark、Qwen-9B vs Gemini 3.1 `GUI-only vs Hybrid` 评测、弱探索+强接管数据合成、DAPO/RL 方案）、`milestone/`（组会周报、研究路线图、工具演进与论文写作计划） |
| [`archive-docs/03-slidegate-and-lingcoder/`](archive-docs/03-slidegate-and-lingcoder/) | **M集群：SlideGate 幻灯片审校 & LingCoder 代码工作流** | `M集群/SlideGate_Survey.md`（PPT 生成与视觉审校综述）、`M集群/评测/`（DeckBench 指标设计、50 题构造、硬门控消融）、`M集群/给学姐/`（LingCoder 代码模型工作流对比与评测建议） |
| [`archive-docs/04-prior-thesis-and-reviews/`](archive-docs/04-prior-thesis-and-reviews/) | **本科毕设、RealEval/SPA-Bench 论文草稿与个人复盘** | `thesis/毕设/`（GUI Agent 架构与技术研究、开题/答辩/文献综述）、`thesis/realbench草稿/`（RealEval / MobileBench-v2 / 轨迹级非二元评测草稿）、`internship-timeline/`（商汤实习全时间线） |

> **安全与体积过滤说明**：为防止密钥泄露及仓库膨胀，已自动排除含账号密码/Token/远程连接码的 5 个敏感文件（`GITHUB账号.md`、`茶思屋ToDesk连接.md`、`给AI.md`、`2026-09-24__anon-repo-checklist.md`、`其他说明.txt`），以及 >5MB 的原始外部论文 PDF 和 `48ti附件汇总` 中的原始大图/PPTX 附件。

---

## 四、对话记录

我说过的话按原文记在 [`log/user-messages.md`](log/user-messages.md)，每次对话追加，新会话先读这里。

## 五、AI 协作分工约定（省钱且不翻车）

1. **机械搜索、拉表、仓库盘点、论文元数据抓取**：交给子 Agent（`grok-4.7-high-fast`），严格限制**只列事实、原文数字、链接与章节位置，禁止主观判断和选题建议**。
2. **判断论文好坏、抓 Method/Eval 的漏洞、定研究 Gap、改论文叙事与实验设计**：由主 Agent 负责把关。
