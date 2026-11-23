# ScaleCUA：在真实桌面容器里自动写可执行裁判，再用它做在线 RL

## 一页读懂
| 项 | 内容 |
|---|---|
| 来源 | arXiv:2607.11185（abs 已打开，citation_date 2026-07-13；citation_title 为全大写 SCALECUA，正文作 ScaleCUA）/ arXiv 预印本 / 清华，部分作者实习于 Z.AI / https://github.com/THUDM/SCALE-CUA（仓库未再打开） |
| 读深度 | 全文（arXiv HTML） |
| 问题 | 可验证的桌面题不够，而且在线 RL 把步数很长的轨迹喂进训练引擎会极慢 |
| 它检查了什么默认假设 | 有了 GRPO 就能把电脑代理训上去；缺的只是再调一点奖励公式 |
| 发现问题的方式 | 拆开两个卡点：裁判函数造不出来，以及均匀抽样和逐步切轨迹浪费 rollout |
| 解决方式 | 训练：VeriGen 在 docker 里多代理改题和改裁判；Frontier Sampling 把 rollout 分给当前学得动的题；视觉上下文用滑动窗口 |
| 最强证据 | 同一 Qwen3.5-9B 管线，OSWorld：完整方法 68.7%，去掉 VeriGen 的基座 43.9%，去掉 Frontier Sampling 63.7%，去掉视觉滑窗 62.2%（表 4） |
| 品味 | A。同基座消融、公开资源承诺、以及一份训练题和榜单的重合审计放在一起。和 2025 年 OpenGVLab 的另一篇 ScaleCUA（2509.15221，跨平台数据）不是同一篇 |

## 一段话介绍
电脑代理做在线强化学习，奖励必须是确定性的：看文件系统、浏览器状态或一段 Python，而不是再叫一个模型判。作者认为这种「题 + 裁判」很难规模化，随机造出来的题又常常全对或全错，一组 rollout 没有优势信号。ScaleCUA 让多个代理在真实 OS 容器里反复改任务和裁判，号称得到 2.4 万以上可执行题、近 3000 道高质量 RL 题。训练时按每题近期成败把采样压到「正在会与不会之间」的题，并把长轨迹的截图收成最近若干张的窗口。Qwen3.5-9B 上，OSWorld 报到 68.7%（4 次 rollout 的标准差 ±0.7，表 2），ScienceBoard 54.0%（±0.5，表 3）。

## 动机
作者把可验证题定义成：配一个确定性裁判，给最终环境打分，不经过人或模型判断。GUI 任务默认只有环境和一句指令，没有这个裁判。

原文（第 1 节）：“A verifiable GUI task is one paired with a deterministic judge function (e.g., a filesystem check, a browser-state inspection, or a piece of Python code) that scores the final environment state without any human or LLM judgment.”

## 方法（或资源构成）
VeriGen 读环境说明和模型自己跑出来的轨迹，在活的 docker 里用多代理回路改题、改裁判。角色包括规则检查、模型裁判和修复代理。100 个以上工人通过共享的 docker 探针并行。Frontier Sampling 给每题维护采样权重，开训前挑当前能力边界上的题。Visual Context Segmentation 保留最近 K 张图（主实验 K=5），文字历史仍接得上，避免一步一条训练样本把训练引擎撑爆。算法是 GRPO，加了不对称裁剪和相对参考策略的 KL。基座写了 GLM-4.6V-Flash、Qwen3-VL-8B-Thinking、Qwen3.5-9B。

具体例子（图 2）：指令是安装 Orchis GTK 主题并在 GNOME 里切换。9B 模型的一条轨迹从看桌面、打开网站、下载解压、到终端和 gsettings，第 47 步 OSWorld 裁判返回 1.0。

## 实验
- 想回答：可验证题的规模、采样方式和多轮打包，各自对 OSWorld 有没有用；生成的裁判能不能执行、和人一不一致；训练题是否抄了测试题。
- 对比：表 2 混有他们自己的运行和从技术报告摘来的行。表注写明，没有子集分数的行直接摘自对应技术报告。Qwen3.5-9B 那一行子集是空的，总分 41.8，属于这一类。因此 41.8→68.7（文中写 +26.9）不是同一套评测脚本下的重跑。
- 主结果：表 2 他们自己的 ScaleCUA-Qwen3.5-9B 总分 68.7±0.7。表 4 同管线消融：完整 68.7，去掉 VeriGen 43.9，去掉 Frontier Sampling 63.7，去掉滑窗 62.2。裁判可执行率：完整回路 94.5%，去掉模型裁判代理降到 62.3%（表 4 右侧；正文写降 32.2 个点）。滑窗相对逐步切分，每步总时间 750s→265s，2.83 倍（第 4.3 节，图 6）。人工审计：每个应用域 10 条轨迹，可执行裁判与人一致 82.5%（第 4 节，细节附录 B.3）。重合审计（附录表 8）：OSWorld 训练子集 1049 条，全文 JSON 重复 0，指令完全重复 0，目标近重复 0.19%（2 条），裁判代码完全复用 2.10%（22 条）。
- 能支持的：在他们的管线里，题和裁判、采样、滑窗都贡献了 OSWorld 分数；生成裁判大多能跑。支持不了的：68.7 已经在完全相同的协议下超过表 2 里每一个摘录的闭源数字。那些行许多带 †§，且没有子集分数。

## 局限
- 作者承认的（第 5 节 Limitations）：每集最多 50 步；环境是 Ubuntu；只验证了 8B–9B 这一档。
- 我看到的：奖励仍可能被钻。人与裁判只在抽查上一致 82.5%，剩下的不一致会直接变成 RL 的对错标签。表 8 有 22 条 OSWorld 训练题复用了评测裁判模板，作者说这是通用模板而不是抄题，但通用模板若和测试题的检查逻辑相同，模型可以学「怎样的文件改动能过这类检查」。另外，VeriGen 就在 OSWorld 的 docker 里造题，应用分布和测试榜是同一套软件。近重复率低只说明指令文本不像，不说明解法不重叠。表 2 的 41.8 和表 4 的 43.9 是两个「基座」，引用时不能写成同一个对照。

## 品味判断
1. 问题来自 RLVR 搬到 GUI 之后的具体报废方式：全对或全错的题没有组内优势，逐步切轨迹把训练样本数乘以步数。这是跑过在线 GUI RL 的人会撞上的，不依赖某个私有数据。换一个有 OS 容器集群的团队可以做 VeriGen；没有 100 路 docker 就做不大，但「训练题和测试题做一次重合审计」谁都能做。
2. 最能说服审稿人的是表 4 的同基座消融，加上附录表 8 的重合审计。前者说明涨分不是换了个模型名字，后者提前回答「是不是背了 OSWorld」。
3. 可模仿的实验：生成题进训练集之前，对官方测试集做四列审计：全文重复、指令规范化后重复、指令相似度超过 0.9 的近重复、裁判代码是否原样复用。近重复阈值和「复用了通用模板」要分开写。再抽每个域固定条数，让人重判裁判的对错，报告一致率，不要只报告可执行率。
4. 论文表 1 把自己和 GUI-Genesis、OS-Genesis、OpenCUA、ComputerRL、EvoCUA 放在一张能力清单上。GUI-Genesis 的环境是重建的轻量网页，这篇是活的 OS 容器。它没有和 GUI-Shepherd 那种过程奖励比，奖励假设就是终态裁判。

## 和 CUA 评测 / 换路鲁棒性的关系（公开层面）
终态脚本奖励可以被「看起来不同、检查逻辑相同」的题泄露。他们的表 8 是一个可照搬的最低限度审计。换应用之后，50 步上限和 Ubuntu-only 会先挡住结论。

## 原文摘录
1. 第 1 节：“Under GRPO-style training, tasks where the model always succeeds or always fails contribute zero within-group advantage and waste the entire rollout group.”
2. 第 4.3 节：“Starting from full ScaleCUA (68.7%), removing VeriGen entirely drops the model to its 43.9% base score, while removing Frontier Sampling or Visual Context Segmentation alone yields 63.7% and 62.2% respectively.”
3. 附录 B.6：“Objective near-duplicates are rare (0.19% on OSWorld and 0.36% on ScienceBoard). … OSWorld shows a small amount of exact evaluator reuse (2.10%).”

## 核对说明
abs 已打开，作者 Bowen Lv、Xiao Liu 等与 HTML 一致。表 2 的 68.7±0.7、表 4 的 43.9/63.7/62.2/94.5、表 8 的 0.19% 与 2.10% 均来自该 HTML。82.5% 写在第 4 节正文，指向附录 B.3，我没有逐行核对附录里的 10×域是否正好凑出这个百分比的分母。无 PDF 页码。与 2509.15221 的 ScaleCUA 不是同一工作。venue 为预印本。
