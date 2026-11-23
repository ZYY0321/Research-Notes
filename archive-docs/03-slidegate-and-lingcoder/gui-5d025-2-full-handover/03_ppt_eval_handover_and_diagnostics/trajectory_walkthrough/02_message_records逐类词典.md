# 02 `message_records` 逐类词典

每条记录常见字段：`id` · `created_at` · `type` · `text` · `payload` · `tool_name` · `tool_call_id` · `subtask_id` · `parent_id` · `scope` · `source` …

`scope=main` 表示主 Agent 线；子任务相关会出现 `subtask:...` 或 `subtask_id`。

---

## `user_input` — 用户侧输入

本样本第 0 条：反诈案例 + **【模板模式】dark-green** 钉死说明。  
`input_kind=text`。

中途第 43 条：自动确认后的「用户已回答…请继续」（批测无人值守注入）。  
第 45 条：再次带上原题（确认后上下文重建常见写法）。

**你会说：** 题干不一定只在开头；`ask_user` 之后还会再进 `user_input`。

---

## `assistant_output` — 模型这一轮「说的话」

- `text`：对用户/日志可见的话；本样本很多轮 `text` 为空，真正意图在工具里。  
- `payload.thinking_content`：思考摘要（若有）。本样本开头 thinking：要读 template skill。  
- `parent_id` / 后续 `tool_call.parent_id`：工具调用挂在哪次 assistant 下。

**你会说：** 空 `text` + 后面紧跟 `tool_call` 很正常；别误判成「模型没输出」。

---

## `tool_call` — 结构化工具调用（派工单）

本样本用过的工具计数：

| 工具 | 次数 | 典型意图 |
|------|------|----------|
| `read_file` | 2 | 读 `SKILL.md` |
| `execute_shell_command` | 11 | ls/find/init/slice/检查 HTML |
| `write_file` | 2 | 写 `task_pack.json` / `info_pack.json` |
| `ask_user` | 1 | 大纲确认 |
| `create_subtask` | 3 | 大纲编排 / 资产规划 / 批量出 HTML |

关键字段：

- `tool_name` / `tool_call_id`  
- `payload.function.name` + `payload.function.arguments`（JSON 字符串）

**你会说：** harness 只认这类结构化调用；若模型把同样内容打成纯文本，这里不会出现 `tool_call`，循环可能早停。

---

## `tool_result` — 工具执行结果

与上一条 `tool_call` 用同一个 `tool_call_id` 配对。

本样本真实例子：

- `read_file` 第一次失败：`success: false`，路径写成了 `local:///...`（三斜杠），错误要求 `prefix://path` 两斜杠。  
- 模型下一轮改成 `local://mnt/...` 后成功。  
→ 这就是「工具报错写回 → 模型纠正」的教科书轨迹。

`ask_user` 的 result：`waiting_for_user_input`；随后批测注入确认，才继续。

`create_subtask` 的 result：先回任务说明；真正完成看后面的 `subtask_summary`。

---

## `subtask_summary` — 子任务收工条

本样本三条，均 `succeeded`：

1. `subtask_0` 模板编排与单页大纲  
2. `subtask_1` 资产规划  
3. `subtask_2` 生成最终页面产物（最耗时：19:38 → 20:19）

**你会说：** 主 Agent 不手写 HTML；第三个子任务跑批量出图脚本；墙钟大头常在这里。

---

## `system_context` — 系统上下文注入

本样本在自动确认之后出现（约 19:15:43），带 Role / 工具能力说明。  
**你会说：** 不是用户打字，是 runtime 补的系统侧上下文。

---

## 配对阅读口诀

```text
assistant_output
  └─ tool_call (同 parent / 紧随其后)
       └─ tool_result (同 tool_call_id)
必要时：
  create_subtask → …子任务内部跑… → subtask_summary
```

精简全表：`/home/gui-5d025-2/zyy/benchmark/docs/总结/_assets/trajectory_samples/prod_26016eba_timeline.json`
