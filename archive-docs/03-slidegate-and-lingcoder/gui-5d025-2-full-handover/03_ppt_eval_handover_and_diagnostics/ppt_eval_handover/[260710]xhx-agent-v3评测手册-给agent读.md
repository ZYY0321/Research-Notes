# PPT 评测复现完整手册（从零上手，零踩坑版）

> **交接副本（2026-09-11）**。人读入口：同目录 `[260911]评测交接（人读）.md`。  
> 本机开跑看台：http://10.151.196.17:8770/automation （服务 `:8877`）。  
> 管线坑、便携 runbook、旧交接：`_不进飞书_agent经验与历史/`。  
> 源文件若继续改：`评测任务文档/0708_评测复现完整手册.md`，改完再同步本包。
>
> 2026-07-08 起稿。目标：**没接触过本项目的人，照这份从零跑通一次完整评测**（换模型 → 生成 → 打分 → 上板对比），并知道每个坑长什么样、怎么绕。
> 与 `_不进飞书_agent经验与历史/0707_新模型接入评测_端到端总纲.md`（速查版）互补——这份是**详版**。
> 配套问题清单：`_不进飞书_agent经验与历史/0708_评测管线问题与现状.md`；打分侧原理：同目录 `0708_机器打分可靠性排查与内容分修复.md`。

---

## 0. 全局图 & 两个工程

```
生成侧 xhx_agent_v3                          打分侧 benchmark                    展示
────────────────────                         ────────────────                   ──────
① 探活端点                                                                        
② 改 2 处模型配置                                                                  
③ run_batch_and_export.py  ──→ output/<batch>/<case>/{result.jsonl,deck html}
④ build_benchmark_eval.py  ──转换──→ /data/.../industry_v2_<VER>/ (打分输入)
⑤                                    run_from_config.py ──→ results/<run>.jsonl
⑥                                    recompute_overall + generate_summary
⑦ runs.json 登记 ─────────────────────────────────────────→ 8770 对比看板
```

- **生成侧根目录**（下称 `$ROOT`）：`/home/gui-5d025-2/zyy/xhx_agent_v3`
- **打分侧根目录**（下称 `$BENCH`）：`/home/gui-5d025-2/zyy/benchmark`（conda env `ppt-eval`）
- **一键无人值守**：③之后的 ④⑤⑥⑦ 全被 `auto_pipeline.sh` 串起来了，跑批起来后跑它就行（见 §7）。手动分步见 §3-§6。
- ⚠️ **每个模型必须跑两个模式**：**无模板** (`..._v2.jsonl`) + **模板** (`..._v2_template.jsonl`)。两模式在看板是两条独立记录（id 分别 `<标志>_notpl` / `<标志>_tpl`），③④⑤⑥⑦ 全流程都要走两遍（或并行两批）。历史上 dpov2/dpo/…每个模型都是两条。**只跑一条是漏交付**。

### 0.1 异常必须立刻查清、记录并主动反馈（每次新跑批强制）

> **硬规矩：任何“稍微有点不对劲”的现象都算异常。发现后必须立即检查，不能因为任务还能继续、样本还少、怀疑只是偶发，就不说、不记或等全批结束。问题不得藏着掖着。**

异常至少包括：请求超时/重试、连接断开、吞吐明显变慢、DSML/伪工具调用、空响应、工具调用形态漂移、**结构化工具调用的参数 schema 校验失败**、无 HTML、页数不符、占位图/空图片槽、review 要求重写、遮挡/低对比度、分数异常、沙盒目录丢失、进程消失、看板状态与真实进程不一致。列表不是穷举；**只要观察者觉得“有点异常”，就触发下面流程。**

**慢请求也必须反馈（2026-08-14 新增）**：不能因为最终请求成功就把极慢响应当正常。逐请求耗时达到 **120 秒**开始记账，达到 **300 秒**立即形成模型/serving 侧反馈；完成请求数达到 20 后若 **P95≥120 秒**，按系统性长尾反馈。证据至少包含模型与端点、模式、case、request_id、发生阶段、消息轮数、开始/结束时间、耗时、是否重试及最终成功/失败；批次状态和看板必须同时展示 P95/P99/max 与慢请求数量。

**自动确认不得覆盖已钉死模式（2026-08-14 新增）**：批处理 case 已通过 `mode` 或正文明确钉死模板/无模板时，自动确认器必须选择与该模式一致且非“其他/调整”的选项，禁止继续随机选择冲突模式或配色。若仍出现确认冲突，当前 case 必须标注为评测侧污染，不能把其失败直接归因给模型，也不能静默混入正式分数。

每次触发必须在同一个监控周期内完成：

1. **先保现场**：记录模型/checkpoint、端点、时间、模式、case/conv_id、影响数量与原始日志/trace/产物路径；不得先清目录或覆盖旧证据。
2. **立即查因**：至少区分模型/checkpoint、serving/tool parser、Agent 管线、沙盒/宿主基础设施四层；做得到时给同上下文 A/B 或最小复现。不能只写“偶发”“可能网络问题”就结束。
3. **写入本批记录与看板**：说明实际表现、影响范围、已确认事实、未确认边界和下一步；新类型异常补入手册/已知问题扫描，使后续每批自动遵循。
4. **主动给用户一段可直接转发给对应责任方的人话**，不等用户追问。必须先确认模型归属，再决定发给内部模型侧、外部模型维护者、端点/推理框架部署方，还是评测/Agent 管线维护者；**禁止看到模型异常就默认写“请模型侧排查”**。内容必须包含：哪个模型/端点、发生了什么、多少题受影响、期望与实际、关键复现/证据、当前判断偏模型/serving/管线/基础设施哪一层、希望责任方核查什么。技术细节可附后，但第一段必须让非管线开发也能看懂。
5. **证据不够也必须报告**：明确写“已发现异常，当前能确认 X，尚不能区分 Y/Z，正在用 A/B 补证”。禁止因为还没完全归因就保持沉默。

工具参数校验失败另有一条强制要求：日志不能只写“arguments 验证失败”。必须在不记录参数值的前提下，记录 request_id、工具名、失败类型（非法 JSON / 空参数 / 缺必填字段 / 多余字段 / 类型不匹配）、字段路径与重试序号；批次结束统计失败次数、受影响 case 和是否直接导致 0 HTML。非法调用不得执行，但诊断证据也不得随调用一起静默丢弃。

跑批交付检查增加两个必答项：

- `是否发现任何异常：是/否`（“否”也要写检查过哪些信号）；
- `是否需要异常反馈：需要/暂不需要/证据不足但已预警`，并写明**对应责任方**，附可直接转发段落。

**违反本节（发现异常但未分析、未记录、未主动告知）视为跑批流程不合格，即使最终有 HTML 或分数也不能算完成。**

**两个前置依赖**：
- `uv`（生成侧用）：装在 `~/.local/bin`。每个 shell 先 `export PATH="$HOME/.local/bin:$PATH"`。没装则 `curl -LsSf https://astral.sh/uv/install.sh | sh`。
- conda env `ppt-eval`（打分侧用）：`conda activate ppt-eval`。

---

## 1. 数据集与判分网关（固定，不用改）

- **测试集**：`$ROOT/data/added/ppt_testset_industry_balanced_v2.jsonl`（industry-balanced-v2，47 个 case，覆盖多行业多输入类型）。
- **判分网关**：TokenHub Claude **sonnet-4-6**。⚠️ 旧 Gemini 网关（34.96 / cloudsway）**已全部禁用**，别用。跑判分必带这组环境变量：
  ```bash
  WANGBO_CLAUDE_BASE=https://tokenhub.sensetime.com
  WANGBO_CLAUDE_KEY="$(python3 -c 'from config import TOKENHUB_API_KEY;print(TOKENHUB_API_KEY)')"
  GEMINI_MAX_RETRIES=3 GEMINI_REQUEST_TIMEOUT=120 GEMINI3_EVAL_MAX_RETRIES=3
  ```
  （`GEMINI_MAX_RETRIES=0` 是无限重试，会打死端点静默挂住——务必设 ≥1。）

---

## 2.1 模型展示名 vs `/v1/models` 登记 id（强制）

对方给的**文档/对齐用展示名**，经常与端点 `/v1/models` 返回的 `id` **不一致**。两边都可能被 API 接受，但对外文档必须以对方原文为准。

| 用途 | 用哪一串 |
|---|---|
| 飞书/仓库总表 `0724`「模型」列 | **对方原文展示名**（一字不差） |
| `0708` 分析文、`model_analysis.json` 的 `subtitle` | **对方原文展示名**（subtitle 可加「· 无模板/模板」；**看板 label 不加**） |
| `runs.json` 的 `model` | **对方原文展示名**（自家 SenseNova 等一字不差） |
| `runs.json` 的 `label`（8770 芯片文字） | **简洁统一短名**，见下表；**同一模型 notpl/tpl 的 label 必须完全相同** |
| conf `llm.model`、skills HTML `DEFAULT_MODEL` | **对方原文展示名**（若 API 只认登记 id，可双写探测；文档侧仍跟原文） |
| 看板短 id / VERSION / `runs.json.id` / 分数文件名 | 技术短 id（如 `flashv39_step4k_notpl`），**不要**把短 id 写进总表当模型名 |

**`label` 统一规则（看板观感，踩过）**：

| 类型 | `label` 怎么写 | 禁止 |
|---|---|---|
| 自家 / 对方给了长全名 | 用**对方原文全名** | 后缀「全量」、在 label 里再写「无模板/模板」 |
| 外部参照（Opus / GPT / OTTO…） | **简洁统一短名**：`Opus 5`、`Opus 4.7`、`Opus 4.8`、`GPT-5.6 Sol` | `Claude`/`Cloud` 混用、有的带 Claude 有的不带、`(thinking)` 乱加、`全量`、label 里写模式 |
| 模式信息 | 只写在 `mode` 字段（`无模板模式` / `模板模式`） | 同一模型两条 label 一个带「无模板」一个不带 |

**反例（踩过）**：`:169` 的 `/v1/models` 是 `SenseNova-Flash-Lite-20260727-v39-fp8-step4k`，对方原文是 `SenseNova-v6.7-Flash-Lte-20260706-v39-fp8-step4k`（注意 `v6.7`、`Flash-Lte`、日期）。总表/分析/卡**禁止**擅自改成登记 id。看板曾出现 `Claude Opus 5 无模板` vs `Opus 4.7` vs `… 全量` 混排——**禁止**。

**正例**：`:170` 的 dpov1-mtp 原文与 `/v1/models` 一致：`SenseNova-Flash-Lite-20260727-v39-fp8-step4k-dpov1-mtp`。看板 label 就写这一串，notpl/tpl 同文；模式靠 `mode` 分列。

总表模型列**不加** `NEW` /「参照」等标注；分析卡 `tags` 里可以加 NEW。

## 2. 步骤①：探活端点（不做=白跑一批）

新模型给你一个端点地址 + 一个 served model 名（`/v1/models` 里的 `id`，**未必等于模型代号**；展示名规则见 §2.1）。

```bash
M=<served模型名>; EP=http://<ip>:<port>
curl -s $EP/v1/models                              # 看 served 名、max_model_len
# 字符串 content（基线，必须 200）
curl -s -o /dev/null -w "%{http_code}\n" $EP/v1/messages -H 'content-type: application/json' \
  -H 'anthropic-version: 2023-06-01' -H 'x-api-key: dummy' \
  -d "{\"model\":\"$M\",\"max_tokens\":16,\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}"
# 数组 content（agent 实际会发这种；必须 200！）
curl -s -o /dev/null -w "%{http_code}\n" $EP/v1/messages -H 'content-type: application/json' \
  -H 'anthropic-version: 2023-06-01' -H 'x-api-key: dummy' \
  -d "{\"model\":\"$M\",\"max_tokens\":16,\"messages\":[{\"role\":\"user\",\"content\":[{\"type\":\"text\",\"text\":\"hi\"}]}]}"
```
- **数组 content 若 500/400 → 端点没实现 block 数组，agent 每次调用必崩，必须先让模型侧修**（复现见 `0706_checkpoint2200_端点报错复现.md`）。
- 内网禁 ICMP（ping 100% 丢包但端口通）→ **判连通只能用 TCP/curl，不能 ping**。
- 首次 curl 偶发超时(000) 是冷启动，复测两次。

**沙盒探活**（生成链路必须，True 才行）：
```bash
cd $ROOT && export PATH="$HOME/.local/bin:$PATH"
uv run python -c "from tools.sandbox.sdk.client import SandboxClient; print(SandboxClient('http://10.210.0.52:3000',30).health_check())"
```

---

## 3. 步骤②：改模型配置（漏一处 = 大量 render_suspect / 用错模型）

⚠️ **最容易踩的坑：主 LLM、沙箱地址、沙盒内 HTML 模型要一起核对。**

**A. 主 config（agent 主体用）**：复制改名带模型标志
```bash
cd $ROOT
cp conf_v3_zh_flashlite_step4k_20260702.yaml conf_v3_zh_<标志>_$(date +%Y%m%d).yaml
```
编辑新文件的 `llm:` 块（约第 4-12 行）：
```yaml
llm:
  base_url: http://<新端点ip>:<port>     # 主 LLM 端点
  model: <served名>                       # /v1/models 拿到的 id
  provider: anthropic                     # 不动
  api_key: sk-...                         # 端点不校验，占位即可
  max_tokens: 128000
  temperature: 1
  # ⚠️ Flash / 多数模型：别加 thinking 块（litellm 不认 -thinking 模型名会崩）
  # ✅ Claude Opus 5（TokenHub）例外——群内「thinking 开满」须用：
  # thinking: {type: adaptive}
  # output_config: {effort: max}   # low|medium|high|xhigh|max；勿用 type=enabled+budget_tokens
```

**B. 沙盒地址（`sandbox.sandbox_base_url`）**：内网沙箱与公有云沙箱不要混用。

**隧道稳定性硬规则（2026-08-13 新增）**：若主端点依赖 SSH/socat 转发，必须在正式跑批前把隧道做成可自动重连的守护服务，并完成一次真实 chat 请求；**首个 case 发请求后禁止再切换临时隧道到守护服务**。切换会中断已有 TCP 连接，SDK 会进行请求级重试，污染“模型一次调用”的证据。若确实发生，必须记录切换时刻、受影响 request/case、重试次数与恢复时刻；这是评测基础设施异常，不得报成模型异常，也不得为了掩盖而偷偷完整重跑第二批。

**思考配置真实生效硬规则（2026-08-15 新增）**：看板选中 `thinking/reasoning_effort` 不等于已生效。OpenAI 协议下，主 agent 和 HTML 生成/评审子调用都必须通过 `chat_template_kwargs` 传递 `thinking`、`enable_thinking` 和 `reasoning_effort`；禁止把 `xhigh` 放在请求顶层（该端点顶层 schema 只接受 low/medium/high，会直接 422）。看板生成的 HTML 脚本必须锁定该配置，case 内不得通过 `PPT_HTML_LLM_ENABLE_THINKING` / `PPT_HTML_LLM_REASONING_EFFORT` 环境变量降级或改写；若模型尝试覆盖，日志必须记录 `reasoning_override_attempted=true` 且看板报警。正式跑批前必须同时完成：有效值真实请求 200、无效哨兵值被 400 拒绝（证明字段未被忽略）、SDK 请求日志显示最终生效值，以及首个 HTML 子调用的真实请求/响应日志。任一缺失必须拒绝启动或标为配置异常，不得用 UI 展示值代替证据。

**Qwen3.8 输出预算与责任归因硬规则（2026-08-15 新增）**：Qwen 官方模型卡说明 Qwen3.8 默认开启思考，原生档位只有 `xhigh`（默认）/`medium`/`low`；官方同时建议 agent 任务为思考和最终回答预留远大于旧 HTML helper 的输出空间。当前 PPT HTML helper 的历史默认值是 `max_tokens=16384`，对 Qwen3.8 会出现“思考吃满、`finish_reason=length`、正文为空”。因此 Qwen3.8 正式批次的 HTML 单页最大输出必须使用 **128000**（看板现已自动选择并展示，日志必须核对真实 `max_tokens`）；若仍看到 16384，必须拒绝启动。此类 16K 截断首先归因为**评测管线预算不匹配**，不能直接发给内部模型侧。官方模型卡：`https://huggingface.co/Qwen/Qwen3.8-27B`；原始模板证据：`tokenizer_config.json` 第 45-60 行。

**切换思考档位前清残留（2026-08-15 新增）**：停止旧档位批次后，不能只相信看板 `status=stopped`；必须按该任务独有的完整 `--output` 路径扫描并确认 uv/python 子进程均退出，再观察端点 `token_load` 回落，方可启动新档位。若旧 `xhigh` 与新 `medium/low` 并跑，整段延迟/吞吐数据按并发污染处理，不得拿来比较思考档位。

**看板与跑批进程隔离硬规则（2026-08-13 新增）**：8770 看板通过 systemd 运行时必须配置 `KillMode=process`，否则重启看板会把它启动的 notpl/tpl 子进程连同 cgroup 一起杀掉。若发生此类中断：保留原 OUT 和日志，状态标 `interrupted`，只允许在原 OUT 上用 `--resume` 恢复未完成 case；禁止另建一套全量输出冒充“第一次跑”。

| 类型 | 示例 | 注意 |
|---|---|---|
| 内网沙箱 | `http://10.210.0.52:3000` | 沙箱内通常能打到内网 HTML 端点（如 `10.210.9.14:134`） |
| 公有云沙箱 | `http://62.234.119.98:3000` | 沙箱内**打不到**内网 HTML 默认端点；HTML 生成要改成沙箱可达的地址（如 mentor 转发 `http://10.120.4.82:8787`） |

换沙箱后先探活：宿主机 `SandboxClient(...).health_check()`，再进沙箱测目标 HTML 端点（本机能连 ≠ 沙箱能连）。

**C. 沙盒内 HTML 生成模型（生成 deck 页面的实际模型）**：两个文件
```
skills/ppt-no-template-mode/scripts/_html_llm_direct.py   (第 36-37 行)
skills/ppt-template-mode/scripts/_html_llm_direct.py      (第 36-37 行)
```
改 `DEFAULT_BASE_URL` / `DEFAULT_MODEL`：
```python
DEFAULT_BASE_URL = "http://10.210.9.14:114"          # ⚠️ 注意这个端点常和主端点不同！
DEFAULT_MODEL = "flash-lite-v36-fp8-step3k-dpo-v1"
```
> ⚠️ **宿主 `export PPT_HTML_LLM_*` 进不了沙箱**（脚本在沙箱进程里跑，读不到本机环境变量）。手册旧说法“用环境变量覆盖不改文件”对沙箱内 HTML 生成**无效**。
>
> **只想改某一批、不动源仓默认时**：实拷一份 skills（如 `cp -a skills skills_<标志>`），只改副本里上述两个 `_html_llm_direct.py`，config 里设 `skill_registry.skills_dir: skills_<标志>`。不要用软链（打包上传到沙箱时容易踩坑）。
>
> **为什么有两处**：A 是 agent 大脑（规划/工具调用，跑在宿主机），C 是实际把内容渲染成 HTML 页的模型（跑在沙箱）。评测同一个模型时两端点都要沙箱/宿主各自可达；两者不一致会导致"评的是 A 但页是 B 生成的"混淆。

---

## 4. 步骤③：跑全量 47 题（生成）

⚠️ **必须两个模式都跑**：**无模板模式**（testset `..._v2.jsonl`）+ **模板模式**（testset `..._v2_template.jsonl`）。同一个模型/端点用**同一份 config**跑两遍，只换 `--input` 和 `--output` 目录。两模式在看板是两条独立记录（`id` 分别是 `<标志>_notpl` / `<标志>_tpl`），两条都要有分数用户才能看到"模板 vs 无模板"对比。**并行跑没问题**（上次 dpov2 就是两批同时压 `10.210.9.14:115` concurrency=4 各一批，端点扛得住）。
⚠️ **max-turns 用 20**（`batch_run_test.sh` 默认写死 8，重题不够会截断成 done_no_html）。
⚠️ **批次隔离（强制）**：每次正式评测用**全新 OUT 目录** + **独立 VERSION/看板 id**；不要把烟雾 5 题、失败空跑、全量 47 题 `--resume` 进同一目录或共用同一个 `runs.json` id。混批会导致旧 deck 被误扫、看板上标签堆叠、真实失败率看不清。烟雾验证用独立 id（如 `<标志>_smoke_*`），全量用正式 id（如 `<标志>_notpl` / `<标志>_tpl`）；无结果的登记要从看板删掉。

⚠️ **分数文件隔离（强制，防看板污染）**：`scores_jsonl` 路径由 VERSION 决定（`results/industry_v2_<VERSION>.jsonl`），`auto_pipeline` 打分配置是 **`skip_done: true`**——旧 jsonl 里已有的 query 会被跳过，**不会被全量重写**，看板上就会一直挂着烟雾/试跑的陈旧分。因此：
1. 烟雾 / 试跑 **必须**用独立 VERSION（如 `gpt56sol_smoke_tpl`），**禁止**写进正式 `*_notpl` / `*_tpl` 的 jsonl。
2. 若正式 id 曾被试跑写过分数：挂 `auto_pipeline` **之前**把 `industry_v2_<正式id>.jsonl` **整文件 mv 到** `results/bak_*/`（缺文件没关系，跑完会新建）；必要时同步备份/清空同名 `EVAL_ROOT=/data/.../industry_v2_<正式id>`。
3. 正式跑未打完分前：看板可先登记 `run_dir`，但确认对应 `scores_jsonl` **不存在或已清空**，避免半截旧分上板。
4. 看板按数字序号对齐分（`_q7` ↔ `seq_0007` / `prod_*7*`），错挂时优先查是否混入了短序号旧 `query_id`。

**无模板模式**：
```bash
cd $ROOT && export PATH="$HOME/.local/bin:$PATH"
TS=$(date +%Y%m%d_%H%M%S); OUT=output/testset_v2_<标志>_notpl_$TS
nohup uv run python scripts/run_batch_and_export.py \
  --input data/added/ppt_testset_industry_balanced_v2.jsonl \
  --output "$OUT" --config conf_v3_zh_<标志>_$(date +%Y%m%d).yaml \
  --concurrency 4 --max-turns 20 --seed 42 \
  --disable-tools web_search,image_search,image_generation,fetch_url,image_vqa,rerank_texts \
  --disable-skills deep-research > "$OUT.log" 2>&1 &
echo "$OUT"   # 记住这个目录
```

**模板模式**（另开一个窗口，与上面并行跑）：
```bash
cd $ROOT && export PATH="$HOME/.local/bin:$PATH"
TS=$(date +%Y%m%d_%H%M%S); OUT_TPL=output/testset_v2_<标志>_tpl_$TS
nohup uv run python scripts/run_batch_and_export.py \
  --input data/added/ppt_testset_industry_balanced_v2_template.jsonl \
  --output "$OUT_TPL" --config conf_v3_zh_<标志>_$(date +%Y%m%d).yaml \
  --concurrency 4 --max-turns 20 --seed 42 \
  --disable-tools web_search,image_search,image_generation,fetch_url,image_vqa,rerank_texts \
  --disable-skills deep-research > "$OUT_TPL.log" 2>&1 &
echo "$OUT_TPL"
```
> ⚠️ 只有 `--input` 换成 `_template.jsonl`、`OUT` 后缀换成 `_tpl` 这两处不同，config/参数完全一样。两批同时跑对端点没压力（dpov2 就是这么跑的），但 §5-§7 每批都要走一遍，`VERSION` 分别用 `<标志>_notpl` / `<标志>_tpl`。

- 单题 15-20 分钟，47 题 concurrency=4 约 **2.5-4 小时**。
- 进度：`tail -f "$OUT.log"` 或 `tail -f "$OUT/events.jsonl"`。
- 关键参数说明：
  - `--seed 42`：固定随机，复现 ask_user 的随机选项。
  - `--disable-tools`：禁联网/搜图/rerank（用这个禁，别写进数据）。
  - `--disable-skills deep-research`：技能层单独关（disable-tools 管不到）。
  - `--resume`：断点续跑（扫 events.jsonl 跳过已完成 + triage 类）。
  - `--start N --count M`：分批切片跑。
- **产物**：`$OUT/<case>/result.jsonl`（agent 轨迹）+ deck html；`$OUT/batch_summary.json`（终态汇总）；`$OUT/events.jsonl`。

**终态类别**（`batch_summary.json` 里 `terminal_class`）：
| 类别 | 含义 |
|---|---|
| `done` | 成功出 deck |
| `done_no_html` | 跑完但没 HTML 产物（模型没产出/中途停） |
| `render_suspect` | 有产物但渲染可疑（可能空壳/畸形） |
| `infra_failed` | 基础设施错误 |

> ⚠️ **`done_no_html` / `render_suspect` 里，自家模型的失败绝大多数不是管线 bug，而是模型侧「没发出结构化 tool call 就早停」**（error 全为 null、多在 17–460s 早停）。分模型的完整错误模式拆解与原始样例见 `评测任务文档/0708_生成失败showcase_模型侧.md`（4 种模式全列、按模型分开）；机器可读明细 `benchmark_failures_analysis.jsonl`，复现脚本 `scripts/analyze_failures.py`。
> 注意本次失败分析覆盖的批次**跨两个模型家族**（`flashv1_1`=Flash v1.1/checkpoint-2200；`flash4k`/`step3kdpo*`=Flash-lite v36），两家族失败形态不同，别混为一谈。

---

## 5. 步骤④-⑥：转换 + 打分 + 重算（手动分步；一键见 §7）

设 `VER=<标志>`（= runs.json 里的 id = 打分 agent_name，全流程必须一致）。

**④ 转换**（生成产物 → 打分输入格式）：
```bash
cd $ROOT && export PATH="$HOME/.local/bin:$PATH"
uv run python scripts/build_benchmark_eval.py \
  --v2-jsonl data/added/ppt_testset_industry_balanced_v2.jsonl \
  --out /data/gui-5d025-2/benchmark_eval/industry_v2_$VER \
  --version $VER --run-dir "$OUT" \
  --sandbox-root $ROOT/output/sandbox --date $(date +%Y%m%d)
```
> ⚠️ 已知漏洞：转换脚本 `scan_pages` 只判 html 存在、不查空壳（1 字节空页会进打分给污染低分）。暂无自动过滤，注意异常低分 case。

**⑤ 打分**（写 config 再跑）：
```bash
cd $BENCH && conda activate ppt-eval
cat > configs/industry_v2_$VER.yaml << YAML
run_name: "industry_v2_$VER"
description: "新模型 $VER 全量评测"
input:
  input_root: "/data/gui-5d025-2/benchmark_eval/industry_v2_$VER"
  agents: []
output: {results_dir: "results"}
run: {workers: 16, heartbeat_seconds: 12, skip_done: true, no_repair: true, debug: true}
model: {eval_model: "claude-sonnet-4-6"}
v2: {enabled: true, agentic_hard_check: false, constraint_llm: false, substantiveness_eval: false}
pairwise: {enabled: false}
pairwise_visual: {enabled: false}
YAML
WANGBO_CLAUDE_BASE=https://tokenhub.sensetime.com \
WANGBO_CLAUDE_KEY="$(python3 -c 'from config import TOKENHUB_API_KEY;print(TOKENHUB_API_KEY)')" \
GEMINI_MAX_RETRIES=3 GEMINI_REQUEST_TIMEOUT=120 GEMINI3_EVAL_MAX_RETRIES=3 \
python -u run_from_config.py configs/industry_v2_$VER.yaml 2>&1 | tee results/industry_v2_$VER.log
```
> `skip_done:true` 可断点续跑（重跑同命令跳过已判）。
> ⚠️ 内容分可靠性：本项目 2026-07-08 修过"内容分静默虚高"bug（判分网关返回空时被当成 0 条动态检查项，内容分虚高）。判据 `content_eval_dynamic_items==0`。修复后代码会快速重试+失败抛错。若跑的是**修复前的老结果**，内容分不可信，需重判。

**⑥ 重算 overall + summary**：
```bash
cd /home/gui-5d025-2/zyy
python -m benchmark.recompute_overall_jsonl --jsonl $BENCH/results/industry_v2_$VER.jsonl --in-place
python3 -c "import sys;sys.path.insert(0,'/home/gui-5d025-2/zyy');from benchmark.aggregator import BenchmarkAggregator;BenchmarkAggregator(results_dir='$BENCH/results').generate_summary(run_name='industry_v2_$VER')"
```

---

## 6. 步骤⑦：登记 runs.json（让 8770 看板认识新版本）

编辑 `$ROOT/results_dashboard/runs.json`，在 `runs` 数组加一条（**notpl / tpl 各一条，`label` 同文**）：
```json
{
  "id": "<标志>_notpl",
  "label": "<看板短名：自家用对方全名；外部用 Opus 5 / GPT-5.6 Sol 等，见 §2.1>",
  "model": "<对方原文展示名或 served 全名>",
  "mode": "无模板模式",
  "run_dir": "<绝对路径的OUT目录>",
  "sandbox_root": "/home/gui-5d025-2/zyy/xhx_agent_v3/output/sandbox",
  "scores_jsonl": "/home/gui-5d025-2/zyy/benchmark/results/industry_v2_<标志>_notpl.jsonl"
}
```
- `id` 必须 = 打分 agent_name（否则分数对不上不显示）。
- `mode` 填「无模板模式」或「模板模式」；**不要**把模式写进 `label`。
- `label` **不要**加「全量」；同一模型两条 label 必须一字不差（§2.1 / §11.4）。
- dashboard（8770）监听 runs.json + scores 文件 mtime，会**自动 reload**，刷页面即可；改完也可 `GET /api/reload`。
- 多版本共写一个 jsonl 时，用 `scores_agent` 字段区分 agent_name。

**看板地址**：http://10.151.196.17:8770/（进程手动起，改 server.py 后需手动重启：`kill <pid>` 再 `nohup python3 server.py --host 0.0.0.0 --port 8770 &`）。

---

## 7. 一键无人值守（推荐，串起 ④⑤⑥⑦）

跑批（步骤③）起来后，另开：
```bash
cd $ROOT
# 无模板批
VERSION=<标志>_notpl OUT=<OUT无模板目录> nohup bash auto_pipeline.sh > /dev/null 2>&1 &
# 模板批（另起一条，与上面并跑）
VERSION=<标志>_tpl   OUT=<OUT模板目录>   nohup bash auto_pipeline.sh > /dev/null 2>&1 &
tail -f <OUT目录>/auto_pipeline.log   # 看进度（每批各一份）
```
它自动：等 batch_done → 转换 → 打分（tokenhub claude）→ 重算 overall+summary → 上板检查 + 刷生成侧看板。**VERSION 必须 = 步骤⑦的 id**，两条模式各一个 id（`<标志>_notpl` / `<标志>_tpl`）。
前置：runs.json 里两个 id 都已登记，`scores_jsonl` 分别指向 `results/industry_v2_<标志>_notpl.jsonl` / `..._tpl.jsonl`（文件不存在没关系，跑完自动落）。**若这两个路径上已有旧 jsonl，先 mv 备份再挂 pipeline**，否则 `skip_done: true` 会保留陈旧分（见 §4「分数文件隔离」）。

---

## 8. 坑清单（都踩过）

| 现象 | 根因 | 对策 |
|---|---|---|
| 3.6s "done"、0 png、deck 是旧的 | sandbox 混放复用历史 deck | 用独立新 OUT 目录 |
| done_no_html / 截断在准备阶段 | max-turns 8 不够 | max-turns=20 |
| 大量 render_suspect、轨迹 `｜DSML｜` 乱码 | 模型工具调用能力弱，吐畸形 tool call | 是评测结论（模型不达标），非流程 bug |
| 模型吐 `<invoke name=...>` 纯文本 | 弱模型不会结构化 tool call | 同上，评测结论 |
| 数组 content → 500/400 | 端点没实现 block 数组 | 模型侧修端点 |
| ping 不通但服务正常 | 内网禁 ICMP | 用 TCP/curl 判连通 |
| 内容分虚高、新旧模型不可比 | 判分网关返回空被当 0 条动态项 | 已修（重试+抛错）；老结果需重判 |
| html 是 1 字节空壳但进打分 | 转换 scan_pages 不查空 | 待修，注意异常低分 |
| 判分静默挂住不报错 | GEMINI_MAX_RETRIES=0 无限重试打死端点 | 设 ≥1（用 §1 环境变量） |
| 用错模型（评 A 页是 B 出的） | 只改了主 config 没改沙盒 html 模型 | §3 A+C 一起改 |
| 公有云沙箱全 `render_suspect`、0 HTML | HTML 仍打内网默认端点；或宿主 export 的 `PPT_HTML_LLM_*` 没进沙箱 | §3 B+C：换沙箱可达端点；用 skills 实拷改 DEFAULT，别只 export |
| 看板同一模型一堆空标签 | 烟雾/失败批与全量共用或残留 `runs.json` id | 批次隔离；无结果登记及时删 |
| 正式标签上莫名低分/少题分 | 正式 `scores_jsonl` 残留烟雾/试跑；`skip_done` 跳过重写 | §4 分数文件隔离：独立 VERSION；挂 pipeline 前 mv 旧 jsonl |
| 大数据表 case 判分失败 | 超大 xlsx+多页触发模型话痨不输出JSON | 已加 prompt 约束，仍是难点 |
| 打分尾段卡死：心跳「槽内仍在跑」无新 ✓；日志 `ContentEvaluator`/`tokenhub Read timed out (360)` | 高并发（如 workers=16）尾题大包（多页忠实度）堆在 tokenhub 读超时，外层还能重到 6/6 | **杀进程 → 缺题串行补跑**（子集 input + `workers=1`，同 `run_name` 追加 jsonl）；不必干等到 6/6。例：2026-07-27 flashv39 notpl 缺 q1081/1190/1472/1495，见 `0727_flashv39_打分尾题超时备忘.md` |
| 续跑已新增成功套数，但早评分仍按旧失败终态跳过；看板 `generated_n` 增长而 eval 输入数不变 | 上一趟 `batch_summary.json` 在整轮续跑退出前不会更新；转换器若无条件优先读它，会遮蔽更新更晚的 `events.jsonl` | 转换时比较两文件 mtime：`events.jsonl` 更新更晚则按 case 的最新 `case_start`/终态构造实时快照；只有汇总不旧于事件时才读 `batch_summary.json`。修复后先用临时 eval 目录核对新成功 case 已进入，再重启断点评分；不得手改终态或伪造 `batch_done`。2026-08-25 v15-dpo-v1 曾因此显示 44 套、评分入口只识别 42 套。 |
| 自动早打分达到 20 条却反复写 partial summary、无 config/evaldir/scores，`monitor.log` 报 `No such file or directory: 'uv'` | 看板由 systemd 启动，服务 PATH 没有 `~/.local/bin`（后续还可能找不到 conda）；交互 shell 能执行不代表服务能执行 | 启动新批前必须从看板服务环境验证 `uv`、`conda`；看到门槛命中只能称“已触发”，必须同时核对打分进程和 `scores_jsonl` 非空后才称“已有分” |

---

## 9. 结果解读：各维度可靠性

| 维度 | 可靠性 | 说明 |
|---|---|---|
| page_score / hard_check | ✅ 高 | 渲染硬检查，判得准 |
| deck / aesthetic | 🟡 中 | VLM 主观，趋势可信、细排名慎信 |
| content | ⚠️ 修复后可信 | 曾有虚高 bug；dyn=0 的不可信 |
| overall 大档位 | ✅ 可信 | 分档可信；分差<3 慎信 |

机器分盖不住"像不像人做的/审美/专业度" → 用人评补，任务书见 `0708_人工对比观察任务书_轻量版.md`。

---

## 10. 关键文件速查

| 用途 | 路径 |
|---|---|
| 测试集 | `$ROOT/data/added/ppt_testset_industry_balanced_v2.jsonl` |
| 跑批脚本 | `$ROOT/scripts/run_batch_and_export.py`（便捷入口 `batch_run_test.sh`，但默认 max-turns=8 要注意） |
| 主 config 模板 | `$ROOT/conf_v3_zh_*.yaml` |
| 沙盒 html 模型 | `$ROOT/skills/ppt-{no-template,template}-mode/scripts/_html_llm_direct.py` |
| 转换脚本 | `$ROOT/scripts/build_benchmark_eval.py` |
| 打分入口 | `$BENCH/run_from_config.py` |
| 重算 overall | `benchmark.recompute_overall_jsonl` |
| 无人值守 | `$ROOT/auto_pipeline.sh` |
| 看板 | `$ROOT/results_dashboard/server.py`（:8770）+ `runs.json` |

---

## 11. Cursor Agent 执行约定（针对本仓库 Cursor 会话，2026-08-01；2026-08-03 补外部模型复盘）

> 本节是**对 Cursor agent 的强制纪律**，不是给人手动跑批的可选建议。来自 dpov2 / v6.7 / 外部模型夜跑踩坑。与上文步骤冲突时：**以本节为准（仅约束 Cursor agent）**。

### 11.1 最高优先级：尽早上分、看板有数

- **自动上板、上分是第一交付**。用户不该等到你被催问才发现「生成还在跑 / 分数一直空」。
- **不要死等 47/47**。全量常有 1～2 题极难、卡很久；卡死一题**不得**拖住整批打分。
- **早打分（初版锚定）**：当某一模式已有 **≥20** 个 `case_done` 且 `html_pages>0`（或 `done` 终态）时，**立即**对已有产物做一轮转换+打分（同正式 `VERSION` / `scores_jsonl`，`skip_done: true`），让 8770 先出现可对照均分。终态仍挂/保留手册 §7 的 `auto_pipeline` 做齐套补分。
- 初版分要在看板/口头标明口径可用「n=已评分」理解，**禁止**把半程当最终榜去改梯队结论；齐套后再重算。
- 开跑后 agent **主动监控**（不必等用户提）：至少周期性看 `events.jsonl` 进度、`auto_pipeline.log`、分数文件 `n`、看板 `/api/reload` 后的 `scored_n`。
- “已触发打分”不等于“已有分”：必须同时确认 `monitor.log` 无入口错误、`benchmark/configs/industry_v2_<VERSION>.yaml` 与 eval 输入目录已生成、`benchmark/results/industry_v2_<VERSION>.jsonl` 存在且 `n>0`。任一不满足都必须在看板标成评测基础设施异常，不能拿生成期 `ReadTimeout` 猜成打分慢。

### 11.2 外部模型：直接全量 + 监控，不强制烟测

- 外部模型（Opus / GPT / OTTO / TokenHub 等）**默认直接开全量 47×2**，靠监控发现挂零页/配额/工具调用失败。
- **不强制**先 smoke 5 题再全量（用户明确：监控能看出来就直接全量）。若首批连续多题 `render_suspect`/0 HTML，再停批量处置——不是开跑前必须烟测。
- 资源紧时：优先**降 concurrency**、分模式错峰、换可达端点；**禁止**为此发明 healer / 假 `batch_done`。

### 11.3 监控与脚本：只走手册，禁止自造管线

- 正式无人值守**只挂** `auto_pipeline.sh`（§7）。禁止自写 overnight healer、假写 `events.jsonl` 的 `batch_done`、私有 finalize/score 脚本替代手册路径。
- `--resume` / remain 补跑后：**必须检查** `batch_summary.json` 的 `case_total` 是否仍≈全量；若被切片覆盖成 1～十几条，要从 `events.jsonl` 重建后再谈「上板完成」（2026-07-31 dpov2 踩过：分数在、看板像没上）。
- `/data` 只读、转换失败、打分尾题 timeout：按 §8 坑表处理（备份路径 / 串行补分），不要另起炉灶。

### 11.4 看板命名（登记 `runs.json` 时一次写对）

- 严格遵守 §2.1：`label` 简洁统一；`mode` 只承载模板/无模板；自家用对方全名；外部用短名（`Opus 5` 而非混用 `Claude Opus 5`）。
- **禁止**在 label 加：`全量`、`smoke5`（正式条）、`无模板`/`模板` 字样、时有时无的 `Claude`/`(thinking)`。
- 改完 `runs.json` 后 `GET /api/reload`，确认芯片文字一致。

### 11.5 验收「这一批算上板了」的最低检查（做完再告诉用户）

1. `auto_pipeline.log`（或早打分日志）出现打分完成 / summary ok  
2. `industry_v2_<VERSION>.jsonl` 存在且 `n` 合理增长  
3. `batch_summary.case_total` 不是被 remain 写烂的小数  
4. `/api/index` 里该 id 的 `avg_score.scored_n` 与文件一致；用户硬刷新 8770 能看见  

缺任一项 = **未交付**，不要说「已经上板」。

### 11.6 外部模型夜跑复盘纪律（2026-08-01～08-03，强制）

> 来源：Kimi / Sonnet / Gemini / DeepSeek / Flash-lite(:188/:199) 同周夜跑。**翻过的错不得再犯**；与 §2～§3、§8、§11.1～11.5 冲突时，仍以「先手册、再动手」为准。

#### A. 开跑前探活：接得通 ≠ 能跑完

- §2 基线（`/v1/models`、字符串 content、**数组 content**、沙箱 health、沙箱→端点）**必须做完**再挂批。
- **额外必测**（agent 真会发、基线 curl 测不到）：
  1. `tool_choice: {"type":"none"}` + 任意 dummy `tools` → 必须 200。若 400 且文案含 `Incompatible tool choice param ... 'none'`：**报模型侧修端点**，**禁止**把 `provider` 改成 `openai` 绕过（§3 写明 Flash/lightllm 系 `provider: anthropic` **不动**）。同类坑见 `0706_checkpoint2200_端点报错复现.md`。
  2. 若配置带 thinking / `output_config.effort`：用与 conf **完全相同**的参数打一枪，确认有 **content 或 tool_calls**，不是只有 thinking / 空 body。
  3. 推理模型（Kimi 等）：`max_tokens` 过小会把额度吃进 `reasoning_content`、正式 `content` 为空——探活用足够大的 `max_tokens`，conf 勿照抄 16/32。
- 连续多题开局即 `other_error` / 空响应 / 0 HTML：**先停批查端点与参数**，不要靠 `--resume` 空转。

#### B. 监控口径：新 HTML 优先，不看假进度

- **第一指标**：本趟新增非空 `htmls/page_*.html`（或 events 里 `deck_html_pages>0` / 终态 `done`）。
- **禁止**把 tqdm `ok`、`case_done`、`done_no_html` 当成「生成成功」。`done_no_html` = 跑完但无页（常是早停/空响应/假交付），**不是**可上榜产物。
- 早打分（§11.1）只覆盖有 HTML 的题；口头/看板必须带 `n=`，**禁止**用半程 overall 改梯队结论。
- 单题卡住（沙箱 `ReadTimeout`、无新 events 数小时）：**杀该题 + remain 续跑**，conc=1 时队头阻塞会拖死整条线。禁止干等；禁止自造假 `batch_done`（§11.3）。

#### C. 参数与协议：先手册 / 厂商口径，禁止凭感觉拧

- **协议以当前任务配置和实际 API 为准，不得根据模型名猜测。** 当前自动化默认是 `provider: openai` + `/v1/chat/completions`，对应 `tool_choice: "none"`；只有配置明确为 `provider: anthropic` + `/v1/messages` 的旧端点，才使用 `tool_choice: {"type":"none"}`。禁止把两种形态混用，也禁止为绕错擅自改 provider。
- Flash / 多数本地 lightllm：不要无依据加 thinking 块；保持任务生成时已经探活通过的 provider，不在跑批中途切协议。
- Claude（TokenHub）thinking：按群内/手册例外用 `adaptive` + `effort`；`effort: max` 若出现「有 thinking、无 content/tool_calls、usage 很大」→ **空响应**，应降 effort 或换口径，**禁止**一刀切关 thinking 导致大批早停假 `done_no_html`。
- 大改 agent 行为（硬 trim 上下文、关 thinking、改分类掩失败）**必须先和用户对齐**再改；评测口径污染比少跑几题更糟。
- Gemini 等：`max_tokens` 过小会截断；改 conf 后确认主 LLM 与 HTML skill 两边一致。

#### D. 终态分类与 `--resume`（看懂再续跑）

| 终态 | 含义（评测侧） | `--resume` |
|---|---|---|
| `done` | 成功且有非空 page HTML | 跳过 |
| `done_no_html` | 成功路径结束但无页（常早停） | 跳过（不自动重跑） |
| `infra_failed` | 沙箱/连接层 | **会重跑** |
| `other_error` | 其它（含「LLM 调用失败已达最大重试」、协议 400 等） | **跳过** |

- events 里常无 `error` 字段：真因在 `result.response` / assistant 文本。定性前**先读原文**，勿把协议硬伤说成「模型不会做 PPT」。
- 协议/参数类 `other_error`（如 `tool_choice=none`）：端点修好后需 **remain 列表重跑**，单靠 `--resume` **不会**捡回这些题。

#### E. 看板命名与展示名

- 遵守 §2.1 / §11.4。自家 served id / 对方原文怎么给就怎么写。
- **禁止**自加中文品牌前缀（如「商汤日日新」）、`全量`、`smoke`、模式字样进 `label`。

#### F. 磁盘与 `/tmp`（运维自伤禁令）

- 批跑输入 jsonl、stdout、monitor、pid **不要只放** `/tmp` 裸目录；用项目下 WD 或带白名单的专用目录。清盘前列出活批 OUT / WD / remain 路径。
- **禁止**对 `/tmp` 无差别 `rm -rf`。磁盘满会出现 tqdm `ENOSPC`、进程假活（futex 挂死）——先腾空间再杀僵复活批。
- `No space left on device` 不一定是磁盘满：若原文同时出现 `inotify watch`，必须核对磁盘容量/inode和 `fs.inotify.max_user_*`，按内核监听配额异常记录；服务仍 active 也不能不报。
- sandbox 可删 **过期**目录；**禁止**删仍在跑的 `conversation_id` 对应目录。

#### G. 对外（模型侧）怎么报

- 协议缺实现（数组 content / `tool_choice=none` 等）：给 **复现 curl + HTTP 码 + 原文**，标明「网关/翻译层，非权重」。
- 限流 429、通道 503、空响应：附时段、model id、是否可重试；与「工具格式不会」分开报。

### 11.7 齐套恢复与假活判定（2026-08-25 新增，强制）

> 来源：`v15-dpov1-2235` 与 `v41-step3k-code-dpov1`。本节修复三类流程漏洞：把服务 `active` 当作任务在推进、误以为 `--resume` 会补所有失败、局部补跑退出码为 0 就宣布齐套。完整现场见 `0806_284b问题反馈_模型侧/0825_v15_v41_code_齐套恢复流程缺陷.md`。

#### A. “完成”的唯一生成口径

- 每个模式仍以 **尽量补到 47 个唯一 case** 为运行目标；单个 case 的真实成功定义为最新有效终态 `done` 且 `deck_html_pages>0`。但业务验收不硬卡 47：有效生成达到约四十套（当前自动门槛为 `>=40`）即可进入最终验收，前提是未成功题及原因完整披露。只看 `case_done=47`、tqdm 100%、`batch_done`、进程退出码 0、服务 `active`，任何一个都不能证明收敛。
- `done_no_html`、`render_suspect`、`content_incomplete`、`other_error`、`infra_failed`、零页 `done` 和只有 `case_start` 没有终态的 case，全部计入“待处置”，不得藏在成功率或阶段性分数里。
- append-only `events.jsonl` 必须按 case 取**最新一次 start/done 关系**去重；新 `case_start` 晚于旧 `case_done` 时，该 case 当前为 `running`，不能继续展示旧成功/失败终态。
- 最终评分与“可验收”标识必须满足：该模式有效生成数 `generated_n>=40`，并且评分的 case 集合覆盖全部有效生成 case；不能只比较数量，因为“旧失败题有分、新补成功题漏分”时两个数字也可能恰好相等。通过 benchmark eval 目录的 `query_info.txt`（`Query序号`）把评分 `query_id` 反查到原始 `case_id` 后做集合差，`generated_case_ids - scored_case_ids` 必须为空。不能把固定 `47` 当评分完成门槛，也不能出现生成 46 套、只评 40 套却标最终。`scored_n` 必须按结果 JSONL 的唯一 `query_id` 统计，禁止直接使用物理行数；后端重启或多 monitor 可能重复派发 evaluator，评分入口必须用 task/mode 级跨进程锁。若已有重复记录，先备份，再按 `query_id` 保留最后一条并原子替换，之后才可续评和重算汇总。

#### B. 续跑前先做终态盘点，禁止盲跑 `--resume`

1. 输出每个模式的：真实 HTML 成功数、各终态数量、当前在途 case、最后一个事件时间、最后一次真实模型响应时间。
2. 对每个非真实成功 case 查原日志上下文，至少区分：模型/协议错误、模型端点连接错误、沙箱工具错误、渲染异常。events 里的 `error=null` 不能作为“无错误”。
3. 明确 `--resume` 的实际策略：它只自动捡 `infra_failed`/killed；`other_error`、`render_suspect`、`done_no_html` 等默认会跳过。**日志出现“resume pass exit=0”不等于恢复完成。**
4. 对确认需要重跑但会被跳过的 case，使用仓库统一的、可审计的重排工具或 remain 子集，把它们显式放回待跑集合；禁止临时手改为 `done`、伪造 `batch_done` 或用旧 sandbox 产物补成功数。重排日志必须记录原终态、case id、原因和时间。
5. 每一趟补跑结束后重新执行 A 节验收。恢复守护默认继续向 47 套补齐；若业务按 `>=40` 收口，则必须同时满足评分覆盖全部有效生成套数，并在看板保留未成功题与归因，不得仅按 shell `rc=0` 退出或隐去缺口。

#### C. 假活不是“慢”，满足证据就立即切换恢复链路

- 进程存在、systemd `active/running`、日志文件偶尔增长，都只能证明进程没退出。若增长内容只是周期性重试/超时，不能算业务进展。
- 满足下列组合即可判假活：单 case 长时间无新终态，且日志连续出现同一基础设施失败（例如沙箱每 1200 秒 `ReadTimeout`，连 `echo ok`/`print("alive")` 都失败），期间没有新增 HTML、有效工具结果或阶段完成信号。不要用“模型可能思考很久”解释工具端超时。
- 无人值守批次若日志停在 `ask_user` 返回 `waiting_for_user_input`，之后数分钟没有自动确认消息、模型请求、工具调用或网络连接，也属于流程假活，不是模型思考慢。先确认仅该 runner/该模式受影响，再终止卡住的 runner，由唯一恢复守护按原 OUT 重排当前 case；验收必须看到新的 `batch_start`、该 case 的新 `case_start`/新 `conv_id`，以及后续真实模型响应。不得整批覆盖已完成 case，也不得让退避睡眠掩盖已确认的无人值守卡死。
- 切换前先确认旧 runner 的所属 service/进程树。**停止整条旧 owner service，再让唯一一个恢复守护接管**；禁止只杀叶子 PID，导致旧 shell 自动重启并与新守护双跑同一 OUT。
- 恢复守护等待旧 runner 退出期间，也必须自身受监控。守护 `failed`/`SIGKILL` 后要立即重建；不能因为原始批次还在跑就放着不管。

#### D. “已经重启”的验收证据（四项缺一不可）

1. 旧 owner service 已停止或确认不会再次拉起；
2. 原 OUT 中出现新的 `batch_start`，参数与正式口径一致；
3. 待跑 case 出现新的 `case_start`；
4. 日志出现至少一个真实 `[llm-response]`，随后有有效工具结果/HTML/终态继续增长。

只有 `systemd-run` 返回成功、PID 存在或端口 TCP 可连，不得对用户说“已重启、在跑”。TCP 探活也不得替代真实推理响应；批中按正式请求日志验收，避免额外探针污染口径。

#### E. 本次已钉死的错误模式

- `v41-step3k-code-dpov1` notpl 的 10 个 `other_error`：2026-08-24 19:48 左右主模型端点 `10.210.9.14:247` 连续 `Connection error`、重试耗尽，属于 serving/连接层，不是 PPT 内容或格式问题；旧 `--resume` 因跳过 `other_error` 永远补不回来。
- 同批最后 1 个长期 `running`：沙箱 `62.234.119.98:3000` 对最小工具调用连续 1200 秒 `ReadTimeout`，日志增长只是超时轮询，属于假活。2026-08-25 11:27 停旧 owner service 后，完整恢复守护从原 OUT 以并发 4 重启 11 题。
- `v15-dpov1-2235` 的旧恢复守护曾被 `SIGKILL`，而原 notpl 仍在推进；正确处置是保留原 runner、立即重建“退出后接管”的守护，同时单独补模板非真实成功题，不能误杀仍有真实响应的主批。
### 优先模型不得依赖看板 `featured` 自动发现

高频迭代期维护 `automation/portfolio_targets.json` 作为显式验收清单。监控程序必须同时扫描：看板 `featured` 运行、目标清单中已归档的历史运行、以及目标清单中尚无 `runs.json` 映射的模型。后两类也必须上监控账，分别标为失败待归因或缺端点/模型 ID/run 映射；禁止因为未登记、被归档或只有单模式而静默消失。

外部 API 补跑必须核对 `/v1/models` 返回的精确 model ID 和渠道身份。名称或 checkpoint 不一致时必须建立独立结果项，不得把不同后端结果合并进“官方 API”或“自部署”分数。验收仍按有效生成 case 集合与评分 case 集合逐题一致；请求完成数、JSONL 行数或同名近似模型均不能代替该检查。

### DeepSeek Flash 工具参数兼容边界（2026-08-25）

- `bailian/deepseek-v4-flash-0731` 曾连续把 `create_subtask.todo` 输出为字符串数组，而仓库工具 schema 明确要求字符串；三次校验重试后会落为零页 `other_error`。这属于可定位的工具参数类型偏差，不能笼统记成“模型生成失败”，更不能让 `--resume` 静默跳过。
- 运行时仅允许一项无损兼容：工具名严格等于 `create_subtask`、且 `todo` 是非空纯字符串数组时，用换行连接为单个字符串，并写 warning 日志。混合类型、对象数组、其它字段或其它工具一律不得自动修复，继续由 schema 校验拒绝。
- 兼容上线必须先跑单测，再按原 OUT 显式重排零页终态；重启验收仍须满足本节 D 的四项证据，并确认日志出现归一化记录后工具实际执行成功。
