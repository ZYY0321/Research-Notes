# PPT 批量测试 Quickstart

把「换个模型/换个数据，跑一批 PPT 测试集，出个 dashboard 对比效果」做成标准流程。
本文覆盖：数据在哪/要改什么、配置在哪/改什么、skill 改什么、怎么启动、输出/日志在哪、
怎么改输入输出、以及踩过的坑。

> 所有路径以工程根 `/home/wangbo/Workspace/Prjs/xhx_agent_v3_test2` 为基准（下称 `$ROOT`）。

---

## 0. 全景（一次测试的数据流）

```
输入 jsonl (data/ppt-testset/*.jsonl)
   │  每行一个 case：query + 可选附件 files
   ▼
scripts/run_batch_and_export.py  ← 启动脚本 batch_run_test.sh 调它
   │  · 读 config（llm / vlm / sandbox / skills）
   │  · 附件 files 上传到沙盒
   │  · 主 agent 跑 → 触发 ppt skill → skill 脚本在【沙盒内】调模型生成 HTML
   ▼
远端沙盒 10.210.0.52:3000  ──生成 deck──►  拉回本地 sandbox_retrieve_path
   │
   ├─ 每个 case 目录 output/<run>/<id>/ (main.json / subtask_*.json / result.jsonl)
   ├─ 事件流 output/<run>/events.jsonl，汇总 output/<run>/batch_summary.json
   ├─ deck 页面 output/sandbox/<conv_id>/<deck>/htmls/page_*.html
   └─ 全量日志 logs/run_batch_and_export/agentv3_concurrent_*.log
   ▼
scripts/build_dashboard.py  →  output/<run>/dashboard.html（自包含，双击即看）
```

**关键认知**：生成 HTML 的模型调用发生在 **沙盒内部**，走 skill 里的 `_html_llm_direct.py`；
主 agent 的模型调用在本机走 config 的 `llm`。**这是两处独立的模型配置，换模型要两处都改**。

---

## 1. TL;DR（换模型跑一批 + 出 dashboard）

```bash
cd /home/wangbo/Workspace/Prjs/xhx_agent_v3_test2

# ① 改主 agent 模型：conf_v3_zh_claude_c_new_sd_3004.yaml 的 llm 块（见 §3）
# ② 改沙盒内 HTML 生成模型：两个 _html_llm_direct.py 的 DEFAULT_*（见 §5）
# ③ 数据附件改基址（19 个 case 带附件，指向本工程副本）
python3 scripts/retarget_testset_files.py \
  --input data/ppt-testset/ppt_testset_industry_balanced_v2.jsonl --write

# ④ 探活沙盒 + 沙盒能不能调新模型（强烈建议先做，见 §8）
# ⑤ 启动批跑
bash batch_run_test.sh          # 打印 OUT=output/testset_v2_YYYYmmdd_HHMMSS PID=...

# ⑥ 跑完出 dashboard
python3 scripts/build_dashboard.py --run-dir output/testset_v2_YYYYmmdd_HHMMSS
#   → output/testset_v2_YYYYmmdd_HHMMSS/dashboard.html  双击打开
#   多版本/多模型长期并排对比：用常驻服务 results_dashboard（见 §7.5）
```

---

## 2. 数据：在哪、要改什么

- **测试集 jsonl**：`data/ppt-testset/ppt_testset_industry_balanced_v2.jsonl`（47 个 case，含 `.bak`）
- **附件实体**：`data/PPT-Testset-industry-balanced-v2/<id>/files/*.pptx|xlsx|pdf|docx`（本工程内已有副本）

**每行 case 的字段**：

| 字段 | 说明 |
|---|---|
| `id` | case 唯一标识（如 `seq_1006` / `prod_xxxx`），输出目录、事件都按它 |
| `query` | 用户诉求文本。附件类 case 里只写"参考附件…"，**不含具体路径** |
| `files` | 附件的**绝对路径**列表（可空）。会被上传到沙盒供 agent 读 |
| `mode` | 生成模式：`html`=无模板 / `template[:<名>]`=模板 / 省略=skill 默认 |
| `category` | 行业（dashboard 分组用） |
| `name` | 展示标题（dashboard 卡片标题） |
| `source` | 来源标注，跑批不使用 |

### ⚠️ 附件 `files` 的地址要改

jsonl 里的 `files` 现在是**旧工程绝对路径** `…/xhx_agent_v3/data/PPT-Testset-industry-balanced-v2/…`。
本工程有同名副本，跑本工程务必把基址改到本工程（否则读的是另一份数据）。用现成脚本：

```bash
# 预览（默认 dry-run，会校验新路径是否都存在）
python3 scripts/retarget_testset_files.py --input data/ppt-testset/ppt_testset_industry_balanced_v2.jsonl
# 写回（自动备份 .bak）
python3 scripts/retarget_testset_files.py --input data/ppt-testset/ppt_testset_industry_balanced_v2.jsonl --write
# 自定义基址：--old-prefix /a/b --new-prefix /c/d
```

> 47 个 case 里有 19 个带附件、共 27 条 files 路径。`query` 不含路径，**不用改 query 文本**。

---

## 3. 配置文件：在哪、改什么

- 路径：`$ROOT/conf_v3_zh_claude_c_new_sd_3004.yaml`
- 启动脚本用 `--config` 显式指定它（不是默认 `conf_v3_zh_claude_c.yaml`）。

### 3.1 换主 agent 模型 —— `llm` 块

```yaml
llm:
  base_url: http://10.210.9.11:671        # 模型端点
  model: flash-lite-v36-fp8-step3k         # 模型名（可 curl {base_url}/v1/models 查）
  provider: anthropic                      # anthropic → 打 {base_url}/v1/messages
  api_key: <占位即可，本地端点不校验>
  max_tokens: 128000
  temperature: 1
```

- 该本地 lightllm 端点**同时支持** OpenAI `/v1/chat/completions` 与 Anthropic `/v1/messages`。
  `provider: anthropic` 时 litellm 打 `/v1/messages`；若某端点只认 OpenAI，改 `provider: openai` 即可。
- litellm 会把自定义 `model` 名**透传**给 base_url，所以模型名不必是"真 Claude 名"。

### 3.2 换沙盒 —— `sandbox` 块

```yaml
sandbox:
  sandbox_base_url: "http://10.210.0.52:3000"                 # 沙盒地址
  sandbox_timeout: 1200.0
  sandbox_absolute_path: "/mnt/data"                         # 沙盒内工作根
  sandbox_retrieve_path: "/home/wangbo/…/xhx_agent_v3_test2/output/sandbox"  # deck 拉回本地的落盘根
```

> **`sandbox_retrieve_path` 要指到本工程 `output/sandbox`**（早期它曾指到旧工程，导致产物落到别处、dashboard 找不到页面）。

### 3.3 其它辅助模型（按需改）

`vlm` / `audio_basellm` / `mem0.llm` / `fetch_url` / `image_generation` 等各自带 base_url+key，
默认指向 `tokenhub.sensetime.com`。只测主链路时**通常不用动**；要整体换供应商才逐个改。

### 3.4 注意
- 配置里 key 是明文，别把带真 key 的配置往外发。
- 每次跑会把**当次生效配置**快照到 `output/<run>/_effective_config.yaml`，事后可查这批到底用了什么。

---

## 4. 换模型时"沙盒内 HTML 生成"也要跟着换（重点）

生成每页 HTML 的 LLM 调用发生在**沙盒里**，走 skill 脚本，**不读 config 的 `llm`**，也**读不到本机环境变量**（见 §9 坑 1）。所以换模型必须改 skill 里的默认常量：

改这两个文件的 `DEFAULT_BASE_URL` / `DEFAULT_MODEL`：

- `skills/ppt-no-template-mode/scripts/_html_llm_direct.py`
- `skills/ppt-template-mode/scripts/_html_llm_direct.py`

```python
DEFAULT_BASE_URL = "http://10.210.9.11:671"      # 与主模型同一端点即可
DEFAULT_MODEL = "flash-lite-v36-fp8-step3k"
```

- 该脚本按 **Anthropic `/v1/messages`** 格式发（`x-api-key` + `anthropic-version`），端点需支持这个路由（本地 lightllm 支持）。
- 无模板/模板两种模式各一份，**跑哪种就改哪份；两种都跑就都改**。
- 失败会抛 `LLMDirectError`（不静默回退），日志里 grep `html_page_generate` / `LLMDirectError` 能看到。

---

## 5. 启动脚本：在哪、参数

- 便捷入口：`$ROOT/batch_run_test.sh`（后台 nohup 跑，打印 `OUT=… PID=…`）
  - 里面固定了：`--input …v2.jsonl`、`--config …_sd_3004.yaml`、`--concurrency 16`、
    `--max-turns 8`、`--seed 42`、`--disable-tools web_search,image_search,image_generation,fetch_url,rerank_texts`、
    `--disable-skills deep-research`。要改跑法就直接改这个脚本，或照抄命令手敲。
- 真正的 runner：`scripts/run_batch_and_export.py`。常用参数：

| 参数 | 作用 |
|---|---|
| `--input` | 测试集 jsonl（必填） |
| `--output` | 结果根目录（必填，脚本里用带时间戳的 `output/testset_v2_<ts>`） |
| `--config` | YAML 配置（默认 `conf_v3_zh_claude_c.yaml`，本流程显式传 `_sd_3004`） |
| `--concurrency` | 并发 case 数（脚本用 16） |
| `--max-turns` | 每 case 最大续跑轮数（默认 8） |
| `--seed` | RNG 种子（给了可复现 ask_user 的随机选项） |
| `--disable-tools` | 逗号分隔工具名，全批生效（禁用工具的正道，别写进数据） |
| `--disable-skills` | 逗号分隔技能名，从 allowlist 摘除（关 deep-research 必须用这个，disable-tools 管不到技能层） |
| `--start` / `--count` | 切片分批：`--start 0 --count 20`（0 基，按有效行序） |
| `--resume` | 断点续传：扫 events.jsonl 跳过"已完成+triage 类"，只重跑 infra_failed/killed |
| `--verbose` | 调试用，日志回打 stdout（会冲歪进度条），默认关 |

---

## 6. 输出 / 日志：都在哪

一次跑（`output/testset_v2_<ts>/`，下称 `<run>`）：

| 路径 | 内容 |
|---|---|
| `<run>/events.jsonl` | 事件流：`batch_start` / `case_start`(id→conv_id) / `case_done`(带 terminal_class/duration/turns/pages) / `case_error` / `batch_done` |
| `<run>/batch_summary.json` | 跑完的汇总：run 元信息 + 每 case `results`（含 `conv_id` / `terminal_class` / `deck_scan_root` / `deck_quality`） |
| `<run>/run.log` | 进度条 + 收尾（`batch_run_test.sh` 的 nohup 输出重定向到这） |
| `<run>/stdout_capture.log` | 仓内裸 print（document_parser 等） |
| `<run>/_effective_config.yaml` | 本批实际生效配置快照 |
| `<run>/<id>/main.json` `subtask_*.json` `result.jsonl` | 每个 case 的主/子任务轨迹 |
| `output/sandbox/<conv_id>/<deck>/htmls/page_*.html` | **deck 页面产物**（`sandbox_retrieve_path` 拉回的） |
| `logs/run_batch_and_export/agentv3_concurrent_<ts>.log` | **agentv3 + LiteLLM 全量 INFO/DEBUG 日志**（只写文件，排查模型/工具调用看这个） |

**terminal_class 含义**：`done`=成功有图 / `done_no_html`=只文字交付没起 deck /
`render_suspect`=起了 deck 但 0 页 / `content_incomplete` `other_error` / `infra_failed`=沙盒连接层挂（可 `--resume` 重跑）。

实时盯进度：
```bash
tail -f output/<run>/events.jsonl                                  # case 级事件
tail -F logs/run_batch_and_export/agentv3_concurrent_<ts>.log      # 模型/工具全量日志
```

---

## 7. Dashboard：生成 & 对比

```bash
python3 scripts/build_dashboard.py --run-dir output/testset_v2_<ts>
#   默认输出 output/<run>/dashboard.html，双击即看
```

- 数据源优先 `batch_summary.json`（跑完最准），没有则回退 `events.jsonl`（跑一半也能出）。
- **页面 HTML 直接内嵌成 `data:` URL**（自包含单文件），双击 / 任意 HTTP 服务下都不会 404，
  也不受中文目录名影响。相关模板：`scripts/dashboard_template.html`（复刻线上样式 + 内嵌改造）。
- 对比多批：对每个 run 各生成一份 dashboard，并排开两个浏览器 tab 看即可。
- 参数：`--run-dir`（必填）、`--input`（默认测试集）、`--retrieve-root`（默认 `output/sandbox`；
  跑的产物落在别处时指过去）、`--template`、`--out`。

---

## 7.5 长期对比服务 `results_dashboard`（多版本并排对比，推荐）

§7 的 `build_dashboard.py` 是**单次跑批**的自包含 html（一份一 tab，适合发人/离线看）。
要**长期挂着、多版本/多模型并排对比同一个 case**，用 `results_dashboard/` 这个常驻服务更顺手。

- 代码：`$ROOT/results_dashboard/`（`server.py` 纯标准库零依赖 + `runs.json` 配置 + `install-service.sh`）
- 访问：本机 **http://127.0.0.1:8770/** ；局域网其他设备 **http://<本机IP>:8770/**（服务绑 `0.0.0.0`，`hostname -I` 查 IP；**无鉴权**，同网段可见）

### 两种视图

| 路由 | 用途 |
|---|---|
| `#/`（总览首页） | 所有已登记版本的成功率 / 终态分布 / 页数 / 耗时汇总表，点行进单次总览 |
| `#/run/<id>` | 单次总览：KPI + 图表 + 全部 case 卡片（缩略图），点卡片弹层逐页看大图 |
| `#/compare?case=<id>` | **跨版本对比**：选一个 case，**勾选要对比的版本**（默认前 2 个），并排看逐页产物差异 |

> 对比模板 vs 无模板、opus vs flash：进 `#/compare`，上面勾选那几个版本，下拉/翻页切 case 即可。

### 加一次新跑批到对比里（关键操作）

编辑 `results_dashboard/runs.json` 的 `runs` 数组，加一条，然后点页面右上「↻ 刷新」或 `curl -s http://127.0.0.1:8770/api/reload`（改 runs.json 后下次请求也会自动重载）：

```json
{
  "id": "tmpl_flash_0702",                 // URL 里的唯一短标识
  "label": "模板模式全量 (flash-lite v36)",  // 展示名
  "model": "flash-lite-v36-fp8-step3k · template",
  "run_dir": "/abs/.../output/testset_v2_20260702_180650",  // 必填：某次 output/testset_* 目录
  "sandbox_root": "/abs/.../output/sandbox"                  // 可选：见下
}
```

- 服务读该 run 的 `batch_summary.json` + 输入 jsonl（取 query/category/name），按每个 case 的
  `deck_scan_root` **递归**发现 `page_*.html`，整套 deck 目录（含背景图 `htmls_png/`、`assets/`）
  原样托管——所以模板背景、配图都能正常渲染。
- **`sandbox_root`（可选，防数据搬家）**：batch_summary 里记的是绝对 deck 路径，一旦数据被移动就失效；
  给了 `sandbox_root` 后，服务会退回用 `sandbox_root/<conv 目录名>` 重新定位。搬数据只改这一处。
- `runs.json` 是**机器相关的**（绝对路径），已 gitignore；仓库里提交的是 `runs.example.json` 模板。
  首次部署：`cp runs.example.json runs.json` 后按本机路径改。

### 起服务 / 运维（systemd --user，开机自启 + 保活）

```bash
cd $ROOT/results_dashboard
cp runs.example.json runs.json      # 首次：改成本机路径
./install-service.sh                # 默认 0.0.0.0:8770（局域网可见）；只本机：./install-service.sh 8770 127.0.0.1

systemctl --user status  ppt-dashboard    # 状态
systemctl --user restart ppt-dashboard    # 改了 server.py 后重启（enable --now 不会重启在跑的服务！）
journalctl --user -u ppt-dashboard -f     # 日志
```

- `Restart=always` + 已开 linger：进程挂了自动拉起，注销 / 重启后仍在跑。
- 误判纠正：批量的 `_compute_deck_quality` 会把「deck 嵌在子目录、标记文件在上层」的情况误报 0 页
  `render_suspect`（如某些 case 实际有图却标失败）；本服务用递归发现真实页数，此时卡片显示绿色
  「done ✓ 纠正」徽章。

---

## 8. 换模型/换沙盒前，先探活（省得白跑一批）

```bash
# ① 沙盒通不通（返回 True 即活）
python3 - <<'PY'
import sys; sys.path.insert(0,'.')
from tools.sandbox.sdk.client import SandboxClient
print(SandboxClient("http://10.210.0.52:3000",30).health_check())
PY

# ② 新模型端点在不在、什么格式
curl -s http://10.210.9.11:671/v1/models
# Anthropic 路由能不能出文本（skill 走这个）
curl -s http://10.210.9.11:671/v1/messages \
  -H 'content-type: application/json' -H 'anthropic-version: 2023-06-01' -H 'x-api-key: dummy' \
  -d '{"model":"flash-lite-v36-fp8-step3k","max_tokens":256,"messages":[{"role":"user","content":"say PONG"}]}'

# ③ 【最关键】沙盒内部能不能调到新模型（skill 就在沙盒里跑）
#    进沙盒 run_code，复刻 _html_llm_direct 的调用，能回 PONG 就稳。
```

> ③ 一定要做：本机能连模型 ≠ 沙盒能连模型。之前正是先验证了"沙盒→模型"这条路才敢开跑。

---

## 9. 注意事项 / 踩过的坑

1. **沙盒内读不到本机环境变量**。`_html_llm_direct.py` 支持 `PPT_HTML_LLM_*` 环境变量覆盖，但
   脚本在沙盒里跑、`load_env` 在本仓其实不存在，env 传不进去 → **换模型只能改 `DEFAULT_*` 常量**（§4）。
2. **两处模型要一起换**：本机主 agent（config `llm`）+ 沙盒内 HTML 生成（skill 常量）。漏一处就是"半换"。
3. **`sandbox_retrieve_path` 必须指向本工程 `output/sandbox`**，否则 deck 落到别处、dashboard 扫不到页面。
4. **retrieve 目录按 `conv_id` 区分、会跨 run 共存**。`conv_id` 带随机后缀（如 `batch_seq_0115_f3bc50`），
   同 `id` 不同 run 不冲突；但 runner 早期按 `batch_<id>_*` 前缀兜底找 deck 可能**误命中旧 run 的同名 case**。
   dashboard 按 `deck_scan_root`/精确 conv_id 取，相对更准；发现某 case 页数对不上先查是不是拿到了旧目录。
5. **dashboard 别再用外部文件引用**。历史上 404 就是 iframe 指了外部/相对路径 + 经 HTTP 打开 + 中文目录名；
   现在改成 `data:` URL 内嵌，彻底规避。页面总量大（几十 MB+）时再考虑换回相对路径 + 从 `output/` 起服务。
6. **禁用工具/技能走命令行**，不要写进数据：工具用 `--disable-tools`，技能用 `--disable-skills`（技能层
   disable-tools 管不到，例如 deep-research 必须用 `--disable-skills`）。
7. **附件路径**：换工程/换机器跑，先 `retarget_testset_files.py` 把 `files` 基址对齐，别让它读到另一份数据（§2）。
8. 配置/脚本里有明文 key，分享前先脱敏。

---

## 10. 常见"我想改 X"速查

| 想改 | 改哪 |
|---|---|
| 主 agent 模型 | `conf_…_sd_3004.yaml` 的 `llm`（§3.1） |
| 沙盒内 HTML 生成模型 | 两个 `_html_llm_direct.py` 的 `DEFAULT_*`（§4） |
| 沙盒地址 | `conf` 的 `sandbox.sandbox_base_url`（§3.2） |
| 产物落盘位置 | `conf` 的 `sandbox.sandbox_retrieve_path`（§3.2） |
| 换测试集 / 改 case | 换 `--input` jsonl；改字段见 §2 |
| 附件换地址 | `scripts/retarget_testset_files.py`（§2） |
| 并发 / 轮数 / 种子 | `batch_run_test.sh` 里的 `--concurrency` / `--max-turns` / `--seed`（§5） |
| 只跑一部分 | `--start` / `--count`（§5） |
| 关某工具 / 某技能 | `--disable-tools` / `--disable-skills`（§5、坑 6） |
| 断点续传 | `--resume`（同 `--input/--output`）（§5） |
| 生成 / 换 dashboard（单次自包含） | `scripts/build_dashboard.py --run-dir <run>`（§7） |
| 多版本长期对比服务 | `results_dashboard/`：加 run 编辑 `runs.json` + `/api/reload`；起服务 `install-service.sh`（§7.5） |
```
