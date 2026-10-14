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

## 三、AI 协作分工约定（省钱且不翻车）

1. **机械搜索、拉表、仓库盘点、论文元数据抓取**：交给子 Agent（`grok-4.7-high-fast`），严格限制**只列事实、原文数字、链接与章节位置，禁止主观判断和选题建议**。
2. **判断论文好坏、抓 Method/Eval 的漏洞、定研究 Gap、改论文叙事与实验设计**：由主 Agent 负责把关。
