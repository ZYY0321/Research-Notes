"""BaseLLM - 极简 LiteLLM 封装"""
import logging
import os
from copy import deepcopy
from typing import Any, Dict, List, Optional
from litellm import completion
from litellm.types.utils import Message as LiteLLMMessage
from src.utils.lightllm_debug import (
    ensure_lightllm_debug_hooks_installed,
    log_lightllm_base_request,
    log_lightllm_base_response,
)
from src.utils.cancellation import RunCancelledError, ensure_not_cancelled

logger = logging.getLogger(__name__)
# litellm._turn_on_debug()


# === Bedrock-compat shim：把 litellm 注入的 anthropic-beta 收敛成上游允许的子集 ===
# 上游若走 AWS Bedrock（如 tokenhub.sensetime.com 后端是 Bedrock）会校验 anthropic-beta，
# 拒绝不在白名单里的项（典型挂法：context-management-2025-06-27 → ValidationException:
# invalid beta flag, HTTP 400）。litellm 在多个点会自动注入未白名单的 beta：
#   1. AnthropicModelInfo.get_anthropic_headers — prompt-caching / files / mcp / computer-use 等
#   2. AnthropicConfig.update_headers_with_optional_anthropic_beta — web_fetch / memory /
#      context_management
#   3. AnthropicConfig._ensure_context_management_beta_header — context-management-2025-06-27
#   4. AnthropicConfig.get_cache_control_headers — 硬编码 prompt-caching-2024-07-31
# **默认全清（白名单为空）**：实测不同 Bedrock 通道/key 对 beta 接受度不一致，连
# `prompt-caching-2024-07-31` 都可能被拒（如 conf_a 那把 key）。为了"任何 Bedrock 后端默认就能通"，
# 默认不发任何 anthropic-beta。代价：失去 prompt cache 加速（功能正确，cache 是性能优化）。
# 想恢复某些 beta（如确认上游接受 prompt-caching）→ env `LITELLM_ANTHROPIC_BETA_ALLOWLIST=
# prompt-caching-2024-07-31,computer-use-2024-10-22` 显式给白名单。
# 兜底：`LITELLM_KEEP_ANTHROPIC_BETA=1` 保留原 litellm 全量行为（直连 Anthropic 原生端点用）。
_env_allowlist = os.getenv("LITELLM_ANTHROPIC_BETA_ALLOWLIST", "").strip()
_BEDROCK_BETA_ALLOWLIST = frozenset(
    b.strip() for b in _env_allowlist.split(",") if b.strip()
) if _env_allowlist else frozenset()


def _filter_anthropic_beta(headers: dict) -> None:
    """就地把 headers['anthropic-beta'] 过滤成白名单子集；全被刷掉时整条删除。"""
    raw = headers.get("anthropic-beta")
    if not raw:
        return
    kept = [b.strip() for b in raw.split(",") if b.strip() in _BEDROCK_BETA_ALLOWLIST]
    if kept:
        headers["anthropic-beta"] = ",".join(kept)
    else:
        headers.pop("anthropic-beta", None)


if os.getenv("LITELLM_KEEP_ANTHROPIC_BETA", "").strip().lower() not in {"1", "true", "yes", "on"}:
    try:
        import litellm.llms.anthropic.common_utils as _aco
        import litellm.llms.anthropic.chat.transformation as _act

        _orig_get_anthropic_headers = _aco.AnthropicModelInfo.get_anthropic_headers

        def _get_anthropic_headers_filtered(self, *args, **kwargs):
            headers = _orig_get_anthropic_headers(self, *args, **kwargs)
            _filter_anthropic_beta(headers)
            return headers

        _aco.AnthropicModelInfo.get_anthropic_headers = _get_anthropic_headers_filtered

        _orig_update_optional_beta = _act.AnthropicConfig.update_headers_with_optional_anthropic_beta

        def _update_optional_beta_filtered(self, headers, optional_params):
            headers = _orig_update_optional_beta(self, headers, optional_params)
            _filter_anthropic_beta(headers)
            return headers

        _act.AnthropicConfig.update_headers_with_optional_anthropic_beta = _update_optional_beta_filtered
        # context-management-2025-06-27 不在白名单 → 直接 noop 阻止注入
        _act.AnthropicConfig._ensure_context_management_beta_header = lambda self, headers: None
        # get_cache_control_headers 硬编码的 prompt-caching-2024-07-31 在白名单，原样返回即可（不动）
    except Exception as _exc:  # noqa: BLE001 — litellm 内部 API 变了就忽略,避免 import 时崩
        logger.warning("anthropic-beta shim 安装失败(litellm 内部 API 可能变了): %s", _exc)


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class BaseLLM:
    """极简 LLM 封装类，使用 LiteLLM 统一接口"""

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 provider: str = "openai", temperature: float = 0.7, max_tokens: int = 4096, **kwargs):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.provider = provider
        self.debug_raw_response = _is_truthy(kwargs.pop("debug_raw_response", None)) or _is_truthy(
            os.getenv("LIGHTLLM_DEBUG_RAW_RESPONSE")
        )

        # 构建基础调用参数
        self._call_kwargs = dict(kwargs)
        self._call_kwargs["model"] = model
        if api_key:
            self._call_kwargs["api_key"] = api_key
        if base_url:
            self._call_kwargs["base_url"] = base_url
        if provider:
            self._call_kwargs["custom_llm_provider"] = provider
        if provider == "lightllm" and self.debug_raw_response:
            ensure_lightllm_debug_hooks_installed()

    def _to_plain_data(self, value: Any) -> Any:
        """Convert LiteLLM/OpenAI typed objects into plain Python data."""
        if value is None:
            return None
        if hasattr(value, "model_dump"):
            try:
                return value.model_dump(exclude_none=False)
            except TypeError:
                return value.model_dump()
        if hasattr(value, "dict"):
            try:
                return value.dict()
            except TypeError:
                return value.dict(exclude_none=False)
        if isinstance(value, dict):
            return {k: self._to_plain_data(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._to_plain_data(item) for item in value]
        return value

    def _extract_provider_specific_fields(self, message: Any) -> Optional[Dict[str, Any]]:
        provider_specific_fields = getattr(message, "provider_specific_fields", None)
        if provider_specific_fields is None and isinstance(message, dict):
            provider_specific_fields = message.get("provider_specific_fields")
        provider_specific_fields = self._to_plain_data(provider_specific_fields)
        if isinstance(provider_specific_fields, dict) and provider_specific_fields:
            return provider_specific_fields
        return None

    def _google_tool_message_compat_enabled(self) -> bool:
        provider = str(self.provider or "").strip().lower()
        model_name = str(self._call_kwargs.get("model") or "").strip().lower()
        custom_provider = str(self._call_kwargs.get("custom_llm_provider") or "").strip().lower()
        joined = " ".join(part for part in (provider, custom_provider, model_name) if part)
        return "gemini" in joined or "google" in joined

    def _message_has_google_thought_signature(self, message: Any) -> bool:
        if not self._google_tool_message_compat_enabled():
            return False
        provider_specific_fields = self._extract_provider_specific_fields(message) or {}
        reasoning_details = provider_specific_fields.get("reasoning_details") or []
        if not isinstance(reasoning_details, list):
            return False
        return any(
            isinstance(item, dict)
            and item.get("type") == "tool"
            and bool(item.get("signature"))
            for item in reasoning_details
        )


    def _rebuild_assistant_message(self, message: Dict[str, Any]) -> Any:
        payload = {k: deepcopy(v) for k, v in message.items() if k in {"role", "content", "tool_calls", "tool_call_id", "name"}}
        provider_specific_fields = message.get("provider_specific_fields")
        if provider_specific_fields:
            payload["provider_specific_fields"] = deepcopy(provider_specific_fields)
        try:
            return LiteLLMMessage(**payload)
        except Exception:
            logger.debug("Failed to rebuild LiteLLM Message, fallback to plain dict", exc_info=True)
            return payload

    def _normalize_tool_message_for_google(self, message: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": message.get("tool_call_id"),
            "name": message.get("name"),
            "content": message.get("content", ""),
        }

    def _prompt_cache_enabled(self) -> bool:
        """是否对本模型启用 prompt caching：仅 anthropic/claude 系，且未被 env 关闭。

        env `LLM_PROMPT_CACHE=0` 可全局关闭。非 claude 模型（如 gemini）一律不打 cache_control，
        避免 provider 不认该字段而报错。
        """
        if not _is_truthy(os.getenv("LLM_PROMPT_CACHE", "1")):
            return False
        model = str(self._call_kwargs.get("model") or "").lower()
        provider = str(self._call_kwargs.get("custom_llm_provider") or "").lower()
        return "claude" in model or "anthropic" in provider

    def _maybe_mark_cache(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """给 system 消息打 ephemeral cache_control 断点。

        Anthropic 的缓存前缀顺序是 tools → system → messages，在 system 块上设一个断点即可把
        「tools + system」这段最大稳定前缀整体缓存。只标第一条 system；str/list 两种 content 都兼容。
        网关若不支持缓存，多带的 cache_control 会被忽略（实测 tokenhub 不报错），属无害透传。
        """
        if not self._prompt_cache_enabled():
            return messages
        out: List[Dict[str, Any]] = []
        marked = False
        for msg in messages:
            if (not marked) and isinstance(msg, dict) and msg.get("role") == "system":
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    msg = {**msg, "content": [
                        {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}
                    ]}
                    marked = True
                elif isinstance(content, list) and content:
                    new_content = [dict(b) if isinstance(b, dict) else b for b in content]
                    for block in reversed(new_content):
                        if isinstance(block, dict) and block.get("type") == "text":
                            block["cache_control"] = {"type": "ephemeral"}
                            marked = True
                            break
                    msg = {**msg, "content": new_content}
            out.append(msg)
        return out

    @staticmethod
    def _usage_get(usage_obj: Any, key: str) -> int:
        if usage_obj is None:
            return 0
        if isinstance(usage_obj, dict):
            return usage_obj.get(key) or 0
        return getattr(usage_obj, key, 0) or 0

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """解析 LiteLLM 响应为标准格式"""
        message = response.choices[0].message
        result = {
            "role": "assistant",
            "content": message.content or ""
        }
        
        # 处理 thinking/reasoning content（Claude extended thinking, DeepSeek reasoning 等）
        thinking_content = None
        if hasattr(message, "reasoning_content") and message.reasoning_content:
            thinking_content = message.reasoning_content
        elif hasattr(message, "thinking") and message.thinking:
            thinking_content = message.thinking
        
        # Claude extended thinking 以 thinking_blocks（含 signature）返回；多轮 tool calling 必须原样回传
        thinking_blocks = getattr(message, "thinking_blocks", None)
        if thinking_blocks is None and isinstance(message, dict):
            thinking_blocks = message.get("thinking_blocks")
        thinking_blocks = self._to_plain_data(thinking_blocks)
        if thinking_blocks:
            result["thinking_blocks"] = thinking_blocks
            if not thinking_content:
                texts = [
                    b.get("thinking") for b in thinking_blocks
                    if isinstance(b, dict) and b.get("thinking")
                ]
                if texts:
                    thinking_content = "\n".join(texts)

        if thinking_content:
            result["thinking_content"] = thinking_content

        provider_specific_fields = self._extract_provider_specific_fields(message)
        if provider_specific_fields:
            result["provider_specific_fields"] = provider_specific_fields
        
        if hasattr(message, "tool_calls") and message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": getattr(tc, "id", ""),
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
                if hasattr(tc, "function")
            ]
        
        # token 用量信息（单独字段，不会存到 messages 中）
        usage_obj = getattr(response, "usage", None)
        if usage_obj is None and isinstance(response, dict):
            usage_obj = response.get("usage")
        usage_total = 0
        if usage_obj:
            # dict 结构
            if isinstance(usage_obj, dict):
                if "total_tokens" in usage_obj:
                    usage_total = usage_obj.get("total_tokens", 0) or 0
                elif "totalTokens" in usage_obj:
                    usage_total = usage_obj.get("totalTokens", 0) or 0
                elif "prompt_tokens" in usage_obj and "completion_tokens" in usage_obj:
                    usage_total = (usage_obj.get("prompt_tokens", 0) or 0) + (usage_obj.get("completion_tokens", 0) or 0)
            else:
                # object 结构
                if hasattr(usage_obj, "total_tokens"):
                    usage_total = getattr(usage_obj, "total_tokens", 0) or 0
                elif hasattr(usage_obj, "prompt_tokens") and hasattr(usage_obj, "completion_tokens"):
                    usage_total = (getattr(usage_obj, "prompt_tokens", 0) or 0) + (getattr(usage_obj, "completion_tokens", 0) or 0)
        if usage_total:
            # Use a stable, explicit key name for total token usage
            result["total_usage"] = usage_total

        # prompt caching 用量：写缓存 cache_creation_input_tokens / 读缓存 cache_read_input_tokens
        if self._prompt_cache_enabled():
            prompt_tokens = self._usage_get(usage_obj, "prompt_tokens")
            cache_read = self._usage_get(usage_obj, "cache_read_input_tokens")
            cache_creation = self._usage_get(usage_obj, "cache_creation_input_tokens")
            result["cache_read_tokens"] = cache_read
            result["cache_creation_tokens"] = cache_creation
            if cache_read:
                tag = f"HIT 省下 {cache_read} 输入token"
            elif cache_creation:
                tag = f"WRITE 写入 {cache_creation} token"
            else:
                tag = "MISS/网关未支持"
            think_n = len(result.get("thinking_blocks") or [])
            logger.info(
                "[prompt-cache] model=%s prompt=%s cache_read=%s cache_create=%s think_blocks=%s -> %s",
                self._call_kwargs.get("model"), prompt_tokens, cache_read, cache_creation, think_n, tag,
            )

        return result

    def _clean_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清洗 messages，只保留 LLM API 需要的字段"""
        # LLM API 标准字段（thinking_blocks 用于 Claude extended thinking 的多轮 tool calling 回传）
        VALID_FIELDS = {"role", "content", "tool_calls", "tool_call_id", "name", "thinking_blocks"}
        
        cleaned = []
        pending_google_tool_reply = False
        for msg in messages:
            if not isinstance(msg, dict):
                cleaned.append(msg)
                pending_google_tool_reply = self._message_has_google_thought_signature(msg)
                continue

            if pending_google_tool_reply and msg.get("role") == "tool":
                clean_msg = self._normalize_tool_message_for_google(msg)
                cleaned.append(clean_msg)
                continue

            if msg.get("role") == "assistant" and self._message_has_google_thought_signature(msg):
                clean_msg = self._rebuild_assistant_message(msg)
            else:
                clean_msg = {k: deepcopy(v) for k, v in msg.items() if k in VALID_FIELDS}

            cleaned.append(clean_msg)
            pending_google_tool_reply = self._message_has_google_thought_signature(msg)
        return cleaned

    def completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """调用 LLM 进行文本生成或工具调用"""
        # 清洗 messages，过滤掉 usage、thinking_content 等内部字段
        clean_messages = self._clean_messages(messages)
        # 给 system 块打 prompt-cache 断点（仅 claude 系生效；清洗后做，cache_control 在 content 内不被过滤）
        clean_messages = self._maybe_mark_cache(clean_messages)
        ensure_not_cancelled()

        request = {
            **self._call_kwargs,
            "messages": clean_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        if tools:
            request["tools"] = tools
        if tool_choice is not None:
            request["tool_choice"] = tool_choice
        
        try:
            if self.provider == "lightllm" and self.debug_raw_response:
                log_lightllm_base_request(request)
            response = completion(**request)
            ensure_not_cancelled()
            if self.provider == "lightllm" and self.debug_raw_response:
                log_lightllm_base_response(
                    getattr(response, "_hidden_params", None),
                    self._to_plain_data(response),
                )
            return self._parse_response(response)
        except RunCancelledError:
            raise
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise
