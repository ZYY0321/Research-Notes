# 02-REF-ScienceBoard-VM-environment

- model: `claude-opus-4-8`
- elapsed_s: 69.0
- finish_reason: stop
- usage: {"prompt_tokens": 2477, "completion_tokens": 3424, "total_tokens": 5901, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 2477, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: 环境描述图.jpeg

---

# MobileGym++ 环境总览图审稿意见（对照 ScienceBoard/OSWorld 构图）

## 1. 这张图现在在说什么

这是 ScienceBoard/OSWorld 风格的"环境-评估器"闭环示意：左侧 New APP → Software（科研桌面软件集）→ Install 进入右上的 Environment (Virtual Machine)，VM 内暴露三块观测/管理面板（Screenshot + Set of Mark、A11yTree、VMManager）。下方 Evaluator 拿着 Task/Config/Downloads，跑一条编号 1–8 的调用链 `init() → predict() → eval()`，Agent 在 predict 处 Interact，最终判出 Task Complete / Incomplete。整张图的信息骨架就是**"环境提供观测→Agent 动作→评估器读状态判定"**这条回路，编号是它最强的可读性资产。

## 2. 内容张力诊断（作为对照标准，不是审它的对错）

作为你要借用的**参考构图**，它的张力来源清晰、可复用：
- **回路编号 1–8** 让人 10 秒读懂"谁先谁后、数据往哪流"——这是必须偷的。
- **三段式调用 init/predict/eval** 把"环境重置 / Agent 决策 / 判定"三件事在同一横轴上对齐——必须偷。
- **Software→Install→Env** 把"任意软件可安装进环境"的可扩展性讲清楚——必须偷其语义槽位。

但它与你的主张**根本冲突**的地方，如果照搬会直接误导审稿人：
- **VM / Virtual Machine**：你的是浏览器仿真的手机商业 App 世界（simulated），不是科研桌面 VM。照搬"Virtual Machine"标题=错误定性。
- **A11yTree 作为一等观测面板**：你的观测**只有像素截图，agent 读不到无障碍树、更读不到业务 store**。这块面板必须整块删除。
- **Set of Mark 作为主观测叠加**：你不做 SoM 主观测，agent 看的是原始截图。这个红框标注不能出现在主观测位。
- **VMManager**：换成你的 App census 语义（可安装 64 apps / 七领域 / 新构造 35），但绝不能叫 Manager，也不能列 GrassGIS 这类桌面软件。
- **Task Complete ✅ / Incomplete ❌ 对勾**：这是最危险的照搬点。你的判定是**读业务 store 的状态差分**，不是一个布尔对勾、更不看截图像不像、不看走了哪条路径。若照搬对勾图标，会把你最核心的"state-diff 判定"主张丢掉。
- **Software 里的科研软件图标**（TeX/VSCode/GrassGIS/Celestia/ChimeraX）：全部替换为你的商业 App 领域图标，且要能读出"七领域 / 64 可安装"。

数字口径提醒（画你的主图时）：环境侧只写 census（新构造 35 / 合计可安装 64 / 七领域），**不要**把训练侧 110+ apps 混进这张环境图。Bench 215 与成功率不属于这张总览图，别塞。

## 3. 改成 MobileGym++ 主图时的模块替换表

| ScienceBoard 槽位 | 照搬语法 | 你的替换内容 | 处理 |
|---|---|---|---|
| Software（科研软件集） | 偷"可插拔软件集合"语义 | 七领域商业 App 图标，角标"64 installable / 35 new" | 换内容留结构 |
| Install 箭头 | 偷 | "Install / Reset"（强调可重置） | 保留 |
| Environment (Virtual Machine) 标题 | ❌绝不照搬 | **Simulated Mobile App World (browser-based)** | 改定性 |
| Screenshot 面板 | 偷"像素观测" | 单块手机截图，占满观测区（**唯一观测**） | 放大为唯一 |
| Set of Mark 红框叠加 | ❌绝不照搬 | 删除 | 删 |
| A11yTree 面板 | ❌绝不照搬 | 删除；可留一句"pixels only, no a11y tree" | 删 |
| VMManager 列表 | ❌语义换 | "App Census: 7 domains · 64 apps"小卡片（非 Manager） | 换 |
| init/predict/eval 三段 | 偷全部 | 保留三段名或改 `reset()→act()→eval()`，但保留三分区 | 偷 |
| 编号 1–8 回路 | 偷 | 保留编号语法，重排为你的数据流 | 偷 |
| Action 图标（点击/API） | 部分偷 | click 与 tool 占**同一动作槽**（同一 store 写入），GUI-only 为一等路径 | 改语义 |
| MONITOR/STATES 标注 | 偷"读状态" | 改成 **read business store → state diff** | 强化 |
| Task Complete/Incomplete ✅❌ | ❌绝不照搬 | **Business-state diff（before→after）**，成败看差分 | 换判定表示 |
| Agent Interact 回环 | 偷 | 保留，注明"observes pixels only" | 偷 |

## 4. 视觉元素逐项优化（画你的主图时）

- **观测区层级**：截图必须是整张图最大的视觉块（你只有一个观测通道），当前参考图里 Screenshot 被 A11yTree/VMManager 挤成三分之一，你要反过来让截图占满右上大半区。
- **动作槽对齐**：click 图标与 tool 图标要**并排等大、同一个槽位框**，中间用"|"或"+"，绝不能画成 tool 在 GUI 之上或体积更大——避免暗示 tools 更强/等价。旁注小字 "GUI-only is first-class; tools = optional second channel, same store"。
- **判定块**：用 before/after 两个小状态卡片 + 一个 Δ 符号，取代 ✅❌。颜色用中性蓝灰表状态、用一个绿/红细边只标 Δ 命中与否，别用大对勾。
- **编号**：沿用深蓝圆底白字编号，保持 1–8 或按你回路重编，字号≥观测面板正文。
- **配色**：Environment 区、Evaluator 区、Agent 三块用三种低饱和背景色区分（参考图这点做得好，可偷）。
- **App census 卡片**：七个领域用七个小色块 chip，标"64 installable (35 newly built)"，一行读完。
- **双栏可读性**：`reset/act/eval` 三段字号在缩到单栏宽时仍要清晰，等宽字体保留（参考图用 typewriter 字体做代码调用，语义好，偷）。

## 5. 顶会可投稿重绘方案

**模块清单（左→右→下的阅读顺序）：**
1. 左：App Census 面板（7 domains chips + 64/35 角标）→ Install/Reset 箭头
2. 中上：**Simulated Mobile App World**（浏览器仿真手机外框），内嵌**唯一大截图**观测
3. 中下：Evaluator 横轴 `reset() → act() → eval()`，编号 1–N 回路箭头连观测与动作
4. act 下方：Agent，标"observes pixels only（no a11y tree / no store access）"
5. act 内动作槽：click 与 tool 并排等大，注"same action slot, same store, GUI-only first-class"
6. 右：Evaluator eval() 输出 = **business-store state diff（before→after→Δ）**，不是对勾

**阅读顺序**：census/install（能装什么）→ 观测（agent 看到什么：只有像素）→ 回路（怎么交互）→ 判定（怎么算成功：读 store 差分）。

**建议 caption（英文）：**
> *MobileGym++ environment loop. A newly built app is installed into a resettable, browser-based simulated mobile world; the agent observes raw pixels only (no accessibility tree, no store access) and acts through a shared slot where GUI clicks and app-native tools write to the same business store. Success is judged by the business-state difference (before→after), not by screenshot similarity or execution path.*

## 6. 必须删掉或改口的元素

- 删：**A11yTree** 面板、**Set of Mark** 红框、**VMManager** 命名。
- 改口：**"Virtual Machine" → "Simulated Mobile App World (browser-based)"**；对外统一 **simulated**，不用 mock。
- 改口：**Task Complete/Incomplete ✅❌ → business-store state diff (Δ)**。
- 改口：Action 双图标不得暗示 tools≥GUI；不写 "300+ tools = GUI 同权"；tools 标注为 optional second channel。
- 删/避免：把训练侧 110+ apps、Bench 215、任何成功率数字塞进这张环境总览图。

## 7. 优先级

- **P0**：删 A11yTree + Set of Mark，观测区改为唯一大截图；标题改为 Simulated Mobile App World；判定块由对勾改为业务 store 状态差分（before→after→Δ）。
- **P0**：Agent 处加注"pixels only, no a11y tree, no store access"。
- **P1**：VMManager 改为 App Census 卡片（7 domains / 64 installable / 35 new）；click 与 tool 等大同槽并加"GUI-only first-class, same store"注。
- **P1**：保留并沿用编号回路 + reset/act/eval 三段式，按你的数据流重排。
- **P2**：三区背景配色分层、chip 化领域、缩到单栏时的字号复核、Install 改为 Install/Reset 以突出可重置。
