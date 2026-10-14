# 非测试类软工文献表：架构 / 技术债 / 代码评审 / 代码质量 / 供应链 / 鸿蒙迁移（2024–2026）

列同 `gui-testing-table.md`。子代理逐篇打开原文；DBLP 被拦截，venue 以会议日程页或论文页眉为准，UNVERIFIED 已标出。

| 论文 | 年份·venue | 第一作者机构 | 动机（原文） | 贡献（要点） | 方法 | 关键数字 | 作者自认局限 | 一段话叙事 |
|---|---|---|---|---|---|---|---|---|
| **PairSmell** | 2025 ICSE | 南京大学 | 重模块化 "require extensive modifications"，问题 "too coarse to guide refactoring" | 新的架构坏味（文件对层面）；20 项目实证 | 4 个模块化工具一致结果当"应有关系"，偏离即坏味 | 26 万个坏味；错误分离的文件对多 190% 共变 | 可能误报；只开源项目 | 架构问题细到文件对 |
| **SemRef** | 2026 ICSE | 南洋理工 | 恢复大系统架构 "may require hundreds of hours from an expert" | 首个 LLM 修正架构恢复结果的框架 | 依赖分析找放错的文件 → LLM 核对 → 分层 → 迭代 | 10 个工具 × 9 项目，准确率 +17.7%~43.4% | 幻觉无法消除；只 9 个项目 | 不从头恢复，修正已有结果 |
| **ATD 生命周期** | 2025 ICSA | 格罗宁根大学 | SATD 中 ATD 仅 0.13%，且一半标错 | 用依赖指标追踪架构债引入与偿还 | git blame 定时刻；FAN-IN/OUT 对比 | 18 ATD vs 18 非 ATD；效应量可忽略 | 数据集小 | 架构债很难量化 |
| **架构侵蚀违规症状识别** | 2025 TOSEM（UNVERIFIED） | 武汉大学 | 团队需 "understand early enough the symptoms of erosion" | 首个从代码评审评论自动识别架构违规 | 15 个 ML + 4 个 DL 分类器；回访开发者 | SVM+word2vec F1 0.779（另一处 0.808） | 闭源项目难泛化 | 从评审讨论里发现架构侵蚀 |
| **LLM 生成设计理由** | 2026 TOSEM | 武汉大学 | 设计理由 "often inadequately documented" | 100 个架构问题数据集；三种提示 + 多 agent | 对照专家论证算 P/R | P 约 0.27，R 0.63–0.72；多出论点 65–69% 有用 | 设计理由没有唯一答案；缺项目上下文 | LLM 能补设计理由但不准 |
| **DL 代码评审：范式转变还是双刃剑** | 2025 ICSE | USI | "little is known about the actual impact" | 29 人对照实验 | 注入缺陷 × 三种处理（人工/LLM/完美自动） | LLM 意见 89% 被保留；**不多发现严重问题，也不省时间** | 统计功效不足 | **自动评审会带偏人** |
| **ChatGPT 代码精炼** | 2024 ICSE | 天津大学 | ChatGPT 在评审任务 "how well… is still unclear" | 首个实证；新数据集 | 对比 CodeReviewer | EM 22.78 vs 15.50 | 提示可能非最优 | 按评论改代码的实证 |
| **Intention is All You Need** | 2025 ICSE | 天津大学 | 难在 "accurately understanding reviewers' intents" | 评论→意图→代码两步 | 规则 + LLM 意图分类 | 意图抽取 79%；修改正确最高 66% | 只一个数据集 | 先理解意图再改 |
| **CORE** | 2024 FSE | 微软印度研究院 | 开发者需 "spend extra efforts to revise their code" 应对静态分析告警 | 提议 LLM + 静态分析过滤 + 排序 LLM | 按工具文档改 → 再检查 → 评分 | Python 59.2% 修改通过工具+人工 | 训练数据可能见过 | 静态分析器当验证器 |
| **ChatGPT 生成代码的质量问题** | 2024 TOSEM | Monash | 生成代码的 "reliability and quality… remain unexplored" | 2,033 题实证；自修复能力 | 测试 + Pylint/PMD 等 + 反馈自修 | 47% 有可维护性问题；新题性能降至 1/5 | 只 LeetCode | **过测试 ≠ 代码质量好** |
| **Pinning Is Futile** | 2025 FSE | CMU | 钉版本是否有安全收益 "remains controversial" | 首个量化证据；生态级干预 | npm 历史反事实模拟 | 依赖 ≥498 时钉版本有害（26% 仓库）；钉 100 个关键包恶意传播降约 30% | 模拟与历史有偏差 | 局部决策解决不了生态问题 |
| **Pinning or Floating** | 2025 ASE | 北卡州立 | 不同版本约束的风险 "is unknown" | 三生态生存分析 | Cox 模型 | floating-minor 漏洞风险降 43% | 不分析漏洞可达性 | 浮动约束 + lockfile 更好 |
| **PeerSpin** | 2025 ICSE | 浙江大学 | peer 依赖冲突让 npm "infinite loops"，被忽视 | 首个研究 + 检测工具 | 观察目录树节点替换 | 0 误报漏报；快 14 倍；28 个确认 | 假设从零解析 | 理解算法后精确检测 |
| **Python 包级弃用** | 2025 ICSE | 港中文（深圳） | 大量包 "in poor maintenance" | 实证 + 10.6 万包数据集 | 元数据 + 问卷 | 75.4% 维护者不愿声明；89.5% 用户想被通知 | 未含 API 级弃用 | 弃用机制缺失 |
| **CuRev** | 2025 MSR | 蒙特利尔大学 | 评审数据集 "noisy and unrefined" | 质量评估框架 + LLM 清洗 | Llama-70B 当裁判改写过滤 | 生成评论 BLEU +46% | LLM 裁判可能不准 | 数据质量决定上限 |
| **Too Noisy To Learn** | 2025 MSR | 墨尔本大学 | 清洗后仍有大量 "vague or non-actionable feedback" | LLM 清洗评审数据 | 只用有效评论微调 | 有效比例 64%→85%；BLEU-4 +13% | 有效≠正确 | 数据少但干净更好 |
| **ArkAdapter** | 2025 ISSTA | 东北大学 / 北航 / 港科大（个人单位 UNVERIFIED） | "LLMs have limited exposure to ArkTS code" | 项目级 TS/JS→ArkTS 适配；209 对基准 | 编译器定位 + 规则知识库 + 依赖排序 | 79 个库中 70 个通过并上架 OHPM | LLM 随机性 | **鸿蒙生态工程** |

## 读出的脉络（对你"学架构、建壁垒"的意义）
1. **架构研究的核心问题是"实际结构偏离了应有结构"**：PairSmell、SemRef、侵蚀症状、ATD 都在回答"怎么知道架构坏了"。这和测试 oracle 是同一类问题——你的 verifier 思维可以直接迁移。
2. **LLM 进入软工的普遍模式 = 生成 + 确定性检查器过滤**：CORE（静态分析器）、ArkAdapter（编译器）、SemRef（依赖分析）。与 AI 方向的"生成 + verifier"完全一致。
3. **反直觉的人因证据**：自动评审不省时间、不多发现严重问题（ICSE 2025）；生成代码过测试但 47% 有可维护性问题（TOSEM 2024）。这是"代码质量"方向可以做 AI 评测的空间。
4. **学习建议对应**：读 PairSmell + SemRef 理解"模块边界"；读 Pinning 两篇理解"依赖与生态"；这比读设计模式书更接近真实工程判断。
