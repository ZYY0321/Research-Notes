# SFT 数据质量报告 ②：子任务轨迹被整条丢弃（subtask_id 计数器复位 bug）

- **日期**：2026-07-14
- **作者**：wangbo（分析由 Claude Code 执行）
- **一句话结论**：并非（只）是生成模型不守协议——在把整段运行轨迹导出成分 agent 的 OpenAI 训练样本之前，**一个运行时 bug 已经把约 28% 的子任务轨迹覆盖丢失了，其中 74% 恰好是 file_action 最密集的"大纲/风格"阶段**。导出脚本是"忠实的受害者"，不是元凶。
- **关联报告**：`01_file_action_protocol_compliance.md`。

---

## 1. 起点：一个对不上的 case

`output/batch_remaining_template_20260703_20260710_093907/q_4136_d2db3589/`（对应 0713 jsonl）：

- `main.json` 里主 agent 发起了 **4 个** `create_subtask`（4 个 tool call id 各不相同）：
  1. `生成设计风格与页面大纲`（**大纲/风格**，parent `…ru7`）
  2. `生成资产规划`（parent `…FYy`）
  3. `批量生成所有页面HTML`（parent `…TuZ`）
  4. `批量复核与按需重写页面`（parent `…oaQU`）
- 但导出目录里只有 **3 个** 子任务文件：`subtask_0.json`(资产规划) / `subtask_1.json`(HTML) / `subtask_2.json`(复核)。
- **丢的正是第一个"大纲/风格"子任务**；而且编号被"压缩"了——`subtask_0` 不是大纲，而是资产规划。

## 2. 直接原因：subtask_id 撞车（覆盖）

在原始 `result.jsonl`（单行 State-V3 富快照）里，`state.runtime_control` 有：

- `subtask_counter = 4`（计数器认为创建了 4 个），但
- `runtime_control.subtasks` 这个 **dict 只有 3 个 key**（subtask_0/1/2），且 `subtask_0` 的内容是**资产规划**。
- `message_records` 里有 **4 条 `subtask_summary`**，其 subtask_id 依次为 **`subtask_0`(大纲) → `subtask_0`(资产) → `subtask_1`(HTML) → `subtask_2`(复核)`**。

**两个不同的子任务（大纲、资产）都拿到了 `subtask_0`。** 由于 `runtime_control.subtasks` 是以 subtask_id 为 key 的 dict，第二个（资产）**覆盖**了第一个（大纲）。导出脚本枚举这个 dict，只能看到 3 条，大纲轨迹已不在其中。

## 3. 根因：顶层计数器在 resume 时未从 runtime_control 恢复

id 分配在 `agents/agentv3/agent_v3.py:1627-1628`：

```python
delegate_id = f"{delegate_prefix}_{state[counter_key]}"   # 用【顶层】 state["subtask_counter"]
state[counter_key] += 1
```

而**持久化的 State-V3 只把计数器存在 `runtime_control.subtask_counter`**（`src/conversation_state_v3.py:1706-1708`、`:1731` 写入 dict），**顶层 `state["subtask_counter"]` 不进持久化快照**（`result.jsonl` 的 `state` 顶层键里没有它）。

运行 setup 时又只是 `setdefault`（`agents/agentv3/agent_v3.py:974`）：

```python
state.setdefault("subtask_counter", 0)   # resume 时顶层缺失 → 复位为 0，而不是从 runtime_control 恢复
```

于是**任何一次中途 resume / 状态重建**都会：**恢复了 `runtime_control.subtasks`（大纲还在 subtask_0），却把顶层计数器复位成 0** → 下一个子任务再拿 `subtask_0` → 覆盖大纲。

**佐证：正确的做法在别处已经存在。** `backend/replay_engine.py:435,439` 明确从 runtime_control 把计数器提回顶层：

```python
"subtask_counter":  (pruned_shared_state.get("runtime_control") or {}).get("subtask_counter", 0),
"reflection_counter": (pruned_shared_state.get("runtime_control") or {}).get("reflection_counter", 0),
```

**replay 路径修了，批量 agent-run 的 setup 路径漏了。** 这就是单一真相源没有对齐导致的复位。

### 事件重演（0,0,1,2 + counter=4）

1. 首次运行：创建大纲 → `subtask_0`，顶层 counter 0→1。checkpoint 持久化 `runtime_control.subtasks={subtask_0:大纲}`、`runtime_control.subtask_counter`；顶层 counter 不入快照。
2. resume：工作态重建。`runtime_control` 恢复（大纲仍在 subtask_0）；顶层 `subtask_counter` 缺失 → setdefault 0。
3. 主 agent 继续，创建资产 → `subtask_{0}` = `subtask_0` → **覆盖大纲**。（去重守卫 `agent_v3.py:1621` 按 parent_tool_call_id 去重，只能阻止"重复创建大纲"，阻止不了"新子任务撞进大纲的槽位"。）
4. 继续：HTML→subtask_1，复核→subtask_2；计数器经多次 resume/`max()` 逻辑最终停在 4。

---

## 4. 影响范围（全量扫描 output/ 8 个批次、7149 个 case 目录）

比较每个 case 的 `main.json` 里 `create_subtask` 数量 vs 目录内 `subtask_*.json` 文件数：

| 批次 | case 目录 | 有 main.json | 缺子任务的 case | 创建的子任务 | 导出的子任务文件 | 被丢弃 |
|---|---|---|---|---|---|---|
| batch_day_20260627_110751_p0 | 345 | 330 | 220 | 1168 | 841 | 343 |
| batch_day_20260627_p0 | 996 | 489 | 435 | 2380 | 1687 | 742 |
| batch_day_20260628_005500_v1 | 508 | 159 | 158 | 830 | 601 | 236 |
| batch_day_20260628_054900 | 2000 | 1141 | 1015 | 5524 | 4023 | 1516 |
| batch_filebased_20260628_v2 | 500 | 468 | 299 | 1865 | 1475 | 390 |
| batch_remaining_template_..._20260708_160337 | 1000 | 828 | 723 | 2682 | 1880 | 802 |
| batch_remaining_template_..._20260709_213556 | 1000 | 849 | 759 | 2819 | 1952 | 868 |
| batch_remaining_template_..._20260710_093907 | 800 | 267 | 236 | 1161 | 877 | 285 |
| **合计** | **7149** | **4531** | **3845** | **18429** | **13336** | **5182** |

- **缺子任务的 case 占比 = 3845 / 4531 = 84.9%**（有 main.json 的 case 中，近 85% 至少丢了一个子任务）。
- **被丢弃的子任务占比 = 5182 / 18429 = 28.1%**。
- 批次→jsonl 大致对应：`batch_day_2026062*` → 0629 query；`batch_filebased_20260628_v2` → 0629 files；三个 `batch_remaining_template_20260703_*` → 0709/0710/0713。**5 个交付 jsonl 全部受影响。**
- 旁注：`case 目录` 远多于 `有 main.json`（7149 vs 4531，约 37% 无 main.json）。这是另一个独立缺口（疑似失败/未导出 case），本报告未展开，建议单独核查。

### 丢弃的是哪一阶段 / 哪个位置

| 被丢子任务的阶段 | 数量 |
|---|---|
| **大纲/风格 (outline/style)** | **3861** |
| 研究/资料收集尾巴 (other/research) | 585 |
| 资产规划 (asset-planning) | 382 |
| 研究 (research) | 349 |
| HTML 生成 | 5 |

| 被丢子任务在创建序列里的位置(0-based) | 数量 |
|---|---|
| **位置 0（第一个）** | **3845 (74.2%)** |
| 位置 1（第二个） | 1211 |
| 位置 2 | 108 |
| 位置 3 | 16 |
| 位置 4 / 7 | 各 1 |

- **每一个"缺子任务"的 case 都缺了它的第一个子任务**（缺失 case 数 3845 == 位置0 丢弃数 3845）。这正是"计数器复位到 0、从 subtask_0 起逐个覆盖"的确凿指纹。
- 位置分布的衰减（3845→1211→108→16）对应"在第 N 个子任务边界发生第 N 次 resume"的概率递减。
- PPT 流水线里第一个子任务几乎总是**大纲/风格**——也就是 file_action 最密集、最规范的阶段。**这批数据恰好把最好的 file_action 正例系统性删掉了。**

---

## 5. 这是不是"数据构造/格式化"的问题？

分层看：

- **导出成 OpenAI 格式那一步（`export_trace_to_openai.py`）本身是忠实的**：它枚举 `runtime_control.subtasks` 并逐个 dump；`q_4136` 的幸存 `subtask_0.json` 与 raw `runtime_control.subtasks.subtask_0` 逐字节一致。它没有"少拆"，是**上游的运行时状态里本来就只剩 3 个**。
- **真正的缺陷在运行时 + 持久化**：顶层 `subtask_counter` 与持久化的 `runtime_control.subtask_counter` 是两个真相源，resume 时未对齐 → id 撞车 → dict 覆盖。属于 State-V3 迁移期"顶层 agent 记账字段 vs runtime_control 字段"未收敛的典型问题。
- 所以用户直觉是对的：**"目标模型没遵循"这个结论对被丢弃的阶段不成立——证据（大纲子任务轨迹）在导出前就被删了。** 对幸存阶段，模型的 file_action 行为（报告①的症状 A/B）确实存在且被忠实导出，是另一回事。

---

## 6. 能不能修复 / 可恢复性

**已交付数据里被丢弃的子任务轨迹：不可从现有产物无损恢复。**

- 逐轮完整子任务轨迹**只**存在于 `runtime_control.subtasks[id].messages`；被覆盖的大纲 messages 已不在 `result.jsonl` 内。
- `message_records` 每个子任务只留**摘要级**记录（`subtask_summary` 的 `result_preview`，截断到 240 字）+ 主 agent 侧的 create_subtask tool_result（含大纲的 `<findings>` 汇总，约数 KB）——有"结果"，没有"逐轮过程"。
- 批量模式下 `checkpoint_runtime_state` / `record_runtime_event` 在 `user_id is None` 时直接 return（`backend/replay_runtime.py:299,330`），**不落独立事件日志**；沙盒工作区只有产物文件（outline.json/style_spec.json），没有轨迹。

⇒ **要拿回这些子任务轨迹，只能在修好 bug 后重跑受影响的 case（或至少重跑其大纲子任务）。**

---

## 7. 修复建议

### 7.1 根因修复（运行时，`agents/agentv3/agent_v3.py` run setup ~974）—— ✅ 已应用并验证（2026-07-14）

**状态：已应用。** 把顶层计数器的 `setdefault(0)` 改为**从 runtime_control 恢复**（对齐 `replay_engine.py:435` 已有的正确写法），并对现存 subtask id 取 max 兜底。

**端到端验证**（`conf_v3_zh_claude_c_chain.yaml` 重跑 2 个原受损模板 case）：
- `q_0523_03f5dc26`（原丢大纲）：post-fix `subtask_counter=4` 且 dict 恰 4 条；`subtask_0=生成模板编排与大纲`(大纲,36 轮完整轨迹)、summary id `[0,1,2,3]` **无重复**；且该 case 的 message_records 里 **确有 `resume_answer`**（走了 ask_user→resume 这条正是撞车触发路径）→ 修复后不再复位/撞车。
- `q_0526_19d307c0`：`created=3 / files=3 / dropped=0`，`subtask_0=模板编排与大纲生成` 保留。
- 单元级 sanity：resume-after-1-subtask → counter 恢复为 1（下一个 id=subtask_1，不撞 subtask_0）；fresh run → 0；stale counter + 现存 id → 取 max 兜底。

实际落地代码（与下方等价）：

```python
rc = state.get("runtime_control") or {}
existing = rc.get("subtasks") or {}
def _next(prefix, key):
    base = state.get(key)
    if base is None:
        base = rc.get(key, 0)
    used = [int(k.rsplit("_",1)[-1]) for k in existing
            if k.startswith(prefix+"_") and k.rsplit("_",1)[-1].isdigit()]
    return max([base] + [u+1 for u in used] + [0])
state["subtask_counter"]   = _next("subtask",   "subtask_counter")
state["reflection_counter"] = _next("reflection","reflection_counter")
```

### 7.2 防御性加固（`src/conversation_state_v3.py:create_delegate_entry`）
`runtime.subtasks[resolved_delegate_id] = entry` 前，若 key 已存在则**顺延到未占用的 id**（绝不覆盖），并 warn 记录。让"计数器万一复位"也不至于丢数据。

### 7.3 导出侧护栏（`scripts/export_trace_to_openai.py` / `pack_sft_jsonl.py`）
导出时校验 `runtime_control.subtask_counter`（及 `message_records` 里 subtask_summary 的条数/去重后的 id 数）与实际导出的 subtask 文件数是否一致；不一致则该 case **标记并从训练集剔除**（而不是静默少拆），并输出一份"受损 case 清单"。

### 7.4 数据侧补救
- 用护栏（7.3）产出全量"受损 case 清单"（预计 ≈ 3845 case）。
- 对需要保留的 case：修好 7.1 后**重跑**；无法重跑的：至少从训练集中剔除，避免"缺大纲阶段"的残缺轨迹继续污染。

> 说明：7.1/7.2 触及 runtime（`agents/agentv3`、`src/`），改动需评审后再落；7.3/7.4 属数据构造管线。

---

## 8. 隐含后果（为什么必须重视）

1. **训练集缺 28% 子任务、且偏向删掉 file_action 最规范的大纲阶段** → 直接放大报告①的两个症状：正例（file_action→tool call→写文件）被系统性移除。
2. **主 agent 轨迹里仍保留了对这些"幽灵子任务"的 create_subtask + tool_result** → 训练主 agent 时，它学到"我发起了一个子任务并拿到了结果"，但对应的子任务执行样本不存在；主/子轨迹在数据集层面不自洽。
3. **幸存子任务被重编号**（大纲的 subtask_0 被资产占用）→ 任何按 subtask_id 对齐 main 与 subtask 的下游逻辑都会错配。
4. **样本级偏置**：位置0 永远最先被覆盖，导致"流水线第一步"这一类轨迹在训练集中被结构性低估。
5. 反射（reflection）子任务用同一套计数器机制，理论上有同样风险（本批 reflection_counter 多为 0，实际命中少，但需同修）。

---

## 9. 复现

- 单 case 解剖：`output/batch_remaining_template_20260703_20260710_093907/q_4136_d2db3589/`（main 4 个 create_subtask、只有 3 个 subtask 文件、`runtime_control.subtasks` 3 条且 subtask_0=资产、summary id 序列 0,0,1,2、counter=4）。
- 全量扫描脚本（session scratchpad）：`scan_missing.py`（对比每 case 的 create_subtask 数 vs subtask 文件数，输出丢弃阶段/位置分布）。
- 关键代码位点：`agents/agentv3/agent_v3.py:1627-1628,974,1621`；`src/conversation_state_v3.py:1706-1708,1731`；`backend/replay_engine.py:435,439`；`backend/replay_runtime.py:299,330`。

如需，可把 `scan_missing.py` 固化进 `docs/ppt_sft_data_quality/scripts/` 并加一个"受损 case 清单"导出模式。
