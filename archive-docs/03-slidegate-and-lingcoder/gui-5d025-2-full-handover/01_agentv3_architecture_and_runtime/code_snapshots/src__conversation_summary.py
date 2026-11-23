import html
import json
import logging
import os
import re
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from src.base_llm import BaseLLM
from src.conversation_state_v3 import (
    apply_summary_offload_to_conversation_state,
    rebuild_compiled_messages,
)
from src.conversation_summary_prompts import smart_optimize_prompt_en, smart_optimize_prompt_zh
from src.utils import ctx
from src.utils.context_token_utils import (
    estimate_content_tokens as _estimate_actual_content_tokens,
    estimate_messages_tokens as _estimate_actual_messages_tokens,
    summarize_message_token_usage,
)
from tools.sandbox import _get_sandbox_meta_from_config, upload_file_to_sandbox

logger = logging.getLogger(__name__)

DEFAULT_RECENT_ROUNDS_TOKEN_BUDGET_RATIO = 0.4
DEFAULT_USER_TOKEN_BUDGET_RATIO = 0.2
DEFAULT_CONTEXT_ARCHIVE_DIR = "message_offload"
SUMMARY_TOOL_CONTENT_CHAR_LIMIT = 12000
SUMMARY_MESSAGE_CONTENT_CHAR_LIMIT = 20000
STATE_SNAPSHOT_TAG = "state_snapshot"
UPLOADED_FILES_STATE_TAG = "uploaded_files_state"
PARSED_FILES_STATE_TAG = "parsed_files_state"
SAVED_FILES_STATE_TAG = "saved_files_state"
CONTEXT_ARCHIVES_STATE_TAG = "context_archives_state"
TODOLIST_STATE_TAG = "todolist_state"
_INTERNAL_PROJECTION_TAGS = (
    "file_context",
    "current_active_editor_projection",
    "preloaded_context",
    "retrieved_context",
)


def _normalize_language(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    lang = str(value).strip().lower()
    if lang.startswith("zh"):
        return "zh"
    if lang.startswith("en"):
        return "en"
    return lang


def _resolve_runtime_language(
    state: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    lang = None
    if isinstance(state, dict):
        runtime = state.get("runtime_control") or {}
        lang = runtime.get("current_prompt_locale") or state.get("language")
    if not lang and isinstance(config, dict):
        lang = (config.get("runtime") or {}).get("language")
    if not lang and hasattr(ctx, "config") and ctx.config:
        lang = (ctx.config.get("runtime") or {}).get("language")
    return _normalize_language(lang) or "en"


def _estimate_content_tokens(content: Any) -> int:
    return _estimate_actual_content_tokens(
        content,
        config=ctx.config if hasattr(ctx, "config") else None,
    )


def _estimate_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    return max(
        1,
        _estimate_actual_messages_tokens(
            messages,
            config=ctx.config if hasattr(ctx, "config") else None,
        ),
    )


def _resolve_positive_int(value: Any) -> Optional[int]:
    try:
        resolved = int(value) if value is not None else None
    except (TypeError, ValueError):
        resolved = None
    if resolved is None or resolved <= 0:
        return None
    return resolved


def _extract_total_usage(msg: Dict[str, Any]) -> Optional[int]:
    for key in ("total_usage", "_usage", "usage"):
        value = msg.get(key)
        if value is None:
            continue
        try:
            ivalue = int(value)
        except (TypeError, ValueError):
            continue
        if ivalue > 0:
            return ivalue
    return None


def _resolve_runtime_ratios(config: Optional[Dict[str, Any]]) -> Tuple[float, float]:
    runtime_cfg = {}
    if isinstance(config, dict):
        runtime_cfg = config.get("runtime", {}) or {}
    elif hasattr(ctx, "config") and ctx.config:
        runtime_cfg = ctx.config.get("runtime", {}) or {}

    def _resolve_ratio(key: str, default: float) -> float:
        raw = runtime_cfg.get(key, default)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = default
        return default if value <= 0 else value

    return (
        _resolve_ratio("recent_rounds_token_budget_ratio", DEFAULT_RECENT_ROUNDS_TOKEN_BUDGET_RATIO),
        _resolve_ratio("summary_user_token_budget_ratio", DEFAULT_USER_TOKEN_BUDGET_RATIO),
    )


def _resolve_selection_budget_context(
    messages: List[Dict[str, Any]],
    *,
    config: Optional[Dict[str, Any]],
) -> Dict[str, Optional[float]]:
    usage = summarize_message_token_usage(messages, config=config or getattr(ctx, "config", None))
    runtime_cfg = (config or {}).get("runtime") if isinstance(config, dict) else {}
    runtime_cfg = runtime_cfg if isinstance(runtime_cfg, dict) else {}

    max_context_tokens = runtime_cfg.get("max_context_tokens")
    resolved_max_context = _resolve_positive_int(max_context_tokens)
    user_budget_max = _resolve_positive_int(runtime_cfg.get("summary_user_token_budget_max"))

    recent_ratio, user_ratio = _resolve_runtime_ratios(config)
    actual_live_tokens = max(1, int(usage.get("non_system_tokens") or 0))
    system_tokens = int(usage.get("system_tokens") or 0)
    available_after_system = None
    if resolved_max_context is not None:
        available_after_system = max(1, resolved_max_context - system_tokens)
    base_tokens = actual_live_tokens
    if available_after_system is not None:
        base_tokens = max(1, min(actual_live_tokens, available_after_system))
    recent_budget = max(1, int(base_tokens * recent_ratio))
    user_ratio_budget = max(1, int(base_tokens * user_ratio))
    user_budget = min(user_ratio_budget, user_budget_max) if user_budget_max is not None else user_ratio_budget

    return {
        "max_context_tokens": resolved_max_context,
        "total_message_tokens": int(usage.get("total_tokens") or 0),
        "system_prompt_tokens": system_tokens,
        "actual_live_tokens": actual_live_tokens,
        "available_after_system_tokens": available_after_system,
        "selection_base_tokens": base_tokens,
        "recent_rounds_ratio": recent_ratio,
        "user_messages_ratio": user_ratio,
        "recent_rounds_budget": recent_budget,
        "user_messages_budget_ratio_only": user_ratio_budget,
        "user_messages_budget_max": user_budget_max,
        "user_messages_budget": user_budget,
    }


def _is_summary_message(msg: Dict[str, Any]) -> bool:
    return bool(msg.get("is_summary"))


def _is_internal_projection_message(msg: Dict[str, Any]) -> bool:
    if msg.get("role") != "user":
        return False
    content = msg.get("content", "")
    if not isinstance(content, str):
        return False
    return any(
        re.search(rf"<{re.escape(tag)}\b", content, flags=re.IGNORECASE)
        for tag in _INTERNAL_PROJECTION_TAGS
    )


def _xml_escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=False)


def _extract_tag_content(blob: Any, tag: str) -> Optional[str]:
    if blob is None:
        return None
    match = re.search(
        rf"<{tag}>(.*?)</{tag}>",
        str(blob),
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return None
    return match.group(1).strip()


def _strip_cdata(value: str) -> str:
    if not isinstance(value, str):
        return str(value)
    content = value.strip()
    match = re.match(r"<!\[CDATA\[(.*?)\]\]>", content, flags=re.DOTALL)
    if match:
        return match.group(1)
    return content


def _inject_key_knowledge_line(summary_xml: str, line: str) -> str:
    payload = str(line or "").strip()
    if not payload:
        return summary_xml

    def _replace(match: re.Match[str]) -> str:
        inner = (match.group(1) or "").strip()
        if payload in inner:
            return match.group(0)
        if inner:
            return f"<key_knowledge>{inner}\n{payload}</key_knowledge>"
        return f"<key_knowledge>{payload}</key_knowledge>"

    updated = re.sub(
        r"<key_knowledge>(.*?)</key_knowledge>",
        _replace,
        summary_xml,
        count=1,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if updated != summary_xml:
        return updated

    if re.search(r"</summary>", summary_xml, flags=re.IGNORECASE):
        return re.sub(
            r"</summary>",
            f"<key_knowledge>{payload}</key_knowledge>\n</summary>",
            summary_xml,
            count=1,
            flags=re.IGNORECASE,
        )
    return summary_xml


def _strip_state_snapshot_from_text(text: Any) -> str:
    if not isinstance(text, str):
        text = str(text or "")
    return re.sub(
        rf"\s*<{STATE_SNAPSHOT_TAG}>.*?</{STATE_SNAPSHOT_TAG}>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()


def _compact_long_text_for_summary(content: Any, *, limit: int, label: str) -> str:
    text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
    if len(text) <= limit:
        return text
    head_budget = max(1, int(limit * 0.65))
    tail_budget = max(1, limit - head_budget)
    omitted = len(text) - head_budget - tail_budget
    return (
        text[:head_budget].rstrip()
        + f"\n\n[{label} truncated for summary input: omitted {omitted} characters; use the archived context or source file if exact text is needed.]\n\n"
        + text[-tail_budget:].lstrip()
    )


def _sanitize_message_for_summary_request(message: Dict[str, Any], *, lang: str) -> Dict[str, Any]:
    sanitized = deepcopy(message)
    sanitized.pop("provider_specific_fields", None)

    role = sanitized.get("role")
    if sanitized.get("is_summary"):
        sanitized["content"] = _strip_state_snapshot_from_text(sanitized.get("content", ""))
    elif role == "user":
        cleaned_content, _uploads = _extract_upload_entries_from_text(sanitized.get("content"), lang=lang)
        sanitized["content"] = _compact_long_text_for_summary(
            cleaned_content,
            limit=SUMMARY_MESSAGE_CONTENT_CHAR_LIMIT,
            label="user message",
        )
    elif role == "tool":
        sanitized["content"] = _compact_long_text_for_summary(
            sanitized.get("content", ""),
            limit=SUMMARY_TOOL_CONTENT_CHAR_LIMIT,
            label="tool result",
        )
    elif role == "assistant":
        sanitized["content"] = _compact_long_text_for_summary(
            sanitized.get("content", ""),
            limit=SUMMARY_MESSAGE_CONTENT_CHAR_LIMIT,
            label="assistant message",
        )
    return sanitized


def _sanitize_messages_for_summary_request(
    messages: List[Dict[str, Any]],
    *,
    lang: str,
) -> List[Dict[str, Any]]:
    return [
        _sanitize_message_for_summary_request(message, lang=lang)
        for message in (messages or [])
        if isinstance(message, dict)
    ]


def _latest_summary_text(messages: List[Dict[str, Any]]) -> Optional[str]:
    for message in reversed(messages or []):
        if message.get("is_summary"):
            return str(message.get("content") or "")
    return None


def _summary_content_is_usable(summary_content: str) -> bool:
    if not str(summary_content or "").strip():
        return False
    key_knowledge = _extract_tag_content(summary_content, "key_knowledge")
    return bool(str(key_knowledge or "").strip())


def _fallback_summary_content(
    *,
    lang: str,
    fallback_summary_text: Optional[str],
) -> str:
    previous = _extract_tag_content(str(fallback_summary_text or ""), "summary")
    if previous:
        previous = _strip_state_snapshot_from_text(previous)
        if _summary_content_is_usable(previous):
            line = (
                "本轮 summary 生成结果无法稳定解析；已沿用上一份有效交接摘要，后续应结合保留的实时消息继续。"
                if lang == "zh"
                else "The latest summary generation was not parseable; preserved the previous valid handoff and continue from retained live messages."
            )
            merged = _inject_key_knowledge_line(f"<summary>{previous}</summary>", line)
            return _extract_tag_content(merged, "summary") or previous
    return _default_summary_content(lang)


def _collect_assistant_rounds(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rounds: List[Dict[str, Any]] = []
    i = 0
    while i < len(messages):
        msg = messages[i]
        if msg.get("role") != "assistant" or _is_summary_message(msg):
            i += 1
            continue

        j = i + 1
        while j < len(messages) and messages[j].get("role") != "assistant":
            j += 1

        between = messages[i + 1 : j]
        round_messages = [msg]
        tool_calls = msg.get("tool_calls") or []
        tool_call_ids = {tc.get("id") for tc in tool_calls if tc.get("id")}

        if tool_call_ids:
            for candidate in between:
                if candidate.get("role") != "tool":
                    continue
                if candidate.get("tool_call_id") in tool_call_ids:
                    round_messages.append(candidate)

        rounds.append(
            {
                "assistant_index": i,
                "messages": round_messages,
                "usage": _extract_total_usage(msg),
                "estimated_tokens": 0,
            }
        )
        i = j
    return rounds


def _estimate_round_tokens_by_usage(rounds: List[Dict[str, Any]]) -> None:
    previous_usage: Optional[int] = None
    for round_item in rounds:
        estimated_tokens = _estimate_messages_tokens(round_item.get("messages", []))
        if estimated_tokens <= 0:
            usage = round_item.get("usage")
            if usage is not None:
                estimated_tokens = usage if previous_usage is None else usage - previous_usage
                previous_usage = usage
        round_item["estimated_tokens"] = max(1, int(estimated_tokens))


def _select_recent_rounds(
    rounds: List[Dict[str, Any]],
    *,
    budget: Optional[int],
) -> Tuple[List[Dict[str, Any]], int]:
    if not rounds:
        return [], 0
    if budget is None or budget <= 0:
        latest_round = rounds[-1]
        latest_tokens = int(latest_round.get("estimated_tokens") or 0)
        return [latest_round], max(1, latest_tokens)

    selected_rev: List[Dict[str, Any]] = []
    total = 0
    for round_item in reversed(rounds):
        estimated_tokens = int(round_item.get("estimated_tokens") or 0)
        if not selected_rev:
            selected_rev.append(round_item)
            total += max(1, estimated_tokens)
            continue
        if total + estimated_tokens > budget:
            break
        selected_rev.append(round_item)
        total += estimated_tokens

    return list(reversed(selected_rev)), total


def _flatten_round_messages(rounds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    flattened: List[Dict[str, Any]] = []
    for round_item in rounds:
        flattened.extend(round_item.get("messages", []))
    return flattened


def _extract_message_record_ids(messages: List[Dict[str, Any]]) -> List[str]:
    record_ids: List[str] = []
    seen: set[str] = set()
    for msg in messages or []:
        raw_ids = msg.get("_record_ids")
        if raw_ids is None:
            raw_ids = [msg.get("_record_id")] if msg.get("_record_id") else []
        elif not isinstance(raw_ids, list):
            raw_ids = [raw_ids]
        for raw_id in raw_ids:
            record_id = str(raw_id or "").strip()
            if not record_id or record_id in seen:
                continue
            seen.add(record_id)
            record_ids.append(record_id)
    return record_ids


def _extract_primary_message_record_id(message: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(message, dict):
        return None
    record_ids = _extract_message_record_ids([message])
    if not record_ids:
        return None
    return record_ids[0]


def _select_user_messages(
    messages: List[Dict[str, Any]],
    *,
    budget: Optional[int],
) -> List[Dict[str, Any]]:
    user_messages = [
        msg
        for msg in messages
        if msg.get("role") == "user" and not _is_summary_message(msg) and not _is_internal_projection_message(msg)
    ]
    if not user_messages:
        return []
    if budget is None or budget <= 0:
        return user_messages

    latest_message = user_messages[-1]
    selected_rev: List[Dict[str, Any]] = [latest_message]
    total = _estimate_content_tokens(latest_message.get("content", ""))
    for msg in reversed(user_messages[:-1]):
        estimated_tokens = _estimate_content_tokens(msg.get("content", ""))
        if total + estimated_tokens > budget:
            break
        selected_rev.append(msg)
        total += estimated_tokens
    return list(reversed(selected_rev))


def _find_previous_user_message(
    messages: List[Dict[str, Any]],
    *,
    start_index: int,
) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    upper_bound = min(max(start_index, 0), len(messages))
    for index in range(upper_bound - 1, -1, -1):
        candidate = messages[index]
        if candidate.get("role") != "user":
            continue
        if _is_summary_message(candidate) or _is_internal_projection_message(candidate):
            continue
        return index, candidate
    return None, None


def _collect_required_user_anchor_indices(
    messages: List[Dict[str, Any]],
    *,
    assistant_indices: List[int],
    retained_user_msg_ids: Optional[set[int]] = None,
    included_indices: Optional[set[int]] = None,
) -> set[int]:
    anchor_indices: set[int] = set()
    retained_user_msg_ids = retained_user_msg_ids or set()
    included_indices = included_indices or set()
    for assistant_index in assistant_indices:
        anchor_index, anchor_message = _find_previous_user_message(messages, start_index=assistant_index)
        if anchor_index is None or anchor_message is None:
            continue
        if id(anchor_message) in retained_user_msg_ids or anchor_index in included_indices:
            continue
        anchor_indices.add(anchor_index)
    return anchor_indices


def _select_compaction_messages(
    messages: List[Dict[str, Any]],
    *,
    config: Optional[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    selection_budget = _resolve_selection_budget_context(messages, config=config)
    rounds = _collect_assistant_rounds(messages)
    _estimate_round_tokens_by_usage(rounds)
    kept_rounds, _ = _select_recent_rounds(
        rounds,
        budget=selection_budget.get("recent_rounds_budget"),
    )
    kept_user_messages = _select_user_messages(
        messages,
        budget=selection_budget.get("user_messages_budget"),
    )

    retained_round_message_ids = {id(msg) for msg in _flatten_round_messages(kept_rounds)}
    retained_user_message_ids = {id(msg) for msg in kept_user_messages}
    retained_assistant_indices = [
        int(round_item.get("assistant_index"))
        for round_item in kept_rounds
        if round_item.get("assistant_index") is not None
    ]
    retained_anchor_indices = _collect_required_user_anchor_indices(
        messages,
        assistant_indices=retained_assistant_indices,
        retained_user_msg_ids=retained_user_message_ids,
    )

    retained_indices: set[int] = set(retained_anchor_indices)
    for index, message in enumerate(messages):
        if id(message) in retained_round_message_ids or id(message) in retained_user_message_ids:
            retained_indices.add(index)

    summarized_indices = [
        index
        for index, message in enumerate(messages)
        if message.get("role") != "system"
        and not _is_summary_message(message)
        and not _is_internal_projection_message(message)
        and index not in retained_indices
    ]

    summarized_assistant_indices = [
        index for index in summarized_indices if messages[index].get("role") == "assistant"
    ]
    summary_input_anchor_indices = _collect_required_user_anchor_indices(
        messages,
        assistant_indices=summarized_assistant_indices,
        retained_user_msg_ids=retained_user_message_ids,
        included_indices=set(summarized_indices) | retained_indices,
    )
    summary_input_indices = sorted(set(summarized_indices) | summary_input_anchor_indices)

    trimmed_messages = [deepcopy(messages[index]) for index in summarized_indices]
    summary_input_messages = [deepcopy(messages[index]) for index in summary_input_indices]
    kept_round_messages = _flatten_round_messages(kept_rounds)
    summary_insert_before_record_id = None
    if kept_rounds:
        first_round_messages = kept_rounds[0].get("messages") or []
        if first_round_messages:
            summary_insert_before_record_id = _extract_primary_message_record_id(first_round_messages[0])

    selection = {
        "compiled_message_count": len(messages),
        "retained_round_record_ids": _extract_message_record_ids(kept_round_messages),
        "retained_user_record_ids": _extract_message_record_ids(kept_user_messages),
        "anchor_user_record_ids": _extract_message_record_ids(
            [messages[index] for index in sorted(retained_anchor_indices)]
        ),
        "summarized_record_ids": _extract_message_record_ids(trimmed_messages),
        "summary_input_indices": list(summary_input_indices),
    }
    if summary_insert_before_record_id:
        selection["summary_insert_before_record_id"] = summary_insert_before_record_id
    return trimmed_messages, summary_input_messages, selection


def _build_summary_upload_placeholder(lang: str) -> str:
    if lang == "zh":
        return "用户上传了文件，附件详情已转入结构化状态。"
    return "The user uploaded files; attachment details were moved into structured state."


def _parse_json_payload(raw: Optional[str], default: Any) -> Any:
    text = str(raw or "").strip()
    if not text:
        return deepcopy(default)
    try:
        return json.loads(text)
    except Exception:
        return deepcopy(default)


def _extract_upload_entries_from_text(
    content: Any,
    *,
    lang: str,
) -> Tuple[str, List[Dict[str, Any]]]:
    if not isinstance(content, str):
        return str(content or ""), []

    uploads: List[Dict[str, Any]] = []

    def _replace(match: re.Match[str]) -> str:
        payload = _parse_json_payload(match.group(1), [])
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    uploads.append(deepcopy(item))

        preceding = match.group("prefix") or ""
        stripped_preceding = preceding.rstrip()
        explanatory_block = ""
        for pattern in (
            r"(?:^|\n)用户输入文件\n(?:.+\n)*?## 用户输入文件解析\n.*?(?:\n.+ -> .+)*$",
            r"(?:^|\n)用户输入文件\n(?:.+\n)*$",
            r"(?:^|\n)User input files\n(?:.+\n)*?## Parsed user input files\n.*?(?:\n.+ -> .+)*$",
            r"(?:^|\n)User input files\n(?:.+\n)*$",
        ):
            explanatory_match = re.search(pattern, stripped_preceding, flags=re.DOTALL)
            if explanatory_match and explanatory_match.end() == len(stripped_preceding):
                explanatory_block = explanatory_match.group(0)
                break

        if explanatory_block:
            prefix_without_explanation = stripped_preceding[: -len(explanatory_block)].rstrip()
            if prefix_without_explanation:
                return prefix_without_explanation + "\n"
            return ""
        return preceding

    cleaned = re.sub(
        r"(?P<prefix>(?:^|[\s\S]*?))<uploads>\s*(.*?)\s*</uploads>",
        _replace,
        content,
        count=1,
        flags=re.DOTALL | re.IGNORECASE,
    )
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    if cleaned:
        return cleaned, uploads
    if uploads:
        return _build_summary_upload_placeholder(lang), uploads
    return cleaned, uploads


def _build_upload_state_entries(
    uploads: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    uploaded_files: List[Dict[str, Any]] = []
    parsed_files: List[Dict[str, Any]] = []
    for item in uploads:
        if not isinstance(item, dict):
            continue

        uploaded_entry = {
            "file_id": item.get("file_id"),
            "name": item.get("name"),
            "path": item.get("path") or item.get("storage_path"),
            "sandbox_path": item.get("sandbox_path"),
        }
        if any(value for value in uploaded_entry.values()):
            uploaded_files.append(uploaded_entry)

        preview = item.get("preview")
        preview_summary = None
        if isinstance(preview, dict):
            preview_summary = preview.get("text") or preview.get("description") or preview.get("ocr_text")
        parsed_entry = {
            "source_file_id": item.get("file_id"),
            "name": item.get("name"),
            "parsed_path": item.get("parsed_path"),
            "summary": item.get("summary") or preview_summary,
        }
        if parsed_entry.get("parsed_path") or parsed_entry.get("summary"):
            parsed_files.append(parsed_entry)
    return uploaded_files, parsed_files


def _prepare_messages_for_summary(
    messages: List[Dict[str, Any]],
    *,
    lang: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    sanitized_messages: List[Dict[str, Any]] = []
    summarized_upload_entries: List[Dict[str, Any]] = []

    for message in messages:
        cloned = deepcopy(message)
        if cloned.get("role") == "user":
            cleaned_content, uploads = _extract_upload_entries_from_text(cloned.get("content"), lang=lang)
            cloned["content"] = cleaned_content
            summarized_upload_entries.extend(uploads)
        if cloned.get("role") == "user" and not str(cloned.get("content") or "").strip():
            continue
        sanitized_messages.append(cloned)

    uploaded_files_state, parsed_files_state = _build_upload_state_entries(summarized_upload_entries)
    return sanitized_messages, uploaded_files_state, parsed_files_state


def _extract_latest_todolist_from_messages(messages: List[Dict[str, Any]]) -> Any:
    pattern = re.compile(r"\[(?:Current Plan State|当前计划状态)\]:\s*(\[[\s\S]*\])", flags=re.IGNORECASE)
    for msg in reversed(messages):
        content = msg.get("content")
        if not isinstance(content, str):
            continue
        match = pattern.search(content)
        if not match:
            continue
        raw = match.group(1).strip()
        try:
            return json.loads(raw)
        except Exception:
            return raw
    return None


def _extract_todolist_feedback_list(payload: Any) -> Optional[List[Dict[str, Any]]]:
    candidate = payload
    if isinstance(candidate, dict) and isinstance(candidate.get("result"), dict):
        candidate = candidate.get("result")
    if not isinstance(candidate, dict):
        return None
    if str(candidate.get("interaction_type") or "").strip() != "todolist_feedback":
        return None
    todo_list = candidate.get("todo_list")
    if not isinstance(todo_list, list):
        return None
    return deepcopy(todo_list)


def _extract_pending_todolist_from_state(state: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    runtime = state.get("runtime_control") or {}
    pending_record_id = str(runtime.get("pending_ask_user_message_id") or "").strip()
    if pending_record_id:
        for record in reversed(state.get("message_records") or []):
            if str(record.get("id") or "").strip() != pending_record_id:
                continue
            pending = _extract_todolist_feedback_list(record.get("payload") or {})
            if pending is not None:
                return pending
            break

    pending = _extract_todolist_feedback_list(state.get("pending_ask_user_payload"))
    if pending is not None:
        return pending

    for record in reversed(state.get("message_records") or []):
        if record.get("type") != "tool_result":
            continue
        if str(record.get("tool_name") or "").strip() != "todolist":
            continue
        pending = _extract_todolist_feedback_list(record.get("payload") or {})
        if pending is not None:
            return pending
    return None


def _resolve_todolist_state_for_summary(state: Dict[str, Any], messages: List[Dict[str, Any]]) -> Any:
    raw_state = state.get("todolist") if isinstance(state, dict) else None
    if isinstance(raw_state, list) and raw_state:
        return raw_state
    pending_todolist = _extract_pending_todolist_from_state(state)
    if pending_todolist is not None:
        return pending_todolist
    latest_from_messages = _extract_latest_todolist_from_messages(messages)
    if latest_from_messages is not None:
        return latest_from_messages
    if raw_state is not None:
        return raw_state
    return None


def _extract_parsed_files(messages: List[Dict[str, Any]]) -> List[str]:
    paths: List[str] = []
    seen = set()
    pattern = re.compile(r"/mnt/data/parser_upload/[^\s)\"']+\.md")
    for msg in messages:
        content = str(msg.get("content", ""))
        for match in pattern.findall(content):
            if match not in seen:
                seen.add(match)
                paths.append(match)
    return paths


def _collect_uploaded_files_state(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    files = (state.get("asset_index") or {}).get("files") or []
    collected: List[Dict[str, Any]] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        collected.append(
            {
                "file_id": item.get("file_id"),
                "name": item.get("name"),
                "path": item.get("storage_path"),
                "sandbox_path": item.get("sandbox_path"),
            }
        )
    return collected


def _collect_parsed_files_state(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    asset_index = state.get("asset_index") or {}
    files = asset_index.get("files") or []
    parsed_artifacts = asset_index.get("parsed_artifacts") or []
    file_names = {
        str(item.get("file_id")): item.get("name")
        for item in files
        if isinstance(item, dict) and item.get("file_id")
    }
    collected: List[Dict[str, Any]] = []
    for item in parsed_artifacts:
        if not isinstance(item, dict):
            continue
        source_file_id = str(item.get("source_file_id") or "").strip()
        collected.append(
            {
                "source_file_id": source_file_id or None,
                "name": file_names.get(source_file_id),
                "parsed_path": item.get("storage_path"),
                "summary": item.get("summary"),
            }
        )
    return collected


def _record_identity(item: Any, candidates: Tuple[str, ...]) -> Optional[str]:
    if not isinstance(item, dict):
        return None
    for key in candidates:
        value = str(item.get(key) or "").strip()
        if value:
            return f"{key}:{value}"
    return None


def _merge_state_records(
    existing: List[Dict[str, Any]],
    incoming: List[Dict[str, Any]],
    *,
    identity_keys: Tuple[str, ...],
) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    index: Dict[str, int] = {}
    for source in ((existing or []), (incoming or [])):
        for item in source:
            if not isinstance(item, dict):
                continue
            identity = _record_identity(item, identity_keys)
            payload = deepcopy(item)
            if identity is None:
                merged.append(payload)
                continue
            if identity in index:
                merged[index[identity]].update(payload)
            else:
                index[identity] = len(merged)
                merged.append(payload)
    return merged


def _extract_offloaded_files_state(summary_xml: str) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = []
    seen = set()
    for block in re.findall(r"<file>(.*?)</file>", summary_xml, flags=re.DOTALL | re.IGNORECASE):
        filename = html.unescape(str(_extract_tag_content(block, "filename") or "").strip())
        path = html.unescape(str(_extract_tag_content(block, "path") or "").strip())
        description = html.unescape(str(_extract_tag_content(block, "description") or "").strip())
        identity = filename or path
        if not identity or identity in seen:
            continue
        seen.add(identity)
        files.append(
            {
                "filename": filename or None,
                "path": path or None,
                "description": description or None,
            }
        )
    return files


def _extract_latest_state_snapshot(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    default = {
        UPLOADED_FILES_STATE_TAG: [],
        PARSED_FILES_STATE_TAG: [],
        SAVED_FILES_STATE_TAG: [],
        CONTEXT_ARCHIVES_STATE_TAG: [],
        TODOLIST_STATE_TAG: [],
    }
    for msg in reversed(messages):
        if not _is_summary_message(msg):
            continue
        snapshot_raw = _extract_tag_content(str(msg.get("content", "")), STATE_SNAPSHOT_TAG)
        if not snapshot_raw:
            continue
        return {
            UPLOADED_FILES_STATE_TAG: _parse_json_payload(
                _extract_tag_content(snapshot_raw, UPLOADED_FILES_STATE_TAG),
                [],
            ),
            PARSED_FILES_STATE_TAG: _parse_json_payload(
                _extract_tag_content(snapshot_raw, PARSED_FILES_STATE_TAG),
                [],
            ),
            SAVED_FILES_STATE_TAG: _parse_json_payload(
                _extract_tag_content(snapshot_raw, SAVED_FILES_STATE_TAG),
                [],
            ),
            CONTEXT_ARCHIVES_STATE_TAG: _parse_json_payload(
                _extract_tag_content(snapshot_raw, CONTEXT_ARCHIVES_STATE_TAG),
                [],
            ),
            TODOLIST_STATE_TAG: _parse_json_payload(
                _extract_tag_content(snapshot_raw, TODOLIST_STATE_TAG),
                [],
            ),
        }
    return default


def _build_noop_summary_xml(
    lang: str,
    *,
    uploaded_files_state: Optional[List[Dict[str, Any]]] = None,
    parsed_files_state: Optional[List[Dict[str, Any]]] = None,
    todolist_state: Any = None,
) -> str:
    uploaded_files_state = uploaded_files_state or []
    parsed_files_state = parsed_files_state or []
    todolist_state = todolist_state or []

    if lang == "zh":
        knowledge_lines = [
            "本轮没有额外旧消息被裁入 summary；当前上下文主要通过保留的实时消息继续承接。",
            "上传文件、解析文件和 todolist 已通过结构化状态快照保留，后续继续执行时应优先读取这些状态。",
        ]
        if uploaded_files_state:
            file_names = "、".join(
                str(item.get("name") or item.get("path") or "").strip()
                for item in uploaded_files_state[:5]
                if isinstance(item, dict)
            )
            if file_names:
                knowledge_lines.append(f"当前上传文件：{file_names}")
        if parsed_files_state:
            parsed_names = "、".join(
                str(item.get("name") or item.get("parsed_path") or "").strip()
                for item in parsed_files_state[:5]
                if isinstance(item, dict)
            )
            if parsed_names:
                knowledge_lines.append(f"当前解析产物：{parsed_names}")
        if todolist_state:
            count = len(todolist_state) if isinstance(todolist_state, list) else 1
            knowledge_lines.append(f"当前 todolist 项数：{count}")
        return (
            "<summary>"
            f"<key_knowledge>{_xml_escape(chr(10).join(knowledge_lines))}</key_knowledge>"
            "<recent_actions>没有旧消息被裁掉；已刷新结构化状态快照并保留实时上下文。</recent_actions>"
            "</summary>"
            "<offloaded_files></offloaded_files>"
        )

    knowledge_lines = [
        "No historical messages were trimmed into the summary in this pass; live context remains the main continuation source.",
        "Uploaded files, parsed artifacts, and todolist state are preserved in the structured snapshot and should be treated as authoritative.",
    ]
    if uploaded_files_state:
        file_names = ", ".join(
            str(item.get("name") or item.get("path") or "").strip()
            for item in uploaded_files_state[:5]
            if isinstance(item, dict)
        )
        if file_names:
            knowledge_lines.append(f"Uploaded files: {file_names}")
    if parsed_files_state:
        parsed_names = ", ".join(
            str(item.get("name") or item.get("parsed_path") or "").strip()
            for item in parsed_files_state[:5]
            if isinstance(item, dict)
        )
        if parsed_names:
            knowledge_lines.append(f"Parsed artifacts: {parsed_names}")
    if todolist_state:
        count = len(todolist_state) if isinstance(todolist_state, list) else 1
        knowledge_lines.append(f"Todolist item count: {count}")
    return (
        "<summary>"
        f"<key_knowledge>{_xml_escape(chr(10).join(knowledge_lines))}</key_knowledge>"
        "<recent_actions>No old messages were trimmed; refreshed the structured snapshot and kept the live context.</recent_actions>"
        "</summary>"
        "<offloaded_files></offloaded_files>"
    )


def _is_deep_research_enabled(
    state: Optional[Dict[str, Any]],
    config: Optional[Dict[str, Any]],
) -> bool:
    if isinstance(state, dict):
        metadata = state.get("session_metadata") or {}
        if "deep_research_enabled" in metadata:
            return bool(metadata.get("deep_research_enabled"))
    runtime_cfg = (config or {}).get("runtime") if isinstance(config, dict) else {}
    runtime_cfg = runtime_cfg if isinstance(runtime_cfg, dict) else {}
    deep_research_cfg = runtime_cfg.get("deep_research") or {}
    if isinstance(deep_research_cfg, dict):
        return bool(deep_research_cfg.get("enabled", False))
    return False

def _build_summary_request_prompt(
    *,
    lang: str,
    todo_list: Any,
    uploaded_files: List[Dict[str, Any]],
    parsed_files: List[str],
    deep_research_enabled: bool,
) -> str:
    try:
        todo_payload = json.dumps(todo_list, ensure_ascii=False)
    except Exception:
        todo_payload = str(todo_list)
    try:
        uploaded_payload = json.dumps(uploaded_files, ensure_ascii=False)
    except Exception:
        uploaded_payload = str(uploaded_files)
    try:
        parsed_payload = json.dumps(parsed_files, ensure_ascii=False)
    except Exception:
        parsed_payload = str(parsed_files)

    base_prompt = smart_optimize_prompt_zh if lang == "zh" else smart_optimize_prompt_en
    if lang == "zh":
        deep_research_block = ""
        if deep_research_enabled:
            deep_research_block = """
## Deep Research 强化保留规则
1. 这是深度研究场景，摘要必须尽量保留所有子任务结果、工具执行结果和已验证事实，默认宁可更长也不要丢失信息。
2. 不要只保留最终结论；每个子任务中仍可能被正文使用的政策条目、时间点、数字、定义、例外、局部比较、未完成发现都应尽量保留。
3. 如果多个子任务分别覆盖不同维度，必须分维度保留，不要为了“更简洁”而把独特结果合并抹平。
4. 对研究报告写作场景，`execution_result`、可靠 `tool_result`、局部结论和 open issues 都属于高价值上下文，除非明显重复，否则不要删掉。
5. 如果子任务结果、证据摘录或分维度研究材料过长，无法安全放进 `<summary>`，应优先写入 `<offload_files>` 保存，并在 `key_knowledge` 中说明该文件保存了什么、后续应如何引用，而不是直接丢弃细节。
"""
        return f"""{base_prompt}

## 当前任务
你现在不是继续上方原始对话，而是对上方真实历史消息做上下文裁剪摘要。
请输出像 Codex compact 一样的高密度结构化交接摘要：短、准、保真、可继续执行。

## 当前结构化状态提示
这些内容只用于帮助你理解当前上下文，系统稍后会自动注入权威状态快照：
TODOLIST_STATE: {todo_payload}
UPLOADED_FILES_STATE: {uploaded_payload}
PARSED_FILES: {parsed_payload}

## 额外保留要求
0. 你前面看到的是被裁掉的真实历史消息，不是 JSON；这条消息只是总结指令本身，不属于要被总结的历史内容。
1. 本次传给你的历史消息，只包含“即将被裁掉并需要进入 summary 的部分”；被保留在实时上下文里的最近对话不会出现在输入里，因此不要试图替它们做全量总结。
2. 摘要要让下一个模型可以直接继续工作，不要只写“已完成分析”“继续处理”这种空话。
3. 优先保留具体事实：文件名、路径、变量名、接口名、命令、参数、约束、阈值、决定、待确认项。
4. 如果存在未完成事项，请明确写出：已经做到哪一步、卡在哪、下一步最应该做什么。
5. `key_knowledge` 用 compact 小节或紧凑标签行来写，每行一个事实；不要写冗长分节散文。
6. 不要把多个工具结果、多个文档发现或多个风险判断压成一句抽象话；如果它们分别重要，就分行写出来。
7. 对文档、PDF、表格、风控、审核类任务，要保留“结论/标签/严重级别 + 证据或数字 + 文件位置（若有）”。
8. `TODOLIST_STATE`、`UPLOADED_FILES_STATE`、`PARSED_FILES` 是流程注入的结构化状态提示，不是你要自己生成的摘要字段。
9. 你可以利用这些注入状态避免丢失计划或文件上下文，但不要在正文里机械输出 `TODOLIST_STATE:`、`UPLOADED_FILES_STATE:`、`PARSED_FILES:` 这种字面头。
10. 用户消息里若原本带有 `<uploads>` 附件块，这些附件元数据已经被系统抽离并并入 `UPLOADED_FILES_STATE` / `PARSED_FILES`；不要在输出中复述原始 `<uploads>` XML，只有当它们会影响继续执行时，才改写成紧凑状态事实。
11. 文件信息优先放进 `key_knowledge` 的紧凑行里，并说明文件为什么重要；不要为了格式再重复输出一遍冗余文件区块。
12. `recent_actions` 只保留最近真正完成的关键动作和结果，避免过程噪声。
13. 即使没有很多旧消息，也不要输出空洞的“无需总结”；要结合结构化状态写出可执行的交接信息。
14. 如果某段高价值长文本当前只存在于消息或 tool response 中、后续仍可能需要原样复用，请优先把它写入 `<offload_files>`，不要只在 `<summary>` 里压成几句。
15. `<offload_files>` 的职责是把“消息承载的有用 artifact”物化成文件；`<file_content>` 应写可复用正文，`<desc>` 应说明来源、用途和后续如何使用。
16. 只输出 XML，不要额外解释。
{deep_research_block}
"""

    deep_research_block = ""
    if deep_research_enabled:
        deep_research_block = """
## Deep Research Lossless Retention Rules
1. This is a deep research run. Preserve all subtask results, tool execution results, and verified findings as aggressively as possible; prefer longer summaries over losing material.
2. Do not keep only top-line conclusions. Preserve policy items, dates, figures, definitions, exceptions, local comparisons, and unresolved findings from each subtask whenever they may still matter.
3. If different subtasks cover different dimensions, keep them separated by dimension instead of flattening them into a shorter generic conclusion.
4. For research-report workflows, `execution_result`, reliable `tool_result`, local conclusions, and open issues are all high-value context. Drop them only when they are clearly duplicate noise.
5. If subtask results, evidence extracts, or dimension-by-dimension research material are too long to fit safely in `<summary>`, write them to `<offload_files>` and keep a precise pointer in `key_knowledge` describing what was saved and how it should be referenced later.
"""
    return f"""{base_prompt}

## Current Task
You are not continuing the original conversation above. You are compressing the real historical messages above into a context-handoff summary.
Produce a Codex-compact structured handoff that is dense, precise, loss-aware, and directly executable.

## Structured State Hints
These are guidance signals only. The system will append the authoritative state snapshot separately:
TODOLIST_STATE: {todo_payload}
UPLOADED_FILES_STATE: {uploaded_payload}
PARSED_FILES: {parsed_payload}

## Additional Retention Rules
0. What you saw before this message were real trimmed historical messages, not a JSON blob; this message is only the summarization instruction and is not part of the historical content.
1. The historical messages provided to you are only the portion that will be trimmed into the summary. The most recent retained live context is intentionally excluded, so do not try to re-summarize missing turns.
2. Write the summary so that the next model can continue the task immediately. Avoid vague lines like "analysis completed" or "continue processing".
3. Preserve concrete facts whenever available: file names, paths, identifiers, APIs, commands, parameters, thresholds, constraints, decisions, and pending confirmations.
4. If work is unfinished, state exactly what is done, what is blocked, and what the next best action is.
5. Write `key_knowledge` as compact mini-sections or compact labeled lines, one fact per line whenever possible; avoid verbose section prose.
6. Do not collapse multiple tool results, document findings, or risk judgments into one abstract sentence; if they matter separately, keep them separately.
7. For document, PDF, table, audit, or risk-review tasks, preserve `judgment/label/severity + evidence or numbers + file location` when available.
8. `TODOLIST_STATE`, `UPLOADED_FILES_STATE`, and `PARSED_FILES` are workflow-injected state hints and do not need to be summarized.
9. If user messages originally contained `<uploads>` blocks, the system has already extracted those attachment details into `UPLOADED_FILES_STATE` / `PARSED_FILES`; do not copy raw `<uploads>` XML into the output, and only restate them as compact facts when they materially affect continuation.
10. Keep file facts inside compact `key_knowledge` lines, explain why a file matters, and avoid repeating them in a redundant second file section unless extra detail is truly needed.
11. `recent_actions` should keep only the latest meaningful completed actions and outcomes, not process noise.
12. If a high-value long text currently exists only in a message or tool response and may need to be reused verbatim later, prefer writing it to `<offload_files>` instead of compressing it into a few lines.
13. `<offload_files>` is for turning message-backed useful artifacts into reusable files; `<file_content>` should contain the reusable body, and `<desc>` should explain source, purpose, and next use.
14. Even when little historical text remains, do not emit a vague "nothing to summarize" placeholder; produce actionable handoff grounded in the structured state.
15. Output XML only. No extra prose.
{deep_research_block}
"""


def _resolve_message_save_dir(config: Optional[Dict[str, Any]]) -> str:
    tool_cfg = (((config or {}).get("tools") or {}).get("memory_compression_and_offload") or {}).get("config") or {}
    archive_dir = str(tool_cfg.get("message_save_dir") or DEFAULT_CONTEXT_ARCHIVE_DIR).strip().strip("/")
    return archive_dir or DEFAULT_CONTEXT_ARCHIVE_DIR


def _normalize_offload_filename(filename: str, names_seen: set[str]) -> str:
    raw = str(filename or "").strip().replace("\\", "/")
    raw = raw.split("/")[-1]
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("._")
    if not safe:
        safe = "offloaded_asset.txt"
    if "." not in safe:
        safe = f"{safe}.txt"

    base, ext = os.path.splitext(safe)
    candidate = safe
    suffix = 1
    while candidate in names_seen:
        suffix += 1
        candidate = f"{base}_{suffix}{ext or '.txt'}"
    names_seen.add(candidate)
    return candidate


def _save_content(
    *,
    content: str,
    filename: str,
    config: Optional[Dict[str, Any]],
    names_seen: set[str],
) -> Optional[Tuple[str, str]]:
    normalized_filename = _normalize_offload_filename(filename, names_seen)
    sandbox_path = f"/mnt/data/{_resolve_message_save_dir(config)}/{normalized_filename}"
    try:
        client, session_id = _get_sandbox_meta_from_config()
        upload_file_to_sandbox(
            sandbox_uri=f"sandbox:{sandbox_path}",
            client=client,
            content=content.encode("utf-8"),
            session_id=session_id,
        )
        return sandbox_path, normalized_filename
    except Exception as exc:
        logger.warning("沙盒上传失败，跳过 offload 文件写入: %s", exc)
        return None


def _default_summary_content(lang: str) -> str:
    if lang == "zh":
        return (
            "<key_knowledge>未能稳定解析结构化摘要，保留本轮关键状态并继续执行。</key_knowledge>\n"
            "<recent_actions>执行了智能上下文分析，但返回格式不完整。</recent_actions>"
        )
    return (
        "<key_knowledge>Structured summary parsing was incomplete; preserving key state for continuity.</key_knowledge>\n"
        "<recent_actions>Ran context analysis but received partially structured output.</recent_actions>"
    )


def _extract_offload_candidates(ai_response: str) -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    file_blocks = re.findall(r"<file>(.*?)</file>", ai_response, flags=re.DOTALL | re.IGNORECASE)
    for block in file_blocks:
        file_name = _extract_tag_content(block, "file_name") or _extract_tag_content(block, "filename")
        file_content = _extract_tag_content(block, "file_content") or _extract_tag_content(block, "content")
        if not file_name or file_content is None:
            continue
        description = _extract_tag_content(block, "desc") or _extract_tag_content(block, "description") or ""
        candidates.append(
            {
                "file_name": file_name,
                "file_content": _strip_cdata(file_content),
                "description": description.strip(),
            }
        )
    return candidates


def _execute_offload(
    *,
    ai_response: str,
    lang: str,
    config: Optional[Dict[str, Any]],
    fallback_summary_text: Optional[str] = None,
) -> str:
    summary_match = re.search(r"<summary>(.*?)</summary>", ai_response, flags=re.DOTALL | re.IGNORECASE)
    summary_content = summary_match.group(1).strip() if summary_match else ""
    if not _summary_content_is_usable(summary_content):
        summary_content = _fallback_summary_content(
            lang=lang,
            fallback_summary_text=fallback_summary_text,
        )

    file_buckets: Dict[str, Dict[str, Any]] = {}
    for candidate in _extract_offload_candidates(ai_response):
        file_name = str(candidate.get("file_name") or "").strip()
        file_content = str(candidate.get("file_content") or "")
        if not file_name or not file_content.strip():
            continue
        bucket = file_buckets.setdefault(
            file_name,
            {
                "contents": [],
                "description": str(candidate.get("description") or "").strip(),
            },
        )
        bucket["contents"].append(file_content)
        if not bucket.get("description") and candidate.get("description"):
            bucket["description"] = str(candidate.get("description") or "").strip()

    offloaded_files: List[Dict[str, Any]] = []
    names_seen: set[str] = set()
    for file_name, bucket in file_buckets.items():
        combined_content = "\n\n".join(bucket["contents"]).rstrip()
        if not combined_content:
            continue
        saved = _save_content(
            content=combined_content,
            filename=file_name,
            config=config,
            names_seen=names_seen,
        )
        if not saved:
            continue
        path, saved_name = saved
        offloaded_files.append(
            {
                "path": path,
                "filename": saved_name,
                "description": bucket.get("description", ""),
            }
        )

    files_xml = ""
    if offloaded_files:
        file_entries = []
        for item in offloaded_files:
            file_entries.append(
                "    <file>"
                f"<filename>{_xml_escape(item['filename'])}</filename>"
                f"<path>{_xml_escape(item['path'])}</path>"
                f"<description>{_xml_escape(item['description'])}</description>"
                "</file>"
            )
        files_xml = "\n" + "\n".join(file_entries) + "\n    "

    return f"""<summary>
        {summary_content}
    </summary>
    <offloaded_files>{files_xml}</offloaded_files>"""


def _generate_summary_xml(
    *,
    llm: BaseLLM,
    compiled_messages: List[Dict[str, Any]],
    summary_input_indices: List[int],
    lang: str,
    todo_list: Any,
    uploaded_files: List[Dict[str, Any]],
    parsed_files: List[str],
    deep_research_enabled: bool,
    config: Optional[Dict[str, Any]],
    fallback_summary_text: Optional[str] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    summary_user_message = {
        "role": "user",
        "content": _build_summary_request_prompt(
            lang=lang,
            todo_list=todo_list,
            uploaded_files=uploaded_files,
            parsed_files=parsed_files,
            deep_research_enabled=deep_research_enabled,
        ),
    }

    source_messages = _sanitize_messages_for_summary_request(compiled_messages, lang=lang)
    request_messages: List[Dict[str, Any]] = []
    if summary_input_indices:
        first_summary_index = min(summary_input_indices)
        if first_summary_index > 0:
            request_messages.extend(
                deepcopy(
                    [
                        message
                        for message in source_messages[:first_summary_index]
                        if message.get("role") == "system" or message.get("is_summary")
                    ]
                )
            )
        request_messages.extend(deepcopy([source_messages[index] for index in summary_input_indices]))
    request_messages.append(summary_user_message)

    response = llm.completion(request_messages)
    ai_response = response.get("content", "")
    result_xml = _execute_offload(
        ai_response=ai_response,
        lang=lang,
        config=config,
        fallback_summary_text=fallback_summary_text,
    )
    generation_messages = deepcopy(request_messages)
    generation_messages.append({"role": "assistant", "content": ai_response, "is_summary_generation": True})
    return result_xml, generation_messages


def compact_conversation_context(
    *,
    state: Dict[str, Any],
    llm: BaseLLM,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not isinstance(state, dict):
        raise ValueError("state is required")
    if llm is None:
        raise ValueError("llm is required")

    if "message_records" in state:
        rebuild_compiled_messages(state)
    compiled_messages = state.get("messages") or []
    if not compiled_messages:
        raise ValueError("state['messages'] is empty")

    runtime_lang = _resolve_runtime_language(state, config)
    trimmed_messages, summary_input_messages, selection = _select_compaction_messages(
        compiled_messages,
        config=config,
    )

    previous_snapshot = _extract_latest_state_snapshot(compiled_messages)
    resolved_todo_list = _resolve_todolist_state_for_summary(state, compiled_messages)
    current_uploaded_files = _collect_uploaded_files_state(state)
    current_parsed_files = _collect_parsed_files_state(state)
    if not current_parsed_files:
        current_parsed_files = [{"parsed_path": path} for path in _extract_parsed_files(compiled_messages)]

    prepared_messages, summarized_uploaded_files, summarized_parsed_files = _prepare_messages_for_summary(
        summary_input_messages,
        lang=runtime_lang,
    )
    uploaded_files_state = _merge_state_records(
        previous_snapshot.get(UPLOADED_FILES_STATE_TAG) or [],
        current_uploaded_files,
        identity_keys=("file_id", "path", "name"),
    )
    uploaded_files_state = _merge_state_records(
        uploaded_files_state,
        summarized_uploaded_files,
        identity_keys=("file_id", "path", "name"),
    )
    parsed_files_state = _merge_state_records(
        previous_snapshot.get(PARSED_FILES_STATE_TAG) or [],
        current_parsed_files,
        identity_keys=("parsed_path", "path", "name"),
    )
    parsed_files_state = _merge_state_records(
        parsed_files_state,
        summarized_parsed_files,
        identity_keys=("parsed_path", "path", "name"),
    )

    deep_research_enabled = _is_deep_research_enabled(state, config)
    previous_summary_text = _latest_summary_text(compiled_messages)
    if prepared_messages:
        summary_xml, summary_generation_messages = _generate_summary_xml(
            llm=llm,
            compiled_messages=compiled_messages,
            summary_input_indices=selection.get("summary_input_indices") or [],
            lang=runtime_lang,
            todo_list=resolved_todo_list,
            uploaded_files=uploaded_files_state,
            parsed_files=[
                item.get("parsed_path") or item.get("path") or item.get("summary") or ""
                for item in parsed_files_state
                if isinstance(item, dict)
            ],
            deep_research_enabled=deep_research_enabled,
            config=config,
            fallback_summary_text=previous_summary_text,
        )
    else:
        summary_xml = _build_noop_summary_xml(
            runtime_lang,
            uploaded_files_state=uploaded_files_state,
            parsed_files_state=parsed_files_state,
            todolist_state=resolved_todo_list,
        )
        summary_generation_messages = []

    if uploaded_files_state:
        if runtime_lang == "zh":
            summary_xml = _inject_key_knowledge_line(
                summary_xml,
                f"结构化状态中保留了 {len(uploaded_files_state)} 个上传文件条目。",
            )
        else:
            summary_xml = _inject_key_knowledge_line(
                summary_xml,
                f"The structured state preserves {len(uploaded_files_state)} uploaded file entries.",
            )
    if resolved_todo_list:
        todo_count = len(resolved_todo_list) if isinstance(resolved_todo_list, list) else 1
        if runtime_lang == "zh":
            summary_xml = _inject_key_knowledge_line(
                summary_xml,
                f"结构化状态中保留了 todolist，共 {todo_count} 项。",
            )
        else:
            summary_xml = _inject_key_knowledge_line(
                summary_xml,
                f"The structured state preserves the todolist with {todo_count} item(s).",
            )

    logger.info(
        (
            "summary scope selected: compiled_messages=%s retained_round_records=%s "
            "retained_user_records=%s trimmed_records=%s deep_research=%s"
        ),
        selection.get("compiled_message_count"),
        len(selection.get("retained_round_record_ids") or []),
        len(selection.get("retained_user_record_ids") or []),
        len(selection.get("summarized_record_ids") or []),
        deep_research_enabled,
    )

    saved_files_state = _merge_state_records(
        previous_snapshot.get(SAVED_FILES_STATE_TAG) or [],
        _extract_offloaded_files_state(summary_xml),
        identity_keys=("path", "filename"),
    )

    return apply_summary_offload_to_conversation_state(
        state,
        summary_text=summary_xml,
        selection=selection,
        summary_generation_messages=summary_generation_messages,
        trimmed_compiled_messages=trimmed_messages,
        uploaded_files_state=uploaded_files_state,
        parsed_files_state=parsed_files_state,
        saved_files_state=saved_files_state,
        todolist_state=resolved_todo_list,
        payload={
            "source": "summary_offload",
            "language": runtime_lang,
        },
        config=config,
    )
