import json
import logging
import threading
from contextlib import contextmanager
from copy import deepcopy
from datetime import date as date_cls, datetime, time as time_cls, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.sax.saxutils import escape as xml_escape

from jinja2 import Environment, FileSystemLoader

from backend.replay_runtime import checkpoint_runtime_state, record_runtime_event
from agents.agentv3.system_prompt_utils import render_system_prompt_from_config
from src.base_agent import BaseAgent, BaseNode, normalize_messages_for_llm
from src.conversation_state_v3 import (
    append_record,
    compile_messages_for_llm,
    extract_persistable_state,
    rebuild_compiled_messages,
)
from src.utils import ctx
from src.utils.context_token_utils import estimate_content_tokens
from tools.multimodal_file.glob_tool import glob as glob_files


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MEMORY_UPDATE_ALLOWED_TOOLS = ("read", "edit", "write")
DEFAULT_MEMORY_UPDATE_MAX_LOOPS = 12
PLACEHOLDER_DATE_SESSION_TITLE_MEMORY_PATH = "__DATE_SESSION_TITLE_MEMORY_PATH__"
PLACEHOLDER_DATE_MEMORY_PATH = "__DATE_MEMORY_PATH__"
DATE_SEPARATOR_CONVERSATION_RECORD_TYPES = {"user_input", "assistant_output", "tool_result"}
MEMORY_UPDATE_INPUT_RECORD_TYPES = {"user_input", "assistant_output"}
MEMORY_UPDATE_INPUT_TOOL_RECORD_TYPES = {"tool_call", "tool_result"}
MEMORY_UPDATE_INPUT_PRESERVED_TOOL_NAME = "ask_user"
MEMORY_UPDATE_INPUT_BLOCK_VAR = "MEMORY_UPDATE_INPUT_BLOCK"
DEFAULT_MEMORY_UPDATE_TENANT_ID = "default"
# date-memory 是跨 session 汇总文件；同一租户同一用户同时写会互相覆盖，
# 所以第二阶段更新必须串行化。这里是进程内锁，跨进程锁需要后续接数据库/队列锁。
_DATE_MEMORY_UPDATE_LOCKS_GUARD = threading.Lock()
_DATE_MEMORY_UPDATE_LOCKS: Dict[tuple[str, str], threading.Lock] = {}


def _normalize_prompt_language(language: Optional[str]) -> Optional[str]:
    if not language:
        return None
    value = str(language).strip().lower()
    if value.startswith("zh"):
        return "zh"
    if value.startswith("en"):
        return "en"
    return value or None


def _resolve_memory_update_prompt_path(
    runtime_conf: Optional[Dict[str, Any]],
    *,
    prompt_key: str,
    zh_path: str,
    en_path: str,
) -> Path:
    runtime_conf = runtime_conf or {}
    lang = _normalize_prompt_language(runtime_conf.get("language"))

    zh_key = f"{prompt_key}_zh"
    en_key = f"{prompt_key}_en"
    if lang == "zh" and runtime_conf.get(zh_key):
        return Path(str(runtime_conf[zh_key]))
    if lang == "en" and runtime_conf.get(en_key):
        return Path(str(runtime_conf[en_key]))

    prompt_value = runtime_conf.get(prompt_key)
    if isinstance(prompt_value, dict):
        if lang and prompt_value.get(lang):
            return Path(str(prompt_value[lang]))
        if prompt_value.get("default"):
            return Path(str(prompt_value["default"]))
    elif isinstance(prompt_value, str) and prompt_value.strip() and prompt_value.strip().lower() != "auto":
        return Path(prompt_value)

    return Path(zh_path if lang == "zh" else en_path)


def _memory_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    memory_cfg = (config or {}).get("memory") if isinstance(config, dict) else {}
    return memory_cfg if isinstance(memory_cfg, dict) else {}


def _runtime_config_for_memory_update(
    config: Optional[Dict[str, Any]],
    *,
    runtime_lang: Optional[str] = None,
) -> Dict[str, Any]:
    config = config or {}
    runtime_conf = dict(config.get("runtime") or {}) if isinstance(config.get("runtime"), dict) else {}
    memory_cfg = _memory_config(config)
    for key in (
        "memory_update_system_prompt",
        "memory_update_system_prompt_zh",
        "memory_update_system_prompt_en",
        "date_separator_prompt",
        "date_separator_prompt_zh",
        "date_separator_prompt_en",
        "memory_update_input_compression_prompt",
        "memory_update_input_compression_prompt_zh",
        "memory_update_input_compression_prompt_en",
        "date_session_memory_update_prompt",
        "date_session_memory_update_prompt_zh",
        "date_session_memory_update_prompt_en",
        "date_memory_update_prompt",
        "date_memory_update_prompt_zh",
        "date_memory_update_prompt_en",
    ):
        if key in memory_cfg:
            runtime_conf[key] = memory_cfg[key]
    runtime_conf["language"] = _normalize_prompt_language(
        runtime_lang or runtime_conf.get("language")
    )
    return runtime_conf


def _memory_update_enabled(config: Optional[Dict[str, Any]]) -> bool:
    memory_cfg = _memory_config(config)
    if not memory_cfg:
        return False
    return bool(memory_cfg.get("enabled", memory_cfg.get("enable", False)))


def _safe_positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _coerce_memory_update_time(value: Any) -> datetime:
    # 记忆更新入口传完整 datetime；这里兼容 date/iso 字符串，方便测试和旧调用逐步迁移。
    if isinstance(value, datetime):
        return value.astimezone() if value.tzinfo else value.astimezone()
    if isinstance(value, date_cls):
        return datetime.combine(value, datetime.min.time()).astimezone()
    text = str(value or "").strip()
    if not text:
        raise ValueError("memory_update_time is required")
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid memory_update_time: {value}") from exc
    return parsed.astimezone() if parsed.tzinfo else parsed.astimezone()


def _coerce_optional_message_time(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value.astimezone() if value.tzinfo else value.astimezone()
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed.astimezone() if parsed.tzinfo else parsed.astimezone()


def _resolve_memory_update_max_loops(config: Optional[Dict[str, Any]]) -> int:
    memory_cfg = _memory_config(config)
    runtime_cfg = (config or {}).get("runtime") if isinstance(config, dict) else {}
    runtime_cfg = runtime_cfg if isinstance(runtime_cfg, dict) else {}
    return _safe_positive_int(
        memory_cfg.get("memory_update_max_loops")
        or runtime_cfg.get("memory_update_max_loops"),
        DEFAULT_MEMORY_UPDATE_MAX_LOOPS,
    )


def resolve_session_end_memory_update_wait_time(config: Optional[Dict[str, Any]]) -> int:
    memory_cfg = _memory_config(config)
    if not _memory_update_enabled(config):
        return 0
    try:
        wait_time = int(memory_cfg.get("session_end_memory_update_wait_time") or 0)
    except (TypeError, ValueError):
        return 0
    return max(wait_time, 0)


def _resolve_allowed_tool_names(config: Optional[Dict[str, Any]]) -> set[str]:
    memory_cfg = _memory_config(config)
    raw_names = memory_cfg.get("memory_update_allowed_tools")
    if raw_names is None:
        raw_names = DEFAULT_MEMORY_UPDATE_ALLOWED_TOOLS
    if isinstance(raw_names, str):
        raw_names = [item.strip() for item in raw_names.split(",")]
    if not isinstance(raw_names, (list, tuple, set)):
        raw_names = DEFAULT_MEMORY_UPDATE_ALLOWED_TOOLS
    return {str(name).strip() for name in raw_names if str(name).strip()}


def _resolve_conversation_id(state: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(state, dict):
        return None
    if state.get("conversation_id"):
        return str(state.get("conversation_id"))
    main_state = state.get("main_state")
    if isinstance(main_state, dict) and main_state.get("conversation_id"):
        return str(main_state.get("conversation_id"))
    return getattr(ctx, "conversation_id", None)


def _resolve_session_id(state: Optional[Dict[str, Any]]) -> Optional[str]:
    conversation_id = _resolve_conversation_id(state)
    if conversation_id:
        return str(conversation_id)
    return None


def _resolve_conversation_title(state: Optional[Dict[str, Any]]) -> str:
    if not isinstance(state, dict):
        return ""
    metadata = state.get("session_metadata") or {}
    if isinstance(metadata, dict):
        return str(metadata.get("conversation_title") or "").strip()
    return ""


def _coerce_identity_value(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _resolve_memory_update_identity(
    *,
    key: str,
    config: Optional[Dict[str, Any]],
    state: Optional[Dict[str, Any]],
) -> Optional[str]:
    if isinstance(config, dict):
        value = _coerce_identity_value(config.get(key))
        if value:
            return value
    ctx_config = getattr(ctx, "config", None)
    if isinstance(ctx_config, dict):
        value = _coerce_identity_value(ctx_config.get(key))
        if value:
            return value
    value = _coerce_identity_value(getattr(ctx, key, None))
    if value:
        return value
    if isinstance(state, dict):
        for container in (
            state,
            state.get("runtime_control"),
            state.get("session_metadata"),
        ):
            if not isinstance(container, dict):
                continue
            value = _coerce_identity_value(container.get(key))
            if value:
                return value
    return None


def _resolve_date_memory_update_lock_key(
    *,
    config: Optional[Dict[str, Any]],
    state: Optional[Dict[str, Any]],
) -> Optional[tuple[str, str]]:
    # 锁粒度只按 tenant_id + user_id；不同会话可以并发更新 date-session-memory，
    # 但同一个用户的 date-memory 汇总只能一次一个。
    user_id = _resolve_memory_update_identity(
        key="user_id",
        config=config,
        state=state,
    )
    if not user_id:
        return None
    tenant_id = _resolve_memory_update_identity(
        key="tenant_id",
        config=config,
        state=state,
    ) or DEFAULT_MEMORY_UPDATE_TENANT_ID
    return tenant_id, user_id


def _get_date_memory_update_lock(key: tuple[str, str]) -> threading.Lock:
    with _DATE_MEMORY_UPDATE_LOCKS_GUARD:
        lock = _DATE_MEMORY_UPDATE_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _DATE_MEMORY_UPDATE_LOCKS[key] = lock
        return lock


@contextmanager
def _date_memory_update_lock(
    *,
    config: Optional[Dict[str, Any]],
    state: Optional[Dict[str, Any]],
):
    lock_key = _resolve_date_memory_update_lock_key(config=config, state=state)
    if lock_key is None:
        yield
        return

    lock = _get_date_memory_update_lock(lock_key)
    logger.info(
        "date-memory update lock waiting: tenant_id=%s user_id=%s",
        lock_key[0],
        lock_key[1],
    )
    lock.acquire()
    try:
        logger.info(
            "date-memory update lock acquired: tenant_id=%s user_id=%s",
            lock_key[0],
            lock_key[1],
        )
        yield
    finally:
        lock.release()
        logger.info(
            "date-memory update lock released: tenant_id=%s user_id=%s",
            lock_key[0],
            lock_key[1],
        )


def _memory_update_rounds_succeeded(rounds: Any) -> bool:
    if not isinstance(rounds, list):
        return False
    statuses = {
        str((item or {}).get("kind") or ""): str((item or {}).get("status") or "")
        for item in rounds
        if isinstance(item, dict)
    }
    return (
        statuses.get("date_session_memory") == "succeeded"
        and statuses.get("date_memory") == "succeeded"
    )


def is_memory_update_payload_complete_for_date(
    payload: Any,
    *,
    date: str,
) -> bool:
    if not isinstance(payload, dict):
        return False
    if str(payload.get("date") or "").strip() != str(date or "").strip():
        return False
    if str(payload.get("status") or "succeeded").strip() != "succeeded":
        return False
    return _memory_update_rounds_succeeded(payload.get("rounds"))


def is_latest_memory_update_complete_for_date(
    state: Optional[Dict[str, Any]],
    *,
    date: str,
) -> bool:
    # 零点收口用这个判断“这个会话树的最后有效节点是否已经完成目标日期记忆更新”。
    # audit_event 不算业务节点；如果最后有效节点不是 memory_update，就说明后面又有新内容。
    if not isinstance(state, dict):
        return False
    for record in reversed(state.get("message_records") or []):
        if not isinstance(record, dict) or record.get("superseded_at"):
            continue
        if record.get("type") == "audit_event":
            continue
        if record.get("type") != "memory_update":
            return False
        return is_memory_update_payload_complete_for_date(record.get("payload"), date=date)

    memory_updates = (state.get("runtime_control") or {}).get("memory_updates")
    if isinstance(memory_updates, dict):
        for node in reversed(list(memory_updates.values())):
            if not isinstance(node, dict):
                continue
            if node.get("kind") != "memory_update":
                continue
            return is_memory_update_payload_complete_for_date(node, date=date)
    return False


def _resolve_date_session_title_memory_path(
    *,
    date: str,
    session_id: Optional[str],
    date_session_memory_dir: str,
    config: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    # 标题不一定提前知道，所以只按 date + session_id 搜索对应的标题化文件名。
    date_session_title_memory_path = None
    if session_id:
        glob_result = glob_files(
            pattern=f"{date}-{session_id}-*.md",
            path=date_session_memory_dir,
            limit=1,
            config=config,
        )
        if isinstance(glob_result, dict) and glob_result.get("success"):
            filenames = glob_result.get("filenames")
            if isinstance(filenames, list) and filenames:
                date_session_title_memory_path = str(filenames[0])
    return date_session_title_memory_path


def _render_date_session_memory_update_prompt_from_config(
    config: Optional[Dict[str, Any]],
    template_path: str,
    *,
    memory_update_time: Any,
    state: Optional[Dict[str, Any]] = None,
    state_var_overrides: Optional[Dict[str, Any]] = None,
) -> str:
    memory_cfg = _memory_config(config)
    update_time = _coerce_memory_update_time(memory_update_time)
    date = update_time.date().isoformat()
    session_id = _resolve_session_id(state)
    date_session_memory_dir = str(
        memory_cfg.get("date_session_memory_dir") or "memory://"
    )
    date_session_title_memory_path = _resolve_date_session_title_memory_path(
        date=date,
        session_id=session_id,
        date_session_memory_dir=date_session_memory_dir,
        config=config,
    )
    state_vars = {
        "CURRENT_TIME": update_time.strftime("%H:%M:%S"),
        "DATE": date,
        "SESSION_ID": session_id or "",
        "CONVERSATION_ID": _resolve_conversation_id(state) or "",
        "CONVERSATION_TITLE": _resolve_conversation_title(state),
        "DATE_SESSION_MEMORY_DIR": date_session_memory_dir,
        "DATE_SESSION_TITLE_MEMORY_PATH": date_session_title_memory_path,
        "DATE_MEMORY_PATH": str(
            memory_cfg.get("date_memory_path")
            or PLACEHOLDER_DATE_MEMORY_PATH
        ),
    }
    if isinstance(state_var_overrides, dict):
        state_vars.update(state_var_overrides)

    template_file = Path(template_path)
    if not template_file.is_absolute():
        template_file = PROJECT_ROOT / template_file
    if not template_file.is_file():
        raise FileNotFoundError(str(template_file))

    env = Environment(loader=FileSystemLoader(str(template_file.parent)))
    template = env.get_template(template_file.name)
    date_session_memory_prompt = template.render(**state_vars)
    return date_session_memory_prompt


def _render_date_memory_update_prompt_from_config(
    config: Optional[Dict[str, Any]],
    template_path: str,
    *,
    memory_update_time: Any,
    state: Optional[Dict[str, Any]] = None,
    state_var_overrides: Optional[Dict[str, Any]] = None,
) -> str:
    memory_cfg = _memory_config(config)
    update_time = _coerce_memory_update_time(memory_update_time)
    date = update_time.date().isoformat()
    session_id = _resolve_session_id(state)
    date_session_memory_dir = str(
        memory_cfg.get("date_session_memory_dir") or "memory://"
    )
    date_session_title_memory_path = _resolve_date_session_title_memory_path(
        date=date,
        session_id=session_id,
        date_session_memory_dir=date_session_memory_dir,
        config=config,
    )
    date_memory_dir = str(
        memory_cfg.get("date_memory_dir") or "memory://date-memory/"
    )
    date_memory_path = f"{date_memory_dir}{date}.md"
    state_vars = {
        "CURRENT_TIME": update_time.strftime("%H:%M:%S"),
        "DATE": date,
        "SESSION_ID": _resolve_session_id(state) or "",
        "CONVERSATION_ID": _resolve_conversation_id(state) or "",
        "CONVERSATION_TITLE": _resolve_conversation_title(state),
        "DATE_MEMORY_DIR": date_memory_dir,
        "DATE_SESSION_TITLE_MEMORY_PATH": date_session_title_memory_path,
        "DATE_MEMORY_PATH": date_memory_path,
    }
    if isinstance(state_var_overrides, dict):
        state_vars.update(state_var_overrides)

    template_file = Path(template_path)
    if not template_file.is_absolute():
        template_file = PROJECT_ROOT / template_file
    if not template_file.is_file():
        raise FileNotFoundError(str(template_file))

    env = Environment(loader=FileSystemLoader(str(template_file.parent)))
    template = env.get_template(template_file.name)
    date_memory_prompt = template.render(**state_vars)
    return date_memory_prompt


def _render_memory_update_system_prompt_from_config(
    config: Optional[Dict[str, Any]],
    template_path: str,
    *,
    memory_update_time: Any,
    state: Optional[Dict[str, Any]] = None,
    state_var_overrides: Optional[Dict[str, Any]] = None,
) -> str:
    memory_cfg = _memory_config(config)
    update_time = _coerce_memory_update_time(memory_update_time)
    date = update_time.date().isoformat()
    session_id = _resolve_session_id(state)
    date_session_memory_dir = str(
        memory_cfg.get("date_session_memory_dir") or "memory://"
    )
    date_session_title_memory_path = _resolve_date_session_title_memory_path(
        date=date,
        session_id=session_id,
        date_session_memory_dir=date_session_memory_dir,
        config=config,
    )
    date_memory_dir = str(
        memory_cfg.get("date_memory_dir") or "memory://date-memory/"
    )
    state_vars = {
        "CURRENT_DATE": date,
        "CURRENT_TIME": update_time.strftime("%H:%M:%S"),
        "DATE": date,
        "SESSION_ID": session_id or "",
        "CONVERSATION_ID": _resolve_conversation_id(state) or "",
        "CONVERSATION_TITLE": _resolve_conversation_title(state),
        "DATE_SESSION_MEMORY_DIR": date_session_memory_dir,
        "DATE_SESSION_TITLE_MEMORY_PATH": date_session_title_memory_path,
        "DATE_MEMORY_DIR": date_memory_dir,
        "DATE_MEMORY_PATH": f"{date_memory_dir}{date}.md",
    }
    if isinstance(state_var_overrides, dict):
        state_vars.update(state_var_overrides)

    template_file = Path(template_path)
    if not template_file.is_absolute():
        template_file = PROJECT_ROOT / template_file
    if not template_file.is_file():
        raise FileNotFoundError(str(template_file))

    return render_system_prompt_from_config(
        config=config,
        template_path=str(template_file),
        state_var_overrides=state_vars,
    )


def _clone_memory_update_node(
    source_node: BaseNode,
    *,
    config: Optional[Dict[str, Any]],
) -> BaseNode:
    allowed_names = _resolve_allowed_tool_names(config)
    cloned = BaseNode(name="main", llm=source_node.llm, tools=None)
    for schema in source_node.tool_schemas:
        tool_name = str(((schema.get("function") or {}).get("name") or "")).strip()
        if tool_name not in allowed_names:
            continue
        if tool_name not in source_node.tool_map:
            continue
        cloned.tool_schemas.append(deepcopy(schema))
        cloned.tool_map[tool_name] = source_node.tool_map[tool_name]
        cloned.tool_config_keys[tool_name] = source_node.tool_config_keys.get(tool_name, tool_name)
    return cloned


def build_memory_update_node(
    *,
    llm: Any,
    tools: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> BaseNode:
    source_node = BaseNode(name="main", llm=llm, tools=tools or [])
    return _clone_memory_update_node(source_node, config=config)


@contextmanager
def _suppress_streaming_for_memory_update():
    had_suppress_stream = hasattr(ctx, "suppress_stream")
    previous_suppress_stream = getattr(ctx, "suppress_stream", None)
    had_delegate_progress = hasattr(ctx, "delegate_progress_callback")
    previous_delegate_progress = getattr(ctx, "delegate_progress_callback", None)
    ctx.suppress_stream = True
    if hasattr(ctx, "delegate_progress_callback"):
        delattr(ctx, "delegate_progress_callback")
    try:
        yield
    finally:
        if had_suppress_stream:
            ctx.suppress_stream = previous_suppress_stream
        elif hasattr(ctx, "suppress_stream"):
            delattr(ctx, "suppress_stream")
        if had_delegate_progress:
            ctx.delegate_progress_callback = previous_delegate_progress


def _source_messages_for_memory_update(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    if "message_records" in state:
        return compile_messages_for_llm(extract_persistable_state(state))
    messages = state.get("messages")
    return deepcopy(messages) if isinstance(messages, list) else []


def _safe_optional_positive_int(value: Any) -> Optional[int]:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _record_created_at(record: Dict[str, Any]) -> Optional[datetime]:
    return _coerce_optional_message_time(record.get("created_at"))


def _target_day_bounds(update_time: datetime) -> tuple[datetime, datetime]:
    start = datetime.combine(update_time.date(), time_cls.min, tzinfo=update_time.tzinfo)
    return start, start + timedelta(days=1)


def _memory_update_input_records(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not isinstance(state, dict):
        return records
    source_records = [
        record
        for record in state.get("message_records") or []
        if isinstance(record, dict) and not record.get("superseded_at")
    ]
    # 空 assistant_output 如果只是承载工具调用，不提供可记忆文本，先过滤掉再做日期分段/压缩。
    tool_parent_ids = {
        str(record.get("parent_id") or "")
        for record in source_records
        if record.get("type") == "tool_call" and record.get("parent_id")
    }
    for record in source_records:
        if not isinstance(record, dict) or record.get("superseded_at"):
            continue
        record_type = record.get("type")
        if record_type in MEMORY_UPDATE_INPUT_RECORD_TYPES:
            if (
                record_type == "assistant_output"
                and not str(record.get("text") or "").strip()
                and str(record.get("id") or "") in tool_parent_ids
            ):
                continue
            records.append(record)
            continue
        # 普通工具消息不进入记忆更新输入；ask_user 表示真实用户澄清，必须保留。
        if (
            record_type in MEMORY_UPDATE_INPUT_TOOL_RECORD_TYPES
            and record.get("tool_name") == MEMORY_UPDATE_INPUT_PRESERVED_TOOL_NAME
        ):
            records.append(record)
    return records


def _record_is_before(record: Dict[str, Any], boundary: datetime) -> bool:
    created_at = _record_created_at(record)
    return created_at is not None and created_at < boundary


def _record_is_on_target_day(record: Dict[str, Any], start: datetime, end: datetime) -> bool:
    created_at = _record_created_at(record)
    if created_at is None:
        # Runtime records normally have timestamps. If an older caller omits one,
        # keep the record in the target view instead of silently losing it.
        return True
    return start <= created_at < end


def _nearest_user_index(records: List[Dict[str, Any]], *, before_index: int) -> Optional[int]:
    upper = min(max(before_index, 0), len(records) - 1)
    for index in range(upper, -1, -1):
        if records[index].get("type") == "user_input":
            return index
    return None


def _collect_carryover_records(
    records: List[Dict[str, Any]],
    target_records: List[Dict[str, Any]],
    *,
    target_start: datetime,
) -> List[Dict[str, Any]]:
    target_record_ids = {
        str(record.get("id") or "")
        for record in target_records
        if record.get("id")
    }
    target_indices = {
        index
        for index, record in enumerate(records)
        if str(record.get("id") or "") in target_record_ids
    }
    carryover_indices: set[int] = set()
    for target_index in sorted(target_indices):
        target_record = records[target_index]
        if target_record.get("type") == "user_input":
            continue
        anchor_index = _nearest_user_index(records, before_index=target_index)
        if anchor_index is None:
            continue
        for index in range(anchor_index, target_index):
            if index in target_indices:
                continue
            candidate = records[index]
            if _record_is_before(candidate, target_start):
                carryover_indices.add(index)
    return [deepcopy(records[index]) for index in sorted(carryover_indices)]


def _xml_attr(value: Any) -> str:
    return xml_escape(str(value or ""), {'"': "&quot;"})


def _xml_text(value: Any) -> str:
    return xml_escape(str(value or ""))


def _record_payload_text(record: Dict[str, Any]) -> str:
    record_type = record.get("type")
    if record_type == "tool_call":
        payload = record.get("payload") or {}
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return str(record.get("text") or "")


def _memory_update_role_for_record(record: Dict[str, Any]) -> str:
    record_type = record.get("type")
    if record_type == "user_input":
        return "user"
    if record_type == "assistant_output":
        return "assistant"
    if record_type == "tool_call":
        return "assistant_tool_call"
    if record_type == "tool_result":
        return "tool"
    return str(record_type or "record")


def _render_record_for_memory_update_input(record: Dict[str, Any]) -> str:
    attrs = {
        "record_id": record.get("id"),
        "role": _memory_update_role_for_record(record),
        "record_type": record.get("type"),
        "created_at": record.get("created_at"),
    }
    if record.get("tool_name"):
        attrs["tool_name"] = record.get("tool_name")
    if record.get("tool_call_id"):
        attrs["tool_call_id"] = record.get("tool_call_id")
    if record.get("parent_id"):
        attrs["parent_id"] = record.get("parent_id")
    attr_text = " ".join(
        f'{key}="{_xml_attr(value)}"'
        for key, value in attrs.items()
        if value not in (None, "")
    )
    content = _xml_text(_record_payload_text(record)).strip()
    return f"<message {attr_text}>\n{content}\n</message>"


def _render_records_for_memory_update_input(records: List[Dict[str, Any]]) -> str:
    return "\n".join(
        _render_record_for_memory_update_input(record)
        for record in records
        if isinstance(record, dict)
    ).strip()


def _resolve_memory_update_input_budget(config: Optional[Dict[str, Any]]) -> Optional[int]:
    runtime_cfg = (config or {}).get("runtime") if isinstance(config, dict) else {}
    runtime_cfg = runtime_cfg if isinstance(runtime_cfg, dict) else {}
    max_context_tokens = _safe_optional_positive_int(runtime_cfg.get("max_context_tokens"))
    if max_context_tokens is None:
        return None
    try:
        ratio = float(runtime_cfg.get("memory_update_input_token_budget_ratio", 0.65))
    except (TypeError, ValueError):
        ratio = 0.65
    if ratio <= 0:
        ratio = 0.65
    return max(1, int(max_context_tokens * min(ratio, 1.0)))


def _estimate_memory_update_text_tokens(text: str, *, config: Optional[Dict[str, Any]]) -> int:
    return estimate_content_tokens(text, config=config)


def _fallback_memory_update_input_summary(messages_block: str, *, max_chars: int = 1200) -> str:
    compact = str(messages_block or "").strip()
    if len(compact) <= max_chars:
        return compact
    return compact[:max_chars].rstrip() + "\n...[truncated for memory update input]..."


def _generate_memory_update_input_summary(
    *,
    mode: str,
    messages_block: str,
    date: str,
    llm: Any,
    config: Optional[Dict[str, Any]],
) -> str:
    if llm is None:
        return _fallback_memory_update_input_summary(messages_block)

    runtime_conf = _runtime_config_for_memory_update(config)
    template_file = _resolve_memory_update_prompt_path(
        runtime_conf,
        prompt_key="memory_update_input_compression_prompt",
        zh_path="agents/agentv3/memory_update_input_compression_prompt_zh.md",
        en_path="agents/agentv3/memory_update_input_compression_prompt_en.md",
    )
    if not template_file.is_absolute():
        template_file = PROJECT_ROOT / template_file
    if template_file.is_file():
        env = Environment(loader=FileSystemLoader(str(template_file.parent)))
        prompt = env.get_template(template_file.name).render(
            DATE=date,
            COMPRESSION_MODE=mode,
            SOURCE_MESSAGES_BLOCK=messages_block,
        )
    else:
        prompt = (
            "你在为 memory-update 构造临时输入摘要，不是在写最终记忆文件。\n"
            f"目标日期：{date}\n压缩类型：{mode}\n\n"
            f"输入消息如下：\n{messages_block}\n\n"
            "只输出压缩后的要点，严禁编造事实，严禁改变日期归属。"
        )
    try:
        response = llm.completion(
            [{"role": "user", "content": prompt}],
            tools=None,
        )
    except Exception as exc:
        logger.warning("memory update input compression failed: %s", exc)
        return _fallback_memory_update_input_summary(messages_block)
    content = str((response or {}).get("content") or "").strip() if isinstance(response, dict) else ""
    return content or _fallback_memory_update_input_summary(messages_block)


def _select_raw_tail_records_for_memory_update(
    records: List[Dict[str, Any]],
    *,
    budget: int,
    config: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if not records:
        return []
    selected_rev: List[Dict[str, Any]] = []
    total = 0
    for record in reversed(records):
        rendered = _render_record_for_memory_update_input(record)
        tokens = _estimate_memory_update_text_tokens(rendered, config=config)
        if not selected_rev or total + tokens <= budget:
            selected_rev.append(record)
            total += max(1, tokens)
            continue
        break
    return list(reversed(selected_rev))


def _render_memory_update_input_block(
    *,
    date: str,
    carryover_records: List[Dict[str, Any]],
    target_records: List[Dict[str, Any]],
    carryover_summary: Optional[str] = None,
    target_prefix_summary: Optional[str] = None,
) -> str:
    lines = [f'<memory_update_input date="{_xml_attr(date)}">']
    lines.append('<carryover_context usage="context_only_not_memory_source">')
    if carryover_summary is not None:
        lines.append(_xml_text(carryover_summary))
    else:
        carryover_text = _render_records_for_memory_update_input(carryover_records)
        lines.append(carryover_text or "<empty />")
    lines.append("</carryover_context>")
    if target_prefix_summary is not None:
        lines.append(f'<target_day_prefix_summary date="{_xml_attr(date)}" usage="memory_source">')
        lines.append(_xml_text(target_prefix_summary))
        lines.append("</target_day_prefix_summary>")
    lines.append(f'<target_day_messages date="{_xml_attr(date)}" usage="memory_source">')
    target_text = _render_records_for_memory_update_input(target_records)
    lines.append(target_text or "<empty />")
    lines.append("</target_day_messages>")
    lines.append("</memory_update_input>")
    return "\n".join(lines).strip()


def _build_memory_update_input_block(
    *,
    state: Dict[str, Any],
    config: Optional[Dict[str, Any]],
    memory_update_time: Any,
    llm: Any,
) -> str:
    update_time = _coerce_memory_update_time(memory_update_time)
    date = update_time.date().isoformat()
    target_start, target_end = _target_day_bounds(update_time)
    records = _memory_update_input_records(state)
    target_records = [
        deepcopy(record)
        for record in records
        if _record_is_on_target_day(record, target_start, target_end)
    ]
    carryover_records = _collect_carryover_records(
        records,
        target_records,
        target_start=target_start,
    )

    raw_block = _render_memory_update_input_block(
        date=date,
        carryover_records=carryover_records,
        target_records=target_records,
    )
    budget = _resolve_memory_update_input_budget(config)
    if budget is None:
        return raw_block
    if _estimate_memory_update_text_tokens(raw_block, config=config) <= budget:
        return raw_block

    carryover_summary = None
    if carryover_records:
        carryover_summary = _generate_memory_update_input_summary(
            mode="carryover_context",
            messages_block=_render_records_for_memory_update_input(carryover_records),
            date=date,
            llm=llm,
            config=config,
        )

    raw_tail_budget = max(1, int(budget * 0.55))
    raw_tail_records = _select_raw_tail_records_for_memory_update(
        target_records,
        budget=raw_tail_budget,
        config=config,
    )
    raw_tail_count = len(raw_tail_records)
    prefix_records = target_records[: max(0, len(target_records) - raw_tail_count)]
    target_prefix_summary = None
    if prefix_records:
        target_prefix_summary = _generate_memory_update_input_summary(
            mode="target_day_prefix",
            messages_block=_render_records_for_memory_update_input(prefix_records),
            date=date,
            llm=llm,
            config=config,
        )

    return _render_memory_update_input_block(
        date=date,
        carryover_records=[],
        target_records=raw_tail_records,
        carryover_summary=carryover_summary,
        target_prefix_summary=target_prefix_summary,
    )


def _template_uses_memory_update_input_block(template_path: str) -> bool:
    template_file = Path(template_path)
    if not template_file.is_absolute():
        template_file = PROJECT_ROOT / template_file
    try:
        return MEMORY_UPDATE_INPUT_BLOCK_VAR in template_file.read_text(encoding="utf-8")
    except Exception:
        return False


def _replace_system_messages_for_memory_update(
    messages: List[Dict[str, Any]],
    *,
    system_prompt: str,
) -> List[Dict[str, Any]]:
    source_messages = messages or []
    first_non_system_index = 0
    while first_non_system_index < len(source_messages):
        message = source_messages[first_non_system_index]
        if not isinstance(message, dict) or message.get("role") != "system":
            break
        first_non_system_index += 1
    round_messages = [
        deepcopy(message)
        for message in source_messages[first_non_system_index:]
        if isinstance(message, dict)
    ]
    system_prompt = str(system_prompt or "").strip()
    if system_prompt:
        return [{"role": "system", "content": system_prompt}, *round_messages]
    return round_messages


def _render_date_separator_prompt(memory_update_time: datetime, *, template_path: str) -> str:
    update_time = _coerce_memory_update_time(memory_update_time)
    template_file = Path(template_path)
    if not template_file.is_absolute():
        template_file = PROJECT_ROOT / template_file
    if not template_file.is_file():
        raise FileNotFoundError(str(template_file))

    env = Environment(loader=FileSystemLoader(str(template_file.parent)))
    template = env.get_template(template_file.name)
    return template.render(CURRENT_DATE=update_time.date().isoformat()).strip()


def _conversation_record_created_at_by_id(state: Dict[str, Any]) -> Dict[str, datetime]:
    record_times: Dict[str, datetime] = {}
    if not isinstance(state, dict):
        return record_times
    for record in state.get("message_records") or []:
        if not isinstance(record, dict):
            continue
        if record.get("type") not in DATE_SEPARATOR_CONVERSATION_RECORD_TYPES:
            continue
        record_id = str(record.get("id") or "").strip()
        if not record_id:
            continue
        created_at = _coerce_optional_message_time(record.get("created_at"))
        if created_at is not None:
            record_times[record_id] = created_at
    return record_times


def _message_created_at(
    message: Dict[str, Any],
    *,
    record_times: Dict[str, datetime],
) -> Optional[datetime]:
    record_ids = message.get("_record_ids")
    if not isinstance(record_ids, list):
        record_ids = [record_ids] if record_ids else []
    resolved_times = [
        record_times[record_id]
        for record_id in (str(item or "").strip() for item in record_ids)
        if record_id in record_times
    ]
    if resolved_times:
        return min(resolved_times)
    if str(message.get("role") or "").strip() == "system":
        return None
    for key in ("created_at", "timestamp", "time"):
        created_at = _coerce_optional_message_time(message.get(key))
        if created_at is not None:
            return created_at
    return None


def _tool_call_ids_from_assistant_message(message: Dict[str, Any]) -> set[str]:
    tool_call_ids: set[str] = set()
    for tool_call in message.get("tool_calls") or []:
        if not isinstance(tool_call, dict):
            continue
        tool_call_id = str(tool_call.get("id") or "").strip()
        if tool_call_id:
            tool_call_ids.add(tool_call_id)
    return tool_call_ids


def _separator_insert_index_without_splitting_tool_group(
    messages: List[Dict[str, Any]],
    insert_index: int,
) -> int:
    if insert_index <= 0 or insert_index >= len(messages):
        return insert_index
    boundary_message = messages[insert_index]
    if not isinstance(boundary_message, dict) or boundary_message.get("role") != "tool":
        return insert_index

    boundary_tool_call_id = str(boundary_message.get("tool_call_id") or "").strip()
    for index in range(insert_index - 1, -1, -1):
        candidate = messages[index]
        if not isinstance(candidate, dict):
            break
        candidate_role = candidate.get("role")
        if candidate_role == "tool":
            continue
        if candidate_role != "assistant":
            break
        assistant_tool_call_ids = _tool_call_ids_from_assistant_message(candidate)
        if assistant_tool_call_ids and (
            not boundary_tool_call_id or boundary_tool_call_id in assistant_tool_call_ids
        ):
            return index
        break
    return insert_index


def _insert_date_separator_for_memory_update(
    messages: List[Dict[str, Any]],
    *,
    state: Dict[str, Any],
    memory_update_time: datetime,
    date_separator_prompt_path: str,
) -> List[Dict[str, Any]]:
    update_time = _coerce_memory_update_time(memory_update_time)
    separator_content = _render_date_separator_prompt(
        update_time,
        template_path=date_separator_prompt_path,
    )
    if not separator_content:
        return deepcopy(messages)

    midnight = datetime.combine(
        update_time.date(),
        time_cls.min,
        tzinfo=update_time.tzinfo,
    )
    record_times = _conversation_record_created_at_by_id(state)
    insert_index = len(messages)
    has_before_midnight = False
    has_on_or_after_midnight = False
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            continue
        created_at = _message_created_at(message, record_times=record_times)
        if created_at is None:
            continue
        if created_at < midnight:
            has_before_midnight = True
            continue
        has_on_or_after_midnight = True
        if insert_index == len(messages):
            insert_index = index

    if not (has_before_midnight and has_on_or_after_midnight):
        return deepcopy(messages)

    insert_index = _separator_insert_index_without_splitting_tool_group(
        messages,
        insert_index,
    )
    updated_messages = deepcopy(messages)
    updated_messages.insert(
        insert_index,
        {"role": "system", "content": separator_content},
    )
    return updated_messages


def _append_memory_update_record(
    state: Dict[str, Any],
    *,
    trigger: str,
    date: str,
    memory_update_time: datetime,
    prompt_rounds: List[Dict[str, Any]],
    update_messages: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if "message_records" not in state:
        return None
    # 记忆更新节点只留下可回退、可审计的元信息；两轮内部消息和工具结果不进入主消息记录。
    payload = {
        "trigger": trigger,
        "date": date,
        "memory_update_time": memory_update_time.isoformat(timespec="seconds"),
        "status": "succeeded",
        "rounds": deepcopy(prompt_rounds),
        "isolated_message_count": len(update_messages),
        "completed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    return append_record(
        state,
        {
            "type": "memory_update",
            "text": "memory update round completed",
            "payload": payload,
            "hidden": True,
            "source": "memory_update",
        },
    )


def _append_memory_update_projection(
    state: Dict[str, Any],
    *,
    record: Optional[Dict[str, Any]],
    trigger: str,
    date: str,
    memory_update_time: datetime,
    prompt_rounds: List[Dict[str, Any]],
    update_messages: List[Dict[str, Any]],
) -> Dict[str, Any]:
    runtime = state.setdefault("runtime_control", {})
    memory_updates = runtime.setdefault("memory_updates", {})
    if not isinstance(memory_updates, dict):
        memory_updates = {}
        runtime["memory_updates"] = memory_updates

    completed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    record_id = record.get("id") if isinstance(record, dict) else None
    node_id = str(record_id or f"memory_update_{trigger}_{len(memory_updates) + 1}")
    # projection 给旧状态结构或无 message_records 的场景留一份同样可判断完成状态的索引。
    node = {
        "id": node_id,
        "kind": "memory_update",
        "status": "succeeded",
        "trigger": trigger,
        "date": date,
        "memory_update_time": memory_update_time.isoformat(timespec="seconds"),
        "record_id": record_id,
        "rounds": deepcopy(prompt_rounds),
        "isolated_message_count": len(update_messages),
        "completed_at": completed_at,
    }
    memory_updates[node_id] = node
    return node


def _checkpoint_memory_update(
    state: Dict[str, Any],
    *,
    trigger: str,
    date: str,
    memory_update_time: datetime,
    record: Optional[Dict[str, Any]],
    prompt_rounds: List[Dict[str, Any]],
) -> None:
    payload = {
        "trigger": trigger,
        "date": date,
        "memory_update_time": memory_update_time.isoformat(timespec="seconds"),
        "status": "succeeded",
        "rounds": deepcopy(prompt_rounds),
    }
    record_runtime_event(
        event_type="memory_update",
        state=state,
        record=record,
        scope="memory_update",
        payload=payload,
    )
    checkpoint_runtime_state(
        checkpoint_kind=f"memory_update_{trigger}",
        state=state,
        include_workspace=False,
    )


def run_memory_update_round(
    *,
    state: Dict[str, Any],
    source_node: Optional[BaseNode],
    config: Optional[Dict[str, Any]] = None,
    runtime_lang: Optional[str] = None,
    memory_update_time: datetime,
    trigger: str = "session_end",
) -> Dict[str, Any]:
    if not _memory_update_enabled(config):
        return {"success": False, "skipped": True, "reason": "memory_update_disabled"}
    if not isinstance(state, dict):
        return {"success": False, "skipped": True, "reason": "invalid_state"}
    if not isinstance(source_node, BaseNode):
        return {"success": False, "skipped": True, "reason": "missing_source_node"}
    try:
        update_time = _coerce_memory_update_time(memory_update_time)
    except ValueError as exc:
        return {"success": False, "skipped": True, "reason": str(exc)}
    # 文件路径和完成判断仍按天聚合，具体触发时刻保留在 memory_update_time。
    date = update_time.date().isoformat()

    runtime_conf = _runtime_config_for_memory_update(config, runtime_lang=runtime_lang)
    memory_update_system_prompt_path = str(
        _resolve_memory_update_prompt_path(
            runtime_conf,
            prompt_key="memory_update_system_prompt",
            zh_path="agents/agentv3/memory_update_system_prompt_zh.md",
            en_path="agents/agentv3/memory_update_system_prompt_en.md",
        )
    )
    date_separator_prompt_path = str(
        _resolve_memory_update_prompt_path(
            runtime_conf,
            prompt_key="date_separator_prompt",
            zh_path="agents/agentv3/date_separator_prompt_zh.md",
            en_path="agents/agentv3/date_separator_prompt_en.md",
        )
    )
    date_session_memory_prompt_path = str(
        _resolve_memory_update_prompt_path(
            runtime_conf,
            prompt_key="date_session_memory_update_prompt",
            zh_path="agents/agentv3/user_prompt_date_session_memory_summary_zh.md",
            en_path="agents/agentv3/user_prompt_date_session_memory_summary_en.md",
        )
    )
    date_memory_prompt_path = str(
        _resolve_memory_update_prompt_path(
            runtime_conf,
            prompt_key="date_memory_update_prompt",
            zh_path="agents/agentv3/user_prompt_date_memory_summary_zh.md",
            en_path="agents/agentv3/user_prompt_date_memory_summary_en.md",
        )
    )
    prompt_rounds = [
        {"kind": "date_session_memory", "prompt_path": date_session_memory_prompt_path, "status": "pending"},
        {"kind": "date_memory", "prompt_path": date_memory_prompt_path, "status": "pending"},
    ]
    logger.info(
        "memory update started: trigger=%s rounds=%s",
        trigger,
        [round_item["kind"] for round_item in prompt_rounds],
    )
    prompts = [
        {
            "kind": "date_session_memory",
            "path": date_session_memory_prompt_path,
        },
        {
            "kind": "date_memory",
            "path": date_memory_prompt_path,
        },
    ]

    update_node = _clone_memory_update_node(source_node, config=config)
    update_agent = BaseAgent(
        name="memory_update_agent",
        nodes=[update_node],
        max_loops=_resolve_memory_update_max_loops(config),
        entry_point="main",
    )
    source_update_messages = _source_messages_for_memory_update(state)
    memory_update_input_block = _build_memory_update_input_block(
        state=state,
        config=config,
        memory_update_time=update_time,
        llm=getattr(source_node, "llm", None),
    )
    memory_update_state_var_overrides = {
        MEMORY_UPDATE_INPUT_BLOCK_VAR: memory_update_input_block,
    }
    update_messages: List[Dict[str, Any]] = []

    with _suppress_streaming_for_memory_update():
        for prompt in prompts:
            round_kind = str(prompt.get("kind") or "")
            prompt_path = str(prompt.get("path") or "")
            uses_memory_update_input_block = _template_uses_memory_update_input_block(prompt_path)
            logger.info(
                "memory update round started: trigger=%s kind=%s prompt_path=%s",
                trigger,
                round_kind,
                prompt_path,
            )
            try:
                if round_kind == "date_session_memory":
                    prompt_content = _render_date_session_memory_update_prompt_from_config(
                        config=config,
                        template_path=prompt_path,
                        state=state,
                        memory_update_time=update_time,
                        state_var_overrides=memory_update_state_var_overrides,
                    ).strip()
                elif round_kind == "date_memory":
                    # date-memory 依赖第一轮创建出的 date-session-title 文件，
                    # 所以必须在第一轮执行完成后再渲染，不能提前批量渲染。
                    prompt_content = _render_date_memory_update_prompt_from_config(
                        config=config,
                        template_path=prompt_path,
                        state=state,
                        memory_update_time=update_time,
                        state_var_overrides=memory_update_state_var_overrides,
                    ).strip()
                else:
                    prompt_content = ""
                system_prompt_content = _render_memory_update_system_prompt_from_config(
                    config=config,
                    template_path=memory_update_system_prompt_path,
                    state=state,
                    memory_update_time=update_time,
                    state_var_overrides=memory_update_state_var_overrides,
                ).strip()
                if uses_memory_update_input_block:
                    round_messages = normalize_messages_for_llm(
                        _replace_system_messages_for_memory_update(
                            [],
                            system_prompt=system_prompt_content,
                        )
                    )
                else:
                    round_messages = normalize_messages_for_llm(
                        _replace_system_messages_for_memory_update(
                            _insert_date_separator_for_memory_update(
                                source_update_messages,
                                state=state,
                                memory_update_time=update_time,
                                date_separator_prompt_path=date_separator_prompt_path,
                            ),
                            system_prompt=system_prompt_content,
                        )
                    )
            except Exception as exc:
                logger.warning(
                    "memory update prompt render failed: trigger=%s kind=%s error=%s",
                    trigger,
                    round_kind,
                    exc,
                )
                return {"success": False, "error": str(exc), "round": round_kind}
            round_state: Dict[str, Any] = {
                "messages": round_messages,
                "active_node": "main",
                "loops": 0,
            }
            if prompt_content:
                round_state["messages"].append(
                    {"role": "user", "content": prompt_content}
                )
            # 每一轮都从同一份 base_update_messages 起步，避免 date-memory 看见
            # date-session-memory 那一轮的 prompt/tool/result，污染原始会话上下文。
            if round_kind == "date_memory":
                with _date_memory_update_lock(config=config, state=state):
                    update_agent.run(round_state)
            else:
                update_agent.run(round_state)
            for round_item in prompt_rounds:
                if round_item.get("kind") == round_kind:
                    round_item["status"] = "succeeded"
                    break
            update_messages.extend(deepcopy(round_state.get("messages") or []))
            logger.info(
                "memory update round completed: trigger=%s kind=%s isolated_message_count=%s",
                trigger,
                round_kind,
                len(round_state.get("messages") or []),
            )
    record = _append_memory_update_record(
        state,
        trigger=trigger,
        date=date,
        memory_update_time=update_time,
        prompt_rounds=prompt_rounds,
        update_messages=update_messages,
    )
    projection_node = _append_memory_update_projection(
        state,
        record=record,
        trigger=trigger,
        date=date,
        memory_update_time=update_time,
        prompt_rounds=prompt_rounds,
        update_messages=update_messages,
    )
    try:
        _checkpoint_memory_update(
            state,
            trigger=trigger,
            date=date,
            memory_update_time=update_time,
            record=record,
            prompt_rounds=prompt_rounds,
        )
    except Exception as exc:
        logger.warning("memory update checkpoint failed: %s", exc)
    if "message_records" in state:
        rebuild_compiled_messages(state)
    logger.info(
        "memory update completed: trigger=%s record_id=%s node_id=%s",
        trigger,
        record.get("id") if isinstance(record, dict) else None,
        projection_node.get("id"),
    )
    return {
        "success": True,
        "trigger": trigger,
        "date": date,
        "memory_update_time": update_time.isoformat(timespec="seconds"),
        "record_id": record.get("id") if isinstance(record, dict) else None,
        "node_id": projection_node.get("id"),
        "rounds": deepcopy(prompt_rounds),
    }
