类型：材料 ｜ 归属：2026-11-24_1215高低级指令导航交付 ｜ 状态：维护中（基线，非验收终稿）

# 12-15 导航+检测：demo5 百炼直接跑基线报告

**挂回**：横向 T+6（12-15）GUI Agent 寻路 + 到达后检测。不是截断自测报告那套。

## 结论（先看这三句）

1. **能跑通**：高级/低级指令 → agent 到页 → 切屏检测，链路在 Mate X5 上已打通。
2. **不能说没 bug**：样本量小（5 App × H/L）、有一次 10 分钟超时（重跑才过）、到达判定目前靠模型自报+截图目录，**未做人审到达率**。
3. **应该再测**：至少扩到更深任务 / 更多 App（手里有 102 条 commercial-bifold-run），并补人工抽检。

## 环境

| 项 | 值 |
|---|---|
| 设备 | Mate X5 `22M0223928009654`（外屏 FOLDED 跑轨迹，检测切 single+dual） |
| 机位 | 生产机 `10.202.10.92`（11-24 夜跑）；11-25 下午手机改插本机，本机 `hdc` 可见 |
| 模型 | TokenHub 百炼 `qwen3.8-max-0902/bailian_L/bailian`（非官方 DashScope） |
| Runtime | `~/uxagent/run_demo_bailian.sh` + `opencode.bailian.json`；`HARMONY_FINAL_UX_DETECT=1` |
| 已知补丁 | `final-ux-detect.ts`：`reasoning_effort=none` + 120s 超时（否则 Qwen content 空会卡死） |

## 数字

| 批次 | 条数 | 通过 | 说明 |
|---|---|---|---|
| 冒烟 B站 H+L | 2 | 2/2 | ~73–85s |
| demo5-v2 首跑 | 10 | **9/10** | 小红书-H 超时失败 |
| 小红书-H 重跑 | 1 | **1/1** | 73.5s，含 final_ux |
| **合计（含重跑）** | — | **实质 10/10 任务可过** | 首跑不稳定 1 条 |

任务覆盖 App：哔哩哔哩、番茄、腾讯视频、微博、小红书（各 H+L）。均为 easy 短路径。

平均：首跑约 141s/条；动作步约 2–5。

## 检测侧

通过任务均写出 `artifacts/final_ux_detect.json`（single + dual）。  
检测用同一百炼 VL，**不是**截断 v1.3.0 真工具；结果未对照 TOP7 真值，只证明「接口能调通」。

## 速度（相对任务书；去掉模型后仍不达标）

任务书：动作响应平均 ≤3s、单步最大 ≤5s；检测端到端（到页后）≤10s。11-23 会：V1 可不卡速度，速度在 7+12。

demo5 日志里的 `postActionWaitMs`（动作后等到 UI 稳定，**不含** LLM）：

| 指标 | 实测 | 要求 |
|---|---|---|
| 样本 | 33 次动作 | — |
| 平均 | **~6.0s** | ≤3s |
| 中位 | ~5.7s | — |
| 最大 | **9.3s** | ≤5s |
| >3s / >5s | **33/33** / **25/33** | — |

整条任务墙钟（含模型）平均 ~86s，不能用来对 3s/5s。结论：**仅设备侧 settle 就已经超标**；现网为等页面稳定故意等到 5～9 秒。

## 已暴露问题（所以不能写「无 bug」）

| 问题 | 证据 | 状态 |
|---|---|---|
| final UX + Qwen `reasoning_effort=medium` 卡死 | 冒烟首轮 | 已改 none |
| 小红书高级偶发跑满 10 分钟超时 | demo5 首跑 11 步未报到达；重跑 2 步过 | **偶发不稳定仍在** |
| 到达成功以 runner `ok`/模型自报为准 | 未做人审截图抽检表 | 缺口 |
| 接口形态未定 | 周会待确认 | 缺口 |
| 任务书 95%/80% 到达率 | 仅 5 对 short case | **远不够统计** |

## 建议下一轮（本机已连设备，可接着跑）

1. 人工抽检 demo5 的终态截图（至少失败过的小红书-H + 随机 3 对 H/L）。
2. 扩测：`tasks-commercial-bifold-run.json` 抽 10～20 对，或 deep-high 若干条。
3. 同一任务连跑 3 次看超时复现率（专盯小红书类弹窗多的 App）。
4. 出接口 demo（CLI/HTTP）前，把「入参=高级或低级、出参=到达+检测 JSON」样例固定下来。

## 证据路径（生产机）

- `/Users/user/uxagent/HarmonyArena-fdu_agent/results/demo5-bailian-1124-2026-11-24T15-02-42-098Z/`
- `/Users/user/uxagent/HarmonyArena-fdu_agent/results/retry-xhs-H-bailian-1124-2026-11-24T15-33-09-529Z/`
- `/Users/user/uxagent/HarmonyArena-fdu_agent/results/smoke-bilibili-bailian-1124b-2026-11-24T14-59-26-223Z/`
