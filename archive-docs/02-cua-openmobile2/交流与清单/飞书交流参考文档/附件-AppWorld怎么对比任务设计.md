# AppWorld 怎么写「别人测什么 / 我们多了什么」（只学论证结构）

学这一下：用**一根轴**把已有基准说清楚，再在这根轴上加复杂度。不要抄他们的数字（750、1–4、9.5、26、48.8），不要把「循环 / 分支 / 写代码」写成我们的轴——那是他们测交互式编码的轴。我们的轴要从出题口径和当前正文里自己提炼。

---

**Abstract 开门（ACL 2024）：**

Existing benchmarks for tool use are inadequate, as they only cover tasks that require a simple sequence of API calls. … We then created AppWorld Benchmark … natural, diverse, and challenging … requiring rich and interactive code generation.

现有工具基准不够，因为它们只覆盖需要**简单 API 序列**的任务。我们的基准要求**丰富、交互式的代码生成**（控制流，而不是一次接一次的短序列）。

---

**Intro 把缺口写死在同一根轴上：**

Existing benchmarks … involve a linear sequence of 1-4 API calls, without the need for rich code or writing code based on interaction with the environment. Further, they evaluate via comparison to a reference solution …

已有工作 = 线性 1–4 次调用 + 对照参考解。我们 = 调用之间有依赖、嵌进循环/条件等程序结构、并且跟环境交互后再写下一步；评测改成看状态、不比轨迹。

---

**Related / §5 对照表的逻辑（不是数字）：**

| 别人 | AppWorld |
| 线性短序列 API | 多次调用且调用之间有依赖 |
| 基本不需要代码 | 循环、条件、异常处理 |
| 很多不可执行 | 可执行、可控、可重置 |
| 比 gold 轨迹 | 程序化看数据库状态 |

一句话：读者能立刻复述「他们测顺序调用，我们测带控制流的交互编排」。

---

AndroidWorld / OSWorld / 前作 MobileGym-Bench 也是先定性再给自己的替代（轨迹匹配不够 → 读系统状态；模板 + 参数化；等等）。学这种「一根轴说完」，不要学成条目拼盘。
