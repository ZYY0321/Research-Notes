# SFT 数据质量报告 ①：File Action 预播报协议合规性

- **日期**：2026-07-14
- **作者**：wangbo（分析由 Claude Code 执行）
- **触发问题**：用这几批数据训出的模型出现两种坏行为——(A) 输出 `<file_action>` 之后就停、不再发 tool call；(B) 写文件时干脆不输出 `<file_action>`。
- **协议出处**：`agents/agentv3/system_prompt_parts/zh/09_output_principles.md:50-84`（「文件操作预播报协议 / File Action Protocol」）。
- **关联报告**：本报告统计的是**已导出轨迹**内部的协议合规性；另有一类"整条子任务被丢弃"的数据构造缺陷见 `02_subtask_drop_counter_bug.md`，两者叠加共同导致上述症状。

> ⚠️ 重要前提（读本报告前必看）：本报告的分子/分母都建立在**已经导出成 OpenAI 格式的轨迹**上。而报告 ② 证明，约 28% 的子任务轨迹（其中 74% 是 file_action 最密集的"大纲/风格"阶段）在导出前就被运行时 bug 丢掉了。因此本报告看到的 file_action 稀缺/不合规，一部分是"最好的正例被提前删除"造成的幸存者偏差，不能全部归因于生成模型不守协议。

---

## 1. 协议不变量

协议要求：当模型决定调用任何**创建/修改/删除文件**的工具时，必须在该 tool call **之前、同一条 assistant 消息内**输出与"紧随其后的那一个 tool call"严格对应的 `<file_action>` 摘要块（`<target>/<action>/<summary>`）。

由于 OpenAI 消息格式里，`<file_action>` 落在 `assistant.content`、tool call 落在同一条 `assistant.tool_calls`，两个症状可被精确度量为：

| 症状 | 对应的数据缺陷 |
|---|---|
| A：出 file_action 就停 | `content` 含 `<file_action>` 但**同条消息 `tool_calls` 为空** |
| B：不出 file_action | 调用了**确定写文件的工具**（`write_file`）但 `content` **不含** `<file_action>` |

## 2. 扫描范围

| 批次(简称) | 文件 | 轨迹数(main/subtask) |
|---|---|---|
| 0629 query | `20260629-xhx-agent轨迹数据/.../ppt_agentic_sft_query_20260629.jsonl` | 7887 (1713/6174) |
| 0629 files | `.../ppt_agentic_sft_with_files_20260629.jsonl` | 1807 (426/1381) |
| 0709 tmpl | `20260709-...-template/.../ppt_agentic_sft_template_query_20260709.jsonl` | 2703 (827/1876) |
| 0710 tmpl2 | `20260709-...-template2/.../ppt_agentic_sft_template_query_20260710.jsonl` | 2783 (843/1940) |
| 0713 query | `20260713-...//ppt_agentic_sft_query_20260713.jsonl` | 1094 (256/838) |

根目录：`/mnt/d/Workspace/PPTGen/Data/`。0 条 JSON 解析失败。方法：逐条 `json.loads`，只扫描 `assistant.content`（不看 `reasoning_content`）里的 `<file_action>` 与同条 `tool_calls`。

---

## 3. Q1 — 系统 prompt 里是否都有预播报协议？

**结论：无一条完全缺失 `<file_action>` 概念（标签定义 100% 在）；但 0629 query 混入了多种系统 prompt 变体，其中 42% 用的是"残缺版"——只在输出通道节提到 `<file_action>` 标签，丢掉了整段"核心规则 + 输出格式 + '必须紧接 tool call'时序"。**

| 批次 | 规范版<br>(含「文件操作预播报协议」完整节) | 残缺版(v2)<br>(仅提标签、无协议节) | 超长英文版(v3) | 完全无协议 |
|---|---|---|---|---|
| **0629 query** | 4473 (**56.7%**) | **3329 (42.2%)** | 85 (1.1%) | 0 |
| 0629 files | 1807 (100%) | 0 | 0 | 0 |
| 0709 tmpl | 2679 (99.1%) | 0 | 24 (0.9%) | 0 |
| 0710 tmpl2 | 2708 (97.3%) | 0 | 75 (2.7%) | 0 |
| 0713 query | 1072 (98.0%) | 0 | 22 (2.0%) | 0 |

- 变体判定：`cn` = 是否含中文标题「文件操作预播报协议」；`en` = 是否含英文「File Action Protocol」；`tag` = 是否含 `<file_action>`。规范版 = (cn,en,tag)=(T,T,T)；残缺版 = (F,F,T)；超长英文版 = (F,T,T)。
- 残缺版与规范版按 case_id **交错**出现（非连续段），说明是两套系统 prompt 构建口径被混进同一批；残缺版长度反而更大（10.8k–36k vs 规范版 ~12k–17k）。
- **影响主要集中在 0629 query（最大的一批，42% 非规范）**；其余 4 批 97–100% 规范。

---

## 4. Q2 — 写文件是否都带对应 file_action？（症状 B）

`write_file` 一定写文件，按协议应 100% 有前置 `file_action`，实测**绝大多数没有**：

| 批次 | write_file 调用 | 缺 file_action | 缺失率 |
|---|---|---|---|
| **0629 query** | 4966 | 4403 | **88.7%** |
| 0629 files | 998 | 651 | 65.2% |
| 0709 tmpl | 1883 | 1347 | 71.5% |
| 0710 tmpl2 | 1991 | 1513 | 76.0% |
| 0713 query | 704 | 502 | 71.3% |

- 已核验实例 `q_0003`（main，0629 query）：连续三条 `write_file`（research_*.md / task_pack.json / info_pack）都只带一句进度文本（如"子任务已采集到核心数据。我先把调研资料落盘…"）、**无 file_action**，且进度文本未包 `<response>`（第二处违约）。
- 说明：`execute_code` / `execute_shell_command` 的 file_action 覆盖率低（3.8% / 0.1%）是**正常**的——它们大量用于读文件/mkdir/ls，不都是写。因此只用 `write_file`（语义无歧义）作为症状 B 的判据。

---

## 5. Q3 — file_action 之后是否都接 tool call？（症状 A）

**结论：每批都有 `<file_action>` 出现但同条消息无 tool call 的"悬空"消息，且 100% 是该轨迹的最后一条（绝大多数是 subtask 轨迹）。**

| 批次 | 悬空 file_action | 占全部 fa 消息 | 是否轨迹末条 |
|---|---|---|---|
| **0629 query** | 393 | 26.3% | 100% |
| 0629 files | 135 | 20.0% | 100% |
| 0709 tmpl | 143 | 13.2% | 100% |
| 0710 tmpl2 | 128 | 12.5% | 100% |
| 0713 query | 75 | 20.8% | 100% |

**两种机制（分类统计）：**

| 批次 | 导出截断(`</invoke>` 泄漏、标签开合不匹配) | 收尾轮(file_action+`<subtask_result>` 同条终止) | 纯停止(格式正常、无后续) |
|---|---|---|---|
| 0629 query | 156 | 184 | 54 |
| 0629 files | 0 | 110 | 24 |
| 0709 tmpl | 0 | 143 | 0 |
| 0710 tmpl2 | 0 | 128 | 0 |
| 0713 query | 0 | 75 | 0 |

- **收尾轮机制（各批主因，模板批 100%）**：subtask 收尾时把 `<file_action>`（重报一个上一轮已写的文件，如 asset_map.json）+ `<subtask_result>` 塞进同一条**终止**消息，无 tool call。→ 训练信号 = `file_action → subtask_result → EOS`。已核验 `q_0009`（asset_map.json 在前一轮由 execute_code 写好，末轮又用 file_action 重报）。
  - 归属：**这是生成模型自身的行为**，导出忠实保留（已核验 `q_4136` 的 raw `result.jsonl` 与导出 `subtask_0.json` 末轮**逐字节一致**）。且技能 SOP 本身禁止收尾轮再输出 file_action（`skills/ppt-no-template-mode/SKILL.md:132`），数据违反了自己的 SOP。
- **网关工具调用解析失败（仅 0629 query/files 源批次，模板批 0）**：模型输出 file_action 后开始发工具调用，但网关/litellm 解析该工具调用失败，`content` 尾巴残留 `</invoke>`、file_action 开合标签不匹配，`tool_calls` 为空。**这一子类在原始 `result.jsonl` 里就已如此**（已核验 `q_1051` main msg18：raw `tool_calls=None`），**不是导出脚本的问题**——导出忠实拷贝 content 与 tool_calls（`scripts/export_trace_to_openai.py:_normalize_message`，见报告 ③）。⚠️ 更正：早前把它记成"导出截断 bug"是错的，实为生成期网关捕获失败。这也是三类里**唯一真正"trace 断了"**的子类（对应用户的直觉），但只占少数、且发生的 case 仍多标记为 terminal success。

> 说明：本节表格的机制数字来自 packed jsonl 的初版扫描；在原始 `result.jsonl` 上重新分类（见报告 ③）的比例为：收尾轮 68% / 网关解析失败 21% / 纯停止 11%。

---

## 6. file_action 的整体稀缺度（模型为何倾向少发）

| 批次 | assistant 消息 | 含 file_action 的消息 | 占比 |
|---|---|---|---|
| 0629 query | 100581 | 1493 | 1.5% |
| 0629 files | 23400 | 676 | 2.9% |
| 0709 tmpl | 28885 | 1086 | 3.8% |
| 0710 tmpl2 | 30290 | 1028 | 3.4% |
| 0713 query | 11178 | 361 | 3.2% |

file_action 只占 assistant 消息 1.5%–3.8%，且其中 13%–26% 是死胡同（悬空、末条）。模型同时学到两件互相矛盾的事：**file_action 大多数时候可省（→ 不发），且它常出现在"下一步就停"的位置（→ 发完就停）**——正好复现两种坏行为。

---

## 7. 结论与去向

1. **症状 B（不发 file_action）**：主要是幸存轨迹里 `write_file` 65–89% 无前置 file_action——部分是模型行为，部分是"file_action 密集的大纲子任务被整条丢弃"（见报告 ②）造成的正例缺失。
2. **症状 A（发完就停）**：悬空 file_action 分三类——收尾轮(68%)是**模型行为**、网关解析失败(21%)是**生成期网关捕获失败**、纯停止(11%)。**三类都在原始 `result.jsonl` 里，不是导出脚本造的**（见报告 ③）。
3. **Q1**：0629 query 42% 用了残缺系统 prompt，监督口径不一致；**残缺 prompt 也在原始 trace 里**（运行时 prompt 组装产生，导出逐字拷贝，非导出注入）。

⚠️ 重要更正（见报告 ③）：**导出/格式化脚本本身是忠实的，不是 1/2/3 的元凶**。问题 1（残缺 prompt）源于运行时 prompt 组装；问题 2/3 源于生成模型行为 + 网关捕获失败——都在原始 `result.jsonl` 里就存在。修复应对准上游（prompt 组装口径、模型对齐/清洗、网关工具调用解析），而非导出脚本。清洗规则（剥离无 tool call 的 file_action 等）见报告 ② 第 7 节。

## 8. 复现

扫描脚本（session scratchpad，逻辑见本报告第 1 节判据）：
- `scan_file_action.py`：Q1/Q2/Q3 主计数。
- `scan2.py`：悬空 file_action 的机制分类。
- `scan3.py`：系统 prompt 变体分桶。

如需固化到仓库，可移入 `docs/ppt_sft_data_quality/scripts/`。
