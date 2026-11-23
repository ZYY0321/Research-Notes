# ToolCUA：同一批模型，给了工具反而掉分——"什么时候该从点屏幕切到调工具"本身是个要学的决策

## 一页读懂
| 项 | 内容 |
|---|---|
| 来源 | arXiv 2605.12481（https://arxiv.org/abs/2605.12481）；venue：arXiv 预印本（页面未见会议标注）；通义实验室（阿里）、复旦、上海 AI Lab |
| 读深度 | 全文（正文 + 附录 A、C.1、C.2 的失败模式分析；案例表没细读） |
| 问题 | 动作空间里同时给 GUI 动作和工具调用（如 API 改一整列表格），模型常常不知道什么时候继续点、什么时候改调工具，路径选得差。 |
| 它检查了什么默认假设 | "给了工具就会更好"。 |
| 发现问题的方式 | 同一批任务（OSWorld 与 OSWorld-MCP 的可行任务交集）上做"纯 GUI vs GUI+工具"的配对对比（表 1），再按任务类型拆（有益工具任务 / 无需工具任务）。 |
| 解决方式 | 训练：把静态 GUI 轨迹改写成 GUI+工具交错轨迹 → 暖启动 SFT + 单步 RL → 在线 RL，并加"工具适当性"奖励与路径效率奖励。 |
| 最强证据 | 表 1：Claude-4.5-Sonnet 纯 GUI 61.9%，加工具后 48.4%（−13.5）；EvoCUA-32B 52.6%→40.5%（−12.1）。ToolCUA-8B 纯 GUI 42.9%，加工具 46.8%（+3.9）；OSWorld-MCP 上 46.85%（表 2）。 |
| 品味 | A：先用一张配对表推翻"工具总有益"，再把问题定义成路径选择。训练部分是常规三段式，价值在前半。 |

## 一段话介绍
多数混合动作空间的工作只报"我的模型总分更高"。这篇先问一个更基本的问题：给现有模型加上同样的工具接口，成绩是升还是降？结果是对几个强模型它是降的：Claude-4.5-Sonnet 掉了 13.5 个点，EvoCUA-32B 掉了 12.1 个点；另一头，Qwen3-VL-8B 几乎不碰工具，在"工具有益"的成功轨迹里平均只调 0.01 次。作者把这个叫做"最优 GUI-工具路径选择"问题，并用合成的交错轨迹 + 在线 RL 训一个 8B 模型。

## 动机
> "they fail to determine when to continue with GUI actions and when to switch to tools, leading to suboptimal execution paths"（摘要）

附录 C.1 把失败分成两种：工具用得太少（underuse，Qwen3VL-8B）和用得太多（overuse，如 Claude-4-Sonnet 成功的有益任务里平均调 4.30 次工具，总体准确率 47.7%→43.5%）。

## 方法
- 数据：取已有"只用工具"的轨迹，随机把一部分工具调用替换回对应 GUI 动作序列，同时把被替换的工具从工具库里删掉，让智能体在"部分工具可用"的上下文中必须退回 GUI（§2.2，Interleaved GUI-Tool Trajectory Generation）。
- 训练：Tool-Bootstrapped GUI RFT（暖启动 SFT + 单轮 RL）→ 在线 agentic RL；奖励含任务成功、Tool Appropriateness（有益任务调工具、无需工具任务不调）、路径更短（§2.3–2.4；超参见附录：λ=0.4，β=0.2，S_max=30）。
- 例子：原文图 1(a)：用 LibreOffice 改一整列，一次 API 调用代替一长串点击和键盘动作。

## 实验
- 想回答：混合动作空间下能否既用对工具又不丢分。
- 数据：OSWorld-MCP 可行任务 333 题（有益 238、无需 95），average@3，最多 50 步（§3.1、表 2）；WindowsAgentArena 107 题子集做跨平台（表 4）。
- 对比：GUI-Owl-1.5-8B 43.84%、Claude-4-Sonnet 43.54%、Gemini-3.1-Pro 41.14%，ToolCUA-8B 46.85%（§3.2）。
- 消融（§3.3，正文表 3）：纯 GUI 路线 Qwen3-VL-8B 29.03% → +SFT 34.93% → +SFT+Agentic RL 42.05%；混合路线 +RFT 38.13%，ToolCUA-8B 46.85%。
- 能支持的结论：混合动作空间下，路径选择要专门训；数据规模相当时，混合路线比纯 GUI 路线高约 4.8 个点（46.85 对 42.05）。
- 支持不了的：对"工具坏了/不可用"的鲁棒性。训练时的"部分工具缺失"是**设计好的**可用性变化，评测里没有运行时工具故障。

## 局限
- 作者承认的（附录 A）：合成数据受限于原 GUI 轨迹的覆盖面；依赖强闭源模型生成，换成 Qwen3.5-Plus 质量明显下降；合成工具不绑定具体实现，真实使用取决于工具成熟度；主要评测只在 OSWorld-MCP，因为缺少开源 GUI-工具协同基准。
- 我看到的：
  1. 纯 GUI 与混合的对比里，混合更高是在 ToolCUA 自己的模型上；上面那些"加工具掉分"的模型也许是对提示词/文档不适配，作者没有排除（表 1 的混合设置统一用同样的工具说明，但没对每个模型调提示）。
  2. 没有"工具失败后能否回到 GUI"的指标。TIR（Tool Invocation Rate）衡量的是该不该用，不是用失败后怎么处理。
  3. 与"总分提升"的关系：它的收益是路径选择带来的总分与步数，**不是**察觉故障。

## 品味判断
1. 问题怎么发现的：把基准里"有工具 / 无工具"的两种设置配对，发现差异是负的。门槛不高：任何有 OSWorld-MCP 的团队都能做；它赢在先把这张表放出来。
2. 最能说服审稿人：表 1 里"工具反而让 Claude-4.5-Sonnet 掉 13.5 个点"。
3. 可模仿：在你想宣称"X 能力有用"之前，先在同一批任务、同一模型上做"开/关"配对，再按任务类型（该用 / 不该用）拆开。实验操作：固定任务集，只切换动作空间，分层报成功率。
4. 没比的工作：Screenshots or Tools（arXiv 2608.03327）直接质疑本文"退化"的普遍性，发现符号随模型变（推理模型 +4.0，非推理 −5.9）。UltraCUA（arXiv 2510.17790）在本文参考之列。我只在 2608.03327 的文本里核到对本文的引用与质疑。

## 和 CUA 评测 / 换路鲁棒性的关系（公开层面）
它说的是"两条路都通时选哪条"，不是"默认那条路坏了怎么办"。对想区分"多路径带来总分提升"与"故障下换路"的人，这是前者的标准样本。

## 原文摘录
- "they fail to determine when to continue with GUI actions and when to switch to tools"（摘要）
- "These cases indicate that the agent is not learning 'use tools more,' but rather needs to learn when tool usage is appropriate."（附录 C.1，Failure Mode II）
- "the replaced tools are simultaneously removed from the tool library, constructing a partial tool-availability context where the agent must fall back to GUI operations"（§2.2）

## 核对说明
读的是 arXiv 页面全文。表 1 的 Claude-4.5-Sonnet、EvoCUA 行数字逐行核过；表 2 的 46.85% 在摘要与 §3.2 对过；正文表 3/4 编号在页面里有错位（正文称"Table 4"，表题为 Table 3），我按表题标。案例研究未读。
