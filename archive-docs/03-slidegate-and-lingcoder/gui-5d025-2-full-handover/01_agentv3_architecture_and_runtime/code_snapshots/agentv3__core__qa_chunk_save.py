"""AgentV3 QA chunk save orchestration."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

from tools.memory.qa_chunk_save import save_qa_chunk


logger = logging.getLogger(__name__)

DEFAULT_AGENT_ID = "xhx_agent_v3"
DEFAULT_SOURCE = "xhx_agent_v3_auto"
DEFAULT_TIMEOUT = 5
DEFAULT_ASYNC_MAX_WORKERS = 2
SKIPPED_INPUT_KINDS = {"functional_instruction", "todolist_edit", "todolist_feedback"}

SaveFn = Callable[..., Dict[str, Any]]

_executor: Optional[ThreadPoolExecutor] = None
_executor_max_workers: Optional[int] = None
_executor_lock = threading.Lock()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _coerce_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _coerce_positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _coerce_timeout(value: Any, default: float = DEFAULT_TIMEOUT) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _qa_config(conf: Dict[str, Any]) -> Dict[str, Any]:
    memory_cfg = conf.get("memory") if isinstance(conf, dict) else None
    if not isinstance(memory_cfg, dict):
        return {}
    qa_cfg = memory_cfg.get("qa_chunk_save")
    return qa_cfg if isinstance(qa_cfg, dict) else {}


def _is_internal_agent_state(state: Dict[str, Any]) -> bool:
    runtime_identity = state.get("runtime_identity")
    raw_depth = None
    if isinstance(runtime_identity, dict):
        raw_depth = runtime_identity.get("delegate_depth")
    if raw_depth is None:
        raw_depth = state.get("delegate_depth")
    try:
        if int(raw_depth or 0) > 0:
            return True
    except (TypeError, ValueError):
        pass

    active_agent = _clean_text(state.get("active_agent") or (state.get("runtime_control") or {}).get("active_agent"))
    return active_agent in {"subtask_agent", "reflection_agent", "memory_update_agent"}


def _record_is_main_visible_user_record(record: Dict[str, Any]) -> bool:
    if record.get("type") != "user_input":
        return False
    if record.get("hidden"):
        return False
    if record.get("subtask_id"):
        return False
    scope = _clean_text(record.get("scope"))
    if scope and scope != "main":
        return False
    return True


def _record_is_save_eligible_user_input(record: Dict[str, Any]) -> bool:
    if not _record_is_main_visible_user_record(record):
        return False
    input_kind = _clean_text(record.get("input_kind")) or "text"
    if input_kind in SKIPPED_INPUT_KINDS:
        return False
    return True


def _state_records(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    records = state.get("message_records")
    if not isinstance(records, list):
        main_state = state.get("main_state")
        records = main_state.get("message_records") if isinstance(main_state, dict) else []
    return [record for record in (records or []) if isinstance(record, dict)]


def _format_answer_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return _clean_text(value)


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


def _record_by_id(records: List[Dict[str, Any]], record_id: Any) -> Optional[Dict[str, Any]]:
    target_id = _clean_text(record_id)
    if not target_id:
        return None
    for record in records:
        if _clean_text(record.get("id")) == target_id:
            return record
    return None


def _tool_result_payload(record: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        return {}
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    result = _parse_jsonish(payload.get("result")) if isinstance(payload, dict) else None
    if isinstance(result, dict):
        return result
    text_result = _parse_jsonish(record.get("text"))
    if isinstance(text_result, dict):
        return text_result
    return payload if isinstance(payload, dict) else {}


def _question_labels_by_id(ask_payload: Optional[Dict[str, Any]]) -> Dict[str, str]:
    if not isinstance(ask_payload, dict):
        return {}
    labels: Dict[str, str] = {}
    questions = ask_payload.get("questions")
    if not isinstance(questions, list):
        return labels
    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            continue
        question_id = _clean_text(question.get("id")) or str(index)
        label = (
            _clean_text(question.get("title"))
            or _clean_text(question.get("label"))
            or _clean_text(question.get("question"))
            or f"问题{index}"
        )
        labels[question_id] = label
    return labels


def _find_resume_ask_payload(records: List[Dict[str, Any]], resume_record: Dict[str, Any]) -> Dict[str, Any]:
    parent_record = _record_by_id(records, resume_record.get("parent_id"))
    if parent_record and parent_record.get("tool_name") == "ask_user":
        return _tool_result_payload(parent_record)

    payload = resume_record.get("payload") if isinstance(resume_record.get("payload"), dict) else {}
    request_id = _clean_text(payload.get("request_id"))
    for record in reversed(records):
        if record.get("type") != "tool_result" or record.get("tool_name") != "ask_user":
            continue
        ask_payload = _tool_result_payload(record)
        if request_id and _clean_text(ask_payload.get("request_id")) != request_id:
            continue
        return ask_payload
    return {}


def _format_resume_supplement(payload: Dict[str, Any], ask_payload: Optional[Dict[str, Any]] = None) -> str:
    answers = payload.get("answers")
    if isinstance(answers, dict):
        items = [(key, _format_answer_value(value)) for key, value in answers.items()]
        items = [(key, value) for key, value in items if value]
        if len(items) == 1:
            return items[0][1]
        labels = _question_labels_by_id(ask_payload)
        lines = []
        for index, (key, value) in enumerate(items, start=1):
            label = labels.get(_clean_text(key)) or f"问题{index}"
            lines.append(f"{label}：{value}")
        if lines:
            return "\n".join(lines)
    if isinstance(answers, list):
        values = [_format_answer_value(value) for value in answers]
        values = [value for value in values if value]
        if len(values) == 1:
            return values[0]
        if len(values) > 1:
            return "\n".join(values)

    for key in ("answer", "user_answer", "user_feedback", "text"):
        candidate = _format_answer_value(payload.get(key))
        if candidate:
            return candidate

    if payload:
        return json.dumps(payload, ensure_ascii=False)
    return ""


def _format_option(option: Any) -> str:
    if isinstance(option, dict):
        label = (
            _clean_text(option.get("label"))
            or _clean_text(option.get("value"))
            or _clean_text(option.get("text"))
            or json.dumps(option, ensure_ascii=False)
        )
        description = _clean_text(option.get("description"))
        return f"{label}：{description}" if description else label
    return _format_answer_value(option)


def _format_ask_user_assistant_text(ask_payload: Dict[str, Any]) -> str:
    questions = ask_payload.get("questions")
    if not isinstance(questions, list) or not questions:
        question = _clean_text(ask_payload.get("question"))
        return question

    sections: List[str] = []
    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            continue
        question_text = (
            _clean_text(question.get("question"))
            or _clean_text(question.get("title"))
            or _clean_text(question.get("label"))
            or f"问题{index}"
        )
        section_lines = [question_text]
        options = question.get("options")
        if isinstance(options, list) and options:
            option_lines = [_format_option(option) for option in options]
            option_lines = [line for line in option_lines if line]
            if option_lines:
                section_lines.append("选项：")
                section_lines.extend(f"{option_index}. {line}" for option_index, line in enumerate(option_lines, start=1))
        sections.append("\n".join(section_lines).strip())
    return "\n\n".join(section for section in sections if section).strip()


def _find_previous_plain_user_text(records: List[Dict[str, Any]], before_index: int) -> str:
    for record in reversed(records[:before_index]):
        if not _record_is_save_eligible_user_input(record):
            continue
        input_kind = _clean_text(record.get("input_kind")) or "text"
        if input_kind == "resume_answer":
            continue
        text = _clean_text(record.get("text"))
        if text:
            return text
    return ""


def _extract_user_text(state: Dict[str, Any], session_ctx: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    records = _state_records(state)
    for index in range(len(records) - 1, -1, -1):
        record = records[index]
        if not _record_is_main_visible_user_record(record):
            continue
        input_kind = _clean_text(record.get("input_kind")) or "text"
        if input_kind in SKIPPED_INPUT_KINDS:
            return None, f"skipped_input_kind:{input_kind}"
        if input_kind == "resume_answer":
            payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
            ask_payload = _find_resume_ask_payload(records, record)
            supplement = _format_resume_supplement(payload, ask_payload=ask_payload)
            if supplement:
                return supplement, None
            return None, "empty_resume_answer"

        text = _clean_text(record.get("text"))
        if text:
            return text, None

    fallback = _clean_text(session_ctx.get("raw_query"))
    if fallback:
        return fallback, None
    return None, "missing_user_text"


def _find_pending_ask_user_record(state: Dict[str, Any], records: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], int]:
    runtime = state.get("runtime_control") if isinstance(state.get("runtime_control"), dict) else {}
    pending_id = runtime.get("pending_ask_user_message_id") if isinstance(runtime, dict) else None
    pending_record = _record_by_id(records, pending_id)
    if pending_record and pending_record.get("type") == "tool_result" and pending_record.get("tool_name") == "ask_user":
        return pending_record, records.index(pending_record)

    request_id = _clean_text(runtime.get("pending_ask_user_request_id")) if isinstance(runtime, dict) else ""
    for index in range(len(records) - 1, -1, -1):
        record = records[index]
        if record.get("type") != "tool_result" or record.get("tool_name") != "ask_user":
            continue
        payload = _tool_result_payload(record)
        if request_id and _clean_text(payload.get("request_id")) != request_id:
            continue
        if _clean_text(payload.get("status")) == "waiting_for_user_input":
            return record, index
    return None, -1


def _resolve_session_id(state: Dict[str, Any], session_ctx: Dict[str, Any]) -> str:
    if isinstance(state, dict):
        conversation_id = _clean_text(state.get("conversation_id"))
        if conversation_id:
            return conversation_id
        main_state = state.get("main_state")
        if isinstance(main_state, dict):
            conversation_id = _clean_text(main_state.get("conversation_id"))
            if conversation_id:
                return conversation_id
    if isinstance(session_ctx, dict):
        conversation_id = _clean_text(session_ctx.get("conversation_id"))
        if conversation_id:
            return conversation_id
    return ""


def _resolve_user_id(conf: Dict[str, Any]) -> str:
    memory_cfg = conf.get("memory") if isinstance(conf, dict) else None
    return _clean_text(conf.get("user_id") or ((memory_cfg or {}).get("user_id") if isinstance(memory_cfg, dict) else None))


def _build_save_config(conf: Dict[str, Any]) -> Dict[str, Any]:
    save_config = deepcopy(conf) if isinstance(conf, dict) else {}
    save_config.setdefault("tenant_id", "default")
    return save_config


def _get_executor(max_workers: int) -> ThreadPoolExecutor:
    global _executor, _executor_max_workers
    with _executor_lock:
        if _executor is None or _executor_max_workers != max_workers:
            old_executor = _executor
            _executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="qa-chunk-save")
            _executor_max_workers = max_workers
            if old_executor is not None:
                try:
                    old_executor.shutdown(wait=False, cancel_futures=False)
                except Exception:
                    logger.debug("old QA chunk save executor shutdown failed", exc_info=True)
        return _executor


def _run_save(save_fn: SaveFn, save_kwargs: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = save_fn(**save_kwargs)
    except Exception as exc:
        logger.warning("QA chunk save failed: %s", exc)
        return {"saved": False, "reason": str(exc)}

    if not isinstance(result, dict):
        logger.warning("QA chunk save returned non-dict result: %r", result)
        return {"saved": False, "reason": "invalid_save_result"}
    if not result.get("saved"):
        logger.warning("QA chunk save skipped/failed: %s", result.get("reason"))
    else:
        config = save_kwargs.get("config") if isinstance(save_kwargs, dict) else {}
        memory_cfg = config.get("memory") if isinstance(config, dict) else {}
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        user_id = ""
        if isinstance(config, dict):
            user_id = _clean_text(config.get("user_id") or (memory_cfg or {}).get("user_id"))
        logger.info(
            "QA chunk save succeeded: session_id=%s user_id=%s chunk_id=%s deduped=%s",
            _clean_text(save_kwargs.get("session_id")),
            user_id,
            _clean_text(data.get("chunk_id") or data.get("id")),
            data.get("deduped"),
        )
    return result


def _submit_async_save(*, save_fn: SaveFn, save_kwargs: Dict[str, Any], max_workers: int) -> Dict[str, Any]:
    executor = _get_executor(max_workers)
    executor.submit(_run_save, save_fn=save_fn, save_kwargs=save_kwargs)
    return {"saved": False, "reason": "queued"}


def maybe_save_final_qa_chunk(
    *,
    state: Dict[str, Any],
    session_ctx: Dict[str, Any],
    final_response: Any,
    waiting_user_input: bool,
    save_fn: SaveFn = save_qa_chunk,
) -> Dict[str, Any]:
    """Maybe save the top-level final QA pair for this AgentV3 run."""
    if waiting_user_input:
        return {"saved": False, "reason": "waiting_user_input"}
    if not isinstance(state, dict):
        return {"saved": False, "reason": "invalid_state"}
    if _is_internal_agent_state(state):
        return {"saved": False, "reason": "internal_agent"}

    conf = session_ctx.get("conf") if isinstance(session_ctx, dict) else {}
    conf = conf if isinstance(conf, dict) else {}
    qa_cfg = _qa_config(conf)
    if not _coerce_bool(qa_cfg.get("enabled"), True):
        return {"saved": False, "reason": "disabled"}

    assistant_text = _clean_text(final_response)
    if not assistant_text:
        return {"saved": False, "reason": "empty_assistant_text"}

    user_id = _resolve_user_id(conf)
    if not user_id:
        logger.warning("QA chunk save skipped: missing user_id")
        return {"saved": False, "reason": "missing_user_id"}

    session_id = _resolve_session_id(state, session_ctx)
    if not session_id:
        return {"saved": False, "reason": "missing_session_id"}

    user_text, reason = _extract_user_text(state, session_ctx)
    if not user_text:
        return {"saved": False, "reason": reason or "missing_user_text"}

    save_kwargs = {
        "config": _build_save_config(conf),
        "user_text": user_text,
        "assistant_text": assistant_text,
        "session_id": session_id,
        "agent_id": _clean_text(qa_cfg.get("agent_id")) or DEFAULT_AGENT_ID,
        "source": _clean_text(qa_cfg.get("source")) or DEFAULT_SOURCE,
        "timeout": _coerce_timeout(qa_cfg.get("timeout"), DEFAULT_TIMEOUT),
    }

    if _coerce_bool(qa_cfg.get("async_enabled"), True):
        return _submit_async_save(
            save_fn=save_fn,
            save_kwargs=save_kwargs,
            max_workers=_coerce_positive_int(qa_cfg.get("async_max_workers"), DEFAULT_ASYNC_MAX_WORKERS),
        )

    return _run_save(save_fn, save_kwargs)


def maybe_save_waiting_ask_user_qa_chunk(
    *,
    state: Dict[str, Any],
    session_ctx: Dict[str, Any],
    waiting_user_input: bool,
    save_fn: SaveFn = save_qa_chunk,
) -> Dict[str, Any]:
    """Save the first QA segment when ask_user turns the run into a waiting state."""
    if not waiting_user_input:
        return {"saved": False, "reason": "not_waiting_user_input"}
    if not isinstance(state, dict):
        return {"saved": False, "reason": "invalid_state"}
    if _is_internal_agent_state(state):
        return {"saved": False, "reason": "internal_agent"}

    conf = session_ctx.get("conf") if isinstance(session_ctx, dict) else {}
    conf = conf if isinstance(conf, dict) else {}
    qa_cfg = _qa_config(conf)
    if not _coerce_bool(qa_cfg.get("enabled"), True):
        return {"saved": False, "reason": "disabled"}

    user_id = _resolve_user_id(conf)
    if not user_id:
        logger.warning("QA chunk save skipped: missing user_id")
        return {"saved": False, "reason": "missing_user_id"}

    session_id = _resolve_session_id(state, session_ctx)
    if not session_id:
        return {"saved": False, "reason": "missing_session_id"}

    records = _state_records(state)
    ask_record, ask_index = _find_pending_ask_user_record(state, records)
    if ask_record is None or ask_index < 0:
        return {"saved": False, "reason": "no_pending_ask_user"}

    ask_payload = _tool_result_payload(ask_record)
    assistant_text = _format_ask_user_assistant_text(ask_payload)
    if not assistant_text:
        return {"saved": False, "reason": "empty_ask_user_question"}

    user_text = _find_previous_plain_user_text(records, ask_index) or _clean_text(session_ctx.get("raw_query"))
    if not user_text:
        return {"saved": False, "reason": "missing_user_text"}

    save_kwargs = {
        "config": _build_save_config(conf),
        "user_text": user_text,
        "assistant_text": assistant_text,
        "session_id": session_id,
        "agent_id": _clean_text(qa_cfg.get("agent_id")) or DEFAULT_AGENT_ID,
        "source": _clean_text(qa_cfg.get("source")) or DEFAULT_SOURCE,
        "timeout": _coerce_timeout(qa_cfg.get("timeout"), DEFAULT_TIMEOUT),
    }

    if _coerce_bool(qa_cfg.get("async_enabled"), True):
        return _submit_async_save(
            save_fn=save_fn,
            save_kwargs=save_kwargs,
            max_workers=_coerce_positive_int(qa_cfg.get("async_max_workers"), DEFAULT_ASYNC_MAX_WORKERS),
        )

    return _run_save(save_fn, save_kwargs)
