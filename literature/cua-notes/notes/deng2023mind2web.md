# Mind2Web：真实网站上的通用网页智能体数据集，把「换站点、换领域」做成三种测试

## 一页读懂
| 项 | 内容 |
|---|---|
| 来源 | arXiv:2306.06070（v3，2023-12-09）；NeurIPS 2023 Datasets and Benchmarks（PDF 页脚写明）；arXiv 备注写 Spotlight；俄亥俄州立大学 OSU NLP；主页 https://osu-nlp-group.github.io/Mind2Web |
| 读深度 | 全文（主文 + 局限；附录没细读） |
| 问题 | 已有网页智能体数据集要么用模拟网站，要么只覆盖少数站点，没法评估「放到任意网站能不能用」 |
| 它检查了什么默认假设 | 「在固定几个网站上训练、测试」就能代表网页智能体的能力 |
| 发现问题的方式 | 重新设计数据划分：同站点新任务 / 新站点 / 新领域，直接测泛化 |
| 解决方式 | 资源（数据集）+ 一个两阶段基线 MindAct（小模型筛元素，大模型做选择题） |
| 最强证据 | Table 2：Flan-T5-XL 版 MindAct 的单步成功率 Cross-Task 52.0，Cross-Website 38.9，Cross-Domain 39.6；整条任务成功率只有 5.2 / 5.1 / 2.9 |
| 品味 | A：数据划分本身就是认识，「整任务成功率很低」这个事实改变了后人怎么报指标 |

## 一段话介绍
2023 年中，LLM 刚能读 HTML，但没人有一个能代表「真实网站有多乱」的数据集。Mind2Web 请众包工人在 137 个真实网站、31 个领域上演示了 2000 多个任务，保存网页快照和网络流量。真实网页的 HTML 太长（清洗后平均还有 580 个元素），直接喂给 LLM 又贵又不准，所以作者先用 86M 的 DeBERTa 给元素打分筛出候选，再让大模型在候选里做选择题。结果是：单步还能做对一半左右，但整条任务几乎全军覆没。

## 动机
作者要的是「给任意网站，能听懂语言指令并完成任务」的智能体，并认为已有数据集在三方面不够：

> "Existing datasets for web agents either use simulated websites or only cover a limited set of websites and tasks, thus not suitable for generalist web agents."（摘要）

引言里把不足拆成三条：只在预先指定的少量站点上跑；对网站做强简化假设；只支持特定类型任务或要求逐步指令（§1）。

## 方法（或资源构成）
- **任务怎么来**：众包标注，2000+ 开放任务，137 个站点，31 个领域，每个任务有操作序列、网页快照、网络流量（摘要、§1）。
- **三种测试集**（§4.1）：
  - Cross-Task：从剩余数据里随机留 20%，252 个任务，69 个站点。训练时见过同站点。
  - Cross-Website：每个顶层领域取 10 个站点留出，177 个任务。训练时没见过这些站点，但见过同领域。
  - Cross-Domain：整个 Information 和 Service 两个顶层领域留出，912 个任务，73 个站点。
  - 训练集 1,009 个任务，73 个站点。
- **怎么判成功**（§4.2）：每一步在「给定真实历史动作」的条件下独立评估。元素选对且操作对才算这一步成功（Step SR）；整个任务所有步都成功才算任务成功（SR）。
- **基线 MindAct**：HTML 先清洗，平均元素数从 1,135 降到 580，目标元素召回仍有 94.7%（§4.2）。DeBERTa-B 做候选生成，Recall@50 为 88.9% / 85.3% / 85.7%（三种测试集，§4.3）。再把候选分组成「每组 5 个 + None」的选择题交给 LLM。
- **一个具体例子**（Figure 5）：任务是「从 Marriott 商店搜 queen 尺寸枕头保护套并加入购物车结账」。模型看到几个候选元素，选中 `<select id=1 meta="Size; Select a Size">`，输出动作 SELECT，值 Queen。

## 实验
- **想回答什么**：模型能不能在没见过的网站、甚至没见过的领域做事？选择题形式是不是比生成式更好？
- **主结果**（Table 2，Step SR / SR，单位 %）：

| 模型 | Cross-Task | Cross-Website | Cross-Domain |
|---|---|---|---|
| 生成式基线 Flan-T5-B | 17.5 / 0.0 | 11.0 / 0.0 | 11.9 / 0.4 |
| MindAct Flan-T5-B | 41.0 / 4.0 | 29.5 / 1.7 | 31.6 / 1.6 |
| MindAct Flan-T5-XL | 52.0 / 5.2 | 38.9 / 5.1 | 39.6 / 2.9 |
| MindAct GPT-4（仅 50 个任务，top-10 候选） | 36.2 / 2.0 | 30.1 / 2.0 | 26.4 / 2.0 |

- **能支持的结论**：
  - 选择题形式明显好于直接生成（同一个 Flan-T5-B，Step SR 17.5 → 41.0，Table 2）。
  - 新站点比同站点低 10 个点以上，而新站点和新领域差不多，作者据此认为难点在网站设计和交互逻辑的多样性，不在领域语义（§4.3）。
  - GPT-3.5 的元素准确率只有 20% 左右，作者分析原因之一是它爱选 None（§4.3）。
- **支持不了的结论**：
  - GPT-4 只在 50 个任务上跑（预算限制），整任务成功率 2.0 的差异没有统计意义，不能和微调模型严格比。
  - Step SR 是「给真实历史」下的单步指标，不是智能体自己连续走的结果。

## 局限
- **作者承认的**（§6）：
  - 网站以英文、美国常用站点为主，标注者来自 MTurk，可能偏熟练用户。
  - 只用文本（HTML），没用渲染画面。
  - 没建模页面变化，每步独立编码。
  - 评估用缓存的离线环境：「the task will fail immediately if an action was not cached during data collection, potentially leading to false negatives due to the existence of multiple paths」。作者在附录 C.1 做了等价元素归一化来缓解。
- **我看到的**：
  - 整任务成功率全在个位数，区分度主要靠 Step SR，而 Step SR 允许用真实历史纠偏，高估连续执行能力。
  - 同时报了 Ele. Acc、Op. F1、Step SR、SR 四个数，读者容易只引最高那个。

## 品味判断
1. **问题怎么发现的？** 不是从榜单异常，而是从「现有数据集都不能回答通用性问题」的缺口出发，设计划分来逼出答案。换一个团队能做出来，但需要 137 个站点的众包预算和标注规范，门槛在工程量，不在想法。
2. **最能说服审稿人的一句话**（我的判断，审稿记录未能打开）：「the overall task success rate remains low for all models, as the agent often commits at least one error step in most cases」（§4.3）。它把「还有空间」写成了数字：Step SR 五成、任务 SR 五个点。
3. **可模仿**：做评测时把「泛化」拆成三层写进数据划分（同站点新任务 / 新站点同领域 / 新领域），再同时报单步和整任务两层指标。做实验就是：同一批模型在三个划分上各跑一遍，比较相邻两层的差。
4. **没比的工作**：只比了自家基线、Flan-T5、GPT-3.5/4。后来视觉模型（如 SeeClick、CogAgent）在这个数据集上重新跑，说明文本 HTML 并非唯一表示。

## 和 CUA 评测 / 换路鲁棒性的关系（公开层面）
§6 自己写了「同一任务有多条路径、离线缓存会误判」，这是后来离线评估被质疑的起点；同一个目标有多条合法路径，这是做换路评测时必须面对的前提。

## 原文摘录
- "With over 2,000 open-ended tasks collected from 137 websites spanning 31 domains…"（摘要）
- "A task is regarded successful only if all steps have succeeded. It is therefore a stringent metric."（§4.2）
- "…the task will fail immediately if an action was not cached during data collection, potentially leading to false negatives due to the existence of multiple paths for completing the same task."（§6）

## 核对说明
读的是 arXiv v3 PDF（pymupdf 抽取文本），摘要、引言、§3 方法、§4 实验与 Table 2、§6 局限都读过。附录 D（GPT-4 子集结果）没读。venue 依据：PDF 页脚「NeurIPS 2023 Track on Datasets and Benchmarks」，arXiv 备注「NeurIPS'23 Spotlight」；未在 NeurIPS 官网核对 Spotlight，OpenReview 被验证页拦截，未读审稿意见。
