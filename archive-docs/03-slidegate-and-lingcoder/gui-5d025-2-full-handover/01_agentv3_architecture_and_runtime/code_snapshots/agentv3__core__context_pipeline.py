import json
import logging
import os
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader

from agents.agentv3.context_layers import (
    extract_knowledge_base_refs,
    normalize_active_editor_file,
)
from agents.agentv3.core.runtime_components import resolve_case_deep_research_enabled
from backend.replay_runtime import checkpoint_runtime_state, record_runtime_event
from backend.sandbox_storage import get_conversation_input_dir
from src.base_llm import BaseLLM
from src.conversation_state_v3 import (
    add_system_context,
    add_user_input,
    find_pending_ask_user_record_for_resume,
    attach_shared_layers,
    clear_waiting_for_user_input,
    ensure_conversation_state,
    extract_persistable_state,
    rebuild_compiled_messages,
    register_file_asset,
    register_parsed_artifact,
    set_active_editor_projection,
    set_conversation_status,
    set_todolist_projection,
    update_language_profile,
)
from src.utils import ctx
from src.utils.cancellation import ensure_not_cancelled
from tools.multimodal_file.read_tool import read
from tools.search import memory_search_tool


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
try:
    _PRE_RUN_STATE_LOG_MAX_CHARS = max(0, int(os.getenv("PRE_RUN_STATE_LOG_MAX_CHARS", "4000")))
except ValueError:
    _PRE_RUN_STATE_LOG_MAX_CHARS = 4000
_PRE_RUN_STATE_LOG_RECENT_RECORDS = 5
_TOKEN_ENCODER = None
_TOKEN_ENCODER_READY = False
_DEFAULT_DATE_MEMORY_MAX_TOKENS = 2000
_DATE_MEMORY_TRUNCATED_SUFFIX_TEMPLATE = "...[内容已截断] 完整内容查看: {content_path}"
_RETRIEVED_CONTEXT_SEARCH_RESULT_MAX_CHARS = 12000
_RETRIEVED_CONTEXT_PREFETCH_EXECUTOR = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="retrieved-context-prefetch",
)


def get_long_term_memory_fingerprint(**kwargs: Any) -> str:
    """兼容旧测试/旧调用：记忆能力已禁用，始终返回空指纹。"""
    return ""


def get_jobs_config(conf: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """兼容旧测试/旧调用：summary jobs 已禁用。"""
    return {"enabled": False}


def build_system_prompt_with_memory(
    base_prompt: str,
    config: Optional[Dict[str, Any]],
    query: Optional[str],
    session_id: Optional[str],
    memory_user_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> str:
    """兼容旧测试/旧调用：保留原接口，但不再注入任何记忆内容。"""
    return base_prompt or ""


def _normalize_prompt_language(language: Optional[str]) -> Optional[str]:
    if not language:
        return None
    value = str(language).strip().lower()
    if value.startswith("zh"):
        return "zh"
    if value.startswith("en"):
        return "en"
    return value or None


def _resolve_date_memory_prompt_path(
    runtime_conf: Optional[Dict[str, Any]],
    *,
    zh_path: str,
    en_path: str,
) -> Path:
    runtime_conf = runtime_conf or {}
    lang = _normalize_prompt_language(runtime_conf.get("language"))

    if lang == "zh" and runtime_conf.get("date_memory_prompt_zh"):
        return Path(str(runtime_conf["date_memory_prompt_zh"]))
    if lang == "en" and runtime_conf.get("date_memory_prompt_en"):
        return Path(str(runtime_conf["date_memory_prompt_en"]))

    prompt_value = runtime_conf.get("date_memory_prompt")
    if isinstance(prompt_value, dict):
        if lang and prompt_value.get(lang):
            return Path(str(prompt_value[lang]))
        if prompt_value.get("default"):
            return Path(str(prompt_value["default"]))
    elif isinstance(prompt_value, str) and prompt_value.strip() and prompt_value.strip().lower() != "auto":
        return Path(prompt_value)

    return Path(zh_path if lang == "zh" else en_path)


def _safe_positive_int(value: Any, default: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, 0)


def _safe_int(value: Any, default: int) -> int:
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except Exception:
        return default


def _config_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if not normalized:
        return default
    return normalized in {"1", "true", "yes", "on", "enabled", "enable"}


def _count_text_tokens(text: str) -> int:
    raw = str(text or "")
    if not raw:
        return 0

    global _TOKEN_ENCODER
    global _TOKEN_ENCODER_READY
    if not _TOKEN_ENCODER_READY:
        try:
            import tiktoken  # type: ignore
            _TOKEN_ENCODER = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _TOKEN_ENCODER = None
        _TOKEN_ENCODER_READY = True

    if _TOKEN_ENCODER is not None:
        try:
            return len(_TOKEN_ENCODER.encode(raw))
        except Exception:
            pass
    return max(1, len(raw) // 4)


def _clip_text_to_token_budget(text: str, max_tokens: int) -> str:
    raw = str(text or "")
    if not raw or max_tokens <= 0:
        return raw

    if _count_text_tokens(raw) <= max_tokens:
        return raw

    low = 0
    high = len(raw)
    while low < high:
        mid = (low + high + 1) // 2
        if _count_text_tokens(raw[:mid]) <= max_tokens:
            low = mid
        else:
            high = mid - 1
    return raw[:low].rstrip()


def _clip_date_memory_content(content: str, content_path: str, max_tokens: Optional[int] = None) -> str:
    token_budget = _safe_int(max_tokens, _DEFAULT_DATE_MEMORY_MAX_TOKENS)
    if token_budget <= 0:
        return content

    if _count_text_tokens(content) <= token_budget:
        return content

    clipped_content = _clip_text_to_token_budget(content, token_budget)
    truncated_suffix = _DATE_MEMORY_TRUNCATED_SUFFIX_TEMPLATE.format(
        content_path=content_path
    )
    return f"{clipped_content}{truncated_suffix}"


def _join_read_tool_path(directory: str, filename: str) -> str:
    base = str(directory or "").strip().rstrip("/")
    if not base:
        return filename
    path = f"{base}/{filename}"
    if base.startswith(("local:", "knowledge:", "memory:")):
        return path
    return f"local:{path}"


def _build_date_memory_list(config: Optional[Dict[str, Any]]) -> List[str]:
    config = config or {}
    memory_cfg = config.get("memory", {}) or {}
    if not isinstance(memory_cfg, dict):
        return []

    date_memory_dir = str(memory_cfg.get("date_memory_dir") or "memory://date-memory/").strip()
    if not date_memory_dir:
        return []

    load_days = _safe_positive_int(memory_cfg.get("date_memory_load_days"), default=0)
    if load_days <= 0:
        return []
    max_tokens = _safe_int(memory_cfg.get("date_memory_max_token"), _DEFAULT_DATE_MEMORY_MAX_TOKENS)

    today = datetime.now().date()
    date_memory_list: List[str] = []
    for offset in range(load_days):
        date_text = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
        file_path = _join_read_tool_path(date_memory_dir, f"{date_text}.md")
        result = read(file_path, state=None, config=config)
        if not isinstance(result, dict) or not result.get("success"):
            logger.debug(
                "date-memory file read skipped: %s (%s)",
                file_path,
                result.get("error") if isinstance(result, dict) else "invalid read result",
            )
            continue
        content = str(result.get("content") or "").strip()
        if content:
            date_memory_list.append(_clip_date_memory_content(content, file_path, max_tokens))
    return date_memory_list[::-1]


def _render_date_memory_prompt_from_config(
    config: Optional[Dict[str, Any]],
    template_path: str,
    *,
    state_var_overrides: Optional[Dict[str, Any]] = None,
) -> str:
    config = config or {}
    date_memory_list = _build_date_memory_list(config)
    date_memory_block = "\n\n".join(date_memory_list) if date_memory_list else ""
    state_vars = {
        "CURRENT_TIME": datetime.now().strftime("%Y-%m-%d"),
        "DATE_MEMORY_BLOCK": date_memory_block
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
    return template.render(**state_vars)


def _build_preloaded_context_messages(
    *,
    config: Optional[Dict[str, Any]] = None,
    runtime_conf: Optional[Dict[str, Any]] = None,
    runtime_lang: Optional[str] = None,
) -> List[Dict[str, Any]]:
    prompt_runtime_conf = dict(runtime_conf or {}) if isinstance(runtime_conf, dict) else {}
    prompt_runtime_conf["language"] = _normalize_prompt_language(
        runtime_lang or prompt_runtime_conf.get("language")
    )
    date_memory_prompt_path = _resolve_date_memory_prompt_path(
        prompt_runtime_conf,
        zh_path="agents/agentv3/date_memory_prompt_zh.md",
        en_path="agents/agentv3/date_memory_prompt_en.md",
    )
    if not date_memory_prompt_path.is_absolute():
        date_memory_prompt_path = PROJECT_ROOT / date_memory_prompt_path
    render_config = dict(config or {}) if isinstance(config, dict) else {}
    render_runtime_conf = dict(render_config.get("runtime") or {}) if isinstance(render_config.get("runtime"), dict) else {}
    render_runtime_conf.update(prompt_runtime_conf)
    render_config["runtime"] = render_runtime_conf
    try:
        content = _render_date_memory_prompt_from_config(
            config=render_config,
            template_path=str(date_memory_prompt_path),
        ).strip()
    except FileNotFoundError:
        logger.warning("date-memory preloaded context template not found: %s", date_memory_prompt_path)
        return []
    except Exception as exc:
        logger.warning("date-memory preloaded context template render failed: %s", exc)
        return []

    if not content:
        return []

    return [
        {
            "id": "preloaded_context",
            "content": content,
        }
    ]


def _attach_preloaded_context_messages(
    state: Dict[str, Any],
    *,
    config: Optional[Dict[str, Any]] = None,
    runtime_conf: Optional[Dict[str, Any]] = None,
    runtime_lang: Optional[str] = None,
) -> None:
    preloaded_context_messages = _build_preloaded_context_messages(
        config=config,
        runtime_conf=runtime_conf,
        runtime_lang=runtime_lang,
    )
    if not preloaded_context_messages:
        state.pop("preloaded_context_messages", None)
        main_state = state.get("main_state")
        if isinstance(main_state, dict):
            main_state.pop("preloaded_context_messages", None)
        return

    state["preloaded_context_messages"] = preloaded_context_messages
    main_state = state.get("main_state")
    if isinstance(main_state, dict):
        main_state["preloaded_context_messages"] = preloaded_context_messages


def _retrieved_context_enabled(config: Optional[Dict[str, Any]]) -> bool:
    memory_cfg = (config or {}).get("memory")
    if not isinstance(memory_cfg, dict):
        return False
    if not _config_bool(memory_cfg.get("enabled", memory_cfg.get("enable")), default=False):
        return False

    retrieved_cfg = memory_cfg.get("retrieved_context")
    if isinstance(retrieved_cfg, dict):
        return _config_bool(
            retrieved_cfg.get("enabled", retrieved_cfg.get("enable")),
            default=True,
        )
    return _config_bool(retrieved_cfg, default=True)


def _retrieved_context_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    memory_cfg = (config or {}).get("memory")
    if not isinstance(memory_cfg, dict):
        return {}
    retrieved_cfg = memory_cfg.get("retrieved_context")
    return retrieved_cfg if isinstance(retrieved_cfg, dict) else {}


def _retrieved_context_async_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    retrieved_cfg = _retrieved_context_config(config)
    async_cfg = retrieved_cfg.get("async")
    return async_cfg if isinstance(async_cfg, dict) else {}


def _retrieved_context_async_enabled(config: Optional[Dict[str, Any]]) -> bool:
    retrieved_cfg = _retrieved_context_config(config)
    async_cfg = retrieved_cfg.get("async")
    if isinstance(async_cfg, dict):
        return _config_bool(
            async_cfg.get("enabled", async_cfg.get("enable")),
            default=True,
        )
    return _config_bool(async_cfg, default=True)


def _resolve_retrieved_context_async_wait_timeout(config: Optional[Dict[str, Any]]) -> Optional[float]:
    async_cfg = _retrieved_context_async_config(config)
    if "wait_timeout_seconds" not in async_cfg or async_cfg.get("wait_timeout_seconds") is None:
        return None
    try:
        return max(0.0, float(async_cfg.get("wait_timeout_seconds")))
    except (TypeError, ValueError):
        return None


def _retrieved_context_llm_summary_enabled(config: Optional[Dict[str, Any]]) -> bool:
    retrieved_cfg = _retrieved_context_config(config)
    llm_summary_cfg = retrieved_cfg.get("llm_summary")
    if isinstance(llm_summary_cfg, dict):
        return _config_bool(
            llm_summary_cfg.get("enabled", llm_summary_cfg.get("enable")),
            default=True,
        )
    return _config_bool(llm_summary_cfg, default=True)


def _retrieved_context_llm_summary_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    retrieved_cfg = _retrieved_context_config(config)
    llm_summary_cfg = retrieved_cfg.get("llm_summary")
    return llm_summary_cfg if isinstance(llm_summary_cfg, dict) else {}


def _retrieved_context_llm_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    llm_summary_cfg = _retrieved_context_llm_summary_config(config)
    llm_cfg = llm_summary_cfg.get("llm")
    return llm_cfg if isinstance(llm_cfg, dict) else {}


def _llm_provider_kwargs_from_config(config: Dict[str, Any]) -> Dict[str, Any]:
    provider = str(config.get("provider") or "").strip().lower()
    kwargs: Dict[str, Any] = {}
    if provider == "anthropic":
        for key in ("thinking", "output_config"):
            value = config.get(key)
            if value is not None:
                kwargs[key] = value
    else:
        extra_body = config.get("extra_body")
        if extra_body is not None:
            kwargs["extra_body"] = extra_body
    return kwargs


def _retrieved_context_llm_summary_validation_available(config: Optional[Dict[str, Any]]) -> Optional[bool]:
    llm_summary_cfg = _retrieved_context_llm_summary_config(config)
    validation = llm_summary_cfg.get("validation")
    if not isinstance(validation, dict) or not validation.get("checked"):
        return None
    return bool(validation.get("available"))


def _iter_retrieved_context_summary_llms(
    *,
    config: Optional[Dict[str, Any]],
    default_llm: Any,
) -> List[Any]:
    llms: List[Any] = []
    llm_summary_cfg = _retrieved_context_llm_summary_config(config)
    llm_cfg = _retrieved_context_llm_config(config)
    has_custom_llm_config = any(
        llm_cfg.get(key) not in (None, "")
        for key in ("model", "api_key", "base_url")
    )
    validation_available = _retrieved_context_llm_summary_validation_available(config)

    if has_custom_llm_config and validation_available is not False:
        model = llm_cfg.get("model")
        api_key = llm_cfg.get("api_key")
        base_url = llm_cfg.get("base_url")
        if model and api_key and base_url:
            try:
                llms.append(
                    BaseLLM(
                        model=model,
                        api_key=api_key,
                        base_url=base_url,
                        provider=llm_cfg.get("provider", "openai"),
                        temperature=llm_cfg.get("temperature", 0.7),
                        max_tokens=llm_cfg.get("max_tokens", 4096),
                        debug_raw_response=llm_cfg.get("debug_raw_response"),
                        **_llm_provider_kwargs_from_config(llm_cfg),
                    )
                )
            except Exception as exc:
                logger.warning("retrieved context llm_summary LLM creation failed; fallback to default LLM: %s", exc)
        elif validation_available is not False:
            logger.warning(
                "retrieved context llm_summary config incomplete; fallback to default LLM "
                "(requires model/api_key/base_url)"
            )

    if default_llm is not None:
        llms.append(default_llm)
    return llms


def _resolve_retrieved_context_score_filter(config: Optional[Dict[str, Any]]) -> Tuple[float, int]:
    retrieved_cfg = _retrieved_context_config(config)
    score_filter_cfg = retrieved_cfg.get("score_filter")
    if not isinstance(score_filter_cfg, dict):
        score_filter_cfg = {}
    try:
        threshold = float(score_filter_cfg.get("threshold", 0.0))
    except (TypeError, ValueError):
        threshold = 0.0
    top_k = _safe_positive_int(score_filter_cfg.get("top_k"), default=6)
    return threshold, top_k


def _extract_retrieved_context_items(search_result: Dict[str, Any]) -> List[Any]:
    for key in ("result", "results"):
        value = search_result.get(key)
        if isinstance(value, list):
            return value
    return []


def _coerce_score(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_retrieved_context_items_without_llm(
    items: List[Any],
    *,
    config: Optional[Dict[str, Any]],
    runtime_lang: Optional[str],
) -> str:
    threshold, top_k = _resolve_retrieved_context_score_filter(config)
    if top_k <= 0:
        return ""

    selected_contents: List[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        score = _coerce_score(item.get("score"))
        if score is None or score <= threshold:
            continue
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        selected_contents.append(content)
        if len(selected_contents) >= top_k:
            break

    if not selected_contents:
        return ""

    is_zh = str(runtime_lang or "").lower().startswith("zh")
    lines = ["以下为筛选后的检索内容：" if is_zh else "Filtered retrieved content:"]
    for index, content in enumerate(selected_contents, start=1):
        title = f"内容 {index}" if is_zh else f"Content {index}"
        lines.append(f"\n## {title}")
        lines.append(content)
    return "\n".join(lines).strip()


def _serialize_search_result_for_retrieved_context(result: Dict[str, Any]) -> str:
    try:
        serialized = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    except Exception:
        serialized = str(result)
    if len(serialized) <= _RETRIEVED_CONTEXT_SEARCH_RESULT_MAX_CHARS:
        return serialized
    return serialized[:_RETRIEVED_CONTEXT_SEARCH_RESULT_MAX_CHARS].rstrip() + "\n...[truncated]"


def _summarize_retrieved_context_result(
    *,
    query: str,
    search_result: Dict[str, Any],
    llm: Any,
    runtime_lang: Optional[str],
) -> str:
    if llm is None or not callable(getattr(llm, "completion", None)):
        logger.warning("retrieved context skipped: no LLM available for search-result summarization")
        return ""

    is_zh = str(runtime_lang or "").lower().startswith("zh")
    serialized_result = _serialize_search_result_for_retrieved_context(search_result)
    if is_zh:
        system_prompt = (
            "你是检索结果整理器。你的任务是从 resource_search 返回结果中提取对回答用户问题有帮助的内容。"
            "只输出相关检索结果摘要，使用简洁 Markdown；不要编造，不要输出无关结果。"
            "如果没有任何有用内容，输出空字符串。"
        )
        user_prompt = (
            f"用户问题：\n{query}\n\n"
            f"resource_search 返回结果：\n```json\n{serialized_result}\n```\n\n"
            "请输出能帮助回答用户问题的相关检索结果。"
        )
    else:
        system_prompt = (
            "You organize resource_search results. Extract only information that helps answer the user's query. "
            "Return concise Markdown, do not invent facts, and omit irrelevant results. "
            "If nothing is useful, return an empty string."
        )
        user_prompt = (
            f"User query:\n{query}\n\n"
            f"resource_search result:\n```json\n{serialized_result}\n```\n\n"
            "Return the relevant retrieved results that can help answer the query."
        )

    try:
        ensure_not_cancelled()
        response = llm.completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            tools=None,
            tool_choice="none",
        )
        ensure_not_cancelled()
    except Exception as exc:
        logger.warning("retrieved context summarization failed: %s", exc)
        return ""

    return str((response or {}).get("content") or "").strip()


def _resolve_retrieved_context_prompt_path(
    runtime_conf: Optional[Dict[str, Any]],
    *,
    zh_path: str,
    en_path: str,
) -> Path:
    runtime_conf = runtime_conf or {}
    lang = _normalize_prompt_language(runtime_conf.get("language"))
    memory_cfg = runtime_conf.get("memory")
    retrieved_cfg = {}
    if isinstance(memory_cfg, dict) and isinstance(memory_cfg.get("retrieved_context"), dict):
        retrieved_cfg = memory_cfg.get("retrieved_context") or {}

    if lang == "zh" and retrieved_cfg.get("prompt_zh"):
        return Path(str(retrieved_cfg["prompt_zh"]))
    if lang == "en" and retrieved_cfg.get("prompt_en"):
        return Path(str(retrieved_cfg["prompt_en"]))
    return Path(zh_path if lang == "zh" else en_path)


def _render_retrieved_context_prompt_from_config(
    *,
    config: Optional[Dict[str, Any]],
    template_path: str,
    query: str,
    retrieved_context_block: str,
    search_result: Dict[str, Any],
) -> str:
    state_vars = {
        "CURRENT_TIME": datetime.now().strftime("%Y-%m-%d"),
        "QUERY": query,
        "USER_QUERY": query,
        "RETRIEVED_CONTEXT_BLOCK": retrieved_context_block,
        "RESOURCE_SEARCH_RESULT": _serialize_search_result_for_retrieved_context(search_result),
    }

    template_file = Path(template_path)
    if not template_file.is_absolute():
        template_file = PROJECT_ROOT / template_file
    if not template_file.is_file():
        raise FileNotFoundError(str(template_file))

    env = Environment(loader=FileSystemLoader(str(template_file.parent)))
    template = env.get_template(template_file.name)
    return template.render(**state_vars)


def _build_retrieved_context_messages_from_search_result(
    *,
    config: Optional[Dict[str, Any]] = None,
    runtime_conf: Optional[Dict[str, Any]] = None,
    runtime_lang: Optional[str] = None,
    query: Optional[str] = None,
    llm: Any = None,
    search_result: Optional[Dict[str, Any]] = None,
    force_score_filter: bool = False,
) -> List[Dict[str, Any]]:
    normalized_query = str(query or "").strip()
    if not normalized_query or not isinstance(search_result, dict):
        return []
    result_items = _extract_retrieved_context_items(search_result)
    if not search_result.get("success") or not result_items:
        return []
    llm_summary_enabled = _retrieved_context_llm_summary_enabled(config) and not force_score_filter
    logger.info(
        "retrieved context resource_search succeeded: lang=%s items=%s llm_summary_enabled=%s",
        runtime_lang or "",
        len(result_items),
        llm_summary_enabled,
    )

    if llm_summary_enabled:
        summary = ""
        for summary_llm in _iter_retrieved_context_summary_llms(
            config=config,
            default_llm=llm,
        ):
            summary = _summarize_retrieved_context_result(
                query=normalized_query,
                search_result=search_result,
                llm=summary_llm,
                runtime_lang=runtime_lang,
            )
            if summary:
                break
        if not summary:
            summary = _format_retrieved_context_items_without_llm(
                result_items,
                config=config,
                runtime_lang=runtime_lang,
            )
    else:
        summary = _format_retrieved_context_items_without_llm(
            result_items,
            config=config,
            runtime_lang=runtime_lang,
        )
    if not summary:
        return []

    prompt_runtime_conf = dict(runtime_conf or {}) if isinstance(runtime_conf, dict) else {}
    prompt_runtime_conf["language"] = _normalize_prompt_language(
        runtime_lang or prompt_runtime_conf.get("language")
    )
    prompt_runtime_conf["memory"] = (config or {}).get("memory") if isinstance(config, dict) else {}
    template_path = _resolve_retrieved_context_prompt_path(
        prompt_runtime_conf,
        zh_path="agents/agentv3/retrieved_context_zh.md",
        en_path="agents/agentv3/retrieved_context_en.md",
    )
    try:
        content = _render_retrieved_context_prompt_from_config(
            config=config,
            template_path=str(template_path),
            query=normalized_query,
            retrieved_context_block=summary,
            search_result=search_result,
        ).strip()
    except FileNotFoundError:
        logger.warning("retrieved context template not found: %s", template_path)
        return []
    except Exception as exc:
        logger.warning("retrieved context template render failed: %s", exc)
        return []

    if not content:
        return []
    logger.info(
        "retrieved context message rendered: lang=%s summary_chars=%s content_chars=%s",
        runtime_lang or "",
        len(summary),
        len(content),
    )
    return [
        {
            "id": "retrieved_context",
            "content": content,
        }
    ]


def _build_retrieved_context_messages(
    *,
    config: Optional[Dict[str, Any]] = None,
    runtime_conf: Optional[Dict[str, Any]] = None,
    runtime_lang: Optional[str] = None,
    query: Optional[str] = None,
    state: Optional[Dict[str, Any]] = None,
    llm: Any = None,
    force_score_filter: bool = False,
    prefetch_holder: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    normalized_query = str(query or "").strip()
    if not normalized_query or not _retrieved_context_enabled(config):
        return []

    try:
        ensure_not_cancelled()
        if str(runtime_lang or "").lower().startswith("zh"):
            search_result = memory_search_tool.search_zh(
                query=normalized_query,
                config=config,
                state=state,
            )
        else:
            search_result = memory_search_tool.search(
                query=normalized_query,
                config=config,
                state=state,
            )
    except Exception as exc:
        logger.warning("retrieved context resource_search failed: %s", exc)
        return []

    if not isinstance(search_result, dict):
        search_result = {"success": True, "query": normalized_query, "results": search_result}
    if isinstance(prefetch_holder, dict):
        prefetch_holder["search_result"] = search_result
    return _build_retrieved_context_messages_from_search_result(
        config=config,
        runtime_conf=runtime_conf,
        runtime_lang=runtime_lang,
        query=normalized_query,
        llm=llm,
        search_result=search_result,
        force_score_filter=force_score_filter,
    )


def start_retrieved_context_prefetch(
    *,
    config: Optional[Dict[str, Any]] = None,
    runtime_conf: Optional[Dict[str, Any]] = None,
    runtime_lang: Optional[str] = None,
    query: Optional[str] = None,
    llm: Any = None,
) -> Optional[Any]:
    normalized_query = str(query or "").strip()
    if not normalized_query or not _retrieved_context_enabled(config):
        return None
    if not _retrieved_context_async_enabled(config):
        return None

    logger.info(
        "retrieved context async prefetch started: lang=%s query_chars=%s",
        runtime_lang or "",
        len(normalized_query),
    )
    prefetch_holder: Dict[str, Any] = {}
    future = _RETRIEVED_CONTEXT_PREFETCH_EXECUTOR.submit(
        _build_retrieved_context_messages,
        config=config,
        runtime_conf=runtime_conf,
        runtime_lang=runtime_lang,
        query=normalized_query,
        state=None,
        llm=llm,
        prefetch_holder=prefetch_holder,
    )
    try:
        setattr(future, "_retrieved_context_prefetch_holder", prefetch_holder)
    except Exception:
        pass
    return future


def _retrieved_context_prefetched_search_result(prefetch_future: Any) -> Optional[Dict[str, Any]]:
    holder = getattr(prefetch_future, "_retrieved_context_prefetch_holder", None)
    if not isinstance(holder, dict):
        return None
    search_result = holder.get("search_result")
    return search_result if isinstance(search_result, dict) else None


def _resolve_retrieved_context_prefetch_messages(
    *,
    config: Optional[Dict[str, Any]],
    prefetch_future: Any,
    runtime_conf: Optional[Dict[str, Any]] = None,
    runtime_lang: Optional[str] = None,
    query: Optional[str] = None,
    state: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    timeout = _resolve_retrieved_context_async_wait_timeout(config)
    try:
        result = prefetch_future.result(timeout=timeout)
    except TimeoutError:
        logger.warning(
            "retrieved context prefetch timed out after %s seconds; falling back to score_filter",
            timeout,
        )
        search_result = _retrieved_context_prefetched_search_result(prefetch_future)
        if search_result is None:
            logger.warning(
                "retrieved context score_filter fallback skipped: prefetched search_result is not ready"
            )
            return []
        return _build_retrieved_context_messages_from_search_result(
            config=config,
            runtime_conf=runtime_conf,
            runtime_lang=runtime_lang,
            query=query,
            llm=None,
            search_result=search_result,
            force_score_filter=True,
        )
    except Exception as exc:
        logger.warning("retrieved context prefetch failed; skipping this turn: %s", exc)
        return []

    if not isinstance(result, list):
        return []
    messages = [message for message in result if isinstance(message, dict)]
    logger.info(
        "retrieved context async prefetch completed: messages=%s timeout=%s",
        len(messages),
        timeout,
    )
    return messages


def _attach_retrieved_context_messages(
    state: Dict[str, Any],
    *,
    config: Optional[Dict[str, Any]] = None,
    runtime_conf: Optional[Dict[str, Any]] = None,
    runtime_lang: Optional[str] = None,
    query: Optional[str] = None,
    llm: Any = None,
    prefetch_future: Any = None,
) -> None:
    if prefetch_future is not None:
        retrieved_context_messages = _resolve_retrieved_context_prefetch_messages(
            config=config,
            prefetch_future=prefetch_future,
            runtime_conf=runtime_conf,
            runtime_lang=runtime_lang,
            query=query,
            state=state,
        )
    else:
        logger.info(
            "retrieved context sync build started: lang=%s query_chars=%s",
            runtime_lang or "",
            len(str(query or "").strip()),
        )
        retrieved_context_messages = _build_retrieved_context_messages(
            config=config,
            runtime_conf=runtime_conf,
            runtime_lang=runtime_lang,
            query=query,
            state=state,
            llm=llm,
        )
    if not retrieved_context_messages:
        state.pop("retrieved_context_messages", None)
        main_state = state.get("main_state")
        if isinstance(main_state, dict):
            main_state.pop("retrieved_context_messages", None)
        return

    state["retrieved_context_messages"] = retrieved_context_messages
    main_state = state.get("main_state")
    if isinstance(main_state, dict):
        main_state["retrieved_context_messages"] = retrieved_context_messages


def _resolve_existing_local_file_paths(
    local_file_path: Optional[Any],
    *,
    file_dir: Optional[str],
) -> List[str]:
    if not local_file_path:
        return []

    raw_paths = local_file_path if isinstance(local_file_path, list) else [local_file_path]
    resolved: List[str] = []
    seen: set[str] = set()

    for local_path in raw_paths:
        norm_local = unicodedata.normalize("NFC", str(local_path)).strip()
        if not norm_local:
            continue

        if os.path.isabs(norm_local):
            file_path = norm_local
        elif file_dir:
            if os.path.normpath(str(norm_local)).startswith(os.path.normpath(str(file_dir))):
                file_path = norm_local
            else:
                file_path = os.path.join(file_dir, norm_local)
        else:
            file_path = os.path.join(os.getcwd(), norm_local)

        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"文件不存在: {norm_local}")

        key = os.path.normcase(abs_path)
        if key in seen:
            continue
        seen.add(key)
        resolved.append(abs_path)

    return resolved


def _collect_conversation_uploaded_files(conversation_id: str) -> List[str]:
    cid = str(conversation_id or "").strip()
    if not cid:
        return []

    input_dir = get_conversation_input_dir(PROJECT_ROOT, cid)
    if not input_dir.exists() or not input_dir.is_dir():
        return []

    files = sorted(path for path in input_dir.rglob("*") if path.is_file())
    return [os.path.abspath(str(path)) for path in files]


def _sandbox_root_for_manager(sandbox_manager: Any) -> str:
    return str(getattr(sandbox_manager, "absolute_sandbox_path", None) or "/mnt/data").rstrip("/")


def _upload_local_path_to_sandbox(
    *,
    sandbox_manager: Any,
    session_id: str,
    file_path: str,
) -> tuple[str, List[str]]:
    path = Path(file_path)
    if path.is_dir():
        base_name = path.name
        sandbox_dir = f"{_sandbox_root_for_manager(sandbox_manager)}/{base_name}"
        uploaded_files: List[str] = []
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            relative = child.relative_to(path).as_posix()
            sandbox_relative_name = f"{base_name}/{relative}"
            with child.open("rb") as file_obj:
                sandbox_file_path = sandbox_manager.put_file(
                    session_id=session_id,
                    filename=sandbox_relative_name,
                    data=file_obj.read(),
                )
            uploaded_files.append(sandbox_file_path)
        return sandbox_dir, uploaded_files

    filename = os.path.basename(file_path)
    with open(file_path, "rb") as file_obj:
        sandbox_file_path = sandbox_manager.put_file(
            session_id=session_id,
            filename=filename,
            data=file_obj.read(),
        )
    return sandbox_file_path, [sandbox_file_path]


def _summarize_context_text(text: str, *, max_chars: int = 100) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return f"{cleaned[:max_chars].rstrip()}..."


def _summarize_persisted_state_for_log(persisted: Dict[str, Any]) -> Dict[str, Any]:
    records = persisted.get("message_records") or []
    asset_index = persisted.get("asset_index") or {}
    runtime = persisted.get("runtime_control") or {}
    metadata = persisted.get("session_metadata") or {}

    latest_user_input = next(
        (
            record for record in reversed(records)
            if record.get("type") == "user_input" and str(record.get("text") or "").strip()
        ),
        None,
    )
    latest_system_context = next(
        (
            record for record in reversed(records)
            if record.get("type") == "system_context" and str(record.get("text") or "").strip()
        ),
        None,
    )

    summary = {
        "conversation_id": persisted.get("conversation_id"),
        "message_records": len(records),
        "recent_record_types": [
            str(record.get("type") or "unknown")
            for record in records[-_PRE_RUN_STATE_LOG_RECENT_RECORDS:]
        ],
        "files": len(asset_index.get("files") or []),
        "parsed_artifacts": len(asset_index.get("parsed_artifacts") or []),
        "todolist": len(persisted.get("todolist") or []),
        "conversation_status": runtime.get("conversation_status"),
        "prompt_locale": runtime.get("current_prompt_locale"),
        "deep_research_enabled": metadata.get("deep_research_enabled"),
        "title": metadata.get("conversation_title"),
    }
    if latest_user_input:
        summary["latest_user_input"] = _summarize_context_text(
            latest_user_input.get("text", ""),
            max_chars=120,
        )
    if latest_system_context:
        summary["latest_system_context"] = _summarize_context_text(
            latest_system_context.get("text", ""),
            max_chars=120,
        )
    return summary


def _serialize_pre_run_state_for_log(
    state: Dict[str, Any],
    *,
    max_chars: Optional[int] = None,
) -> Tuple[str, bool]:
    persisted = extract_persistable_state(state)
    serialized = json.dumps(persisted, ensure_ascii=False, default=str)
    resolved_max_chars = _PRE_RUN_STATE_LOG_MAX_CHARS if max_chars is None else max(0, int(max_chars))
    if resolved_max_chars > 0 and len(serialized) <= resolved_max_chars:
        return serialized, False

    summary = _summarize_persisted_state_for_log(persisted)
    summary["full_state_chars"] = len(serialized)
    summary["full_state_omitted"] = True
    summary["log_max_chars"] = resolved_max_chars
    return json.dumps(summary, ensure_ascii=False, default=str), True


def _build_file_preview_from_parsed_text(
    file_name: str,
    parsed_text: str,
    *,
    max_chars: int = 1200,
) -> Tuple[Optional[Dict[str, Any]], str]:
    raw = str(parsed_text or "").strip()
    if not raw:
        return None, "text"

    lower_name = str(file_name or "").lower()
    if lower_name.endswith((".xlsx", ".xls", ".csv")) or raw.startswith(("Table summary:", "表格摘要:")):
        description = re.sub(r"^(Table summary:|表格摘要:)\s*", "", raw).strip()
        if description:
            return {"description": description}, "table"
        return None, "table"

    compact = re.sub(r"[ \t]+\n", "\n", raw)
    compact = re.sub(r"\n{3,}", "\n\n", compact)
    preview_text = compact if len(compact) <= max_chars else compact[:max_chars].rstrip() + "......"
    preview: Dict[str, Any] = {
        "text": preview_text,
        "is_full": len(compact) <= max_chars,
    }
    if len(compact) > max_chars:
        preview["total_length"] = len(compact)
    return preview, "text"


def _best_effort_parse_files_for_context(
    sandbox_paths: List[str],
    *,
    conf: Dict[str, Any],
    runtime_lang: Optional[str],
) -> List[Dict[str, Any]]:
    parser_conf = (conf.get("tools", {}) or {}).get("document_parser", {}) or {}
    if not parser_conf.get("enabled"):
        return []

    try:
        from tools.multimodal_file.document_parser import document_parser, document_parser_zh
    except Exception as exc:
        logger.warning("document_parser import failed: %s", exc)
        return []

    parser_fn = document_parser_zh if str(runtime_lang or "").lower().startswith("zh") else document_parser
    parser_tool_conf = parser_conf.get("config", {}) or {}
    summaries: List[Dict[str, Any]] = []
    for sandbox_path in sandbox_paths:
        file_name = os.path.basename(sandbox_path)
        try:
            parsed_text = parser_fn(file_path=sandbox_path, config=deepcopy(parser_tool_conf))
            parsed_path_match = re.search(r"/mnt/data/[^\s\]]+\.md", str(parsed_text))
            parsed_path = parsed_path_match.group(0) if parsed_path_match else None
            preview, content_kind = _build_file_preview_from_parsed_text(file_name, str(parsed_text))
            summaries.append(
                {
                    "name": file_name,
                    "path": sandbox_path,
                    "summary": _summarize_context_text(parsed_text, max_chars=100),
                    "parsed_path": parsed_path,
                    "preview": preview,
                    "content_kind": content_kind,
                    "status": "parsed",
                }
            )
        except Exception as exc:
            summaries.append(
                {
                    "name": file_name,
                    "path": sandbox_path,
                    "summary": _summarize_context_text(str(exc), max_chars=100),
                    "preview": _build_file_preview_from_parsed_text(file_name, str(exc), max_chars=400)[0],
                    "content_kind": "text",
                    "status": "failed",
                }
            )
    return summaries


def publish_live_state_snapshot_if_available(state: Dict[str, Any], *, conversation_id: str) -> None:
    state_update_callback = getattr(ctx, "state_update_callback", None)
    if not callable(state_update_callback):
        return
    try:
        state_update_callback(state)
    except Exception as exc:
        logger.warning("[%s] live state snapshot publish failed: %s", conversation_id, exc)


def _derive_conversation_title_from_user_input(
    *,
    query: Optional[str],
    uploads: Optional[List[Dict[str, Any]]] = None,
    runtime_lang: Optional[str] = None,
    max_chars: int = 30,
) -> str:
    text = re.sub(r"\s+", " ", str(query or "")).strip()
    if not text:
        for item in uploads or []:
            if not isinstance(item, dict):
                continue
            candidate = str(item.get("name") or item.get("filename") or "").strip()
            if candidate:
                text = candidate
                break
    if not text:
        return "新对话" if str(runtime_lang or "").lower().startswith("zh") else "New conversation"
    return text[:max_chars] + ("..." if len(text) > max_chars else "")


def _ensure_conversation_title(
    state: Dict[str, Any],
    *,
    query: Optional[str],
    uploads: Optional[List[Dict[str, Any]]] = None,
    runtime_lang: Optional[str] = None,
) -> None:
    metadata = state.setdefault("session_metadata", {})
    existing = re.sub(r"\s+", " ", str(metadata.get("conversation_title") or "")).strip()
    if existing:
        metadata["conversation_title"] = existing[:40]
        return
    metadata["conversation_title"] = _derive_conversation_title_from_user_input(
        query=query,
        uploads=uploads,
        runtime_lang=runtime_lang,
    )


def _case_supports_ask_user(case: Dict[str, Any]) -> bool:
    if case.get("supports_ask_user") is False:
        return False

    raw_disabled = case.get("disable_tools")
    if isinstance(raw_disabled, (list, tuple, set)):
        for item in raw_disabled:
            if str(item or "").strip() == "ask_user":
                return False
    return True


def _build_resume_user_input_text(
    *,
    resume_answers: Dict[str, Any],
    interaction_type: str,
    runtime_lang: Optional[str],
) -> str:
    is_zh = str(runtime_lang or "").lower().startswith("zh")
    if interaction_type == "todolist_feedback":
        decision = str(resume_answers.get("decision") or "").strip()
        user_feedback = str(resume_answers.get("user_feedback") or "").strip()
        if is_zh:
            if decision == "revise":
                base = "用户已修改 todolist，以用户修改后的版本为准"
                if user_feedback:
                    return f"{base}（{user_feedback}）。请回到原始用户请求，按当前 todolist 直接推进，**不要再重新创建 todolist**。"
                return f"{base}。请回到原始用户请求，按当前 todolist 直接推进，**不要再重新创建 todolist**。"
            if decision == "timeout_approve":
                return "上一轮 todolist 已按倒计时规则自动通过；用户没有新增自然语言请求。请回到原始用户请求，并根据已通过的 todolist 推进后续步骤。"
            return "上一轮 todolist 已收到用户确认；请回到原始用户请求，并根据已确认的 todolist 推进后续步骤。"
        if decision == "revise":
            base = "The user has revised the todolist; the user's version is now canonical"
            if user_feedback:
                return f"{base} ({user_feedback}). Return to the original user request, proceed from the current todolist, and **do NOT recreate the todolist**."
            return f"{base}. Return to the original user request, proceed from the current todolist, and **do NOT recreate the todolist**."
        if decision == "timeout_approve":
            return "The previous todolist was auto-approved by the countdown rule; the user did not add a new natural-language request. Return to the original user request and proceed from the approved todolist."
        return "The previous todolist was approved by the user. Return to the original user request and proceed from the approved todolist."
    return "用户已回答上一轮澄清问题；请回到原始用户请求，并结合补充答案推进后续步骤。" if is_zh else "The user answered the previous clarification question. Return to the original user request and proceed using the additional answer."


def _deep_research_runtime_enabled(conf: Optional[Dict[str, Any]]) -> bool:
    runtime_cfg = (conf or {}).get("runtime", {}) or {}
    deep_research_cfg = runtime_cfg.get("deep_research", {}) or {}
    return bool(deep_research_cfg.get("enabled", True))


def _build_deep_research_mode_user_instruction(conf: Optional[Dict[str, Any]]) -> str:
    runtime_cfg = (conf or {}).get("runtime", {}) or {}
    deep_research_cfg = runtime_cfg.get("deep_research", {}) or {}
    skill_name = str(deep_research_cfg.get("skill_name") or "deep-research").strip() or "deep-research"
    return (
        f"用户已打开深度研究模式。"
        f"如果用户问题是简单问候、闲聊或无明确研究需求，可直接回复，无需调用 `{skill_name}` skill；"
        f"否则应读取并按照 `{skill_name}` skill 执行。"
    )


def prepare_runtime_state(
    case: Dict[str, Any],
    components: Dict[str, Any],
    session_ctx: Dict[str, Any],
) -> Dict[str, Any]:
    conf = session_ctx["conf"]
    raw_query = session_ctx["raw_query"]
    runtime_conf = session_ctx["runtime_conf"]
    runtime_lang = session_ctx["runtime_lang"]
    runtime_session_id = session_ctx["runtime_session_id"]
    conversation_id = session_ctx["conversation_id"]
    sandbox_manager = session_ctx["sandbox_manager"]
    system_prompt_template = session_ctx["system_prompt_template"]
    locale_seed = session_ctx["locale_seed"]
    detected_locale = session_ctx["detected_locale"]
    log = session_ctx["log"]
    replay_agent_state = case.get("replay_agent_state")
    supports_ask_user = _case_supports_ask_user(case)

    if isinstance(replay_agent_state, dict) and isinstance(replay_agent_state.get("main_state"), dict):
        state = deepcopy(replay_agent_state)
        shared_state = ensure_conversation_state(state.get("main_state"))
        shared_state["conversation_id"] = conversation_id
        update_language_profile(shared_state, runtime_lang, source_message_id=None)
        shared_state.setdefault("runtime_control", {})["supports_ask_user"] = supports_ask_user
        attach_shared_layers(state, shared_state)
        state["main_state"] = dict(state.get("main_state") or {})
        attach_shared_layers(state["main_state"], shared_state)
        _attach_preloaded_context_messages(
            state,
            config=conf,
            runtime_conf=runtime_conf,
            runtime_lang=runtime_lang,
        )
        _attach_retrieved_context_messages(
            state,
            config=conf,
            runtime_conf=runtime_conf,
            runtime_lang=runtime_lang,
            query=raw_query,
            llm=components.get("llm") or getattr(ctx, "llm", None),
            prefetch_future=session_ctx.get("retrieved_context_future"),
        )
        rebuild_compiled_messages(state["main_state"])
        state["conversation_id"] = conversation_id
        state.setdefault("runtime_control", {})["conversation_status"] = "running"
        publish_live_state_snapshot_if_available(state, conversation_id=conversation_id)
        return {
            "query": raw_query,
            "raw_query": raw_query,
            "runtime_conf": runtime_conf,
            "runtime_lang": runtime_lang,
            "state": state,
        }

    local_file_path = case.get("local_file_path", None)
    file_dir = components.get("file_dir")
    query = raw_query
    suppress_user_query_message = bool(case.get("suppress_user_query_message"))
    skip_persisted_upload_rehydration = bool(case.get("skip_persisted_upload_rehydration"))

    explicit_local_paths = _resolve_existing_local_file_paths(local_file_path, file_dir=file_dir)
    persisted_local_paths = [] if skip_persisted_upload_rehydration else _collect_conversation_uploaded_files(conversation_id)
    explicit_keys = {os.path.normcase(os.path.abspath(path)) for path in explicit_local_paths}
    rehydration_paths = [
        path for path in persisted_local_paths if os.path.normcase(os.path.abspath(path)) not in explicit_keys
    ]
    # 本轮显式上传优先，历史文件只做补齐，不覆盖这次请求里传进来的同名路径。
    upload_paths = [*explicit_local_paths, *rehydration_paths]
    explicit_sandbox_paths: List[str] = []
    explicit_parse_sandbox_paths: List[str] = []
    uploaded_sandbox_by_local: Dict[str, str] = {}

    if upload_paths:
        for file_path in upload_paths:
            ensure_not_cancelled()
            sandbox_path, uploaded_file_paths = _upload_local_path_to_sandbox(
                sandbox_manager=sandbox_manager,
                session_id=runtime_session_id,
                file_path=file_path,
            )
            norm_path = os.path.normcase(os.path.abspath(file_path))
            uploaded_sandbox_by_local[norm_path] = sandbox_path
            if norm_path in explicit_keys:
                explicit_sandbox_paths.append(sandbox_path)
                if not os.path.isdir(file_path):
                    explicit_parse_sandbox_paths.extend(uploaded_file_paths)
            log.info("文件已上传: %s -> %s", os.path.basename(file_path), sandbox_path)

        if rehydration_paths:
            logger.info(
                "[%s] 已回填历史上传文件: %s个（本轮新增: %s个）",
                conversation_id,
                len(rehydration_paths),
                len(explicit_local_paths),
            )

    # 这里把“恢复旧会话”和“开始新一轮输入”收束成一个统一 state。
    conversation_state = ensure_conversation_state(case.get("agent_state"))
    conversation_state["conversation_id"] = conversation_id
    update_language_profile(conversation_state, runtime_lang, source_message_id=None)
    conversation_state.setdefault("runtime_control", {})["supports_ask_user"] = supports_ask_user
    resume_answers = case.get("resume_answers")
    resume_interaction_type = ""
    resume_todolist_decision = ""
    resolved_resume_todolist = None
    if isinstance(resume_answers, dict) and resume_answers:
        resume_interaction_type = str(resume_answers.get("interaction_type") or "").strip()
        resume_todolist_decision = str(resume_answers.get("decision") or "").strip()
        updated_ask_record = find_pending_ask_user_record_for_resume(
            conversation_state,
            answer_payload=resume_answers,
        )
        if updated_ask_record is None:
            logger.warning("[%s] 未找到可回填的待确认 tool_result，resume_answers 将作为用户输入继续", conversation_id)
        updated_result = (
            (updated_ask_record.get("payload") or {}).get("result")
            if isinstance(updated_ask_record, dict)
            else None
        )
        resume_user_record = add_user_input(
            conversation_state,
            text=_build_resume_user_input_text(
                resume_answers=resume_answers,
                interaction_type=resume_interaction_type,
                runtime_lang=runtime_lang,
            ),
            input_kind="todolist_feedback" if resume_interaction_type == "todolist_feedback" else "resume_answer",
            payload=deepcopy(resume_answers),
            language=runtime_lang,
            parent_id=updated_ask_record.get("id") if isinstance(updated_ask_record, dict) else None,
            source="resume_interaction",
        )
        resume_user_record["scope"] = "main"
        record_runtime_event(
            event_type="user_input",
            state=conversation_state,
            record=resume_user_record,
            scope="main",
        )
        if isinstance(resume_answers.get("todo_list"), list):
            resolved_resume_todolist = resume_answers.get("todo_list")
        elif isinstance(updated_result, dict) and isinstance(updated_result.get("todo_list"), list):
            resolved_resume_todolist = updated_result.get("todo_list")
        if resume_interaction_type == "todolist_feedback":
            if resume_todolist_decision in {"approve", "timeout_approve", "revise"}:
                if isinstance(resolved_resume_todolist, list):
                    set_todolist_projection(conversation_state, resolved_resume_todolist)
    clear_waiting_for_user_input(conversation_state)
    set_conversation_status(conversation_state, "running")

    deep_research_enabled = resolve_case_deep_research_enabled(case) and _deep_research_runtime_enabled(conf)
    conversation_state.setdefault("session_metadata", {})["deep_research_enabled"] = deep_research_enabled

    active_editor_file = normalize_active_editor_file(
        case.get("active_editor_file")
        or (conversation_state.get("projections") or {}).get("current_active_editor_projection")
    )
    if active_editor_file is not None:
        set_active_editor_projection(conversation_state, active_editor_file)

    manual_todolist_patch = case.get("manual_todolist_patch")
    is_todolist_feedback_resume = resume_interaction_type == "todolist_feedback"
    if manual_todolist_patch is not None and not is_todolist_feedback_resume:
        if isinstance(manual_todolist_patch, list):
            set_todolist_projection(conversation_state, manual_todolist_patch)
        elif isinstance(manual_todolist_patch, dict) and isinstance(manual_todolist_patch.get("todo_list"), list):
            set_todolist_projection(conversation_state, manual_todolist_patch.get("todo_list"))

    # asset_index 用 storage_path 做主键，避免重复注册同一份本地文件。
    existing_files_by_storage = {
        os.path.normcase(os.path.abspath(str(item.get("storage_path")))): item
        for item in (conversation_state.get("asset_index", {}).get("files") or [])
        if isinstance(item, dict) and item.get("storage_path")
    }
    input_file_meta = case.get("input_file_meta") or []
    upload_entries: List[Dict[str, Any]] = []

    for index, file_path in enumerate(explicit_local_paths):
        abs_path = os.path.abspath(file_path)
        sandbox_path = explicit_sandbox_paths[index] if index < len(explicit_sandbox_paths) else None
        saved_meta = input_file_meta[index] if index < len(input_file_meta) and isinstance(input_file_meta[index], dict) else {}
        existing_entry = existing_files_by_storage.get(os.path.normcase(abs_path))
        if existing_entry is None:
            existing_entry = register_file_asset(
                conversation_state,
                origin_message_id=None,
                name=os.path.basename(abs_path),
                asset_kind="user_upload",
                storage_path=abs_path,
                sandbox_path=sandbox_path,
                file_id=saved_meta.get("file_id"),
                stable_order=len(conversation_state["asset_index"]["files"]) + 1,
            )
            existing_files_by_storage[os.path.normcase(abs_path)] = existing_entry
        else:
            existing_entry["sandbox_path"] = sandbox_path
            if saved_meta.get("file_id"):
                existing_entry["file_id"] = saved_meta["file_id"]

        upload_entries.append(
            {
                "file_id": existing_entry.get("file_id"),
                "name": existing_entry.get("name"),
                "asset_kind": existing_entry.get("asset_kind"),
                "storage_path": existing_entry.get("storage_path"),
                "sandbox_path": existing_entry.get("sandbox_path"),
                "size_bytes": saved_meta.get("size_bytes"),
                "stable_order": existing_entry.get("stable_order"),
            }
        )

    for file_path in rehydration_paths:
        abs_path = os.path.abspath(file_path)
        sandbox_path = uploaded_sandbox_by_local.get(os.path.normcase(abs_path))
        existing_entry = existing_files_by_storage.get(os.path.normcase(abs_path))
        if existing_entry is None:
            existing_entry = register_file_asset(
                conversation_state,
                origin_message_id=None,
                name=os.path.basename(abs_path),
                asset_kind="user_upload",
                storage_path=abs_path,
                sandbox_path=sandbox_path,
                stable_order=len(conversation_state["asset_index"]["files"]) + 1,
            )
            existing_files_by_storage[os.path.normcase(abs_path)] = existing_entry
        else:
            existing_entry["sandbox_path"] = sandbox_path

    # 只对本轮显式上传的文件做预解析，历史回填文件保持惰性，不额外重跑 parser。
    parsed_file_summaries = _best_effort_parse_files_for_context(
        explicit_parse_sandbox_paths,
        conf=conf,
        runtime_lang=runtime_lang,
    )
    for item in parsed_file_summaries:
        source_file_id = None
        sandbox_path = item.get("path")
        for file_entry in conversation_state.get("asset_index", {}).get("files", []):
            if file_entry.get("sandbox_path") == sandbox_path:
                source_file_id = file_entry.get("file_id")
                break
        if source_file_id:
            register_parsed_artifact(
                conversation_state,
                source_file_id=source_file_id,
                parser="document_parser",
                storage_path=item.get("parsed_path"),
                summary=item.get("summary"),
                preview=item.get("preview"),
                content_kind=item.get("content_kind"),
            )

    knowledge_base_refs = extract_knowledge_base_refs(
        raw_query,
        explicit_refs=case.get("knowledge_base_refs"),
    )
    final_system_prompt = system_prompt_template
    conversation_state["message_records"] = [
        record for record in conversation_state.get("message_records", []) if record.get("type") != "system_context"
    ]
    add_system_context(
        conversation_state,
        text=final_system_prompt,
        payload={
            "prompt_locale": runtime_lang,
            "deep_research_enabled": deep_research_enabled,
        },
    )

    if manual_todolist_patch is not None and not is_todolist_feedback_resume:
        if isinstance(manual_todolist_patch, list):
            todo_payload = manual_todolist_patch
        elif isinstance(manual_todolist_patch, dict) and isinstance(manual_todolist_patch.get("todo_list"), list):
            todo_payload = manual_todolist_patch.get("todo_list")
        else:
            todo_payload = manual_todolist_patch
        # todolist 编辑要先进入时间线，这样编译 prompt 时它会排在本轮原始 user input 之前。
        todolist_record = add_user_input(
            conversation_state,
            text="用户修改了当前 todolist",
            input_kind="todolist_edit",
            payload={
                "operation": "replace",
                "source": "manual_editor",
                "todo_list": todo_payload,
            },
            language=runtime_lang,
        )
        todolist_record["scope"] = "main"
        record_runtime_event(
            event_type="user_input",
            state=conversation_state,
            record=todolist_record,
            scope="main",
        )

    created_user_input_record = None
    if not suppress_user_query_message and (raw_query.strip() or upload_entries):
        input_kind = "text" if raw_query.strip() else "upload_only"
        input_text = raw_query if raw_query.strip() else "用户上传了文件"
        created_user_input_record = add_user_input(
            conversation_state,
            text=input_text,
            input_kind=input_kind,
            uploads=upload_entries,
            refs=knowledge_base_refs,
            language=detected_locale,
        )
        created_user_input_record["scope"] = "main"
        record_runtime_event(
            event_type="user_input",
            state=conversation_state,
            record=created_user_input_record,
            scope="main",
        )
        if deep_research_enabled:
            deep_research_record = add_user_input(
                conversation_state,
                text=_build_deep_research_mode_user_instruction(conf),
                input_kind="functional_instruction",
                payload={"mode": "deep_research"},
                language=runtime_lang,
                language_confidence=1.0,
                source="runtime",
            )
            deep_research_record["scope"] = "main"
            deep_research_record["hidden"] = True
        _ensure_conversation_title(
            conversation_state,
            query=raw_query,
            uploads=upload_entries,
            runtime_lang=runtime_lang,
        )

    # 从 agent.init_state 起步，确保主/子任务运行时需要的 runtime 字段完整存在。
    state = deepcopy(dict(session_ctx["agent"].init_state))
    state.update(conversation_state)
    state["main_state"] = dict(state["main_state"])
    attach_shared_layers(state["main_state"], state)
    _attach_preloaded_context_messages(
        state,
        config=conf,
        runtime_conf=runtime_conf,
        runtime_lang=runtime_lang,
    )
    _attach_retrieved_context_messages(
        state,
        config=conf,
        runtime_conf=runtime_conf,
        runtime_lang=runtime_lang,
        query=raw_query,
        llm=components.get("llm") or getattr(ctx, "llm", None),
        prefetch_future=session_ctx.get("retrieved_context_future"),
    )
    rebuild_compiled_messages(state["main_state"])
    # conversation_id 是持久会话树 id；runtime_session_id 是本次运行的 session id。
    # 记忆更新可能在 session-end 等待后或 daily closeout 中离线执行，所以这里必须把真实 session id 写进 state。
    state["session_metadata"]["session_id"] = runtime_session_id
    state["session_metadata"]["memory_fingerprint"] = None
    if created_user_input_record is not None:
        checkpoint_runtime_state(
            checkpoint_kind="user_input",
            state=state,
        )
    publish_live_state_snapshot_if_available(state, conversation_id=conversation_id)

    log.info(
        "[%s] prompt_source=%s restored_records=%s memory_disabled=%s",
        conversation_id,
        "state_v3_compiled",
        len(state.get("message_records", [])),
        True,
    )
    pre_run_state_log, full_state_omitted = _serialize_pre_run_state_for_log(state)
    log.info(
        "[%s] %s=%s",
        conversation_id,
        "pre_run_state_summary" if full_state_omitted else "pre_run_state",
        pre_run_state_log,
    )

    return {
        "query": query,
        "raw_query": raw_query,
        "runtime_conf": runtime_conf,
        "runtime_lang": runtime_lang,
        "state": state,
    }
