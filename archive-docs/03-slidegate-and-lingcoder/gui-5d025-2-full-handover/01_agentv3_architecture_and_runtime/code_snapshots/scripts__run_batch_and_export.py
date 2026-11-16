#!/usr/bin/env python3
"""Batch runner + OpenAI trace 导出一体化 CLI。

把"从 JSONL 喂 case → 并发跑 → 自动处理 ask_user 续跑 → 落 result.jsonl →
当场拆 OpenAI 训练格式 trace"合到一个脚本里,避免分两步跑、避免散落各处的临时
runner。

## CLI

    uv run python scripts/run_batch_and_export.py \\
        --input  <input.jsonl> \\
        --output <output_dir> \\
        [--config conf_v3_zh_claude_c.yaml]   # 默认见下
        [--concurrency 4] \\
        [--seed N] \\
        [--max-turns 8] \\
        [--disable-tools web_search,image_search,image_generation,fetch_url,image_vqa,rerank_texts] \\
        [--disable-skills deep-research] \\
        [--start 0 --count 500]     # 分批切片
        [--resume]                  # 断点续传:只重跑 infra_failed + killed(见下「断点续传 / 自愈」)

过夜自愈别手搓循环,直接用 `scripts/run_batch_loop.sh <input> <output> <hours> [其它参数]`
(外层反复 --resume + sleep,沙盒挂自动等、恢复接着跑,收敛即停)。

## 禁用工具 / 技能(启动参数,作用于整批 —— 不要再写进数据)

- `--disable-tools`：逗号分隔的工具名(= conf 里 `tools:` 的 key),对整批所有 case 生效。
  合法名:web_search / image_search / fetch_url / image_vqa / rerank_texts / image_generation 等。
  ⚠️ 拼错的名字会**静默失效**(disable_tools 对未知名 fail-open),脚本会校验并告警。
  **不要**禁用 create_subtask / execute_code / execute_shell_command / read_file / write_file /
  todolist_* / reflection —— 会直接打断 PPT 流程。
- `--disable-skills`：逗号分隔的技能名,从本批 `skill_registry.allowlist` 摘除(写一份临时
  `<output>/_effective_config.yaml`,不改原 config)。**deep-research 是技能不是工具,
  disable_tools 关不掉它**——要禁深度研究必须用 `--disable-skills deep-research`。

## JSONL schema(每行一个 case)

    {
        "id": "<必填,case 唯一标识,会成为输出目录名>",
        "query": "<必填,用户 prompt>",
        "mode": "<可选,钉死生成模式:html=无模板 / template[:<模板名>]=模板(默认 dark-gold) / 缺省=skill默认无模板>",
        "files": ["<可选,本地附件绝对路径>", ...],
        "ask_user": {
            "answers": {"qid1": "value1", ...}                  // 可选,显式回复
        },
        "conversation_id": "<可选,默认自动生成 batch_<id>_<rand6>>"
        // disable_tools: 仍兼容此字段(与 --disable-tools 取并集),但推荐用启动参数,别绑数据里
    }

## 模式钉死(mode 字段)—— 不再靠随机 ask_user 选模式

- `mode` 翻成「query 后缀」(复用 ppt_testset_runner.resolve_mode_suffix),模型据此直接定模式、跳过模式 ask_user。
- 取值:`html`(无模板) / `template` 或 `template:<模板名>`(模板,模板在沙盒 /mnt/data/skill/templates/<名>/) / 缺省或 `auto`(让 skill 默认,即无模板)。
- **`creative` 已下线**(本地出不了图):传 creative 会被拒收并退化为默认;ask_user 兜底随机也会过滤掉"创意"选项。

## ask_user 续跑(关键,不能直接 supports_ask_user=False)

- 主流程会自然触发 ask_user(PPT 入口缺 config 参数等),不能强制不回。
- 每题取值优先级:
    1. JSONL 里 `ask_user.answers[qid]` 显式给的
    2. 题自带 `options` → **`random.choice(options).value`**(给训练数据加多样性)
    3. **开放题(没 options)= 流程异常,该 case 直接失败丢掉**,error="open_ended_question_in_flow"
- `interaction_type == "todolist_feedback"` 直接 `decision: "approve"`(plan 待批默认通过)
- 续跑上限 `--max-turns`(默认 8)。超了标 `max_turns_exceeded`。

## 随机性 / 复现

- `--seed N` 给了 → 每个 case 的 RNG 用 `Random(f"{N}::{case_id}")` 派生,
  同 seed + 同 id 永远拿到同一组随机答案。
- 不给 → 用系统熵,每次跑不一样。
- 并发安全:每个 case 拿独立 RNG 实例,不共享。

## 断点续传 / 自愈(终态分类,扛沙盒成片宕机)

每个 case 结束算一个 `terminal_class`(从 `result.success`+`result.error`+deck 派生,不看有没有 case_done):
  - `done`           成功且有非空 page HTML
  - `done_no_html`    成功、无 HTML 且没起 deck —— 合法文字/大纲交付
  - `render_suspect`  成功、起了 deck 却 0 页/全空页 —— 疑似 render bug
  - `infra_failed`    error 命中沙盒/连接层(ConnectionError/Max retries/ReadTimeout…)
  - `content_incomplete` max_turns_exceeded / open_ended_question_in_flow
  - `other_error`     其它
写进 events 的 case_done / case_error 事件;`--resume` 扫 events 取每个 id **最后一条** terminal_class:
**跳过** done/done_no_html/render_suspect/content_incomplete/other_error,**只重跑** `infra_failed` +
killed(只 start 没终态)。→ 确定性失败不会被反复空跑;沙盒掉线会被重跑。退出码:本趟还有 infra_failed→1,否则 0。
配 `run_batch_loop.sh` 外层循环即过夜自愈:沙盒挂→该趟全 infra_failed(秒返)→sleep→下趟重跑;恢复→done→不再跑;
全 done/triage 后 rerun 集空、退出码 0、循环收敛。`--resume-skip-started` 是激进档:连 infra/in-flight 也跳(OOM 绕坑用)。

## 产物位置(重要)

deck 实际产物落在 config `sandbox.sandbox_retrieve_path/<conv_id>/result/pptid_*/htmls/page_*.html`,
**不** copy 进 case 目录、**不读** backend/database。质量判定(html 页数)按 conv_id 去那里读;html 仅作质量
字段,**不卡 done**(完成与 html 解耦)。事后统计/筛重跑用 `scripts/stat_batch_results.py`。

## 输出布局

    <output_dir>/
    ├── batch_summary.json           # 整批汇总(terminal_breakdown / 每 case 起止/ask_user 选择/OpenAI trace 数/error)
    ├── events.jsonl                 # 进度事件流(case_start/case_done(带 terminal_class)/case_error/batch_done)
    ├── stdout_capture.log           # 仓内裸 print 兜底(document_parser 等绕过 logger 的输出)
    └── <case_id>/
        ├── result.jsonl             # 原始 trace(message_records + state + tool_schemas 全在;含 thinking_content)
        ├── main.json                # OpenAI 主 agent trace
        └── subtask_*.json           # OpenAI 子任务 trace
    # 注:deck 的 HTML/图片产物不在这里,在 sandbox_retrieve_path/<conv_id>/ 下。
    # stat_batch_results.py 另写 stat_report.json / stat_report.csv / rerun_ids.txt。

## 默认配置

`--config` 默认按顺序找:`AGENT_CONFIG_PATH` env > `conf_v3_zh_claude_c.yaml`(缓存
和 thinking 都开)。绝对路径或相对项目根路径都接受。

## 日志输出

默认情况(干净进度条模式):
- agentv3 / LiteLLM 的 INFO/DEBUG 日志**只写文件**(`logs/run_batch_and_export/agentv3_concurrent_*.log`),不打 stdout/stderr。
- runner 自己的 JSON 事件(case_start/case_done/...)只写 `<output_dir>/events.jsonl`,**不打 stdout**。
- **仓内裸 print**(`document_parser._poll_parser_result` 的"当前状态: ..."等绕过 logger 的输出)被 `sys.stdout` 重定向兜到 `<output_dir>/stdout_capture.log`,**不打终端**。
- stderr 上只剩 tqdm 进度条 + 启动时的 tail 命令提示。

加 `--verbose`:恢复传统行为,所有日志/事件/裸 print 同时打 stdout。调试时用(进度条会被冲歪)。
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import os
import random
import sys
import threading
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import yaml  # noqa: E402

from agents.agentv3.core import build_agent_components, run_single_case  # noqa: E402
from agents.agentv3.run_agent import setup_logger  # noqa: E402
from agents.agentv3.tests.ppt_testset_runner import (  # noqa: E402
    extract_pending_ask_payload,
    resolve_mode_suffix,
)
from run_demo import save_result  # noqa: E402
from src.utils import ctx  # noqa: E402
from src.utils.config_utils import load_yaml_config  # noqa: E402

# sibling script
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from export_trace_to_openai import export_one as export_openai_traces  # noqa: E402


DEFAULT_CONFIG = "conf_v3_zh_claude_c.yaml"
DEFAULT_CONCURRENCY = 4
DEFAULT_MAX_TURNS = 8

# 无人值守批处理:从根上防"自由文本 <response> 提问"这个静默致命点——
# 批量里没有真人,模型若把问题写进普通回复(而非 ask_user),会话直接 idle、harness 无法续答 → 0 产物却记成功。
# 故强制:能自决的一律走默认直接继续;确需确认只能用 ask_user(会被自动确认),不许把问题写进普通回复。
_AUTONOMOUS_SUFFIX = (
    "\n\n【自动化批处理模式·无人值守】本次为批量无人值守生成,没有真人会回复你。"
    "凡可由你自行决定的选择(模式/模板/风格/页数/配色等)一律采用合理默认,直接继续到底,"
    "**禁止把问题写进普通回复(<response>)向用户提问、禁止停下来等用户输入**;"
    "确有必须由用户拍板的事项,只能用 `ask_user` 工具(会被自动确认),严禁用自由文本代替提问。"
    "目标:一口气把 PPT 做到逐页产物为止。"
)


# ---------------------------------------------------------------------------
# 进度 / 日志 / 事件输出(干净进度条模式的核心:静音 stdout/stderr 日志、事件写文件)
# ---------------------------------------------------------------------------

_EVENTS_FH: Optional[TextIO] = None
_STDOUT_CAPTURE_FH: Optional[TextIO] = None
_VERBOSE: bool = False
_EVENTS_LOCK = threading.Lock()


def _emit(event: Dict[str, Any]) -> None:
    """JSON 事件落 <output_dir>/events.jsonl;`--verbose` 时也回 stdout。

    取代之前散落的 `print(json.dumps({...}), flush=True)`。线程安全。
    """
    line = json.dumps(event, ensure_ascii=False)
    with _EVENTS_LOCK:
        if _EVENTS_FH is not None:
            _EVENTS_FH.write(line + "\n")
            _EVENTS_FH.flush()
        if _VERBOSE:
            print(line, flush=True)


def _mute_console_logging(verbose: bool) -> None:
    """干净模式:把 root logger 上写 stdout/stderr 的 StreamHandler 全摘掉(FileHandler 保留),
    LiteLLM 自家 logger 也降到 WARNING。verbose=True 时跳过,保留原行为。"""
    if verbose:
        return
    root = logging.getLogger()
    for h in list(root.handlers):
        # FileHandler 继承自 StreamHandler,必须显式排除
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler):
            stream = getattr(h, "stream", None)
            if stream in (sys.stdout, sys.stderr):
                root.removeHandler(h)
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.WARNING)


def _resolve_log_file_from_root_logger() -> Optional[str]:
    """从 root logger 反查 FileHandler 的实际文件名(setup_logger 用 basicConfig 装的)。"""
    for h in logging.getLogger().handlers:
        if isinstance(h, logging.FileHandler):
            return getattr(h, "baseFilename", None)
    return None


def _redirect_stdout_to_capture(capture_path: Path, verbose: bool) -> None:
    """非 verbose 时把 sys.stdout 重定向到 capture 文件,兜住仓内 100+ 处裸 print
    (主要是 tools/multimodal_file/document_parser.py 等),避免它们冲歪 stderr 上的进度条。

    `_emit` 在 verbose 模式下才打 stdout,默认模式不打——所以 redirect 不会污染 events 流。
    tqdm 在 stderr,跟这无关。verbose 时跳过此函数,保留 stdout = 终端。
    """
    if verbose:
        return
    global _STDOUT_CAPTURE_FH
    capture_path.parent.mkdir(parents=True, exist_ok=True)
    # line-buffered(buffering=1),让 tail -F 实时看到
    _STDOUT_CAPTURE_FH = capture_path.open("a", encoding="utf-8", buffering=1)
    sys.stdout = _STDOUT_CAPTURE_FH


def _print_log_locations(log_file: Optional[str], events_file: Path, stdout_capture: Optional[Path]) -> None:
    """进度条之前把 log/事件流路径 + tail 命令打到 stderr,省得用户事后翻。"""
    lines = ["", "实时 tail(另开窗口看进度细节):"]
    if log_file:
        lines.append(f"  tail -F {log_file}              # agentv3 + LiteLLM 全量日志")
    lines.append(f"  tail -F {events_file}              # runner 事件流(case_start/done/...)")
    if stdout_capture:
        lines.append(f"  tail -F {stdout_capture}              # 仓内裸 print(document_parser 等)")
    lines.append("")
    print("\n".join(lines), file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# 工具 / 技能禁用（启动参数，作用于整批；不再绑定在每行数据里）
# ---------------------------------------------------------------------------

def _parse_csv(value: Optional[str]) -> List[str]:
    """'a, b ,c' -> ['a','b','c']；空/None -> []。"""
    if not value:
        return []
    return [x.strip() for x in str(value).replace("，", ",").split(",") if x.strip()]


def _validate_disable_tools(names: List[str], conf: Dict[str, Any]) -> None:
    """对照 conf['tools'] 的合法 key 校验 --disable-tools；未知名只告警不阻断。

    disable_tools 对未知名是 fail-open(静默当无事)，所以这里主动报出来，避免拼错却以为关了。
    """
    valid = set((conf.get("tools") or {}).keys())
    unknown = [n for n in names if n not in valid]
    if unknown:
        print(
            f"[warn] --disable-tools 含未知工具名 {unknown}，这些不会生效(disable_tools 对未知名静默失败)。"
            f"\n       合法工具名: {sorted(valid)}",
            file=sys.stderr, flush=True,
        )


def _missing_ppt_runtime_files(
    conf: Dict[str, Any],
    cases: List[Dict[str, Any]],
    *,
    project_root: Path = PROJECT_ROOT,
) -> List[Path]:
    """返回当前批次会用到、但在专用 skills 目录中缺失的 PPT 运行文件。

    页面批处理脚本会直接 import ``_html_llm_direct.py``；过去专用 skills
    目录只带了旧 ``__pycache__``、漏掉源码，直到 case 跑到页面阶段才报错，
    造成整批长时间 0 HTML。这里把检查前移到任何 case 启动之前。
    """
    runtime = conf.get("runtime") or {}
    registry = runtime.get("skill_registry") or {}
    if not runtime.get("enable_skill_registry", True) or not registry:
        return []

    skills_dir_raw = str(registry.get("skills_dir") or "skills").strip()
    skills_dir = Path(skills_dir_raw)
    if not skills_dir.is_absolute():
        skills_dir = project_root / skills_dir

    modes = {str(case.get("mode") or "html").strip() for case in cases}
    needs_template = any(mode.startswith("template") for mode in modes)
    needs_notpl = any(not mode.startswith("template") for mode in modes)

    required: List[Path] = []
    if needs_notpl:
        scripts = skills_dir / "ppt-no-template-mode" / "scripts"
        required.extend([
            scripts / "_html_llm_direct.py",
            scripts / "html_page_generate_batch.py",
            scripts / "html_page_review_batch.py",
        ])
    if needs_template:
        scripts = skills_dir / "ppt-template-mode" / "scripts"
        required.extend([
            scripts / "_html_llm_direct.py",
            scripts / "html_page_generate_batch.py",
        ])
    return [path for path in required if not path.is_file()]


def _find_allowlist(conf: Dict[str, Any]) -> Optional[List[str]]:
    """定位 runtime.skill_registry.allowlist（返回可原地修改的 list 引用，找不到返回 None）。"""
    node = conf
    for key in ("runtime", "skill_registry", "allowlist"):
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node if isinstance(node, list) else None


def _write_effective_config_without_skills(
    conf_path: Path, disable_skills: List[str], output_dir: Path
) -> Path:
    """生成一份去掉指定 skill 的临时 config（从 allowlist 摘除），返回临时 config 路径。

    skill 是技能层，disable_tools 管不到；从 skill_registry.allowlist 摘除后，该技能的 SKILL.md
    不会打包上传到沙箱，技能阶段无法执行（deep-research 即如此被真正关掉）。不改原 config。
    """
    # load_yaml_config 有进程级缓存且返回共享对象——必须 deepcopy 后再改,否则污染缓存里的原 config
    conf = copy.deepcopy(load_yaml_config(str(conf_path)))
    allowlist = _find_allowlist(conf)
    if allowlist is None:
        print(
            "[warn] 配置里找不到 runtime.skill_registry.allowlist，--disable-skills 无法生效",
            file=sys.stderr, flush=True,
        )
        return conf_path
    want = {s.strip().lower() for s in disable_skills}
    kept = [s for s in allowlist if str(s).strip().lower() not in want]
    removed = [s for s in allowlist if str(s).strip().lower() in want]
    not_found = sorted(want - {str(s).strip().lower() for s in allowlist})
    if not_found:
        print(f"[warn] --disable-skills 里这些不在 allowlist(忽略): {not_found}", file=sys.stderr, flush=True)
    if not removed:
        return conf_path
    # 原地替换 allowlist 内容
    allowlist[:] = kept
    output_dir.mkdir(parents=True, exist_ok=True)
    eff_path = output_dir / "_effective_config.yaml"
    eff_path.write_text(yaml.safe_dump(conf, allow_unicode=True, sort_keys=False), encoding="utf-8")
    _emit({"event": "skills_disabled", "removed": removed, "effective_config": str(eff_path)})
    return eff_path


# ---------------------------------------------------------------------------
# ask_user 续跑
# ---------------------------------------------------------------------------

def _build_resume_answers_random(
    payload: Dict[str, Any],
    explicit_answers: Dict[str, Any],
    rng: random.Random,
    pinned_mode: str = "",
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """造一个 resume_answers,options 兜底走 random.choice。

    Returns (resume_answers_or_None, picks_log)。
    picks_log 每条 = {qid, source: explicit|random|missing, value} 进 batch_summary。
    """
    interaction_type = str(payload.get("interaction_type") or "").strip()
    request_id = str(payload.get("request_id") or "").strip()

    if interaction_type == "todolist_feedback":
        return (
            {
                "request_id": request_id,
                "interaction_type": "todolist_feedback",
                "decision": "approve",
                "todo_list": payload.get("todo_list") or [],
            },
            [{"interaction_type": "todolist_feedback", "decision": "approve"}],
        )

    answers: List[Dict[str, str]] = []
    picks: List[Dict[str, Any]] = []
    for q in payload.get("questions") or []:
        qid = str(q.get("id") or "").strip()
        if not qid:
            continue
        value: Any = explicit_answers.get(qid)
        source = "explicit"
        if value is None:
            qtext = q.get("question") or ""
            options = q.get("options") or []
            # 数据集 mode 已经钉死时，参数确认不能再随机选到冲突模式/配色。此前
            # template:dark-green 会随机命中“模板模式（其他配色）”，污染模型评测。
            # 这里先守住模式；模板内优先非“其他/调整”项，具体模板仍以原 query 为准。
            pinned = str(pinned_mode or "").strip().lower()
            if request_id == "ppt_mode.confirm_params" and pinned and options:
                target = "无模板" if pinned == "html" else ("模板" if pinned.startswith("template") else "")
                if target:
                    mode_options = []
                    for opt in options:
                        if not isinstance(opt, dict):
                            continue
                        text = f'{opt.get("label") or ""} {opt.get("value") or ""} {opt.get("description") or ""}'
                        if target not in text:
                            continue
                        if any(word in text.lower() for word in ("其他", "调整", "修改", "creative", "创意")):
                            continue
                        mode_options.append(opt)
                    if mode_options:
                        chosen = mode_options[0]
                        value = chosen.get("value") or chosen.get("label")
                        source = "pinned_mode"
            # 「推进 vs 调整」形态的确认题(大纲确认 / 参数确认 / 模式确认…):一律选"推进"那条,
            # 不要随机、更不能选"需要调整"(选了调整 → agent 等用户补内容 → 自由文本提问 → 卡死)。
            # 这是 q_0012/q_0032 那类卡死的根治:此前只认含"大纲"的题,现在覆盖所有确认题。
            _PROCEED = ("确认", "可以", "开始", "继续", "通过", "采用", "用默认", "approve", "proceed", "go ahead", "ok")
            # 关键:带"调整/补充/修改…"语义的选项一律不算推进——否则"基本可以，我补充几点调整"会因含"可以"
            # 被误判为推进项,一旦选中就进入"用户要微调大纲"分支,反复追问直到 max_turns 失败(正是要避免的循环)。
            _ADJUST = ("调整", "补充", "修改", "重新", "重来", "重做", "再改", "另", "其他", "adjust", "change", "edit", "modify", "revise")
            def _is_proceed(opt: Any) -> bool:
                s = (str(opt.get("label") or "") + str(opt.get("value") or "")) if isinstance(opt, dict) else str(opt)
                low = s.lower()
                if any(a in low for a in _ADJUST):
                    return False  # 含"调整/补充"语义 → 不是推进项,排除(防"基本可以…调整"误选)
                return any(t in low for t in _PROCEED)
            proceed_opts = [o for o in options if isinstance(o, dict) and _is_proceed(o)]
            if proceed_opts:
                chosen = proceed_opts[0]
                value = chosen.get("value") or chosen.get("label")
                source = "confirm_proceed"
            if value is None and options:
                # 安全网:随机前先剔除"创意/creative"选项(creative 已下线,本地出不了图)。
                # 仅对仍残留的旧行/未钉 mode 行兜底——钉了 mode 的行根本不会走到这。
                def _is_creative(opt: Any) -> bool:
                    s = (str(opt.get("value") or "") + str(opt.get("label") or "")) if isinstance(opt, dict) else str(opt)
                    return ("创意" in s) or ("creative" in s.lower())
                pickable = [o for o in options if not _is_creative(o)] or options
                chosen = rng.choice(pickable)
                if isinstance(chosen, dict):
                    value = chosen.get("value") or chosen.get("label")
                source = "random"
        if value is None:
            # 开放题(没 options)= 流程异常,该 case 直接失败丢掉。
            picks.append({
                "qid": qid,
                "source": "open_ended_abort",
                "value": None,
                "question_preview": (q.get("question") or "")[:120],
            })
            return None, picks
        answers.append({"id": qid, "value": str(value)})
        picks.append({"qid": qid, "source": source, "value": str(value)})

    return (
        {
            "request_id": request_id,
            "interaction_type": "ask_user_feedback",
            "answers": answers,
        },
        picks,
    )


def _progress_bar(total: int):
    """返回一个 tqdm 进度条（走 stderr）；tqdm 不可用时返回 None，调用方退化为打印计数。"""
    try:
        from tqdm import tqdm
    except ImportError:
        return None
    return tqdm(total=total, desc="batch", unit="case", file=sys.stderr, dynamic_ncols=True)


def _make_case_rng(global_seed: Optional[int], case_id: str) -> random.Random:
    if global_seed is None:
        return random.Random()
    return random.Random(f"{global_seed}::{case_id}")


_DECK_MARKER_FILES = ("task_pack.json", "info_pack.json")


# 沙盒产物持久化根(= config sandbox.sandbox_retrieve_path);main 里按 config 设。
# 沙盒现在把 deck 落到 <retrieve_path>/<conv_id>/result/pptid_*/htmls/page_*.html,
# 不再 copy 进 case_dir,也不在旧 mirror 读的 backend/database —— 故质量判定按 conv_id 去这里读。
_SANDBOX_RETRIEVE_PATH: Optional[Path] = None

# infra(沙盒/HTTP 连接层)失败的特征串。基于实测死连接串 `ConnectionError: HTTPConnectionPool(...)
# : Max retries exceeded` 定;**不**匹配裸 "timeout"(避免把含 timeout 的确定性内容错误误判成 infra
# 而每趟空跑),只收连接层 / HTTP 层的明确信号。
_INFRA_ERR_PATTERNS = (
    "ConnectionError", "Max retries exceeded", "HTTPConnectionPool",
    "Connection refused", "Connection aborted", "Connection reset",
    "NewConnectionError", "Failed to establish a new connection",
    "ConnectTimeout", "ConnectTimeoutError", "ReadTimeout", "Read timed out",
    "RemoteDisconnected", "ProtocolError",
    # TokenHub / gateway capacity: should resume when channel recovers
    "No available channel",
    "ServiceUnavailableError",
    "EngineOverloaded",
    "currently overloaded",  # DashScope/Kimi: "The engine is currently overloaded"
    "RateLimitError",
    # Anthropic/Bedrock context / request rejection — must NOT freeze as done_no_html
    "ContextWindowExceeded",
    "prompt is too long",
    "ValidationException",
    "UnsupportedParamsError",
)


def is_infra(err_text: Any) -> bool:
    """err 文本是否是沙盒/连接层 infra 失败(可重跑)。"""
    s = str(err_text or "")
    return any(p in s for p in _INFRA_ERR_PATTERNS)


def classify_terminal(result: Dict[str, Any], deck_quality: Optional[Dict[str, Any]]) -> str:
    """从 result.success + result.error + deck_quality 派生终态(单一可信源,不看有没有 case_done)。

    返回: done | done_no_html | render_suspect | infra_failed | content_incomplete | other_error
      - done            : 成功且有非空 page HTML
      - done_no_html     : 成功、无 HTML 且根本没起 deck —— 合法的文字/大纲交付(不重跑)
      - render_suspect   : 成功、起了 deck 却 0 页 / 全空页 —— 疑似 render bug(triage,不自动重跑)
      - infra_failed     : error 命中沙盒/连接层特征 —— 可重跑
      - content_incomplete: max_turns_exceeded / open_ended_question_in_flow —— 确定性内容失败(triage)
      - other_error      : 其它(triage)
    """
    error = str(result.get("error") or "")
    # success=True 时 error 常为空，RateLimit/超窗文案只在 response 里 → 也要扫，否则会误成 done_no_html
    blob = error + "\n" + str(result.get("response") or "")
    if is_infra(blob):
        return "infra_failed"
    # agent 把 LLM 重试耗尽写成 assistant content 且 success 仍可能为 True
    if any(
        marker in blob
        for marker in (
            "LLM 调用失败，已达到最大重试",
            "LLM 返回空响应，已达到最大重试",
            "工具调用 arguments 验证失败，已达到最大重试",
        )
    ):
        return "other_error"
    success = bool(result.get("success"))
    dq = deck_quality if isinstance(deck_quality, dict) else {}
    html_pages = dq.get("html_pages", 0) or 0
    deck_found = bool(dq.get("deck_dir"))
    if success:
        if html_pages > 0:
            return "done"
        return "render_suspect" if deck_found else "done_no_html"
    if "max_turns_exceeded" in error or "open_ended_question_in_flow" in error:
        return "content_incomplete"
    return "other_error"


def _resolve_deck_scan_root(conv_id: str, case_id: str, case_dir: Path) -> Path:
    """deck 产物实际落地目录: 只认本次 conv_id 的目录 <retrieve_path>/<conv_id>;
    取不到再 fallback 到本 run 自己的 case_dir(兼容旧的 mirror-into-case 行为)。

    ⚠️ 不再按 batch_<case_id>_* 通配兜底: 该通配会匹配到其他 run / 其他日期同 case_id 的
    历史旧 deck, 导致"模型本次没真生成"的题蹭到旧 deck、误报成功并污染打分
    (如 prod_1289b84a 蹭 07-02 旧 deck 报 13 页)。本次没落地 deck 时应扫出 0 页 = 判失败。"""
    root = _SANDBOX_RETRIEVE_PATH
    if root is not None:
        exact = root / conv_id
        if exact.is_dir():
            return exact
    return case_dir


def _compute_deck_quality(scan_root: Path) -> Dict[str, Any]:
    """扫 scan_root 找 deck 根(含 task_pack.json 或 info_pack.json 的目录,或有 htmls/page_*.html),
    报 htmls/page_*.html 和 pages/page_*.png 的非空/空数量。"""
    deck_root: Optional[Path] = None
    candidates: List[Path] = []
    for marker in _DECK_MARKER_FILES:
        candidates.extend(m.parent for m in scan_root.rglob(marker))
    if not candidates:
        # 没有 marker 文件时,用「含 page_*.html 的 htmls 目录」的父目录兜底认 deck
        candidates = [h.parent for h in scan_root.rglob("htmls/page_*.html")]
        candidates = [p.parent for p in candidates]  # htmls -> deck 根
    if candidates:
        # 多候选时挑文件最多 / mtime 最新的(同 ppt_testset_runner 的策略)
        def _score(p: Path) -> tuple:
            files = [x for x in p.rglob("*") if x.is_file()]
            latest = max((x.stat().st_mtime for x in files), default=0.0)
            return (len(files), latest, str(p))
        deck_root = max(set(candidates), key=_score)

    html_pages = 0
    html_pages_empty = 0
    png_pages = 0
    png_pages_empty = 0
    if deck_root:
        htmls = deck_root / "htmls"
        if htmls.is_dir():
            for f in htmls.glob("page_*.html"):
                if f.stat().st_size == 0:
                    html_pages_empty += 1
                else:
                    html_pages += 1
        pages = deck_root / "pages"
        if pages.is_dir():
            for f in pages.glob("page_*.png"):
                if f.stat().st_size == 0:
                    png_pages_empty += 1
                else:
                    png_pages += 1

    return {
        "deck_dir": str(deck_root.relative_to(scan_root)) if deck_root else None,
        "html_pages": html_pages,
        "html_pages_empty": html_pages_empty,
        "png_pages": png_pages,
        "png_pages_empty": png_pages_empty,
    }


def load_cases(input_path: Path) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    with input_path.open(encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                rec = json.loads(stripped)
            except json.JSONDecodeError as exc:
                print(f"[warn] {input_path}:{ln} JSON 解析失败: {exc}", file=sys.stderr)
                continue
            if not isinstance(rec, dict):
                print(f"[warn] {input_path}:{ln} 不是 dict,跳过", file=sys.stderr)
                continue
            if "id" not in rec or "query" not in rec:
                print(f"[warn] {input_path}:{ln} 缺 id 或 query,跳过", file=sys.stderr)
                continue
            cases.append(rec)
    return cases


# 续传跳过(不重跑)的终态类:已完成 + triage 类(确定性失败,重跑只会复现+空烧)。
# 反过来:infra_failed(可重跑)和「只 start 没终态」(killed/in-flight)不在此集 → 会被重跑。
RESUME_SKIP_CLASSES = frozenset({
    "done", "done_no_html", "render_suspect", "content_incomplete", "other_error",
})


def _scan_event_ids(events_path: Path) -> Tuple[Dict[str, str], set]:
    """断点续传:单趟扫旧 events.jsonl,返回 (terminal_class_by_id, started_ids)。

    - terminal_class_by_id:每个 id 最后一条终态事件解析出的 terminal_class(同一 id 跨趟会出现
      多条 infra_failed→…→done,**后者胜**)。事件带 terminal_class 字段就用它;旧事件没有时:
      case_done→"done";case_error→按 error 文本 is_infra 判 "infra_failed"/"other_error"。
    - started_ids:有 case_start 的 id(用于 --resume-skip-started 与 killed 检测)。
    文件不存在或坏行静默跳过。
    """
    cls_by_id: Dict[str, str] = {}
    started: set = set()
    if not events_path.exists():
        return cls_by_id, started
    with events_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:  # noqa: BLE001 — 坏行不阻断续传
                continue
            if not (isinstance(ev, dict) and ev.get("id")):
                continue
            cid = str(ev["id"])
            etype = ev.get("event")
            if etype == "case_start":
                started.add(cid)
            elif etype == "case_done":
                cls_by_id[cid] = str(ev.get("terminal_class") or "done")
            elif etype == "case_error":
                cls_by_id[cid] = str(
                    ev.get("terminal_class")
                    or ("infra_failed" if is_infra(ev.get("error")) else "other_error")
                )
    return cls_by_id, started


# ---------------------------------------------------------------------------
# 单 case 执行(含 ask_user 续跑)
# ---------------------------------------------------------------------------

def run_one_with_ask_user(
    spec: Dict[str, Any],
    components: Dict[str, Any],
    output_dir: Path,
    *,
    rng: random.Random,
    max_turns: int = DEFAULT_MAX_TURNS,
    global_disable_tools: Optional[List[str]] = None,
) -> Dict[str, Any]:
    case_id = spec["id"]
    case_dir = output_dir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    conv_id = spec.get("conversation_id") or f"batch_{case_id}_{uuid.uuid4().hex[:6]}"

    # 模式钉死:把 mode 翻成 query 后缀(复用 testset 那套），模型据此确定模式、不再 ask_user。
    # mode 取值:html=无模板 / template[:<名>]=模板 / 缺省=让 skill 默认(无模板)。creative 已下线,拒收。
    mode = str(spec.get("mode") or "").strip()
    if mode == "creative":
        _emit({
            "event": "mode_rejected",
            "id": case_id,
            "reason": "creative 模式已下线,本地不可用;请用 html 或 template[:<名>]",
        })
        mode = ""  # 退化为默认(无模板),不让它进创意
    query = spec["query"] + resolve_mode_suffix(mode) + _AUTONOMOUS_SUFFIX

    base_case: Dict[str, Any] = {
        "id": case_id,
        "query": query,
        "local_file_path": list(spec.get("files") or []),
        "conversation_id": conv_id,
        "session_id": str(uuid.uuid4()),
        "supports_ask_user": True,
        "persist_sandbox_state": True,
    }
    # 工具禁用 = 全局 --disable-tools(对所有 case 生效) ∪ 本 case 自带 disable_tools(若有)
    disabled_tools: List[str] = list(global_disable_tools or [])
    for t in (spec.get("disable_tools") or []):
        if t not in disabled_tools:
            disabled_tools.append(t)
    if disabled_tools:
        base_case["disable_tools"] = disabled_tools

    explicit_answers = dict(((spec.get("ask_user") or {}).get("answers") or {}))

    ctx.conversation_id = conv_id
    ctx.result_dir = case_dir

    started = datetime.now()
    _emit({
        "event": "case_start",
        "id": case_id,
        "conv_id": conv_id,
        "ts": started.isoformat(timespec="seconds"),
    })

    ask_user_picks_history: List[Dict[str, Any]] = []
    current_case = dict(base_case)
    result: Dict[str, Any] = {}
    turns_used = 0
    result_pending: Optional[Dict[str, Any]] = None

    try:
        for turn in range(1, max_turns + 1):
            turns_used = turn
            result = run_single_case(
                case=current_case, components=components, conversation_id=conv_id
            )
            result_pending = extract_pending_ask_payload(result)
            if result_pending is None:
                break  # case 跑完了
            resume_answers, picks = _build_resume_answers_random(
                result_pending, explicit_answers, rng, pinned_mode=mode
            )
            ask_user_picks_history.append({"turn": turn, "picks": picks})
            if resume_answers is None:
                # 流程里出现了开放题(没 options 可选),按约定该 case 直接失败丢掉。
                result["error"] = "open_ended_question_in_flow"
                break
            current_case = {
                **base_case,
                "agent_state": result.get("state"),
                "resume_answers": resume_answers,
            }

        if result_pending is not None and not result.get("error"):
            result["error"] = f"max_turns_exceeded ({max_turns})"

        save_result(case_dir, base_case, result)

        result_jsonl = case_dir / "result.jsonl"
        try:
            main_n, sub_n = export_openai_traces(result_jsonl, output_dir)
        except Exception as exc:  # noqa: BLE001
            main_n, sub_n = 0, 0
            _emit({"event": "export_error", "id": case_id, "error": f"{type(exc).__name__}: {exc}"})

        # deck 质量从沙盒真实落地目录按 conv_id 读(不再 mirror 进 case_dir、不读 backend/database)。
        scan_root = _resolve_deck_scan_root(conv_id, case_id, case_dir)
        try:
            deck_quality = _compute_deck_quality(scan_root)
        except Exception as exc:  # noqa: BLE001
            deck_quality = {"error": f"{type(exc).__name__}: {exc}"}

        ended = datetime.now()
        # 终态分类(单一可信源)。完成与 html 解耦:done / done_no_html 都算"完成、不重跑";
        # html 仅作质量字段。不再把 completed_but_no_html 塞进 result.error(那会污染分类)。
        cls = classify_terminal(result, deck_quality)
        ok = cls in ("done", "done_no_html")
        html_pages = deck_quality.get("html_pages") if isinstance(deck_quality, dict) else None
        rec: Dict[str, Any] = {
            "id": case_id,
            "conv_id": conv_id,
            "ok": ok,
            "terminal_class": cls,
            "turns": turns_used,
            "duration_s": round((ended - started).total_seconds(), 2),
            "started_at": started.isoformat(timespec="seconds"),
            "completed_at": ended.isoformat(timespec="seconds"),
            "openai_main_count": main_n,
            "openai_subtask_count": sub_n,
            "deck_quality": deck_quality,
            "deck_scan_root": str(scan_root),
            "ask_user_picks": ask_user_picks_history,
            "error": result.get("error"),
        }
        _emit({
            "event": "case_done",
            "id": case_id,
            "terminal_class": cls,
            "success": ok,
            "duration_s": rec["duration_s"],
            "turns": turns_used,
            "deck_html_pages": html_pages,
            "deck_png_pages": deck_quality.get("png_pages") if isinstance(deck_quality, dict) else None,
        })
        return rec
    except Exception as exc:  # noqa: BLE001 — 不要让单 case 异常炸掉整批
        ended = datetime.now()
        err_text = f"{type(exc).__name__}: {exc}"
        # 异常路径同样分类:沙盒会话创建期连不上多走这里 → infra_failed(可重跑)。
        cls = "infra_failed" if is_infra(err_text) else "other_error"
        _emit({"event": "case_error", "id": case_id, "terminal_class": cls, "error": err_text})
        return {
            "id": case_id,
            "conv_id": conv_id,
            "ok": False,
            "terminal_class": cls,
            "turns": turns_used,
            "duration_s": round((ended - started).total_seconds(), 2),
            "started_at": started.isoformat(timespec="seconds"),
            "completed_at": ended.isoformat(timespec="seconds"),
            "openai_main_count": 0,
            "openai_subtask_count": 0,
            "deck_quality": None,
            "ask_user_picks": ask_user_picks_history,
            "error": err_text,
        }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a batch of cases (jsonl) and export OpenAI traces in one shot."
    )
    parser.add_argument("--input", required=True, type=Path, help="JSONL 输入(每行一个 case)")
    parser.add_argument("--output", required=True, type=Path, help="结果根目录")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(os.environ.get("AGENT_CONFIG_PATH", DEFAULT_CONFIG)),
        help=f"YAML 配置,默认 {DEFAULT_CONFIG}(或 AGENT_CONFIG_PATH env)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"并发度(默认 {DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed(给了就能复现 ask_user 随机选项)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=DEFAULT_MAX_TURNS,
        help=f"每个 case 最大续跑轮数(默认 {DEFAULT_MAX_TURNS})",
    )
    parser.add_argument(
        "--disable-tools",
        type=str,
        default=None,
        help="逗号分隔的工具名,对整批所有 case 生效(如 web_search,image_search,image_generation,"
             "fetch_url,image_vqa,rerank_texts)。这是禁用工具的正道——不要再写进数据。",
    )
    parser.add_argument(
        "--disable-skills",
        type=str,
        default=None,
        help="逗号分隔的技能名,从本批 config 的 skill_registry.allowlist 摘除(如 deep-research)。"
             "技能层 disable_tools 管不到——关 deep-research 必须用这个。",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="从第几个有效 case 开始跑(0 基,按 input 里的有效行顺序)。用于分批:配合 --count 切片。",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="本次跑多少个 case(从 --start 起)。省略=跑到末尾。分批跑就 --start 0 --count 500 / --start 500 --count 500 …",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="断点续传(按终态分类):扫 <output>/events.jsonl,跳过『已完成 + triage 类』"
             "(terminal_class ∈ done/done_no_html/render_suspect/content_incomplete/other_error),"
             "只重跑 infra_failed(沙盒/连接层失败)和 killed(只 start 没终态)。"
             "外层 shell 循环 + --resume 即可自愈过夜:沙盒挂→该趟全 infra_failed→下趟重跑;恢复→拿到 done→不再跑;"
             "全部 done/triage 后 rerun 集为空、循环自然收敛。续传用和上次一样的 --input/--output(+--start/--count)。",
    )
    parser.add_argument(
        "--resume-skip-started",
        action="store_true",
        help="续传时把跳过放宽到「只要 case_start 出现过的 id 都跳」(连 infra_failed/in-flight 也跳)。"
             "用于上次 OOM/重启、怀疑在跑的数据本身有问题要绕开时。隐含开启 --resume。",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="恢复传统行为:agentv3/LiteLLM 日志同时打 stdout、runner 的 JSON 事件也回 stdout。"
             "调试用,会冲歪进度条。默认不开。",
    )
    args = parser.parse_args(argv)

    global _VERBOSE
    _VERBOSE = bool(args.verbose)

    if not args.input.is_file():
        print(f"input 不存在: {args.input}", file=sys.stderr)
        return 2

    config_path = args.config if args.config.is_absolute() else (PROJECT_ROOT / args.config)
    if not config_path.exists():
        print(f"config 不存在: {config_path}", file=sys.stderr)
        return 2

    cases = load_cases(args.input)
    if not cases:
        print("input 中没有有效 case", file=sys.stderr)
        return 2

    # 分批切片:--start(0 基)/--count。切片在「有效 case 列表」上做(已过滤空行/注释/缺字段)。
    total_valid = len(cases)
    if args.start < 0:
        print(f"--start 不能为负: {args.start}", file=sys.stderr)
        return 2
    if args.start >= total_valid:
        print(f"--start {args.start} 超过有效 case 数 {total_valid},没东西可跑", file=sys.stderr)
        return 2
    slice_end = (args.start + args.count) if args.count is not None else total_valid
    cases = cases[args.start:slice_end]
    if not cases:
        print(f"切片 [{args.start}:{slice_end}] 为空(有效 case 共 {total_valid})", file=sys.stderr)
        return 2
    print(
        f"[slice] 有效 case 共 {total_valid};本次跑 [{args.start}:{args.start + len(cases)}] 共 {len(cases)} 个",
        file=sys.stderr, flush=True,
    )

    # 断点续传:在「重新以 append 打开 events.jsonl」之前先读旧记录,把要跳过的 id 从本切片剔除。
    # 读 / 写用不同 handle,互不影响。--resume-skip-started 隐含开启 --resume。
    # 跳过集:默认=已 case_done 的 id;--resume-skip-started=所有出现过 case_start 的 id(done 的超集,
    # 额外含崩溃/上次进程被杀时正在跑的 in-flight),用于绕开疑似卡死整批的坏数据。
    resume_cls_by_id: Dict[str, str] = {}
    resume_started_ids: set = set()
    resume_skipped = 0
    resume_active = bool(args.resume or args.resume_skip_started)
    if resume_active:
        resume_cls_by_id, resume_started_ids = _scan_event_ids(args.output / "events.jsonl")
        if args.resume_skip_started:
            # 激进:只要 start 过就跳(OOM/坏数据绕开,含 in-flight/崩溃)
            skip_ids = set(resume_started_ids)
            mode_desc = "started(全跳,含 infra/in-flight)"
        else:
            # 默认:跳「已完成 + triage 类」;infra_failed 与 killed(start 无终态)会重跑 → 外层循环据此收敛
            skip_ids = {i for i, c in resume_cls_by_id.items() if c in RESUME_SKIP_CLASSES}
            mode_desc = "skip=done/done_no_html/render_suspect/content_incomplete/other_error;rerun=infra_failed+killed"
        before = len(cases)
        cases = [c for c in cases if str(c["id"]) not in skip_ids]
        resume_skipped = before - len(cases)
        print(
            f"[resume] 模式={mode_desc};events 终态分布={dict(Counter(resume_cls_by_id.values()))} "
            f"started={len(resume_started_ids)};本切片跳过 {resume_skipped} 个,待跑 {len(cases)} 个",
            file=sys.stderr, flush=True,
        )
        if not cases:
            print("[resume] 本切片已无可重跑(剩下的都是已完成/triage),无需再跑", file=sys.stderr, flush=True)
            return 0

    disable_tools = _parse_csv(args.disable_tools)
    disable_skills = _parse_csv(args.disable_skills)

    # 在启动任何 case 前做 PPT skills 完整性 gate。缺源码时直接拒绝整批，
    # 避免几十个 case 运行到 HTML 阶段才同时失败或由模型临时自修复污染口径。
    conf_for_preflight = load_yaml_config(str(config_path)) or {}
    missing_runtime_files = _missing_ppt_runtime_files(conf_for_preflight, cases)
    if missing_runtime_files:
        print(
            "[fatal] PPT skills 运行文件不完整，拒绝启动跑批:\n  - "
            + "\n  - ".join(str(path) for path in missing_runtime_files),
            file=sys.stderr,
            flush=True,
        )
        return 2

    # --disable-tools 校验(未知名静默失败,主动告警)
    if disable_tools:
        _validate_disable_tools(disable_tools, load_yaml_config(str(config_path)))
    # --disable-skills 走临时 effective config(从 allowlist 摘除),整批生效
    args.output.mkdir(parents=True, exist_ok=True)

    # 打开事件文件;干净模式下所有 _emit 都只写这里,verbose 时也回 stdout。
    # 每条事件都 flush 过,落盘是即时的;进程退出时 Python 自动关 fd,这里不挂 atexit。
    global _EVENTS_FH
    _EVENTS_FH = (args.output / "events.jsonl").open("a", encoding="utf-8")

    if disable_skills:
        config_path = _write_effective_config_without_skills(config_path, disable_skills, args.output)

    # deck 产物落在 config 的 sandbox.sandbox_retrieve_path/<conv_id> 下;质量判定按 conv_id 去这里读。
    global _SANDBOX_RETRIEVE_PATH
    try:
        _sb_cfg = (load_yaml_config(str(config_path)) or {}).get("sandbox") or {}
        _rp = str(_sb_cfg.get("sandbox_retrieve_path") or "").strip()
        _SANDBOX_RETRIEVE_PATH = Path(_rp) if _rp else None
    except Exception:  # noqa: BLE001
        _SANDBOX_RETRIEVE_PATH = None
    print(f"[deck] 质量判定读取根: {_SANDBOX_RETRIEVE_PATH or '(未配置 sandbox_retrieve_path,回退 case_dir)'}",
          file=sys.stderr, flush=True)

    setup_logger(PROJECT_ROOT / "logs/run_batch_and_export")
    # 静音 stdout/stderr 日志(verbose 时跳过)
    _mute_console_logging(_VERBOSE)
    # 把 sys.stdout 重定向到文件,兜住仓内 100+ 处裸 print(verbose 时跳过)
    stdout_capture_path = args.output / "stdout_capture.log" if not _VERBOSE else None
    if stdout_capture_path is not None:
        _redirect_stdout_to_capture(stdout_capture_path, _VERBOSE)
    # 在进度条之前告诉用户日志/事件流在哪 + 怎么 tail
    _print_log_locations(
        _resolve_log_file_from_root_logger(),
        args.output / "events.jsonl",
        stdout_capture_path,
    )
    components = build_agent_components(config_path)

    batch_started = datetime.now()
    _emit({
        "event": "batch_start",
        "input": str(args.input),
        "output": str(args.output),
        "config": str(config_path),
        "concurrency": args.concurrency,
        "seed": args.seed,
        "max_turns": args.max_turns,
        "disable_tools": disable_tools,
        "disable_skills": disable_skills,
        "slice_start": args.start,
        "slice_count": len(cases),
        "input_total_valid": total_valid,
        "cases": len(cases),
        "resume": resume_active,
        "resume_skip_started": bool(args.resume_skip_started),
        "resume_skipped": resume_skipped,
        "resume_prev_terminal": dict(Counter(resume_cls_by_id.values())),
        "resume_started_seen": len(resume_started_ids),
    })

    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(
        max_workers=max(1, args.concurrency), thread_name_prefix="batch-case"
    ) as pool:
        futures = {
            pool.submit(
                run_one_with_ask_user,
                c,
                components,
                args.output,
                rng=_make_case_rng(args.seed, c["id"]),
                max_turns=args.max_turns,
                global_disable_tools=disable_tools,
            ): c["id"]
            for c in cases
        }
        # 进度条走 stderr，不污染 stdout 的 JSON 事件流；标题实时显示成功/失败计数
        ok_n = fail_n = 0
        bar = _progress_bar(len(cases))
        try:
            for fut in as_completed(futures):
                rec = fut.result()
                results.append(rec)
                if rec.get("ok"):
                    ok_n += 1
                else:
                    fail_n += 1
                if bar is not None:
                    bar.set_postfix_str(f"ok={ok_n} fail={fail_n}", refresh=False)
                    bar.update(1)
                else:
                    print(
                        f"[progress] {len(results)}/{len(cases)} done (ok={ok_n} fail={fail_n})",
                        file=sys.stderr, flush=True,
                    )
        finally:
            if bar is not None:
                bar.close()

    batch_ended = datetime.now()
    summary = {
        "input": str(args.input),
        "output_dir": str(args.output),
        "config": str(config_path),
        "concurrency": args.concurrency,
        "seed": args.seed,
        "max_turns": args.max_turns,
        "disable_tools": disable_tools,
        "disable_skills": disable_skills,
        "slice_start": args.start,
        "input_total_valid": total_valid,
        "resume": resume_active,
        "resume_skip_started": bool(args.resume_skip_started),
        "resume_skipped": resume_skipped,
        "started_at": batch_started.isoformat(timespec="seconds"),
        "completed_at": batch_ended.isoformat(timespec="seconds"),
        "total_duration_s": round((batch_ended - batch_started).total_seconds(), 2),
        "case_total": len(cases),
        "case_ok": sum(1 for r in results if r["ok"]),
        "terminal_breakdown": dict(Counter(r.get("terminal_class") for r in results)),
        "results": sorted(results, key=lambda r: r["id"]),
    }
    (args.output / "batch_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # 本趟收尾摘要(外层循环每趟会看到这一行;infra_failed/killed 下趟 --resume 会自动重跑)
    tb = summary["terminal_breakdown"]
    rerun_left = tb.get("infra_failed", 0)
    print(
        f"[batch_done] 本趟 {summary['case_total']} 个: " +
        ", ".join(f"{k}={v}" for k, v in sorted(tb.items())) +
        f" | 可重跑(infra_failed)={rerun_left};用时 {summary['total_duration_s']}s",
        file=sys.stderr, flush=True,
    )
    _emit({
        "event": "batch_done",
        "summary": str(args.output / "batch_summary.json"),
        "ok": summary["case_ok"],
        "total": summary["case_total"],
        "terminal_breakdown": tb,
        "duration_s": summary["total_duration_s"],
    })
    # 退出码:本趟还有 infra_failed(可重跑)→ 返回 1,方便外层循环判断是否继续;否则 0。
    return 0 if rerun_left == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
