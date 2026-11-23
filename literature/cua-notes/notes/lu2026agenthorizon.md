# AgentHorizon：用「把两条相近指令的轨迹互换」造负例，测评判器能不能看穿长轨迹里的小偏差

## 一页读懂
| 项 | 内容 |
|---|---|
| 来源 | arXiv 2610.11050（2026-10-08 提交）／venue：arXiv 预印本／ServiceNow Research、McGill、Mila 等／代码与数据：https://github.com/ServiceNow/agenthorizon（在论文页首看到的链接，我没有打开仓库） |
| 读深度 | 全文（正文 §1–§4 + Limitations + 附录 B.1–B.4 的主要段落；附录 A 标注细节只扫了） |
| 问题 | 桌面长任务里，自动评判器（直接喂整条轨迹的 LLM，或会用工具翻轨迹的 agent）能否分辨「真完成」和「看起来完成」 |
| 它检查了什么默认假设 | 「轨迹看起来完整、终点正常 = 任务完成」；「给评判器工具去翻证据一定更准」 |
| 发现问题的方式 | 配对构造：同一批人类轨迹，换一条指令就变成负例；再用不同评判器和 harness 对照 |
| 解决方式 | 基准（1,373 条指令-轨迹对）+ 11 个评判模型 × 5 种 harness 的评估 |
| 最强证据 | 最好的 agentic 评判器 GPT-5.5 + Codex 在 AgentHorizon 子集上的平衡准确率 80.9%（Table 2） |
| 品味 | A：配对设计让负例「看起来完整、只在指令上不对」，评判器不能靠「轨迹看着顺」蒙对；缺点是轨迹由人类录制，不是 agent 的真实失败 |

## 一段话介绍
agent 评测越来越多用 LLM 评判器，但长任务里评判器靠不靠谱不清楚。AgentHorizon 请标注员为一对相近的指令各录一条完整操作（比如两条指令只差「画三角形」还是「画五边形」），把轨迹和对方的指令配对就得到一个负例：操作本身流畅完整，只是不满足这条指令。共 523 个正例、850 个负例，来自 166 小时、三种操作系统的录屏。作者让 11 个模型当评判器，一部分直接读全轨迹，一部分通过 Codex、Claude Code 等 harness 当 agent 去翻轨迹。

## 动机
> "A trajectory, composed of long sequences of screenshots and actions, may appear complete, but in reality violates constraints from the instruction or introduces an unwanted side effect."（Abstract）

## 方法（资源构成）
- **规模**（§3.1）：166 小时录屏，Windows / Linux / macOS，6 个任务域；中位每条 121 步，83 条至少 200 步。**被评判的是人类录制的轨迹，不是 agent 自己做的**（§3 开头）。
- **配对构造**（§3.2，Figure 3）：每对指令 A、B 各录一条；匹配的 (A, A轨迹) 是候选正例，交叉的 (A, B轨迹) 是候选负例。正例要经过质量和证据复核：留下 135/462 个，排除 327 个；最终正例 523；负例 850 条全部由供应商复核（耗 212.5 人时），全部保留；合计 1,373。
- **三类负例标签**：关键错误（没完成主目标）、不良副作用（目标完成但带来危害或不想要的后果）、误解（合理但错的理解）。
- **三份切分**：AgentHorizon（AH，528 条，用三个模型联合筛选出的难例）、AgentHorizon-Simple（AH-S，683 条）、开发集 AH-D。
- **评判器配置**：6 个闭源模型 + 5 个开源权重模型；每个既可「直接」把完整轨迹（最多 300 张截图+动作）塞进一次请求，又可通过 harness 当 agent 查看文件（5 个 harness）。
- **指标**：平衡准确率 = 正例准确率和负例准确率的均值，全猜一类就是 50%。

## 实验
- **主表（Table 2，AH 子集）**：
  - GPT-5.5 + Codex：平衡 80.9（正例 71.8，负例 90.0）；
  - Gemini 3.1 Pro + Gemini CLI：77.7；Claude Opus 4.7 + Claude Code：76.0（正例 76.7，负例 75.4）；
  - 最强开源权重 agentic 评判：Qwen 3.6 27B + OpenCode 70.4；
  - 直接评判：Qwen 3.6 27B 77.6（正例 93.8、负例 61.5），GPT-5.5 直接评判 68.6。
- **工具不一定帮忙**：GPT-5.5 从直接评判的 68.6 提高到 Codex 的 80.9；Qwen 3.6 27B 直接评判 77.6，反而比 OpenCode 的 70.4 高 7.2 个点（§4）。作者强调这些比较换了整个 harness，不能归因于单个组件。
- **harness 影响**（附录 B.3，Table 8）：同一 GPT-5.5，Codex 换 OpenCode 降 3.7 点；Qwen 换 OpenHands 降 20.4 点。
- **没有指令时评判器几乎都说成功**（§4 讨论，附录 B.4）：Qwen 3.6 27B 在不给对应指令时把 98.9% 的匹配和互换后的完整轨迹都判成成功；去掉指令和动作日志后平衡准确率在 47.8%–49.8%（Table 9）。意思是：轨迹本身看不出成败，必须对着指令检查。
- **不良副作用最难**：它在所有主要评判器上的精确召回最低（§4 讨论，附录 B.2，Table 7）。例：一条 Trello + Slack 任务里消息发错了频道，Claude Opus 4.7 判成功，GPT-5.5 拒绝（§4）。

**能支持的结论**：长桌面轨迹上，最好的评判器也只有约 81% 平衡准确率；工具、harness、模型之间的关系不单调；评判器常常容易接受「做得完整但对象不对」。
**支持不了的结论**：
- 轨迹是人类录的，不含 agent 常见的循环、卡死、逐渐漂移（作者明确说，Limitations）。
- 只有英语语料，没有独立标注者一致性（Limitations）。

## 局限
- 作者承认（Limitations）：配对设计只看细微的「差一点」错误，不覆盖循环、崩溃、停滞、漂移，所以不能用指令缺失对照去建模一般的 agent 失败；难度切分依赖具体的筛选模型和版本；开发早期的试点让「完全未见」的说法受限；没有独立的人际标注一致性（只有各复核阶段间的一致性）；英语、有限应用、只有截图和动作日志（没有应用状态）。
- 我看到的：
  1. 平衡准确率给正负错同权，但作者自己在 §4 讨论中说不同用途对两种错的代价不同（误杀好数据 vs 放过坏数据）。Table 2 里 Qwen 直接评判正例 93.8、负例 61.5，说明平衡 77.6 掩盖了「过度放行」。
  2. 负例是「换指令」得到的，所以错误类型分布由标注员写指令的方式决定，不一定等于真实 agent 的失败分布。

## 品味判断
1. **问题怎么发现的**：从「评判需要在长历史里找到被隐藏的证据」出发，想到一个不需要人为注入错误的负例来源：同一条轨迹对另一条指令就是失败。换一个团队能做吗？想法能复制；贵的是 850 条录制和供应商复核（212.5 人时）。
2. **最能说服审稿人的**：Table 9——不给指令，评判器把几乎所有轨迹都判成功，平衡准确率在 47.8%–49.8%，这证明负例确实是靠指令才能分出来的，而不是靠轨迹质量。
3. **可模仿**：做评判器评测时，给每个正例找一个「同样流畅但不满足指令」的反例，再用「去掉指令」做对照实验，证明指标不是靠表面线索拿分。
4. **没比的**：没有把评判器放在 agent 真实失败轨迹上测（作者在 §1 区分了：此前工作聚焦未能产生任务结果的轨迹）；没有与完成声明（agent 自述）相关的对照，自述怎样影响评判可见 zhu2026selfreportleakage。

## 和 CUA 评测 / 换路鲁棒性的关系（公开层面）
对「动作先生效再下结论」来说，AgentHorizon 提供的是评判侧的反面：评判器容易被「看起来完整」骗，因此用「删掉某个证据来源、看评判器判断变化」这类对照是可行的。

## 原文摘录
- "Experiments reveal that agentic judges can revisit screenshots and actions, but our direct judge results show that this flexibility is not sufficient by itself."（§4 讨论）
- "Thus, allowing a model to inspect the trajectory through tools does not necessarily improve its verdicts."（§4）
- "The recordings are performed by human annotators, and the agents evaluate these recordings rather than performing the tasks themselves."（§3）

## 核对说明
读的是 arXiv 全文文本，Table 2、Table 8、Table 9 的数字从原文抄出。「GitHub 链接」只在论文页首看到，没打开。98.9% 一句的原文是 "Qwen 3.6 27B classifies 98.9% of both matched and swapped full trajectories as successful without the corresponding instruction given as input (Appendix B.4)."；附录 B.4 的 Table 9 只给出了去掉不同输入后的平衡准确率，我没有逐项核对 98.9% 对应的表。
