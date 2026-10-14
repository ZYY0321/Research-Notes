# MobileGym 本地开发变更审查

## 1. 审查范围

本文审查从项目最初 clone 的远端基线到 2026-07-27 当前工作区的全部本地开发。

Git 时间线如下：

```text
738c13a  origin/main，最初 clone 基线
   |
d12f098  mobilegym official evaluation
   |
5f36284  GUI and Tools Hybrid Agent Demo
   |
当前工作区：40 个已跟踪文件被修改，另有 196 个未跟踪文件（不含本文）
```

当前 `main` 比 `origin/main` 领先两个提交。用户最初提到的 `d12f098` 之后，实际上
还有一个已经提交的 `5f36284`；大量 V1-V6 benchmark、扩展工具、模型适配和环境修复
仍未提交。

本文不把原始项目在 `738c13a` 之前已经存在的淘宝闪购、Days Matter 等 App 算作本轮
新增功能。`runs/` 和截图归档属于实验产物，不计入源代码 diff，但在第 10 节单独说明。

## 2. 总体结论

从 clone 到现在，代码库完成了六组主要工作：

1. 跑通并记录官方 MobileGym 256 任务的 Gemini-3.1-Pro 复现；
2. 建立浏览器环境侧 App Tool 框架，并扩展到 19 个 App、203 个工具；
3. 建立独立 Python Hybrid Agent Runtime，支持 GUI + Tools 和 GUI-only；
4. 建立独立 benchmark runner 和 V1-V6 六代任务集，当前固定版为 V6 的 75 条任务；
5. 为固定时间、GUI-only 可完成性和 GUI/Tool 状态一致性修复若干 App 与模拟器细节；
6. 形成设计指南、失败审计、证据归档和 7 个模型的 V6 双设置基线。

整体架构已经可以交接，但当前工作区还不适合直接推送或交给同事继续修改，原因是：

- `tools/test_api.py` 和已提交的 Python bytecode 中存在明文 API 凭证；
- 绝大多数 V1-V6、扩展工具和文档仍是未跟踪文件；
- 两组 TypeScript 环境工具测试因模拟时间 bootstrap 与测试 window stub 不兼容而失败；
- 重要截图和完整 run 被 `.gitignore` 排除，不能通过普通 Git clone 交付。

## 3. 已提交变更一：`d12f098` 官方评测复现

该提交共有 9 个文件，主要目标是复现官方 MobileGym-Bench 256 个 test tasks。

### 3.1 评测链路

新增：

- `MOBILEGYM_REPRODUCTION.md`
- `tools/test_api.py`

完成了：

- Google GenAI SDK 和 OpenAI-compatible API 的 smoke；
- `generic_v2`、state judge、grounded 模式的正式启动配置；
- proxy/NO_PROXY、并行 worker、8192 max token 等运行说明；
- 官方指标 SR、PR、L1-L4、FC、USE 的本地重算和对比。

最终保留的官方复现包含 256/256 条 episode。原始 run 的 SR 是 134/256；按已同步的
官方 clean/ignore 口径离线重算后是 146/256，即 57.03%，接近官方 58.8±1.4。

详见 [MOBILEGYM_REPRODUCTION.md](MOBILEGYM_REPRODUCTION.md)。

### 3.2 LLM 空响应重试

修改：

```text
trial_apps/mobilegym/bench_env/llm/openai_chat.py
```

非流式请求现在会对空 `content` 重试，最多 3 次，并记录 `finish_reason`。此前空响应
会进入 Agent 解析失败并最终算作 `ABORT`。网络连接、超时、服务器错误和可重试状态码
继续使用相同重试循环。

当前工作区又在此基础上加入了总 deadline：每次 retry 的请求 timeout 不得超过剩余
总推理时间，防止多次 retry 让一次 Agent step 大幅超过 `infer_timeout`。

### 3.3 官方 clean/USE 口径

修改：

```text
trial_apps/mobilegym/bench_env/task/base.py
```

`BaseTask.always_ignore` 增加：

- TaskManager 任务栈和最近任务面板；
- 本地扩展 App 后自动生成的 Launcher 页数/布局；
- alarm manager 和 media session 等派生镜像状态。

这会直接改变所有使用 `BaseTask` clean 判定的官方评测结果，属于**评测口径修改**，
不是仅在 Hybrid benchmark 中生效的独立功能。

### 3.4 小红书 expected changes

修改两个官方 cross-app task：

```text
RedbookUserBestWorstToNotes.py
RedbookUserTopCollectToWechat.py
```

两者将 `redbook.searchHistory` 纳入允许变化，避免正常搜索被判为 unexpected side
effect。这同样会影响官方任务的 clean/USE。

### 3.5 App 名称别名

修改：

```text
trial_apps/mobilegym/bench_env/env/mobile_gym.py
```

为 Map 增加“高德地图”“高德”“Maps”“AMap”等别名，为 Taobao 增加“淘宝”“淘宝网”
及英文别名。该变更只影响 `open_app` 的名称解析，不改变 App 业务状态。

### 3.6 非功能性变化

`package-lock.json` 只出现 npm 版本产生的 peer metadata 变化，没有新增依赖。

该提交还误加入了：

```text
tools/__pycache__/test_api.cpython-311.pyc
```

这是生成物，不应进入版本控制。

## 4. 已提交变更二：`5f36284` 首个 GUI + Tools Demo

该提交新增 53 个文件、约 5.6k 行，实现了第一版完整端到端链路。

### 4.1 环境侧 App Tool 框架

新增：

```text
trial_apps/mobilegym/app_tools/
```

核心能力：

- `ToolDefinition`、schema、annotation、结构化错误；
- 按 App 注册和列出工具；
- `window.__MOBILE_GYM_TOOLS__.listTools()`；
- `window.__MOBILE_GYM_TOOLS__.callTool()`；
- query/navigation/draft/write 四类工具；
- 静态加载定义、动态懒加载 handler；
- 浏览器状态 diff、GUI 后续可操作性和工具错误测试。

`index.tsx` 会始终导入 `app_tools/bootstrap.ts`，所以普通模拟器页面也会注册全局工具
API；但 bootstrap 只静态导入 schema，App store 和 handler 只有真正调用工具时才
动态加载，不会主动执行工具业务逻辑。

### 4.2 第一批工具

第一批包含：

| App | 工具数 |
| --- | ---: |
| Calendar | 5 |
| WeChat | 10 |
| Taobao Instant | 10 |
| Days Matter | 9 |
| Clock | 9 |
| Notes | 10 |
| **合计** | **53** |

工具优先复用 App store action 或正常 route，不用 `__SIM__.setState()` 执行业务操作。
Calendar 的 event draft 只预填页面，不直接保存，提醒和最终提交保留给 GUI。

### 4.3 Calendar App 改动

为支持 GUI/Tool 同源，Calendar 普通 App 也做了以下共享修改：

- 新增 `domain/eventQueries.ts`，统一日期解析、搜索、范围和 busy interval；
- 首页支持通过 `date`/`view` query 参数打开指定日期和视图；
- 新建页支持工具 draft query 参数；
- 搜索页复用同一 `searchCalendarEvents()`；
- 工具 draft 保存后回到 Calendar 首页。

这些改动会影响 Calendar 正常 GUI 路由和搜索，但不包含 benchmark 答案或隐藏状态。

### 4.4 第一版 Hybrid Agent Runtime

新增：

```text
trial_apps/mobilegym/bench_env/hybrid_agent/
```

第一版运行循环：

1. 根据当前前台 App 动态获取工具；
2. 每轮构造 `mobile_use + 当前 App Tools` 的 XML system prompt；
3. 模型返回一个 Qwen 风格 XML tool call；
4. GUI 动作转为 `MobileGymEnv.step(Action)`；
5. App Tool 通过 Playwright 调用浏览器 API；
6. 执行完成后重新截图并把 tool result 反馈给下一轮；
7. 保存 prompt、response、前后截图、工具参数、工具返回和 HTML trace。

General XML Agent 使用标准多轮消息：保留过去的 user/assistant 文本历史，省略过去截图，
仅在当前 user turn 提供最新截图。

### 4.5 工程集成

- ESLint/TypeScript include 增加 `app_tools/`；
- `npm run lint` 增加工具目录；
- 增加 Calendar、multi-app 和 benchmark isolation 测试；
- 增加确定性的 Calendar demo setup 和 standalone CLI。

## 5. `5f36284` 之后的未提交主要功能

### 5.1 扩展到 203 个工具

在原 53 个工具外，为 13 个 App 增加 150 个工具：

| App | 工具数 | 主要能力 |
| --- | ---: | --- |
| Map | 14 | POI 搜索、附近排序、比较、打开地点/路线、导航偏好 |
| Weather | 10 | 城市搜索、当前/预报/空气质量、条件筛选、添加城市 |
| Railway 12306 | 14 | 车站/车次/中转/订单/乘客查询和购票页导航 |
| Alipay | 13 | 账单查询汇总、余额、联系人、转账草稿、聊天 |
| File Manager | 11 | 搜索、目录、文本读取、存储汇总、创建目录、复制 |
| Tencent Meeting | 11 | 会议查询、参会统计、加入/预约草稿、已读 |
| Bilibili | 12 | 搜索、排行榜、视频/作者信息、收藏和关注 |
| RedBook | 11 | 笔记/用户/聊天查询、页面导航、发布草稿 |
| WeChat Reading | 11 | 搜书、热搜、书架、阅读统计、打开阅读器 |
| Spotify | 12 | 歌曲/艺人/播放历史/歌单查询、加入队列/歌单 |
| eBay | 8 | 搜索、比较、详情、打开页面、保存搜索 |
| Reddit | 9 | 帖子/社区/聊天查询、打开页面、加入社区 |
| Taobao | 14 | 商品/店铺/购物车/订单/优惠券查询和 checkout 草稿 |

完整 19 App、203 Tool 的 schema、直接写入边界和刻意不开放能力见
[TOOL_CATALOG.md](trial_apps/mobilegym/app_tools/TOOL_CATALOG.md)。

新增 `core/define.ts` 和 `core/helpers.ts`，统一工具命名、closed schema、annotation、
分页返回、输入校验和 route 编码。`bootstrap.ts` 保持 definition 静态、handler 懒加载。

### 5.2 Agent Runtime 扩展

在 General XML Runtime 上继续增加：

- `hybrid` / `gui_only` 两种 interaction mode；
- GUI-only 只移除 App Tools，保留相同 prompt 结构、截图、GUI 动作和 `open_app`；
- `[0,1000]` 和 1080×2400 physical 两类坐标；
- 未知 App 的 `APP_NOT_FOUND`，避免 `open_app` 假 success；
- Launcher、Recents、通知栏出现时隐藏 App Tools；
- 工具执行前再次检查前台 App，拒绝 stale tool context；
- HTML 显示 interaction mode、tool call、tool result 和 call ID；
- benchmark 并行 worker 独立绑定环境页面和 Tool Client。

### 5.3 模型专用协议

新增两个隔离适配器：

| 适配器 | 文件 | 关键差异 | 当前定位 |
| --- | --- | --- | --- |
| Kimi-K2.6 | `kimi_k2_6.py` | Thought + Action JSON、`[0,1]` 坐标、最近 3 张截图、Kimi thinking 参数 | 已用于 V6 正式结果 |
| GPT Responses | `gpt_responses.py` | Responses API computer tool、原始 1080×2400 坐标、`detail="original"`、native function tools | 实验性；未纳入最终 V6 七模型表 |

两者复用相同 `HybridAgentRuntime`、MobileGym 动作执行、App Tool 发现和 verifier，不修改
General XML Agent。GPT 适配曾暴露 grounding/runtime 匹配问题，当前不能把它视为已
完成质量验证的正式基线。

### 5.4 独立 Hybrid Benchmark Runner

新增：

```text
trial_apps/mobilegym/bench_env/hybrid_benchmark/
```

Runner 负责：

- 动态加载指定 suite；
- 每个 worker 建立独立环境和模型 client；
- 执行 `BaseTask.setup()`；
- 从 Launcher 开始 Hybrid/GUI-only agent loop；
- 获取所有任务 App 的最终完整状态；
- 调用同一 state verifier；
- 输出 `meta.json`、`tasks.json`、`results.jsonl`、`summary.json` 和每任务 HTML；
- 汇总 SR、stop reason、App Tool 调用数和 distinct coverage。

`repair_run.py` 支持把少量 rerun 替换进旧 run，并记录 provenance。该能力用于历史修复，
但当前指南要求正式版本优先生成不可变的新 run，避免原位覆盖首次问题轨迹。

## 6. Hybrid Benchmark V1-V6

| 版本 | 任务数 | 核心变化 | 当前定位 |
| --- | ---: | --- | --- |
| V1 | 90 | 围绕首批 53 tools 构建固定任务，证明 setup→agent→state verifier 全链路 | 历史原型；任务偏简单、模板相似 |
| V2 | 50 | 40 条固定官方 L3/L4 + 10 条新 cross-app，高层指令 | 暴露继承 verifier、指令歧义和环境缺失 |
| V3 | 80 | 67 条官方 test、8 条 Taobao、5 条 cross-app，覆盖 203 tools | 提高复杂度，但仍有任务契约问题 |
| V4 | 76 | 逐条审计 V3，固定 `2026-07-12 09:00`，删除 4 条不可完成任务 | 首个以一致性为中心的版本 |
| V5 | 76 | 对 41 条任务做 instruction/setup/verifier 修订并增加环境边界测试 | 大幅减少文本 matcher 和隐藏条件问题 |
| V6 | 75 | 删除 GUI-only 无稳定路径的 Case45，修复 GUI 可见精度、天气、滚轮和等价表达 | **当前固定版** |

V6 的核心契约是：同一任务必须能通过纯 GUI 完成；Hybrid 和 GUI-only 只在是否暴露 App
Tools 上不同，使用相同 instruction、setup、environment 和 verifier。

V6 已完成 7 个模型的双设置测试。最高结果为 Gemini-3.1-Pro-Preview：

```text
Hybrid   64/75 = 85.33%
GUI-only 44/75 = 58.67%
```

七个 Hybrid run 合计调用 1109 次 App Tool，实际覆盖 99/203 种工具和 19 个 App。
完整表格见
[MOBILEGYM_HYBRID_GUIDELINE.md](MOBILEGYM_HYBRID_GUIDELINE.md#76-v6-最终评测结果)。

## 7. 对 App 和模拟器本体的细节修改

以下改动不是单纯新增独立工具文件，普通 GUI 或官方任务也可能观察到。

| 模块 | 改动 | 目的 | 普通 GUI/官方评测影响 |
| --- | --- | --- | --- |
| Calendar | 共享查询函数、date/view 路由、event draft 预填 | GUI 与 Tools 使用同一业务语义 | Calendar 搜索和路由行为改变 |
| Alipay | 三个年月滚轮按真实 `scrollTop` 读值，只初始化一次，确认时重读 DOM | 修复滚到目标月份但内部 state 未更新 | 正常账单筛选更稳定 |
| Weather | GUI 和 Tool 统一 `addSavedCityWithBundle`；主页面、管理页和预报页共享离线 fallback | 修复添加南京后出现 `--°`、无法继续 GUI | 添加/切换城市行为改变 |
| Spotify | 最近播放列表显示真实 `HH:mm` | 让“今天第 N 首”有稳定 GUI 可观察顺序 | 增加了 GUI 可见信息 |
| Taobao | checkout 保存精确 `sourceCartLineIds`，支付后只删除本次结算行 | 修复工具准备 checkout 后误删其他已选购物车行 | 普通购物车结算更精确 |
| Tencent Meeting | 加入会议页和预约页读取 query 参数预填会议号、标题、时间、时长、邀请人 | 支持 navigation/draft 工具后继续 GUI | 无 query 参数时保持旧默认 |
| Notes | 列表固定按 pinned、updatedAt 排序 | 对齐“最新笔记”等任务的 GUI 观察 | 笔记显示顺序可能改变 |
| Taobao Instant Tool | 搜索匹配不再使用隐藏 `category` 字段 | 避免 Tool 命中 GUI 文本无法解释的候选 | 只影响 Tool 搜索结果 |
| WeChat Tool | `findLast()` 改为 reverse/find | 提高浏览器兼容性 | 业务语义不变 |
| Launcher/横向分页 | 水平 x-scroll-snap swipe 时暂时关闭 snap，手势结束恢复 | 防止一次左滑从第一页跳到第三页 | 所有横向 snap 容器受益；纵向不变 |
| Simulator Time | URL 可传 `mobilegym_simulated_time` 和 `mobilegym_time_flowing` | 在 App eager init 前冻结统一时间 | 普通无参数 URL 仍使用 real time |

其中 Weather、Alipay、Taobao、Notes 和横向手势属于共享环境修复；它们没有读取任务
答案，但可能改变原官方任务的 GUI 执行轨迹。因此后续升级原项目时应保留回归测试，
不能简单把整个 `apps/` 或 `os/` diff 当作 Hybrid 专用代码删除。

## 8. 对原 MobileGym 的隔离边界

### 8.1 默认不执行的独立功能

以下内容只有显式使用时才生效：

- `bench_env.hybrid_agent`；
- `bench_env.hybrid_benchmark`；
- `hybrid_tools_v1` 到 `hybrid_tools_v6`；
- App Tool handler 的实际业务操作；
- Kimi/GPT 专用协议；
- Hybrid/GUI-only 自定义 prompt。

这些模块没有改官方 `bench_env.agent`、官方 split 或原 runner。

### 8.2 普通页面会加载但不产生业务 mutation

`index.tsx` 会加载 `app_tools/bootstrap.ts`，向 `window` 注册工具 API。定义会进入页面
bundle，但 handler 按需加载；如果官方 agent 不调用该 API，工具不会主动修改 App
state。`appToolsBenchmarkIsolation.test.ts` 用于保护这一边界。

### 8.3 明确会影响原评测或普通 GUI 的修改

- `BaseTask.always_ignore` 和两个 RedBook `expected_changes`：直接改变 clean/USE；
- `openai_chat.py`：改变空响应、retry 和 timeout 行为；
- `MobileGymEnv.APP_NAME_MAP`：改变 open-app 名称解析；
- Calendar、Alipay、Weather、Spotify、Taobao、Tencent Meeting、Notes 的共享 UI/state；
- `simInput.ts`：改变受保护的横向 scroll-snap 手势；
- URL 模拟时间参数：只有带参数的环境才改变时间。

因此正确表述应是：**Hybrid runner 和任务集与官方评测隔离，但整个工作区并非完全没有
改动原 MobileGym 共享实现。**

## 9. 测试与验证状态

### 9.1 本次重新执行

Python：

```text
bench_env/tests/hybrid_agent
bench_env/tests/hybrid_tools_v1 ... hybrid_tools_v6
111 passed
```

TypeScript 目标测试：

```text
6 个文件通过，13 tests passed
2 个 suite 导入失败，24 tests skipped
```

失败 suite：

```text
tests/calendarToolEnvironment.test.ts
tests/multiAppToolEnvironment.test.ts
```

根因是 `simulatorConfig.ts::readTimeBootstrap()` 直接读取 `window.location.search`，而这
两组 Node/Vitest 测试手动构造的 `window` 没有 `location`。应在交接前选择一个最小
修复：

- production 代码使用 `window.location?.search ?? ''`；或
- 两组测试 stub 增加 `location: { search: '' }`。

优先建议让 production bootstrap 对不完整 window 更健壮，并保留回归测试。

TypeScript 类型检查：

```text
npx tsc --noEmit
```

在 Node 默认约 2 GB heap 下 OOM；使用
`NODE_OPTIONS=--max-old-space-size=4096` 后通过，没有类型错误。

Lint：

```text
8 errors, 76 warnings
```

8 个 error 位于原基线已存在且本轮未修改的 Days Matter/Meituan 文件，属于仓库原有
TimeService lint debt；App Tools 没有新增 lint error。本轮 Weather 改动产生一条
unnecessary dependency warning，后续可以清理。

### 9.2 历史验证记录

[app_tools/VALIDATION.md](trial_apps/mobilegym/app_tools/VALIDATION.md) 记录了真实浏览器
工具审计：

- 13 App 扩展的 150 个工具全部注册；
- 159 次调用成功，0 次失败；
- 55 个 navigation/draft/write 后截图；
- read-only 工具无业务状态变化；
- write 工具只修改允许字段；
- draft 不直接产生最终业务对象；
- Tool 后 GUI 页面可继续操作。

V5/V6 另有 Python verifier 正反例、browser setup smoke 和 boundary smoke。由于清理
旧 `runs/`，本次没有重新执行完整浏览器 smoke；其结论和历史证据保留在相关文档。

## 10. 文档、结果和证据

新增的主要根文档：

| 文档 | 用途 |
| --- | --- |
| `MOBILEGYM_REPRODUCTION.md` | 官方 256 benchmark 复现 |
| `MOBILEGYM_HYBRID_DESIGN.md` | GUI + Tools 架构和 V1-V4 演进 |
| `MOBILEGYM_HYBRID_GUIDELINE.md` | 任务五层契约、V1-V6 问题案例和发布门禁 |
| `MOBILEGYM_HYBRID_HANDOFF.md` | 接手入口 |
| `MOBILEGYM_HYBRID_RUNS.md` | 当前保留实验目录 |
| 本文 | 从 clone 基线到当前工作区的总变更审查 |

当前 `trial_apps/mobilegym/runs/` 已清理为：

- 14 个 V6 正式 run；
- 1 个官方 256 任务复现；
- 1 个 Calendar Hybrid demo；
- 总体积约 11 GiB。

代表性历史错误案例位于：

```text
trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/
```

该目录约 688 MiB，其中 `episodes/` 下 12,358 个截图/HTML/trace 文件被该目录自己的
`.gitignore` 排除。普通 Git commit 只能包含索引和 run metadata，不能带走截图证据。

## 11. 交接前风险和待办

### P0：必须先处理

1. **API 凭证泄露**  
   `tools/test_api.py` 当前包含多个真实 API key 和内部 endpoint；`d12f098` 已经把至少
   一个 key 和包含常量的 `.pyc` 提交进 Git 历史。交接前应：
   - 立即轮换所有出现过的 key；
   - 改为从环境变量读取；
   - 删除并 ignore `tools/__pycache__`；
   - 若仓库将推送到多人或公开远端，评估重写历史，而不只是改当前文件。

2. **未提交改动规模很大**  
   审查开始时有 40 个已跟踪文件被修改、196 个未跟踪文件（不含本文）。未跟踪部分包含全部 V1-V6、
   13 App 扩展工具、benchmark runner、模型适配、测试和核心文档。若只 push 当前两个
   commit，同事拿不到这些功能。

3. **修复 TypeScript 环境工具测试**  
   处理 `window.location` bootstrap 兼容问题，重新拿到 Calendar 6 tests 和 multi-app
   18 tests 的有效通过结果。

### P1：交接前建议处理

1. 为当前工作区创建 checkpoint branch/commit，并按功能拆分，避免 200 多文件一次性
   混合提交。
2. 明确 688 MiB evidence 和 11 GiB runs 的外部交付方式；它们不会随普通 Git clone
   传输。
3. 更新 `hybrid_agent/README.md` 中“未来再接 benchmark adapter”的过时描述；adapter
   已经存在。
4. 统一 GPT 文档口径：V5 README 的 physical XML 与 benchmark README 的 native
   Responses 方案并存，当前正式推荐应明确为哪一条。
5. `tools/test_api.py` 的模块说明仍写 Gemini smoke，但默认模型已多次切换，建议改为
   provider-neutral CLI/config。
6. V6 通过 V5 spec/task/verifier 复用未修改任务。修改 V5 共享实现时必须跑 V6 回归；
   这不是运行时失败后回退旧 verifier。
7. 官方复现目录的原始 `summary.json` 是 52.34% SR，57.03% 是离线 clean 规则重算；
   汇报时以 `MOBILEGYM_REPRODUCTION.md` 为准，避免直接读取 summary 产生误解。

### P2：可后续整理

- 移除 `package-lock.json` 的无语义 peer metadata churn；
- 清理 Weather hook warning 和仓库原有 lint debt；
- 为 TypeScript 全量检查固定 4 GB Node heap 的脚本；
- 将历史 run 的旧链接统一指向 evidence archive；
- 将 `repair_run.py` 限制为显式维护工具，正式发布默认采用不可变 run。

## 12. 建议的提交拆分

在不重写已有两个提交的前提下，后续工作区建议至少拆成：

1. `security/cleanup`：移除 key、pycache、整理 API smoke；
2. `expanded-app-tools`：13 App、150 tools、core helpers 和工具测试；
3. `shared-environment-fixes`：Weather、Alipay、Spotify、Taobao、Meeting、Notes、
   simulator time 和 horizontal swipe；
4. `hybrid-runtime-v2`：GUI-only、坐标模式、Kimi/GPT adapter、timeout、artifacts；
5. `hybrid-benchmark-runner`：runner、repair utility 和 runner tests；
6. `hybrid-suites-v1-v6`：任务、setup、verifier、smoke、审计；
7. `hybrid-docs-and-evidence-index`：设计、指南、交接、run manifest 和可提交的证据索引。

如果允许重写尚未推送的本地历史，更干净的方案是先清除 `d12` 中的凭证和 pycache，
再按上述边界重组提交。

## 13. 关键入口

```text
MOBILEGYM_HYBRID_HANDOFF.md
MOBILEGYM_HYBRID_GUIDELINE.md
MOBILEGYM_HYBRID_RUNS.md
trial_apps/mobilegym/app_tools/
trial_apps/mobilegym/bench_env/hybrid_agent/
trial_apps/mobilegym/bench_env/hybrid_benchmark/
trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/
```

工具内部实现与扩展规范以 `app_tools/TOOLS_DESIGN.md` 为准；任务构造和 verifier 审查
以 `MOBILEGYM_HYBRID_GUIDELINE.md` 为准；当前正式实验和保留轨迹以
`MOBILEGYM_HYBRID_RUNS.md` 为准。
