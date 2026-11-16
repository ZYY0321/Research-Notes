# `gui-5d025-2` 评测与模型蒸馏训练机器 · 全量资产分类交接索引

> **归档日期**：2026-11-16  
> **源机器**：`/home/gui-5d025-2/zyy/`（商汤 PPT AgentV3 运行时、数据蒸馏与全轨迹 DPO、SlideGate 基准与 ICLR 2027 论文/Rebuttal 主力开发机）  
> **归档原则**：纯文本/代码/LaTeX 源码全量入库（共约 3.5 MB，已自动剔除大图/PDF/音频并完成 API Key 与凭证脱敏），**任何人在任何电脑打开本仓库，都能完整还原架构源码、数据蒸馏链路、SFT/DPO 构造细节、评测系统与论文实验，绝不存在「上下文缺失」**。

---

## 一、四类资产分层导航（原始素材 vs 项目深挖 vs 面试背题）

| 资产分层 | 仓库内路径 | 定位与内容边界 |
|---|---|---|
| **① 原始工程与实验素材（本目录）** | `archive-docs/03-slidegate-and-lingcoder/gui-5d025-2-full-handover/` | 源机器上的第一手架构文档、核心 Python 源码快照、数据蒸馏/清洗脚本、全轨迹 DPO 跑批交接、排障报告、SlideGate 论文定稿与 ICLR 2027 Rebuttal 原件 |
| **② 跟项目有关的知识点详细讲解** | `interview/01_项目架构与蒸馏训练硬核深挖/` | 将散落在几十份工程文档与源码里的细节提炼成 4 篇体系化技术精讲（AgentV3 架构、四条数据蒸馏与 SFT/DPO 管线、SlideGate 评测与论文、OpenMobile/CUA/UX-Agent/LingCoder 全闭环） |
| **③ 已重构的面试背诵资料与真题题库** | `interview/00_自我介绍与四大项目全闭环/`<br>`interview/02_公开面经真题总表与逐题详解/`<br>`interview/03_算法与大模型手撕极简题库/` | 可直接背诵的 1/2/3 分钟自我介绍、85 道 2025–2026 大厂公开面经真题总表与逐题详答、极简四要素（标题+题面+思路+代码）C++ 算法与 Python 大模型/RL 手撕题库 |
| **④ 2025 历史刷题文档解压清洗归档** | `interview/04_2025历史刷题资料解压精选与2026升级对照/` | 源自 `docs/总结/面试/` 的 5 个压缩包解压文本、`刷题.docx` 提取纯文本及 9 份基础八股笔记，附 2025→2026 知识演进对照说明 |

---

## 二、本目录（原始工程与实验素材）子目录清单

### 1. `01_agentv3_architecture_and_runtime/` —— 小浣熊 AgentV3 架构文档与核心源码快照
源自 `/home/gui-5d025-2/zyy/xhx_agent_v3_skill_v1.1_distill/`：
- **`docs/`**：
  - `agentv3.md`：`BaseLLM` → `BaseNode` → `BaseAgent` → `MainAgent / SubtaskAgent / ReflectionAgent` → `AgentV3` 完整分层编排机制。
  - `state_v3.md` & `消息列表规则与状态边界.md`：`State V3` 事件事实层（`message_records`）、资产层（`asset_index`）、控制层（`runtime_control`）与消息重编译协议。
  - `skills.md` / `tools.md` / `llms.md` / `backend.md` / `deepresearch.md` / `ppt_quickstart.md`：Skill 目录按需加载、工具注册校验、SSE 推流恢复。
  - `llm_thought_signature.md`：Cloudsway / Google 多轮工具调用中 `provider_specific_fields.reasoning_details[*].signature` 原样拼回机制。
  - `memory_system.md`：基于 `memory://user.md`、`memory://memory.md`、`date-memory/` 与 `resource_search` 的文件型长期记忆架构。
  - `change_summary_20260317.md` ～ `change_summary_20260427_agent_v3.md`：架构演进全记录。
- **`code_snapshots/`**：
  - `src__base_llm.py`、`src__base_node.py`、`src__base_agent.py`
  - `agentv3__agent_v3.py`、`agentv3__core__context_pipeline.py`、`agentv3__core__memory_update.py`、`agentv3__core__runtime_components.py` 等核心编排源码
  - `scripts__export_trace_to_openai.py`、`scripts__run_batch_and_export.py`（轨迹转 OpenAI 训练格式与保留 `reasoning_content` / signature 脚本）
  - `skills__ppt-maker__SKILL.md`、`skills__ppt-no-template-mode__SKILL.md`、`skills__ppt-template-mode__SKILL.md`（PPT 业务 SOP 工程化原文）

### 2. `02_data_distillation_sft_and_dpo/` —— 四条数据蒸馏、SFT 清洗与全轨迹 DPO 管线
- **`sft_data_quality_reports/` & `sft_repair_scripts/`**（源自 `xhx_agent_v3_skill_v1.1_distill/docs/ppt_sft_data_quality/`）：
  - 报告 `01`～`05`：完整记录 16,274 条 Claude Opus 4.7 蒸馏轨迹中发现的三大底层问题（① 28% 大纲/风格子任务因运行时计数器 bug 被静默丢弃；② 0629 批次 42% 混入残缺 system prompt；③ `write_file` 缺 `<file_action>` 达 65–89%，末轮悬空 `<file_action>` 达 12.5–26.3% 导致模型学出“不发”或“发完即停”），以及 6 步 Qwen 自动修复管线（产出无模板 9,901 + 模板 6,373 条，C1/C2 100% 合规）。
  - 附全部修复与质检源码：`repair_file_action.py`、`fix_c5_targets.py`、`rewrite_ask_user.py`、`qc_file_action.py` 等。
- **`full_trajectory_dpo_0818/`**（源自 `xhx_agent_v3_skill_v1.1_distill/评测任务文档/0818新蒸馏任务/`）：
  - `0818_蒸馏分支交接与开跑.md` & `0819_今晚端点将关_全轨迹DPO现状交接.md`、`会议纪要.txt`、`基础信息.txt`：首次全轨迹 DPO 构造实录（正样本 accept = Opus 4.7 全量轨迹 1,879 主 query / 10,975 行含子任务；负样本 reject = SenseNova Flash 284B v14 / Flash-Lite 同题重跑；含客户端 128 并发 `/tmp` FD 耗尽雪崩复盘、波次限流 `SANDBOX_CREATE_WAVE_SIZE=16`、A+C 主模型与沙盒内 HTML 端点对齐、`deck_html_pages>0` 质量门禁）。
- **`ppt_image_and_query_distill/`**（源自 `/home/gui-5d025-2/zyy/benchmark/docs/`）：
  - `0615_数据汇总_PPT图像蒸馏.md`、`附件一_Design_Prompt数据来源说明.md`、`附件二_标准模式Query合成管线说明.md`、`0617_端午数据扩充方案.md`、`0623_数据处理交接手册.md`、`0707_数据总清单.md`：51,981 张 PPT 页面蒸馏全流程（创意模式 18,197 张原样回流重绘 + 标准模式 36,573 页纯内容耦合 L2 19,150→495 蒸馏设计卡与 L3 300 精拆设计卡，经 Claude 5 选 1 择优合成英文生图 Prompt → `gpt-image-2` → G6 13 类规则前置+LLM 兜底版式分类）。
- **`code_distill_deepseek/`**（源自 `/home/gui-5d025-2/zyy/distill_proxy/distilled.py`）：
  - `distilled_deepseek_v3_sanitized.py`：AST 解析第三方库依赖 → 剥离原回复构造种子 → 多模型轮询调用 DeepSeek V3.2（禁思考模式、严格代码块抽取）的并发断点续传蒸馏器。

### 3. `03_ppt_eval_handover_and_diagnostics/` —— 工业级 Agent 评测体系、分层排障与真实轨迹样本
- **`ppt_eval_handover/`**（源自 `/home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/`）：
  - `[260911]PPT生成与自动化评测技术报告.md`（153 KB 完整技术白皮书）、`[260915]离职交接总览.md`、`[260915]评测管线升级方向与开放问题.md`（E1–E18 共 18 项验证实验）、`[260920]sensenova-flash-284b-vision-v16-step400-dpo-v2_tpl失败原因深度分析.md`（DSML 文本泄漏与 JSON 自救死循环量化归因）、`[260921]平台全局评分锁问题与建议.md` 等全套文档。
- **`benchmark_diagnostics/`**（源自 `/home/gui-5d025-2/zyy/benchmark/docs/` & `/home/gui-5d025-2/hzw/agentcompass/`）：
  - `0708_机器打分可靠性排查与内容分修复.md`（`content_eval_dynamic_items==0` 静默降级导致“假 DPO 退化”的完整侦破与重判数据表）、`0708_生成失败根因分析_自家模型.md`、`0724_评测维度与提示词说明.md`、`BoxAgent_PPT_BENCH_GUIDE.md`（AgentCompass / Box-Agent 对比）。
- **`trajectory_walkthrough/`**：
  - 真实线上题目轨迹 `prod_26016eba` 的元数据、时间线与 `message_records` 逐类词典，支撑面试现场手读轨迹。

### 4. `04_slidegate_iclr2027_and_rebuttal/` —— SlideGate 顶会论文定稿、LaTeX 源码与 Rebuttal
源自 `/home/gui-5d025-2/zyy/benchmark/docs/0906论文迭代/最终正式稿/`：
- **`paper_final/` & `overleaf_tex/`**：SlideGate ICLR 2027 投稿中英文完整正文與全套 `.tex` / `.bib` 源码（40 任务 × 6 商业系统 = 240 份文稿，2,191 条冻结核查项，指令/内容/视觉三维可交付性评测）。
- **`rebuttal_202611/`**：2026 年 11 月最新审稿意见原文、`SlideGate Rebuttal完整版_v3_20261113.md`、`OpenReview粘贴版_20261113.md`、`rebuttal_数字验算表_20261113.md`、`标签有效性证据_20261113.md`。

### 5. `05_openmobile_and_previous_interview_research/` —— OpenMobile 专题笔记与目标岗位面经源档
- `research_interest_notes/`：本机整理的 `0420_OpenMobile论文解读.md`、`OpenMobile_V2_协作准备.md`、`mock_app_research_note.md` 等（与仓库 `archive-docs/02-cua-openmobile2/` 互补）。
- `jd_and_mianjing_raw/`：阿里 Personal Agent Harness 岗位 JD 原文存档、牛客/面栈/小红书/面试库公开面经原始调研链接表。
