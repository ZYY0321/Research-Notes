# MobileGym GUI + Tools 任务契约构建与审查指南

本文用于指导后续同事或 Coding Agent 批量构建、审查和维护 MobileGym 中的
GUI + App Tools 任务。这里的“任务契约”不是只有一句 instruction，而是以下内容的
整体：

```text
Instruction + Setup + Environment + Tool Surface + Verifier
```

文档总结了 Hybrid Tools V1 到 V6 的实际迭代、模型轨迹审查、用户人工复核和最终
修订经验。目标是让后续新增任务在进入评测、SFT 轨迹生成或 RL 训练前，已经具备
清晰、可完成、可复现、可公平评分的闭环。

文档状态：2026-07-16。

## 1. 核心原则

### 1.1 一个任务是五层契约

只有同时满足以下条件，任务才可以计分：

1. **Instruction**：自然语言准确描述用户真正要求的结果。
2. **Setup**：初始化出唯一、稳定、可观察的目标和必要干扰项。
3. **Environment**：GUI 中确实存在能完成任务的路径，交互能正确提交业务状态。
4. **Tool Surface**：工具看到的数据、候选域和业务状态与 GUI 一致，且工具不是隐藏
   的完整任务答案 API。
5. **Verifier**：只检查指令要求的最终结果，既不漏掉明确要求，也不附加隐藏要求。

任一层与其他层不一致，SR 就混入了 benchmark 缺陷，不能再干净表示 Agent 能力。

### 1.2 优先避免合理完成被误判为失败

本项目采用以下判定偏好：

- 指令明确、结构化、无歧义的要求应严格检查。例如指定收件人、金额、日期、数量、
  是否支付、是否启用提醒。
- 自由文本允许语义等价、合理空白、标点、单位和日期格式差异。
- 如果一句指令存在两种普通用户都可能接受的理解，不能只因 Agent 选择了其中一种
  就判失败。应当澄清指令，或让 verifier 接受全部合理结果。
- 对“似有似无”的语用要求，宁可适度宽松，也不要用隐藏的单一措辞制造假阴性。
- 对指令明确强调的要求仍应严格。例如“最后一句加上‘我最近得省着点了’”就必须
  校验该结尾，不能因文本 verifier 通常宽松而忽略。

这个偏好不是让 verifier 无条件放宽。错误对象、错误数值、错误收件人、漏做明确
子任务、产生禁止副作用，仍然必须失败。

### 1.3 结果导向，不绑定执行路径

同一个任务应尽量同时支持：

- 纯 GUI 完成；
- GUI + Tools 混合完成；
- 不同但业务等价的操作序列。

Verifier 应检查最终业务状态，而不是检查 Agent 是否调用过某个工具、是否访问过某页、
是否使用某个内部节点 ID。除非用户明确要求“搜索”“打开”“播放”等本身就是目标，
否则搜索快照、页面访问历史和工具调用历史不应成为成功条件。

“支持纯 GUI”不能只靠代码静态阅读或 Hybrid 成功轨迹推断。Hybrid 工具可能正好绕过
失效控件、缺失页面或 GUI 未展示的字段，使工具增益中混入环境缺陷。正式比较前，
必须把纯 GUI 可完成性作为独立契约，用 GUI-only 轨迹和浏览器证据验证。

### 1.4 高分和低分都不能替代契约审查

- V1 的 96.7% 主要说明任务过于简单，不代表评测质量已经很高。
- V2 的 28.0% 混入了指令漂移、隐藏条件和环境缺陷，不代表任务真正困难。
- V3 的原始失败中，大部分后来被确认是 benchmark failure 或歧义。
- V4/V5 经过逐条契约审查后，强模型高分更多反映工具效率和模型能力，而不是简单
  说明任务无效。
- V6 进一步用强模型 GUI-only 失败轨迹反查环境和 verifier，说明“Hybrid 能完成”
  仍不足以证明 Hybrid/GUI-only 差值全部来自 Tools。

模型分数只能用于发现问题，不能用于证明任务契约正确。

### 1.5 V1-V6 各自提供了什么经验

| 版本 | 主要做法 | 关键结论 |
| --- | --- | --- |
| V1 | 90 条固定任务跑通 GUI、Tools、Setup、Verifier 和轨迹记录。 | 工程闭环成立，但指令像操作步骤、任务重复且强模型 96.7%，更像功能 smoke。 |
| V2 | 50 条高难任务，其中 40 条基于官方 L3/L4，10 条跨 App。 | 复杂度提高不等于有效性提高；改写 instruction 后继承旧 verifier 是主要缺陷。 |
| V3 | 扩展到 203 个候选工具，精选 80 条官方/淘宝/跨 App 任务。 | 混合度和覆盖提升，但时间、候选域、隐藏约束和环境不可完成分支仍大量污染失败。 |
| V4 | 逐条审查 80 条，保留 76 条，删除 4 条不可稳定完成任务，冻结模拟时间。 | 需要把 instruction/setup/environment/verifier 当成整体，并用真实轨迹发现系统性缺陷。 |
| V5 | 对 V4 高中风险项做 task-local 契约修订和语义 matcher 加固，当前累计修订 42 条。 | 文本应宽容格式、业务状态应严格；模型运行后仍要持续审查假阴性、工具 side effect 和 runtime。 |
| V6 | 对 V5 做强模型 Hybrid/GUI-only 配对审查，删除 1 条 GUI 信息不足任务，修复天气状态、时间滚轮、GUI 可见并列和文本等价表达，保留 75 条。 | 纯 GUI 可完成性是独立发布门禁；只有排除 GUI 合约缺陷后，setting 差值才可主要解释为工具增益。 |

## 2. 任务指令如何设计

### 2.1 写用户目标，不写操作教程

任务应保持高层、自然、结果导向。不要在 instruction 中直接提供操作路径。

不推荐：

```text
打开微信，点击老板聊天，记住两个文件名；打开文件管理器，进入 Download/待提交，
依次移动两个文件；再打开微信，把两个文件名发给老板。
```

推荐：

```text
在微信看看老板最近让我补交的材料，然后在 Download/待提交 里找到对应文件，
移动到 Documents/submission，并把文件名微信回复给老板。
```

前者主要测指令跟随和点击执行，后者才会测信息提取、跨 App 记忆、对象消歧、文件
操作和收尾。

### 2.2 明确评分边界，但不要泄露解法

应该明确的是 verifier 必须判断、且普通用户无法唯一推断的边界：

| 容易歧义的维度 | Instruction 应明确什么 |
| --- | --- |
| 相对日期 | 是否包含今天，窗口从今天还是明天开始，是否为自然周或滚动 N 天 |
| 排名 | 候选集合、排序字段、升降序、并列规则 |
| “第几个” | 列表方向，例如按实际时间从早到晚的第 3 个 |
| 统计 | 时间范围、记录类型、是否递归、是否排除归档 |
| 会议“最长” | 预定时长、实际参会时长，还是开始到结束时长 |
| 买票 | 日期、线路、乘车人、是否高铁、是否需要提交订单 |
| 输出 | 收件人、必须包含的事实、是否要求完整标题或生成 ID |
| 条件分支 | 条件依据、各分支必须做什么、禁止做什么 |
| 集合任务 | 是“任一”“全部”“恰好 N 个”还是“至少 N 个” |
| 保留约束 | 哪些对象必须保留，通配语义是否存在例外 |

不应明确的是具体点击顺序、应调用哪个工具、目标内部 ID、测试集答案或工具排名提示。

### 2.3 任务难度来自依赖关系，而不是句子长度

优先使用以下可稳定验证的难度来源：

1. **跨 App 信息传递**：在 A 获取 X，在 B 使用 X。
2. **排序与聚合**：遍历完整候选集，求最大、最小、Top-K、总数或总时长。
3. **时间推理**：从设备日期和业务日期推导昨天、明天、提前一周等结果。
4. **条件分支**：根据天气、冲突、余额等信息选择不同副作用。
5. **多渠道一致性**：新生成的会议号必须同时写入 Notes、微信和短信。
6. **集合完备性**：处理所有合格项，同时排除不合格项。
7. **干扰项与消歧**：同名、相近日期、相近金额、归档目录、不同门店。
8. **长程收尾**：工具获得信息后，仍需通过 GUI 保存、发布、支付、开启提醒。

不要依靠以下方式制造“难度”：

- 隐藏 verifier 条件；
- 环境页面不可用；
- 目标数据不唯一；
- 把 UI 不显示的字段作为答案；
- 用精确字符串格式卡 Agent；
- 人为压低 max steps 到正常路径无法完成。

### 2.4 GUI + Tools 混合任务的要求

单条任务不必强制调用某个 App Tool，但整个核心评测集应满足：

- App Tools 是可选加速器，Verifier 不检查工具调用。
- 任务原则上存在纯 GUI 路径，GUI-only 和 Hybrid 共用同一 setup/verifier。
- 工具应稀疏地覆盖查询、导航或草稿准备，给 GUI 留出阅读、选择、确认、敏感提交
  或工具未覆盖的 App 阶段。
- 不要求每条任务机械地“至少一次 GUI + 一次 Tool”。这会诱导设计者构造不自然
  的流程。应通过 suite 级轨迹统计确认实际混合度。
- 可以包含没有 App Tools 的 App。它们能迫使 Agent 在部分阶段使用 GUI，并提高
  跨 App 组合多样性。
- Runtime 应根据当前前台 App 动态暴露该 App 的工具。任务中的 `candidate_tools`
  只用于覆盖统计和审查，不等于把这些工具在每一步全部塞进 prompt。

Hybrid 与 GUI-only 做配对比较时，除了 App Tools 是否暴露外，其余实验条件应一致：

- 相同 instruction、setup、模拟时间、verifier、截图和 max steps；
- 相同 GUI 动作语义和同一模型适配器；
- GUI-only 仍保留 `mobile_use` 和通用 `open_app`，只移除 App 业务工具；
- 不为 GUI-only 额外提供答案、完整日期或 step-by-step 提示；
- 模型专用坐标、图片 detail 或输出 parser 必须在两个 setting 中保持一致。

如果 GUI-only 使用了错误坐标体系或缺失模型必需的图片分辨率，这属于 runtime 配置
不公平，不能把低分归因于没有 App Tools。

一个有价值的典型结构是：

```text
工具定位候选日期 -> GUI 读取隐藏详情 -> 工具预填草稿 -> GUI 设置提醒并保存
-> 另一 App 工具或 GUI 完成通知
```

### 2.5 保持任务分布多样

批量生成时不要让同一个模板只替换实体名。至少按以下维度做覆盖统计：

- 单 App / 双 App / 三 App 以上；
- Query / Mutation / Conditional / Transfer / Aggregation；
- 纯文本、数值、日期、地址、生成 ID、文件、购物车、会议等数据类型；
- GUI 敏感提交、GUI 视觉读取、工具查询、工具导航、工具草稿；
- 单对象、Top-K、精确集合、递归目录、条件分支；
- 正常完成分支和拒绝/无操作分支。

V1 中大量“检索 + 创建”任务过于相似。后续不能只看工具覆盖数量，还要看任务结构
和推理依赖是否重复。

### 2.6 工具描述不能泄露 benchmark

工具只描述一般业务语义。例如最近播放工具可以说明排序方向和时间字段，但不能写：

```text
回答“今天第三首”时请使用 position_from_earliest=3。
```

这既泄露测试解法，也说明工具返回本身缺少足以支持通用推理的时间信息。正确做法是
返回 `played_at`、本地日期和稳定顺序，让 Agent 自己计算。

### 2.7 步数预算必须来自可行路径

- 先估算一条合理 Hybrid 路径和一条合理 GUI-only 路径。
- max steps 应覆盖正常路径和有限恢复，不应根据某个模型刚好能否通过来调整。
- 任务需要 50 到 60 步并不自动无效，但应确认耗时来自真实长程操作，而不是控件循环。
- 对接近步数边界的任务可做敏感性实验，但正式 suite 使用统一预算。

## 3. Setup 与环境设计

### 3.1 固定完整模拟时间

凡是涉及今天、昨天、今年、最近 N 天、聊天相对时间、天气预报、播放历史和文件时间，
都必须绑定同一个模拟时间源：

- Launcher 和状态栏；
- App 默认相对数据；
- task setup；
- GUI 展示；
- App Tool 输出；
- verifier 的时间窗口。

模拟时间必须在 App 模块初始化前生效。V4 曾在 reset 后才设置时间，Weather 和微信
默认数据已经按 host 时间 eager-load，造成 Launcher 是 7 月 12 日而微信出现 7 月
13 日聊天。最终修复是在页面首次启动前通过 URL 参数冻结时间。

是否把完整日期写进 system prompt 是另一件事。可以保留 temporal grounding 难度，
但环境中必须有稳定、合理的方式观察到任务所需时间。若年份根本不可观察，“今年”
任务就会混入 benchmark 缺口。

### 3.2 初始化必须产生唯一 ground truth

Setup 完成后应能程序化计算唯一答案。逐项检查：

- 排名是否唯一，是否存在并列；
- 同名对象是否能靠日期、店铺、状态等信息消歧；
- 时间窗口内是否恰好有预期记录；
- 条件分支是否由固定数据唯一决定；
- 目标是否已经在初始状态中成立；
- 默认数据是否比注入目标更符合 instruction。

V2 Transfer06 注入了一个闹钟，却没处理默认状态中更早的闹钟。Agent 合理选择默认
闹钟，verifier 却硬编码注入目标。这就是 setup contamination。

### 3.3 干扰项要真实，但必须可区分

好的干扰项用于测试筛选和保留能力：

- 上周、本周和更早的流水截图；
- 当前日志与 archive 日志；
- 多家同品牌门店及不同距离；
- 多本有进度、已完成、未开始的书；
- 相似商品但不同店铺、规格或数量。

坏的干扰项是视觉和语义上完全重复、却只有隐藏 ID 不同。例如 V2 Official15 中多对
重复图片没有可见 hash 或唯一线索，verifier 却指定其中一对。这样的任务没有公平
ground truth。

### 3.4 每个固定任务只保留一个确定分支

当前 benchmark 的一个 case 可以固定在某个条件分支，不要求同一 case 同时覆盖所有
分支，但必须：

- setup 明确落在哪个分支；
- verifier 只执行对应分支；
- 另一分支没有残留隐藏要求；
- suite 级别另有任务覆盖重要分支，或明确记录覆盖缺口。

例如“03:30 有空则建会，否则通知没空”的固定 setup 可以只覆盖冲突分支，但不能在
冲突分支仍检查会议和短信副作用。

### 3.5 Setup 应最小、隔离、可重复

- 每条任务 reset 到已知默认状态后再注入。
- 只修改相关 App 和 OS provider，不污染无关 App。
- 使用稳定 ID，避免碰撞已有记录。
- 同一任务重复 setup 三次应得到相同 ground truth 和初始 verifier 结果。
- 多 worker 使用隔离 browser context，不共享任务状态。
- setup 不把答案或 verifier 目标写进 Agent 可见的调试字段。

### 3.6 GUI、Tools、State 必须来自同一业务事实

同一对象在以下位置必须一致：

```text
GUI visible value == Tool result == final app/store state == Verifier selector
```

典型错误包括：

- Weather GUI 只显示白天“多云”，verifier 却用隐藏夜间“雨”决定带伞。
- GUI 新增南京后显示 `--`，Tool 却能读到完整天气。
- RedBook GUI 可滚动 40 条，verifier 永久只看前 20 条。
- 地图工具截断前 50 条后声称 `truncated=false`，verifier 用全量候选。
- 腾讯会议昵称在输入框里改变，但保存到 participant state 的仍是旧昵称。

这些问题应在环境或共享 selector 层修复，而不是通过放宽 verifier 掩盖。

### 3.7 先确认环境真的支持目标状态

对所有 mutation 和敏感分支，用真实浏览器完成一次：

- 页面能打开；
- 控件能操作；
- 保存/支付/发布/退款后状态真的落库；
- 返回或重新打开页面仍能看到结果；
- 后续 GUI 操作不被工具调用破坏。

如果功能未实现，应修复环境或删除任务。V3 删除了持续 loading 的 Bilibili 收藏夹、
未实现候补的 12306 场景、不可稳定生成路线的地图任务，以及昵称视觉修改不落库的
腾讯会议任务。不能降低 verifier 来假装这些任务可完成。

“某个按钮失效”也不自动等于任务无效。需要继续判断：

- 若该按钮是唯一合理路径，或 verifier 所需事实根本没有其他 GUI 可见入口，任务无效；
- 若存在稳定、可发现、能在预算内完成的替代路径，并有成功轨迹或浏览器证据，任务可
  保留为 GUI 恢复能力测试；
- 若替代路径只在源码中理论存在、实际页面持续空白或状态不落库，仍按环境缺陷处理；
- 若 GUI 路径需要穷举大量对象，应验证 max steps 足够，不能用“理论可穷举”掩盖
  不合理的交互成本。

## 4. Verifier 设计

### 4.1 先写“判定意图”，再写代码

每个任务应先用中文列出 verifier 的完整意图，例如：

```text
1. 相对初始状态新增一个会议，标题、日期、时长和密码正确。
2. 取该新会议生成的同一个会议号。
3. Notes、发给陈静的新微信、发给张三的新短信都包含该会议号和密码。
4. 不接受初始已有会议，也不接受三个渠道使用不同会议号。
```

只有自然语言意图和 instruction 对齐后才实现代码。V5 的
`TASK_VERIFIER_INTENT_AUDIT.md` 就是这种逐条展开，它比直接 review helper 名称更容易
发现隐藏约束。

### 4.2 使用 initial/final diff

凡是“新建、发送、支付、收藏、启用、移动”都应比较初始和最终状态：

- 新消息必须是新增 outgoing message，不能命中历史消息。
- 新会议不能复用 initial active meeting。
- 新闹钟必须是新增且 enabled，不能命中同一时刻的默认闹钟。
- 新订单必须是本轮新增订单。
- 删除/移动必须验证源状态变化，而不是只看目标存在。

如果只检查 final state 中“存在一个符合项”，初始状态可能直接通过，或 Agent 可以
借用已有对象绕过任务。

### 4.3 明确要求要检查完整

Instruction 中明确写出的每项都要覆盖。常见漏检：

- Top-3 只检查金额，不检查交易标题和逐笔配对；
- 要求高铁，却只检查线路和日期；
- 要求“约他一起跑步”，短信只检查日期和天气；
- 要求恰好各 2 首，verifier 使用 `>=2`；
- 要求数量 1、默认规格，却只检查商品 ID；
- 要求“所有不下雨日期”，只做 expected subset，不拒绝雨天和额外日期；
- 多渠道发送生成 ID，却不确保各渠道使用同一个新 ID。

### 4.4 不增加 instruction 没说的隐藏条件

常见隐藏条件：

- 要求固定笔记标题，但 instruction 只说“记录到笔记”；
- 要求消息包含项目标题，但 instruction 只要求两个日期；
- “下一场会议”却要求消息包含全部未来会议；
- “会议信息”暗中要求会议号，但普通理解也可能是主题、时间、密码；
- 文件“移动”要求目标继承内部节点 ID；
- 要求搜索历史或页面访问快照，虽然用户只关心最终结果。

修复选择只有两个：把必要条件以自然语言适度说明，或者删除 verifier 的隐藏要求。
不要依赖“模型应该猜到”。

### 4.5 自由文本使用任务局部的语义匹配

文本 matcher 应按字段类型拆开，而不是把整个目标拼成一个精确子串。

#### 实体

- 忽略合理空白、常见标点、大小写和全半角。
- 保留身份相关字符，不能把不同商品或不同地点归一成同一个对象。
- 别名只做局部白名单，例如周杰伦/周杰倫/Jay Chou。

#### 数值

- 先从文本抽取数值，再按容差比较。
- 支持 `1.2万`、`12000`、`12k` 等明确等值形式。
- 标题与金额必须在局部上下文绑定，不能只检查文本中分别出现所有标题和所有数字。

#### 百分比和时长

- `95%` 与 `95.0%` 等价。
- `1小时30分钟`、`90分钟` 可等价。
- 不要用一个宽泛数字 matcher 让日期、邮编或会议号误命中金额。

#### 日期和时间

- 支持明确等价格式：`2026-11-01`、`2026年11月1日`、`2026年11月1号`。
- 是否必须包含年份由 instruction 决定。
- 周几表达必须在固定模拟时间和指定窗口中解析。
- 对集合任务，解析后比较完整日期集合，而不是做字符串包含。

#### 地址

- 可忽略空格、常见标点、中国前缀和邮编后缀。
- 可以容忍合理行政区前缀差异。
- 必须保留街道、门牌、POI 或门店身份，不能只因同在北京市海淀区就通过。
- 地址、天气、温度等多字段必须绑定同一个候选地点。

#### 明确固定措辞

只有 instruction 明确要求固定句子时才精确匹配。其他消息应验证收件人和关键事实，
不要求“订单”“已联系”“已汇总”等冗余词，除非它们承载明确任务语义。

### 4.6 集合任务使用精确集合和负向约束

对于“所有、只、恰好、不要额外”的任务，应检查：

```text
actual_delta == expected_delta
```

而不是：

```text
expected_delta subset_of actual_delta
```

例如补齐购物车需要验证：每个目标恰好一件、没有额外 SKU、订单未新增、checkout
draft 未改变。天气日期需要验证输出集合等于所有非雨日期，而不是仅包含这些日期。

对于没有“只/恰好”语义的自由文本，不要为了追求严格而无条件做精确集合。

### 4.7 多字段和多渠道必须做对象绑定

不能只验证所有 token 在某处出现。应确保：

- 每个交易标题与自己的金额配对；
- 地址、天气和温度来自同一地点候选；
- 收藏的帖子和私信的作者属于同一篇笔记；
- 新会议号在微信和短信中相同；
- 订单的商品、地址、支付方式属于同一新增订单。

### 4.8 不绑定内部实现身份

Verifier 检查用户可观察的业务结果，不检查实现路径。V5 Case57 中 GPT 使用
“复制文件后删除源文件”完成了移动，但旧 verifier 要求目标节点继承源节点 ID，
产生假阴性。修复后检查：

- 源路径消失；
- 目标路径存在；
- 文件名、类型和大小一致；
- 目标目录内容精确；
- 干扰文件保留；
- 微信回复正确。

除非任务明确要求审计内部对象身份，否则内部 ID、操作类型和调用顺序都不应计分。

### 4.9 SR 与诊断分离

当前 Hybrid benchmark 主要指标是 SR。`progress`、`clean`、unexpected changes 和
tool usage 用于诊断，不应在定义不成熟时直接混入主分数。

- 明确禁止的副作用应进入 verifier，影响 SR。
- 与任务无关但可能有噪声的状态变化先保留为 warning/clean 诊断。
- 不要让 USE、搜索历史或 launcher 页面变化决定业务任务是否完成。

查询型任务的 `agent_answer` 也应视为一种最终结果：按答案字段做语义匹配，并与
setup 的确定性事实比较。不要要求 Agent 为了提交答案额外操作一个 instruction 未提及
的答题卡；`answer` 与任务终止在 runtime 中是两个动作，也不能因已回答就跳过 verifier。

## 5. App Tools 与任务契约

### 5.1 工具是业务原子能力

推荐工具层级：

- Query：查询账单、搜索事件、列目录、列候选。
- Navigation：打开某日期、对象详情或搜索结果页。
- Draft：预填日程、会议、帖子、结算草稿，最终提交留给 GUI。
- Limited Mutation：真实产品可能开放、风险可控的原子变更。

不推荐：

```text
complete_calendar_and_notify_wechat(...)
```

这会直接吞掉跨 App 规划和 GUI 收尾能力。

### 5.2 工具必须复用 GUI 业务状态

工具执行应调用 App store 或 GUI handler 使用的同一业务函数。工具不能只返回
`success=true`，也不能维护独立数据库。

V5 Taobao Case67 曾暴露工具路径落单后没有移除购物车行，而 GUI 支付会移除。
这不是 Agent 错误，而是工具和 GUI side effect 不一致。修复应落在工具业务逻辑，
而不是放宽购物车 verifier。

### 5.3 查询工具必须声明候选域和完整性

每个列表/搜索工具应说明并正确返回：

- 排序字段和方向；
- 时间窗口；
- 过滤范围；
- `total`；
- `truncated`；
- 稳定 ID；
- 必要的时间戳或显示字段。

不能截断 50 条后声称完整，也不能让 verifier 使用全量候选而 Tool 只看到前 20 条。

### 5.4 Navigation/Draft 的 UI effect 必须兑现

工具返回成功后，下一张 screenshot 必须位于承诺页面。`open_app`、打开详情和草稿
工具应验证前台 App/route，而不是只验证调用函数没有抛异常。

### 5.5 Runtime 缺陷要和 benchmark 缺陷区分

坐标映射、按键覆盖、App 别名、空响应重试、横向分页手势等属于 Agent runtime。
审查失败轨迹时应单独分类：

- Case65/71 的 GPT `Tab/Backspace/Space` 未适配会放大 GUI 表单失败；
- `open_app` 返回 success 却未切换前台会制造循环；
- 这类问题不应通过改 task verifier 解决。

## 6. 一条任务的标准构建流程

### 第一步：写任务卡，而不是先写代码

建议每条任务先保存以下字段：

```yaml
task_id: stable_id
instruction: 高层用户目标
apps: [source_app, target_app]
simulated_time: 2026-07-12T09:00:00+08:00
setup_summary: 初始化对象、干扰项和固定分支
canonical_ground_truth: 可程序化计算的目标
candidate_tools: 可能暴露的 App Tools
gui_required_reason: 哪一阶段没有高层工具或保留 GUI 提交
gui_only_candidate_path: 不依赖 App Tools 的候选 GUI 路径
gui_only_evidence: 成功轨迹、浏览器重放或关键边界测试
expected_changes: 允许/要求发生的状态变化
forbidden_changes: 明确禁止的副作用
verifier_intent: 每条判定的自然语言说明
accepted_equivalents: 文本、日期、单位、别名的合法变体
max_steps: 基于可行路径估算
```

### 第二步：静态契约审查

Reviewer 不运行模型，逐项回答：

1. Instruction 中每个名词是否指向唯一 App/对象？
2. 时间范围、排序字段、集合边界是否明确？
3. Verifier 的每个必要字段能否在 instruction 中找到依据？
4. Instruction 的每个明确动作/输出是否都被 verifier 覆盖？
5. Setup 是否产生唯一答案，是否被默认数据污染？
6. GUI、Tool 和 verifier 是否使用同一候选域？
7. 是否能写出不依赖 App Tools 的候选 GUI 路径，并明确后续需要什么真实证据？
8. 是否存在合理文本格式会被 matcher 拒绝？
9. 是否存在明显错误结果能钻 verifier 空子？
10. 是否有不必要的内部 ID、搜索历史或执行路径要求？

建议给每条任务标注：`OK / P2 / P1 / INVALID_ENV`。

### 第三步：离线 verifier 正反例测试

每条任务至少包含：

- 一个标准 positive final state；
- 一个 unchanged initial state；
- 每个明确关键字段的 single-fault negative；
- 至少一个合理等价表达 positive；
- 至少一个容易误通过的 adversarial negative；
- verifier diagnostics 可 JSON 序列化。

例如 Top-3 消息应测试：

- 三个标题金额正确且格式不同，PASS；
- 只有三个金额，FAIL；
- 标题和金额互换配对，FAIL；
- 漏掉指定结尾，FAIL；
- 发给错误联系人，FAIL。

### 第四步：浏览器 setup smoke

对每条任务检查：

- reset/setup 成功；
- 初始状态不能通过 verifier；
- 模拟时间正确；
- 所有相关 App 能打开；
- 目标和干扰项可在 GUI 中观察；
- 前台 App 暴露正确工具集合；
- judge 无异常，诊断可序列化。

### 第五步：GUI/Tool 边界 smoke

对 repaired 或高风险 case 做任务专用 smoke：

- GUI 能获得 verifier 使用的值；
- Tool 返回同一值和候选域；
- Navigation/Draft 后页面正确；
- Mutation 后 GUI 可见且状态落库；
- 工具后仍可继续 GUI；
- 禁止副作用没有发生。

### 第六步：获得可行性证据

不强制每条长任务都手写完整 reference trajectory。可以使用以下证据组合：

- 成功的强模型轨迹；
- 对关键边界的浏览器脚本；
- 每个 mutation 的 state regression；
- 对复杂任务的人类一次完整重放。

但不能只凭“代码看起来能做”就宣称纯 GUI 可完成。对没有任何成功轨迹的长任务，
至少要逐段验证关键 GUI 路径。

### 第七步：执行配对 GUI-only 合约审查

至少选择一个稳定的强视觉模型，在同一任务版本上分别运行 Hybrid 和 GUI-only。审查
优先级不是只看 GUI-only 的低分，而是按配对结果排序：

1. `Hybrid PASS / GUI-only FAIL`：最高优先级。检查工具是否绕过了坏控件、隐藏字段或
   不合理枚举。
2. `Hybrid FAIL / GUI-only FAIL`：检查共同失败是否来自 instruction/setup/environment，
   不能因两边都错就默认是模型问题。
3. `Hybrid FAIL / GUI-only PASS`：检查工具选择、工具副作用、动态工具面和 runtime，
   防止工具反而破坏环境或误导模型。
4. `Hybrid PASS / GUI-only PASS`：抽样确认 verifier 没有过弱，且两种路径确实落到
   同一业务状态。

对疑似环境问题，必须继续查看截图、真实点击效果、对应 React handler、最终 store
和 verifier selector。只看到 Agent 重复点击不能判断坐标错；也可能是按钮没有 handler、
滚动后的视觉选中值没有写回 state，或页面读取了和 Tool 不同的数据缓存。

### 第八步：模型运行后逐条审查

先审查所有 verifier failure，再抽查 verifier pass。每条轨迹按以下顺序看：

1. 原始 instruction；
2. setup ground truth；
3. Agent 实际看到的截图和 Tool Result；
4. Agent 动作是否真的命中控件；
5. 最终 App/OS state；
6. verifier 每个 check 的 expected/actual；
7. 是否存在错误收件人或额外 side effect；
8. 同任务在另一模型、另一模式或上一轮是否可完成。

分类使用：

- `AGENT_ERROR`：要求清晰、证据可见、路径可行，Agent 确实做错。
- `FALSE_NEGATIVE`：用户可观察目标已完成，verifier 错拒。
- `FALSE_POSITIVE`：明确要求未完成，verifier 错放。
- `AMBIGUOUS`：存在多种合理理解或目标不唯一。
- `INVALID_ENV`：GUI 分支不可完成、状态不提交或页面破损。
- `TOOL_RUNTIME`：工具 side effect、坐标、按键、别名或协议问题。
- `MIXED`：Agent 有独立错误，同时 runtime/environment 实质性放大失败。

### 第九步：在最窄责任层修复

优先顺序不是固定改 verifier，而是判断根因：

1. 指令歧义：有限澄清 instruction。
2. Setup 不唯一或污染：修 setup。
3. GUI/Tool/State 不一致：修共享环境或工具业务逻辑。
4. Verifier 过严/过弱：写任务局部 matcher 或补充状态约束。
5. 环境功能未实现且不值得立即修：删除任务。
6. Runtime 适配问题：修 runtime，不污染任务契约。

不要为了让某个模型通过而改变正确契约。修复必须由独立的 instruction/setup/state
证据支持。

### 第十步：修复后完整重跑

人工给旧轨迹“补分”只能作为诊断，不是正式结果。正式版本需要：

- 修复代码和回归测试；
- 对受影响 case 重放；
- 系统性修复后最好 full-suite rerun；
- 再次逐条审查新失败；
- 保存 run provenance，禁止静默拼接结果。

## 7. V6：把 GUI-only 可完成性作为独立契约

V5 已经较系统地审查了 instruction/setup/environment/tool/verifier，但当时仍主要从
Hybrid 轨迹判断任务是否成立。V6 增加了一条独立问题：

> GUI + Tools 比 GUI-only 高出的分数，究竟来自工具能力，还是工具绕开了 GUI 缺陷？

答案不能从 SR 差值直接得到。需要对同一模型、同一任务的两种 setting 做配对轨迹
审查，特别检查 `Hybrid PASS / GUI-only FAIL`。V5 的强模型 GUI-only 轨迹证明，即使
最终 state verifier 本身正确，GUI 仍可能没有稳定路径观察或写入该状态。

### 7.1 GUI-only 可行性的证据等级

按可信度从高到低使用以下证据：

1. 强模型或人类在正式 max steps 内完成的完整 GUI-only 轨迹；
2. 真实浏览器逐段完成关键路径，并用最终 state/verifier 验证；
3. 控件 handler、store mutation 和页面重开回显的自动化测试；
4. 只做静态源码阅读，认为“理论上可以点击/穷举”。

第 4 级不能单独作为发布证据。尤其要防止以下误判：

- 页面显示了按钮或标签，但没有 `onClick`；
- 滚轮视觉上停在目标值，内部 React state 仍是旧值；
- GUI mutation 只保存对象 ID，没有保存页面渲染需要的数据 bundle；
- verifier 使用 raw 精度或隐藏字段，GUI 只显示舍入值；
- GUI 理论上能遍历，但候选量和返回链路使统一步数预算根本不够。

### 7.2 配对轨迹应该怎样读

不要只看最后一张截图。对每个 GUI-only failure 依次确认：

1. Hybrid 是否成功，以及实际调用了什么 App Tool；
2. 两条轨迹的首个事实分歧发生在哪里；
3. GUI-only 是否选错 App、点错坐标，还是控件根本没有状态变化；
4. Agent 是否已经合理完成，只是 verifier 拒绝一种等价表达；
5. 是否存在替代 GUI 路径，Agent 是否观察到无进展并尝试恢复；
6. 同一任务是否有另一模型的 GUI-only 成功轨迹；
7. max steps 是否消耗在真实枚举，还是消耗在坏控件循环。

`Hybrid PASS / GUI-only FAIL` 不是自动的 Tools 胜利；`GUI-only PASS / Hybrid FAIL` 也
不是任务回归。后者常暴露错误工具选择、工具 side effect、解析协议或工具调用后 GUI
状态不同步。

### 7.3 V5 到 V6 的修复和删除案例

| Case | GUI-only/跨模型轨迹暴露的问题 | V6 处理 | 可复用经验 |
| --- | --- | --- | --- |
| Case08 及同类支付宝年月选择 | 滚轮已经显示 1 月，但仍是灰色或确认无效；旧 state 还会把滚轮拉回。 | 三个账单页面统一按真实 `scrollTop` 读值，弹窗只初始化一次，确认前再读取 DOM。 | 视觉选中值、内部 state 和最终查询参数必须做三方一致性测试。 |
| Case11 | Agent 发送可见姓名“刘沐辰”，verifier 只接受完整账单标签 `正中(刘沐辰)`。 | 从同一交易对象生成完整标签、外部昵称和括号内姓名的局部合法别名。 | “对象名称”不等于内部唯一 display string；身份严格、展示格式宽容。 |
| Case20 | Agent 保留完整标题核心内容，但省略装饰性 emoji、标点或空格而失败。 | task-local 标题 matcher 忽略装饰字符，仍要求全部核心文字按顺序出现。 | 先区分内容缺失与排版差异；不能用整条 raw substring 校验自由文本。 |
| Case25 | Kimi 和 Qwen 都正确求出“今日播放 ∩ 已点赞”五首歌，又合理把“现在在听的歌”理解为当前曲目《搁浅》；verifier 同时禁止该未点赞曲目。 | 指令明确两个栏目标题，第二栏改为“今天在听的歌”；verifier 只同步标题，完整交集和负向排除保持严格，并重跑 7 个模型的两种 setting。 | verifier 的集合语义可能正确，但栏目名称本身也会制造另一种合理任务语义；应使用多模型族发现歧义。 |
| Case33 | 两家咖啡馆 raw 距离为 456m/470m，但 GUI 都显示 450m，评分也同为 5.0。 | 按 GUI 实际显示粒度计算并列，接受同评分、同显示距离的任一候选；名字、评分、地址仍必须绑定同一候选。 | Verifier 不能使用比 Agent 可见信息更高的精度打破并列。 |
| Case36 | GUI 添加南京后主页面长期显示 `--°` 和空白预报，而 Tool 在同一初态能返回南京天气。 | GUI 和 Tool 统一走 `addSavedCityWithBundle`；主页面、管理页、预报页共享离线 fallback。 | Mutation 成功不仅是保存 ID，还要让后续所有 GUI 页面能够从同一事实恢复完整对象。 |
| Case45 | 微信读书书架有“推荐值”标签但无排序逻辑，卡片也不稳定展示 verifier 需要的全部推荐值。 | 从 V6 删除，任务数由 76 变为 75。 | 工具能直接拿到字段不能补偿 GUI 缺失；没有稳定纯 GUI 观察路径时应删除或进入 tool-required 分层。 |
| Case54 | 正确消息写“会议11点开始”，旧 matcher 只接受 `11:00`、`11点00分`。 | 仅在分钟为 00 时接受“11点/上午11点/11时”，不误收“11点30分”。 | 时间等价表达要做结构化解析，并限制宽松规则的适用边界。 |

这些修复分别落在最窄责任层：Case08/36 修共享环境，Case11/20/33/54 修 task-local
verifier，Case25 同步澄清 instruction 和 heading matcher，Case45 删除。不能把所有
问题统一处理成“放宽 verifier”。

### 7.4 有环境摩擦但仍保留的任务

V6 没有要求 GUI 完全没有摩擦。若替代路径稳定、可观察，并有成功证据，可以保留为
Agent 恢复、枚举或长程规划能力测试。

| Case/问题 | 为什么保留 | 后续约束 |
| --- | --- | --- |
| Case10/11 当前年份推理 | 不把完整日期直接注入 prompt；Agent 可通过 Launcher、日历或业务页面建立时间基准。 | 若某次环境版本完全无法观察年份，就必须修环境，不能把猜错年份算能力错误。 |
| Case17 书架“进度”标签能力有限 | 逐本打开可以看到阅读进度，且已有强模型 GUI-only 成功轨迹。 | 作为高成本枚举任务保留，不把点击无效标签本身当成功证据。 |
| Case35 地图精确排名成本高 | GUI 与 Tools 均存在完成路径，保留用于测完整候选枚举。 | 持续监控 max steps；若没有任何成功 GUI 证据，需改任务或补充排序视图。 |
| Case53 会议内分享/邀请入口有限 | 可以结束会议，再从历史/详情读取会议号并手动发送。 | 失效入口不能是唯一取号路径；审查 Agent 是否尝试返回和替代路径。 |
| Case31 未显式指定消息 App | 当前短信无法解析陈静，Agent 可合理恢复到微信；失败轨迹也没有通过其他渠道成功发送。 | 新合成任务若 verifier 只检查一个渠道，最好在 instruction 中明确渠道，避免潜在隐藏要求。 |
| Case73/75 日历新建页日期只读 | 稳定流程是先在月视图选择目标日期再新建，已有成功轨迹。 | 页面可供性虽容易误导，但属于可恢复的工作流理解，不等于不可完成。 |
| Case74/75 `open_app` 别名失败 | Runtime 会诚实返回 `APP_NOT_FOUND`，Agent 可回到 Launcher 或改用规范名称。 | 不能返回假 success；少量可恢复别名错误属于 runtime/Agent 恢复，不改 verifier。 |

这里的边界是：**替代路径必须真实存在且可在预算内完成**。仅仅能从源码想象一条
极端绕行路径，不足以保留任务。

### 7.5 如何解释 Hybrid 与 GUI-only 差值

- 单次配对运行适合定位行为差异，不是严格的因果效应估计；正式结论应多 seed 重复。
- GUI-only 的 `MAX_STEPS` 同时反映低层交互成本和模型效率，但坏控件导致的循环必须
  单独剔除或修复。
- Agent 主动 `COMPLETE` 后因错事实、漏项、错排序失败，通常比单纯点击失败更能说明
  认知能力差异。
- 应同时报告 SR、平均/P50/P90 步数、实际 App Tool 调用数、调用工具的任务数和
  distinct tool coverage；candidate tools 暴露过不等于模型使用过。
- Tools 可能提高也可能降低单条任务成功率。GUI-only 成功而 Hybrid 失败时，要检查
  工具选择和工具后 GUI 收尾，不能假设提供工具后性能单调不降。

V6 最终保留 75 条任务，并完成 7 个模型、Hybrid/GUI-only 两种 setting 的运行。
所有 Hybrid 轨迹合并后实际调用了 99/203 种 App Tools，覆盖 19 个 App。该结果说明
V6 可以作为试行评测集，但 203 个候选工具的“候选覆盖”仍不能替代实际调用覆盖和
逐条契约质量。

### 7.6 V6 最终评测结果

以下是当前固定版 V6 在 7 个模型上的最终单次运行结果。每个 setting 包含 75 条任务，
固定模拟时间为 `2026-07-12 09:00:00`，并行度为 8，最大输出 token 为 8192。
Hybrid 与 GUI-only 对同一模型使用相同的 instruction、setup、environment、截图、
基础 GUI 动作和 verifier；GUI-only 只移除 App Tools，保留 `open_app` 等基础运行时
能力。Kimi-K2.6 使用独立适配协议和 `[0,1]` 坐标，其他表中模型使用通用 XML 协议和
`[0,1000]` 坐标。内部 Qwen3.5-9B 关闭 thinking。

| 模型 | Hybrid 成功数 | Hybrid SR | Hybrid 平均步数 | GUI-only 成功数 | GUI-only SR | GUI-only 平均步数 | SR 差值 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gemini-3.1-Pro-Preview | 64/75 | 85.33% | 13.16 | 44/75 | 58.67% | 26.47 | +26.67 pp |
| Kimi-K2.6 | 56/75 | 74.67% | 25.56 | 45/75 | 60.00% | 36.05 | +14.67 pp |
| Qwen3.5-Plus | 54/75 | 72.00% | 23.65 | 34/75 | 45.33% | 32.79 | +26.67 pp |
| Gemini-3.5-Flash | 53/75 | 70.67% | 16.56 | 43/75 | 57.33% | 28.08 | +13.33 pp |
| Gemini-2.5-Pro | 24/75 | 32.00% | 19.61 | 4/75 | 5.33% | 33.33 | +26.67 pp |
| Qwen3.5-27B | 22/75 | 29.33% | 34.64 | 18/75 | 24.00% | 40.48 | +5.33 pp |
| 内部 Qwen3.5-9B | 7/75 | 9.33% | 48.47 | 5/75 | 6.67% | 51.36 | +2.67 pp |

平均步数按全部 75 条任务计算，包含成功、失败、主动结束和达到步数上限的 episode，
不是仅对成功任务的条件均值。因此它同时受模型效率、失败时是否较早退出和
`MAX_STEPS` 数量影响，不能脱离 SR 单独解释。

Hybrid setting 的实际 App Tool 使用情况如下。调用次数不包含 `mobile_use`；覆盖数是
该模型至少调用过一次的不同 App Tool 数量，不同模型的覆盖集合存在重叠，不能直接
相加。

| 模型 | App Tool 调用总数 | 平均每任务调用数 | 不同 App Tools | 覆盖率 |
| --- | ---: | ---: | ---: | ---: |
| Gemini-3.1-Pro-Preview | 237 | 3.16 | 55/203 | 27.09% |
| Kimi-K2.6 | 178 | 2.37 | 64/203 | 31.53% |
| Qwen3.5-Plus | 135 | 1.80 | 50/203 | 24.63% |
| Gemini-3.5-Flash | 263 | 3.51 | 67/203 | 33.00% |
| Gemini-2.5-Pro | 213 | 2.84 | 65/203 | 32.02% |
| Qwen3.5-27B | 67 | 0.89 | 33/203 | 16.26% |
| 内部 Qwen3.5-9B | 16 | 0.21 | 8/203 | 3.94% |
| **7 个模型合计/并集** | **1109** | **2.11** | **99/203** | **48.77%** |

这里的合计平均值以 `7 × 75 = 525` 个 Hybrid episode 为分母；99/203 是跨模型并集，
覆盖 19 个 App。较高的 distinct tool coverage 不等于较高 SR，例如 Gemini-2.5-Pro
调用了 65 种工具但 SR 只有 32.00%，说明工具发现、参数构造、调用后的 GUI 收尾和
长程规划仍是相互独立的能力维度。

正式结果来源如下；当前文件中的 Case25 均为澄清指令和 verifier 后重放并原位替换的
最终轨迹：

```text
trial_apps/mobilegym/runs/hybrid-tools-v6-gemini31pro-preview-{hybrid,gui-only}-75-par8-matrix-r1/
trial_apps/mobilegym/runs/hybrid-tools-v6-gemini35flash-{hybrid,gui-only}-75-par8-matrix-r1/
trial_apps/mobilegym/runs/hybrid-tools-v6-gemini25pro-{hybrid,gui-only}-75-par8-matrix-r1/
trial_apps/mobilegym/runs/hybrid-tools-v6-kimi-k2.6-{hybrid,gui-only}-75-par8-r1/
trial_apps/mobilegym/runs/hybrid-tools-v6-qwen35plus-{hybrid,gui-only}-75-par8-r1/
trial_apps/mobilegym/runs/hybrid-tools-v6-qwen35-27b-{hybrid,gui-only}-75-par8-r1/
trial_apps/mobilegym/runs/hybrid-tools-v6-qwen35-9b-{hybrid,gui-only}-75-par8-r1/
```

这些数字是单次运行，不包含多 seed 方差。它们适合描述当前 V6 实现下的基线和同模型
配对差异，不应被表述为模型能力的稳定置信区间。经过 GUI-only 契约审查后，Hybrid
相对 GUI-only 的差值已更能反映工具带来的效率与能力增益，但仍可能包含采样随机性、
模型协议适配和单次执行波动。

## 8. V1-V6 典型问题与修复案例

以下案例库应作为后续任务生成和 reviewer 的反例集。Case 编号按当时版本记录，
同一编号在不同版本中可能对应不同来源 task。

### 8.1 指令歧义、隐藏条件与继承漂移

| 版本/Case | 原问题 | 为什么不公平 | 最终处理与通用经验 | 归档轨迹 |
| --- | --- | --- | --- | --- |
| V2 Official27 | 改写后只要求同步行程，继承 verifier 仍要求固定标题“出行”。 | Agent 完成所有业务状态仍因未说明标题失败。 | 删除隐藏标题要求，或在指令明确标题。改 instruction 后必须重新审查 inherited verifier。 | [v2/official27](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v2/official27/index.html) |
| V2 Official29 | 改写后只要求条件成立时查车，旧 verifier 始终要求 train query。 | Agent 根据雨天正确不产生副作用仍失败。 | 分支 verifier 必须与新 instruction 同步，不能保留原任务的程序性要求。 | [v2/official29](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v2/official29/index.html) |
| V2 Official34 | 指令说“下一场会议”，verifier 要求所有未来会议。 | 单数目标与全集目标冲突。 | 明确单一下一场，并只验证该对象。 | [v2/official34](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v2/official34/index.html) |
| V2 Official40 | 改写后没说项目例会位于腾讯会议，verifier 固定查腾讯会议。 | Agent 在 Calendar/Notes 查找是合理行为。 | 指定 App，或 setup 提供跨 App 可发现线索。不要隐藏数据源。 | [v2/official40](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v2/official40/index.html) |
| V2 月支出记录类 | 指令只说“记到 Notes”，没有规定标题、正文排版或固定句式。 | 固定标题/格式 matcher 会把正常记录误判为失败。 | 在 title+content 的合并文本中匹配必要事实；只有明确要求“新建标题为 X”时才严格校验标题。 | [v2/official03](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v2/official03/index.html) |
| V2 转账统计类 | “转账”“收到普通红包”和 UI 小字“转账红包”边界不清，时间范围也可能未说明。 | 人和模型对计数口径可能不同。 | 明确记录类型、方向和时间窗口；setup 中让不同类别视觉可区分，verifier 按同一结构化类型统计。 | [v2/official04](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v2/official04/index.html) |
| V3 Case33 | “给我买票”未说明乘车人，verifier 要求账号 owner。 | 选择另一已有乘客可能同样合理。 | 明确“当前登录账号本人”，或接受合法乘车人集合。 | [v3/case33](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v3/case33/index.html) |
| V3 Case45 | “未来两周”未说明是否包含今天。 | Agent 使用今天，verifier 用 offsets 1..14。 | 改为“从明天开始的未来14天”或明确“包含今天”。 | [v3/case45](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v3/case45/index.html) |
| V3 Case51 | 指令要求删除所有 `raw_` 文件，verifier 又保护两个 `raw_` 文件。 | Instruction 与 verifier 直接矛盾。 | 明确只删除三个具体文件或声明例外；保留项必须和通配语义一致。 | [v3/case51](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v3/case51/index.html) |
| V3 Case59 | “会议信息”未说明必须包含会议号，verifier 要求多个渠道都含 ID。 | 主题、时间、密码也可理解为会议信息。 | 指令明确“生成的会议号和密码”，再严格验证。 | [v3/case59](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v3/case59/index.html) |
| V3 Case79 | “提前一天提醒”与独立 alarm toggle 的含义不明确。 | 普通 reminder 正确但额外开关关闭时难判。 | 指令明确“并打开闹钟提醒”，或只验证普通 reminder。 | [v3/case79](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v3/case79/index.html) |
| V3/V4 微信读书 | “最近一周”可指自然周或滚动七天。 | 人和模型都可能选择自然周，verifier 用 trailing 7 days。 | 改为“从今天起往前7天，包含今天”，并冻结周日使 GUI 周视图一致。 | [v3/case25](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v3/case25/index.html)<br>[v4/case24](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case24/index.html) |
| V4 Case13 | Moment verifier 要求完整视频标题，指令只说推荐视频。 | 概括标题可能合理。 | 指令增加“包含完整标题”，不提供具体标题答案。 | [v4/case13](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case13/index.html) |
| V4 Case17 | “正在读的书”可指当前一本或所有未读完书。 | GUI active book 与 shelf 集合语义不同。 | 改成“书架中所有已有阅读进度且尚未读完的书”。 | [v4/case17](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case17/index.html) |
| V4 Case21/22 | “今天第一/第三首”未定义列表方向。 | 最近列表通常 newest-first，verifier 取 chronological earliest。 | 明确“按实际播放时间从早到晚”，并让 GUI/Tool 显示 timestamp。 | [v4/case21](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case21/index.html)<br>[v4/case22](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case22/index.html) |
| V4 Case57 | 老板说“上周流水”，目录有多周截图，月份线索仍不足。 | A/B/C 多个文件都可被表面文本解释。 | setup 的老板消息增加“这个月1号修改”的可观察线索，保持消歧难度。 | [v4/case57](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case57/index.html) |
| V4 Case63 | “开得最久”可指计划时长或实际参会时长。 | verifier 使用 planned duration。 | 指令改为“预定时长最长”。 | [v4/case63](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case63/index.html) |
| V4 Case73 | 只要求发送原日期和准备日期，verifier 还要求事项标题。 | 隐藏消息字段造成 observed false negative。 | 删除微信标题要求；日历事件已证明使用了正确事项。 | [v4/case73](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case73/index.html) |
| V4/V5 Case15 | “简单汇总最新两条笔记”难定义文本质量，但 verifier 需要身份信息。 | 抽象摘要没有唯一字符串。 | 指令增加“记得包含两条笔记标题”，让身份字段可严格验证。 | [v4/case15](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case15/index.html)<br>[v5-hybrid/case15](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case15/index.html) |
| V4/V5 Case16 | 商品推荐可用简称，但 verifier 需要商品身份。 | 简称是否足够存在主观性。 | 指令明确“包含完整商品标题”。 | [v4/case16](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case16/index.html)<br>[v5-hybrid/case16](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case16/index.html) |
| V4/V5 Case18 | “告诉陈静已经联系”未明确是否要博主昵称。 | 仅说“已经联系他了”也可能合理。 | 指令明确发送博主昵称和已联系状态。 | [v4/case18](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case18/index.html)<br>[v5-hybrid/case18](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case18/index.html) |
| V4/V5 Case74 | 笔记只写牛奶/咖啡/苹果，环境有多个合法商品，verifier 硬编码三个 SKU。 | Hybrid 全站搜索排序恰好命中目标，GUI 店内搜索可能选另一个合法商品。 | setup 将笔记固定为完整商品和店铺；verifier 要求精确一件增量及无额外副作用。另一方案是定义每类 allowed SKU set。 | [v4/case74](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case74/index.html)<br>[v5-hybrid/case74](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case74/index.html) |

### 8.2 Verifier 过于严格造成假阴性

| 版本/Case | 过严点 | 修复方式 | 仍保持的严格边界 | 归档轨迹 |
| --- | --- | --- | --- | --- |
| V2 Official01 | 要求账本昵称 `正中(刘沐辰)`，拒绝“转账给刘沐辰2500块”。 | 分别匹配“转账”、对象和金额。 | 对象和金额仍必须正确。 | [v2/official01](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v2/official01/index.html) |
| V2 Official11 | regex 接受“5个/5条”但拒绝“投稿数为5”。 | 对数值和语义字段分别匹配。 | 粉丝数、投稿数和标题都要正确。 | [v2/official11](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v2/official11/index.html) |
| V4/V5 Case02/03/05/06/07 | 商品标题原始 substring 对空格敏感。 | 规范化空白、标点、大小写。 | 不同商品 ID/身份文本不能通过。 | [v4/case02](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case02/index.html)<br>[v4/case03](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case03/index.html)<br>[v4/case05](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case05/index.html)<br>[v4/case06](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case06/index.html)<br>[v4/case07](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case07/index.html)<br>[v5-hybrid/case02](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case02/index.html)<br>[v5-hybrid/case03](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case03/index.html)<br>[v5-hybrid/case05](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case05/index.html)<br>[v5-hybrid/case06](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case06/index.html)<br>[v5-hybrid/case07](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case07/index.html) |
| V5 Case01 | 整条笔记要求固定连续格式。 | “转账”、对象、准确金额独立校验。 | 三项都不可缺。 | [v5-hybrid/case01](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case01/index.html) |
| V5 Case08 | 胜出月份只接受单一年月格式。 | 支持中文年月、斜杠、连字符和明确上下文月份。 | 必须是正确胜出月份和差额。 | [v5-hybrid/case08](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case08/index.html) |
| V5 Case10 | 消息必须重复“订单”二字。 | 只检查收件人、笔数和金额。 | 年份、计数和总额不放宽。 | [v5-hybrid/case10](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case10/index.html) |
| V5 Case23 | `95%` 与 `95.0%` 被视为不同。 | 解析百分比数值。 | 排名字段仍是 recommendedValue。 | [v5-hybrid/case23](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case23/index.html) |
| V5 Case24 | `1小时30分钟` 与 `90分钟` 不等价。 | 统一换算总分钟。 | 总时长必须准确。 | [v5-hybrid/case24](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case24/index.html) |
| V5 Case29/30 | `1.2万` 与 `12000` 不等价。 | 支持万/千和展开数值。 | 作者和对应帖子仍绑定。 | [v5-hybrid/case29](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case29/index.html)<br>[v5-hybrid/case30](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case30/index.html) |
| V5 Case33/34/44 | 地址空格、标点、国家前缀或邮编导致失败。 | 地址专用安全规范化。 | 街道、门牌、POI/门店核心身份必须保留。 | [v5-hybrid/case33](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case33/index.html)<br>[v5-hybrid/case34](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case34/index.html)<br>[v5-hybrid/case44](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case44/index.html) |
| V5 Case37 | 地址、天气、温度均用原始字符串。 | 地址安全匹配、天气类别匹配、温度数值匹配，并按同候选成组。 | 不能拼接不同地点的数据。 | [v5-hybrid/case37](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case37/index.html) |
| V5 Case38 | 正确歌单艺人为繁体 `周杰倫/林俊傑`，verifier 只接受简体。 | 两位艺人使用局部别名白名单。 | 歌单仍严格恰好 2+2，无第三艺人，且要播放。 | [v5-hybrid/case38](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case38/index.html) |
| V5 Case40 | 合理的“周一/周三”“13号”无法解析。 | 在固定窗口解析星期、号和中文数字。 | 输出日期集合必须精确等于非雨日集合。 | [v5-hybrid/case40](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case40/index.html) |
| V5 Case51 | “03:30已有安排/没空”不在“不行/冲突”白名单。 | 增加有安排、没空、占用、无法安排等语义。 | 冲突分支仍禁止创建会议/日程/短信。 | [v5-hybrid/case51](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case51/index.html) |
| V5 Case72 | 笔记必须逐字包含 `18:00/17:50`。 | 使用时间语义 matcher，接受“下午6点/5点50”。 | 版本、标题和闹钟状态严格。 | [v5-hybrid/case72](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case72/index.html) |
| V5 Case73/75 | `日`、`号`、中文数字格式差异。 | 扩展日期 parser。 | 两个日期都必须存在；Case75 仍必须包含年份。 | [v5-hybrid/case73](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case73/index.html)<br>[v5-hybrid/case75](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case75/index.html) |
| V5 Case57 | 文件移动要求目标继承源 node ID。 | 接受 native move 和 copy+delete 的等价 final state。 | 源消失、目标元数据、精确目录、干扰保留和回复仍严格。 | [v5-gpt-hybrid/case57](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-gpt-hybrid/case57/index.html)<br>[v5-hybrid/case57](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case57/index.html) |

### 8.3 Verifier 过弱造成假阳性

| 版本/Case | 漏检 | 修复 | 归档轨迹 |
| --- | --- | --- | --- |
| V2 Official25 | 要求最便宜高铁，实际购买普通 D 车仍 PASS。 | 绑定列车类型、候选排序、日期、乘客和新增订单。 | [v2/official25](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v2/official25/index.html) |
| V4 Case09 | 只检查三个金额和结尾，不检查交易标题或配对。 | 每条标题和金额局部配对，并验证收件人和指定结尾。 | [v4/case09](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case09/index.html) |
| V4 Case25 | 只检查第一首 liked song，未检查艺人、全部歌曲、标题和排除项。 | 要求两个 heading、完整 liked title/artist 集合，并拒绝 unliked songs。 | [v4/case25](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case25/index.html) |
| V4 Case32/42 | 任一已有同时间闹钟都能通过，disabled 也可能通过。 | 要求相对 initial 新增且 enabled 的目标闹钟。 | [v4/case32](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case32/index.html)<br>[v4/case42](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case42/index.html) |
| V4 Case38 | `total>=4`、每位艺人 `>=2`，额外歌曲也通过。 | 精确四首、艺人 multiset 恰好 2+2。 | [v4/case38](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case38/index.html) |
| V4 Case40 | 包含所有非雨日即可，额外雨天也通过。 | 解析并比较精确日期集合。 | [v4/case40](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case40/index.html) |
| V4 Case41 | 只检查线路/日期/乘客，不检查高铁；空候选可静默成功。 | `trainNo` 必须以 G 开头；无候选是 setup failure。 | [v4/case41](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case41/index.html) |
| V4 Case46 | 短信有日期和天气即可，不检查邀约。 | 增加“一起跑步/约跑”等邀请语义。 | [v4/case46](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case46/index.html) |
| V4 Case53 | 可复用 initial active meeting。 | scheduled/active 都与 initial diff，并要求两个渠道同一新会议号。 | [v4/case53](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case53/index.html) |
| V4 Case74 | 目标数量用下界，允许额外商品、结算和订单变化。 | 精确 cart delta，orders 和 checkout draft 不变。 | [v4/case74](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case74/index.html) |
| V4 Case75 | 只搜 token `11` 和 `1`，许多错误日期可通过。 | 匹配完整 `2026-11-01`，并要求年份。 | [v4/case75](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case75/index.html) |
| V5 Case70 | 只检查商品和支付，漏掉数量1与默认规格。 | 同一订单行严格 `qty=1`，SKU 等于首选项组成的默认规格。 | [v5-hybrid/case70](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case70/index.html) |

### 8.4 Setup、环境、候选域和工具问题

| 版本/Case | 问题 | 处理与经验 | 归档轨迹 |
| --- | --- | --- | --- |
| V2 Official15 | 多对重复图片视觉相同，verifier 用隐藏文件名指定一对。 | 删除或注入可观察的唯一线索。目标必须由用户证据确定。 | [v2/official15](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v2/official15/index.html) |
| V2 Official26 | GUI 只显示白天多云，verifier 用隐藏夜间雨判断。 | GUI、Tool、verifier 使用同一公开天气字段。 | [v2/official26](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v2/official26/index.html) |
| V2 Transfer06 | 默认更早闹钟污染注入目标。 | setup 前清理/显式纳入默认状态，验证唯一 ground truth。 | [v2/transfer06](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v2/transfer06/index.html) |
| V2/V3 文件移动 | GUI 显示移动 A，状态出现另一文件或旧页面无法复现。 | 用状态快照和浏览器重放确认提交逻辑；不只凭最后截图判断。 | [v2/official36](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v2/official36/index.html)<br>[v3/case60](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v3/case60/index.html) |
| V3 Case14 | Bilibili 收藏夹新建页持续 skeleton/black。 | 任务删除，不能算 Agent 点击失败。 | [v3/case14](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v3/case14/index.html) |
| V3 Case36 | 目标日期无票，只有未实现候补，verifier 要 pending order。 | 删除任务或实现候补完整业务流。 | [v3/case36](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v3/case36/index.html) |
| V3 Case39 | 多次有效地图交互仍无法生成路线。 | 未建立纯 GUI 可完成性，删除或修路线环境。 | [v3/case39](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v3/case39/index.html) |
| V3 Case42 | GUI feed 有目标，verifier selector 前20条找不到。 | selector 对齐完整可滚动 feed。 | [v3/case42](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v3/case42/index.html) |
| V3 Case46 | GUI 当前定位海淀与 verifier 保存城市北京不是同一对象。 | 指令明确目标 city card，并统一状态 selector。 | [v3/case46](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v3/case46/index.html) |
| V3 Case67 | 昵称输入视觉更新但 participant state 仍旧。 | 修提交业务逻辑或删除任务，不能放宽 verifier。 | [v3/case67](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v3/case67/index.html) |
| V4 Weather | host 时间物化默认 forecast，冻结时间下 Tool 重新物化另一日期。 | 模拟时间在 boot 前生效，并做 day-zero parity test。 | [v4/case36](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case36/index.html) |
| V4 Case36 | GUI 新增南京显示 `--`，Tool 有天气。 | 保存城市卡复用同一 offline weather library。 | [v4/case36](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case36/index.html) |
| V4 Case47 | instruction 固定 7月14日，参数用 host `default_tomorrow()`。 | 参数固定为 2026-07-14，增加 host-date-independent test。 | [v4/case47](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case47/index.html) |
| V4 Case61 | Launcher 是7月12日，微信默认消息显示7月13日。 | 在 App eager-load 前冻结系统时间，而非 setup 后覆盖。 | [v4/case61](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case61/index.html) |
| V4 Map | Tool 前50条截断后报完整，verifier 用全量候选。 | 全量过滤后返回，准确报告 total/truncated。 | [v4/case44](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case44/index.html) |
| V4 Spotify | 最近列表无日期/时间，工具描述却直接提示测试解法。 | state/GUI/Tool 增加 timestamp，删除 benchmark-specific hint。 | [v4/case22](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case22/index.html) |
| V4/V5 Case44 | 屏幕可见的三家麦当劳不代表全量最近结果。 | verifier 与全量候选一致；轨迹审查需确认 Agent 是否遍历完整列表。 | [v4/case44](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v4/case44/index.html)<br>[v5-hybrid/case44](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case44/index.html) |
| V5 Case67 | Tool 结算成功但未移除源购物车行。 | 修工具保存 source cart line IDs，确保 GUI/Tool side effect 一致。 | [v5-flash-hybrid/case67](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-flash-hybrid/case67/index.html)<br>[v5-hybrid/case67](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case67/index.html) |
| V5 Case74 补跑 | `open_app("淘宝闪购")` 返回成功但前台没切换。 | runtime 对未知/失败 App 返回 `APP_NOT_FOUND`，导航 success 应可验证。 | [v5-gui-only/case74](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-gui-only/case74/index.html)<br>[v5-hybrid/case74](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-hybrid/case74/index.html) |
| GPT Case65/71 | 标准 keypress 未适配，表单恢复受阻。 | 标为 runtime/mixed，修 GPT adapter；不要修改任务 ground truth。 | [v5-gpt-hybrid/case65](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-gpt-hybrid/case65/index.html)<br>[v5-gpt-hybrid/case71](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/episodes/v5-gpt-hybrid/case71/index.html) |



### 8.5 证据可追溯性与原始轨迹索引

上面的案例表是经验摘要，不应默认每一行都来自一条唯一失败轨迹。证据分为：

- `RAW_EPISODE`：能回到当时的 `index.html`、截图、prompt、response、trace 和 final state；
- `MULTI_TRACE`：结论来自多个模型或多个 setting 的共同现象；
- `CONTRACT_AUDIT`：通过 instruction/verifier 正反例或人工契约审查发现，不需要模型先失败；
- `BROWSER_SOURCE`：通过真实浏览器复现和源码 handler/state 检查确认；
- `HISTORY_ONLY`：原始 episode 已被覆盖，只剩审计文档和 Codex 会话记录。

典型案例已经独立归档到
[hybrid_guideline_cases](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/README.md)。
[CASE_INDEX.md](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/CASE_INDEX.md)
按本章 71 条问题逐行映射，[manifest.json](trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/manifest.json)
记录原 run、task ID、归档路径和 tree SHA-256。第 8.1-8.4 节的“归档轨迹”列直接
指向独立副本，因此删除旧 `runs/` 后仍可查看。

#### 归档目录与原来源路径

下表保留归档前的来源路径，仅用于 provenance。`XX` 替换为两位 Case 编号；V2 的
Official/Transfer 使用各自前缀。旧 run 可以在核验归档后删除，不能再作为长期链接。

| 版本/证据 ID | 原来源 run 与 episode 规则 | 主要审计文档 | 归档状态 |
| --- | --- | --- | --- |
| `V2-FINAL` | `trial_apps/mobilegym/runs/hybrid-tools-v2-gemini31pro-50-par4-final/episodes/hybrid_tools_v2.HTV2OfficialXX/index.html`；Transfer 使用 `HTV2TransferXX` | [V2 Failure Audit](trial_apps/mobilegym/bench_env/task/hybrid_tools_v2/FAILURE_AUDIT.md) | 13 条代表 episode 已归档到 `episodes/v2/`。 |
| `V2-E2E-R2` | `trial_apps/mobilegym/runs/hybrid-tools-v2-gemini31pro-50-par4-e2e-r2/episodes/hybrid_tools_v2.HTV2OfficialXX/index.html` | 同上；会话中人工打开过 Official03/04/11/25/36 | 人工讨论对应 Case 已由 V2-FINAL 等价实例归档。 |
| `V3-R4` | `trial_apps/mobilegym/runs/hybrid-tools-v3-gemini31pro-80-par4-final-r4/episodes/hybrid_tools_v3.HTV3CaseXX/index.html` | [V3 Failure Audit](trial_apps/mobilegym/bench_env/task/hybrid_tools_v3/FAILURE_AUDIT.md)、[V3→V4 Audit](trial_apps/mobilegym/bench_env/task/hybrid_tools_v4/V3_TO_V4_AUDIT.md) | 13 条代表 episode 已归档到 `episodes/v3/`。 |
| `V4-R1` | `trial_apps/mobilegym/runs/hybrid-tools-v4-gemini31pro-76-par8-e2e-r1/episodes/hybrid_tools_v4.HTV4CaseXX/index.html` | [V4 Failure Audit](trial_apps/mobilegym/bench_env/task/hybrid_tools_v4/FAILURE_AUDIT_GEMINI31PRO.md) | Case51/56/61 的同任务冻结时间版本已归档。 |
| `V4-TIMEBOOT` | `trial_apps/mobilegym/runs/hybrid-tools-v4-gemini31pro-76-par8-e2e-r2-timeboot-retry1/episodes/hybrid_tools_v4.HTV4CaseXX/index.html` | [V4 Contract Audit](trial_apps/mobilegym/bench_env/task/hybrid_tools_v4/CASE_BY_CASE_CONTRACT_AUDIT.md) | 31 条代表 episode 已归档到 `episodes/v4/`。 |
| `V5-G31-H/G` | `trial_apps/mobilegym/runs/hybrid-tools-v5-gemini31pro-preview-{hybrid,gui-only}-76-par8-matrix-r1/episodes/hybrid_tools_v5.HTV5CaseXX/index.html` | [G31 GUI-only Audit](trial_apps/mobilegym/bench_env/task/hybrid_tools_v5/GUI_ONLY_FAILURE_AUDIT_GEMINI31PRO.md) | Hybrid 29 条、GUI-only 12 条已分别归档。 |
| `V5-FLASH-H/G` | `trial_apps/mobilegym/runs/hybrid-tools-v5-gemini35flash-{hybrid,gui-only}-76-par8-matrix-r1/episodes/hybrid_tools_v5.HTV5CaseXX/index.html` | [Flash GUI-only Audit](trial_apps/mobilegym/bench_env/task/hybrid_tools_v5/GUI_ONLY_FAILURE_AUDIT_GEMINI35FLASH.md) | Case67 Hybrid 及 3 条 GUI-only 边界轨迹已归档。 |
| `V5-GPT-H` | `trial_apps/mobilegym/runs/hybrid-tools-v5-gpt54-native-hybrid-76-par8-xhigh-r1/episodes/hybrid_tools_v5.HTV5CaseXX/index.html` | [GPT Hybrid Audit](trial_apps/mobilegym/bench_env/task/hybrid_tools_v5/FAILURE_AUDIT_GPT54_NATIVE_HYBRID.md) | Case57/65/71 已归档到 `episodes/v5-gpt-hybrid/`。 |
| `V6-G31-H/G` | `trial_apps/mobilegym/runs/hybrid-tools-v6-gemini31pro-preview-{hybrid,gui-only}-75-par8-matrix-r1/episodes/hybrid_tools_v6.HTV6CaseXX/index.html` | [V6 G31 Hybrid](trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/FAILURE_AUDIT_GEMINI31PRO_HYBRID.md)、[V6 G31 GUI-only](trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/GUI_ONLY_FAILURE_AUDIT_GEMINI31PRO.md) | Hybrid Case25 和 15 条 GUI-only 代表轨迹已归档。 |

#### 案例表中不能简单映射到一条轨迹的条目

| 案例表条目 | 证据类型和反向定位方式 |
| --- | --- |
| V2 月支出记录类 | 主要对应 `V2-E2E-R2/HTV2Official03` 和当时人工讨论；这是 instruction/verifier 格式边界审查，不是一条 verifier failure。 |
| V2 转账统计类 | 主要对应 `V2-E2E-R2/HTV2Official04`，并结合支付宝页面“转账红包”视觉语义的人工审查。 |
| V3/V4 微信读书 | 原始触发轨迹是 `V3-R4/HTV3Case25`；最终结论还结合 verifier 时间窗口、固定模拟时间和 V4 指令修订，因此属于 `MULTI_TRACE + CONTRACT_AUDIT`。 |
| V4/V5 Case02/03/05/06/07 商品空格 | 多个失败/成功文本和 verifier mutation 的共同结论，主要证据在 [V4 Contract Audit](trial_apps/mobilegym/bench_env/task/hybrid_tools_v4/CASE_BY_CASE_CONTRACT_AUDIT.md) 与 [V5 Intent Audit](trial_apps/mobilegym/bench_env/task/hybrid_tools_v5/TASK_VERIFIER_INTENT_AUDIT.md)，不是单一 episode。 |
| V5 Case08/10/23/24/29/30/33/34/37/38/40/51/72/73/75 | 多数来自逐条 verifier 意图审计和人工正反例，而不是模型首次失败；应从 [V5 Intent Audit](trial_apps/mobilegym/bench_env/task/hybrid_tools_v5/TASK_VERIFIER_INTENT_AUDIT.md) 和 [Contract Repairs](trial_apps/mobilegym/bench_env/task/hybrid_tools_v5/CONTRACT_REPAIRS.md) 回溯，再按 Case ID 打开 `V5-G31-H/G`。 |
| V4 Case09/25/32/38/40/41/46/53/74/75 的假阳性风险 | 主要由 adversarial verifier review 发现；对应 raw episode 可用于理解任务，但“旧 verifier 会误放错误状态”的直接证据是 contract test，不一定是该 episode 本身。 |
| V4 Weather/Map/Spotify | 属于共享环境或工具层问题，来自多条轨迹、工具返回和源码对照；分别回溯 V4 Contract Audit 中的时间、地图候选域和 Spotify 排序章节，不能指定唯一原始轨迹。 |
| V5 Case67 | 直接行为证据可看 `trial_apps/mobilegym/runs/hybrid-tools-v5-gemini35flash-hybrid-76-par8-matrix-r1/episodes/hybrid_tools_v5.HTV5Case67/index.html`，再结合淘宝 checkout state 源码确认 Tool 与 GUI side effect 不同。 |
| V5 Case74 `open_app` | 主要来自 GUI-only 补跑和 runtime 源码检查；当前 `V5-G31-G/Case74` 可复核恢复行为，但 `APP_NOT_FOUND` 修复本身属于 runtime contract。 |
| GPT Case65/71 | 直接对应 `V5-GPT-H/HTV5Case65` 和 `HTV5Case71`，并结合 GPT 专用按键/坐标 adapter 源码，属于 `RAW_EPISODE + BROWSER_SOURCE`。 |
| V6 Case08/11/20/33/36/45/54 | 证据链记录在 [V6 Repairs](trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/V6_REPAIRS.md)；Case08/36 还包括 browser boundary smoke，Case45 是 GUI-only 多轨迹加源码确认。 |
| V6 Case25 | 首次歧义由 Kimi-K2.6 和 Qwen3.5-Plus 两条 Hybrid 失败共同发现，详见 [跨模型审计](trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/FAILURE_AUDIT_KIMI_K26_QWEN35PLUS_HYBRID.md)。后来按修订指令重跑并原位替换 14 个 Case25 episode，所以当前 run 中是修订后轨迹；原始截图级 episode 已不保留，只能从该审计和 Codex rollout 回溯，证据类型为 `HISTORY_ONLY`。 |

因此，“版本 + Case ID”对绝大多数 `RAW_EPISODE` 可以一一回到轨迹；但 grouped matcher、
静态 verifier 漏检和共享环境缺陷本来就不是由单条轨迹独立证明，必须保留 audit/test/source
组成的证据链。后续每个新案例建议显式记录：

```yaml
evidence_type: RAW_EPISODE | MULTI_TRACE | CONTRACT_AUDIT | BROWSER_SOURCE | HISTORY_ONLY
run_dir: immutable run path
task_id: stable task id
audit_doc: finding and rationale
source_revision: environment/verifier revision
supersedes: optional corrected rerun
```

本轮人工讨论的会话 ID 是 `019f4b16-f22d-7d62-8e12-7748a4a5b21b`。本机可从
`/Users/chengkanzhi/.codex/history.jsonl` 检索用户提出的 Case 和显式 episode 路径，
从 `/Users/chengkanzhi/.codex/sessions/2026/07/10/rollout-2026-07-10T16-13-42-019f4b16-f22d-7d62-8e12-7748a4a5b21b.jsonl`
恢复完整对话文字和工具输出。会话记录不能替代已经删除的 screenshot 文件，只能作为
`HISTORY_ONLY` 的文字证据。

## 9. 批量合成任务的建议流水线

### 9.1 生成与审查必须分离

不要让同一个 Agent 一次性生成 instruction、setup、verifier 后直接发布。建议至少分为：

1. **Task Designer**：提出业务任务和难度结构。
2. **Environment Builder**：实现确定性 setup 和 GUI 可完成状态。
3. **Verifier Builder**：根据独立判定意图实现 final-state judge。
4. **Contract Reviewer**：寻找歧义、隐藏要求、假阴性和假阳性。
5. **Trajectory Auditor**：用真实模型轨迹和浏览器证据复核。

可以由不同 Coding Agent 承担，也可以在同一 Agent 的不同阶段强制重新读取原始
instruction，不参考自己生成 verifier 的实现细节。

### 9.2 先构建候选池，再经过门禁筛选

大规模生产时可以生成 2 到 3 倍候选任务，再按以下门禁淘汰：

```text
候选任务
  -> 静态契约审查
  -> 唯一 ground-truth 检查
  -> 离线 verifier 正反例
  -> 真实浏览器 setup smoke
  -> GUI/Tool parity smoke
  -> 强模型 Hybrid/GUI-only 配对试跑
  -> Hybrid PASS / GUI-only FAIL 专项审查
  -> failure + pass 抽样审查
  -> 修复重放
  -> 冻结发布
```

不要因为任务实现成本已经投入，就保留不满足契约的 case。

### 9.3 为自动审查建立攻击样例库

后续可把 V1-V6 缺陷固化成自动 mutation：

- 删除标题空格；
- 改用同义时间格式；
- 只输出金额不输出标题；
- 交换标题金额配对；
- 加入一个额外集合元素；
- 使用普通列车代替高铁；
- 使用已有闹钟代替新增闹钟；
- 消息发给错误联系人；
- 使用另一个门店地址；
- 复制后删除代替原生 move；
- Tool 截断候选后声称完整；
- GUI/Tool 使用不同时区或城市对象；
- 滚轮视觉值改变但内部 state 不变；
- 两个 raw 数值不同但 GUI 舍入后并列；
- GUI 只保存对象 ID，后续页面缺少渲染 bundle；
- 栏目标题可以被合理理解为额外业务要求；
- 页面存在与任务同名但没有 handler 的控件。

对每个 verifier 自动运行这些攻击，可以显著降低批量任务的人工 review 压力。

### 9.4 记录覆盖，不以覆盖代替质量

建议每个 suite 输出：

- App 和 App pair/triple 覆盖；
- Candidate Tool 覆盖和实际 Tool 调用覆盖；
- Hybrid、GUI-only、Tool-only-like 轨迹比例；
- 平均、P50、P90 步数；
- Query/Mutation/Conditional/Aggregation/Transfer 分布；
- 文本、日期、数值、地址、生成 ID 等 verifier 类型；
- 初始 false-positive 数量；
- judge/runtime error 数量；
- failure audit 分类分布；
- `Hybrid PASS / GUI-only FAIL`、反向成功和双失败的配对数量；
- GUI-only 不可完成、环境摩擦、Agent failure 和 runtime failure 的独立数量。

“覆盖 203 个工具”不代表任务有价值。V3 中真正使用的 distinct tools 明显少于候选
工具总数，说明 candidate coverage 和 trajectory coverage 必须分开报告。

### 9.5 用于 SFT/RL 时的额外要求

训练数据比一次性评测更容易放大契约错误：

- 假阴性会惩罚合理策略，诱导模型学习 verifier 特定措辞。
- 假阳性会奖励漏步骤、错误对象或 reward hacking。
- 工具描述泄露答案会被模型直接记忆。
- 不稳定 setup 会把同一动作映射到冲突 reward。
- runtime error 被当成 Agent failure 会污染策略学习。

因此训练任务还应保存：

- 任务版本和 verifier hash；
- setup seed 和模拟时间；
- tool schema 版本；
- environment commit；
- reward breakdown；
- INVALID_ENV/TOOL_RUNTIME 与普通失败的分离标签。

RL 主 reward 应基于稳定 SR。中间 progress reward 只有在每个子目标无歧义、不会奖励
错误顺序或副作用时才能使用。

### 9.6 参数化任务的额外门禁

V1-V6 主要采用固定实例，后续批量生产可能引入参数模板。模板通过审查不代表每个
实例都有效。每次实例化后都要重新执行：

- 参数写入 instruction、setup 和 verifier 的一致性检查；
- 候选非空、唯一最大/最小和无意外并列检查；
- 时间窗口、时区和边界日期检查；
- 初始 verifier negative 检查；
- 目标 App/联系人/商品仍存在检查；
- 分支可达性检查。

采样结果必须在 episode 开始前冻结，并把 template ID、参数、seed 和计算出的
ground truth 写入任务 provenance。Verifier 不能在 episode 结束时重新随机采样。

## 10. 发布门禁清单

一条任务进入正式 scored suite 前，以下项目必须全部满足：

### Instruction

- [ ] 是高层用户目标，不是 step-by-step 教程。
- [ ] 时间、排序、集合、收件人和输出边界无关键歧义。
- [ ] Verifier 每个严格字段在指令中都有依据。
- [ ] 没有内部 ID、工具名或 benchmark 解法泄露。

### Setup

- [ ] 固定模拟时间在 App 初始化前生效。
- [ ] ground truth 唯一且可程序化计算。
- [ ] 默认数据不会抢占目标。
- [ ] 干扰项可观察且可区分。
- [ ] 初始状态不能通过 verifier。
- [ ] 重复 setup 结果一致。

### Environment 与 Tools

- [ ] 正式 Hybrid/GUI-only 对比任务存在可完成的纯 GUI 路径；若任务刻意要求工具，
      应放入单独的 tool-required 分层，不混入同一对比口径。
- [ ] GUI、Tool Result、State、Verifier 使用同一数据域。
- [ ] Mutation 真正提交状态，重开页面仍存在。
- [ ] Query 无 side effect，Navigation/Draft 的页面承诺正确。
- [ ] 工具返回 total/truncated/排序/时间语义准确。
- [ ] Verifier 使用的精度和字段都能从 GUI 观察，raw 隐藏精度不会打破 GUI 并列。
- [ ] 可见主控件失效时，存在经过真实验证且能在步数预算内完成的替代 GUI 路径。
- [ ] 原始 MobileGym suite 在未启用工具时不受影响。

### Verifier

- [ ] 使用 initial/final diff 检查新增或删除。
- [ ] 所有明确要求都覆盖。
- [ ] 没有隐藏字段或执行路径要求。
- [ ] 文本 matcher 接受合理等价表达。
- [ ] 对象、数值、收件人和生成 ID 正确绑定。
- [ ] “所有/只/恰好”使用精确集合和负向约束。
- [ ] diagnostics 可序列化且能解释失败原因。

### Validation

- [ ] 标准 positive、unchanged negative、single-fault negatives 通过。
- [ ] 合理替代表达 positive 和 adversarial negative 通过。
- [ ] 浏览器 setup smoke 通过。
- [ ] 高风险 GUI/Tool 边界 smoke 通过。
- [ ] 至少有分段或完整可行性证据。
- [ ] 至少一个强模型完成 Hybrid/GUI-only 配对试跑，且两边只差 App Tools 暴露。
- [ ] 所有 `Hybrid PASS / GUI-only FAIL` 已检查是否由坏控件、隐藏字段或不合理步数造成。
- [ ] 多模型出现同一种合理解释时，已按潜在 instruction/verifier 歧义复审。
- [ ] 强模型 failures 已逐条审查，passes 已抽样审查。
- [ ] 修复后已重放，正式结果不是人工补分。

## 11. 维护和版本策略

- 已发布 suite 不原地静默改语义。重大契约修复生成新版本，保留旧版本用于复现。
- 任务 ID、instruction、setup、verifier 和 tool schema 的变更都记录 provenance。
- 环境共享修复必须增加 benchmark isolation regression，确认原始 MobileGym 不受污染。
- 小范围 verifier matcher 修复优先放在新 suite 的 task-local overlay，避免修改官方任务。
- 新版本可以继承上一版未修改任务以减少复制，但必须生成有效任务目录，并用测试证明
  override 先于旧实现、删除任务不会重新注册；这种继承是代码复用，不是评分时遇错再
  回落到旧 verifier。
- 系统性 GUI/Tool/state 不一致应修共享业务层，并为旧任务做回归。
- 分数报告必须标明 suite 版本、interaction mode、模型协议、坐标空间、模拟时间、
  max steps、并行度和 run directory。
- 修改已运行任务后，应在新的不可变 run/revision 中重跑受影响 case，并用
  `supersedes` 指向旧结果；不要覆盖首次发现问题的截图和 trace。面向汇总的“最新结果”
  可以单独生成视图，但必须能反查旧 run。人工重新判分只能用于敏感性分析；系统性
  环境修复后应优先完整重跑。V6 Case25 的原位替换是已知反例，原始歧义轨迹目前只在
  审计文档和会话历史中留存。

## 12. 相关资料

设计与演进：

```text
MOBILEGYM_HYBRID_DESIGN.md
MOBILEGYM_REPRODUCTION.md
trial_apps/mobilegym/app_tools/TOOLS_DESIGN.md
trial_apps/mobilegym/app_tools/VALIDATION.md
trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/
```

各版本任务与审计：

```text
trial_apps/mobilegym/bench_env/task/hybrid_tools_v1/
trial_apps/mobilegym/bench_env/task/hybrid_tools_v2/FAILURE_AUDIT.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v3/FAILURE_AUDIT.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v4/V3_TO_V4_AUDIT.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v4/CASE_BY_CASE_CONTRACT_AUDIT.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v4/FAILURE_AUDIT_GEMINI31PRO.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v5/CONTRACT_REPAIRS.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v5/TASK_VERIFIER_INTENT_AUDIT.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v5/FAILURE_AUDIT_GEMINI31PRO_MATRIX.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v5/FAILURE_AUDIT_GEMINI35FLASH_MATRIX.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v5/FAILURE_AUDIT_GPT54_NATIVE_HYBRID.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v5/GUI_ONLY_FAILURE_AUDIT_GEMINI31PRO.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v5/GUI_ONLY_FAILURE_AUDIT_GEMINI35FLASH.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/V6_REPAIRS.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/GUI_ONLY_FAILURE_AUDIT_GEMINI31PRO.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/GUI_ONLY_FAILURE_AUDIT_GEMINI35FLASH.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/FAILURE_AUDIT_GEMINI31PRO_HYBRID.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/FAILURE_AUDIT_GEMINI35FLASH_HYBRID.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/FAILURE_AUDIT_KIMI_K26_QWEN35PLUS_HYBRID.md
```

本文还回顾了本次 Codex 会话历史中关于 V2 指令歧义、V3 失败轨迹、V4 逐条审计、
V5 文本 verifier 宽严边界、地址匹配、Spotify 时间语义、淘宝闪购商品歧义和
Case57 文件移动语义，以及 V6 GUI-only 可完成性、天气新增城市、支付宝滚轮、地图
显示精度并列、Case25 跨模型语义歧义的人工复核意见。
