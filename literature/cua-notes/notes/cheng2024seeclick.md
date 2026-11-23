# SeeClick：只看截图的 GUI 智能体，先把「点哪里」练好

## 一页读懂
| 项 | 内容 |
|---|---|
| 来源 | arXiv:2401.10935（v2，2024-02-23）；ACL 2024 主会长文（ACL Anthology 2024.acl-long.505，第 9313–9332 页）；南京大学 + 上海 AI Lab；https://github.com/njucckevin/SeeClick |
| 读深度 | 全文（主文 + 局限；附录没细读） |
| 问题 | 靠 HTML 之类结构化文本的 GUI 智能体，在桌面、iOS 上拿不到结构，又冗长；纯视觉做法缺一个关键能力：根据指令找到屏幕上的元素 |
| 它检查了什么默认假设 | 默认「通用多模态大模型天然会点屏幕」 |
| 发现问题的方式 | 初步研究（preliminary study）发现通用 LVLM 点不准，再单独拿出「定位」（grounding）来测 |
| 解决方式 | 资源 + 训练：约 1M 数据继续预训练 Qwen-VL，加 ScreenSpot 评测集 |
| 最强证据 | Table 1：ScreenSpot 平均点击准确率 SeeClick 53.4%，CogAgent 47.4%，GPT-4V 16.2%，Qwen-VL 5.2% |
| 品味 | A：把「定位」从智能体里拆成独立能力、独立基准，后来多篇工作沿用 ScreenSpot |

## 一段话介绍
2023 年的 GUI 智能体大多读 HTML，让 LLM 在候选元素里选一个。SeeClick 换成看截图、直接输出点击坐标。作者发现这样做的瓶颈是「定位」：通用 LVLM 根本不会在 GUI 里找元素。于是他们从 Common Crawl 抓约 30 万网页，用 HTML 里「有可见文字」和「有 title 提示」的元素自动造定位数据，再加移动端公开数据，对 Qwen-VL 做继续预训练，并建了 ScreenSpot 来测定位。最后在 MiniWob、AitW、Mind2Web 三个任务上证明：定位越好，下游越好。

## 动机
> "…we have discovered a key challenge in developing visual GUI agents: GUI grounding – the capacity to accurately locate screen elements based on instructions."（摘要）

引言列了文本表示的三个问题（§1）：结构化文本不一定拿得到（iOS、桌面）；啰嗦且丢掉布局、图片、图标信息；HTML、DOM、Android VH 各不相同，要为每种定制观察和动作空间。

## 方法（或资源构成）
- **数据**（§3.2）：
  - 网页：约 30 万个网页（Common Crawl 最新库）。每页收两类元素：显示可见文字的元素；带 `title` 属性（鼠标悬停提示）的元素。前者给「文字目标」，后者给「图标/控件目标」。另加网页 OCR 任务（给坐标预测文字）。
  - 移动：widget captioning（约 2 万张截图、4 万控件、10 万条描述；把描述当指令、控件当目标，反过来就是定位数据）、RICO 自动抽取、UI 摘要。
  - 通用：LLaVA 指令数据，保持通用能力。
  - 合计约 1M 条，每个 GUI 任务配 30 个提示模板。
- **训练**（§3.3）：在 Qwen-VL（448×448 输入）上继续预训练约 10k 步（约 1 个 epoch），LoRA 微调视觉编码器和 LLM。
- **ScreenSpot**（§4）：600+ 张截图、1200+ 条指令，覆盖 iOS、Android、macOS、Windows、网页，分文字元素与图标/控件两类；指标是预测点是否落在目标元素的框内。
- **一个具体例子**（Figure 1）：指令「Download the e-receipt with the last name Smith and confirmation number X123456989」，文本智能体要从 HTML 里选 element_id=206；SeeClick 直接输出 `{"action":"click","loc":[0.46,0.62]}`。

## 实验
- **想回答什么**：定位预训练有没有用？定位好是不是下游任务就好？
- **ScreenSpot**（Table 1，点击准确率）：

| 模型 | 参数 | 平均 | 备注 |
|---|---|---|---|
| Qwen-VL | 9.6B | 5.2% | 通用，未专门训练 |
| GPT-4V | - | 16.2% | |
| CogAgent | 18B | 47.4% | GUI 专用 |
| SeeClick | 9.6B | 53.4% | 参数更少 |

  - 分项里不全是 SeeClick 第一：网页文字元素 CogAgent 70.4% 对 SeeClick 55.7%；桌面文字元素 74.2% 对 72.2%。SeeClick 的优势在图标/控件，例如移动端 52.0% 对 24.0%（Table 1）。
- **MiniWob**（Table 2，35 个任务的纯视觉组）：SeeClick 67.0%（2.8K 训练数据），Pix2Act 64.6%（1.3M），Qwen-VL 48.4%（同样 2.8K）。作者写 SeeClick 用不到 0.3% 的数据超过 Pix2Act（§5.2.1）。
- **AitW**（Table 3）：作者认为按 episode 划分有泄漏风险（测试指令在训练里出现过，每条指令平均约 20 条相似轨迹，§5.2.2），改成按指令划分，每条指令只留 1 条轨迹。
- **Mind2Web**（Table 4）：SeeClick 的 Cross-Task Step SR 25.5%，Qwen-VL 13.3%，「几乎翻倍」；但仍低于用 HTML 候选的方法。
- **grounding 与下游的相关**（§5.2.4，Figure 6）：比较若干检查点在 ScreenSpot 与三个下游任务上的平均得分，随定位提升一起上升。
- **能支持的结论**：同一基座、同样小数据下，加定位预训练明显更好；定位与下游相关。
- **支持不了的结论**：「因果」只是同一条训练曲线上的相关，没有单独操纵定位而固定其他因素的实验。

## 局限
- **作者承认的**（Limitations）：动作空间只有点击和输入，没有拖拽、双击；受开源 LVLM 水平限制，多步任务必须用任务数据再训练。另外在 Table 5 处提到：把三个下游任务合成一个统一模型，成绩略有下降，「可能由于不同 GUI 界面差异大」。
- **我看到的**：
  - ScreenSpot-Pro 的作者写 ScreenSpot 的截图是「裁剪到局部区域」的（其 Figure 3）。他们在 Table 3 里重测，SeeClick-7B 平均只有 1.1%（见 `li2025screenspotpro.md`）。同一模型从 53.4% 掉到 1.1%，是因为基准的分辨率和场景变了，这个对比跨了两篇论文。
  - Mind2Web 上视觉版低于 HTML 版（Table 4，作者自己写了原因：预测坐标比选候选难得多）。

## 品味判断
1. **问题怎么发现的？** 是「初步研究」里观察到通用 LVLM 的失败集中在点不准，把这个观察变成训练目标和基准两件事。换一个团队能做，难在想到把定位单列出来，数据构造本身（HTML 里取可见文字和 title）很便宜。
2. **最能说服审稿人**（我的判断）：Table 2 里同一个 Qwen-VL、同样的 2.8K 数据，加不加定位预训练差近 20 个点（48.4 → 67.0），把「定位有用」做成了一个干净的对照。
3. **可模仿**：怀疑某个能力是瓶颈时，做「同基座、同数据量、有无该能力预训练」两组，再用一个独立的、覆盖多平台的小基准（ScreenSpot）单独测它，最后拿几个检查点画「该能力 vs 下游得分」的曲线。
4. **没比的工作**：Aguvis 的审稿意见（OpenReview，经 `reviews/gui-agent-ai-venues.md` 二手引用，未自行打开）把 SeeClick 当作「纯视觉 + grounding」的已有做法来对照，说明它很快成了参照物。

## 和 CUA 评测 / 换路鲁棒性的关系（公开层面）
SeeClick 把「看见哪里」与「做什么」拆开测，这个思路可以直接用来区分失败是定位问题还是规划问题；ScreenSpot 与 ScreenSpot-Pro 的落差也提醒：同一能力在换了截图尺寸和场景之后数字可以大幅变化。

## 原文摘录
- "GUI grounding – the capacity to accurately locate screen elements based on instructions."（摘要）
- "SeeClick exceeded the sota visual method Pix2Act, using less than 0.3% training data."（§5.2.1）
- "SeeClick currently simplifies the GUI action space to mainly focus on clicking and typing, excluding complex actions like dragging and double-clicking."（Limitations）

## 核对说明
读的是 arXiv v2 PDF；摘要、§1、§3、§4（ScreenSpot）、§5.1、§5.2（MiniWob、AitW、Mind2Web、相关性）、结论与局限读过，Table 1、2、4 的数字核对过；Table 3（AitW）只抽查了原文描述，未逐格核对。附录没细读。venue 依据 ACL Anthology 页面元数据（会议名 Proceedings of the 62nd ACL, Volume 1: Long Papers，2024/8）。
