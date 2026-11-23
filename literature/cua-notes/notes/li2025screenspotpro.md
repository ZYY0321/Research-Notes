# ScreenSpot-Pro：把「点哪里」放到专业软件的高分辨率整屏上，榜单一下子从 90% 掉到 18.9%

## 一页读懂
| 项 | 内容 |
|---|---|
| 来源 | arXiv:2504.07981（v1，2025-04-04；文中注明最初上传于 2025-01-03）；venue **UNVERIFIED**（arXiv 页面备注只写「13pages」，未查到会议接收信息）；新加坡国立大学等；榜单 https://gui-agent.github.io/grounding-leaderboard/ |
| 读深度 | 全文（主文 + 局限；附录没细读） |
| 问题 | 已有定位基准截图小、软件简单，不能反映专业软件里的高分辨率、小目标、复杂界面 |
| 它检查了什么默认假设 | 默认「在 ScreenSpot 上定位准，就能用在真实电脑上」 |
| 发现问题的方式 | 换基准：用专业软件整屏高分辨率截图，让现有最强模型重测 |
| 解决方式 | 基准 + 一个免训练的搜索基线 ScreenSeekeR |
| 最强证据 | 摘要与 Table 3：最强模型（OS-Atlas-7B）只有 18.9%，GPT-4o 在表里是 0.8%；ScreenSeekeR 用 OS-Atlas-7B 做定位器，提到 48.1%（Table 4） |
| 品味 | A：一个新基准让当时的数字大幅掉下来，后来 OpenCUA、ScaleCUA 都把它列进主表 |

## 一段话介绍
ScreenSpot 里的截图是裁剪到局部的小图，目标元素相对屏幕不算小。ScreenSpot-Pro 收集 23 个专业软件（AutoCAD、Photoshop、MATLAB、VSCode 等）的整屏高分辨率截图，由使用这些软件的专家当场标注，共 1,581 条指令。当时的定位模型从 ScreenSpot 的几十个点掉到个位数到十几。作者接着发现：缩小搜索范围（先裁剪出可能区域，再定位）能大幅提高准确率，并据此做了 ScreenSeekeR，让强模型当规划者给出候选区域，逐级裁剪后再交给定位模型。

## 动机
> "Existing GUI grounding models perform poorly on this dataset, with the best model achieving only 18.9%."（摘要）

引言的论证有三层（§1）：专业软件复杂，需要更高分辨率，超过模型的有效处理能力；分辨率越高，目标相对尺寸越小，定位准确率越差（Figure 2 用 ScreenSpot-v2 上目标框面积和准确率的关系说明）；专业用户还依赖额外文档和外部工具，屏幕更杂。

## 方法（或资源构成）
- **任务怎么来**（§3）：
  - 23 个应用，5 个行业类别（开发、创意、CAD、科学分析、办公）加 3 个操作系统的常见用法，1,581 条指令，每条一张独立截图。
  - 标注方式：工具把截图叠加在屏幕上，专家直接画框、写指令，不用事后回忆（§3.2）。优先用分辨率高于 1080p 的屏幕，关闭系统缩放；双屏时截图跨两屏。
  - 文字/图标分类沿用 ScreenSpot，但规则更细：只有没有文字提示时才算图标。
  - 质检（§3.3）：每条至少两位标注员检查指令和框，歧义指令被消解到只有唯一目标，框只含可交互区域。
- **怎么判成功**：沿用点击落在目标框内的准确率。
- **ScreenSeekeR**（§4–5）：用 GPT-4o 当规划者推理目标最可能在哪，把区域裁出来交给定位模型；每步会再扩展邻近区域，并给候选打分。对比的无规划基线有 Iterative Focusing（正文有处写作 Iterative Zooming）、Iterative Narrowing、ReGround（先定位，再裁出初始预测点周围的区域重新定位）。
- **一个具体例子**（Figure 3）：同一类指令在 ScreenSpot 里是 960×540 的小图，在 ScreenSpot-Pro 里是 2560×1440 的整屏，目标只占屏幕很小一块。

## 实验
- **想回答什么**：现有模型在这里到底多差？差在哪类目标？搜索缩小范围有没有用？
- **主结果**（Table 3，平均准确率，%）：

| 模型 | 平均 |
|---|---|
| OS-Atlas-7B | 18.9 |
| UGround (7B) | 16.5 |
| Aria-UI | 11.3 |
| CogAgent (18B) | 7.7 |
| ShowUI (2B) | 7.7 |
| SeeClick (7B) | 1.1 |
| GPT-4o | 0.8 |

- **图标比文字难**（§5.1）：OS-Atlas-7B 文字 28.1、图标 4.0（Table 3）。作者给了三个原因：功能太多无法文字描述；专业软件默认用户熟悉图标；图标在专业语境里的含义很少出现在网页数据里。
- **多轮方法**（Table 4，OS-Atlas-7B 为定位器）：直接 18.9；Iterative Focusing 31.0；Iterative Narrowing 31.9；ReGround 40.2；完整 ScreenSeekeR 48.1。去掉递归搜索降到 41.9，作者写这是消融里降幅最大的一项（§5 消融段）。
- **能支持的结论**：当时的定位模型离专业场景很远；缩小搜索区域有明显效果。
- **支持不了的结论**：ScreenSeekeR 靠 GPT-4o 当规划者，结果混合了「规划者的 GUI 知识」和「搜索策略」；文中没有拆开两者的贡献（没有换规划者的对照）。

## 局限
- **作者承认的**（Limitations）：基准只测定位，不含规划和执行（如 OSWorld 那样的任务）；原因是这些软件的授权带来法律风险。
- **我看到的**：
  - 正文 §5.1 写 GPT-4o「scored only 0.9%」，Table 3 平均是 0.8%，同篇不一致（可能是取整或版本差异，我没追）。
  - 1,581 条是每条一张独立截图，同一软件内的版本、主题差异小；Figure 1(a) 里个别软件只有几十个样本（如 Illustrator 31）。
  - 新近模型数字上升很快（OpenCUA-72B 在其 Table 5 报 60.8，ScaleCUA 论文也在主表报），说明这个基准的区分度会随时间衰减，是否会饱和要继续看。

## 品味判断
1. **问题怎么发现的？** 对着已有基准的截图（局部裁剪的小图）提出「这不像真实使用」，换成整屏、专业软件，再让现有最强模型重测。其他团队也能想到，难点是找到专业软件使用者当场标注，且要有 23 个软件的授权环境。
2. **最能说服审稿人**（我的判断）：摘要里并列「最强模型只有 18.9%」和「不加训练的搜索方法到 48.1%」，既立了难题，又给了方向。
3. **可模仿**：怀疑某个基准过易时，不要改模型，改输入——把截图放回真实尺寸、真实软件里，再看同样的模型掉多少。再用 Figure 2 那种「目标相对面积 vs 准确率」曲线，把「难在目标小」画出来。
4. **没比的工作**：只评了定位，没测定位提升之后端到端任务能不能完成。

## 和 CUA 评测 / 换路鲁棒性的关系（公开层面）
说明截图尺寸与目标相对大小是影响「能不能点到」的独立因素；如果评测里的失败来自定位，要先确认是不是被分辨率和缩放设置放大的。

## 原文摘录
- "Existing GUI grounding models perform poorly on this dataset, with the best model achieving only 18.9%."（摘要）
- "ScreenSpot-Pro features screenshots of the entire screen, while ScreenSpot contains unrealistic screenshots cropped to local areas."（Figure 3 题注）
- "This benchmark is specifically designed to evaluate GUI grounding, excluding agent planning and execution tasks like those in OSWorld."（Limitations）

## 核对说明
读的是 arXiv v1 PDF；摘要、§1、§3、§4（方法概述）、§5（Table 2–4 与分析）、结论、局限读过，Table 3、Table 4 数字核对过。ScreenSeekeR 的算法细节、附录没细读。venue 未核实：arXiv 备注不含会议；没有在会议官网或 OpenReview 上找到录用记录，因此标 arXiv 预印本（UNVERIFIED）。
