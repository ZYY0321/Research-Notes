import io
import logging
import os
import zipfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.agentv3.system_prompt_utils import (
    render_system_prompt_from_config,
    resolve_system_prompt_path,
)
from src.base_llm import BaseLLM
from src.skill_registry import get_skill_registry_settings
from src.utils import convert_to_openai_tool, load_yaml_config
from src.utils.tool_utils import load_tools
from tools.search.knowledge_base_tool import (
    KnowledgeBaseArgs,
    KnowledgeBaseArgs_zh,
    knowledge_base,
)


logger = logging.getLogger(__name__)
_ALWAYS_DISABLED_TOOLS = frozenset({
    "memory_compression_and_offload",
})


def _coerce_optional_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()
    if not text:
        return None
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return bool(value)


def resolve_case_deep_research_enabled(case: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(case, dict):
        return False
    return _coerce_optional_bool(case.get("deep_research")) is True


def _apply_disabled_tools(
    conf: Dict[str, Any],
    disabled_tools: Optional[List[str] | set[str] | tuple[str, ...]] = None,
) -> Dict[str, Any]:
    disabled = {
        str(name).strip()
        for name in (disabled_tools or [])
        if str(name).strip()
    }
    disabled.update(_ALWAYS_DISABLED_TOOLS)
    if not disabled:
        return conf

    effective_conf = deepcopy(conf)
    tool_cfg = effective_conf.setdefault("tools", {})
    for tool_name in disabled:
        current = tool_cfg.get(tool_name) or {}
        if not isinstance(current, dict):
            current = {}
        current["enabled"] = False
        tool_cfg[tool_name] = current
    return effective_conf


def _llm_provider_kwargs(conf: Dict[str, Any]) -> Dict[str, Any]:
    provider = str(conf.get("provider") or "").strip().lower()
    kwargs: Dict[str, Any] = {}
    if provider == "anthropic":
        for key in ("thinking", "output_config"):
            value = conf.get(key)
            if value is not None:
                kwargs[key] = value
    else:
        extra_body = conf.get("extra_body")
        if extra_body is not None:
            kwargs["extra_body"] = extra_body
    return kwargs


def _load_skill_assets(conf: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_skill_registry_settings(conf)
    return {
        "enabled": settings["enabled"],
        "skills_local_dir": settings["skills_dir"],
        "skills_sandbox_dir": settings["skills_sandbox_dir"],
        "skills_allowlist": settings["allowlist"],
        "skills_extra_dirs": settings["extra_dirs"],
    }


def _compress_skills_folder(
    skills_dir: str,
    allowlist: Optional[List[str]] = None,
    extra_dirs: Optional[List[str]] = None,
) -> Optional[bytes]:
    """动态压缩 skills 文件夹为 zip 格式并返回字节数据."""
    skills_path = Path(skills_dir)
    if not skills_path.exists() or not skills_path.is_dir():
        logger.warning("Skills 目录不存在或不是文件夹: %s", skills_path)
        return None

    allow = {item.strip().lower() for item in (allowlist or []) if isinstance(item, str)}
    extras = {item.strip().lower() for item in (extra_dirs or []) if isinstance(item, str)}

    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(skills_path):
                root_path = Path(root)
                for file_name in files:
                    file_path = root_path / file_name
                    rel_path = file_path.relative_to(skills_path)
                    if allow and rel_path.parts:
                        top = rel_path.parts[0].lower()
                        if top not in allow and top not in extras:
                            continue
                    zipf.write(file_path, rel_path.as_posix())
        data = buf.getvalue()
        logger.info("成功压缩 skills 文件夹: %s, 大小: %s bytes", skills_path, len(data))
        return data
    except Exception as exc:
        logger.error("压缩 skills 文件夹失败: %s", exc, exc_info=True)
        return None


def _clone_tool_with_new_name(
    tool: Dict[str, Any],
    new_name: str,
    description_suffix: str = "",
) -> Dict[str, Any]:
    cloned = deepcopy(tool)
    cloned["schema"]["function"]["name"] = new_name
    if description_suffix:
        desc = str(cloned["schema"]["function"].get("description") or "").strip()
        cloned["schema"]["function"]["description"] = f"{desc} {description_suffix}".strip()
    return cloned


def _append_virtual_tools(
    tools: List[Dict[str, Any]],
    *,
    runtime_conf: Optional[Dict[str, Any]],
    language: Optional[str],
) -> List[Dict[str, Any]]:
    runtime_cfg = runtime_conf or {}
    tool_names = {
        tool.get("schema", {}).get("function", {}).get("name")
        for tool in tools
        if isinstance(tool, dict)
    }
    augmented = list(tools)

    if "execute_jupyter_code" in tool_names and "execute_code" not in tool_names:
        execute_tool = next(
            tool
            for tool in augmented
            if tool.get("schema", {}).get("function", {}).get("name") == "execute_jupyter_code"
        )
        augmented.append(_clone_tool_with_new_name(execute_tool, "execute_code"))

    if runtime_cfg.get("enable_knowledge_base_tool") and "knowledge_base" not in tool_names:
        kb_args = KnowledgeBaseArgs_zh if str(language or "").lower().startswith("zh") else KnowledgeBaseArgs
        augmented.append(
            convert_to_openai_tool(
                target=knowledge_base,
                args_schema=kb_args,
                name="knowledge_base",
                description="Reserved interface for user knowledge-base access.",
                filter_args=["self", "cls", "state", "config", "llm"],
            )
        )

    return augmented


def build_agent_components(conf_path: Path) -> Dict[str, Any]:
    """初始化 LLM/VLM 与工具等共用组件."""
    conf = load_yaml_config(str(conf_path))
    effective_conf = _apply_disabled_tools(conf)
    skill_assets = _load_skill_assets(conf)

    llm_conf = effective_conf.get("llm", {})
    vlm_conf = effective_conf.get("vlm", {})
    audio_basellm_conf = effective_conf.get("audio_basellm", {})

    use_new_llm_raw = effective_conf.get("use_new_llm")
    use_new_llm = True if use_new_llm_raw is None else bool(use_new_llm_raw)  # Stage 3: default true
    if use_new_llm:
        from src.llm.base import BaseLLM as NewBaseLLM
        llm = NewBaseLLM(conf=llm_conf)
        logger.info("初始化 LLM (v2 chain mode), conf=%s", llm_conf.get("model") or "<chain>")
    else:
        logger.info("初始化 LLM，模型: %s", llm_conf.get("model"))
        llm = BaseLLM(
            model=llm_conf.get("model"),
            api_key=llm_conf.get("api_key"),
            base_url=llm_conf.get("base_url"),
            provider=llm_conf.get("provider"),
            max_tokens=llm_conf.get("max_tokens", 4096),
            temperature=llm_conf.get("temperature", 0.7),
            debug_raw_response=llm_conf.get("debug_raw_response"),
            **_llm_provider_kwargs(llm_conf),
        )

    logger.info("初始化 VLM，模型: %s", vlm_conf.get("model"))
    vlm = BaseLLM(
        model=vlm_conf.get("model"),
        api_key=vlm_conf.get("api_key"),
        base_url=vlm_conf.get("base_url"),
        provider=vlm_conf.get("provider"),
        temperature=vlm_conf.get("temperature", 1.0),
        debug_raw_response=vlm_conf.get("debug_raw_response"),
        **_llm_provider_kwargs(vlm_conf),
    )

    logger.info("初始化 Audio LLM，模型: %s", audio_basellm_conf.get("model"))
    audio_basellm = BaseLLM(
        model=audio_basellm_conf.get("model"),
        api_key=audio_basellm_conf.get("api_key"),
        base_url=audio_basellm_conf.get("base_url"),
        provider=audio_basellm_conf.get("provider"),
        temperature=audio_basellm_conf.get("temperature", 0.7),
        debug_raw_response=audio_basellm_conf.get("debug_raw_response"),
        **_llm_provider_kwargs(audio_basellm_conf),
    )

    runtime_conf = effective_conf.get("runtime", {})
    runtime_lang = runtime_conf.get("language")
    tools = load_tools(config=effective_conf["tools"], language=runtime_lang)
    tools = _append_virtual_tools(tools, runtime_conf=runtime_conf, language=runtime_lang)

    return {
        "conf": effective_conf,
        "config_path": conf_path,
        "system_prompt": "",
        "tools": tools,
        "sandbox_conf": effective_conf.get("sandbox", {}),
        "llm": llm,
        "vlm": vlm,
        "audio_basellm": audio_basellm,
        "skill_assets": skill_assets,
    }


def resolve_locale_resources(
    components: Dict[str, Any],
    locale: Optional[str],
    *,
    disabled_tools: Optional[List[str] | set[str] | tuple[str, ...]] = None,
) -> tuple[str, List[Dict[str, Any]], str]:
    conf = components["conf"]
    runtime_conf = conf.get("runtime", {}) or {}
    normalized = "zh" if str(locale or "").lower().startswith("zh") else "en"
    prompt_runtime_conf = dict(runtime_conf)
    prompt_runtime_conf["language"] = normalized
    effective_conf = _apply_disabled_tools(conf, disabled_tools)
    effective_runtime_conf = effective_conf.get("runtime", {}) or {}
    prompt_runtime_conf = dict(effective_runtime_conf)
    prompt_runtime_conf["language"] = normalized
    system_prompt_path = resolve_system_prompt_path(
        prompt_runtime_conf,
        default_zh="agents/agentv3/system_prompt_zh.md",
        default_en="agents/agentv3/system_prompt_en.md",
    )
    system_prompt = render_system_prompt_from_config(
        config=effective_conf,
        template_path=str(system_prompt_path),
    )
    tools = load_tools(config=effective_conf["tools"], language=normalized)
    tools = _append_virtual_tools(tools, runtime_conf=effective_runtime_conf, language=normalized)
    return system_prompt, tools, normalized
