====================3.24版本====================
1. 输入与整体流程
步骤
触发条件
主要做什么
输出/产物
Step 0 报告预处理
只有当目录里有 report.md 或 report.json（优先 .md）时
从标准报告里抽取 key_topics / key_facts（用于后续“内容完整性/真实性回退”）
debug/00_report_preprocessor.json（debug 开启时）
Step 1 单页评估（PageEvaluator）
总是
打分：Hard Check + 细粒度美学 + 高层次美学；若有 report，则额外做真实性核查
page_results[]、summary（并发逐页）
Step 2 全套评估（DeckEvaluator）
总是
结构完整性 + 跨页视觉一致性 +（可选）内容完整性（coverage）
deck_eval 三部分结果

Step 3 修复闭环（RepairLoop）
暂时无
用模型根据评估结果改输出（当前 repo 只配置了少量轮次）
修复后的新结果（视实现而定）

---
2. 页级（PageEvaluator）到底测哪些指标
指标模块
维度
分数含义
Hard Check
4项（boundary_crop / occlusion_overlap / content_integrity / image_quality）
通过=1、不通过=0（最终聚合是 pass_rate/均值）

细粒度美学（Aes Fine）
6项
每项 0/1/2（差/轻微/好）先归一化再均值
高层次美学（Aes High）
只输出一个 1~5 分
单页 1~5 分再归一化到 0~1 后均值
（可选）真实性核查（Truthfulness）
按页做
覆盖率：有支撑的陈述数 / 总可检验陈述数；无可检验内容则该页 total=0
[2026-3-5]PPT标注标准 - 2026030 10项维度详情见

---
4. 全套 Deck（DeckEvaluator）测哪些指标、怎么计分

模块
输出结构
重点看什么
结构完整性（Structural Completeness）
structural_completeness: {score, issues, ...}
封面/目录/主体/总结等结构是否齐全、页数分配是否合理
跨页视觉一致性（Visual Consistency）
visual_consistency: {score, issues, color_consistent, font_consistent, style_consistent, ...}
配色/字体/版式跨页是否统一，异常页是否存在
内容完整性（Content Completeness，可选）
topic_coverage, fact_coverage, completeness_score
报告抽取的 topics/facts 是否在 PPT 中被覆盖（coverage / missing）
deck_score 融合（query+report）
deck_score = 结构*0.40 + 一致性*0.35 + 完整性*0.25
把三块综合成 0~1 的总分