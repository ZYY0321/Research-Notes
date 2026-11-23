# SFT 数据质量报告 ⑤：file_action + ask_user 数据修复管线

- **日期**：2026-07-14
- **作者**：wangbo（实现由 Claude Code 执行）
- **目的**：把 5 个 xhx-agent 轨迹 jsonl 里的 file_action 协议问题(报告①)和 ask_user 机械反馈问题,一键修复成两个干净的 SFT 文件(有模板 / 无模板)。
- **关联**：①协议合规、②子任务丢失、③根源确认、④模型评测。本报告是"怎么修 + 修了什么"的落地记录。

---

## 0. 一键运行

```bash
# 后台跑(读 ~1.9GB + 调 ~1.5万次 qwen,约 1 小时)
nohup bash scripts/run_repair_pipeline.sh [OUT_DIR] [WORKERS] > /tmp/repair_pipeline.log 2>&1 &
# OUT_DIR 默认 data/sft_repaired,WORKERS 默认 8
```

产物：`data/sft_repaired/ppt_agentic_sft_repaired_{template,notemplate}_<DATE>.jsonl`

---

## 1. 修的是什么问题(对应报告①/④结论)

| 问题 | 现象 | 本管线的处理 |
|---|---|---|
| **Q1** 系统 prompt 残缺 | 0629_query 42% 的 sys 缺「文件操作预播报协议」整段 | 注入规范协议段(锚点在 `## skill / SOP` 前) |
| **Q2** 写文件不发 file_action | write_file 65–89% 无 file_action;execute_code 写入也多不发 | 给 write_file **和可解析出目标的 execute_code/shell 写入**补规范 file_action |
| **Q3** file_action 后不接 tool call | 悬空 file_action(收尾轮冗余 / 网关畸形) | 删除悬空块;删空后整条 assistant 消息也丢弃 |
| **格式** | 源数据 ~19% file_action 缺 `<summary>` 开标签等 | 规范化为完整 target/action/summary 结构 |
| **summary 机械** | 早期版本按库随机抽、全 6 字、和上下文无关 | **qwen 结合 reasoning + 写入内容现编**,自然多样、不泄漏文件名/工具名 |
| **C5 target 对不齐** | 原数据里 file_action 的 target 和同轮写入对不上(140 处) | 归类:批量目录/结果确认/脚本产出=保留;写了别的文件=重定向;纯读/create_subtask=删除 |
| **ask_user 反馈机械** | 5184 处反馈=固定前缀 + `<ask_user_answer>` JSON,99% 照抄"确认"选项 | 去 JSON,**qwen 生成自然口语回复**,保持原决定(前缀保留) |

> **重要背景(报告④)**：这些问题不是导出脚本造成的,也不是 0629 数据"带坏"了模型——恰恰是 0629 教会了模型发 file_action(覆盖率 0→38%,≈opus)。本管线是把这批数据**清洗到超过 opus 的一致性**(覆盖率→100%、悬空→0、summary 更贴合)。

---

## 2. 管线步骤(scripts/)

| 步 | 脚本 | 作用 |
|---|---|---|
| 1 | `gen_summary_library.py` + `clean_summary_library.py` | qwen 生成 + 校验 summary **兜底库**(模型现编失败时用),按文件类型各 ~30 条自然短语 |
| 2 | `repair_file_action.py` | **主修复**:Q1 注入协议 / Q2 补 file_action(write_file + execute_code 写入解析)/ Q3 删悬空 / 规范化 / **qwen 上下文 summary** / 按 mode 分模板-非模板两文件输出。分块流式 + qwen 并发。 |
| 3 | `clean_repaired_summaries.py` | summary 里若残留内部标识(工具名/文件名),定点用 qwen 重生成;泄漏则回退兜底库。循环 2–3 遍收敛到 0。 |
| 4 | `fix_c5_targets.py` | C5 target 归属:重定向 / 删孤儿(见 §3)。跑 2 遍(第 2 遍处理 retarget)。 |
| 5 | `rewrite_ask_user.py` | ask_user 反馈去 JSON,qwen 现编自然回复,保持原决定。 |
| 6 | `qc_file_action.py` | 质检 C1–C6 + qwen 判定(见 §4)。 |

**辅助**：`trace_viewer.html` + `trace_viewer_server.py` —— 远程按绝对路径预览任意 jsonl(`python scripts/trace_viewer_server.py 8000`)。

---

## 3. 几个关键设计决策

- **mode 路由**：0629_query/0713 → 无模板;0709/0710 → 模板;0629_files(混合)→ 按 `data/test_inputs/ppt_file_based.jsonl` 的 `mode` 字段逐 case 判定(0 缺失)。
- **action**：write_file 从工具结果 `operation`(create→CREATE / overwrite→UPDATE);execute_code 默认 CREATE。
- **summary 由 qwen 现编**：喂 `reasoning_content` + 该轮进度正文 + 将写入的内容/代码 + 文件类型用途;硬约束不出现文件名/扩展名/路径/pptid/工具名。失败回退兜底库。
- **C5 归属策略**：目标匹配写入 / 批量目录 / 工具结果确认写入 / 该轮跑了 execute_code|shell(脚本产出,合理保留)→ **保留**;该轮写了**别的**真实文件 → **重定向**到真实写入(重生成 summary);该轮只有 read_file/create_subtask/todolist 或坏占位符 `pptid_xxx` → **删除**(孤儿)。
- **ask_user 重写**：只 naturalize 措辞,**决定不变**(99% 是确认,轨迹后续都按确认走,不能改成"调整");前缀(`context_pipeline.py:1276` 运行时串)保留,和生产"前缀+自然答案"对齐;去掉批量特有的 `<ask_user_answer>` JSON。

---

## 4. 质检口径(qc_file_action.py)

| 项 | 判据 |
|---|---|
| C1 | 每条 system prompt 含「文件操作预播报协议」或「File Action Protocol」 |
| C2 | 每个 write_file 同条 assistant 消息含 `<file_action>`(覆盖率应 100%) |
| C3 | 无悬空 file_action(content 有 fa、无 tool_calls) |
| C4 | 每个 file_action 结构完整、action∈{CREATE,UPDATE,DELETE}、summary 不含文件名/路径/工具名 |
| C5 | file_action target 归属:直配/代码内/批量目录/结果确认/脚本产出;**真正 mismatch(该轮无任何写)应为 0** |
| 模型判定 | qwen 抽样判 summary 是否贴合该文件类型、且不泄漏内部标识(允许含具体主题) |

---

## 5. 全量结果(20260714)

**输入** 16,274 条(0629_query 7887 + 0629_files 1807 + 0709 2703 + 0710 2783 + 0713 1094)
**输出** 无模板 9,901 条 + 模板 6,373 条

处理量：新增 file_action **10,262**(write_file 8416 + execute_code 1846,summary 全 qwen 现编)· 规范化 **3,138** · 删悬空 **883** · 修系统 prompt **3,329** · 丢弃坏收尾轮 **83** · C5 重定向 5 / 删孤儿 8 · **ask_user 反馈重写 5,184**。

**最终质检**：C1 100% · C2 100%(10542/10542)· C3 0 · C4 0/0/0 · C5 真正 mismatch **0** · qwen 判定 **98%**。

---

## 6. 复现 / 单步调试

各步可单独跑(见 §2)。质检：
```bash
python3 scripts/qc_file_action.py "data/sft_repaired/*.jsonl" --model-sample 50
```
预览某条：`python3 scripts/trace_viewer_server.py 8000` → 浏览器填绝对路径。

> 注:`repair_file_action.py` 的原始输入路径(SOURCES)硬编码在脚本顶部;换数据集改那里即可。summary 兜底库 `scripts/file_action_summary_library.json` 生成一次可复用。
