# 目标岗位存档：阿里 · 大模型算法实习生（Personal Agent Harness）

> 存档日期：2026-11-14  
> 用途：后续所有面试材料 / 轨迹讲义 / Fable 出题，**默认贴合本 JD**。  
> 来源：BOSS 直聘截图（已复制到 `screenshots/`）

## 一句话

依托 Accio Work，做 B2B 外贸多渠道沟通的 Personal Agent，并探索支撑其持续运行的 **Agent Harness**（长期记忆、商家 Skills、主动服务、前后端 Agent 协作）。

## 基本信息

| 项 | 内容 |
|----|------|
| 职位 | 大模型算法实习生 |
| 公司 | 阿里巴巴（中国）有限公司 |
| 地点 | 杭州滨江区阿里巴巴滨江园区 3 栋 |
| 课题名 | 基于 Accio Work 的外贸沟通 Personal Agent Harness 研发 |

截图：

- `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/12_目标岗位_阿里PersonalAgent/screenshots/01_课题与目标.jpg`
- `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/12_目标岗位_阿里PersonalAgent/screenshots/02_工作内容与职位要求.jpg`
- `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/12_目标岗位_阿里PersonalAgent/screenshots/03_加分项.jpg`

## JD 原文要点（从截图整理）

### 项目目标

- 跨 Web 多渠道外贸沟通的 Personal Agent  
- 能力：长期记忆、商家专属技能、主动服务  
- 研究支撑持续运行的 Agent Harness  
- 前台 Agent：与商家交互、理解目标、管理知识与接待策略、关键决策共创  
- 后台 Agent：按商家 Skills 执行买家接待与商机跟进，结果与问题回流商家  
- 目标指标：沟通质量、接待效率、订单转化  

### 工作内容（4 条）

1. **Harness**：Personal/Super Agent 架构与执行机制；任务规划、工具调用、异步执行、状态恢复；前后台协作与商机识别  
2. **Skill**：从 SOP / 历史轨迹 / 人类反馈抽取可复用商家技能（报价、物流、下单等）；生成、组合调用、评测、迭代  
3. **Memory / Context**：抽取、检索、更新、失效；跨会话跨渠道上下文组织；一致性与个性化  
4. **评测闭环**：真实外贸沟通 case 建评测集；**分析执行轨迹与失败原因**；实验验证 Harness/Skill/Memory；优化完成率、时延、调用成本  

### 职位要求

- 硕博在读，计科/AI 等相关；连续实习 ≥ 4 个月  
- 大模型原理；熟悉 Agent 任务规划、工具调用、RAG 或上下文管理之一  

### 加分项（重点准备）

1. Agent Harness / 多智能体协作 / 长期记忆 / Skill 体系 / **Agent 评测** 项目经验  
2. 熟悉 SFT、RLHF 或 Agentic RL；训练环境、奖励设计、**执行轨迹优化**  
3. 高质量开源 / 论文复现 / 研究成果，能讲清完整实现与实验结论  

## 和你现有经历的贴合地图（后续分析默认用这张表）

| JD 能力 | 你可讲的项目锚点 | 准备重点 |
|---------|------------------|----------|
| Agent Harness | xhx AgentV3：BaseNode/BaseAgent、工具循环、超时/沙盒、状态恢复 | 用真实 `result.jsonl` 讲清一轮执行 |
| 工具调用 / 规划 | Skills 阶段、`create_subtask`、结构化 tool call vs 文本伪调用 | 早停失败 taxonomy |
| Skill 体系 | ppt-maker / template-mode Skill；从流程文档驱动行为 | 类比「商家 SOP → Skill」 |
| 多智能体 | 主 Agent + SubtaskAgent；前后台分工可类比 | 别夸大成完整 multi-agent 产品 |
| Memory / Context | 上下文裁剪、确认后 system_context 注入、批测自动确认 | 诚实：长期记忆不是你主责，但懂上下文组织痛点 |
| **Agent 评测** | 47×2 题集、轨迹分析、成功率 vs 质量分、内容分虚高修复 | **最强差异化，面试主叙事** |
| 轨迹与失败归因 | `message_records`、terminal_class、分层归因手册 | 当场打开一条轨迹走读 |
| SFT / DPO 等 | 模型名解读、评测反哺训练、假 DPO 案例 | 加分项 2；讲清评测如何服务训练 |
| 论文 / 实验 | SlideGate / 维度验证 / 消融 | 加分项 3 |

详细准备清单见：  
`/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/12_目标岗位_阿里PersonalAgent/岗位贴合与准备清单.md`

## 飞宝按本岗重写的材料（优先背）

| 文件 | 内容 |
|------|------|
| `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/12_目标岗位_阿里PersonalAgent/07_阿里岗_面试题库30题.md` | 30 题，按 Harness/Skill/Memory/评测/训练分块，答案强制「JD点→PPT证据→外贸映射」 |
| `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/12_目标岗位_阿里PersonalAgent/08_阿里岗_口述与故事卡.md` | 2/5/12 分钟口述 + 加分故事卡 + 薄弱点答法 |
| `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/12_目标岗位_阿里PersonalAgent/09_近期公开面经调研_牛客面栈.md` | **近期牛客/面栈/小红书真题分布：是否手撕、八股清单、Accio 专场、准备矩阵** |
| `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/12_目标岗位_阿里PersonalAgent/10_备考总规划_按面经定制.md` | **按面经定制的四周备考节奏 + 每日剂量 + 必会清单** |
| `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/12_目标岗位_阿里PersonalAgent/背题分批/README.md` | **可直接背：手撕 C++ + 八股分批共 8 份（Fable）** |
| `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/12_目标岗位_阿里PersonalAgent/13_B站干货面经听力清单.md` | **B 站非零基础干货听力清单（含评论区判断）** |
