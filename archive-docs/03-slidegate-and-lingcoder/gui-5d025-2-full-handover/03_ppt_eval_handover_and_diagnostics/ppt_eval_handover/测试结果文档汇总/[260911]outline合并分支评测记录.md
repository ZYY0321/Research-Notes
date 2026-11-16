# test/ppt-outline-merge 评测记录

本轮是技能分支与指定模型组合的集成评测。源仓库是 `/home/gui-5d025-2/zyy/aipptx-templates`，分支 `test/ppt-outline-merge`，提交 `cc8c1e010b3c6184b353fd34dd9b06a35959a8c4`。运行宿主是 `xhx_agent_v3`；两者不是同一个 Git 仓库。源分支保持不变，在本项目输出目录内建立冻结的部署副本。

此文记录实际配置、命令和验收条件；最终结论须结合实时状态与 smoke 产物。当前阶段以 `automation/tasks/ppt_outline_merge_v39_dpov2_mtp_20260911/latest.md` 为准；本文不以 doctor 或单测通过代替真实全量结果。

## 1. 配置和隔离

| 角色 | 实际模型 | 请求入口 |
|---|---|---|
| 主 agent / 子任务 agent / 大纲生成 / HTML 生成及重写 | `SenseNova-Flash-Lite-20260727-v39-fp8-step4k-dpov2-mtp` | `http://10.210.9.14:208/v1/chat/completions` |
| HTML 截图 review / 图片筛选 | `qwen3.8-max-a`（服务返回别名 `qwen3.8-max`） | TokenHub OpenAI 接口 |
| 最终 benchmark 裁判 | `claude-sonnet-4-6` | TokenHub Anthropic 接口 |

原请求的 Qwen 3.7 没有可用通道。经用户明确同意，可使用 3.8；可用模型列表返回的是 `qwen3.8-max-a`。review 凭据向指定沙盒的上传已获用户明确授权。密钥仅存在任务私有文件和沙盒运行副本，不写在本文、复现命令或结果展示里。

主协议由实际 doctor 确定为 OpenAI。主模型温度 1、输出额度 128000、不额外传入 thinking 字段；HTML/大纲与主模型一致。review 输出额度 8192。并未通过关闭模型思考或降低正文额度来掩盖失败。

目录约定：

```bash
cd /home/gui-5d025-2/zyy/xhx_agent_v3
PPT_TASK=ppt_outline_merge_v39_dpov2_mtp_20260911
PPT_CONTROL="$PWD/output/${PPT_TASK}_control"
PPT_STATE="$PWD/automation/tasks/$PPT_TASK"
```

| 路径（相对 `PPT_CONTROL`） | 用途 |
|---|---|
| `source/` | `git archive cc8c1e0` 原始快照 |
| `skills_branch_snapshot/` | 当前冻结技能副本，含源提交自带的 20 套模板 |
| `config_branch.yaml` | 当前冻结模型与沙盒配置 |
| `manifest.json`、`runtime_skill_sha256.json`、`branch_template_sha256.json` | 来源、部署适配、87 个技能文件和 1444 个模板文件的校验记录 |
| `smoke_runs/notpl`、`smoke_runs/tpl_branch` | 独立 smoke 输出，后续不得并入正式 47 题 |
| `doctor_*.json` | 各项 doctor 结果 |
| `smoke_scoring.json` | smoke 自动评分状态与实际评分文件 |

## 2. 新分支如何接入旧评测宿主

部署副本替换四个完整技能目录：`ppt-maker`、`ppt-no-template-mode`、`ppt-template-mode`、`ppt-creative-mode`。20 套行业模板完整取自同一源提交的 `templates/templates/`，通用技能沿用宿主资源。技能里的 `/skills/` 部署路径适配为宿主实际挂载路径 `/mnt/data/skill/`。

部署核验发现最初的 `skills/` 副本沿用了宿主旧模板，其中 6 套与目标提交不同。因此新增 `skills_branch_snapshot/` 和 `config_branch.yaml`，没有覆盖旧产物；旧 `smoke_runs/tpl` 仅作为兼容性诊断，不计本分支验收和正式分数。模板 smoke 改在 `smoke_runs/tpl_branch` 运行。87 个非模板运行文件逐一校验不变，无模板两题不依赖模板资源，故复用成功结果，避免无意义重跑。详情见 `template_snapshot_correction.json`。

新分支调用模型的公共入口是 `_tool_call.call_tool`。本次在四个入口增加评测路由：生成类请求走指定 `:208`；视觉 review 类请求走 Qwen；`html_to_png` 继续使用原代码执行服务。路由传递调用方给定的 `timeout` 与 `max_attempts`，不会追加一层无限重试。只对 408、429、5xx 和网络超时/断连退避重试，硬 400 不重试。每次记录 request id、模型、端点、尝试次数、额度、耗时和实际返回模型，不记录密钥。

禁用工具为 `web_search,image_search,image_generation,fetch_url,image_vqa,rerank_texts`；`deep-research` 从技能 allowlist 移除。helper 入口同时封锁相关搜索/生图调用，避免技能脚本绕过运行时工具禁用设置。

宿主做了三项兼容修正，均与源分支算法分开记录：

1. `scripts/run_batch_and_export.py` 的预检根据真实 import 检查 `_tool_call.py` 或 `_html_llm_direct.py`，不再强制新分支提供旧传输实现。启动前仍会拒绝缺失的实际依赖。
2. `scripts/build_benchmark_eval.py` 随 HTML 拷贝 `themes/`；否则模板页面引用 `../themes/*.css` 时会在裁判截图中丢失主题样式。
3. `automation/pipeline.py` 支持任务固定 `eval_date=20260911`，防止跨午夜续评生成第二套 query 目录；尚无正式输出时也不再把空路径解析到仓库根目录的历史 events。

验证：原分支测试 90 passed、4 subtests passed；传输路由测试 4 passed；宿主兼容、恢复、评分导出与后置文档相关测试最终 28 passed。原有一项终态测试期望不正确：同一 case 新 start 后旧失败终态已失效，当前终态总数应为 1 而非 2，已修正断言。

## 3. 本轮重点验证的实现链路

普通请求先产出 `task_pack.json` 和 `info_pack.json`，执行 pack preflight，然后由生成接口产出 `outline.md`。大纲解析器校验结构和模式容量约束；无效候选在有限次数内只修正校验问题。用户确认后下游只读该大纲。

用户提供的大纲通过 `ppt-maker/scripts/user_outline.py` 导入，保留源文本、选取文本和规范化大纲三份记录；`outline_contract.json` 保存三者 SHA256、页数、结构锁、正文扩展策略和受保护页。`--check` 会检验确认版本是否被替换。正文可以在既有叶节点内补充，但不得新增大纲节点、填充受保护占位或空白页。

无模板流程先确定 pipeline capabilities，分别规划风格和语义正文，随后确定性编译 `slide_plan.json`，再进行素材、页面输入切片、HTML 批量生成、lint、截图 review 与有限重写。`finalize_html_pages.py` 读取真实产物输出 success / partial_success / error，并单独报告 degraded pages。确定性 fallback HTML 是降级结果，不能隐藏为正常生成成功。

模板流程将大纲映射到固定模板页面类型，由 agent 按模板 schema 写 plan，随后生成素材与页面输入；批量生成后运行 lint，必要时有限重试。此分支的模板路径没有无模板路径那样的全页视觉 review/重写阶段；最终两种模式都由独立 Sonnet benchmark 评分。

端到端链路采用普通文本，Markdown 预览无需 Mermaid 支持：

```text
用户请求 / 原始附件
  -> task_pack + info_pack
  -> 生成大纲或无损导入用户大纲
  -> 确认版本 / outline_contract
  -> 模式规划 -> 无模板确定性编译 / 模板 agent 写 plan -> 校验
  -> 素材选择 -> 每页 input.json
  -> 指定主模型生成 HTML -> lint
  -> 无模板截图 review + 有限重写
  -> 最终页面与终态审计
  -> benchmark 转换（code + 相对资源 + query_info + 附件）
  -> Sonnet 4.6 评分 -> 重算 overall -> 汇总 -> 看板
```

## 4. Doctor 与 smoke 的复现

已完成的 doctor 包含主模型字符串/数组 content、工具选择 none、结构化 tool call、宿主 review 和裁判视觉调用、沙盒到主端点实际推理、文件上传下载、沙盒 HTML 截图与实际 review、宿主 Chromium 截图。不是只测 TCP 或 `/v1/models`。

需要主动复测时使用以下命令。它们会实际请求端点；已有通过结果不需要因查看状态而重复执行。

```bash
.venv/bin/python "$PPT_CONTROL/doctor_endpoints.py"
.venv/bin/python "$PPT_CONTROL/doctor_sandbox.py"
.venv/bin/python "$PPT_CONTROL/doctor_runtime_transport.py"
```

注意 `doctor_endpoints.py` 保留最初 3.7 探测失败作为原始证据。最终 review 门槛读取 `doctor_review_qwen38.json`；不能把旧通道失败误记为当前 3.8 失败。

smoke 由以下三个案例构成：

| 模式 | case | 检查重点 |
|---|---|---|
| 无模板 | `seq_0007`，FDD 10–15 页 | 普通请求到生成大纲、页面规划、完整页面与 review |
| 无模板 | `seq_900001`，专用 3 页用户大纲 | 中文/英文标题、页序、点树、45%、TODO 和留白页的保留 |
| 模板 | `prod_1289b84a`，固定 blue-table 模板 | 模板映射、相对资源、HTML 与 lint |

```bash
# --resume 会保留成功 case；运行前先确认没有同目录的 runner。
bash "$PPT_CONTROL/run_branch_smoke.sh"

# smoke 服务已在后台运行时，只查看日志，不重复执行上述命令。
systemctl --user status ppt-outline-merge-0911-template-branch-smoke.service
cat "$PPT_CONTROL/smoke_scoring.json"
cat "$PPT_STATE/latest.md"
tail -n 30 "$PPT_CONTROL/smoke_notpl.batch.log"
tail -n 30 "$PPT_CONTROL/smoke_tpl_branch.batch.log"
```

自动评分守护 `score_smoke.py` 每 60 秒盘点 smoke；对已有 `done` 且有 HTML 的案例调用现有 `pipeline._score_mode` 做隔离诊断评分，模式结束后核对全部覆盖。评分启动不等于 smoke 质量验收通过。评分入口有全局锁和任务/模式锁；evaluator workers=4、skip_done=true、no_repair=true。smoke 使用独立版本 `ppt_outline_merge_v39_dpov2_mtp_20260911_smoke_notpl` 和 `ppt_outline_merge_v39_dpov2_mtp_20260911_smoke_tpl_branch`。守护返回 scored 后，仍需检查评分字段和截图，不能仅凭结果文件存在放行。截图由本次 agent 查看并记录，后续分数字段由受测的启动门槛逐项检查。

```bash
# 已有受管服务，不重复启动。以下是前台复现入口。
.venv/bin/python "$PPT_CONTROL/score_smoke.py"
systemctl --user status ppt-outline-merge-0911-smoke-score.service
```

smoke 的运行门槛依照 `pipeline_AI_RUNBOOK.md` §3：沙盒、技能、大纲/规划链路实际运行，生成可打开的非空页面，评分器输出实际分数。质量问题须原样记录和计分，不把质量满分作为额外的开跑条件。另需逐项检查：三题最新有效终态与非空页数；plan 预期页码与实际 HTML 页码一致；用户大纲 contract 校验、TODO 与空白页；无模板真实 review 记录；模板 CSS/图片可达；独立裁判产出有效分数。不能仅按 runner 的 `done` 宣称页面质量合格；缺页、无 review 或大纲不一致都需单独说明、归因，恢复可恢复环节，并在验收记录列明。

## 5. 全量、续跑、打分与上板规则

smoke 验收前不执行本节全量命令。正式输入分别是 `data/added/ppt_testset_industry_balanced_v2.jsonl` 和 `data/added/ppt_testset_industry_balanced_v2_template.jsonl`，各 47 个唯一 case，按 id 对齐，不按行号对应。每模式并发 4，max-turns=20，seed=42，使用同一冻结配置和技能。

下列命令展示完整生成参数。`PPT_FORMAL_OUT` 必须保存为该模式唯一正式 OUT，续跑保持原值；切勿每次重设新时间戳重跑成功题。

```bash
PPT_MODE=notpl
PPT_INPUT="$PWD/data/added/ppt_testset_industry_balanced_v2.jsonl"
PPT_FORMAL_OUT="$PWD/output/testset_v2_${PPT_TASK}_${PPT_MODE}_20260911"
.venv/bin/python scripts/run_batch_and_export.py \
  --input "$PPT_INPUT" --output "$PPT_FORMAL_OUT" \
  --config "$PPT_CONTROL/config_branch.yaml" \
  --concurrency 4 --max-turns 20 --seed 42 --resume \
  --disable-tools web_search,image_search,image_generation,fetch_url,image_vqa,rerank_texts \
  --disable-skills deep-research
```

模板模式改为 `PPT_MODE=tpl`、模板输入文件，并使用另一个固定 OUT。正式启动后必须把两个 OUT、PID、固定日期和版本写入任务 state，然后登记两张正式看板卡片。不要调用会重新生成旧版 skills 的 `pipeline.start_task` 覆盖本次分支副本。

本次已准备专用启动入口，仍调用现有 `pipeline.launch_batch` / `register_dashboard` / `monitor_loop`：

```bash
.venv/bin/python "$PPT_CONTROL/launch_formal.py"
```

该入口要求有根据真实产物与评分写出的 `smoke_acceptance.json`，核对配置、技能和验收证据指纹；验收缺失或文件变化均拒绝启动。不要手工造一个 `accepted=true` 绕过 smoke。已有正式 OUT 时不会另起一套生成任务。


现有 `pipeline._score_mode(task_id, mode, out_dir, input_jsonl, version, log_path)` 串联四步：`build_benchmark_eval.py` 转换、`benchmark/run_from_config.py` 评分、`benchmark.recompute_overall_jsonl` 重算、`BenchmarkAggregator.generate_summary` 汇总与看板 reload。使用任务私有 `eval_api_key_file`，不能错误继承其它模型裁判 key。单套达到 20 个有效 HTML 后早打分，新增缺分 case 达到 3 后增量评分，全部终态后最终补评分。

本次正式任务启用现有 `automation/pipeline.py` 中的 `auto_resume_infra=true`：进程已退出时，只对最新 infra_failed/无终态的中断 case 调用官方 runner 的原 OUT `--resume`；跨进程 generation 锁防止双跑，恢复间隔至少300秒，每模式最多3趟，日志写 `infra_resume_history.jsonl`，仍失败则标记待归因。该选项默认关闭，只为本任务开启；不会用它重跑已完成或内容失败的 case。

正式转换增加 `--only-successful`，仅导出最新终态 done 的产物。失败残页不提前入评分，避免恢复后 skip_done 复用失败版本分数。

每次恢复前输出最新终态盘点并读原日志。`--resume` 只自动补 `infra_failed` 和无终态的被中断任务；`other_error`、`done_no_html`、`render_suspect`、`content_incomplete` 会被跳过，须先归因，再用有审计记录的 remain 子集处理可恢复项。不得伪造终态、把模型内容问题改成基础设施问题，或覆盖成功产物。

最终必须将评分 query_id 通过 `query_info.txt` 映射回原 case_id，核对 `G - S` 为空，其中 G 为最新 `done` 且有页的生成集合，S 为去重的有效评分集合。目标仍是每模式 47 套；按业务最低 40 套收口时必须公开所有缺口和原因。只看 JSONL 行数、shell rc=0 或服务 active 不足以认定完成。

本任务启用 `export_local_deliverables=true`，官方评分函数结束后由 `automation/task_deliverables.py` 从去重 JSONL 自动刷新本地 A/F/B/C，保留其它模型记录；飞书同步单独记 pending，不伪报同步成功。

上板后仍需交付：两卡 `model_analysis.json`、分数总表、模型特点与缺陷分析、失败 showcase、交接文档，以及手册要求的同步产物。正式结论不能使用 smoke 分数，发布前确认两模式点击可见当前分数和真实生成记录。

## 6. 持续监控

`ppt-outline-merge-0911-watch.service` 每 300 秒检查主端点、沙盒、看板、分支提交及本次 smoke / 正式输出，持续写 `latest.json`、`latest.md` 和 `monitor_history.jsonl`。它只读状态，不会绕过 smoke 验收启动全量。

```bash
systemctl --user status ppt-outline-merge-0911-watch.service
cat "$PPT_STATE/latest.md"
tail -n 5 "$PPT_STATE/monitor_history.jsonl"
```

监控按 agent / HTML / review 分开统计成功与失败耗时；只统计主 smoke 和正式日志中实际可见的请求，不含旧模板诊断与隔离恢复，工具输出截断也可能漏计。慢请求按手册记录：单次 120 秒开始记账，300 秒形成反馈；20 次以上请求 P95 达到 120 秒时记录系统性长尾。断点恢复后必须看到新的 case_start、实际模型响应和有效工具/HTML 增长，不能只报告服务启动成功。

## 7. 比较边界

现有看板中有 v39 step4k dpov2、dpov1-mtp 等历史结果，但未发现与本次 `dpov2-mtp` 完全同名、同配置的旧技能分支配对基线。本轮可以评价本组合的完成率、页面质量、大纲保留行为及错误类型；不能直接把不同 checkpoint / 不同 review 配置的历史分差解释为本次合并的因果收益。需要做合并收益实验时，应另立同一模型、同一数据、同一 review/judge 配置的旧技能对照组，分别保存输出和分数。

## 8. 已观察到的 smoke 效果与限制

- 无模板普通 FDD 请求产出 12/12 页，runner 终态 done；分支 finalizer 为 partial_success，质量失败页为 3、7、8、10、11，因禁用生图而缺素材的降级页为 1、12。第 3、11 页截图确认正文过小、第 11 页六列排版过密。没有确定性 fallback 页。runner done 只能说明存在可导出结果，不能替代页面验收。
- 用户大纲案例产出 3/3 页，finalizer success。源文本与输入完全一致，三份 contract 哈希通过，45%、TODO：待定、中文与 English 标题均保留；第 3 页没有被补写正文。已人工查看页面截图。这是当前大纲保真链路的正向证据，尚不能代表所有输入都保真。
- Qwen review 出现 120 秒请求超时。原 FDD review 达到预算后，部分最终 review 没有完成；在隔离副本仅恢复未完成/传输失败 review，没有重新生成或改动原 12 页 HTML。第 10 页补 review 成功并检出页脚越界；第 7、8 页各重试两次后仍超时。不能把恢复脚本 rc=0 当成全部恢复成功。
- 分支恢复逻辑把非空但失败的 final_review 视为已完成；review 抛错时又可能保留旧 review.md，finalizer 有读取旧审查结果的风险。证据见 `review_recovery_summary.json`、`review_recovery_seq_0007/`、`smoke_anomalies.md`。本轮保持待测分支行为不变，先记录并由独立裁判对最终 HTML 计分。
- 第一题风格子任务反复读文件耗尽轮次，最后在禁止工具调用阶段返回伪工具文本，未真正写出 style_spec；后续由主任务恢复。该现象属于规划/预算边界，不等于主端点不支持结构化 tool call。doctor 已验证后者。

这些发现区分了部署偏差、模型生成质量、review 传输故障与分支恢复逻辑。正式结论将以 47×2 的完成率和去重评分更新，不把 smoke 的局部效果外推为全量结论。

## 9. 合并分支的实现索引和局部复现

以下路径均相对冻结副本 `skills_branch_snapshot/`。源代码在 `source/skills/agent-3.0/` 下同名；两者仅有 manifest 中记录的路径、端点传输适配。不能用旧版 `_html_llm_direct.py` / `outline.json` 的说明替代本节。

### 9.1 大纲导入与不可变约束

`ppt-maker/scripts/user_outline.py` 的 `import_outline()` 先选择整份输入或 inline 大纲，再解析页面和嵌套节点。每个源节点保留 title、level、children 和 source_span；规范化时生成 `outline.md` 头部和页结构。输入指纹为 `SHA256(source + NUL + body_policy + NUL + protected_pages串 + NUL + authorization)`。存在旧 contract 且指纹不同而没有 `--replace-confirmed` 时拒绝覆盖；同一指纹重复导入保持版本号，新指纹递增版本。

`user_outline_contract_v2` 默认允许在叶节点内解释，始终锁页序、页数和点树；`--preserve-only` 关闭正文扩展，`--preserve-page N` 单独保护某页。原始、选取、规范化文本分别落盘并记录 SHA256。`check_contract()` 比较三份文本哈希及 confirmed 标记：这是文件未被替换的校验，并不单独证明 HTML 没有编造内容；后者还依赖 plan 对账、渲染约束及独立裁判。

```bash
# 沙盒内局部复现；PPT_DECK 指向已建立 task_pack 的本次 deck。
PPT_SKILLS=/mnt/data/skill
PPT_DECK=/mnt/data/ppt/example_deck
python "$PPT_SKILLS/ppt-maker/scripts/user_outline.py" \
  --deck "$PPT_DECK" --source /mnt/data/user_outline_fixture.md \
  --allow-body-expansion --preserve-page 3
python "$PPT_SKILLS/ppt-maker/scripts/user_outline.py" --deck "$PPT_DECK" --check
```

普通 query 使用 `outline_md_generate.py`，最多生成/结构修正 3 个候选。它从 task_pack/info_pack 及提示词构造请求，剥除 Markdown fence、解析页型与要点，只有校验通过才落盘。模板容量从 `tag_gen_results.json` 读取；当前代码实际取排序后 `int(n*0.6)` 位置的容量，注释写“70% 分位”与实现不一致，应以代码为准。用户已确认大纲的结构不能为了模板容量被合并，应回模板选择阶段重选。

### 9.2 两种 plan 的生产方式不同

无模板 `build_slide_plan.py` 的正常路径是：capabilities → 风格与语义两份输入 → compile → validate。`assemble_content_semantic()` 接受每页一个 `page_NNN.json` 或每块 1–4 页的 `part_*.json`，禁止两种混用；检查缺页、重复页、未知页和页码与文件名不符。语义对象经过字段级验证，再与 style variant 绑定，`compile_semantic()` 产生 `slide_plan.json`。写入采用同目录临时文件、flush/fsync、os.replace，避免中断留下半份 JSON。失败返回结构化 phase/page_number/point_number/field/retryable，供 agent 定点修正。

```bash
# 风格子任务已写好 style_spec.json，语义子任务已写好 content_parts 后执行。
python "$PPT_SKILLS/ppt-no-template-mode/scripts/build_slide_plan.py" \
  capabilities --deck "$PPT_DECK"
python "$PPT_SKILLS/ppt-no-template-mode/scripts/build_slide_plan.py" \
  assemble-content --deck "$PPT_DECK" --parts-dir "$PPT_DECK/content_parts" \
  --out "$PPT_DECK/content_semantic.json"
python "$PPT_SKILLS/ppt-no-template-mode/scripts/build_slide_plan.py" \
  compile --deck "$PPT_DECK" --content-semantic "$PPT_DECK/content_semantic.json" \
  --out "$PPT_DECK/slide_plan.json"
python "$PPT_SKILLS/ppt-no-template-mode/scripts/build_slide_plan.py" \
  validate --deck "$PPT_DECK" --plan "$PPT_DECK/slide_plan.json"
```

模板模式没有同名确定性 plan 编译器。agent 读取 `stages/03-slide-plan-generation.md` 按 `ppt_template_slide_plan_v1` 写 JSON：顶层 deck_dir/ppt_id/language/title/total_pages/pages/unresolved；页级 page_id/page_number/page_number_label/page_type/title/layout/content/unresolved/template_id/page_goal；`content` 只允许 sub_pointN，每点包含 icon/sub_point_name/text/table/chart/picture/picture_source_path/sub_sub_points/slot_id。slot_id 必须来自已 enrich 的 template_map，picture-NNN 是另一命名空间，table/chart/picture 至多一种非空。然后运行公共 `outline_md_preflight.py --deck ... --against-json`，比较页序、标题与节点骨架。模板槽容量不足必须重选模板，不能删节点凑槽。

### 9.3 HTML、review 和最终终态

`slice_stage5_inputs.py` 为每页生成 `page_NNN.input.json`，关联计划、已解析资源、提示词所需契约及目标 HTML 路径。`html_page_generate_batch.py` 并发调用 `_tool_call.call_tool`；模板模式附带原模板 HTML 并执行 `lint_page_html.py`，检查主题链接/变量、模板结构和占位等；无模板模式进行自身页面 lint，允许显式记录的 fallback 降级。

无模板 `html_page_review_batch.py` 用 `review_status.json` 记录每页 initial_html_hash、initial_review、rewrite_attempted、rewrite、rewritten_html_hash、final_review。初审 → 有问题且未重写页 → 重写 lint 通过才替换 → 复审；提交重写前先持久化 rewrite_attempted，防止中断重跑同一页的生成。下次运行按 HTML 哈希辨认原版或已提交重写版，仅补缺失阶段。当前对“存在但传输失败的 final_review”没有正确重新排队，是本轮实测发现的恢复边界，不能承诺此脚本能自动补全所有超时。

`finalize_html_pages.py` 从 plan 得出预期页码，再读取真实 HTML、lint、review 和素材降级证据：全部页失败为 error，部分失败为 partial_success，无失败为 success；另报 missing_pages、quality_failed_pages、degraded_pages。它的 page_count 是预期页数，不应直接当成磁盘上的有效 HTML 数量。外层 runner 的 done 是另一层终态，因此本任务同时保存 finalizer 结果与 runner 事件。

### 9.4 宿主与沙盒路径的区别

沙盒持久化 JSON 使用 `/mnt/data/...` 逻辑路径，宿主回收目录为 `output/sandbox/<conv_id>/...`。做只读审计/隔离恢复时，`runtime_paths.py` 可通过 `AGENT_LOCAL_WORKSPACE_ROOT` 和 `AGENT_LOCAL_SKILLS_ROOT` 映射到副本；不要批量字符串替换已生成的 input.json，否则会改变证据与恢复哈希。局部脚本示例说明阶段接口，实际整套复现应由第 4、5 节 runner/控制器维护会话、自动答疑与导出。

## 10. 无人值守续接与评分验收门槛

`continue_after_smoke.py` 每 60 秒检查状态，只有 `smoke_visual_acceptance.json` 已记录实际产物检查且证据哈希未变化后，才等待两种 smoke 的实际评分完成。检查项为：最新成功集合与三题预期集合一致；score query_id 映射回 case_id 后覆盖完全；去重条数为 2+1；七项分数均为有限的 0–1 数值；content_eval_dynamic_items > 0；存在真实页面评分。质量分低不等于运行门槛失败，但缺失/NaN/无内容评测不能放行。

通过后写 `accepted_smoke_scores.json` 和 `smoke_acceptance.json`，再进入现有 `launch_formal.py` / official pipeline。发现证据变化或非法分数字段时写 `continuation_status.json` 的 needs_triage，保留监控，不篡改或删除评分记录。已有正式 OUT 则恢复监控原任务，不能新建目录重跑。门槛的 7 项测试已通过，涵盖等待真实分数、拒绝缺失/NaN/零 checklist/无页面结果及拒绝变化的产物证据。

```bash
# 前台复现入口。已有同名服务时只看状态，不重复启动。
.venv/bin/python "$PPT_CONTROL/continue_after_smoke.py"
cat "$PPT_CONTROL/continuation_status.json"
systemctl --user status ppt-outline-merge-0911-pipeline.service
```

持续生成恢复与评分由本任务的官方 pipeline 负责；只读 watch 负责每 5 分钟把状态写入报告。报告文件会持续更新，聊天中的状态消息是当次观察，不代表后台仍未完成的部分已完成。


## 11. 正确模板快照的实际验收（2026-09-11 19:53）

prod_1289b84a，conv=batch_prod_1289b84a_0ed915，总耗时578.06秒，12/12页齐全。首批256.043秒，11页lint通过，页5失败；agent只对页5再调用一次批脚本（含内部一次lint重试），耗时93.104秒，仍失败。没有重跑已通过的11页。

宿主Chromium渲染12页：所有主题CSS可加载，所有实际img均加载成功，网络请求失败0。第5页lint错误并非浏览器找不到文件，而是生成HTML删除了fallback_h.jpg占位图，lint把该文件当成必须保留的固定图；代码只豁免fallback.png，未涵盖fallback_h.jpg/fallback_v.jpg。第4/6/7/8/10页则保留了建筑照片占位图，静态lint通过，但与植物认知内容明显不匹配。

第3页有JavaScript语法错误 Unexpected identifier 'or'，HTML第569行写成 if (!nextSrc or nextSrc === currentSrc)，静态页面可打开，但主题切换脚本不能执行。第11页圆环标签互相挤压，顶部另有极小文字。已查看模板1/3/4/5/10/11页截图，保留原始HTML进入裁判评测，没有人工修图、替换素材或修页面。

产物运行门槛：27/27页存在且计划页码一致，3页用户大纲contract通过，27页中的模板12页均可在浏览器加载。独立Sonnet实际评分仍排队，因此尚未放行正式全量。
