# 真机百炼到页试跑备忘（2026-11-24/25）：高级指令批次与失败归因

> **存放状态**：已入 Research-Notes `archive-docs/01-ux-agent/2026-11-25_到指定页面研究/`（【到指定页面】）；工程原件仍在 UX-Agent。
> **作者**：正文由 **Claude Opus 5.5**（TokenHub CLAUDE55 / `awsb_L/sfa`）生成；§「主 agent 核对」为 Composer 补路径。更早的分条归因见 `api归因原文.md`（同 Opus 5.5）与 `api归因续.md`（**Fable 5.2**）。
> **新文献**：见同目录 `新文献对照_到页与高低级.md`（DestBench/TAG-Nav、DAC-Bench HL/LL、GUI-Robust 等）。
> **覆盖范围**：API 分条归因覆盖 **1125b 五失败**；总台账覆盖到 **1125d**（及当时进行中的 1125e）。**1125e 已收 11/11**；**1125f（149）仍在跑，尚无新一轮失败 API 归因**。

---

## 1. 一句话结论

T+6 阶段（12-15 交 Agent V1，交付内容为到达页面 + 7 类检测）的现状如下：

- **高级指令、免登录口径**：nav-high-nologin-1125d 到页 **11/12（91.7%）**，高于验收线 ≥80%。
- **深路径**：deep 0/3，尚未打通。
- **低级指令（验收线 ≥95%）**：本轮没有独立批次数据，**状态未知**。
- **剩余免登录高级**：1125e 共 11 条，在跑。

---

## 2. 数字台账

| 批次 | 口径 | ok/总 | 比例 | 备注 |
|---|---|---|---|---|
| demo5 | 百炼，实质 | 10/10 | 100% | 含小红书-H 重跑 |
| nav-high-167-1125b | 全部 | 13/18 | 72.2% | 5 条失败，见 §3 |
| 1125b · 短路径 commercial | 全部 | 13/15 | 86.7% | 失败为 amap、dingding |
| 1125b · 短路径 commercial | 剔除钉钉（登录墙） | 13/14 | 92.9% | 只剔除了已知登录墙；其余条目是否免登录未逐条核对 |
| 1125b · deep | 全部 | 0/3 | 0% | DEEP-ctrip 类 |
| nav-high-nologin-1125d | 免登录高级 | **11/12** | **91.7%** | 唯一失败：COM-kugou-tablet-g02-H |
| nav-high-nologin-1125e | 免登录高级（剩余） | **11/11** | 100% | 已收；无失败可归因 |
| nav-nologin-expand-1125f | 免登录 H+L 扩包 | 进行中 / 149 | — | 收完后若有失败再跑 API 归因 |

**口径规则**：按用户要求，「不能登录的先不跑」。钉钉等登录墙任务不计入分母，单独记为「范围外」。

**验收线对照**（来源：archive-docs/01-ux-agent/）：高级 ≥80%，低级 ≥95%。

- 1125d 达到高级线。
- 低级线无数据。

---

## 3. 失败原因词表

合并 1125b 的 5 条失败和 1125d 的酷狗 g02，共 6 条。

| 代码 | 类别 | 定义 | 实例 | 优先级 | 状态 |
|---|---|---|---|---|---|
| F-OBS | 观测管道失效 | 截图为 0 字节 PNG 或观测链路断，Agent 拿不到有效画面 | DEEP-ctrip（0 字节 png / 观测管道） | **P0** | 已整改（§4），未重跑验证 |
| F-TO-NAV | 导航超时（无效操作或循环） | 操作无效或反复滑动，480s 内未到页 | amap（点驾车无效）；kugou-g02（15 步，目标为粤语歌曲频道） | **P0** | 未解决 |
| F-TASK | 任务定义不可达或含噪 | 指令中有不合理子目标 | amap 原任务含「移到太平洋」 | P1 | 已删除该子目标；新卡仍超时 1 次 |
| F-DEEP | 深路径超时 | 多层级任务超出步数或时间预算 | DEEP-ctrip 超时（deep 0/3） | P1 | 未做 |
| F-LOGIN | 登录墙 | 目标页需要登录 | dingding | P1（范围外） | 已按口径剔除 |

**酷狗 g02 轨迹补记**

- 轨迹共 15 步：open_app ×1、tap ×6（i1–5、i8）、swipe ×8（i6–7、i9–14）。
- 后 6 步是连续 swipe，**疑似**在找频道入口时滑动循环。
- 轨迹文件中 `args` 均为空，且没有逐步 reason，所以**无法确认点击对象**。本条按 **timeout** 记，循环归因只作推测。

---

## 4. 整改：已落地 vs 未做

**已落地**

| 项 | 内容 | 验证 |
|---|---|---|
| harmony_ux_detect | 截屏由 uitest screenCap 改为 snapshot_display | 未单独回归 |
| captureDisplayPngToHost | 加 PNG 校验和重试（针对 F-OBS） | 未用 DEEP-ctrip 重跑验证 |
| 高德任务卡 | 去掉「移到太平洋」 | 新卡仍超时 1 次，暂未优先重跑 |

**未做**

- 超时或循环检测：例如连续 N 次 swipe 且画面无变化时触发回退或换策略。对应 F-TO-NAV。
- 轨迹记录补全：tool `args` 和逐步 reason 目前为空，影响归因。
- deep 任务：步数和时间预算调整、重跑。
- 低级指令批次（≥95% 线）。
- amap、kugou-g02 单条重跑。
- 1125e 结果回填。

---

## 5. 与 Research-Notes / Testing-Survey 对照

| 库 | 已有 | 缺 | 建议落点（仅建议，未上传） |
|---|---|---|---|
| Research-Notes | archive-docs/01-ux-agent/：验收说明书、高低级到达率线、交接文档、缺陷环境与探索采集、0917 demo | **没有** 11-24/25 真机百炼到页试跑记录和失败词表 | `archive-docs/01-ux-agent/` 下新建试跑记录（如 `2026-11-25_真机到页试跑/`），放本备忘和台账 |
| Research-Notes | ux-research-brief/STATE.md：12-15 交 V1 | 当前进度（1125d 91.7%、deep 0/3、低级未测） | 在 STATE.md 追加一行进度并链接上条 |
| Research-Notes | archive-docs/02-cua-openmobile2/：CUA 轨迹与失败模式 | 本项目失败码与其失败模式的映射 | 可在本备忘 §3 加交叉引用，不移动文件 |
| Testing-Survey | GUI testing、显示缺陷、oracle；GUITester 与导航笔记；README 明确「到达目标页面 ≠ UX 缺陷发现」 | 不是交付跑批记录，交叉少 | **不建议**放跑批记录；至多在导航笔记里加一句指向 Research-Notes 的链接 |

---

## 6. 论文/文献叙事定位

| 叙事 | 贴合度 | 理由 |
|---|---|---|
| **UX-Agent 验收：到页** | **最高** | 本工作就是 V1 到达率验收（高 ≥80% / 低 ≥95%），失败词表服务于交付 |
| GUI testing 导航 | 中 | F-TO-NAV、F-DEEP 是导航能力问题。但按 Testing-Survey README，到页本身不等于缺陷发现 |
| 模糊指令评测 | 中低 | 「高级指令」有一定模糊性（如「浏览粤语频道」），但本轮没有做模糊度标注或对照 |

**notes 中已有的相关条目**（相对路径；绝对根路径 `〈待补〉`）

- `Research-Notes/archive-docs/01-ux-agent/`：验收说明书、到达率指标、交接文档、缺陷环境与探索采集、0917 demo
- `Research-Notes/ux-research-brief/STATE.md`
- `Research-Notes/archive-docs/02-cua-openmobile2/`：CUA / OpenMobile 轨迹与失败模式
- 毕设 / RealEval / AmbiBench：模糊指令评测线（具体路径 `〈待补〉`）
- `Testing-Survey/`：README（到页 ≠ UX 缺陷）、GUITester 与导航相关笔记（具体文件名 `〈待补〉`）

---

## 7. 下次可上传包清单

| # | 文件 | 绝对路径 | 状态 |
|---|---|---|---|
| 1 | 本备忘 | `〈UX-Agent 材料目录，待补〉/2026-11-25_真机到页试跑备忘.md` | 暂存 |
| 2 | 1125d 结果目录 | `/Users/user/uxagent/HarmonyArena-fdu_agent/results/nav-high-nologin-1125d-2026-11-25T10-06-00-478Z/` | 已有 |
| 3 | 酷狗 g02 轨迹摘要 | `〈与本备忘同目录，待补〉/kugou_g02_轨迹摘要.txt` | 无逐步 reason 和 args |
| 4 | 1125b 结果目录 | `/Users/user/uxagent/HarmonyArena-fdu_agent/results/nav-high-167-1125b-〈时间戳待补〉/` | 待确认 |
| 5 | 1125e 结果目录 | `/Users/user/uxagent/HarmonyArena-fdu_agent/results/nav-high-nologin-1125e-〈时间戳待补〉/` | 在跑 |
| 6 | demo5 结果目录 | `〈待补〉` | 待确认 |
| 7 | 整改 diff（harmony_ux_detect、captureDisplayPngToHost、高德任务卡） | `〈仓库内路径待补〉` | 需导出 |

**上传前检查**

1. 补全所有 `〈待补〉` 路径。
2. 回填 1125e 结果。
3. 确认 1125b 中除钉钉外是否还有需要登录的任务，修正 §2 的剔除口径。

---

## 主 agent 核对（补绝对路径；可推翻 API）

| # | 文件 | 绝对路径 |
|---|---|---|
| 本备忘 | `/Users/zhangyingying/UX-Agent/docs/材料/2026-11-24_1215高低级指令导航交付/失败归因_1125/api总归因与笔记对照.md` |
| 1125b | `/Users/user/uxagent/HarmonyArena-fdu_agent/results/nav-high-167-1125b-2026-11-25T07-14-45-048Z/` |
| 1125d | `/Users/user/uxagent/HarmonyArena-fdu_agent/results/nav-high-nologin-1125d-2026-11-25T10-06-00-478Z/` |
| 1125e（在跑） | `/Users/user/uxagent/HarmonyArena-fdu_agent/results/nav-high-nologin-1125e-2026-11-25T10-35-07-073Z/` |
| demo5 | `/Users/user/uxagent/HarmonyArena-fdu_agent/results/demo5-bailian-1124-2026-11-24T15-02-42-098Z/` |
| 酷狗摘要 | `/Users/zhangyingying/UX-Agent/docs/材料/2026-11-24_1215高低级指令导航交付/失败归因_1125/kugou_g02_轨迹摘要.txt` |
| Research-Notes 根 | `/Users/zhangyingying/Research-Notes`（GitHub `https://github.com/ZYY0321/Research-Notes`） |
| Testing-Survey | `/tmp/Testing-Survey-clone` 或 `Desktop/research-lab/testing-survey`（`https://github.com/ZYY0321/Testing-Survey`） |

建议上传落点：`Research-Notes/archive-docs/01-ux-agent/2026-11-25_真机到页试跑/`（她点头后再 push）。Testing-Survey 只交叉引用，不塞跑批。