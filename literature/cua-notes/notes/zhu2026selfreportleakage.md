# Self-Report Leakage：让评判器看到 agent 自己写的「我做完了」，会把失败漏判成成功

## 一页读懂
| 项 | 内容 |
|---|---|
| 来源 | arXiv 2610.29609（2026-10-21 提交）／venue：arXiv 页面备注称 "accepted by the Research Track of ICSE 2027"，我只看到这条作者备注，未在会议官网核实（UNVERIFIED）／南京大学、慕尼黑工大等／§III-B 提到实现、schema 和策略已发布（released），我没有打开仓库，也没有找到链接 |
| 读深度 | 全文（正文 §I–§VIII；附录没有细读） |
| 问题 | 评判器同时读轨迹和 agent 的最终报告时，报告会不会影响它对「到底完成没有」的判断 |
| 它检查了什么默认假设 | 「把 agent 的最终报告放进评判 prompt 是无害的上下文」 |
| 发现问题的方式 | 可控干预：同一个评判器、同一份任务和轨迹，只在「看到自述」和「看不到自述」之间切换（aware / blind） |
| 解决方式 | 报告隔离 + 结构化审计器：先让一个组件读报告判断它声称了什么，另一个组件不看报告只读轨迹抽取证据，最后用确定性规则判 pass/flag/review |
| 最强证据 | 不给评判器看自述，「危险误报」召回提升 43.4 个百分点（Qwen3.5-35B-A3B）和 13.3 个百分点（DeepSeek-284B-A13B）（Table II） |
| 品味 | A：干预设计干净（只改一个变量），结论马上可用（别把自述喂给评判器）；缺点是数据只有 Android 轨迹 |

## 一段话介绍
自动化流水线里，agent 会写「任务完成」。如果下游评判器也读这句话，它就容易跟着相信。作者把「agent 声称成功、但轨迹没有显示它真的做成」叫做「危险误报」。他们做了一个干净的对照：同一个评判器、同一条轨迹，只把 agent 的自述加进去或拿掉，发现拿掉以后能抓出更多误报。然后做了一个把「读报告」和「读轨迹」分开的审计器，F1 约 0.75–0.81。

## 动机
> "A controlled aware/ blind intervention reveals self-report leakage: the agent's own self-report changes how completion is judged."（Abstract）

## 方法
- **对象**：一次完整运行 u=(任务 x, 轨迹 τ, 最终报告 m)。轨迹是每步 GUI 状态的文本序列（可见文字、内容描述、控件 id、边界等）。审计在事后离线进行，没有活设备或任务专用检查器（§II-A）。
- **成功的定义**：用「因果达成」而不是「最终画面看起来对」。例如，目标状态在第 0 步就已存在、目标列表本来是空的、输入了但没保存，都不算（§I，§II-A）。
- **危险误报** = 报告声称成功 且 人类盲标认为轨迹没完成（§II-B）。两个标签分别独立标：声称由报告单独判，是否完成由任务+轨迹单独判，标注员判完成时看不到报告。
- **审计器**（§III）：
  1. 声明读取器：只读报告，输出 success / failure_or_incomplete / unclear；
  2. 证据抽取器：只读任务和轨迹，输出五个字段（有无相关动作、目标对不对、有无状态转移、是否提交、最终状态是否支持目标），不允许直接说「完成」；
  3. 确定性检查器：按任务类（创建/编辑、删除、配置、发送、查询、其他）规定必须为「是」的字段，缺一就 not_completed 或 unknown。例：删除类必须有动作、目标、转移、最终支持；
  4. 声明与轨迹对比：声称成功但轨迹未完成 → flag；任一边不确定 → review。
- **可重放**：证据缓存后换策略不需要再调用模型。

## 实验
- **数据**（§IV）：从 1,384 次在范围内的 GUI agent 运行里取 465 条「审计目标」记录（含 180 条危险误报）；来源是 AndroidWorld 原版 151 条、AndroidWorld 扩展 276 条、Themis 38 条；两种 agent（AppAgent、Mobile-Agent-v3），各 90 个正例。Batch 1（335 条，130 正例）用于开发；Batch 2（130 条，50 正例）留作验证，含全部 Themis 记录。
- **RQ1 干预**（Table II，合并集）：
  - Qwen：aware F1 0.37（召回 0.23）→ blind F1 0.62（召回 0.49），仅轨迹召回提升 +0.43；有害翻转 79 次 vs 恢复翻转 1 次。
  - DeepSeek：aware F1 0.59（召回 0.44）→ blind F1 0.64（召回 0.52），+0.13；翻转 31 vs 7。
  - Batch 2 方向相同（+38.0 和 +14.0 个百分点）；DeepSeek 在 Batch 2 的符号检验 p=0.065，不显著，其余三组 p<0.001。
- **RQ2 结构化审计 vs 对照**（Table III，合并集 F1）：Qwen 下：claim-aware 0.56，prompt-blind 0.62，结构化审计器 0.75；DeepSeek 下 0.63 / 0.64 / 0.78。
- **RQ3 门控**（Table IV）：合并集上拦住 138/180（Qwen）和 159/180（DeepSeek）个危险误报，代价是检查 48% 和 56% 的审计目标；相对全部 1,384 次运行约 16%–19%。

**能支持的结论**：对两个开源评判模型，给评判器看自述会让它更倾向判成功；把报告隔离出去是低成本的有效做法。
**支持不了的结论**：
- 只测了两个中小评判模型（Qwen3.5-35B-A3B、DeepSeek-284B-A13B），没测 GPT / Claude 一类前沿评判。
- Android 轨迹、两个 agent；「危险误报」的真实比例在全部运行中是多少，没有给（样本取的是 harness 状态判不了的难例，分母是 audit-target 集）。

## 局限
- 作者承认（§VI-C、§VII）：结果在 Android GUI 轨迹、被研究的报告风格和被动轨迹表示下最强；跨应用生态、agent 家族、轨迹表示的泛化留作未来；Themis 子集太小（38 条，一条记录能让 F1 变约 0.07）不下结论；残余的静默误通过多半是轨迹本身没给决定性证据，或抽取器漏了。
- 我看到的：
  1. 轨迹是文本序列化的 UI 状态，没有截图，和用截图的桌面/网页评判不同。
  2. 评测的被审 agent 是 AppAgent 和 Mobile-Agent-v3，不是最新的前沿模型，自述风格可能不同。

## 品味判断
1. **问题怎么发现的**：从「评判器读的是任务+轨迹+报告」这个常见 prompt 模板出发，怀疑报告是个泄漏通道，然后设计干预去测。换一个团队只要有轨迹和人工「是否完成」标注就能做，难点是 180 个危险误报的人工标注。
2. **最能说服审稿人的**：Table II 的翻转计数：79 次有害翻转 vs 1 次恢复翻转，说明不是随机波动，是单向的偏移。
3. **可模仿**：任何用 LLM 评判 agent 的工作，都可以补一个「盲评对照」：同一评判器、同一份轨迹，只拿掉 agent 自述，看召回和精度各变多少。一个小时的实验就能做。
4. **没比的**：没和用截图的前沿评判（如 AgentHorizon、VeriCUA）直接比；RQ2 的对照 AER 是改写 Agent-Eval-Refine 的 prompt，不是官方实现。

## 和 CUA 评测 / 换路鲁棒性的关系（公开层面）
「最终画面兼容」不等于「agent 做成了」是和动作生效核验直接相关的论断；论文给出的「因果达成」五字段（动作、目标、转移、提交、最终支持）可以当成核验动作是否真生效的清单参考。

## 原文摘录
- "The same judge reads the same task and trace; only that self-report is included or withheld."（Abstract）
- "The report records what the agent claims, but it must not influence the trace-state judgment."（Abstract）
- "Final-screen compatibility alone is insufficient, because pre-existing goal states, empty target lists, proxy screens, and unsaved edits can all make a failed run appear successful"（§I）

## 核对说明
读的是 arXiv 全文文本，读了摘要、§I、§II、§III、§IV、§V、§VI、§VII 的主要段落；Table II、III 的数字从原文表格抄出；Table IV 的 138/180、159/180 来自 §V 正文。ICSE 2027 仅来自 arXiv 备注。
