import json
import re
import uuid
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.utils.context_token_utils import summarize_message_token_usage


STATE_VERSION = 3
_INTERNAL_PROMPT_BLOCK_TAGS = (
    "file_context",
    "current_active_editor_projection",
    "PRELOADED_CONTEXT",
    "RETRIEVED_CONTEXT",
)
_INTERNAL_SUMMARY_CHILD_TAGS = (
    "overall_goal",
    "key_knowledge",
    "recent_actions",
    "important_files",
    "state_snapshot",
    "uploaded_files_state",
    "parsed_files_state",
    "saved_files_state",
    "context_archives_state",
    "todolist_state",
)
DEFAULT_RECENT_ROUNDS_TOKEN_BUDGET_RATIO = 0.4
DEFAULT_USER_TOKEN_BUDGET_RATIO = 0.2
DEFAULT_CONTEXT_ARCHIVE_DIR = "message_offload"
STATE_SNAPSHOT_TAG = "state_snapshot"
UPLOADED_FILES_STATE_TAG = "uploaded_files_state"
PARSED_FILES_STATE_TAG = "parsed_files_state"
SAVED_FILES_STATE_TAG = "saved_files_state"
CONTEXT_ARCHIVES_STATE_TAG = "context_archives_state"
TODOLIST_STATE_TAG = "todolist_state"
SUMMARY_PROMPT_STATE_KEY = "_summary_prompt"
_REDUNDANT_RUNTIME_CONTROL_FIELDS = (
    "active_run_id",
    "current_input_locale",
    "current_tool_locale",
)
_SUPPORTED_PROJECTION_FIELDS = (
    "current_active_editor_projection",
)


def _iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _deepcopy_jsonable(value: Any) -> Any:
    try:
        return deepcopy(value)
    except Exception:
        return value


def _get_summary_prompt_state(record: Dict[str, Any]) -> Dict[str, Any]:
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return {}
    marker = payload.get(SUMMARY_PROMPT_STATE_KEY)
    if not isinstance(marker, dict):
        return {}
    return marker


def _record_is_summary_compacted(record: Dict[str, Any]) -> bool:
    return bool(_get_summary_prompt_state(record).get("compacted"))


def _set_summary_prompt_state(
    record: Dict[str, Any],
    *,
    compacted: bool,
    summary_id: Optional[str],
    summary_kind: Optional[str],
) -> Dict[str, Any]:
    updated = _deepcopy_jsonable(record)
    payload = updated.get("payload")
    if not isinstance(payload, dict):
        payload = {}
    else:
        payload = _deepcopy_jsonable(payload)

    if compacted:
        payload[SUMMARY_PROMPT_STATE_KEY] = {
            "compacted": True,
            "summary_id": str(summary_id or "").strip() or None,
            "summary_kind": str(summary_kind or "").strip() or None,
        }
    else:
        payload.pop(SUMMARY_PROMPT_STATE_KEY, None)

    updated["payload"] = payload
    return updated


def _parse_jsonish(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    trimmed = value.strip()
    if not trimmed or trimmed[0] not in "{[":
        return value
    try:
        return json.loads(trimmed)
    except Exception:
        return value


def _resolve_positive_int(value: Any) -> Optional[int]:
    try:
        resolved = int(value) if value is not None else None
    except (TypeError, ValueError):
        resolved = None
    if resolved is None or resolved <= 0:
        return None
    return resolved


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _extract_tag_content(text: Any, tag: str) -> Optional[str]:
    if text is None:
        return None
    match = re.search(
        rf"<{tag}>(.*?)</{tag}>",
        str(text),
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return None
    return match.group(1).strip()


def _remove_xml_block(text: str, tag: str) -> str:
    return re.sub(
        rf"\s*<{tag}\b[^>]*>\s*[\s\S]*?\s*</{tag}>\s*",
        "\n",
        text,
        flags=re.IGNORECASE,
    )


def _remove_orphan_xml_tag_lines(text: str, tag: str) -> str:
    return re.sub(
        rf"(?im)^[ \t]*</?{tag}\b[^>]*>[ \t]*\n?",
        "",
        text,
    )


def sanitize_assistant_output_text(text: Optional[str]) -> str:
    raw = str(text or "")
    if not raw:
        return ""

    sanitized = raw
    for tag in _INTERNAL_PROMPT_BLOCK_TAGS:
        sanitized = _remove_xml_block(sanitized, tag)

    if re.search(r"<summary\b", sanitized, flags=re.IGNORECASE):
        lowered = sanitized.lower()
        if any(f"<{tag}>" in lowered for tag in _INTERNAL_SUMMARY_CHILD_TAGS):
            sanitized = _remove_xml_block(sanitized, "summary")

    for tag in (*_INTERNAL_PROMPT_BLOCK_TAGS, "summary", *_INTERNAL_SUMMARY_CHILD_TAGS):
        sanitized = _remove_orphan_xml_tag_lines(sanitized, tag)

    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)
    return sanitized.strip()


def _normalize_locale(locale: Optional[str]) -> Optional[str]:
    if not locale:
        return None
    value = str(locale).strip()
    if not value:
        return None
    lower = value.lower()
    if lower.startswith("zh"):
        return "zh-CN"
    if lower.startswith("en"):
        return "en-US"
    return value


def detect_locale(text: Optional[str], default_locale: Optional[str] = None) -> str:
    source = str(text or "")
    if not source.strip():
        return _normalize_locale(default_locale) or "zh-CN"

    cjk_count = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", source))
    latin_count = len(re.findall(r"[A-Za-z]", source))
    # 中文查询里常会夹杂产品名、命令、路径等拉丁字符；这类场景不应因为少量英文片段误判为英文会话。
    if cjk_count >= 2 and (latin_count == 0 or cjk_count * 2 >= latin_count):
        return "zh-CN"
    if latin_count >= max(4, cjk_count * 2):
        return "en-US"
    if cjk_count > 0:
        return "zh-CN"
    if latin_count > 0:
        return "en-US"
    return _normalize_locale(default_locale) or "zh-CN"


def empty_conversation_state(
    *,
    conversation_id: Optional[str] = None,
    preferred_locale: Optional[str] = None,
) -> Dict[str, Any]:
    timestamp = _iso_now()
    return {
        "state_version": STATE_VERSION,
        "conversation_id": str(conversation_id or "").strip() or None,
        "message_records": [],
        "asset_index": {
            "files": [],
            "parsed_artifacts": [],
        },
        "runtime_control": {
            "conversation_status": "idle",
            "current_prompt_locale": None,
            "supports_ask_user": True,
            "pending_ask_user_message_id": None,
            "pending_ask_user_request_id": None,
            "pending_subtask_ids": [],
            "active_subtask_id": None,
            "subtask_counter": 0,
            "reflection_counter": 0,
            "subtasks": {},
            "pause_reason": None,
            "termination_requested_at": None,
            "termination_reason": None,
            "last_error": None,
            "active_agent": "main_agent",
            "global_loops": 0,
            "global_loops_limit": None,
        },
        "session_metadata": {
            "conversation_title": None,
            "preferred_locale": _normalize_locale(preferred_locale),
            "deep_research_enabled": False,
            "created_at": timestamp,
            "updated_at": timestamp,
            "memory_fingerprint": None,
        },
        "todolist": [],
        "projections": {
            "current_active_editor_projection": None,
        },
    }


def ensure_conversation_state(
    raw: Optional[Dict[str, Any]],
    *,
    refresh_updated_at: bool = True,
) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return empty_conversation_state()

    state = deepcopy(raw)
    if state.get("state_version") != STATE_VERSION:
        state["state_version"] = STATE_VERSION
    state.setdefault("conversation_id", None)

    if not isinstance(state.get("message_records"), list):
        state["message_records"] = []

    asset_index = state.get("asset_index")
    if not isinstance(asset_index, dict):
        asset_index = {}
    asset_index.setdefault("files", [])
    asset_index.setdefault("parsed_artifacts", [])
    state["asset_index"] = asset_index

    runtime = state.get("runtime_control")
    if not isinstance(runtime, dict):
        runtime = {}
    defaults_runtime = empty_conversation_state().get("runtime_control", {})
    for key, value in defaults_runtime.items():
        runtime.setdefault(key, deepcopy(value))
    for key in _REDUNDANT_RUNTIME_CONTROL_FIELDS:
        runtime.pop(key, None)
    state["runtime_control"] = runtime

    metadata = state.get("session_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    defaults_meta = empty_conversation_state().get("session_metadata", {})
    for key, value in defaults_meta.items():
        metadata.setdefault(key, deepcopy(value))
    state["session_metadata"] = metadata

    todolist = state.get("todolist")
    if not isinstance(todolist, list):
        todolist = []
    state["todolist"] = _deepcopy_jsonable(todolist)

    raw_projections = state.get("projections")
    if not isinstance(raw_projections, dict):
        raw_projections = {}
    projections = {}
    for key in _SUPPORTED_PROJECTION_FIELDS:
        value = raw_projections.get(key)
        projections[key] = _deepcopy_jsonable(value) if isinstance(value, dict) and value else None
    state["projections"] = projections

    if refresh_updated_at:
        touch_updated_at(state)
    return state


def touch_updated_at(state: Dict[str, Any]) -> None:
    metadata = state.setdefault("session_metadata", {})
    metadata["updated_at"] = _iso_now()
    if not metadata.get("created_at"):
        metadata["created_at"] = metadata["updated_at"]


def extract_persistable_state(
    state: Dict[str, Any],
    *,
    refresh_updated_at: bool = True,
) -> Dict[str, Any]:
    source = state if "message_records" in state else state.get("main_state", {})
    base = ensure_conversation_state(
        source if isinstance(source, dict) else {},
        refresh_updated_at=refresh_updated_at,
    )
    return {
        "state_version": base["state_version"],
        "conversation_id": base.get("conversation_id"),
        "message_records": _deepcopy_jsonable(base["message_records"]),
        "asset_index": _deepcopy_jsonable(base["asset_index"]),
        "runtime_control": _deepcopy_jsonable(base["runtime_control"]),
        "session_metadata": _deepcopy_jsonable(base["session_metadata"]),
        "todolist": _deepcopy_jsonable(base["todolist"]),
        "projections": _deepcopy_jsonable(base["projections"]),
    }


def attach_shared_layers(target_state: Dict[str, Any], conversation_state: Dict[str, Any]) -> Dict[str, Any]:
    target_state["state_version"] = conversation_state["state_version"]
    target_state["conversation_id"] = conversation_state.get("conversation_id")
    target_state["message_records"] = conversation_state["message_records"]
    target_state["asset_index"] = conversation_state["asset_index"]
    target_state["runtime_control"] = conversation_state["runtime_control"]
    target_state["session_metadata"] = conversation_state["session_metadata"]
    target_state["todolist"] = conversation_state["todolist"]
    target_state["projections"] = conversation_state["projections"]
    return target_state


def _ensure_record_fields(record: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {
        "id": record.get("id") or _new_id("rec"),
        "created_at": record.get("created_at") or _iso_now(),
        "type": record.get("type") or "audit_event",
        "text": record.get("text") or "",
        "payload": _deepcopy_jsonable(record.get("payload") or {}),
        "uploads": _deepcopy_jsonable(record.get("uploads") or []),
        "refs": _deepcopy_jsonable(record.get("refs") or []),
        "subtask_id": record.get("subtask_id"),
        "parent_id": record.get("parent_id"),
        "source": record.get("source") or "runtime",
        "version": int(record.get("version") or 1),
    }
    for key in (
        "input_kind",
        "language",
        "language_confidence",
        "tool_name",
        "tool_call_id",
        "scope",
        "consumes_tool_call_ids",
        "superseded_at",
        "summary_kind",
        "summary_inserted",
        "hidden",
    ):
        if key in record:
            normalized[key] = _deepcopy_jsonable(record.get(key))
    return normalized


def append_record(state: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
    normalized = _ensure_record_fields(record)
    state.setdefault("message_records", []).append(normalized)
    touch_updated_at(state)
    return normalized


def add_system_context(
    state: Dict[str, Any],
    *,
    text: str,
    payload: Optional[Dict[str, Any]] = None,
    source: str = "system",
) -> Dict[str, Any]:
    return append_record(
        state,
        {
            "type": "system_context",
            "text": str(text or ""),
            "payload": payload or {},
            "source": source,
        },
    )


def add_user_input(
    state: Dict[str, Any],
    *,
    text: Optional[str],
    input_kind: str = "text",
    payload: Optional[Dict[str, Any]] = None,
    uploads: Optional[List[Dict[str, Any]]] = None,
    refs: Optional[List[Dict[str, Any]]] = None,
    language: Optional[str] = None,
    language_confidence: float = 0.98,
    parent_id: Optional[str] = None,
    source: str = "user",
) -> Dict[str, Any]:
    resolved_locale = _normalize_locale(language) or detect_locale(text, (state.get("session_metadata") or {}).get("preferred_locale"))
    record = append_record(
        state,
        {
            "type": "user_input",
            "input_kind": input_kind,
            "text": str(text or ""),
            "payload": payload or {},
            "uploads": uploads or [],
            "refs": refs or [],
            "language": resolved_locale,
            "language_confidence": language_confidence,
            "parent_id": parent_id,
            "source": source,
        },
    )
    update_language_profile(state, resolved_locale, source_message_id=record["id"], confidence=language_confidence)
    return record


def clone_state_with_temporary_user_inputs(
    state: Dict[str, Any],
    *,
    temporary_inputs: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    temp_state = extract_persistable_state(state)
    for item in temporary_inputs or []:
        if not isinstance(item, dict):
            continue
        raw_confidence = item.get("language_confidence")
        try:
            resolved_confidence = float(raw_confidence) if raw_confidence is not None else 1.0
        except (TypeError, ValueError):
            resolved_confidence = 1.0
        add_user_input(
            temp_state,
            text=item.get("text"),
            input_kind=str(item.get("input_kind") or "text"),
            payload=_deepcopy_jsonable(item.get("payload") or {}),
            uploads=_deepcopy_jsonable(item.get("uploads") or []),
            refs=_deepcopy_jsonable(item.get("refs") or []),
            language=item.get("language"),
            language_confidence=resolved_confidence,
            parent_id=item.get("parent_id"),
            source=str(item.get("source") or "derived_prompt"),
        )
    return temp_state


def compile_messages_with_temporary_user_inputs(
    state: Dict[str, Any],
    *,
    temporary_inputs: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    temp_state = clone_state_with_temporary_user_inputs(
        state,
        temporary_inputs=temporary_inputs,
    )
    return compile_messages_for_llm(temp_state)


def compile_messages_with_temporary_user_input(
    state: Dict[str, Any],
    *,
    text: Optional[str],
    input_kind: str = "text",
    payload: Optional[Dict[str, Any]] = None,
    uploads: Optional[List[Dict[str, Any]]] = None,
    refs: Optional[List[Dict[str, Any]]] = None,
    language: Optional[str] = None,
    language_confidence: float = 1.0,
    parent_id: Optional[str] = None,
    source: str = "derived_prompt",
) -> List[Dict[str, Any]]:
    return compile_messages_with_temporary_user_inputs(
        state,
        temporary_inputs=[
            {
                "text": text,
                "input_kind": input_kind,
                "payload": payload or {},
                "uploads": uploads or [],
                "refs": refs or [],
                "language": language,
                "language_confidence": language_confidence,
                "parent_id": parent_id,
                "source": source,
            }
        ],
    )


def add_assistant_turn(
    state: Dict[str, Any],
    response: Dict[str, Any],
    *,
    source: str = "assistant",
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    sanitized_content = sanitize_assistant_output_text(response.get("content") or "")
    payload: Dict[str, Any] = {
        "total_usage": response.get("total_usage"),
        "provider_specific_fields": _deepcopy_jsonable(response.get("provider_specific_fields")),
    }
    thinking = response.get("thinking_content")
    if thinking:
        payload["thinking_content"] = _deepcopy_jsonable(thinking)
    thinking_blocks = response.get("thinking_blocks")
    if thinking_blocks:
        payload["thinking_blocks"] = _deepcopy_jsonable(thinking_blocks)
    assistant_record = append_record(
        state,
        {
            "type": "assistant_output",
            "text": sanitized_content,
            "payload": payload,
            "source": source,
        },
    )
    tool_records: List[Dict[str, Any]] = []
    for tool_call in response.get("tool_calls") or []:
        tool_records.append(
            append_record(
                state,
                {
                    "type": "tool_call",
                    "text": "",
                    "payload": _deepcopy_jsonable(tool_call),
                    "tool_name": (tool_call.get("function") or {}).get("name"),
                    "tool_call_id": tool_call.get("id"),
                    "parent_id": assistant_record["id"],
                    "source": source,
                },
            )
        )
    return assistant_record, tool_records


def add_tool_result(
    state: Dict[str, Any],
    *,
    tool_name: str,
    tool_call_id: Optional[str],
    content: Any,
    payload: Optional[Dict[str, Any]] = None,
    parent_id: Optional[str] = None,
    source: str = "tool",
) -> Dict[str, Any]:
    text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
    return append_record(
        state,
        {
            "type": "tool_result",
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "text": text,
            "payload": payload or {},
            "parent_id": parent_id,
            "source": source,
        },
    )


def add_summary_record(
    state: Dict[str, Any],
    *,
    summary_text: str,
    summary_kind: str = "offload",
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    record = append_record(
        state,
        {
            "type": "summary",
            "summary_kind": summary_kind,
            "text": str(summary_text or ""),
            "payload": payload or {},
            "hidden": True,
            "source": "summary",
        },
    )
    return record


def _estimate_content_tokens(content: Any) -> int:
    if isinstance(content, list):
        content = json.dumps(content, ensure_ascii=False)
    elif not isinstance(content, str):
        content = str(content)
    return max(1, len(content) // 4)


def _estimate_record_tokens(
    record: Dict[str, Any],
    *,
    state: Optional[Dict[str, Any]] = None,
) -> int:
    record_type = str(record.get("type") or "").strip()
    if record_type == "user_input":
        return _estimate_content_tokens(_record_to_user_content(record, state=state))
    if record_type == "tool_call":
        return _estimate_content_tokens(record.get("payload") or {})
    if record_type == "tool_result":
        return _estimate_content_tokens(record.get("text") or "")
    if record_type == "assistant_output":
        return _estimate_content_tokens(record.get("text") or "")
    return _estimate_content_tokens((record.get("text") or "")) + _estimate_content_tokens(record.get("payload") or {})


def _resolve_summary_runtime_settings(
    config: Optional[Dict[str, Any]],
    *,
    compiled_messages: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Optional[float]]:
    runtime_cfg = (config or {}).get("runtime") if isinstance(config, dict) else {}
    runtime_cfg = runtime_cfg if isinstance(runtime_cfg, dict) else {}

    resolved_max_context = _resolve_positive_int(runtime_cfg.get("max_context_tokens"))
    user_budget_max = _resolve_positive_int(runtime_cfg.get("summary_user_token_budget_max"))

    def _resolve_ratio(key: str, default: float) -> float:
        raw = runtime_cfg.get(key, default)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = default
        if value <= 0:
            return default
        return value

    recent_ratio = _resolve_ratio("recent_rounds_token_budget_ratio", DEFAULT_RECENT_ROUNDS_TOKEN_BUDGET_RATIO)
    user_ratio = _resolve_ratio("summary_user_token_budget_ratio", DEFAULT_USER_TOKEN_BUDGET_RATIO)

    usage = summarize_message_token_usage(compiled_messages or [], config=config)
    actual_live_tokens = max(1, int(usage.get("non_system_tokens") or 0))
    system_tokens = int(usage.get("system_tokens") or 0)
    available_after_system = None
    if resolved_max_context is not None:
        available_after_system = max(1, resolved_max_context - system_tokens)
    selection_base = actual_live_tokens
    if available_after_system is not None:
        selection_base = max(1, min(actual_live_tokens, available_after_system))

    recent_budget = max(1, int(selection_base * recent_ratio))
    user_ratio_budget = max(1, int(selection_base * user_ratio))
    user_budget = min(user_ratio_budget, user_budget_max) if user_budget_max is not None else user_ratio_budget

    return {
        "max_context_tokens": resolved_max_context,
        "total_message_tokens": int(usage.get("total_tokens") or 0),
        "system_prompt_tokens": system_tokens,
        "actual_live_tokens": actual_live_tokens,
        "selection_base_tokens": selection_base,
        "available_after_system_tokens": available_after_system,
        "recent_rounds_ratio": recent_ratio,
        "recent_rounds_budget": recent_budget,
        "user_messages_ratio": user_ratio,
        "user_messages_budget_ratio_only": user_ratio_budget,
        "user_messages_budget_max": user_budget_max,
        "user_messages_budget": user_budget,
    }


def _collect_assistant_rounds_from_records(
    records: List[Dict[str, Any]],
    *,
    state: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    rounds: List[Dict[str, Any]] = []
    i = 0
    while i < len(records):
        record = records[i]
        if record.get("type") != "assistant_output":
            i += 1
            continue

        round_records = [record]
        j = i + 1
        while j < len(records):
            candidate = records[j]
            candidate_type = candidate.get("type")
            if candidate_type in {"assistant_output", "user_input", "system_context", "summary"}:
                break
            if candidate_type in {"tool_call", "tool_result"}:
                round_records.append(candidate)
            j += 1

        rounds.append(
            {
                "assistant_record_id": record.get("id"),
                "assistant_index": i,
                "record_ids": [item.get("id") for item in round_records if item.get("id")],
                "estimated_tokens": sum(_estimate_record_tokens(item, state=state) for item in round_records),
            }
        )
        i = j
    return rounds


def _select_recent_record_rounds(
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


def _select_retained_user_records(
    records: List[Dict[str, Any]],
    *,
    budget: Optional[int],
    state: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    user_records = [record for record in records if _is_retained_pre_summary_user_input(record)]
    if not user_records:
        return []
    if budget is None or budget <= 0:
        return user_records

    latest_record = user_records[-1]
    selected_rev: List[Dict[str, Any]] = [latest_record]
    total = _estimate_record_tokens(latest_record, state=state)
    for record in reversed(user_records[:-1]):
        estimated_tokens = _estimate_record_tokens(record, state=state)
        if total + estimated_tokens > budget:
            break
        selected_rev.append(record)
        total += estimated_tokens
    return list(reversed(selected_rev))


def _find_previous_user_record(
    records: List[Dict[str, Any]],
    *,
    start_index: int,
) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    upper_bound = min(max(start_index, 0), len(records))
    for index in range(upper_bound - 1, -1, -1):
        candidate = records[index]
        if _is_retained_pre_summary_user_input(candidate):
            return index, candidate
    return None, None


def _collect_required_user_anchor_record_indices(
    records: List[Dict[str, Any]],
    *,
    assistant_indices: List[int],
    retained_user_record_ids: Optional[set[str]] = None,
) -> set[int]:
    anchor_indices: set[int] = set()
    retained_user_record_ids = retained_user_record_ids or set()
    for assistant_index in assistant_indices:
        anchor_index, anchor_record = _find_previous_user_record(
            records,
            start_index=assistant_index,
        )
        if anchor_index is None or anchor_record is None:
            continue
        if str(anchor_record.get("id") or "") in retained_user_record_ids:
            continue
        anchor_indices.add(anchor_index)
    return anchor_indices


def _normalize_context_archive_filename(filename: str) -> str:
    raw = str(filename or "").strip().replace("\\", "/")
    raw = raw.split("/")[-1]
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("._")
    if not safe:
        safe = f"context_archive_{uuid.uuid4().hex[:8]}.json"
    if "." not in safe:
        safe = f"{safe}.json"
    return safe


def _save_context_archive(
    *,
    content: str,
    config: Optional[Dict[str, Any]],
    filename: str,
) -> Dict[str, Any]:
    tool_cfg = (((config or {}).get("tools") or {}).get("memory_compression_and_offload") or {}).get("config") or {}
    archive_dir = str(tool_cfg.get("message_save_dir") or DEFAULT_CONTEXT_ARCHIVE_DIR).strip().strip("/")
    archive_dir = archive_dir or DEFAULT_CONTEXT_ARCHIVE_DIR
    normalized_filename = _normalize_context_archive_filename(filename)
    sandbox_path = f"/mnt/data/{archive_dir}/{normalized_filename}"

    try:
        from tools.sandbox import _get_sandbox_meta_from_config, upload_file_to_sandbox

        client, session_id = _get_sandbox_meta_from_config()
        upload_file_to_sandbox(
            sandbox_uri=f"sandbox:{sandbox_path}",
            client=client,
            content=content.encode("utf-8"),
            session_id=session_id,
        )
        return {
            "path": sandbox_path,
            "filename": normalized_filename,
            "storage_kind": "sandbox",
        }
    except Exception as exc:
        return {
            "path": None,
            "sandbox_path": sandbox_path,
            "filename": normalized_filename,
            "storage_kind": "unavailable",
            "error": str(exc),
        }


def _parse_json_payload(raw: Optional[str], default: Any) -> Any:
    text = str(raw or "").strip()
    if not text:
        return deepcopy(default)
    try:
        return json.loads(text)
    except Exception:
        return deepcopy(default)


def _extract_context_archives_state_from_summary(summary_text: str) -> List[Dict[str, Any]]:
    snapshot_raw = _extract_tag_content(summary_text, STATE_SNAPSHOT_TAG)
    if not snapshot_raw:
        return []
    payload = _parse_json_payload(
        _extract_tag_content(snapshot_raw, CONTEXT_ARCHIVES_STATE_TAG),
        [],
    )
    return payload if isinstance(payload, list) else []


def _extract_context_archives_state_from_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for msg in reversed(messages or []):
        if not bool(msg.get("is_summary")):
            continue
        return _extract_context_archives_state_from_summary(str(msg.get("content") or ""))
    return []


def _get_latest_summary_record(records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for record in reversed(records or []):
        if record.get("type") == "summary":
            return record
    return None


def _build_context_archive_state_entry(
    archive_meta: Dict[str, Any],
    *,
    summary_kind: str,
) -> Dict[str, Any]:
    entry = {
        "archive_kind": "summary_context_archive",
        "summary_kind": summary_kind,
        "archived_at": archive_meta.get("archived_at"),
        "storage_kind": archive_meta.get("storage_kind"),
        "path": archive_meta.get("path"),
        "sandbox_path": archive_meta.get("sandbox_path"),
        "filename": archive_meta.get("filename"),
        "record_count": archive_meta.get("record_count"),
        "message_count": archive_meta.get("message_count"),
    }
    if archive_meta.get("error"):
        entry["error"] = archive_meta.get("error")
    return entry


def _merge_context_archive_history(
    existing: List[Dict[str, Any]],
    current: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen: Dict[str, int] = {}

    for source in (existing or []), (current or []):
        for item in source:
            if not isinstance(item, dict):
                continue
            payload = _deepcopy_jsonable(item)
            identity = str(
                payload.get("path")
                or payload.get("sandbox_path")
                or payload.get("filename")
                or payload.get("archived_at")
                or ""
            ).strip()
            if not identity:
                merged.append(payload)
                continue
            if identity in seen:
                merged[seen[identity]].update(payload)
            else:
                seen[identity] = len(merged)
                merged.append(payload)
    return merged


def _inject_context_archives_state_into_summary(
    summary_text: str,
    *,
    context_archives_state: List[Dict[str, Any]],
) -> str:
    block = (
        f"<{CONTEXT_ARCHIVES_STATE_TAG}>\n"
        f"{json.dumps(context_archives_state, ensure_ascii=False, indent=2)}\n"
        f"</{CONTEXT_ARCHIVES_STATE_TAG}>"
    )

    state_snapshot_pattern = rf"<{STATE_SNAPSHOT_TAG}>.*?</{STATE_SNAPSHOT_TAG}>"
    if re.search(state_snapshot_pattern, summary_text, flags=re.DOTALL | re.IGNORECASE):
        def _replace_snapshot(match: re.Match[str]) -> str:
            snapshot_xml = match.group(0)
            context_archives_pattern = rf"<{CONTEXT_ARCHIVES_STATE_TAG}>.*?</{CONTEXT_ARCHIVES_STATE_TAG}>"
            if re.search(context_archives_pattern, snapshot_xml, flags=re.DOTALL | re.IGNORECASE):
                return re.sub(
                    context_archives_pattern,
                    block,
                    snapshot_xml,
                    count=1,
                    flags=re.DOTALL | re.IGNORECASE,
                )
            return re.sub(
                rf"</{STATE_SNAPSHOT_TAG}>",
                f"{block}\n</{STATE_SNAPSHOT_TAG}>",
                snapshot_xml,
                count=1,
                flags=re.IGNORECASE,
            )

        return re.sub(
            state_snapshot_pattern,
            _replace_snapshot,
            summary_text,
            count=1,
            flags=re.DOTALL | re.IGNORECASE,
        )

    if re.search(r"</summary>", summary_text, flags=re.IGNORECASE):
        return re.sub(
            r"</summary>",
            f"<{STATE_SNAPSHOT_TAG}>\n{block}\n</{STATE_SNAPSHOT_TAG}>\n</summary>",
            summary_text,
            count=1,
            flags=re.IGNORECASE,
        )
    return summary_text


def _build_state_snapshot_xml(
    *,
    uploaded_files_state: List[Dict[str, Any]],
    parsed_files_state: List[Dict[str, Any]],
    saved_files_state: List[Dict[str, Any]],
    context_archives_state: List[Dict[str, Any]],
    todolist_state: Any,
) -> str:
    return (
        f"<{STATE_SNAPSHOT_TAG}>\n"
        f"<{UPLOADED_FILES_STATE_TAG}>\n{json.dumps(uploaded_files_state, ensure_ascii=False, indent=2)}\n</{UPLOADED_FILES_STATE_TAG}>\n"
        f"<{PARSED_FILES_STATE_TAG}>\n{json.dumps(parsed_files_state, ensure_ascii=False, indent=2)}\n</{PARSED_FILES_STATE_TAG}>\n"
        f"<{SAVED_FILES_STATE_TAG}>\n{json.dumps(saved_files_state, ensure_ascii=False, indent=2)}\n</{SAVED_FILES_STATE_TAG}>\n"
        f"<{CONTEXT_ARCHIVES_STATE_TAG}>\n{json.dumps(context_archives_state, ensure_ascii=False, indent=2)}\n</{CONTEXT_ARCHIVES_STATE_TAG}>\n"
        f"<{TODOLIST_STATE_TAG}>\n{json.dumps(todolist_state, ensure_ascii=False, indent=2)}\n</{TODOLIST_STATE_TAG}>\n"
        f"</{STATE_SNAPSHOT_TAG}>"
    )


def _inject_state_snapshot_into_summary(
    summary_text: str,
    *,
    uploaded_files_state: List[Dict[str, Any]],
    parsed_files_state: List[Dict[str, Any]],
    saved_files_state: List[Dict[str, Any]],
    context_archives_state: List[Dict[str, Any]],
    todolist_state: Any,
) -> str:
    snapshot_xml = _build_state_snapshot_xml(
        uploaded_files_state=uploaded_files_state,
        parsed_files_state=parsed_files_state,
        saved_files_state=saved_files_state,
        context_archives_state=context_archives_state,
        todolist_state=todolist_state,
    )
    without_snapshot = re.sub(
        rf"<{STATE_SNAPSHOT_TAG}>.*?</{STATE_SNAPSHOT_TAG}>",
        "",
        summary_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if re.search(r"</summary>", without_snapshot, flags=re.IGNORECASE):
        return re.sub(
            r"</summary>",
            f"{snapshot_xml}\n</summary>",
            without_snapshot,
            count=1,
            flags=re.IGNORECASE,
        )
    return without_snapshot


def _extract_previous_inline_archive_history(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    latest_summary = _get_latest_summary_record(records)
    if not isinstance(latest_summary, dict):
        return []
    payload = latest_summary.get("payload") or {}
    history = payload.get("context_archive_inline_history")
    if isinstance(history, list):
        return _deepcopy_jsonable(history)
    inline_payload = payload.get("context_archive_inline")
    if isinstance(inline_payload, dict):
        return [_deepcopy_jsonable(inline_payload)]
    return []


_ARCHIVE_INLINE_PAYLOAD_KEYS = (
    "context_archive_inline",
    "context_archive_inline_history",
)


def _strip_state_snapshot_from_text(text: Any) -> str:
    if not isinstance(text, str):
        text = str(text or "")
    return re.sub(
        rf"\s*<{STATE_SNAPSHOT_TAG}>.*?</{STATE_SNAPSHOT_TAG}>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()


def _sanitize_summary_payload_for_context_archive(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    sanitized = _deepcopy_jsonable(payload)
    for key in _ARCHIVE_INLINE_PAYLOAD_KEYS:
        sanitized.pop(key, None)
    return sanitized


def _sanitize_record_for_context_archive(record: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = _deepcopy_jsonable(record)
    if sanitized.get("type") == "summary":
        sanitized["payload"] = _sanitize_summary_payload_for_context_archive(sanitized.get("payload"))
        sanitized["text"] = _strip_state_snapshot_from_text(sanitized.get("text", ""))
    return sanitized


def _sanitize_records_for_context_archive(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        _sanitize_record_for_context_archive(record)
        for record in (records or [])
        if isinstance(record, dict)
    ]


def _sanitize_message_for_context_archive(message: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = _deepcopy_jsonable(message)
    if sanitized.get("is_summary"):
        sanitized["content"] = _strip_state_snapshot_from_text(sanitized.get("content", ""))
    return sanitized


def _sanitize_messages_for_context_archive(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        _sanitize_message_for_context_archive(message)
        for message in (messages or [])
        if isinstance(message, dict)
    ]


def _extract_previous_context_archive_history(
    records: List[Dict[str, Any]],
    compiled_messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    latest_summary = _get_latest_summary_record(records)
    if isinstance(latest_summary, dict):
        payload = latest_summary.get("payload") or {}
        history = payload.get("context_archive_history")
        if isinstance(history, list):
            return _deepcopy_jsonable(history)
    return _extract_context_archives_state_from_messages(compiled_messages)


def _merge_context_archive_inline_history(
    existing: List[Dict[str, Any]],
    current: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen: Dict[str, int] = {}
    for source in ((existing or []), (current or [])):
        for item in source:
            if not isinstance(item, dict):
                continue
            payload = _deepcopy_jsonable(item)
            identity = str(
                payload.get("archive_filename")
                or payload.get("archive_path")
                or payload.get("archive_sandbox_path")
                or payload.get("archived_at")
                or payload.get("summary_text")
                or payload.get("summary_kind")
                or ""
            ).strip()
            if not identity:
                merged.append(payload)
                continue
            if identity in seen:
                merged[seen[identity]].update(payload)
            else:
                seen[identity] = len(merged)
                merged.append(payload)
    return merged


def _archive_current_context(
    state: Dict[str, Any],
    *,
    summary_text: str,
    compiled_messages_before: List[Dict[str, Any]],
    trimmed_compiled_messages: List[Dict[str, Any]],
    selection: Dict[str, Any],
    config: Optional[Dict[str, Any]],
    summary_kind: str,
    summary_generation_messages: Optional[List[Dict[str, Any]]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    archived_at = _iso_now()
    conversation_id = str(state.get("conversation_id") or "conversation").strip() or "conversation"
    safe_conversation_id = re.sub(r"[^A-Za-z0-9._-]+", "_", conversation_id).strip("._") or "conversation"
    archive_payload: Dict[str, Any] = {
        "conversation_id": state.get("conversation_id"),
        "archived_at": archived_at,
        "summary_kind": summary_kind,
        "summary_text": str(summary_text or ""),
        "compiled_messages_before": _sanitize_messages_for_context_archive(compiled_messages_before),
        "message_records_before": _sanitize_records_for_context_archive(state.get("message_records") or []),
        "trimmed_compiled_messages": _sanitize_messages_for_context_archive(trimmed_compiled_messages),
        "trimmed_record_ids": _deepcopy_jsonable(selection.get("summarized_record_ids") or []),
        "selection": _deepcopy_jsonable(selection),
        "summary_generation_messages": _sanitize_messages_for_context_archive(summary_generation_messages or []),
        "asset_index": _deepcopy_jsonable(state.get("asset_index") or {}),
        "runtime_control": _deepcopy_jsonable(state.get("runtime_control") or {}),
        "session_metadata": _deepcopy_jsonable(state.get("session_metadata") or {}),
        "projections": _deepcopy_jsonable(state.get("projections") or {}),
    }

    timestamp = archived_at.replace(":", "").replace("-", "").replace("+", "_").replace("T", "_")
    filename = f"{safe_conversation_id}_summary_context_{timestamp}_{uuid.uuid4().hex[:8]}.json"
    saved = _save_context_archive(
        content=json.dumps(archive_payload, ensure_ascii=False, indent=2),
        config=config,
        filename=filename,
    )
    saved["archive_kind"] = "summary_context_archive"
    saved["summary_kind"] = summary_kind
    saved["archived_at"] = archived_at
    saved["record_count"] = len(state.get("message_records") or [])
    saved["message_count"] = len(compiled_messages_before)
    archive_payload["archive_filename"] = saved.get("filename")
    archive_payload["archive_path"] = saved.get("path")
    archive_payload["archive_sandbox_path"] = saved.get("sandbox_path")
    return saved, archive_payload


def apply_summary_offload_to_conversation_state(
    state: Dict[str, Any],
    *,
    summary_text: str,
    selection: Dict[str, Any],
    summary_generation_messages: Optional[List[Dict[str, Any]]] = None,
    trimmed_compiled_messages: Optional[List[Dict[str, Any]]] = None,
    uploaded_files_state: Optional[List[Dict[str, Any]]] = None,
    parsed_files_state: Optional[List[Dict[str, Any]]] = None,
    saved_files_state: Optional[List[Dict[str, Any]]] = None,
    todolist_state: Any = None,
    summary_kind: str = "offload",
    payload: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    try:
        from backend.replay_runtime import checkpoint_runtime_state

        checkpoint_runtime_state(
            checkpoint_kind="summary_before_compact",
            state=state,
        )
    except Exception:
        pass

    if not isinstance(selection, dict):
        raise ValueError("summary selection is required")

    original_records = _deepcopy_jsonable(state.get("message_records") or [])
    compiled_messages_before = state.get("messages")
    if not isinstance(compiled_messages_before, list) or not compiled_messages_before:
        compiled_messages_before = compile_messages_for_llm(state)
    compiled_messages_before = _deepcopy_jsonable(compiled_messages_before)

    try:
        compiled_count = int(selection.get("compiled_message_count"))
    except (TypeError, ValueError):
        compiled_count = None
    if compiled_count != len(compiled_messages_before):
        raise ValueError("summary selection no longer matches current compiled messages")

    trimmed_compiled_messages = _deepcopy_jsonable(trimmed_compiled_messages or [])
    summary_generation_messages = _deepcopy_jsonable(summary_generation_messages or [])
    uploaded_files_state = _deepcopy_jsonable(uploaded_files_state or [])
    parsed_files_state = _deepcopy_jsonable(parsed_files_state or [])
    saved_files_state = _deepcopy_jsonable(saved_files_state or [])
    todolist_state = _deepcopy_jsonable(todolist_state or [])

    archive_meta, _archive_inline = _archive_current_context(
        state,
        summary_text=summary_text,
        compiled_messages_before=compiled_messages_before,
        trimmed_compiled_messages=trimmed_compiled_messages,
        selection=selection,
        config=config,
        summary_kind=summary_kind,
        summary_generation_messages=summary_generation_messages,
    )
    previous_context_archive_history = _extract_previous_context_archive_history(
        original_records,
        compiled_messages_before,
    )
    context_archive_history = _merge_context_archive_history(
        previous_context_archive_history,
        [_build_context_archive_state_entry(archive_meta, summary_kind=summary_kind)],
    )
    summary_text = _inject_state_snapshot_into_summary(
        summary_text,
        uploaded_files_state=uploaded_files_state,
        parsed_files_state=parsed_files_state,
        saved_files_state=saved_files_state,
        context_archives_state=context_archive_history,
        todolist_state=todolist_state,
    )

    summarized_record_ids = {
        str(record_id).strip()
        for record_id in (selection.get("summarized_record_ids") or [])
        if str(record_id).strip()
    }
    summary_insert_before_record_id = str(selection.get("summary_insert_before_record_id") or "").strip()
    if not summary_insert_before_record_id and (selection.get("retained_round_record_ids") or []):
        raise ValueError("summary selection is missing summary_insert_before_record_id")

    summary_payload = _deepcopy_jsonable(payload) if isinstance(payload, dict) else {}
    summary_payload["context_archive"] = archive_meta
    summary_payload["context_archive_history"] = _deepcopy_jsonable(context_archive_history)
    summary_payload["retention"] = _deepcopy_jsonable(selection)

    summary_record = _ensure_record_fields(
        {
            "type": "summary",
            "summary_kind": summary_kind,
            "text": str(summary_text or ""),
            "payload": summary_payload,
            "hidden": True,
            "source": "summary",
        }
    )

    rebuilt_records: List[Dict[str, Any]] = []
    system_records = [record for record in original_records if record.get("type") == "system_context"]
    if system_records:
        rebuilt_records.append(_deepcopy_jsonable(system_records[-1]))

    record_compaction_states: Dict[int, bool] = {}
    for index, record in enumerate(original_records):
        record_type = record.get("type")
        record_id = str(record.get("id") or "")
        if record_type in {"system_context", "summary", "audit_event"}:
            continue
        record_compaction_states[index] = record_id in summarized_record_ids

    summary_boundary_index = None
    if summary_insert_before_record_id:
        summary_boundary_index = next(
            (
                index
                for index, record in enumerate(original_records)
                if record.get("type") not in {"system_context", "summary", "audit_event"}
                and str(record.get("id") or "").strip() == summary_insert_before_record_id
            ),
            None,
        )

    summary_inserted = False
    for index, record in enumerate(original_records):
        record_type = record.get("type")
        record_id = str(record.get("id") or "")
        if record_type in {"system_context", "summary", "audit_event"}:
            continue

        if summary_boundary_index is not None and not summary_inserted and index >= summary_boundary_index:
            summary_record["summary_inserted"] = True
            rebuilt_records.append(_deepcopy_jsonable(summary_record))
            summary_inserted = True

        rebuilt_records.append(
            _set_summary_prompt_state(
                record,
                compacted=record_compaction_states.get(index, False),
                summary_id=summary_record.get("id"),
                summary_kind=summary_kind,
            )
        )

    if not summary_inserted:
        summary_record["summary_inserted"] = False
        rebuilt_records.append(_deepcopy_jsonable(summary_record))

    existing_records = state.get("message_records")
    if isinstance(existing_records, list):
        existing_records[:] = rebuilt_records
    else:
        state["message_records"] = rebuilt_records
    touch_updated_at(state)
    rebuild_compiled_messages(state)
    return summary_record


def add_subtask_summary(
    state: Dict[str, Any],
    *,
    subtask_id: str,
    title: Optional[str],
    status: str,
    text: str,
    parent_id: Optional[str] = None,
    kind: str = "subtask",
    payload_extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload = {
        "subtask_id": subtask_id,
        "subtask_title": title,
        "subtask_status": status,
        "kind": kind,
    }
    if isinstance(payload_extra, dict) and payload_extra:
        payload.update(_deepcopy_jsonable(payload_extra))
    return append_record(
        state,
        {
            "type": "subtask_summary",
            "subtask_id": subtask_id,
            "parent_id": parent_id,
            "text": text,
            "payload": payload,
            "source": kind,
        },
    )


def add_audit_event(
    state: Dict[str, Any],
    *,
    text: str,
    payload: Optional[Dict[str, Any]] = None,
    subtask_id: Optional[str] = None,
) -> Dict[str, Any]:
    return append_record(
        state,
        {
            "type": "audit_event",
            "text": str(text or ""),
            "payload": payload or {},
            "subtask_id": subtask_id,
            "hidden": True,
            "source": "audit",
        },
    )


def set_todolist_projection(state: Dict[str, Any], todo_list: Any) -> None:
    if isinstance(todo_list, list):
        state["todolist"] = _deepcopy_jsonable(todo_list)
    else:
        state["todolist"] = []


def finalize_todolist_projection(state: Dict[str, Any]) -> bool:
    raw_projection = state.get("todolist", [])
    if not isinstance(raw_projection, list) or not raw_projection:
        return False

    next_projection: List[Dict[str, Any]] = []
    changed = False
    for item in raw_projection:
        if not isinstance(item, dict):
            next_projection.append(item)
            continue
        next_item = _deepcopy_jsonable(item)
        if next_item.get("status") != "complete":
            next_item["status"] = "complete"
            changed = True
        next_projection.append(next_item)

    if changed:
        set_todolist_projection(state, next_projection)
    return changed


def set_active_editor_projection(state: Dict[str, Any], active_editor: Optional[Dict[str, Any]]) -> None:
    state.setdefault("projections", {})["current_active_editor_projection"] = _deepcopy_jsonable(active_editor) if active_editor else None


def update_language_profile(
    state: Dict[str, Any],
    locale: Optional[str],
    *,
    source_message_id: Optional[str],
    confidence: Optional[float] = None,
) -> None:
    normalized = _normalize_locale(locale) or "zh-CN"
    runtime = state.setdefault("runtime_control", {})
    runtime["current_prompt_locale"] = normalized
    preferred = (state.get("session_metadata") or {}).get("preferred_locale")
    if not preferred:
        state.setdefault("session_metadata", {})["preferred_locale"] = normalized


def register_file_asset(
    state: Dict[str, Any],
    *,
    origin_message_id: Optional[str],
    name: str,
    asset_kind: str,
    storage_path: Optional[str],
    sandbox_path: Optional[str],
    mime_type: Optional[str] = None,
    stable_order: Optional[int] = None,
    file_id: Optional[str] = None,
) -> Dict[str, Any]:
    files = state.setdefault("asset_index", {}).setdefault("files", [])
    resolved_file_id = file_id or _new_id("file")
    order = stable_order if stable_order is not None else len(files) + 1
    entry = {
        "file_id": resolved_file_id,
        "origin_message_id": origin_message_id,
        "asset_kind": asset_kind,
        "name": str(name or ""),
        "storage_path": storage_path,
        "sandbox_path": sandbox_path,
        "mime_type": mime_type,
        "stable_order": order,
    }
    files.append(entry)
    return entry


def _sanitize_preview_value(value: Any, *, max_chars: int = 4000) -> Any:
    if isinstance(value, str):
        if len(value) <= max_chars:
            return value
        return value[:max_chars].rstrip() + "......"
    if isinstance(value, dict):
        sanitized = {k: _sanitize_preview_value(v, max_chars=max_chars) for k, v in value.items()}
        for key in ("text", "description", "ocr_text"):
            original = value.get(key)
            if isinstance(original, str) and len(original) > max_chars:
                sanitized["is_full"] = False
                sanitized["total_length"] = len(original)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_preview_value(item, max_chars=max_chars) for item in value]
    return _deepcopy_jsonable(value)


def register_parsed_artifact(
    state: Dict[str, Any],
    *,
    source_file_id: str,
    parser: str,
    storage_path: Optional[str],
    summary: Optional[str] = None,
    preview: Optional[Dict[str, Any]] = None,
    content_kind: Optional[str] = None,
    artifact_id: Optional[str] = None,
) -> Dict[str, Any]:
    artifacts = state.setdefault("asset_index", {}).setdefault("parsed_artifacts", [])
    entry = {
        "artifact_id": artifact_id or _new_id("artifact"),
        "source_file_id": source_file_id,
        "parser": parser,
        "storage_path": storage_path,
        "summary": summary,
        "preview": _sanitize_preview_value(preview) if isinstance(preview, dict) else None,
        "content_kind": content_kind,
    }
    artifacts.append(entry)
    return entry


def set_conversation_status(state: Dict[str, Any], status: str, *, reason: Optional[str] = None) -> None:
    runtime = state.setdefault("runtime_control", {})
    runtime["conversation_status"] = status
    if status == "paused":
        runtime["pause_reason"] = reason
    if status in {"terminating", "terminated"}:
        runtime["termination_reason"] = reason


def request_termination(state: Dict[str, Any], reason: str) -> None:
    runtime = state.setdefault("runtime_control", {})
    runtime["conversation_status"] = "terminating"
    runtime["termination_requested_at"] = _iso_now()
    runtime["termination_reason"] = reason


def finalize_termination(state: Dict[str, Any], reason: str) -> None:
    runtime = state.setdefault("runtime_control", {})
    runtime["conversation_status"] = "terminated"
    runtime["termination_reason"] = reason


def mark_waiting_for_user_input(
    state: Dict[str, Any],
    *,
    tool_result_record_id: Optional[str],
    request_id: Optional[str],
) -> None:
    runtime = state.setdefault("runtime_control", {})
    runtime["conversation_status"] = "waiting_user_input"
    runtime["pending_ask_user_message_id"] = tool_result_record_id
    runtime["pending_ask_user_request_id"] = request_id


def clear_waiting_for_user_input(state: Dict[str, Any]) -> None:
    runtime = state.setdefault("runtime_control", {})
    runtime["pending_ask_user_message_id"] = None
    runtime["pending_ask_user_request_id"] = None
    if runtime.get("conversation_status") == "waiting_user_input":
        runtime["conversation_status"] = "running"


def is_waiting_for_user_input(state: Dict[str, Any]) -> bool:
    if "message_records" in state:
        runtime = state.get("runtime_control") or {}
        return bool(runtime.get("conversation_status") == "waiting_user_input")
    return bool(state.get("waiting_user_input"))


def get_record_by_id(state: Dict[str, Any], record_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not record_id:
        return None
    for record in state.get("message_records") or []:
        if record.get("id") == record_id:
            return record
    return None


def get_pending_ask_user_payload(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    runtime = state.get("runtime_control") or {}
    pending_id = runtime.get("pending_ask_user_message_id")
    record = get_record_by_id(state, pending_id)
    if not record:
        return None
    payload = record.get("payload") or {}
    if isinstance(payload, dict):
        tool_result = _parse_jsonish(payload.get("result"))
        if isinstance(tool_result, dict):
            return _deepcopy_jsonable(tool_result)
    return _deepcopy_jsonable(payload) if payload else None


def get_runtime_pending_ask_user_payload(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if "message_records" in state:
        return get_pending_ask_user_payload(state)
    payload = state.get("pending_ask_user_payload")
    return _deepcopy_jsonable(payload) if isinstance(payload, dict) else None


def find_pending_ask_user_record_for_resume(
    state: Dict[str, Any],
    *,
    answer_payload: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not isinstance(answer_payload, dict) or not answer_payload:
        return None

    runtime = state.get("runtime_control") or {}
    request_id = str(answer_payload.get("request_id") or "").strip()
    record = get_record_by_id(state, runtime.get("pending_ask_user_message_id"))

    if not record:
        for candidate in reversed(state.get("message_records") or []):
            if candidate.get("type") != "tool_result":
                continue
            payload = candidate.get("payload") or {}
            result = _parse_jsonish(payload.get("result")) if isinstance(payload, dict) else None
            if request_id and isinstance(result, dict) and str(result.get("request_id") or "").strip() == request_id:
                record = candidate
                break

    if not record:
        return None

    return record


def get_latest_record(state: Dict[str, Any], record_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    for record in reversed(state.get("message_records") or []):
        if record_type and record.get("type") != record_type:
            continue
        return record
    return None


def _parse_jsonish(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    if text[0] not in "{[":
        return value
    try:
        return json.loads(text)
    except Exception:
        return value


def update_tool_result_content(
    state: Dict[str, Any],
    *,
    tool_call_id: str,
    content: Any,
    payload: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    for record in reversed(state.get("message_records") or []):
        if record.get("type") == "tool_result" and record.get("tool_call_id") == tool_call_id:
            record["text"] = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            if payload is not None:
                record["payload"] = _deepcopy_jsonable(payload)
            return record
    return None


def create_delegate_entry(
    state: Dict[str, Any],
    *,
    kind: str,
    instruction: str,
    parent_tool_call_id: Optional[str],
    title: Optional[str] = None,
    user_visible_todo_list: Optional[List[str]] = None,
    delegate_id: Optional[str] = None,
) -> Dict[str, Any]:
    runtime = state.setdefault("runtime_control", {})
    counter_key = "subtask_counter" if kind == "subtask" else "reflection_counter"
    prefix = "subtask" if kind == "subtask" else "reflection"
    counter = int(runtime.get(counter_key) or 0)
    resolved_delegate_id = delegate_id or f"{prefix}_{counter}"
    runtime[counter_key] = max(counter + 1, int(resolved_delegate_id.split("_")[-1]) + 1 if resolved_delegate_id.rsplit("_", 1)[-1].isdigit() else counter + 1)
    resolved_title = title or instruction[:80]
    visible_todo_list = [
        str(item).strip()
        for item in (user_visible_todo_list or [])
        if str(item).strip()
    ]
    entry = {
        "subtask_id": resolved_delegate_id,
        "kind": kind,
        "status": "queued",
        "title": resolved_title,
        "user_visible_title": resolved_title,
        "user_visible_todo_list": visible_todo_list,
        "instruction": instruction,
        "parent_tool_call_id": parent_tool_call_id,
        "loop_count": 0,
        "max_loops": None,
        "messages": [],
        "result": None,
        "raw_result": None,
        "error": None,
    }
    runtime.setdefault("subtasks", {})[resolved_delegate_id] = entry
    runtime.setdefault("pending_subtask_ids", []).append(resolved_delegate_id)
    return entry


def set_delegate_active(state: Dict[str, Any], delegate_id: Optional[str], *, status: str) -> None:
    runtime = state.setdefault("runtime_control", {})
    runtime["active_subtask_id"] = delegate_id
    if delegate_id:
        entry = runtime.setdefault("subtasks", {}).get(delegate_id)
        if entry:
            entry["status"] = status
    pending = runtime.setdefault("pending_subtask_ids", [])
    if delegate_id in pending:
        pending.remove(delegate_id)


def append_delegate_message(
    state: Dict[str, Any],
    delegate_id: str,
    message: Dict[str, Any],
) -> None:
    runtime = state.setdefault("runtime_control", {})
    entry = runtime.setdefault("subtasks", {}).get(delegate_id)
    if not entry:
        return
    entry.setdefault("messages", []).append(_deepcopy_jsonable(message))
    if entry.get("status") == "queued":
        entry["status"] = "running"

def complete_delegate(
    state: Dict[str, Any],
    *,
    delegate_id: str,
    status: str,
    content: str,
    raw_content: Optional[str] = None,
    error: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    runtime = state.setdefault("runtime_control", {})
    entry = runtime.setdefault("subtasks", {}).get(delegate_id)
    if not entry:
        return None
    entry["status"] = status
    entry["result"] = content
    entry["raw_result"] = raw_content if raw_content is not None else content
    entry["error"] = error
    if runtime.get("active_subtask_id") == delegate_id:
        runtime["active_subtask_id"] = None
    delegate_label = str(entry.get("title") or delegate_id or "delegate").strip() or delegate_id
    summary_text = f"{delegate_label} [{status}]"
    result_preview = str(content or "").strip()
    if len(result_preview) > 240:
        result_preview = result_preview[:240].rstrip() + "..."
    return add_subtask_summary(
        state,
        subtask_id=delegate_id,
        title=entry.get("title"),
        status=status,
        text=summary_text,
        parent_id=None,
        kind=entry.get("kind") or "subtask",
        payload_extra={
            "result_preview": result_preview,
        },
    )


def _build_file_asset_index(state: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not isinstance(state, dict):
        return {}
    asset_index = state.get("asset_index") or {}
    indexed: Dict[str, Dict[str, Any]] = {}
    for item in asset_index.get("files") or []:
        if not isinstance(item, dict):
            continue
        file_id = str(item.get("file_id") or "").strip()
        if file_id:
            indexed[file_id] = item
    return indexed


def _build_latest_parsed_artifact_index(state: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not isinstance(state, dict):
        return {}
    asset_index = state.get("asset_index") or {}
    indexed: Dict[str, Dict[str, Any]] = {}
    for item in asset_index.get("parsed_artifacts") or []:
        if not isinstance(item, dict):
            continue
        source_file_id = str(item.get("source_file_id") or "").strip()
        if source_file_id:
            indexed[source_file_id] = item
    return indexed


def _enrich_upload_prompt_entry(
    upload: Any,
    *,
    file_assets_by_id: Dict[str, Dict[str, Any]],
    parsed_artifacts_by_file_id: Dict[str, Dict[str, Any]],
) -> Any:
    if not isinstance(upload, dict):
        return _deepcopy_jsonable(upload)

    entry = _deepcopy_jsonable(upload)
    file_id = str(entry.get("file_id") or "").strip()
    file_entry = file_assets_by_id.get(file_id) if file_id else None
    parsed_artifact = parsed_artifacts_by_file_id.get(file_id) if file_id else None

    if not isinstance(parsed_artifact, dict):
        return entry

    resolved_name = str(entry.get("name") or (file_entry or {}).get("name") or "").strip() or None
    preview = _fallback_preview_from_artifact(parsed_artifact, resolved_name)
    if preview:
        entry["preview"] = preview

    parsed_path = str(parsed_artifact.get("storage_path") or "").strip()
    if parsed_path:
        entry["parsed_path"] = parsed_path

    content_kind = str(parsed_artifact.get("content_kind") or "").strip()
    if content_kind:
        entry["content_kind"] = content_kind

    return entry


def _build_prompt_upload_entries(
    uploads: List[Dict[str, Any]],
    *,
    state: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    if not uploads:
        return []
    file_assets_by_id = _build_file_asset_index(state)
    parsed_artifacts_by_file_id = _build_latest_parsed_artifact_index(state)
    return [
        _enrich_upload_prompt_entry(
            upload,
            file_assets_by_id=file_assets_by_id,
            parsed_artifacts_by_file_id=parsed_artifacts_by_file_id,
        )
        for upload in uploads
    ]


def _resolve_upload_display_path(upload: Any) -> Optional[str]:
    if not isinstance(upload, dict):
        return None
    for key in ("path", "sandbox_path", "storage_path", "name"):
        value = str(upload.get(key) or "").strip()
        if value:
            return value
    return None


def _upload_preview_is_incomplete(upload: Any) -> bool:
    if not isinstance(upload, dict):
        return False
    preview = upload.get("preview")
    if not isinstance(preview, dict):
        return False
    is_full = preview.get("is_full")
    if is_full is False:
        return True
    if isinstance(is_full, str):
        return is_full.strip().lower() in {"false", "0", "no"}
    return False


def _build_upload_explanatory_text(
    prompt_uploads: List[Dict[str, Any]],
    *,
    locale: Optional[str],
) -> Optional[str]:
    if not prompt_uploads:
        return None

    normalized_locale = _normalize_locale(locale) or "zh-CN"
    is_zh = normalized_locale.startswith("zh")
    file_heading = "用户输入文件" if is_zh else "User input files"
    parsed_heading = "## 用户输入文件解析" if is_zh else "## Parsed user input files"
    parsed_description = (
        "以下是对用户输入文档的预解析文本版本，便于你快速理解文档内容。如果用户要求对原始文件进行格式转换、编辑或生成新文件等操作，请使用「用户输入文件」中的原始路径。"
        if is_zh
        else 'Below are pre-parsed text versions of the user-provided documents to help you understand the content quickly. If the user asks for format conversion, editing the original file, or generating new files from it, use the original paths listed under "User input files".'
    )
    incomplete_preview_notice = (
        "重要：如果下方 uploads JSON 中某个 `preview.is_full` 为 `false`，该 preview 只是 document_parser 预解析摘要或截断预览，不是完整文件内容；需要精确分析、引用、计算或核对时，必须继续读取 `parsed_path` 或原始文件，不能只凭该摘要下结论。"
        if is_zh
        else "Important: if any `preview.is_full` value in the uploads JSON block below is `false`, that preview is only a document_parser summary or truncated preview, not the complete file content. For precise analysis, citation, calculation, or verification, read the `parsed_path` or original file instead of relying only on that summary."
    )
    has_incomplete_preview = any(_upload_preview_is_incomplete(upload) for upload in prompt_uploads)

    sections: List[str] = [file_heading]
    display_paths = [path for path in (_resolve_upload_display_path(upload) for upload in prompt_uploads) if path]
    sections.extend(display_paths)

    parsed_mappings = []
    for upload in prompt_uploads:
        source_path = _resolve_upload_display_path(upload)
        parsed_path = str(upload.get("parsed_path") or "").strip()
        if source_path and parsed_path:
            parsed_mappings.append(f"{source_path} -> {parsed_path}")

    if parsed_mappings:
        parsed_sections = ["", parsed_heading, parsed_description]
        if has_incomplete_preview:
            parsed_sections.append(incomplete_preview_notice)
        parsed_sections.extend(parsed_mappings)
        sections.extend(parsed_sections)
    elif has_incomplete_preview:
        sections.extend(["", incomplete_preview_notice])

    return "\n".join(sections).strip()


def _build_upload_block(
    uploads: List[Dict[str, Any]],
    *,
    state: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    prompt_uploads = _build_prompt_upload_entries(uploads, state=state)
    if not prompt_uploads:
        return None
    return "<uploads>\n" + json.dumps(prompt_uploads, ensure_ascii=False, indent=2) + "\n</uploads>"


def _build_refs_block(refs: List[Dict[str, Any]]) -> Optional[str]:
    if not refs:
        return None
    return "<knowledge_base_refs>\n" + json.dumps(refs, ensure_ascii=False, indent=2) + "\n</knowledge_base_refs>"


def _build_input_kind_block(record: Dict[str, Any]) -> Optional[str]:
    payload = record.get("payload") or {}
    kind = record.get("input_kind")
    if kind == "todolist_edit":
        return "<todolist_edit>\n" + json.dumps(payload, ensure_ascii=False, indent=2) + "\n</todolist_edit>"
    if kind == "todolist_feedback":
        return "<todolist_feedback>\n" + json.dumps(payload, ensure_ascii=False, indent=2) + "\n</todolist_feedback>"
    if kind == "resume_answer":
        return "<ask_user_answer>\n" + json.dumps(payload, ensure_ascii=False, indent=2) + "\n</ask_user_answer>"
    return None


def _record_to_user_content(
    record: Dict[str, Any],
    *,
    state: Optional[Dict[str, Any]] = None,
    include_uploads: bool = True,
) -> str:
    sections: List[str] = []
    text = str(record.get("text") or "").strip()
    if text:
        sections.append(text)
    kind_block = _build_input_kind_block(record)
    if kind_block:
        sections.append(kind_block)
    if include_uploads:
        prompt_uploads = _build_prompt_upload_entries(record.get("uploads") or [], state=state)
        if prompt_uploads:
            runtime_locale = None
            if isinstance(state, dict):
                runtime_locale = (state.get("runtime_control") or {}).get("current_prompt_locale")
            locale = (
                _normalize_locale(runtime_locale)
                or _normalize_locale(record.get("language"))
                or detect_locale(text, default_locale=runtime_locale or record.get("language"))
            )
            upload_explanatory_text = _build_upload_explanatory_text(
                prompt_uploads,
                locale=locale,
            )
            if upload_explanatory_text:
                sections.append(upload_explanatory_text)
            sections.append("<uploads>\n" + json.dumps(prompt_uploads, ensure_ascii=False, indent=2) + "\n</uploads>")
    refs_block = _build_refs_block(record.get("refs") or [])
    if refs_block:
        sections.append(refs_block)
    return "\n".join(sections).strip()


def _is_retained_pre_summary_user_input(record: Dict[str, Any]) -> bool:
    if record.get("type") != "user_input":
        return False

    if _record_is_summary_compacted(record):
        return False

    source = str(record.get("source") or "user").strip()
    if source != "user":
        return False

    input_kind = str(record.get("input_kind") or "text").strip()
    if input_kind in {"todolist_edit", "functional_instruction", "resume_answer"}:
        return False

    return True


def _trim_preview_text(text: Any, *, max_chars: int = 1200) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    compact = re.sub(r"[ \t]+\n", "\n", value)
    compact = re.sub(r"\n{3,}", "\n\n", compact)
    if len(compact) <= max_chars:
        return compact
    return compact[:max_chars].rstrip() + "......"


def _build_text_preview(text: Any, *, max_chars: int = 1200, assume_full: bool = True) -> Optional[Dict[str, Any]]:
    if isinstance(text, (dict, list)):
        raw = json.dumps(text, ensure_ascii=False, indent=2).strip()
    else:
        raw = str(text or "").strip()
    if not raw:
        return None
    preview_text = _trim_preview_text(raw, max_chars=max_chars)
    is_full = bool(assume_full and len(raw) <= max_chars)
    preview: Dict[str, Any] = {
        "text": preview_text,
        "is_full": is_full,
    }
    if not is_full:
        preview["total_length"] = len(raw)
    return preview


def _build_table_preview(text: Any) -> Optional[Dict[str, Any]]:
    raw = str(text or "").strip()
    if not raw:
        return None
    raw = re.sub(r"^(Table summary:|表格摘要:)\s*", "", raw)
    if not raw:
        return None
    return {"description": raw}


def _guess_content_kind_from_name(name: Optional[str]) -> Optional[str]:
    lower = str(name or "").lower()
    if lower.endswith((".xlsx", ".xls", ".csv")):
        return "table"
    if lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")):
        return "image"
    if "." in lower:
        return "text"
    return None


def _fallback_preview_from_artifact(artifact: Dict[str, Any], file_name: Optional[str]) -> Optional[Dict[str, Any]]:
    preview = artifact.get("preview")
    if isinstance(preview, dict) and preview:
        return _deepcopy_jsonable(preview)

    summary = str(artifact.get("summary") or "").strip()
    if not summary:
        return None

    content_kind = str(artifact.get("content_kind") or _guess_content_kind_from_name(file_name) or "").strip()
    if content_kind == "table" or summary.startswith(("Table summary:", "表格摘要:")):
        return _build_table_preview(summary)
    if content_kind == "image":
        return {
            "ocr_text": _trim_preview_text(summary),
            "is_full": True,
        }
    return _build_text_preview(summary, assume_full=False)


def _build_active_editor_projection_block(state: Dict[str, Any]) -> Optional[str]:
    projections = state.get("projections") or {}
    active_editor = projections.get("current_active_editor_projection")
    if active_editor is None:
        return None
    return (
        "<current_active_editor_projection>\n"
        + json.dumps(active_editor, ensure_ascii=False, indent=2)
        + "\n</current_active_editor_projection>"
    )


def _projection_injection_messages(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    sections: List[str] = []
    active_editor_block = _build_active_editor_projection_block(state)
    if active_editor_block:
        sections.append(active_editor_block)
    if not sections:
        return []
    return [{"role": "user", "content": "\n".join(sections)}]


def _preloaded_context_injection_messages(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = []
    for item in state.get("preloaded_context_messages") or []:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        messages.append(
            {
                "role": "user",
                "content": content,
                "id": str(item.get("id") or "preloaded_context"),
            }
        )
    return messages


def _retrieved_context_injection_messages(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = []
    for item in state.get("retrieved_context_messages") or []:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        messages.append(
            {
                "role": "user",
                "content": content,
                "id": str(item.get("id") or "retrieved_context"),
            }
        )
    return messages


def _normalize_internal_record_ids(*values: Any) -> List[str]:
    normalized: List[str] = []
    seen: set[str] = set()
    for value in values:
        candidates = value if isinstance(value, list) else [value]
        for candidate in candidates:
            record_id = str(candidate or "").strip()
            if not record_id or record_id in seen:
                continue
            seen.add(record_id)
            normalized.append(record_id)
    return normalized


def _summary_snapshot_preserves_file_state(summary_text: Any) -> bool:
    snapshot_raw = _extract_tag_content(summary_text, STATE_SNAPSHOT_TAG)
    if not snapshot_raw:
        return False
    uploaded_files = _parse_json_payload(
        _extract_tag_content(snapshot_raw, "uploaded_files_state"),
        [],
    )
    parsed_files = _parse_json_payload(
        _extract_tag_content(snapshot_raw, "parsed_files_state"),
        [],
    )
    return bool(uploaded_files or parsed_files)


def compile_messages_for_llm(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    records = [
        record
        for record in (state.get("message_records") or [])
        if not (isinstance(record, dict) and record.get("superseded_at"))
    ]
    messages: List[Dict[str, Any]] = []
    summary_record = None
    summary_index = -1
    assistant_tool_records: Dict[str, List[Dict[str, Any]]] = {}
    for index, record in enumerate(records):
        if record.get("type") == "summary":
            summary_record = record
            summary_index = index
        if record.get("type") == "tool_call" and not _record_is_summary_compacted(record):
            parent_id = record.get("parent_id")
            if parent_id:
                assistant_tool_records.setdefault(parent_id, []).append(record)

    system_records = [record for record in records if record.get("type") == "system_context"]
    if system_records:
        record = system_records[-1]
        messages.append(
            {
                "role": "system",
                "content": record.get("text", ""),
                "_record_ids": _normalize_internal_record_ids(record.get("id")),
            }
        )

    messages.extend(_preloaded_context_injection_messages(state))
    messages.extend(_retrieved_context_injection_messages(state))

    suppress_pre_summary_uploads = bool(
        summary_record and _summary_snapshot_preserves_file_state(summary_record.get("text", ""))
    )
    summary_payload = summary_record.get("payload") if isinstance(summary_record, dict) else {}
    retention = (
        summary_payload.get("retention")
        if isinstance(summary_payload, dict) and isinstance(summary_payload.get("retention"), dict)
        else None
    )
    retained_round_record_ids = {
        str(record_id).strip()
        for record_id in ((retention or {}).get("retained_round_record_ids") or [])
        if str(record_id).strip()
    }
    summarized_record_ids = {
        str(record_id).strip()
        for record_id in ((retention or {}).get("summarized_record_ids") or [])
        if str(record_id).strip()
    }
    anchor_user_record_ids = {
        str(record_id).strip()
        for record_id in ((retention or {}).get("anchor_user_record_ids") or [])
        if str(record_id).strip()
    }
    defer_pre_summary_users_until_after_summary = bool(summary_record) and (
        retention is None or bool(retained_round_record_ids)
    )
    deferred_pre_summary_messages: List[Dict[str, Any]] = []
    earliest_summarized_record_index = next(
        (
            index
            for index, record in enumerate(records)
            if str(record.get("id") or "").strip() in summarized_record_ids
        ),
        None,
    )

    if summary_index >= 0:
        for index, record in enumerate(records[:summary_index]):
            if not _is_retained_pre_summary_user_input(record):
                continue
            content = _record_to_user_content(
                record,
                state=state,
                include_uploads=not suppress_pre_summary_uploads,
            )
            if content:
                message = {
                    "role": "user",
                    "content": content,
                    "_record_ids": _normalize_internal_record_ids(record.get("id")),
                }
                record_id = str(record.get("id") or "").strip()
                should_defer = False
                if defer_pre_summary_users_until_after_summary and record_id not in anchor_user_record_ids:
                    should_defer = True
                    if (
                        earliest_summarized_record_index is not None
                        and index < earliest_summarized_record_index
                    ):
                        should_defer = False
                if should_defer:
                    deferred_pre_summary_messages.append(message)
                else:
                    messages.append(message)

    if summary_record:
        messages.append(
            {
                "role": "user",
                "content": summary_record.get("text", ""),
                "is_summary": True,
                "_record_ids": _normalize_internal_record_ids(summary_record.get("id")),
            }
        )

    messages.extend(_projection_injection_messages(state))
    messages.extend(deferred_pre_summary_messages)

    visible_records = records[summary_index + 1 :] if summary_index >= 0 else records

    for record in visible_records:
        record_type = record.get("type")
        if record_type in {"system_context", "summary", "audit_event"}:
            continue
        if _record_is_summary_compacted(record):
            continue
        if record_type == "user_input":
            content = _record_to_user_content(record, state=state)
            if content:
                messages.append(
                    {
                        "role": "user",
                        "content": content,
                        "_record_ids": _normalize_internal_record_ids(record.get("id")),
                    }
                )
            continue
        if record_type == "assistant_output":
            tool_calls = [
                _deepcopy_jsonable(tool_record.get("payload"))
                for tool_record in assistant_tool_records.get(record.get("id"), [])
            ]
            message = {
                "role": "assistant",
                "content": record.get("text", ""),
                "_record_ids": _normalize_internal_record_ids(
                    record.get("id"),
                    [tool_record.get("id") for tool_record in assistant_tool_records.get(record.get("id"), [])],
                ),
            }
            payload = record.get("payload") or {}
            provider_specific_fields = None
            thinking_content = None
            thinking_blocks = None
            if isinstance(payload, dict):
                provider_specific_fields = payload.get("provider_specific_fields")
                thinking_content = payload.get("thinking_content")
                thinking_blocks = payload.get("thinking_blocks")
            if provider_specific_fields:
                message["provider_specific_fields"] = _deepcopy_jsonable(provider_specific_fields)
            if thinking_content:
                message["thinking_content"] = _deepcopy_jsonable(thinking_content)
            if thinking_blocks:
                message["thinking_blocks"] = _deepcopy_jsonable(thinking_blocks)
            if tool_calls:
                message["tool_calls"] = tool_calls
            messages.append(message)
            continue
        if record_type == "tool_result":
            messages.append(
                {
                    "role": "tool",
                    "content": record.get("text", ""),
                    "name": record.get("tool_name"),
                    "tool_call_id": record.get("tool_call_id"),
                    "_record_ids": _normalize_internal_record_ids(record.get("id")),
                }
            )
            continue
        if record_type == "subtask_summary":
            continue

    return messages


def rebuild_compiled_messages(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    compiled = compile_messages_for_llm(state)
    state["messages"] = compiled
    return compiled


def build_timeline(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    timeline: List[Dict[str, Any]] = []
    for record in state.get("message_records") or []:
        if record.get("type") == "audit_event" or record.get("hidden") or record.get("superseded_at"):
            continue
        timeline.append(_deepcopy_jsonable(record))
    return timeline


def build_api_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    persisted = extract_persistable_state(state, refresh_updated_at=False)
    conversation = {
        "id": persisted.get("conversation_id"),
        "title": persisted["session_metadata"].get("conversation_title"),
        "created_at": persisted["session_metadata"].get("created_at"),
        "updated_at": persisted["session_metadata"].get("updated_at"),
    }
    runtime_control = _deepcopy_jsonable(persisted["runtime_control"])
    runtime_control["pending_ask_message_payload"] = get_pending_ask_user_payload(persisted)
    return {
        "conversation": conversation,
        "timeline": build_timeline(persisted),
        "runtime_control": runtime_control,
        "session_metadata": _deepcopy_jsonable(persisted["session_metadata"]),
        "todolist": _deepcopy_jsonable(persisted["todolist"]),
        "projections": _deepcopy_jsonable(persisted["projections"]),
        "asset_index": _deepcopy_jsonable(persisted["asset_index"]),
    }
