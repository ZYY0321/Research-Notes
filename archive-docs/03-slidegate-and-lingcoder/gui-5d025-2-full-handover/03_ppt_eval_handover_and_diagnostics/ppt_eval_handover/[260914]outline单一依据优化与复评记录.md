# outline.md 单一依据优化与复评记录

更新：2026-09-14。任务：`ppt_outline_md_only_v39_20260914`。本文记录合并后的小范围优化、复测口径、实际采集方式及操作入口；进行中的数字以文末实时文件为准。

## 1. 版本和修改边界

源仓库：`/home/gui-5d025-2/zyy/aipptx-templates`，分支 `test/ppt-outline-merge`，合并基线 `cc8c1e010b3c6184b353fd34dd9b06a35959a8c4`。该合并由 `dev/wangbo/ppt-outline-template` 与 `dev/tzk/ppt-v2` 组成。本次保留合并后的制作流程，不回退为 xhx_agent_v3 历史 skill。

本次修改在基线之上：

- 用户提供的大纲直接转换为公共 `outline.md`。移除 JSON 契约文件、源文本副本、选中文本副本、版本哈希及相关读写校验。
- 保真规则直接从当前 Markdown 提取。页数、顺序、页型、标题、要点和子要点都对照它校验。明确不扩写的要求以可读制作要求写在同一 Markdown 中，不生成新约束文件。
- 用户修改 Markdown 后，后续规划及生成使用当前内容。导入器不因重试覆盖修改；明确确认替换整份文件时才允许 `--replace-confirmed`。
- 页面请求和 review 读取当前 Markdown，并检查已有页面计划和切片是否过期。不通过时要求修正已有下游计划。
- 原有风格规划、语义分片/编译器、模板编排、素材处理、页面生成、review 及其预算/重试方式保持合并版本设计。

源仓库改动清单及每文件前后哈希保存在本轮控制目录 `source_changes.json`。运行副本 `skills_branch_snapshot` 包含与上一轮一致的模板资源和评测端点适配，独立冻结。`runtime_skill_sha256.json` 和 `branch_template_sha256.json` 用于本轮 smoke 与正式运行一致性检查，不是 PPT 生成过程中的大纲约束文件。

代码回归：90 项测试、4 项子测试通过；4 个 Skill 的 quick_validate 通过；git diff --check 通过。耗时/token 采集与汇总另有 8 项测试，覆盖无重复计数、缓存/reasoning 不重复加总、未知 usage、失败请求和分段边界。另有 3 项全量放行门槛测试通过。

## 2. 模型与并发

| 角色 | 模型/端点 |
|---|---|
| xhx_agent_v3 主 agent、子任务、实际 HTML 生成 | `SenseNova-Flash-Lite-20260727-v39-fp8-step4k-dpov2-mtp`，`http://10.210.9.14:208/v1`，OpenAI 协议 |
| 生成流程中的视觉 review | `qwen3.8-max-a`，TokenHub；返回的模型别名为 `qwen3.8-max`。沿用用户允许的 3.8 替代方案 |
| 最终独立机评 | `claude-sonnet-4-6`，TokenHub `/v1/messages` |

密钥从本轮权限受限的 `review.key` / `judge.key` 读取；不写入本文或源仓库。

Smoke 使用并发 1：无模板常规题 `seq_0007`、用户大纲保真题 `seq_900001`、模板题 `prod_1289b84a`。正式评测沿用 47×2 题，两个模式各并发 4，总计最多同时 8 套 deck。单页脚本内部并发另由实际命令决定，不把“8 套”说成“8 个模型请求”。

## 3. 耗时和 token 的分段定义

| 分段 | 包含内容 | 分界依据 |
|---|---|---|
| 大纲前（含确认） | 输入解析、附件处理、资料整理、任务/信息包、大纲生成或导入、校验与确认 | case_start 至有效大纲之后实际向模式制作阶段交接 |
| 大纲后 | 风格/页面规划、语义编译或模板编排、素材、HTML 生成、review、返修、交付 | 实际交接至该次 case_done |
| 最终裁判 | 渲染检查、逐页、全套和内容机评 | 与生成分开计算 |

分界采用实际事件，而非 outline.md 的 mtime：有效 `drafting_outline/done` 后的下游脚本调用或模式工作包分发。运行中可从 HTTP 工具元数据识别；结束后用该 case 的结构化 message_records 补充调度时间。若模型提前读取模式文档，不把那次阅读误算成大纲完成。记录具体 evidence_id、边界类型和时间精度。跨分界的单次调用单列；无法确定边界的调用单列，禁止按耗时比例摊分 token。该口径把确认到制作交接的调度开销放在大纲前，不声称测到了不存在的前端确认按钮时间。

时间同时报告：

1. 逐题大纲前、大纲后、整套真实用时；未完成题标为“截至当前”。
2. 请求耗时之和、P50/P95/P99/max、≥120 秒和 ≥300 秒数量。
3. 完成题的均值/分位数、逐题 token 和每页 token（有实际页数时）。
4. 烟测、正式评测分别汇总；最终裁判单列。生成与评分可能重叠，不能把二者简单相加叫端到端墙钟时间。

Token 报告输入、输出、缓存读取/写入、reasoning（网关报告时）、调用数、usage 已知/未知次数。OpenAI prompt_tokens 已包含缓存 token；Anthropic input_tokens 不含缓存读取/创建，因此输入合计另加二者。缓存与 reasoning 分项均不再次加进 total。没有返回 usage 的失败请求记为未知，已知 token 总和在存在缺口时是下界。任何请求成功但后续格式校验失败，其 usage 仍计入实际消耗。

## 4. 采集实现与限制

本轮通过私有 `telemetry/sitecustomize.py` 启用采集，环境变量只有设置 `PPT_EVAL_METRICS_DIR` 时才生效。它观察同步 httpx/requests 实际 HTTP 尝试的起止、HTTP 状态和响应 usage；不修改模型参数、消息、重试次数或响应。日志不记录请求正文、密钥、图片内容。主 agent/子任务以原运行时的 conversation_id、case_id、source 归属。裁判使用评分 worker 的 query_id。

沙箱中的既有评测 transport 为每次尝试加入唯一 attempt_id 和起止时间，继续通过工具 stdout/stderr 返回。宿主在工具 HTTP 回包处采集，避免依赖被主日志截断的打印文本。若模型在沙箱命令中主动用 tail 截断输出，无法保证恢复未回传的远端调用；此类覆盖缺口必须结合命令轨迹披露。阶段时间戳加入原有 stage_status 事件，不新增业务工作流阶段或约束载体。

汇总器去重键为实际尝试 id；同一次请求被多处观察不会重复计数。HTTP/SDK 重试的不同尝试全部保留。主模型对子任务的重复上下文输入是实际 token 使用，按网关 usage 计入，不能只统计最终回答 token。

## 5. 复现及持续运行

```bash
cd /home/gui-5d025-2/zyy/xhx_agent_v3
PPT_CONTROL="$PWD/output/ppt_outline_md_only_v39_20260914_control"
PPT_TASK="$PWD/automation/tasks/ppt_outline_md_only_v39_20260914"
```

检查源修改与单测：

```bash
git -C /home/gui-5d025-2/zyy/aipptx-templates branch --show-current
git -C /home/gui-5d025-2/zyy/aipptx-templates diff --check
.venv/bin/python -m pytest \
  /home/gui-5d025-2/zyy/aipptx-templates/skills/agent-3.0/tests \
  -q --import-mode=importlib
.venv/bin/python -m pytest "$PPT_CONTROL/telemetry/test_observer.py" \
  "$PPT_CONTROL/telemetry/test_analysis.py" -q
```

Doctor 原始探针与验收：

```bash
.venv/bin/python "$PPT_CONTROL/doctor_endpoints.py"
.venv/bin/python "$PPT_CONTROL/doctor_sandbox.py"
.venv/bin/python "$PPT_CONTROL/doctor_runtime_transport.py"
.venv/bin/python "$PPT_CONTROL/check_doctor.py"
```

首次 doctor 的失败证据和相同请求的复测证据分别保存。`check_doctor.py` 不改写失败记录，必须确认复测通过才放行。

已经挂起的四个服务：

```bash
systemctl --user status ppt-outline-md-only-smoke-20260914.service
systemctl --user status ppt-outline-md-only-score-smoke-20260914.service
systemctl --user status ppt-outline-md-only-pipeline-20260914.service
systemctl --user status ppt-outline-md-only-watch-20260914.service
```

- `run_smoke.sh` 使用 `scripts/run_batch_and_export.py` 和本轮 config，两个模式独立 OUT，保留 `--resume`。
- `score_smoke.py` 复用官方 `automation.pipeline._score_mode`：转换、Sonnet 打分、重算；使用官方评分锁与 skip_done。
- `continue_after_smoke.py` 等待全部 smoke 实际产物及有效分数，检查页集合、当前 Markdown 对账、无大纲 sidecar，随后调用 `launch_formal.py`。它不伪造 case 终态、不修改 deck、不替代评分器。
- `launch_formal.py` 校验快照后调用原 `pipeline.launch_batch/monitor_loop`，仍由官方链路早评分、断点恢复和上板。已创建正式 OUT 时继续原批。
- `monitor_preflight.py` 每 300 秒刷新进度、端点与看板状态，并更新耗时/token 分析。

若服务退出，应先查日志、确认是否已有 runner，再恢复原服务；不要同时手工启动同一个 OUT 的第二个 runner。模型/格式失败不得盲目用 --resume 掩盖，需按手册归因后对未成功子集恢复。

按需手工刷新只读分析：

```bash
.venv/bin/python "$PPT_CONTROL/telemetry/analyze.py" --control "$PPT_CONTROL"
cat "$PPT_CONTROL/time_token_analysis.md"
cat "$PPT_TASK/latest.md"
cat "$PPT_CONTROL/continuation_status.json"
```

## 6. 当前状态与异常

2026-09-14 17:54 开始新 smoke。doctor 通过复测，生成和评分监控已启动；截至本文初稿时首题仍在制作，不能宣称新一轮评分已上板。

已发现：主端点一次未返回工具调用（三次同请求复测通过）；Sonnet 图像请求一次 120 秒超时（复测成功）；常规题初次大纲生成内部三次格式失败后，主 agent 又调用一次生成器，违反 skill 停止条件。原始调用及消耗全部保留。后续新增问题与受影响范围追加在本轮 `smoke_anomalies.md`，实时进度以控制目录和 task 状态文件为准。

正式结果不覆盖 `ppt_outline_merge_v39_dpov2_mtp_20260911` 旧批。完成后仍需核对真实成功 case 与已评分 case 的集合、内容分有效性、看板数字一致性，并按手册更新模型卡、总分表和分析。外部同步状态另行披露。

## 7. 文件入口

- 实时状态：`automation/tasks/ppt_outline_md_only_v39_20260914/latest.md`。
- 分段耗时/token 可读报告：`output/ppt_outline_md_only_v39_20260914_control/time_token_analysis.md`。
- 逐题明细及证据：同目录 `time_token_analysis.json`。
- 原始请求计量：`metrics_smoke/requests.jsonl`、`metrics_formal/requests.jsonl`。
- 分支修改、冻结配置、doctor、smoke 和自动续接记录均在同一控制目录。
