# 个人求职面试全栈备战库（2026 重构定稿版）

> **重构说明（针对此前材料痛点的彻底革新）**：
> 1. **跳出单一 PPT 评测视角，拉齐全局视野与全项目闭环掌控**：不再用“这部分不是我主责所以回避”的被动话术。简历上的 **四大项目（① 小浣熊 AgentV3 + 轨迹/图文蒸馏 + 全轨迹 DPO + SlideGate ICLR 2027；② OpenMobile-1&2 / MobileGym++ 63 应用环境 + 333 MCP 工具 + Store Verifier + 1.16万 SFT + 2,475 题 DAPO RL；③ 桌面 macOS CUA 驱动解耦与 AX 树诊断 + 华为鸿蒙 UX-Agent 三阶段主动滑动验证；④ LingCoder 30B MoE 285万代码标签与 32 卡集群训练）** 从架构、数据、训练到评测每一个技术细节全部正面打通。
> 2. **真题 100% 列表化 + 85 道真题逐题详答**：将牛客、面栈、小红书、面试库搜集到的阿里 Accio、阿里国际、淘天、月之暗面、字节、华为、OPPO 等公开面经还原为场次映射表与 `Q01`–`Q85` 独立清单，**每一道题都有可直接背诵的硬核解答**。
> 3. **算法与手撕彻底去冗余**：严格采用 **「标题 + 题目描述 + 一段核心思路 + 一段标准代码」** 四要素极简排版（35 道 C++ LeetCode 高频真题 + 12 道 Python 大模型/RL/Agent 手撕真题）。
> 4. **原始工程证据全归档**：源机器（`gui-5d025-2`）上的架构文档、核心代码快照、蒸馏与清洗脚本、排障报告、SlideGate 论文与 Rebuttal 全量分类存入 [`../archive-docs/03-slidegate-and-lingcoder/gui-5d025-2-full-handover/`](../archive-docs/03-slidegate-and-lingcoder/gui-5d025-2-full-handover/)，任何人打开本仓库都能查到完整实现依据。

---

## 目录导览与背诵顺序建议

| 优先级 | 目录 / 文件 | 核心内容 |
|---|---|---|
| **Step 0 · 必背开场** | [`00_自我介绍与四大项目全闭环/01_自我介绍_1min_2min_3min可直接背版.md`](00_自我介绍与四大项目全闭环/01_自我介绍_1min_2min_3min可直接背版.md)<br>[`00_自我介绍与四大项目全闭环/02_四大项目端到端闭环主线卡（全链路掌控版）.md`](00_自我介绍与四大项目全闭环/02_四大项目端到端闭环主线卡（全链路掌控版）.md) | 1 / 2 / 3 分钟三档脱稿自我介绍 + 四大项目全链路（架构/数据蒸馏/SFT/DPO/RL/评测）一图一卡总纲 |
| **Step 1 · 项目硬核深挖** | [`01_项目架构与蒸馏训练硬核深挖/01_小浣熊AgentV3与Skills运行时架构全解.md`](01_项目架构与蒸馏训练硬核深挖/01_小浣熊AgentV3与Skills运行时架构全解.md)<br>[`01_项目架构与蒸馏训练硬核深挖/02_数据蒸馏与SFT_DPO构造全链路详解.md`](01_项目架构与蒸馏训练硬核深挖/02_数据蒸馏与SFT_DPO构造全链路详解.md)<br>[`01_项目架构与蒸馏训练硬核深挖/03_SlideGate评测体系与ICLR2027论文全解.md`](01_项目架构与蒸馏训练硬核深挖/03_SlideGate评测体系与ICLR2027论文全解.md)<br>[`01_项目架构与蒸馏训练硬核深挖/04_GUI_Agent_CUA_OpenMobile_UXAgent_LingCoder全解.md`](01_项目架构与蒸馏训练硬核深挖/04_GUI_Agent_CUA_OpenMobile_UXAgent_LingCoder全解.md) | 源码级讲透：AgentV3 四层编排与 `State V3`、Box-Agent ACP 容器与 OE/RR 效率指标、五条蒸馏与 SFT 六步清洗管线、全轨迹 DPO、SlideGate 论文与“假 DPO 退化”排障、macOS CUA AX 树诊断 + OpenMobile-1&2 + 鸿蒙 UX-Agent + LingCoder MoE |
| **Step 2 · 85道真题全解** | [`02_公开面经真题总表与逐题详解/00_真题总目录与编号清单（85题全覆盖）.md`](02_公开面经真题总表与逐题详解/00_真题总目录与编号清单（85题全覆盖）.md)<br>[`01_Accio与Agent后训练专场真题详解（Q01-Q18）.md`](02_公开面经真题总表与逐题详解/01_Accio与Agent后训练专场真题详解（Q01-Q18）.md)<br>[`02_Agent_Harness_Skill_Memory_Context真题详解（Q19-Q36）.md`](02_公开面经真题总表与逐题详解/02_Agent_Harness_Skill_Memory_Context真题详解（Q19-Q36）.md)<br>[`03_强化学习SFT_DPO_PPO_GRPO_DAPO_GSPO与训推一致真题详解（Q37-Q58）.md`](02_公开面经真题总表与逐题详解/03_强化学习SFT_DPO_PPO_GRPO_DAPO_GSPO与训推一致真题详解（Q37-Q58）.md)<br>[`04_GUI_Agent与CUA专场真题详解（Q59-Q72）.md`](02_公开面经真题总表与逐题详解/04_GUI_Agent与CUA专场真题详解（Q59-Q72）.md)<br>[`05_Transformer底座_MLA_MoE_推理优化_RAG真题详解（Q73-Q85）.md`](02_公开面经真题总表与逐题详解/05_Transformer底座_MLA_MoE_推理优化_RAG真题详解（Q73-Q85）.md) | 按真实场次还原题单 + 85 道高频真题逐题标准答案（含蒸馏被封、`pass@k` 收敛、Tool Loss Mask、Token-in/out、DAPO/GSPO、MoE 训推不一致、GUI Grounding、`Tool Hurts`、MLA 解耦 RoPE、RAG 幻觉定位等） |
| **Step 3 · 极简手撕默写** | [`03_算法与大模型手撕极简题库/01_LeetCode高频手撕35题_极简C++版.md`](03_算法与大模型手撕极简题库/01_LeetCode高频手撕35题_极简C++版.md)<br>[`03_算法与大模型手撕极简题库/02_大模型与RL手撕12题_极简Python版.md`](03_算法与大模型手撕极简题库/02_大模型与RL手撕12题_极简Python版.md) | 纯净四要素排版：35 道 C++ 算法题 + 12 道 PyTorch/Python 手撕（GRPO、DAPO、GSPO、DPO、AgentLoop、GQA+KVCache、RoPE/RMSNorm/SwiGLU、SFT Mask、OPD、LoRA、Online Softmax、BPE、GAE） |
| **Step 4 · 历史笔记参考** | [`04_2025历史刷题资料解压精选与2026升级对照/`](04_2025历史刷题资料解压精选与2026升级对照/) | 2025 年压缩包与 Word 刷题文档完整解压纯文本及 2026 知识升级索引表 |
| **工程工具箱** | [`05_无GitHub与远程ClaudeCode同步协作指南.md`](05_无GitHub与远程ClaudeCode同步协作指南.md) | 无 GitHub 环境克隆/修改回传方案（`ssh://` 直拉、`git bundle`、反向隧道、双远端镜像）+ 远程 Claude Code 实时可视化审阅指南 |
