# CogAgent：把输入分辨率拉到 1120，只看截图也能在网页和手机上超过读 HTML 的模型

## 一页读懂
| 项 | 内容 |
|---|---|
| 来源 | arXiv:2312.08914；CVPR 2024，页 14281–14290（openaccess.thecvf.com 已打开）；清华 + 智谱；代码 https://github.com/THUDM/CogVLM ，摘要另给后续版 https://github.com/THUDM/CogAgent |
| 读深度 | 全文（CVPR PDF 主文、表 1–6、结论；附录没逐页） |
| 问题 | 通用视觉语言模型吃不消 GUI：屏幕上的字和图标太小，224 或 490 的分辨率认不出来 |
| 它检查了什么默认假设 | 「把现有 VLM 的输入分辨率直接加大」就能看清界面；以及「GUI 必须读 HTML / OCR，截图不够用」 |
| 发现问题的方式 | 拆计算量：原结构把分辨率加到 1120 时 FLOPs 可以比交叉注意力支路高 10 倍以上（§4.1）；再用同一套 Mind2Web / AITW 协议比「读 HTML」和「看图」 |
| 解决方式 | 模型：在 CogVLM-17B 上加一条高分辨率交叉注意力支路（EVA2-CLIP-L，约 0.30B），低分辨率仍走 224，高分辨率吃 1120×1120 |
| 最强证据 | Mind2Web 步成功率：CogAgent 62.3 / 54.0 / 59.4（cross-task / website / domain），整体 58.2；同表 Flan-T5-XL 是 52.0 / 38.9 / 39.6，整体 43.5（CVPR PDF 中该表题为 Table 3） |
| 品味 | A：架构改动对准 GUI 自己的难点（字小），而且截图模型在公开协议上超过更大的 HTML 模型 |

## 一段话介绍
CogAgent 是一个 18B 的视觉语言模型，专门用来看懂并操作界面。基座是 CogVLM。作者没有把整张 1120 的图塞进原来的视觉编码器，而是加一条轻量的高分辨率支路，每一层用交叉注意力把高分辨率特征注进语言模型。训练上先补 GUI 和 OCR 数据，再在 Mind2Web 和 AitW 上微调。结果是：只看截图，网页步成功率整体 58.2，高于用清洗 HTML 的 LLaMA2-70B（整体 54.4）；手机上统一模型整体 76.88，比当时的视觉基线 Auto-UI 高 2.61。

## 动机
引言把 GUI 写成语言模型的盲区：没有标准 API，图标和空间关系写不进文字，canvas 和 iframe 也抽不进 HTML（§1）。接着问：

> "With the rapid development of VLM, can we naturally achieve universality on GUIs by relying solely on visual inputs?"（§1）

他们认定通用 VLM 的分辨率（224 或 490）对不上电脑和手机常见的 720p 以上屏幕（§2.1，arXiv HTML）。

## 方法（或资源构成）
输入是一张界面截图加文字任务。图被缩成两份：224×224 走原来的低分辨率编码器，1120×1120 走新的高分辨率编码器。解码器仍是原来的计算，只在每一层插入对高分辨率特征的交叉注意力（§2.2）。

预训练先用图文和 OCR，再加 GUI 与定位数据。对齐阶段用人工标的两千多张手机和电脑截图，加上把 Mind2Web、AitW 转成问答，以及公开 VQA（§2，CVPR PDF 训练段）。GUI 评测时：Mind2Web 按 Deng 等人的设定报步成功率；AitW 在全部子集上联合微调，GoogleApps 下采样到 10%，避免它比其他子集大 10–100 倍。

一个具体例子：给一张网页截图和「下一步该点哪」，模型直接出动作，不从 HTML 候选里选。论文没有逐步展开某一条 Mind2Web 轨迹，上面是它的输入输出形式。

## 实验
- Mind2Web 想回答：只看图能不能超过读 HTML。表里 CogAgent 三个划分 62.3 / 54.0 / 59.4，整体 58.2。LLaMA2-70B 是 55.8 / 51.6 / 55.7，整体 54.4。Qwen-VL 整体只有 10.2。正文说相对 LLaMA2-70B 三个划分高 11.6%、4.7%、6.6%：用表内绝对数相减是 6.5、2.4、3.7 个百分点，除以 LLaMA2-70B 的 55.8 / 51.6 / 55.7 大约就是这三句相对涨幅。GPT-4 few-shot 整体 30.9，和 Mind2Web 原文表 2 的 26.4–36.2 步成功率同一量级，但 CogAgent 是微调、GPT-4 是 few-shot，不能当成同训练预算的对比。
- AitW 想回答：同一套视觉模型能不能覆盖多个手机子集。表内 CogAgent 整体 76.88，Auto-UI 74.27，差 +2.61，与正文一致。作者抽查错误案例后说，超过 40% 被他们重判为其实做对了，因为手机上常常有多条合法路径（§3.3）。
- 消融（表 5、表 6）：高分辨率交叉模块在 1120 上的 FLOPs，比把原 CogVLM 结构直接拉到 1120 低一个数量级（正文写 “more than 10 times”）。表 6 最后一列是消融设定下的 Mind2Web，不是主表的 58.2。双栏抽取把相邻两行并进同一格：只有 caption/OCR 时这一列是 38.6 和 40.7，加上 GUI 与定位数据后出现 54.2。正文只说网页和定位数据对 Mind2Web「影响很大」，我不再把 41.4 单写成对照基线。
- 能支持的结论：在这两份 2023 年的数据上，专门的高分辨率视觉模型可以打过「读结构化文本」的强基线。支持不了的：不能推出它在实时环境里任务级成功率也更高——Mind2Web 报的是步成功率，AitW 报的是动作匹配，都不是端到端任务成功。

## 局限
- 作者承认的（§5）：坐标不够准；不能处理多张图。原文：`imprecise output coordinates and incapability of processing multiple images`。
- 我看到的：AitW 上相对 Auto-UI 只高 2.61，而且作者自己说四成「错误」其实是另一条合法路径，说明动作匹配分母偏严，2.61 里有多少是真能力说不清。Mind2Web 上对 LLaMA2-70B 的优势在 cross-website 只有 2.4 个百分点。高分辨率支路的计算故事是硬的，跨数据集的领先幅度并不均匀。

## 品味判断（本模板最重要的一节）
1. 问题是从 GUI 的物理约束里来的：字和图标比自然图像小，直接加大原编码器的分辨率算不动。换一个有 VLM 训练条件的团队可以做，但要把交叉注意力的计算曲线和两份公开基准同时做完，门槛在算力和数据，不在想法本身。
2. 最能说服审稿人的是两张东西叠在一起：图 3 的 FLOPs 曲线（1120 不必付 10 倍计算），加上 Mind2Web 表里截图模型超过 70B 的 HTML 模型。后一句对 CVPR 更关键，因为它把「看图」从辅助特征变成了可以打榜的主输入。
3. 可模仿的实验：固定基座和数据，只改输入分辨率和融合方式，报计算量（FLOPs 或同等指标）和同一份公开基准。不要只报「我们用了更高清的图」。若要证明「看图优于读结构」，对照必须使用对方论文里的同一划分、同一指标（这里是 Mind2Web 步成功率）。
4. 它没有比的：没有端到端的在线网站或真机任务成功率；没有和稍后的 SeeClick 比（SeeClick 的 ScreenSpot 表把 CogAgent 平均放在 47.4%，那是另一篇的数字）。多图历史、动作没生效之后怎么改，结论里已经承认做不到。

## 和 CUA 评测 / 换路鲁棒性的关系（公开层面）
作者在 AitW 错误分析里写明，多条合法路径会被动作匹配判错。这和「换一条路仍算成功」是同一件事，但这篇只做了事后抽查，没有把第二条路径写进指标。

## 原文摘录
- "CogAgent, using only screenshots as input, outperforms LLM-based methods that consume extracted HTML text on both PC and Android GUI navigation tasks—Mind2Web and AITW."（摘要）
- "Its FLOPs can even be more than 10 times higher compared to employing a cross-module at a resolution of 1120."（§4.1）
- "CogAgent is an initial exploration of VLM-based GUI agent, and still has some shortcomings, e.g. imprecise output coordinates and incapability of processing multiple images."（§5）

## 核对说明
读的是 CVPR 2024 open-access PDF 的文本抽取，以及 arXiv HTML 的摘要和 §2。表 3 / 表 4 的题注在双栏 PDF 抽取里前后颠倒，我用表内的 Flan-T5-XL 52.0 / 38.9 / 39.6 与 Mind2Web 原文表 2 对齐，确认 58.2 那张是 Mind2Web；76.88 那张与正文 “+2.61” 对齐，确认是 AitW。VQA 表 1、表 2 扫过，没有逐项核对每个 VQA 数字。附录没读。
