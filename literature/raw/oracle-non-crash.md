# 非崩溃类 GUI 测试 oracle 文献（子代理检索原始清单，待逐篇核实）

状态标记：已核实 = 已对照官网/DBLP 确认 venue；待核 = 只有子代理给出。

| 简称 | venue | oracle 思路 | 状态 |
|---|---|---|---|
| Barr et al. oracle survey | TSE 2015 | oracle 问题综述，分类：specified / derived / implicit / human | 已核实 |
| SetDroid | ISSTA 2021 | 改系统设置前后对比，变化即可疑 | 待核 |
| Genie | OOPSLA 2021 | 独立视图性质：插入无关操作前后 GUI 应一致 | 已核实 |
| Odin | ESEC/FSE 2022 | 多次执行行为差异找"异常值"作为 bug | 待核 |
| PBFDroid | ESEC/FSE 2023（不是 ISSTA） | 基于性质的数据操作类功能 bug | 已核实 |
| AutoConsis | ICSE-SEIP 2024 | 工业界 UI 显示一致性（同一数据多处显示） | 待核 |
| Kea | ASE 2024 | 性质测试框架（property-based），用户写性质 | 待核 |
| PDTDroid | FSE 2024 Industry | 工业落地的性质测试 | 待核 |
| OLLM | APSEC 2024 | LLM 当 oracle 判功能 bug | 待核 |
| AndroB2O | ASE 2025 | 从 bug 报告生成 oracle | 已核实（会议页） |
| VisionDroid（arXiv 名 Trident） | TSE 2025 / ICSE 2026 journal-first | MLLM 看截图判非崩溃功能 bug | 已核实 |
| iPBT | ISSTA 2026 | 交互式性质测试 | 待核 |

备注：
- Themis 是崩溃类 benchmark，不属于本表范围。
- KNighter 未核实，先不引用。
