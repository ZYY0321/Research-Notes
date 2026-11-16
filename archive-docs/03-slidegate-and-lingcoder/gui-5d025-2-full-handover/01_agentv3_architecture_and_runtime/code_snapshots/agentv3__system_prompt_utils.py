import json
import os
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import yaml
from jinja2 import Environment, FileSystemLoader

from src.skill_registry import build_skill_registry
from tools.multimodal_file.read_tool import read

logger = logging.getLogger(__name__)
_TOKEN_ENCODER = None
_TOKEN_ENCODER_READY = False
_DEFAULT_MEMORY_CONTENT_MAX_TOKENS = 2000
_MEMORY_CONTENT_TRUNCATED_SUFFIX_TEMPLATE = "...[内容已截断] 完整内容查看: {content_path}"
_READ_TOOL_SCHEMES = ("local:", "knowledge:", "memory:")

def load_config(config_path):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_enabled_tools(config):
    """获取启用的工具列表"""
    enabled_tools = {}
    if 'tools' in config:
        for tool_name, tool_config in config['tools'].items():
            enabled_tools[f"enable_{tool_name}"] = tool_config.get('enabled', False)
    enabled_tools["enable_execute_code"] = bool(
        enabled_tools.get("enable_execute_code")
        or enabled_tools.get("enable_execute_jupyter_code")
    )
    enabled_tools["enable_execute_jupyter_code"] = enabled_tools["enable_execute_code"]
    return enabled_tools


def _is_delegate_from_depth(delegate_depth: Any) -> bool:
    try:
        return int(delegate_depth or 0) > 0
    except (TypeError, ValueError):
        return False


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


def _clip_content(content: str, content_path: str, max_tokens: Optional[int] = None) -> str:
    token_budget = _safe_int(max_tokens, _DEFAULT_MEMORY_CONTENT_MAX_TOKENS)
    if token_budget <= 0:
        return content

    if _count_text_tokens(content) <= token_budget:
        return content

    clipped_content = _clip_text_to_token_budget(content, token_budget)
    truncated_suffix = _MEMORY_CONTENT_TRUNCATED_SUFFIX_TEMPLATE.format(
        content_path=content_path
    )
    return f"{clipped_content}{truncated_suffix}"


def _read_text_with_read_tool(
    file_path: str,
    *,
    config: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
) -> str:
    read_path = (
        file_path
        if str(file_path).startswith(_READ_TOOL_SCHEMES)
        else f"local://{str(file_path).lstrip('/')}"
    )
    result = read(read_path, state=state, config=config)
    if not isinstance(result, dict):
        raise ValueError(f"read tool did not return text content for {file_path}")
    if not result.get("success"):
        raise ValueError(str(result.get("error") or f"failed to read {file_path}"))
    content = result.get("content", "")
    if not isinstance(content, str):
        raise ValueError(f"read tool returned non-text content for {file_path}")
    return content


def render_system_prompt_from_config(
    config: Optional[Dict[str, Any]],
    template_path: str,
    user_profile_path: Optional[str] = None,
    long_term_memory_path: Optional[str] = None,
    *,
    state_var_overrides: Optional[Dict[str, Any]] = None,
) -> str:
    """根据配置动态渲染系统提示"""
    config = config or {}

    # 获取工具启用状态
    tool_states = get_enabled_tools(config)
    runtime_cfg = config.get("runtime", {}) or {}
    enable_skill_registry = bool(runtime_cfg.get("enable_skill_registry", False))
    enable_knowledge_base_tool = bool(runtime_cfg.get("enable_knowledge_base_tool", False))
    now = datetime.now()
    # 设置模板变量
    state_vars = {
        "CURRENT_DATE": now.strftime("%Y-%m-%d"),
        "CURRENT_TIME": now.strftime("%H:%M:%S"),
        **tool_states,
        "agent_role": "main",
        "delegate_depth": 0,
        "agent_name": "main_agent",
        "delegate_id": "",
        "parent_tool_call_id": "",
        "is_delegate": False,
        "runtime_identity": {
            "agent_role": "main",
            "delegate_depth": 0,
            "agent_name": "main_agent",
            "is_delegate": False,
        },
        "enable_skill_registry": enable_skill_registry,
        "enable_knowledge_base_tool": enable_knowledge_base_tool,
        "enable_execute_code": bool(tool_states.get("enable_execute_code")),
        "enable_read": bool(tool_states.get("enable_read")),
    }
    if isinstance(state_var_overrides, dict):
        state_vars.update(state_var_overrides)
    state_vars["is_delegate"] = _is_delegate_from_depth(state_vars.get("delegate_depth"))
    runtime_identity = state_vars.get("runtime_identity")
    if isinstance(runtime_identity, dict):
        runtime_identity = dict(runtime_identity)
    else:
        runtime_identity = {}
    for identity_key in (
        "agent_role",
        "delegate_depth",
        "agent_name",
        "delegate_id",
        "parent_tool_call_id",
    ):
        if identity_key in state_vars:
            runtime_identity[identity_key] = state_vars[identity_key]
    runtime_identity["is_delegate"] = _is_delegate_from_depth(runtime_identity.get("delegate_depth"))
    state_vars["runtime_identity"] = runtime_identity

    skill_registry = build_skill_registry(config, use_sandbox_location=True)
    state_vars["SKILL_REGISTRY"] = skill_registry
    state_vars["SKILL_REGISTRY_JSON"] = json.dumps(skill_registry, ensure_ascii=False, indent=2)
    if isinstance(state_var_overrides, dict):
        for registry_key in ("enable_skill_registry", "SKILL_REGISTRY", "SKILL_REGISTRY_JSON"):
            if registry_key in state_var_overrides:
                state_vars[registry_key] = state_var_overrides[registry_key]

    memory_config = config.get("memory", {})
    if not isinstance(memory_config, dict):
        memory_config = {}
    memory_enabled = bool(memory_config.get("enabled", True))
    if memory_enabled:
        if user_profile_path is None:
            user_profile_path = memory_config.get("user_profile_path", "memory://user.md")
        if long_term_memory_path is None:
            long_term_memory_path = memory_config.get("long_term_memory_path", "memory://memory.md")
        try:
            user_profile = _read_text_with_read_tool(user_profile_path, config=config)
            state_vars["USER_PROFILE"] = _clip_content(
                user_profile,
                user_profile_path,
                memory_config.get("user_profile_max_token", _DEFAULT_MEMORY_CONTENT_MAX_TOKENS),
            )
            state_vars["USER_PROFILE_PATH"] = user_profile_path
        except Exception as e:
            logger.warning(f"user profile 导入失败: {e}")

        try:
            long_term_memory = _read_text_with_read_tool(long_term_memory_path, config=config)
            state_vars["LONG_TERM_MEMORY"] = _clip_content(
                long_term_memory,
                long_term_memory_path,
                memory_config.get("long_term_memory_max_token", _DEFAULT_MEMORY_CONTENT_MAX_TOKENS),
            )
            state_vars["LONG_TERM_MEMORY_PATH"] = long_term_memory_path
        except Exception as e:
            logger.warning(f"long-term memory 导入失败: {e}")

    template_file = Path(template_path)
    template_dir = template_file.parent if str(template_file.parent) else Path(".")
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template(template_file.name)
    system_prompt = template.render(**state_vars)
    return system_prompt


def render_system_prompt(config_path, template_path):
    """根据配置动态渲染系统提示"""
    config = load_config(config_path)
    return render_system_prompt_from_config(config, template_path)


def _normalize_language(language: Optional[str]) -> Optional[str]:
    if not language:
        return None
    lang = str(language).strip().lower()
    if lang.startswith("zh"):
        return "zh"
    if lang.startswith("en"):
        return "en"
    return lang


def resolve_system_prompt_path(
    runtime_conf: Optional[Dict[str, Any]],
    default_zh: str,
    default_en: str,
) -> str:
    """Resolve system prompt path based on runtime language with safe fallbacks."""
    runtime_conf = runtime_conf or {}
    lang = _normalize_language(runtime_conf.get("language"))

    # Prefer explicit per-language keys if provided
    if lang == "zh" and runtime_conf.get("system_prompt_zh"):
        return runtime_conf["system_prompt_zh"]
    if lang == "en" and runtime_conf.get("system_prompt_en"):
        return runtime_conf["system_prompt_en"]

    prompt_value = runtime_conf.get("system_prompt")
    if isinstance(prompt_value, dict):
        if lang and prompt_value.get(lang):
            return prompt_value[lang]
        if prompt_value.get("default"):
            return prompt_value["default"]

    if not prompt_value or str(prompt_value).strip().lower() == "auto":
        return default_zh if lang == "zh" else default_en

    # If a default path is set and language is specified, align to language.
    if lang:
        raw_norm = os.path.normpath(str(prompt_value))
        if raw_norm in {os.path.normpath(default_zh), os.path.normpath(default_en)}:
            return default_zh if lang == "zh" else default_en

    return str(prompt_value)
def _safe_int(value: Any, default: int) -> int:
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except Exception:
        return default


def _append_block(base: str, block: Optional[str]) -> str:
    if not block:
        return base
    if not base:
        return block
    if base.endswith("\n"):
        return base + block
    return base + "\n" + block


def _tag_block_pattern(tag_name: str) -> re.Pattern:
    escaped = re.escape(str(tag_name or "").strip())
    return re.compile(rf"<{escaped}>\n?.*?</{escaped}>", re.DOTALL)


def replace_system_prompt_block(
    system_prompt: str,
    tag_name: str,
    block: Optional[str],
) -> str:
    """Replace a tagged block in system prompt; append if missing and block is provided."""
    prompt = system_prompt or ""
    pattern = _tag_block_pattern(tag_name)
    match = pattern.search(prompt)
    if match:
        start, end = match.span()
        if block:
            return prompt[:start] + block + prompt[end:]
        updated = prompt[:start] + prompt[end:]
        updated = re.sub(r"\n{3,}", "\n\n", updated)
        return updated.strip("\n")

    if block:
        return _append_block(prompt, block)
    return prompt


def build_user_memories_block(
    config: Optional[Dict[str, Any]],
    query: Optional[str],
    session_id: Optional[str],
    memory_user_id: Optional[str] = None,
    recall_mode: Optional[str] = None,
) -> Optional[str]:
    del config, query, session_id, memory_user_id, recall_mode
    return None


def refresh_user_memories_in_system_prompt(
    system_prompt: str,
    config: Optional[Dict[str, Any]],
    query: Optional[str],
    session_id: Optional[str],
    memory_user_id: Optional[str] = None,
    recall_mode: Optional[str] = None,
) -> str:
    recall_block = build_user_memories_block(
        config=config,
        query=query,
        session_id=session_id,
        memory_user_id=memory_user_id,
        recall_mode=recall_mode,
    )
    return replace_system_prompt_block(system_prompt, "user-memories", recall_block)


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

def build_system_prompt_with_memory(
    base_prompt: str,
    config: Optional[Dict[str, Any]],
    query: Optional[str],
    session_id: Optional[str],
    memory_user_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> str:
    # 主运行链路已关闭所有记忆注入，避免 summary/recall 额外占用执行时间。
    return base_prompt or ""


def build_runtime_system_prompt(
    config: Optional[Dict[str, Any]],
    *,
    query: Optional[str],
    session_id: Optional[str],
    memory_user_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    deep_research_enabled: bool = False,
    include_deep_research_mode: bool = True,
    language_override: Optional[str] = None,
    state_var_overrides: Optional[Dict[str, Any]] = None,
) -> str:
    cfg = config or {}
    runtime_conf = dict((cfg.get("runtime") or {}))
    normalized_language = _normalize_language(language_override)
    if normalized_language:
        runtime_conf["language"] = normalized_language

    template_path = resolve_system_prompt_path(
        runtime_conf,
        default_zh="agents/agentv3/system_prompt_zh.md",
        default_en="agents/agentv3/system_prompt_en.md",
    )
    base_prompt = render_system_prompt_from_config(
        cfg,
        template_path,
        state_var_overrides=state_var_overrides,
    )
    system_prompt = build_system_prompt_with_memory(
        base_prompt,
        cfg,
        query,
        session_id,
        memory_user_id=memory_user_id,
        conversation_id=conversation_id,
    )
    return system_prompt
