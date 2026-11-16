# SFT 数据质量报告 ④：file_action 行为的模型对比评测（4 模型 × 同一测试集）

- **日期**：2026-07-14
- **作者**：wangbo（分析由 Claude Code 执行）
- **目的**：用受控评测确认——报告①的 file_action 问题（Q2 不发 / Q3 发完就停）**到底是不是 0629 这批数据带来的**；对比蒸馏源 opus-4.7；并据此决定后续数据怎么修。
- **关联**：报告 ①(协议合规统计)、②(子任务丢失)、③(根源确认)。

---

## 0. 结论（TL;DR）

1. **"不出 file_action" 不是 0629 数据造成的——恰恰相反。** 没加 0629 的模型**几乎完全不发 file_action**（47 case 里 0 个真实的），因为训练里没见过。**是 0629 数据教会了模型发 file_action**，覆盖率/配对率**已达 opus 水平（写文件覆盖率甚至略高）**。
2. **opus 自己也远没守协议**：write_file 只有 30% 带 file_action、11% 悬空。协议要 ~100%，**谁都没做到**；蒸馏数据继承了 opus 的"低覆盖 + 收尾轮多余 file_action"。
3. **"出了 file_action 就停" 拆开：无一例"无故 bad-stop"**。csft 的悬空 = 收尾轮(和 opus 同源、没变多) + 网关畸形 tool-call(flash-lite 小模型能力问题，所有小模型变体都有)。
4. **后续怎么修**：脚本规范化 file_action（补齐到 ~100% 覆盖 + 删悬空）是**最高杠杆**、且能让模型**超过 opus**；补丢失子任务是**互补项**；网关畸形属模型/解码侧。

---

## 1. 评测设置

同一测试集 **47 个 case**（`prod_*`/`seq_*`），4 个模型跑同样输入（均无模板模式），产物同为 `main.json + subtask_*.json`。终态成功率都 ~46/47，**差异在行为、不在成败**。

| 简称 | 模型 | 是否含 0629 数据 | 目录 |
|---|---|---|---|
| 无0629 | `flash-lite-v36-fp8-step3k` | 否（基线） | `testset_v2_flashlite3k_notpl_20260701_002858` |
| opus-4.7 | `claude-opus-4-7` | —（蒸馏源） | `testset_v2_opus_4_7_notpl_20260702_140406` |
| **有0629** | `flash-lite-v36-fp8-step3k-csft` | **是** | `testset_v2_step3kcsft_notpl_20260713_095138` |
| 无0629+htmlDPO | `flash-lite-v36-fp8-step3k-dpo-v2` | 否（+html dpo） | `testset_v2_step3kdpov2_notpl_20260708_182527` |

> Q1（系统 prompt 残缺）是**训练数据**属性；推理时所有模型用同一份现行 prompt，故本报告只比 **Q2/Q3 的模型行为**。

## 2. 对比结果

| 指标 | 无0629 | opus-4.7 | **有0629(csft)** | 无0629+htmlDPO |
|---|---|---|---|---|
| assistant 消息 | 2905 | 1709 | 1712 | 3042 |
| **发出 file_action** | **2**(假) | 66 | **60** | **1**(假) |
| write_file 调用 | 211 | 132 | 76 | 208 |
| **write_file 带 file_action** | **0** | 39 | 29 | **0** |
| **→ 覆盖率(要 ~100%)** | **0%** | 30% | **38%** | **0%** |
| execute_code 带 file_action | 0/378 | 20/97 | 16/148 | 0/408 |
| **悬空 file_action** | 2 | 7 | 10 | 1 |
| → 占总 fa | — | 11% | 17% | — |
| ↳ 收尾轮(subtask_result) | 0 | 7 | 6 | 0 |
| ↳ 网关畸形(malformed) | 2 | **0** | 4 | 1 |
| ↳ **无故 bad-stop** | 0 | 0 | **0** | 0 |
| **配对率(接了 toolcall)** | — | 89% | **83%** | — |

已核验实例：
- **有0629 正确配对**（`prod_1289b84a/subtask_0`）：`"…我将生成 12 页…asset_map.json。\n\n<file_action><target>…asset_map.json</target><action>CREATE…"` + `tool_calls=['execute_code']` —— 规范 file_action 与写入**同条消息**。0629 SFT 教会的。
- **无0629 的"2 个 file_action"**均非真实：一个末尾其实是 `<ppt_task_finished>`（误报），一个是 **畸形 tool-call**（`</parameter></function></tool_call>` 泄漏进 content）——模型**想**写 info_pack.json 但 flash-lite 把 tool-call XML 写崩了。

## 3. 分症状解读

**Q2「不出 file_action」**：
- 无0629 / htmlDPO：**~0 真实 file_action**（训练没见过 → 完全无视协议）。这才是"不出 file_action"的极端形态。
- 有0629：把 write_file 覆盖率从 **0% → 38%**、配对率 83%，**≈ opus（写文件覆盖率 38% vs 30% 还略高）**。
- ⇒ **是 0629 数据让模型"开始发"file_action，不是让它"不发"。**

**Q3「发完就停」**：
- **无一例"无故 bad-stop"**（发个 file_action 平白停下）。
- 有0629 的 10 个悬空 = **6 收尾轮**（与 opus 的 7 个同源、是学来的冗余 pattern，**没变多**）+ **4 网关畸形**（小模型 tool-call 写崩，所有 flash-lite 变体都有：无0629=2、htmlDPO=1）。
- ⇒ 工程侧看到的"file_action 后没 toolcall"，要么是子任务合法收尾，要么是小模型畸形；**0629 数据没把收尾轮悬空变严重**。

## 4. 0629 数据到底做了什么

| | 效果 |
|---|---|
| ✅ 正面 | 让模型**从 0 学会发 file_action**，覆盖率/配对率达到（甚至略超）opus |
| ⚠️ 继承 | opus 的低覆盖（~30%，离协议 100% 远）+ 收尾轮多余 file_action（~11-17% 悬空） |
| ❌ 无关 | 网关畸形 tool-call 是 flash-lite 模型能力问题，非数据所致 |

## 5. 后续数据怎么修（基于证据）

**优先级 1 —— 脚本规范化 file_action（最高杠杆，可让模型超过 opus）**，作用于**全量**训练数据：
- **补**：每个 write_file（及可判定写文件的 execute_code/shell）若同条消息无 file_action，在 content 里、tool_call 之前插入规范 `<file_action>`（target 取自 tool 参数、action 判 CREATE/UPDATE）。→ 覆盖率 ~38% → ~100%，比 opus 更干净。
- **删**：所有悬空 file_action（该条无 tool_call），尤其收尾轮那种。→ 消除"file_action→停"的教材，同时避免强化网关畸形样本。
- ⚠️ `summary` **不得暴露具体文件名**（协议第 69 行）；按文件类型生成泛化描述。

**优先级 2 —— 补回丢失的子任务（互补）**：大纲子任务被整条删（报告②），补回恢复该阶段真实覆盖；与优先级 1 叠加：**先补轨迹、再统一规范化**。

**优先级 3 —— 网关畸形 tool-call**：数据端只能"不喂畸形样本"（删悬空-leak）；根治靠模型/解码侧。

**直接回答两个决定**：
- 补缺子任务：**要**，但是互补项；主力是脚本规范化（作用于全量，不止补回那些）。
- 脚本加 Q1-3：**要**，最高性价比——覆盖率推到 100%（超 opus）+ 删"发完就停"教材；Q1 残缺 prompt 一并脚本替换成规范版。

## 6. 复现

- 扫描脚本：`docs/ppt_sft_data_quality/scripts/scan_testset.py`（对每个 testset 的 main+subtask 统计 Q2/Q3）。
- 4 个测试集目录见 §1 表。
