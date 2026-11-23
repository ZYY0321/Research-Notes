# GSAR：用成功轨迹的终屏当锚，给手机 GUI 的模型裁判一个对照

## 一页读懂
| 项 | 内容 |
|---|---|
| 来源 | arXiv:2608.22847（abs 已打开，citation_date 2026-08-24；所读 HTML 标明 latest v2，2026-11-03，Full text of v2）/ arXiv 预印本 / 单位未写在 abs 的 citation 作者元数据里 / https://github.com/lossooo/GSAR（仓库未再打开） |
| 读深度 | 全文（v2 HTML） |
| 问题 | 手机 GUI 的在线 RL 要么靠手写规则，要么靠会幻觉的模型裁判；环境也造不出多样的可重置起点 |
| 它检查了什么默认假设 | 给模型裁判多看动作历史，就足以判断这题做完没有 |
| 发现问题的方式 | 同一批轨迹上，把「无参照 / 只给终屏 / 给终屏加锚点 / 再加动作史」拆开比准确率 |
| 解决方式 | 训练：模型自己探索、出题、跑成功轨迹；把成功终屏上与任务相关的控件标成锚，在线时用锚当奖励参照 |
| 最强证据 | 离线轨迹判定，Qwen3-VL-8B 上 GSAR 准确率 90.2、F1 91.0；四种裁判模型平均准确率 91.5、F1 91.8（表 2） |
| 品味 | B。锚点这个对照实验干净，在线涨幅小，而且在线评测把训练题留在了全量榜里 |

## 一段话介绍
规则奖励准，但每道新题都要人写检查函数。模型看截图和动作史来打分，又会把没做完的界面判成完成，尤其是两张图很像的时候。GSAR 先让模型在手机应用里乱点、出题、再让 GPT-4o 去执行，留下成功轨迹和当时的环境快照。成功轨迹的最后一屏被标出「这题真正相关的控件」，称为锚。之后判一条新轨迹，模型同时看到动作史、这张锚图和锚点。离线看，这个参照把准确率抬到 90% 以上，接近作者心目中 100% 的规则上限。在线看，同一套 UI-TARS-7B-DPO 上，GSAR 把 AndroidWorld 从 26.7% 做到 30.2%，手写规则做到 32.8%（图 6）。

## 动机
作者说，模型裁判缺少「做完时长什么样」的显式参照，所以假阳性高。规则方法又无法跟着自动出的题一起扩展。

原文（第 3.2 节附近，Limitations in Action History Based Evaluation）：“Compared with rule-based approaches, model-based methods are less reliable because the model lacks explicit references of completed task states.”

## 方法（或资源构成）
数据飞轮分三步。先随机点出一个探索轨迹，用视觉模型按截图出若干用户任务，并保存当时的环境当起点。再用 GPT-4o 执行，丢掉失败和冗余。多轮执行会把应用从「刚安装、几乎是空的」点成更杂的状态，下一轮题就从新状态里出。作者称之为自进化。成功轨迹的终屏由 GPT-4o 框出任务相关元素，自动标注总体准确率 91.5%（表 4）；删除类因为目标消失，被他们记成 100%。在线奖励仍是模型打分，输入是动作史加上这张带锚的参照图。基座实验用了 UI-TARS-7B-DPO，也在 Qwen2.5-VL-7B 上用合成数据做了 SFT。

具体例子：一道「把某条记录删掉」的题，终屏上那个记录不在了。锚几乎不用细定位，裁判只要看见参照图里没有它。问答类则相反：答案还没说出来，画面可能已经像终态，作者承认这时会提前给正奖励。

## 实验
- 想回答：合成轨迹能不能提升离线动作匹配；锚是否让完成判定更准；在线 RL 是否接近规则奖励。
- 离线判定集：AndroidWorld 上 GUI-Owl-7B 和 Qwen2.5-VL-7B 的轨迹，共 315 条，164 正、151 负（附录）。在线：从 AndroidWorld 抽 42 题训练，在全量榜上评测。
- 主结果：表 2，Qwen3-VL-8B 的准确率/F1：DigiRL 67.0/64.9，DistRL 67.9/69.3，StepCritic 64.4/74.1，只给目标状态 84.1/84.2，只给锚 87.6/88.2，GSAR 90.2/91.0。四种模型平均，GSAR 91.5/91.8。图 6：UI-TARS-7B-DPO 26.7%，GSAR 30.2%（+3.5），规则 32.8%（+6.1）。表 1 的 SFT 数字（AndroidControl 低/高分 EM +5.2 / +3.2，GUI-Odyssey TM +6.3）是合成数据的离线动作匹配，不是在线成功率。
- 能支持的：在这 315 条上，终屏参照比只看历史更准，锚再高一截。支持不了的：在线 +3.5 个点是新能力，而不是记住了那 42 道训练题。全文写评估在全量榜上做，没有写把这 42 题从分母里拿掉。

## 局限
- 作者承认的（Limitations）：每题只认一个终态，同一目标可以有多条合法终屏。问答可能在真正说出答案之前就给正奖励。删东西这类完成状态不一定能靠视觉元素标出来。
- 我看到的：奖励和数据都有空子。锚来自 GPT-4o 判为成功的轨迹；若这条「成功」本身是假完成，锚会把错误终屏教给裁判，表 4 的标注准确率 91.5% 说明自动框也有近一成是错的。在线训练的 42 题来自 AndroidWorld，测试又是 AndroidWorld 全量，存在题目泄漏，作者没有单列「扣掉训练题之后的成功率」。自进化出的题分布由同一个执行模型决定，模型走不到的页面不会变成题。

## 品味判断
1. 问题来自一张对照图：规则准但写不动，模型裁判可扩展但假阳性高。他们没有发明新的策略梯度，而是给裁判加一张「做完时的屏幕」。有 Android 模拟器和一个能出框的模型就能做。
2. 最有力的是表 2 的阶梯：同一批轨迹上，从无参照到终屏再到锚，准确率往上走，而且 Qwen3-VL-8B 和 GPT-4o 都过了 90。这比只报 AndroidWorld +3.5 更像一个会改变做法的结果。
3. 可模仿的实验：固定一组正负轨迹，裁判模型也固定，只改变参照（无 / 终屏 / 终屏+框 / 再加动作史），报告准确率和假阳性。在线实验必须把训练题从测试分母里去掉，并同时画规则奖励的曲线，看模型裁判是否只是更吵的规则。
4. GUI-Shepherd、OS-Themis 做的是过程或里程碑奖励。GSAR 仍是结果奖励，卖点是参照从哪来。它没有和「同一终屏、不画锚」以外的过程奖励在在线 RL 里比。

## 和 CUA 评测 / 换路鲁棒性的关系（公开层面）
完成判定若只看动作史，会把相似界面的失败判成成功。锚点实验说明参照屏幕能补这个洞，但也把「哪张图算做完」锁死成一条轨迹的终屏。换一条合法路径时，这个奖励会误罚。

## 原文摘录
1. 第 3 节：“model-based methods are less reliable because the model lacks explicit references of completed task states.”
2. 第 5 节附近：“GSAR increases the performance to 30.2% (+3.5%), while rule-based rewards achieve 32.8% (+6.1%).”
3. Limitations：“it considers only a single final state as the success criterion for each task, whereas a task may be achievable through multiple alternative solutions. Moreover, for question-answering tasks, our method may assign a correct reward before the actual correct answer is produced.”

## 核对说明
abs 标题、作者 Long Zhang 等已核对。表 2 的 90.2 来自 v2 HTML 中 Qwen3-VL-8B / GSAR / Acc 那一格，本批抽查对过这一格。图 6 的 26.7 / 30.2 / 32.8 在正文，不在表格。单位未在 citation 元数据中出现。venue 为预印本。
