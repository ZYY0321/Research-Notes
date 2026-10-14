# 01 · Testing-Survey 组内协作评估与你的切入点（UX Agent × LLM Testing × 测试部实务）

## 一、远端同学（`yukinoyushi`）近期更新评估

刚刚已将 `ZYY0321/Testing-Survey` 从 `f126b86` 快进同步到 `584f6c8`（共新增约 2,500 行内容）。

### 1. 他做了什么
- **合入 4 篇核心文献笔记**：
  1. `notes/kong2019android.md`：Android 自动化测试传统系统综述（IEEE TR 2019），把随机、模型驱动（Stoat）、搜索式、符号执行底子理了一遍。
  2. `notes/yu2025guisurvey.md`：视觉移动 GUI 测试综述（ACM Computing Surveys 2025/2026），拆成生成（GEN）、录制重放（R&R）、框架（FRM）、脚本维护（SRP）、报告（RPT）、控件识别（ELE）、易用性与可访问性（U&A）、评测（EVA）八块。
  3. `notes/liu2024gptdroid.md`：GPTDroid（ICSE 2024），把控件树转文本 + 功能记忆做 LLM 探索。
  4. `notes/trong2026guilifecycle.md`：LLM 在 GUI 测试全生命周期的综述（PeerJ CS 2026）。
- **重写了 `field.md`（1,400+ 行）**：用一个统一的“自编任务应用（创建/删除任务，重启不恢复）”把三问（生成、判定、充分性）、四种输入信息（源码、layout 树、截图、需求规格）、以及 GUI Agent / GUI Testing / UX Testing 的边界全部写成了可读正文。
- **清理了协作噪音**：在第二个 commit（`584f6c8`）里删掉了临时的 `AGENTS.md`、`glossary.md`、`reading-guide.md`，把术语表收进了 `field.md#gui-terms`。

### 2. 客观评价：写得怎么样？
- **优点（非常扎实，是很好的合作者）**：
  - **边界意识极强**：他在笔记里反复区分“原论文真实实验证明的结论”和“为了讲清楚机制编的教学例子”，并且严格核对了摘要和正文的数字差异（比如指出 GPTDroid 摘要写“35 confirmed and fixed”，正文实际是 20 修复 + 15 确认）。
  - **已经帮你搭好了跳板**：他在 `field.md` 里专门写了一节《GUI Agent、GUI testing 与 UX testing 怎样相交》，明确区分了：**GUI Agent 执行任务**（看终态完没完成）、**GUI 功能测试**（看假删除等非崩溃错误能不能检出）、**UX 显示/可访问性检查**（遮挡、大字体失效）和**UX 用户体验评估**（用户理解成本）。
- **目前的空档（正好留给你的位置）**：
  - 他目前读的 4 篇主要是 **3 篇综述 + 1 篇早期纯文本 LLM 探索（GPTDroid，只抓 crash）**。
  - **2025–2026 最核心的“多模态非崩溃功能判定 + 视觉/UX 缺陷 + 探索型 Agent 评测”还没有人认领**：比如 VisionDroid（ICSE 2026）、GUITester（ACL 2026 Findings）、GUITestScape（2026.05）、AUITestAgent（工业界自然语言驱动 GUI 测试）。

---

## 二、工业界「测试部 / QA / 质量工程」到底在干什么？

如果你在组里做这个方向，或者跟工业界测试团队打交道，你要知道测试部不是“招一堆人手点 App”，现代大厂测试部（QA / QE / 质量效能）的核心痛点只有四件事：

| 测试部日常模块 | 真正耗人力的痛点 | 传统工具怎么做 | LLM / VLM / UX Agent 能切进去的点 |
|---|---|---|---|
| **1. 冒烟与回归测试（Regression）** | 每次发版前，核心链路（登录→搜商品→加购→下单→退款）必须全通。UI 一改版，Appium/UIAutomator 脚本全挂（Flaky Tests） | 写死 XPath / resource-id，改版后人工修脚本 | **意图驱动自愈（Self-healing / Execution）**：脚本不写死控件 ID，写业务意图 + 断言；界面变了由 Agent 语义重定位，且不掩盖真 Bug |
| **2. 探索式发版巡检（Exploratory）** | 找“没崩但坏了”的 Bug（按钮点了没反应、页面白屏、金额算错、状态不同步） | Monkey 随机乱点（只能抓 Crash，过不了登录和表单） | **带业务记忆与探测意图的 Agent**：这就是你在 `mobilegym-mock` 验收时发现的那些问题（京东结算算全车、拼多多筛完不改 state、返回栈错乱） |
| **3. UI / UX 与显示质量巡检（Visual & UX QA）** | 多机型、多分辨率、深色模式、中英文切换、大字号下：文字截断、重叠遮挡、图片裂开、对比度不够、交互反人类 | 像素级截图 diff（一有动态内容就满屏误报）或静态规则扫描 | **VLM 视觉判定 + 布局树联合核验**：这完全就是你做 **SlideGate（PPT 视觉/版式缺陷评测 + 人机对齐）** 的同构迁移 |
| **4. 线上问题复现与定位（Bug Reproduction）** | 用户或测试提了一句口语化的 Bug 报告（或一张截图），开发复现不出来 | 人工看着描述猜步骤 | **Bug Report → 可重放轨迹 + 自动生成失败断言（如 ASE 2025 ANDROB2O）** |

> 你在 `cua过程文档/交接与协作/721app现状检查/` 和 `全量环境验收/` 里干的事——发现“UI 看着能点但底层 store 没写进去”“深色模式/多语言漏配”“返回栈卡死”——**在软工顶会里就叫 Non-crash Functional & Display Bug Detection，在工业界就叫智能 UI/UX 验收系统**。

---

## 三、你在 `Testing-Survey` 里最省力、最出彩的认领方案

不要去跟同学抢传统 Android 覆盖率或早期综述。你在 `Testing-Survey` 里直接认领**和你的 UX Agent、SlideGate 视觉评测、以及 CUA 轨迹验证完全重合**的 4 篇论文 + 3 个概念：

1. **概念认领（`field.md`）**：
   - `llm-judge`（模型当判定器：直接把你在 SlideGate 里算人机一致性、控制假阳性的经验写进去）
   - `functional-bug`（非崩溃功能缺陷：结合你在 Mock App 里抓“假交互/状态未写入”的真实例子）
   - `display-bug`（显示与 UX 缺陷：结合你在 PPT 评测和移动端多语言/深色模式验收的例子）
2. **论文笔记认领（`notes/`）**：
   - `liu2024visiondroid`（ICSE 2026，非崩溃功能缺陷多模态检测）
   - `guitester2026`（ACL 2026 Findings，为什么任务型 GUI Agent 会掩盖缺陷）
   - `guitestscape2026`（2026.05，把探索测试拆成到达、触发、检测三阶段）
   - `auitestagent` / 华为鸿蒙工业界 GUI 测试论文（你之前调研过鸿蒙 AI 自动测试，正好补工业界闭环）
