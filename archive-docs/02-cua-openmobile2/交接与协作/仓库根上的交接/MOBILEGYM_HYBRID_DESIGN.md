# MobileGym GUI + Tools Evaluation Benchmark 设计与演进

本文记录基于 MobileGym 构建 GUI + App Tools 混合调用评测集的探索过程，重点说明 V1 到 V4 的设计变化、实验结果、暴露的问题、修复方法和当前结论。

文档状态：2026-07-13。

## 1. 项目目标

我们的目标不是简单地给 MobileGym 增加更多 GUI 动作，而是构建一个能够评测以下能力的环境：

- Agent 可以通过截图和触屏动作操作任意 App。
- 当前 App 可以按真实产品能力稀疏地提供业务工具。
- Agent 可以在一条轨迹中交替使用 GUI 和 App Tools。
- 工具执行与 GUI 执行落到相同的 App 状态和业务逻辑。
- 同一任务既可以由纯 GUI 完成，也可以由 GUI + Tools 完成。
- Verifier 只检查最终业务状态，不依赖某条固定执行路径。
- 环境能够用于评测、轨迹采集、SFT 和后续 RL。

这类任务的核心不是“是否会调用工具”，而是 Agent 能否在工具不完整、App 能力不对称的情况下完成规划、信息提取、跨 App 传递和 GUI 收尾。

## 2. 基础架构

### 2.1 App Tools

App Tools 位于：

```text
trial_apps/mobilegym/app_tools
```

设计原则如下：

- 工具采用业务原子能力，不直接封装完整用户任务。
- 工具暴露应当稀疏，不能让所有任务退化成一次高层 API 调用。
- 查询工具可以直接返回结构化结果。
- 导航或草稿工具可以打开目标页面、预填表单，但敏感提交保留给 GUI。
- 修改状态的工具应复用 App store 和业务函数，使其结果与 GUI 操作一致。
- 工具代码尽量独立于 MobileGym 原始 benchmark 逻辑。

早期日历 Demo 验证了这条路径：工具负责搜索、打开日期和预填日程，Agent 再通过 GUI 阅读详情、设置提醒并保存。随后工具扩展到微信、淘宝闪购、Days Matter、时钟、笔记，以及地图、天气、12306、支付宝、文件、腾讯会议、Bilibili、小红书、微信读书、淘宝等 App。

工具规模从 V1 的 53 个扩展到 V3/V4 使用的 203 个候选工具。

### 2.2 Hybrid Agent Runtime

Agent runtime 位于：

```text
trial_apps/mobilegym/bench_env/hybrid_agent
```

它采用兼容性较高的 XML Tool Call 协议：

```xml
<tool_call>
<function=mobile_use>
<parameter=action>
click
</parameter>
<parameter=coordinate>
[163, 718]
</parameter>
</function>
</tool_call>
```

主要行为：

- `mobile_use` 始终可用，覆盖 MobileGym GUI 动作空间。
- App Tools 根据当前前台 App 动态暴露，避免一次提供数百个工具。
- GUI 坐标统一为截图上的 `[0, 1000] x [0, 1000]` 归一化空间。
- 每轮保留标准多轮对话历史、截图、Assistant 输出、Tool Call 和 Tool Result。
- 工具返回的结构化结果进入下一轮模型上下文。
- 每步动作、截图、工具输入和工具输出写入 episode HTML，便于轨迹审查。
- `answer` 只记录查询答案，不自动结束任务；Agent 仍需调用 `terminate`。

评测 runner 位于：

```text
trial_apps/mobilegym/bench_env/hybrid_benchmark
```

它负责并行 worker、任务 setup、Agent 执行、状态获取、Verifier 调用、轨迹记录和 SR 汇总。

### 2.3 统一状态判定

GUI 和 Tools 最终都修改同一套 App store，因此任务 verifier 不需要知道动作来源：

```text
GUI click/type -> App UI handler -> App store
App Tool       -> App business function/store -> App store
Verifier       -> compare initial/final App state
```

这是整个方案成立的关键。如果工具维护独立数据库，或者只返回一个虚拟成功结果，GUI 后续操作和 verifier 都会与工具状态分离。

## 3. V1：先证明端到端流程

### 3.1 设计

V1 包含 90 个固定任务：

| 分组 | 数量 |
| --- | ---: |
| 日历 | 12 |
| 微信 | 12 |
| 淘宝闪购 | 12 |
| Days Matter | 12 |
| 时钟 | 12 |
| 笔记 | 12 |
| 跨 App | 18 |
| 合计 | 90 |

它覆盖当时全部 53 个工具，其中 51 条任务包含至少一个不能直接由工具完成的 GUI 阶段。

V1 的主要目标是验证完整链路：

- 固定指令和确定性 setup 能否注册为 MobileGym Task。
- Agent 能否动态拿到前台 App 工具。
- GUI 和工具能否交替执行。
- Verifier 能否统一判断两种执行路径。
- HTML 是否能完整记录截图、动作和工具返回。

### 3.2 结果

Gemini 3.1 Pro 完整运行结果：

```text
runs/hybrid-tools-v1-gemini31pro-90-par4-e2e-r3
87 / 90 = 96.7% SR
```

典型步长很短，之前统计约为 median 7、P90 11。

### 3.3 暴露的问题

V1 证明了工程链路可用，但不适合作为高质量能力 benchmark：

1. 很多指令近似 step-by-step 操作说明，而不是高层用户意图。
2. 相同 App 内任务模板重复，例如“搜索日程，再创建日程”。
3. 指令直接给出了后续步骤需要的信息，缺少 A App 提取 X、再将 X 用于 B App 的依赖。
4. 核心功能往往能被几个工具调用直接完成，GUI 阶段较浅。
5. 初始化数据规模小，目标明显，强模型几乎不需要排序、消歧和长程记忆。
6. 高 SR 主要反映任务简单，不能说明 benchmark 稳定或具有区分度。

### 3.4 V1 的价值

V1 应被视为端到端功能测试集，而不是最终能力评测集。它确认了“工具与 GUI 共享状态、统一 verifier、动态工具暴露”的架构是可行的。

## 4. V2：提高难度，但暴露任务契约问题

### 4.1 设计

V2 缩减为 50 个高难度任务：

- 40 条固定化的官方 MobileGym L3/L4 场景。
- 10 条新增的跨 App 依赖任务。
- 指令改成高层目标，不再描述完整操作步骤。
- 增加隐藏值提取、排序聚合、条件分支、日期推理、保留约束和多输出一致性。

当时工具覆盖仍有限，因此大量 App 只能通过 GUI 操作。40 条官方派生任务主要复用官方 setup 和 verifier，并尝试调整成适合混合 Agent 的表达。

### 4.2 结果

最终记录结果：

```text
runs/hybrid-tools-v2-gemini31pro-50-par4-final
14 / 50 = 28.0% SR
mean steps = 24.14
median steps = 18
P90 steps = 54
```

难度显著高于 V1，但逐条审查 36 个 verifier failure 后发现：

| 审查结论 | 数量 |
| --- | ---: |
| Agent failure | 27 |
| False negative | 6 |
| Invalid / ambiguous | 3 |

另外还发现一条 verifier pass 实际是 false positive。人工临时校正口径约为 `19/47 = 40.4%`，但该数字不能作为正式结果，因为通过轨迹没有全部人工审查。

### 4.3 关键问题

#### 改写指令与继承 verifier 漂移

V2 有些任务修改了官方指令，却继续继承原 verifier。被删掉或改写的约束仍然在 verifier 中，例如：

- 指令说“下一场会议”，verifier 却要求全部未来会议。
- 指令没有指定 App，verifier 默认目标位于腾讯会议。
- 指令允许自然语言表达，verifier 要求内部账单标签的精确形式。

结论：复用官方任务时，应当将 instruction、setup、verifier 作为不可随意拆分的整体。

#### 指令本身存在歧义

官方或派生任务中出现了：

- “最近一周”究竟是自然周还是包含今天的最近七天。
- “未来两周”是否包含今天。
- “会议信息”是否必须包含会议号、密码、主题、时间。
- “买票”是否要求高铁、最便宜车次和特定乘车人。
- 转账、红包等视觉记录的统计边界不明确。

#### 环境能力不足

一些任务要求的分支在 mock App 中并未可靠实现：

- 无票时只有候补，但 verifier 要求普通待支付订单。
- 表单视觉上接受修改，业务状态仍保存旧值。
- 路线规划或页面加载进入不可恢复状态。

#### Setup 污染和数据表示差异

- Days Matter 使用本地 `+08:00` 午夜，而 App 使用 UTC 午夜。
- 注入的新闹钟不是默认状态中最早的闹钟，导致目标不唯一。
- “笔记”与后来增加的 Flomo 存在 App 名称歧义。
- 淘宝与淘宝闪购入口和能力范围容易混淆。

### 4.4 V2 的教训

难度不能通过直接堆叠官方 L4 任务获得。一个低分 benchmark 可能只是包含更多歧义、隐藏约束和环境缺陷。任务复杂度和评测有效性必须分开审查。

## 5. 工具扩展：从少数 App 到 203 个工具

V2 后的一个瓶颈是工具种类太少，任务很容易重复调用同一批查询和创建接口，这让我们构建长程、高难度、真实的GUI+Tools任务很不方便。为支持更真实的跨 App 组合，决定先将工具扩展到 10 多个常用 App，覆盖：

- 地图、天气、铁路 12306、支付宝、文件管理器。
- 腾讯会议、Bilibili、小红书、微信读书、淘宝。
- eBay、Reddit、Spotify 等官方任务涉及的 App。
- 原有日历、微信、笔记、时钟、Days Matter、淘宝闪购。

扩展后的工具总表包含 203 个候选能力。工具仍遵循以下约束：

- 真实业务原子能力，而不是完整任务 API。
- 高风险提交尽量保留 GUI 确认。
- Query、Navigation、Draft、Mutation 的 UI effect 明确。
- 返回结果必须可由 GUI 或底层状态验证。
- 浏览器 smoke 检查调用成功、状态变化、页面仍可继续操作和无额外副作用。

这一步使后续 benchmark 能够覆盖更多 App 和工具组合，而不必让所有新任务都围绕日历、微信和笔记展开。

## 6. V3：扩大覆盖，重新使用官方任务契约

### 6.1 设计

V3 包含 80 条任务：

| 来源 | 数量 |
| --- | ---: |
| 官方 256 test split 精选 | 67 |
| 淘宝任务 | 8 |
| 确定性跨 App transfer | 5 |
| 合计 | 80 |

设计变化：

- 官方派生任务尽量保留原始 instruction、setup 和 verifier，不再任意改写。
- 排除 V2 已知歧义或 verifier 不完整的任务。
- 优先选择排序、聚合、条件分支、日期推理、多输出和 GUI 敏感提交。
- 覆盖 21 个 App 和全部 203 个候选工具。
- 工具仍是可选能力，不成为 verifier 的程序性要求。

### 6.2 Gemini 结果

最终合并审查 run：

```text
runs/hybrid-tools-v3-gemini31pro-80-par4-final-r4
63 / 80 = 78.75% SR
```

| 指标 | 结果 |
| --- | ---: |
| Mean / median steps | 14.49 / 10.5 |
| P90 / max steps | 23 / 60 |
| App Tool calls | 278 |
| Distinct App Tools | 61 |
| 同时使用 GUI 和 Tools | 72 / 80 |
| Runtime errors | 0 |

该目录是多轮修复后的审计合并结果，不是一次全新 single-pass run。`repair_provenance.json` 记录了每条轨迹来源。

GPT-5.4 在同一 V3 suite 的完整结果为：

```text
runs/hybrid-tools-v3-gpt54-80-par4-final-r1
23 / 80 = 28.75% SR
```

这说明该环境能够区分不同模型，但 GPT run 中存在较多 ABORT、MAX_STEPS 和坐标/格式适配问题，不能只用单一数字解释模型能力。

### 6.3 V3 failure audit

Gemini 的 17 个 raw failure 逐条审查结果：

| 分类 | 数量 |
| --- | ---: |
| 明确 Agent failure | 4 |
| Invalid benchmark failure | 10 |
| Ambiguous / 需要修复后重放 | 3 |

主要问题：

- 微信读书 GUI 自然周与 verifier 最近七天窗口不一致。
- 天气 GUI、工具和 verifier 使用不同城市或日期数据源。
- 指令未说明今天是否计入未来时间范围。
- 地图地址存在不同规范化版本。
- 文件删除指令与 verifier 的保留规则直接矛盾。
- 会议任务隐藏要求会议号。
- Bilibili 页面持续 loading/black。
- 12306 目标日期只有未实现的候补分支。
- 腾讯会议昵称视觉修改没有提交到状态。
- RedBook GUI feed 与 verifier candidate selector 不一致。

V3 的核心贡献不是得到 78.75%，而是通过大量真实轨迹暴露了 benchmark contract 的系统性缺陷。

V3 的一轮修复曾把模拟设备日期直接加入 Agent 上下文，以减少相对日期错误。这能提高执行稳定性，但会削弱 temporal grounding 难度，也可能掩盖 GUI 与 App 默认数据本身的时间冲突。V4 因此取消 prompt 日期注入，改为从环境层统一时间，让 Agent 自己从设备和 App 中获取日期。

## 7. V4：以一致性为中心的逐条审计版本

### 7.1 构建方式

V4 不再大规模生成新任务，而是逐条审查 V3 的 80 条任务：

- 保留 76 条。
- 删除 4 条当前环境不能可靠完成的任务。
- 61 条完全保留。
- 14 条做有限指令澄清，其中一条同时有 verifier 修复。
- 2 条修复 verifier。

删除的任务包括：

- Bilibili 收藏夹页面持续 loading/black。
- 12306 目标日期只有不可靠的候补分支。
- 地图路线规划无法建立稳定纯 GUI 可完成性。
- 腾讯会议昵称修改没有提交到业务状态。

指令澄清只暴露 verifier 已经要求、但自然语言存在歧义的边界，不提供 step-by-step 解法。例如：

- “最近一周”改为“从今天起往前 7 天，包含今天”。
- 明确 forecast horizon 从明天开始。
- 明确是否使用当前账号乘车人。
- 明确“会议信息”必须包含生成的会议号和密码。
- 明确文件保留例外。
- 区分北京保存城市和海淀当前定位。

### 7.2 固定模拟时间

V4 将时间固定为：

```text
2026-07-12 09:00:00 Asia/Shanghai
```

选择周日是为了让微信读书 GUI 的周一到周日视图与包含今天的最近七天窗口一致。

时间不注入 Agent prompt。Agent 应从设备 UI 和 App 数据判断时间，这保留了 temporal grounding 难度。

最初实现是在环境 reset 后调用 `setSimulatedTime`。这只能改变运行时读取的系统时间，不能修复已经 eager-loaded 的相对默认数据。

#### Weather 日期错位

Weather 默认 library 在 host 日期下物化，工具又在冻结日期下重新物化，导致同一天气内容在工具中是 7 月 13 日，在 verifier state 中是 7 月 14 日。它影响多个天气联动任务。

修复：在 V4 setup 中对 Weather offline snapshot 做日期 realignment，并增加工具 day-zero 与 verifier state day-zero 一致性检查。

#### 微信未来聊天日期

Case61 暴露了更通用的问题：Launcher 显示 7 月 12 日，但微信默认 `-30m` 消息在页面启动时按真实 7 月 13 日解析，因此聊天列表显示“7月13日”。Agent 最初正确识别昨天是 7 月 11 日，进入微信看到 7 月 13 日后，合理地改用 7 月 12 日记录和周一巡检人。

修复：Hybrid V4 runner 在页面首次加载前通过专用 URL 参数启动模拟时间。`SIMULATOR_CONFIG.time` 在所有 eager app modules 物化默认数据之前就是冻结时间。任务 reset 后仍会再次验证 frozen clock。

普通 4181 URL 和其他 suite 不携带参数，保持原来的 real-time 行为。

浏览器回归结果：

```text
ordinary URL mode = real
V4 mode = simulated, 2026-07-12 09:00, flowing=false
Boss latest relative message = 08:30
WeChat no longer displays 7月13日
```

### 7.3 其他 V4 修复

#### Map 工具与 verifier 候选域

`map__find_nearby` 曾只读取前 50 个原始结果，再做半径过滤，却返回 `truncated=false`。Verifier 使用全部候选，因此评分排名可能差一位。

修复：工具消费完整可用结果页后再过滤，使工具与 verifier 使用相同候选域，并准确报告 total/truncated。

#### RedBook candidate selector

Verifier helper 曾永久限制在 feed 前 20 条，而 GUI 可以滚动看到更多候选。

修复：Verifier candidate 集与完整可滚动 recommendation feed 对齐。

#### 隐藏的日历 description

生日准备任务的 verifier 要求 description 包含 `Mia birthday`，但指令没有要求 description。

修复：删除隐藏字段要求，只检查指令明确要求的日期、时间、提醒、闹钟和微信消息。

### 7.4 V4 Gemini 结果及正确口径

现有 run：

```text
runs/hybrid-tools-v4-gemini31pro-76-par8-e2e-r1
raw result = 59 / 76 = 77.63% SR
COMPLETE = 74
MAX_STEPS = 2
runtime errors = 0
```

原始 failure audit 将 17 条失败分为 9 条 Agent failure 和 8 条评测问题，对 8 条简单记功得到 `67/76`。随后 Case61 被确认也是模拟时间不一致导致的 false negative，因此旧轨迹的反事实审查口径接近：

```text
59 raw passes + 9 invalid failures = 68 / 76 = 89.47%
```

`68/76` 不是正式 V4 SR，不能作为发布结果，原因如下：

- 它不是修复后的完整重跑结果。
- 远程模型即使 temperature=0 也不完全确定。
- 系统性缺陷也可能影响旧 run 中恰好通过的任务。
- 旧 failure audit 中 Case61 的分类已经过时。

明确可归因于 Agent 的旧失败主要包括：

- 将 2026 年任务错误处理为 2024 年。
- 将明天点成后天，走错日历冲突条件分支。
- 在可滚动内容中选错最大/最小值。
- 重复点击相同坐标，无法从 GUI loop 中恢复。
- 未递归进入文件子目录完成日志汇总。
- 创建会议后未能完成日历或消息收尾。

这些错误覆盖 temporal grounding、条件规划、视觉排序、GUI recovery、递归读取和长程完成能力，说明 V4 即使对 Gemini 成功率较高，仍然具有实际挑战性。

## 8. 跨版本问题与通用解决原则

### 8.1 高 SR 不一定说明 benchmark 无效

高 SR 可能来自：

- 指令过于详细。
- 工具层级过高。
- 数据规模小且目标唯一。
- Verifier 过弱产生 false positive。
- 模型确实很强，且工具按设计提高了效率。

必须通过失败和成功轨迹抽查判断是哪一种原因。V1 的高分主要是任务简单；V4 的高分更多来自强模型和工具加速，同时仍保留稳定的复杂错误。

### 8.2 低 SR 也不一定说明任务有挑战性

低 SR 可能来自：

- 指令和 verifier 不一致。
- GUI 显示值与 verifier 数据源不同。
- 环境分支没有实现。
- 时间或时区不一致。
- 目标不唯一或 setup 被默认数据污染。
- 工具隐藏候选却声称结果完整。

V2 是最典型的例子。必须把 capability failure 与 benchmark failure 分开。

### 8.3 Instruction、Setup、Environment、Verifier 是一个契约

任务只有在以下四者一致时才可计分：

1. Instruction 明确表达 verifier 检查的所有必要约束。
2. Setup 创建唯一、稳定且可观察的目标状态。
3. Environment 确实允许通过 GUI 完成要求。
4. Verifier 只检查指令要求，并读取与 GUI/Tools 相同的数据域。

复用官方任务时，优先整体复用 instruction + setup + verifier。若修改指令，则必须重新审查 verifier，而不能假设语义仍然一致。

### 8.4 相对日期必须有统一时间源

所有以下数据都必须绑定同一个模拟时间：

- Launcher、状态栏和系统日期。
- App 默认相对时间。
- Task setup 生成的日期。
- App Tools 返回的日期。
- GUI forecast、history、chat label。
- Verifier 的 today/yesterday/window 计算。

仅在任务 setup 后修改 `TimeService` 不足以覆盖 eager-loaded 数据。模拟时间应在页面模块初始化前启动。

### 8.5 工具必须声明完整性

排序、聚合和排名任务尤其依赖候选域。工具必须：

- 返回真实 total。
- 正确设置 truncated。
- 不在内部静默截断后声称结果完整。
- 与 GUI 和 verifier 使用相同过滤、排序和日期语义。

### 8.6 环境不支持的任务应删除，而不是放宽 verifier

当 GUI 无法稳定提交目标状态时，应：

1. 先用浏览器重放确认是环境问题。
2. 如果能小范围修复真实业务逻辑，则修复并回归。
3. 如果当前功能没有实现，则删除任务或标记 INVALID_ENV。
4. 不应通过降低 verifier 要求来制造虚假成功。

### 8.7 Verifier 应语义化，但不能遗漏关键约束

文本输出应允许等价自然语言和合理空白差异；结构化业务条件应严格验证。需要同时避免：

- False negative：要求特定措辞、隐藏字段或内部标签。
- False positive：只检查路线日期，却漏掉高铁类型、最低价格或目标乘车人。

## 9. 验证流程

每个 suite 至少应包含以下验证层次。

### 9.1 离线 verifier 测试

- 构造满足要求的 positive state，必须通过。
- 构造 unchanged initial state，必须失败。
- 针对每个关键字段构造 negative state。
- 检查 unexpected state change 和 clean diagnostics。

### 9.2 真实浏览器 setup smoke

- 每条任务可以正常 reset 和 setup。
- 初始状态不能直接通过 verifier。
- 模拟时间与 setup 数据一致。
- 任务涉及的 App 能正常打开。
- 当前 App 动态暴露的工具集合正确。

### 9.3 工具浏览器 smoke

- 工具调用成功并返回符合 schema 的结果。
- Mutation 工具产生预期状态变化。
- Query 工具没有 side effect。
- Navigation/Draft 工具执行后截图处于承诺页面。
- 工具后仍可继续通过 GUI 操作。
- 原始 MobileGym benchmark 在未启用工具时不受影响。

### 9.4 模型轨迹审查

对所有 verifier failure 检查：

- 指令是否明确。
- Agent 是否获得了 verifier 使用的信息。
- GUI、Tool Result、State 和 Verifier 是否一致。
- 坐标是否真的点错，还是控件无响应。
- 环境是否进入未实现或不可恢复分支。
- 是否存在错误收件人、额外修改等真实 side effect。

对 verifier pass 也应抽样检查，防止 verifier 漏字段造成 false positive。

## 10. Runner 和轨迹层的工程问题

探索过程中还修复或规避了以下运行问题：

- API 空响应会被解析成 ABORT。Runtime 增加了空响应重试，并提高模型输出上限到 8192。
- OpenAI-compatible API 需要显式处理代理变量、请求超时和流式/非流式差异。
- 工具返回最初没有展示在 HTML 中，后来加入每步 viewer。
- 模型需要明确知道坐标空间是 `[0,1000]`，否则不同模型可能按物理像素输出。
- 横向 launcher swipe 曾把一次左滑放大成跨两页，后续只对横向分页手势做了稳定化处理，避免影响普通滚动。
- App 名称存在同义词和新增 App 冲突，应在 prompt 和 app mapping 中使用稳定 ID/明确名称。
- 多 worker 可以显著加速评测，但每个 worker 必须拥有隔离的浏览器状态，并使用相同启动时间配置。

### 10.1 GUI-only 对照模式

为比较 App Tools 带来的收益，runner 支持同一个 XML Agent 的两种交互模式：

- `--interaction-mode hybrid`：提供 `mobile_use` 和当前前台 App 的业务工具。
- `--interaction-mode gui_only`：只提供 `mobile_use`，保留点击、输入、滑动、
  `open_app`、`answer` 和 `terminate` 等完整 MobileGym GUI 动作。

GUI-only 不是删除环境中的工具，也不是换用官方 runner 的另一种 Agent。Runtime
跳过 App Tool discovery，prompt 的 `<tools>` 只包含 `mobile_use`，parser schema 和
执行层也拒绝业务工具调用。两种模式继续共享截图、多轮历史、XML 格式、V4 setup、
冻结时间、verifier、模型参数和最大步数，使 App Tools 是否可用成为主要实验变量。

运行时只需在标准 V4 命令中选择：

```bash
python -m bench_env.hybrid_benchmark \
  --suite hybrid_tools_v4 \
  --interaction-mode gui_only \
  ...
```

模式会写入 `meta.json`、`results.jsonl`、`summary.json`、episode `trace.json` 和
HTML viewer。GUI-only 结果中的 App Tool 调用数应始终为 0。完整成对运行命令见
`trial_apps/mobilegym/bench_env/hybrid_benchmark/README.md`。

## 11. 当前结论

V1 到 V4 的角色可以概括为：

| 版本 | 主要目的 | 核心结论 |
| --- | --- | --- |
| V1 | 跑通 GUI + Tools + Verifier | 架构可行，但任务过于简单 |
| V2 | 快速提高复杂度 | 难度上升，但任务契约和环境有效性不足 |
| V3 | 扩大 App/工具覆盖并复用官方任务 | 覆盖和混合度较好，但系统性 benchmark 缺陷仍多 |
| V4 | Case-by-case 审计和一致性修复 | 已可作为内部 GUI + Tools 评测基线 |

当前 V4 的任务复杂度足够，工具和 GUI 混合明显，失败轨迹也能暴露有意义的模型能力问题。任务、环境、初始化和 verifier 已基本对齐。

正式冻结 V4 前仍应完成一次修复后的 76 条 full-suite rerun，并再次审查所有新失败。若结果稳定，且失败主要是明确 Agent error，则应冻结 V4，避免继续围绕 Gemini 的具体行为做模型特定调整。

## 12. 相关文件

```text
trial_apps/mobilegym/app_tools/
trial_apps/mobilegym/app_tools/TOOLS_DESIGN.md
trial_apps/mobilegym/app_tools/VALIDATION.md

trial_apps/mobilegym/bench_env/hybrid_agent/
trial_apps/mobilegym/bench_env/hybrid_benchmark/

trial_apps/mobilegym/bench_env/task/hybrid_tools_v1/
trial_apps/mobilegym/bench_env/task/hybrid_tools_v2/
trial_apps/mobilegym/bench_env/task/hybrid_tools_v3/
trial_apps/mobilegym/bench_env/task/hybrid_tools_v4/

trial_apps/mobilegym/bench_env/task/hybrid_tools_v2/FAILURE_AUDIT.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v3/FAILURE_AUDIT.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v4/V3_TO_V4_AUDIT.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v4/FAILURE_AUDIT_GEMINI31PRO.md
```

其中 V4 failure audit 记录的是 Case61 时间问题发现前的第一次分类。最终解释应以本文和修复后的下一次 full-suite run 为准。
