# AI 操作手册：接入新模型并完成生成、评分、上板

本文件面向接手任务的 AI。目标是把新模型从端点接入一直跑到可查看的评分看板，并把明确结果交给用户。

## 首要指令

开始前完整阅读两份 canonical docs：

1. [`0708_评测复现完整手册.md`](../评测任务文档/0708_评测复现完整手册.md)
2. [`0709_跑完模型的后置产出清单.md`](../评测任务文档/0709_跑完模型的后置产出清单.md)

本文件只说明新的自动入口。模板/无模板双批、探活、keep-good remain、评分验收、模型命名，以及上板后的模型卡、总分总表、分析和失败 showcase，以上述两份文档为准。

## 完成标准

只有同时满足以下条件，任务才算完成：

1. 新模型配置不含写入 Git 的真实密钥。
2. smoke 任务成功生成可打开的页面。
3. 全量任务已完成，或所有未完成项都有明确、可恢复的错误分类。
4. 评分 JSONL 已生成，已检查题数及缺失分数。
5. `results_dashboard/runs.json` 已登记本次 run。
6. 看板 `/healthz` 正常，首页能看到新模型、分数和页面。
7. 向用户报告版本、输出路径、成功数、评分覆盖数、总分及主要异常。

## 禁止事项

- 不假设宿主机环境变量会进入沙箱。配置脚本会按完整手册自动实拷 skills，并把 HTML 端点写入 `.pipeline/skills_<model>/`。
- 不运行 `git add .`；运行结果、密钥、私有配置不得提交。
- 不把 API key 写进 README、YAML 模板、shell 历史展示或日志。
- 不因少数 infra 错误重跑整批；使用 `--resume`。
- 不把旧 run 的 deck 当成本次成功产物。

## 0. 收集输入

必须取得：

- `VERSION`：看板中的唯一短标识。
- `MODEL_NAME`、`MODEL_API_BASE`、`MODEL_API_KEY`。
- `MODEL_PROVIDER`：`openai` 或 `anthropic`。
- `EVAL_API_BASE`、`EVAL_API_KEY`；可选 `EVAL_MODEL`。
- `BASE_CONFIG`：默认是仓库内的 `pipeline/conf_v3_ppt_eval_base.yaml`，通常无需用户另给。

缺少密钥时向用户索取或让用户在 shell 中导出；不要让用户提交密钥文件。

## 1. 环境检查（doctor）

```bash
set -e
git status --short --branch
command -v git
command -v uv
python3 --version
test -f "$BASE_CONFIG"
test -f data/added/ppt_testset_industry_balanced_v2.jsonl
bash -n pipeline/run_both.sh pipeline/run_all.sh pipeline/bootstrap_eval.sh
python3 -m py_compile pipeline/*.py scripts/run_batch_and_export.py \
  scripts/build_benchmark_eval.py scripts/build_dashboard.py results_dashboard/server.py
```

然后执行评分器 bootstrap：

```bash
bash pipeline/bootstrap_eval.sh
```

它会自动取得固定版本的 `xhx-ppt-eval` 并安装隔离环境。

## 2. 设置运行参数

只在当前 shell/export 环境中设置：

```bash
export VERSION='my_model_v1'
export MODEL_NAME='new-model'
export MODEL_PROVIDER='openai'
export MODEL_API_BASE='https://gateway.example/v1'
export MODEL_API_KEY='***'

export PPT_HTML_LLM_PROTOCOL="$MODEL_PROVIDER"
export PPT_HTML_LLM_BASE_URL="$MODEL_API_BASE"
export PPT_HTML_LLM_MODEL="$MODEL_NAME"
export PPT_HTML_LLM_API_KEY="$MODEL_API_KEY"

export EVAL_API_BASE='https://judge.example/v1'
export EVAL_API_KEY='***'
export EVAL_MODEL='claude-sonnet-4-6'
export BASE_CONFIG='pipeline/conf_v3_ppt_eval_base.yaml'
```

如果 API Base 已包含 `/v1`，确认目标协议路径没有形成重复 `/v1/v1`。先用最小请求探活，不输出完整响应头或密钥。

## 3. Smoke 验证

全量之前，将输入限制为少量 case，验证以下链路：

- 主 LLM 能响应并调用工具。
- HTML 模型协议与路径正确。
- 沙箱可执行且产物可取回。
- 至少生成一个非空 `page_*.html`。
- 评分器能读取转换后的图片/HTML 并输出一行分数。

如果当前入口尚未提供独立 `--smoke` 参数，可用小型输入 JSONL 设置 `INPUT`，并给一个新的 `RUN_ID` 执行 `pipeline/run_all.sh`。不得直接以 47 题试错端点。

## 4. 全量运行

```bash
export CONCURRENCY=4
export EVAL_WORKERS=8
export LABEL='看板展示名称'
bash pipeline/run_both.sh
```

该入口先跑无模板，再跑模板；每个模式依次执行：

1. 从基础 YAML 生成私有运行配置；
2. 批量生成并导出 trace；
3. 构建生成侧 dashboard；
4. 转换为 `xhx-ppt-eval` 输入结构；
5. 自动安装并运行正式评分器；
6. 将 run 和评分文件登记到结果看板。

重复执行同一 `VERSION/RUN_ID/OUT` 时应利用断点续跑。保留原输出目录，不手工删除成功 case。

## 5. 验收与上板

```bash
test -f "$OUT/batch_summary.json"
test -f "results_dashboard/scores/industry_v2_${VERSION}.jsonl"
python results_dashboard/server.py --host 127.0.0.1 --port 8770
curl -f http://127.0.0.1:8770/healthz
```

检查：

- `batch_summary.json` 的总题数、成功数和终态分布。
- 评分 JSONL 的行数、`overall_score` 缺失数。
- 首页能选择新模型；模板/无模板标签正确。
- case 卡片能打开真实页面，资源没有 404。
- “模型分析”页有对应条目；如果没有，明确说明分析仍需人工补充，不伪称已生成。

最后逐项执行 `0709_跑完模型的后置产出清单.md`。分数上板不等于任务结束。

## 6. 常见故障与动作

| 症状 | 处理 |
|---|---|
| 401/403 | 检查 key、权限和协议；不要循环重试 |
| 404 | 检查 Base 是否应包含 `/v1`，以及 OpenAI/Anthropic 路径 |
| 429/503/overloaded | 保留输出目录，稍后 `--resume` |
| 空响应 | 检查 thinking/tool-call 协议和服务返回；保留诊断日志 |
| `done` 但无页面 | 归为 `render_suspect`，不得借用旧 deck |
| 评分为 0 或图片缺失 | 检查 Playwright/Chromium、页面资源和转换目录 |
| 看板无新模型 | 检查 `runs.json`、评分路径并调用 `/api/reload` |

## 7. 向用户交付的固定格式

### 续评输入去重与日期固定（2026-09-16补充）

续评必须固定本批 `eval_date`。转换器按日期创建目录；每天使用当天日期会让同一个 case 在同一 VERSION 的输入根目录下出现多份，`skip_done` 不能阻止尚未成功的同题副本被同时提交。若评分长时间无新增整题分数但同一页的 debug 文件反复更新，检查输入目录数与唯一 `Query序号` 数是否一致。

本次发现旧 v41 批次有611个目录、47个唯一题，未评分 q1495 有13份相同的 HTML 与题目信息。处置须先备份已成功分数、停止明确归属的重复评分器，再核对内容摘要并将重复副本归档到输入根目录之外，保留唯一有效副本后串行续评。不同内容不能只凭相同题号合并；不能为抢评分锁擅停其它任务。本批实际修复记录见 `automation/tasks/sensenova-flash-284b-vision-v16-20260908-sft-step400/0916_takeover.md`。

```text
版本：
模型与协议：
生成输出目录：
总题数 / 生成成功 / 可评分：
评分文件：
总分与主要子分：
看板地址：
主要优势：
主要问题：
仍需补跑或人工处理：
```

不要只说“跑完了”；必须给出可核对的数字、路径和地址。
