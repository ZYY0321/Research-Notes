# PPT 评测管线：评分标准评价与 rubric 扩展建议

> 用于基模团队后续产出 rubric 的参考。**这份文档定位**：结合本轮机评 6 模型 + 人评 5 组对比的差异，评价当前评测管线的评分标准，指出 3 类关键空白维度，给出具体的 rubric 扩展建议。

---

## 一、当前评测管线的评分标准（现状 snapshot）

### 主分组成（industry_v2 · content_evaluator）

**overall_score = 0.30 × page + 0.30 × deck + 0.40 × content**（大致权重，见 `benchmark/aggregator.py`）

**三层展开**：

| 层 | 维度 | 判分方式 | 输出范围 |
|---|---|---|---|
| **page（单页）** | hard_check（4项）| 二值 pass/fail | 0/1 |
| | aesthetic_fine（6项 layout/font/spacing/text 等）| 0/1/2 三档 | 0/0.5/1 |
| | aesthetic_high（3项 hierarchy/language/impression）| 1-10 整数 | 归一化 0-1 |
| **deck（整套）** | structural_completeness | 1-5 整数 | 归一化 0-1 |
| | visual_consistency | 1-5 整数 | 归一化 0-1 |
| | content_quality | 1-5 整数 | 归一化 0-1 |
| **content（内容）** | core_checklist（6 项 × 3 层 L0/L1/L2）| 二值 pass/fail | 0/1 |
| | dynamic_checklist（6-10 项 × 3 层）| 二值 pass/fail | 0/1 |
| | faithfulness（三值 supported/derived/unsupported）| 三值 | 归一化 0-1 |

---

## 二、评价：当前评分标准的三类关键空白维度

**结论先说**：现有 rubric 在**单页视觉细粒度**（对齐/间距/字号）和**内容存在性**（有没有覆盖该讲的点）这两个维度分辨力已经不错，但在三类维度上有系统性失明：

### 空白维度 1：内容-呈现匹配度（Content-Presentation Fit）

**现象**：CSFT 在人评里被指出"跨风格适配差"——**游戏/生日会/品牌类的题，视觉呈现没有"那味儿"**。同样是"深蓝商务风"配色，做金融汇报是对的，做游戏 PPT 就出戏。机评的 aes_high（整体观感）给的分和做金融汇报几乎一样，因为它**只评页面本身是否精致，不评"页面呈现是否匹配题目类型"**。

**为什么当前 rubric 抓不到**：
- `aesthetic_high` 是"页面精致度评分"，不带 query 上下文
- `dynamic_checklist` 里虽然有场景相关项（如"炫酷跑车风格"），但只判"是否体现了黑蓝机甲配色"这种存在性，不判"这个配色在这个题上是否合适"
- **本质上缺一个 rubric 维度：视觉主题选择的合理性**

**建议新增 rubric 项**（VLM 判分）：
```
维度：主题匹配度（Theme Fit）
问题：这份 PPT 的视觉主题（配色/字体/装饰/图表风格）与题目类型的匹配度如何？
评分（1-5）：
  5 = 完全匹配。看到第一页就能感觉到"这就是XX类型 PPT 的样子"
  4 = 大致匹配，个别地方违和（例：给游戏做深蓝商务色但插画选对了）
  3 = 中性匹配。配色不出错但也不出彩，看不出题目类型
  2 = 有明显违和（例：给儿童教育 PPT 用深黑金主题）
  1 = 完全错位（例：给生日祝福用财务报表配色）
参考例：
  游戏 PPT → 应该有"电竞感/科幻感/漫画感"其中之一
  金融汇报 → 应该有"专业稳重/数据充实/严肃感"
  儿童教育 → 应该有"亮色/大字/图形化"
  生日祝福 → 应该有"暖色/装饰/情感感"
```

### 空白维度 2：图表能力（Chart Capability）

**现象**：人评发现"**CSFT 短稿几乎没图；数据分析类内容 CSFT 图表种类少；DPO v2 tpl 图表能力显著强**"。机评的 `hard_check.image_quality` 只判"图片是否模糊拉伸"，`content_checklist` 里可能有"是否有图表"但只是二值 pass/fail。**没有维度评价图表的种类丰富度、图表与数据的贴合度、图表信息传达效率**。

**为什么当前 rubric 抓不到**：
- image_quality 是二值（好/坏），只看单张图质量
- 没有 deck 级"图表多样性"评分
- 没评"图表 vs 纯文字堆积"的比例

**建议新增 rubric 项**（VLM + 规则组合）：
```
维度 A：图表多样性（Chart Diversity）
问题：这份 PPT 里出现了几种不同类型的图表（柱/折/饼/雷达/漏斗/时间轴/桑基/思维导图 等）？
评分：直接数不同类型数量，映射到 1-5
  5 = ≥ 4 种类型
  4 = 3 种
  3 = 2 种
  2 = 1 种
  1 = 0 种（纯文字/纯色块/占位）

维度 B：图表使用适宜度（Chart Appropriateness）
问题：数据类内容是否用图表呈现（而非纯文字堆积）？纯文字类内容是否避免了强行加图表？
评分（1-5）：
  5 = 数据必图、文字必字，各得其所
  4 = 大致对，个别数据被写成文字或个别文字硬加图表
  3 = 一半对一半错
  2 = 大部分错位
  1 = 全部错位（数据一堆文字堆、单纯的定义/概念却加了饼图）
```

### 空白维度 3：装饰/模板疲劳（Decorative Fatigue）

**现象**：人评发现"**CSFT tpl 装饰元素重复堆砌**（'▶▶▶' 箭头、五角星、圆点散点几乎每页都用）"。**同一个 PPT 内视觉重复到审美疲劳**，人一眼看出是"AI 生成的模板套用"。机评的 `visual_consistency` 反而给 CSFT tpl 高分（因为"一致"），但**一致过头就是无聊/贴纸感**。

**为什么当前 rubric 抓不到**：
- `visual_consistency` 是"越一致越好"的单调评分，捕捉不到"过度一致 = 无变化 = 疲劳"这种非单调关系
- 没有 rubric 项判"页面间是否有必要的视觉变化"（章节页 vs 正文页 vs 收尾页应该有不同）

**建议新增 rubric 项**（VLM 判分）：
```
维度：装饰节制度（Decorative Discipline）
问题：装饰元素（箭头/星星/散点/色块/几何图形）的使用是否节制？
评分（1-5）：
  5 = 装饰恰到好处，能强调关键内容不喧宾夺主
  4 = 稍多但不影响阅读
  3 = 装饰重复但没到疲劳程度
  2 = 装饰重复堆砌，多页出现同一套装饰
  1 = 装饰完全成了模板贴纸感

维度：页面变化度（Layout Variation）
问题：一份 PPT 里，章节页/正文页/图表页/收尾页的版式是否有区分？（并非要求每页都变，而是"该变的时候变"）
评分（1-5）：
  5 = 结构清晰，章节页有节奏感
  4 = 大部分对，个别章节页跟正文页版式一样
  3 = 有部分变化但不明显
  2 = 几乎每页版式都一样
  1 = 完全一个模子
```

---

## 三、方法层建议

### 建议 1：判分产物的稳定性 vs 灵活性权衡

本轮 `dynamic_checklist` 每次现生成 → 口径漂移的教训表明：**判分侧的"每次现生成"是漂移风险源，能固化就应该固化**。

**新 rubric 项设计原则**：
- 维度定义（1-5 评分标准）**固化到 prompt 里，永不变动**
- 参考例（每档 2-3 个）**固化到 prompt 里，永不变动**
- 只有"针对当前 case 的具体问题"允许模型现生成（例如"这张图表是柱状图还是折线图"）

**已经固化的**：`core_checklist`（6 项）、`aesthetic_fine`（6 项，0/1/2 档定义固定）、`hard_check`（4 项二值）
**本周新固化的**：`dynamic_checklist` 从"每次现生成"改为"预生成基线库 + 缓存"
**建议下一步固化**：新维度（主题匹配、图表能力、装饰节制、页面变化）的评分标准 + 参考例应该一开始就固化

### 建议 2：生成成功率作为独立维度

当前 dashboard 里"生成成功率"藏在 `terminal_class` 分布里，overall 分不包含它。CSFT+DPO 生成成功率 47/47 = 100% vs OTTO 3/47 = 6%——这种量级差异应该在 overall 里体现。

**建议**：`overall_score` 引入"可交付率"惩罚系数，或者独立报出：
```
overall_reliable = overall × (done_count / total_case_count)
```
CSFT+DPO: 0.773 × 1.0 = 0.773
OTTO: 0.727 × 0.064 = 0.047（暴露真实产线可用性）

### 建议 3：机评的置信度分层展示

overall 分给到 4 位小数（0.7893）会让读者高估精度。**Δ < 0.02 的差距应该视为噪声**，除非同 case 严谨配对且样本量足够。

**建议**：dashboard 展示时按分层：
- **T1 高置信维度**（hard_check、aesthetic_fine 的对齐/字体等基本功）：可以看到 3 位小数
- **T2 中置信维度**（aesthetic_high、deck 一致）：只看 2 位小数或"梯队标签"
- **T3 低置信 / 空白维度**（主题匹配、图表能力、内容-呈现匹配）：**不看机评分，走人评** 或标"需人评复核"

### 建议 4：人评-机评差异样例库

积累每个"机评抓不到但人评能看到"的 case，作为下一步机评 rubric 扩展的 anchor set。**建议格式**：
```
case_id / query / 机评结论 / 人评结论 / 差异维度 / 差异原因
prod_1eaed984 / 宝马M4 / CSFT 低 0.12 / CSFT 更好 / 判分口径漂移 / dynamic_checklist 不一致（已修）
seq_1495 / 益智休闲 / CSFT tpl 打平 DPO v2 / DPO v2 更好 / 图表能力 / CSFT 短稿没图（rubric 空白）
seq_XXX  / 生日祝福 / ... / ... / 主题匹配 / CSFT 用商务色（rubric 空白）
```

---

## 四、对基模团队的评测建议

面向即将产出 rubric 的基模团队：

1. **关注这些维度作为训练偏好信号**：
   - **主题匹配度**：训练数据里应该有"同一 query 不同视觉主题"的偏好对
   - **图表多样性**：训练数据里应该给"图表多样 > 图表单一"的偏好信号
   - **装饰节制度**：训练数据里应该有"同一装饰元素重复出现 = 差样例"

2. **别过度优化模板模式**：模板模式全模型塌方（含 Opus），主要瓶颈在 skill/prompt/管线层。**训练调优主要看无模板模式分数**。

3. **重视工具调用格式稳定性**（DPO 阶段的隐藏收益）：
   - SFT 里补充"复杂 tool call 用结构化 JSON 表达"强样例（重点：`write_file` 嵌大段 JSON 内容、`create_subtask` 嵌长任务规格）
   - 清理训练数据里所有 XML tool-call 模板（`<file_action>`/`<invoke>`/`<function=>`/`<｜DSML｜>` 都要清）
   - DPO 里"结构化 tool_calls JSON 表达"胜过"XML 表达"

4. **接入前 smoke test 需要跑完整 agent loop**（不是单轮）：至少 3 个包含 `write_file`/`create_subtask` 的 case，看复杂 tool call 稳定性。单轮 smoke test 会漏掉 OTTO 那类问题。

---

## 五、相关文档索引

- 本轮机评数据：`benchmark/results/industry_v2_step3kcsft_{notpl,tpl}.jsonl` / `industry_v2_step3kdpov2_{notpl,tpl}.jsonl` / `industry_v2_step3kcsftdpo_{notpl,tpl}.jsonl`
- 模型横评正文：`评测任务文档/0708_模型特点与缺陷分析.md`（本周已刷新到新 checklist 口径）
- 人评观察：`评测任务文档/人评0714.md`（5 组对比）
- 评测管线问题：`评测任务文档/0708_评测管线问题与现状.md`
- 评分标准（对外）：`评测任务文档/0708_评分标准说明_附共建邀请.md`
- checklist 固定基线：`benchmark/checklist_lib/industry_v2/`（44 份 JSON）+ 预生成脚本 `benchmark/scripts/build_checklist_lib.py`
- content_evaluator 新增缓存机制：`benchmark/evaluators/content_evaluator.py`（`checklist_cache_dir` 参数）
- OTTO 失败分析（作为"接入前 smoke test"的反面案例）：`评测任务文档/0714_otto_prod_1eaed984_失败trace分析.md`
