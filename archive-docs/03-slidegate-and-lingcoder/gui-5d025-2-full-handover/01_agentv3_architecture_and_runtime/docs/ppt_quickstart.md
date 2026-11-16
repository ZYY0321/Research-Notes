# PPT 生成 · Quick Start

一份"按这页操作能跑出一份 PPT"的最短手册。聚焦 PPT 生成主链,不重复 `README.md` / `docs/agentv3.md` / `CLAUDE.md` 里已经写过的运行时/状态层细节。

## 这是什么

基于 AgentV3 调度的 PPT 生成流水线,由四个 skill 组成:

| skill | 作用 |
|-------|------|
| `ppt-entry` | 入口路由,根据 query 选择下面三种模式之一 |
| `ppt-template-mode` | 模板模式 — 套用 `templates/<name>/` 现成视觉框架,产物落到 `htmls/page_xxx.html` |
| `ppt-no-template-mode` | 无模板模式 — 模型自由设计版式,带 review/rewrite 自检环 |
| `ppt-creative-mode` | 创意模式 — 单页 HTML,不切分多页结构 |

跑批入口是 `agents/agentv3/tests/manual_multi_turn_cli.py`,支持 `ask_user` 暂停 → 终端选择 → 续跑,无需启动后端/前端。

## 环境准备

```bash
uv sync
```

配置文件级联(取第一个存在的):

1. 环境变量 `AGENT_CONFIG_PATH`
2. 环境变量 `CONFIG_PATH`
3. `conf_v3_zh.yaml`(默认,本地常用)
4. `conf_v3_zh_claude.yaml`(Claude 模型组合)
5. `conf_v3.yaml` → `conf.yaml`

> `conf_v3_zh*.yaml` **含 API key**,在 `.gitignore` 里被 `**/*.yaml` 全局拦截。改之前先备份,**不要直接提交**。

**模板目录约定**:用模板模式时,模板路径必须落在 sandbox 内,通常是 `/mnt/data/skill/templates/<name>/`。该目录需要包含 `tag_gen_results.json`(模板布局标注)和 `htmls/`(每页 HTML 骨架)。

## 单次生成

### 模板模式

```bash
uv run agents/agentv3/tests/manual_multi_turn_cli.py \
  --config conf_v3_zh_claude.yaml \
  --query "制作一份2026世界杯参赛队伍介绍PPT,要有世界杯相关的图片,用/mnt/data/skill/templates/dark-purple 这个模板,总页数4页。"
```

要点:

- query 里直接给绝对的模板路径,agent 会路由到 `ppt-template-mode`。
- 中途遇到 `ask_user` 时终端会打出问题和编号选项,输入数字回车续跑;`todolist_feedback` 类型默认自动批准。
- 模板模式**不会**生成 `review.md`(那是无模板模式的产物)。

### 无模板模式

```bash
uv run agents/agentv3/tests/manual_multi_turn_cli.py \
  --config conf_v3_zh_claude.yaml \
  --query "制作一份2026世界杯参赛队伍介绍PPT,主要是要有世界杯相关的图片,总页数6页。"
```

要点:

- 不写模板路径 → 路由到 `ppt-no-template-mode`。
- 每页生成后会跑 `lint_pages.py` 结构校验 + `html_page_review` 视觉评审,失败页自动 rewrite 一次。
- 产物含 `htmls/page_xxx.html` + `htmls/page_xxx.review.md`。

### 输出在哪 — 三条独立通道

跑一个 PPT case 会同时往**三个解耦的位置**写东西,理解这点对后续分析很关键:

| 通道 | 路径 | 内容 | 谁写 | 何时写 |
|------|------|------|------|--------|
| **Trace JSONL** | 单跑:`results/<timestamp>_<query_slug>/result.jsonl`<br>批跑:`output/<run_name>/<case_id>/result.jsonl` | message_records 事件流 + state 快照 + tool_schemas + subtasks 子树 | `run_demo.save_result` | case 结束时一次性写 |
| **Sandbox 持久化** | `backend/database/<conversation_id>/session_files/`(默认 legacy 路径,可被 conf 里 `sandbox_retrieve_path` 覆盖) | deck 实际产物(`htmls/page_*.html`、`assets/`、`task_pack.json`、`outline.json` 等) | sandbox manager 的 retrieve 流程 | runtime 内任何 retrieve 调用 |
| **SQLite 元数据** | `backend/chatbot.db` | 会话/消息/事件元数据 | `backend/database.py` | **仅走 HTTP/SSE 后端时**;CLI 跑批**不写**它 |

跑批脚本(`ppt_testset_runner`)结束时还会把 sandbox 持久化目录 mirror 一份到 `output/<run_name>/<case_id>/`,所以你跑批后,**trace + deck 文件会在同一个目录**下;单跑(`manual_multi_turn_cli`)则需要自己去 `backend/database/<conversation_id>/` 找 deck 文件。

### 渲染成 PNG 看效果

仓库自带渲染脚本(批量渲染 `<root>` 及子目录里的 HTML 到同级 `screenshot/`):

```bash
uv run scripts/capture_ppt_html_screenshots.py --root <deck_dir>
```

> 该脚本目前不在 git 索引里(`scripts/` 在 `.gitignore` 中被全局拦截),按需从仓库内拷贝或问负责人获取。

### 拆 OpenAI 训练格式 trace

每个 case 跑完后,`result.jsonl` 里同时存了**主 agent 完整事件流**(`message_records`)+**每个 subtask 的独立对话**(`state.runtime_control.subtasks[N].messages`)+**当时主/子 agent 各自的 tool schemas**(`tool_schemas.main` / `tool_schemas.delegate`)。

用 `scripts/export_trace_to_openai.py` 可以把一份 `result.jsonl` 拆成 N+1 份 OpenAI 训练样本(主 1 份 + 每个 subtask 1 份):

```bash
# 拆单个 case
uv run python scripts/export_trace_to_openai.py \
  --result output/ppt_testset_mini_0427_smoke_html_20260618/seq_0007/result.jsonl \
  --output-dir output/openai_traces

# 拆整个跑批目录下所有 result.jsonl
uv run python scripts/export_trace_to_openai.py \
  --root output/ppt_testset_mini_0427_smoke_html_20260618 \
  --output-dir output/openai_traces
```

输出形状:

```
output/openai_traces/
└── <case_id>/
    ├── main.json              # 主 agent 完整 trace
    ├── subtask_0.json         # 第 1 个子任务
    ├── subtask_1.json
    └── ...
```

每份文件字段:

```json
{
    "case_id": "...",
    "agent": "main" | "subtask",
    "subtask_id": "subtask_0",       // 仅 subtask
    "subtask_kind": "subtask" | "reflect",
    "subtask_title": "无模板模式 阶段 4:资产规划",
    "status": "completed" | "failed" | "stopped" | "waiting_user_input",
    "total_steps": 12,
    "enable_thinking": true,
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "...", "reasoning_content": "...",
         "tool_calls": [{"id": "...", "type": "function",
                         "function": {"name": "read_file", "arguments": {"path": "..."}}}]},
        {"role": "tool", "name": "read_file", "tool_call_id": "...",
         "content": "...", "success": true}
    ],
    "tools": [
        {"type": "function",
         "function": {"name": "read_file", "description": "...",
                      "parameters": {"type": "object", "required": [...], "properties": {...}}}}
    ],
    "metadata": {"source_result_jsonl": "...", "conversation_id": "...", "exported_at": "..."}
}
```

**字段补给链路**(2026-06 起):

- `reasoning_content`(对应 LiteLLM 的 `reasoning_content` / Claude extended thinking 的 `thinking`):由 `BaseLLM._parse_response` 抽出,经 `add_assistant_turn` 写进 `assistant_output.payload.thinking_content`,`compile_messages_for_llm` 重建 LLM context 时贴回 assistant 消息;`BaseLLM._clean_messages` 会在下次 LLM 请求前剥掉(API 不接收),只用于离线导出。子 agent 链路靠 `_to_llm_message` 白名单保留。
- `tools[]`:主 agent 的取自 `tool_schemas.main`(`localized_tools` 全集),subtask 的取自 `tool_schemas.delegate`(`build_delegate_tools` 过滤掉 `create_subtask` / `reflection` / `ask_user` 后的子集)。两份都在 `finalize_session_result` 时落盘。
- `tool.success`:由导出脚本内 `_infer_tool_success` 推断;优先从 `tool_result.payload` 取显式 `success` bool,否则按 `status` 字段、`error`/`exit_code` 等字段、最后是 content 文本里的失败关键词依次回退。

## 跑批 (Testset)

### 测试集 · PPT-Testset-mini-0427

位置:`data/PPT-Testset-mini-0427/`

| 项 | 取值 |
|----|------|
| 用例总数 | 40 条 |
| 带附件用例 | 28 条 |
| 输入模态分布 | 文档与要求 × 17、详细要求 × 6、一句话 × 6、已有 PPT 与资料 × 6、模板与资料 × 5 |
| 场景分布 | 培训教学 × 8、数据分析 × 8、学术演讲 × 6、商业提案 × 5、项目规划 × 5、工作汇报 × 5、述职/竞聘 × 3 |
| 默认 mode | `html`(无模板模式) |

目录结构:

```
data/PPT-Testset-mini-0427/
├── README.md
├── manifest.json          # 全量 40 条
├── manifest_smoke.json    # 3 条 smoke(含 1 带文件)
├── manifest_debug.json    # 1 条 debug
└── seq_<NNNN>/
    ├── meta.json
    ├── query.md           # 喂给 agent 的 prompt(已剥离 <FILE/> 标签)
    └── files/             # 附件目录,仅带文件用例有
```

`seq_*/` 子目录由 `scripts/ppt_testset/build_minset_0427.py` 从源 zip(`data/0427_minset_40_source/0427_minset_40_tasks.zip`,**该 zip 不在 git 仓库,从负责人处获取**)重新生成:

```bash
uv run python scripts/ppt_testset/build_minset_0427.py
```

### 跑批脚本

三个 launcher 都在 `scripts/ppt_testset/`,封装了 `agents.agentv3.tests.ppt_testset_runner` 的常用参数组合:

| 脚本 | 用例数 | 并发 | 用途 |
|------|-------|------|------|
| `run_minset_0427_debug.sh` | 1 | 1 | 单条跑通验证 |
| `run_minset_0427_smoke.sh` | 3 | 3 | 端到端 + 带文件分支不退化 |
| `run_minset_0427_full.sh` | 40 | 4(默认) | 完整批次 |

共用参数:

```
-m | --mode          模式覆盖(默认 html);可选 auto / html / creative / template[:<name>] / manifest
-n | --name          Run name(默认时间戳)
-c | --config        yaml 配置路径(默认 conf_v3_zh.yaml)
-j | --concurrency   并发度
```

例:跑 smoke 改成创意模式

```bash
bash scripts/ppt_testset/run_minset_0427_smoke.sh -m creative -n my_run
```

### Runner 内部行为

`agents.agentv3.tests.ppt_testset_runner` 两阶段:

1. **Phase 1 — 并发跑**:线程池(`--concurrency`,默认 4),每 case 起独立 `conversation_id`,跑 `execute_ppt_test_case`,落 `result.jsonl` 到 `<output_dir>/<case_id>/`。跑完镜像 `backend/database/<conversation_id>/session_files/` 内容到 case 目录方便归档。
2. **Phase 2 — 顺序评估**:对每 case 跑六个检查项:

   | 检查项 | 验什么 |
   |--------|-------|
   | `ask_user_checks` | 期望 ask_user 是否触发,问题 id 是否全 |
   | `trace_checks` | 必出/禁出 trace 关键词 |
   | `artifact_checks` | 必出/禁出文件(如 `task_pack.json` `outline.json`) |
   | `mode_checks` | 模式专属约束(模板模式禁 review、无模板禁 `template_map.json`、创意禁 `*.html`) |
   | `content_checks` | `outline.json` 页数、`task_pack.ppt_mode` 等 JSON 字段值 |
   | `process_checks` | `<process>` 标签协议是否合规(必出/禁出 process 目标、配对、bad-format) |

   产物 `<output_dir>/summary.md`(人读) + `summary.json`(机读)。

常用 runner 直调:

```bash
# 子集
uv run python -m agents.agentv3.tests.ppt_testset_runner \
  --manifest data/PPT-Testset-mini-0427/manifest.json \
  --cases seq_0007,seq_0115 \
  --output-dir output/my_subset

# 仅复评(不重跑,基于已有 result.jsonl)
uv run python -m agents.agentv3.tests.ppt_testset_runner \
  --manifest data/PPT-Testset-mini-0427/manifest.json \
  --output-dir output/ppt_testset_mini_0427_smoke_html_20260618_123456 \
  --eval-only

# 列出会跑的 case 但不执行
uv run python -m agents.agentv3.tests.ppt_testset_runner \
  --manifest data/PPT-Testset-mini-0427/manifest_smoke.json \
  --dry-run
```

`--mode-override` 是全局兜底覆盖(每 case manifest 自己的 `mode` 字段被这个值取代),会以"指令后缀"形式追加到原 prompt 末尾,不动 `query.md` 文件本身。

## 常见坑

- **找不到 deck**:evaluator 先看 `<output_dir>/<case_id>/` 镜像;若空(老批次),回退到 `backend/database/<conversation_id>/session_files/`。
- **ask_user 续跑后沙盒丢文件**:`manual_multi_turn_cli.py` 和 runner 都默认开 `persist_sandbox_state=True`,跨轮镜像沙盒。如果你魔改 case 关掉了它,deck 会丢。
- **模板路径写错**:模板路径必须是 sandbox 内绝对路径(默认 `/mnt/data/skill/templates/<name>/`),且必须含 `tag_gen_results.json` + `htmls/`,缺一项 skill 会回退到无模板/失败。
- **批次产物太大**:`output/ppt_testset_*/` 不在 git 内,自行清理。
