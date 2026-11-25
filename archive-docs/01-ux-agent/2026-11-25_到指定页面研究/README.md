类型：核心 ｜ 归属：T+6 / 12-15 Agent V1 前置 ｜ 状态：维护中

# 【到指定页面】研究存档（2026-11-24/25）

> **主题边界（必读）**：本目录只研究 **GUI Agent 根据高级/低级指令到达指定页面（page arrival / destination navigation）**。  
> **不是**截断 / 开合 / UX 缺陷检出主线；到达后的 7 类检测另册。  
> 与 Testing-Survey 口径一致：**到指定页面 ≠ UX 缺陷发现**。

## 研究问题（一句话）

在鸿蒙真机（Mate X5）上，用百炼 Qwen 驱动现有 HarmonyArena runtime，**模糊/高级指令（及成对低级）能否稳定到达目标页？失败可归成哪些原因？如何统一整改？**

## 与验收口径的关系

- 说明书：高级到达率 ≥80%，低级 ≥95%（见同仓 `archive-docs/01-ux-agent/` 验收设计说明书）。
- 11-23 决议：12-15 交 Agent V1 = **到达页面 + 7 类检测**（先 Prompt）；本目录只沉淀「到达」侧证据。
- 外部对齐：DestBench / TAG-Nav「只评到页」；DAC-Bench 高/低级掉点（见 `材料/新文献对照_到页与高低级.md`）。

## 当前数字（截至同步日；扩测仍在跑）

| 批次 | 口径 | 结果 |
|---|---|---|
| demo5 百炼 | 5 App × H/L | 实质 **10/10**（含小红书-H 重跑） |
| nav-high-167-1125b | 高级混合（含 deep） | **13/18**；短路径 commercial 13/15；deep 0/3 |
| nav-high-nologin-1125d | 免登录高级 | **11/12** |
| nav-high-nologin-1125e | 免登录高级 | **11/11** |
| nav-nologin-expand-1125f | 免登录 H+L 扩包 | **149 条进行中**（同步时未收完） |

需登录（钉钉/企微/微信等）按用户要求不跑，不进分母。

## 材料索引

| 文件 | 内容 | 作者 |
|---|---|---|
| [材料/api总归因与笔记对照.md](材料/api总归因与笔记对照.md) | 总台账 + 失败词表 + 整改 + 上传清单 | Claude Opus 5.5（CLAUDE55） |
| [材料/api归因原文.md](材料/api归因原文.md) | 1125b 五失败分条归因 | Claude Opus 5.5 |
| [材料/api归因续.md](材料/api归因续.md) | 整改 B/C/D + 短路径动作 | Claude Fable 5.2 |
| [材料/统一整改清单.md](材料/统一整改清单.md) | 主 agent 核对后的执行清单 | Composer |
| [材料/新文献对照_到页与高低级.md](材料/新文献对照_到页与高低级.md) | 2026-11-25 新搜文献（DestBench/DAC-Bench/GUI-Robust 等） | Composer + 检索 |
| [材料/基线试跑报告_demo5_bailian_1124.md](材料/基线试跑报告_demo5_bailian_1124.md) | demo5 基线 | Composer |
| [材料/试跑记录_bailian冒烟.md](材料/试跑记录_bailian冒烟.md) | 时间线 | Composer |
| [材料/轨迹摘要_raw.txt](材料/轨迹摘要_raw.txt) / [材料/kugou_g02_轨迹摘要.txt](材料/kugou_g02_轨迹摘要.txt) | 失败轨迹摘要 | 生产机抽取 |

工程原件仍在 UX-Agent：

`/Users/zhangyingying/UX-Agent/docs/材料/2026-11-24_1215高低级指令导航交付/`

生产机结果目录示例：

`/Users/user/uxagent/HarmonyArena-fdu_agent/results/nav-high-*-1125*/`

## 主失败原因（摘要）

- `tap_no_effect_loop` / 超时空转（高德、酷狗粤语）
- `env_precondition_missing`（钉钉登录墙 → 剔除）
- `obs_pipeline_down`（0 字节 png / screenCap 浮层；已改 snapshot_display + PNG 校验）
- deep 长链与任务过难 → 先移出短路径分母

## 不要把本目录当成

- 截断 oracle / 开合研究证据
- UX 检出率统计
- 端到端下单/付款成功率
