# SFT 数据质量报告 ③：问题 1/2/3 是否在原始 result.jsonl（根源确认 + 悖论澄清）

- **日期**：2026-07-14
- **作者**：wangbo（分析由 Claude Code 执行）
- **要回答的问题**：报告①的三个问题（1 系统 prompt 预播报协议不全 / 2 write_file 未 100% 配 file_action / 3 file_action 未 100% 接 tool call）——**到底是原始轨迹 `result.jsonl` 里就有，还是导出/打包（格式化）时才产生的？** 以及一个矛盾点：既然 jsonl 只收「确定出了 HTML」的成功任务，那问题 3（file_action 后没 tool call ⇒ trace 断了）为什么没让 HTML 生成失败？
- **数据源**：`output/` 下 8 个 batch 的原始 `result.jsonl`（每个 case 一行 State-V3 富快照），抽样每批 ≤400 个 case、共 2754 个 case 直接扫描（不经导出脚本）。

---

## 0. 结论（TL;DR）

1. **问题 1/2/3 全部在原始 `result.jsonl` 里就存在**，不是导出/格式化制造的。导出脚本（`scripts/export_trace_to_openai.py`）是**忠实转码器**，逐字拷贝 content 与 tool_calls，无法凭空造出"悬空 file_action"或删掉系统 prompt 段落。
2. **矛盾点已澄清**：问题 3 的"没有 tool call"绝大多数（68%）是**子任务合法终态**（`<subtask_result>` 交回主 agent，本就不是 tool call；真正的写文件在更早一轮已完成），因此 pipeline 没断、HTML 照常生成。只有少数（21%）是**网关工具调用解析失败**才是真正的 trace 中断——但这些 case 仍多被标记为成功。
3. **更正报告①的一处归因**：早前把 `</invoke>` 泄漏那 156 条记成"导出截断 bug"是**错的**；它在原始 trace 里就已 `tool_calls=None`，属**生成期网关捕获失败**，导出只是忠实保留。
4. **一个需要注意的副作用**：`output/` 的 `result.jsonl` 在 0629 打包之后**被重跑覆盖过**（同一 case_id 的 deck id 已变），所以它反映的是"最新一次运行"，与 /mnt/d 里已打包的 0629 jsonl 不再逐字节对应；但问题的**类别**在两边都在。

---

## 1. 为什么可以断定"导出脚本是忠实的"（代码层证据）

`scripts/export_trace_to_openai.py`：

- `_build_main_trace`（:278）主轨迹取自 case 顶层 `messages`；`_build_subtask_traces`（:332）子任务取自 `state.runtime_control.subtasks[id].messages`；均逐条过 `_normalize_message`。
- `_normalize_message`（:149）：
  - system → `content` **逐字拷贝**（:162）。⇒ 不会注入/改写系统 prompt，问题 1 若在 packed 里，必在 raw 里。
  - assistant → `content` **逐字拷贝**（:170）；`tool_calls` **逐字拷贝**（:196-222，仅把 arguments 字符串反序列化成 dict），**只有当原始 tool_calls 为空时输出才没有 tool_calls**。⇒ 导出**无法**把"有 tool call 的写文件轮"变成"悬空 file_action"。问题 3 若在 packed 里，必在 raw 里。

唯一的边角：若原始某个 tool_call 是**非 dict**（畸形），`_normalize_message` 会跳过它（:200）。但实测网关泄漏 case 的原始 `tool_calls` 直接就是 `None`（`q_1051`），没有可跳过的对象——所以连这个边角也没触发。

## 2. 原始 result.jsonl 实测（抽样 2754 case，直接扫 raw）

| 问题 | 原始 raw 指标 | packed jsonl 对照（报告①） |
|---|---|---|
| **P2** write_file 无前置 file_action | **5830 / 7376 = 79.0%** | 65–89% ✓ 一致 |
| **P3** 悬空 file_action（有 fa、无 tool_calls） | **676**，其中 **100% 是所在轨迹末条** | 100% 末条 ✓ 一致 |
| P3 悬空里"同一轨迹更早已有真实写入" | **97.8%** | — |
| **P1** 主 agent 系统 prompt 变体 | canonical 2440 / **残缺 278** / bigEN 35 | 残缺变体存在 ✓ |
| P1 子任务系统 prompt 变体 | canonical 7145 / **残缺 1039** / bigEN 102 | ✓ |

三项都在 raw 里，且比例与 packed 对得上 ⇒ **问题 1/2/3 是生成/捕获阶段就有的，不是格式化产生的。**

## 3. 悖论澄清：问题 3 的三类子机制（原始 result.jsonl 重新分类）

676 条悬空 file_action，按原始 content 特征分类：

| 子类 | 数量 | 占比 | main/subtask | 所在 case 是否 terminal success | 是不是"真的断了" |
|---|---|---|---|---|---|
| **收尾轮**（含 `<subtask_result>`、格式正常） | 461 | **68.2%** | 0 / 461 | 461/461 (100%) | **否**——子任务合法终态 |
| **网关解析失败**（`</invoke>` 泄漏 / 标签开合不匹配） | 141 | 20.9% | 39 / 102 | 141/141 (100%) | **是**——工具调用真的没执行 |
| **纯停止**（格式正常、无 subtask_result） | 74 | 10.9% | 1 / 73 | 74/74 (100%) | 多数否（多为子任务末态） |

- **收尾轮（主因，模板批 100%）**：subtask 干完活（真实写文件在更早一轮、用真 tool call）后，末轮输出 `<subtask_result>` 交回主 agent，并**多余地**重报了一个 `<file_action>`。`<subtask_result>` 在运行时是"交回信号"、**本来就不是 tool call**，所以 OpenAI 格式里这条 assistant 消息**天然没有 tool_calls**。→ **pipeline 没断，HTML 照常生成**。已核验 `q_4136` subtask_0：turn[10] `execute_code` 真正写了 asset_map.json（exit_code 0、无 file_action），turn[12] 才补一个 file_action + subtask_result（无 tool call）；case 结果 `<ppt_task_finished><status>success</status>`。
- **网关解析失败（仅 0629 源批次）**：模型发完 file_action 开始发工具调用，但网关/litellm 解析失败，content 尾巴残留 `</invoke>`、`tool_calls=None`。**这才是你直觉里"trace 断了"的那类。** 已核验 `q_1051` main：`messages` 停在 msg18（file_action + `</invoke>`、无 tool call），主轨迹就此截断——但 case 仍标 success（写 task_pack 之前的产物已够 / 或被重跑覆盖，见 §4）。

**所以矛盾解开**：数据集层面没有"trace 断了却出了 HTML"的悖论——占主导的 68% 根本不是断（是子任务合法交回，真实写入更早已发生）；剩下真正断的 21% 是网关捕获失败，且这些 case 因为任务已推进够远/被判成功而仍进了成功集。

## 3bis. 问题 2/3 的精确刻画 + "trace 记反了吗"的证伪

针对两个常见疑问逐一给出原始 result.jsonl 层面的答案。

### 3bis.1 问题 2 的本质：是"该配没配"，不是"位置放反"

模型在**真正写文件的那一轮**（`write_file` 或 `execute_code`）大多不在该轮 content 里带 `file_action`（raw 79% 的 write_file 轮如此）。但模型**知道并经常用对**正确写法——raw 合规例 `q_3999` main msg[36]（同一条 assistant 消息）：

```
content:    <file_action><target>…/task_pack.json</target><action>CREATE</action>…</file_action>
tool_calls: ["write_file"]
```

`file_action` 在 content、`write_file` 在 tool_calls，**同一条消息**。**raw 里约 80% 的 file_action 都是这样正确地与 tool call 绑在同条消息**（file_action 总数 3355，其中 2679 条与 tool call 同条 = 79.9%；模板批更高，约 87%）。

所以问题 2 = 两件事，都不是"位置放反"：
- **绝大多数写文件根本没发 file_action**（遗漏）；
- 少数把 file_action **推迟到子任务收尾轮**再补发（即"在 toolcall 之后再给"）——但那是**另一条更晚的消息**，不是同一轮内顺序颠倒。

### 3bis.2 问题 3：悬空 file_action 是不是"记录时把它记到 toolcall 后面了"？——否

消息结构可一刀切排除该假设。`q_4136` 子任务 raw 原文 turn 10→11→12：

```
[10] assistant  content=(空,无 file_action)   tool_calls=["execute_code"]   ← 真正写 asset_map.json
[11] tool       execute_code 返回 (exit_code 0, stdout "OK …asset_map…")     ← 环境对 [10] 的响应
[12] assistant  content=<file_action>…asset_map.json…</file_action><subtask_result>…  tool_calls=(空)
```

三点证明这不是"记反/同轮内挪位"：

1. **悬空那条（turn 12）`tool_calls` 为空** —— 该条消息**根本没有 tool call**，谈不上 file_action 在其前或后，没有可颠倒的对象。
2. **turn 11 是一条 `tool` 消息**，是环境对 turn 10 的 `execute_code` 的返回。tool 消息只能出现在**两个独立 LLM 轮次之间**（模型发 tool_call → 环境执行返回 → 再喂回生成下一轮）。故 turn 10 与 turn 12 **必是两次独立的模型生成**，中间隔着一次真实工具执行。
3. 每条 assistant 消息各自带 `total_usage`（独立 token 计量）与 `thinking_blocks` —— 印证每条 = 一次独立 LLM 调用。turn 12 是模型**看到写文件结果之后**才另起一轮生成的。

⇒ 模型确实是"turn 10 先写文件（不带 file_action）→ turn 12 事后补一个 file_action + subtask_result（无 tool call）"。若真按协议做，turn 10 应长成 `q_3999` 那样（file_action 与 execute_code 同条）；实际 turn 10 的 content 是空的。**真实模型行为，非记录顺序问题。**

### 3bis.3 关于"同一轮内 content 与 tool_call 有没有先后"

- **数据层（OpenAI json）**：一条 assistant 消息 = `content`(str) + `tool_calls`(array) 两个独立字段，JSON **不编码**二者先后。此信息本就不在数据里——但只对"同条既有 content 又有 tool_call"的合规轮次才有意义；悬空轮次无 tool_call，顺序无从谈起。
- **训练渲染层（chat template）**：模型训练时看到的先后由**训练框架的 chat 模板**决定（标准模板 content 在前、tool_calls 在后 → file_action 渲染在 tool call 之前，正确）。此项**不在本数据内**，属训练脚本侧，建议单独确认模板；但不改变问题 2/3 的存在性。

### 3bis.4 统一结论

模型**不是**不懂 file_action 放哪（80% 都正确与 tool call 同条绑定）。真正的病是同一倾向的两面：把 file_action 当**可选的事后小结**而非**强制的写前播报** → (2) 多数写文件懒得发；(3) 偶尔在子任务收尾轮补一个、而那条没有 tool call。

## 4. 一个必须知道的副作用：output/ 已被重跑覆盖

同一 `case_id`（如 `q_0005_f4459146`）：0629 打包时那版 deck 是 `pptid_f32ebfd3…`、含 `</invoke>` 泄漏的悬空 file_action；而**现在 `output/` 里的 `result.jsonl` deck 是 `pptid_beba2ba1…`、4 个子任务全部干净收尾**。说明批量自愈 `--resume`（见 [[project_batch_resilience_model]]）重跑并**覆盖**了 result.jsonl。

含义：
- `output/result.jsonl` = 最新一次运行，**不再是 /mnt/d 那份已打包 jsonl 的逐字节源头**；要复核已交付 jsonl 的具体某条，应以 /mnt/d 的 jsonl 为准。
- 但问题**类别**在最新 raw 里同样成立（§2/§3），结论不受影响。
- 顺带：某些重跑覆盖可能让单个 `result.jsonl` 内部不自洽（如主轨迹截断于早期失败轮、但 `result.success=True` 来自更早一次完成）——这类不一致值得单独排查。

## 5. 四个问题的"源头层"归属汇总

| # | 问题 | 源头层 | 是不是导出/格式化的锅 |
|---|---|---|---|
| 1 | 系统 prompt 预播报协议不全（残缺变体） | **运行时 prompt 组装**（口径不统一） | 否（导出逐字拷贝） |
| 2 | write_file 未 100% 配 file_action（raw 79%） | **生成模型行为**（把 file_action 当事后小结，而非事前播报） | 否 |
| 3 | file_action 未 100% 接 tool call（raw 676） | 68% **模型收尾轮行为** + 21% **网关工具调用解析失败** + 11% 纯停止 | 否（三类都在 raw） |
| 4 | 大纲子任务丢失（28%） | **运行时/持久化**：subtask_counter resume 复位致 subtask_id 撞车覆盖（报告②） | 否（导出忠实枚举被覆盖后的 dict） |

**四个问题没有一个是 OpenAI 格式导出脚本造成的。** 修复应对准：①运行时 prompt 组装口径统一（P1）；②模型对齐 / 数据清洗（P2、P3 收尾轮）；③网关工具调用解析健壮性（P3 网关类）；④运行时计数器恢复 + 撞车防御（P4，报告②§7）。

## 6. 复现

- 直接扫原始 raw：`scan_raw.py`（P1/P2/P3 raw 指标 + 悖论统计）、`scan_raw2.py`（悬空 file_action 三类分类）。
- 忠实性代码位点：`scripts/export_trace_to_openai.py:149-241,278,332`。
- 关键样例：`output/batch_remaining_template_20260703_20260710_093907/q_4136_d2db3589`（收尾轮，真实写在 turn[10]）；`output/batch_day_20260627_110751_p0/q_1051_663c8553`（网关解析失败，main 截断于 msg18，raw `tool_calls=None`）；`output/batch_day_20260627_p0/q_0005_f4459146`（重跑覆盖，deck 已变）。
