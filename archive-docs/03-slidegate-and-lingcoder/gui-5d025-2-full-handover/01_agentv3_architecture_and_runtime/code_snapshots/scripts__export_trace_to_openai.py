#!/usr/bin/env python3
"""Export an AgentV3 case result into OpenAI-flavored training-data JSON.

读一个 case 的 `result.jsonl`(可含多行,默认每行一个 case),按主 agent 和每个
subtask 各产出一份 OpenAI 训练格式的 JSON 文件:

    <output_dir>/<case_id>/main.json
    <output_dir>/<case_id>/subtask_0.json
    ...

输出形状(对齐 OpenAI 训练样本约定):

    {
        "case_id": "...",
        "agent": "main" | "subtask",
        "subtask_id": "subtask_N",          # 仅 subtask
        "subtask_kind": "subtask"|"reflect", # 仅 subtask
        "subtask_title": "...",              # 仅 subtask
        "status": "completed" | "failed" | "stopped" | "waiting_user_input",
        "total_steps": int,
        "enable_thinking": bool,
        "messages": [...OpenAI shape...],
        "tools": [...OpenAI function schemas...],
        "metadata": {...source pointers...}
    }

`messages` 字段:
    role=system   → {role, content}
    role=user     → {role, content}
    role=assistant→ {role, content, reasoning_content?, tool_calls?}
    role=tool     → {role, name, tool_call_id, content, success}

`tools` 取自 result.jsonl 的 `tool_schemas.main`(主)或 `tool_schemas.delegate`(子任务)。

依赖:仅 Python 3 标准库。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Helpers — tool success inference
# ---------------------------------------------------------------------------

_SUCCESS_STATUS_TOKENS = {"ok", "success", "succeeded", "completed", "done", "200"}
_FAILURE_STATUS_TOKENS = {
    "error",
    "failed",
    "failure",
    "exception",
    "timeout",
    "denied",
    "invalid",
    "not_found",
    "fatal",
}


def _parse_jsonish(value: Any) -> Any:
    """字符串能解析成 JSON 就解析,否则原样返回。"""
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped or stripped[0] not in "{[":
        return value
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, TypeError):
        return value


def _infer_tool_success(payload: Any) -> bool:
    """从 tool_result 的 payload 或 content 推断 success bool。

    规则(顺序):
    1. 能 parse 成 dict:按显式字段判定
       - success: bool → 直接用
       - status: 命中 success/failure token → True/False
       - error / error_code / errno 非空 → False
       - exit_code / return_code:0 → True,非零 → False
    2. free text(非结构化 / 长文本):**只**认 `Traceback (most recent call last)`
       这种代码型确证为 False;其余默认 True。
       不在 free text 上跑通用失败关键词回退 — 因为 agent 业务报告里大量出现
       字面 'failed'/'error' 字样(如 `failed_pages=[]`、`成功: failed=无` 等),
       关键词回退会大量误判。
    """
    parsed = _parse_jsonish(payload)
    if isinstance(parsed, dict):
        inner = parsed.get("result")
        if isinstance(inner, (dict, list)):
            parsed = inner
        elif isinstance(inner, str):
            inner_parsed = _parse_jsonish(inner)
            if isinstance(inner_parsed, (dict, list)):
                parsed = inner_parsed

    if isinstance(parsed, dict):
        if isinstance(parsed.get("success"), bool):
            return bool(parsed["success"])
        status = parsed.get("status")
        if isinstance(status, str):
            token = status.strip().lower()
            if token in _SUCCESS_STATUS_TOKENS:
                return True
            if token in _FAILURE_STATUS_TOKENS:
                return False
        for key in ("error", "error_code", "errno"):
            value = parsed.get(key)
            if value not in (None, "", 0, False, [], {}):
                return False
        for key in ("exit_code", "return_code", "returncode"):
            if key in parsed:
                try:
                    return int(parsed[key]) == 0
                except (TypeError, ValueError):
                    pass

    text = parsed if isinstance(parsed, str) else json.dumps(parsed, ensure_ascii=False)
    if isinstance(text, str) and "traceback (most recent call last)" in text.lower():
        return False
    return True


# ---------------------------------------------------------------------------
# Message normalization
# ---------------------------------------------------------------------------

_DROP_KEYS = ("_record_ids", "provider_specific_fields", "is_summary")


def _stringify_tool_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    try:
        return json.dumps(content, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(content)


def _normalize_message(
    raw: Dict[str, Any],
    *,
    tool_payload_by_call_id: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """把 state.messages / subtask.messages 里一条原始消息转成 OpenAI 训练 schema。"""
    if not isinstance(raw, dict):
        return None
    role = str(raw.get("role") or "").strip()
    if not role:
        return None

    if role == "system":
        return {"role": "system", "content": str(raw.get("content") or "")}

    if role == "user":
        return {"role": "user", "content": str(raw.get("content") or "")}

    if role == "assistant":
        out: Dict[str, Any] = {
            "role": "assistant",
            "content": str(raw.get("content") or ""),
        }
        thinking = raw.get("thinking_content") or raw.get("reasoning_content")
        # Anthropic 把 extended thinking 放在 thinking_blocks 数组里(每个 block 形如
        # {type: "thinking", thinking: "<text>", signature: "<base64>"}),可能在消息顶层
        # (_to_llm_message 白名单透传)或 provider_specific_fields 里。签名从这里取。
        blocks = raw.get("thinking_blocks")
        if not blocks:
            psf = raw.get("provider_specific_fields")
            if isinstance(psf, dict):
                blocks = psf.get("thinking_blocks")
        if not thinking:
            # Fallback: 没有 thinking_content 时,抽出每个 block 的 thinking 字段拼成单个
            # reasoning_content 字符串,以便下游消费。
            # 备注:当上游 gateway 把 thinking 字段剥成空字符串时(只留 signature),拼出来仍是
            # 空 → 维持原行为不写 reasoning_content。
            if isinstance(blocks, list) and blocks:
                parts: List[str] = []
                for b in blocks:
                    if isinstance(b, dict):
                        t = b.get("thinking") or b.get("text")
                        if t:
                            parts.append(str(t))
                if parts:
                    thinking = "\n\n".join(parts)
        if thinking:
            out["reasoning_content"] = thinking if isinstance(thinking, str) else json.dumps(thinking, ensure_ascii=False)
            # 紧跟 reasoning_content 输出签名(claude/gpt 蒸馏数据要求携带)。
            # 实际数据里 blocks 恒为单元素;若出现多个带签名的 block,取第一个。
            if isinstance(blocks, list):
                for b in blocks:
                    if isinstance(b, dict) and b.get("signature"):
                        out["reasoning_signature"] = str(b["signature"])
                        break
        tool_calls = raw.get("tool_calls") or []
        if tool_calls:
            cleaned_calls = []
            for tc in tool_calls:
                if not isinstance(tc, dict):
                    continue
                fn = tc.get("function") or {}
                args = fn.get("arguments")
                # 参数原本是 JSON 字符串,尝试反序列化成 dict 便于训练消费
                args_parsed: Any = args
                if isinstance(args, str):
                    try:
                        args_parsed = json.loads(args)
                    except (json.JSONDecodeError, TypeError):
                        args_parsed = args
                cleaned_calls.append(
                    {
                        "id": tc.get("id") or "",
                        "type": tc.get("type") or "function",
                        "function": {
                            "name": fn.get("name") or "",
                            "arguments": args_parsed,
                        },
                    }
                )
            if cleaned_calls:
                out["tool_calls"] = cleaned_calls
        return out

    if role == "tool":
        tool_call_id = raw.get("tool_call_id") or ""
        content_text = _stringify_tool_content(raw.get("content"))
        # success 优先从 record payload 推,再从 content 推
        success_source: Any = content_text
        if tool_payload_by_call_id and tool_call_id in tool_payload_by_call_id:
            success_source = tool_payload_by_call_id[tool_call_id]
        return {
            "role": "tool",
            "name": raw.get("name") or raw.get("tool_name") or "",
            "tool_call_id": tool_call_id,
            "content": content_text,
            "success": _infer_tool_success(success_source),
        }

    # 未识别 role 直接丢
    return None


def _strip_extra_keys(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for m in messages:
        for k in _DROP_KEYS:
            m.pop(k, None)
    return messages


# ---------------------------------------------------------------------------
# Per-trace assembly
# ---------------------------------------------------------------------------

def _collect_tool_payload_map(message_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """tool_call_id → tool_result.payload。供 success 推断使用。"""
    mapping: Dict[str, Any] = {}
    for record in message_records or []:
        if not isinstance(record, dict):
            continue
        if record.get("type") != "tool_result":
            continue
        tcid = record.get("tool_call_id")
        if not tcid:
            continue
        mapping[str(tcid)] = record.get("payload")
    return mapping


def _derive_status(*, success: Any, stopped: Any, waiting: Any) -> str:
    if waiting:
        return "waiting_user_input"
    if stopped:
        return "stopped"
    return "completed" if success else "failed"


def _build_main_trace(
    case_record: Dict[str, Any],
    *,
    source_path: Path,
) -> Optional[Dict[str, Any]]:
    messages_raw = case_record.get("messages") or []
    if not isinstance(messages_raw, list) or not messages_raw:
        return None

    message_records = case_record.get("message_records") or []
    if isinstance(message_records, list):
        tool_payload_map = _collect_tool_payload_map(message_records)
    else:
        tool_payload_map = {}

    normalized: List[Dict[str, Any]] = []
    for raw in messages_raw:
        n = _normalize_message(raw, tool_payload_by_call_id=tool_payload_map)
        if n is not None:
            normalized.append(n)
    _strip_extra_keys(normalized)

    result_payload = case_record.get("result") or {}
    state = case_record.get("state") or {}
    runtime_control = state.get("runtime_control") or {}
    waiting = runtime_control.get("conversation_status") == "waiting_user_input"

    enable_thinking = any(m.get("reasoning_content") for m in normalized)
    total_steps = sum(
        1 for m in normalized if m.get("role") == "assistant" and (m.get("content") or m.get("tool_calls"))
    )

    tools_schema = (case_record.get("tool_schemas") or {}).get("main") or []

    return {
        "case_id": str(case_record.get("id") or ""),
        "agent": "main",
        "status": _derive_status(
            success=bool(result_payload.get("success")),
            stopped=bool(result_payload.get("stopped")),
            waiting=waiting,
        ),
        "total_steps": total_steps,
        "enable_thinking": enable_thinking,
        "messages": normalized,
        "tools": list(tools_schema),
        "metadata": {
            "source_result_jsonl": str(source_path),
            "conversation_id": state.get("conversation_id") or runtime_control.get("conversation_id"),
            "exported_at": datetime.now().isoformat(timespec="seconds"),
        },
    }


def _build_subtask_traces(
    case_record: Dict[str, Any],
    *,
    source_path: Path,
) -> List[Dict[str, Any]]:
    state = case_record.get("state") or {}
    subtasks = (state.get("runtime_control") or {}).get("subtasks") or {}
    if not isinstance(subtasks, dict) or not subtasks:
        return []

    tools_schema = (case_record.get("tool_schemas") or {}).get("delegate") or []
    case_id = str(case_record.get("id") or "")
    result_payload = case_record.get("result") or {}

    traces: List[Dict[str, Any]] = []
    for sid, sub in sorted(subtasks.items(), key=lambda kv: str(kv[0])):
        if not isinstance(sub, dict):
            continue
        messages_raw = sub.get("messages") or []
        if not isinstance(messages_raw, list) or not messages_raw:
            continue
        normalized = [m for m in (_normalize_message(raw) for raw in messages_raw) if m is not None]
        _strip_extra_keys(normalized)

        sub_status = str(sub.get("status") or "").strip().lower()
        if sub_status in {"success", "succeeded", "completed", "ok", "done"}:
            status = "completed"
        elif sub_status in {"error", "errored", "failed", "failure"}:
            status = "failed"
        elif sub_status in {"stopped", "cancelled", "canceled"}:
            status = "stopped"
        elif sub_status:
            status = sub_status
        else:
            status = _derive_status(
                success=bool(result_payload.get("success")),
                stopped=bool(result_payload.get("stopped")),
                waiting=False,
            )

        enable_thinking = any(m.get("reasoning_content") for m in normalized)
        total_steps = sum(
            1 for m in normalized if m.get("role") == "assistant" and (m.get("content") or m.get("tool_calls"))
        )

        traces.append(
            {
                "case_id": case_id,
                "agent": "subtask",
                "subtask_id": str(sid),
                "subtask_kind": sub.get("kind") or "",
                "subtask_title": sub.get("title") or sub.get("user_visible_title") or "",
                "parent_tool_call_id": sub.get("parent_tool_call_id"),
                "loop_count": sub.get("loop_count"),
                "max_loops": sub.get("max_loops"),
                "instruction_preview": (sub.get("instruction") or "")[:500],
                "raw_result_preview": (
                    sub.get("result")
                    if isinstance(sub.get("result"), str)
                    else json.dumps(sub.get("result"), ensure_ascii=False)
                    if sub.get("result") is not None
                    else None
                ),
                "status": status,
                "total_steps": total_steps,
                "enable_thinking": enable_thinking,
                "messages": normalized,
                "tools": list(tools_schema),
                "metadata": {
                    "source_result_jsonl": str(source_path),
                    "exported_at": datetime.now().isoformat(timespec="seconds"),
                },
            }
        )
    return traces


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _iter_records(jsonl_path: Path) -> Iterable[Dict[str, Any]]:
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield json.loads(stripped)
            except json.JSONDecodeError as exc:
                print(f"[warn] {jsonl_path}:{line_no} 解析失败: {exc}", file=sys.stderr)


def export_one(result_path: Path, output_dir: Path) -> Tuple[int, int]:
    """处理一个 result.jsonl。返回(主 trace 数, 子任务 trace 数)。"""
    main_count = 0
    subtask_count = 0
    for case_record in _iter_records(result_path):
        case_id = str(case_record.get("id") or "case").strip() or "case"
        case_out_dir = output_dir / case_id
        case_out_dir.mkdir(parents=True, exist_ok=True)

        main_trace = _build_main_trace(case_record, source_path=result_path)
        if main_trace is not None:
            (case_out_dir / "main.json").write_text(
                json.dumps(main_trace, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            main_count += 1

        for trace in _build_subtask_traces(case_record, source_path=result_path):
            (case_out_dir / f"{trace['subtask_id']}.json").write_text(
                json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            subtask_count += 1

    return main_count, subtask_count


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export AgentV3 case result.jsonl to OpenAI training-format JSON (main + subtasks)."
    )
    parser.add_argument(
        "--result",
        type=Path,
        action="append",
        required=False,
        help="单个 result.jsonl 路径,可多次。或用 --root 扫目录。",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="扫描目录,遇到 result.jsonl 就处理(递归)。",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="输出根目录;每个 case 落 <output-dir>/<case_id>/{main,subtask_*}.json",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    targets: List[Path] = list(args.result or [])
    if args.root:
        targets.extend(sorted(args.root.rglob("result.jsonl")))
    if not targets:
        print("ERROR: 请用 --result <path> 或 --root <dir> 指定输入。", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    total_main = 0
    total_sub = 0
    for path in targets:
        if not path.is_file():
            print(f"[skip] 不存在: {path}", file=sys.stderr)
            continue
        m, s = export_one(path, args.output_dir)
        total_main += m
        total_sub += s
        print(
            json.dumps(
                {"event": "exported", "source": str(path), "main": m, "subtasks": s},
                ensure_ascii=False,
            ),
            flush=True,
        )

    print(
        json.dumps(
            {"event": "done", "main_total": total_main, "subtask_total": total_sub, "output_dir": str(args.output_dir)},
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
