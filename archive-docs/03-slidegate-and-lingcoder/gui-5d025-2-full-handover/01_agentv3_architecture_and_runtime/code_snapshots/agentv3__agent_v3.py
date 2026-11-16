"""
使用重构之后的 BaseAgent 和 BaseNode，实现主/子 Agent 与调度器
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from types import MappingProxyType
from typing import Any, Callable, Dict, List, Optional

from src.base_agent import BaseAgent, BaseNode, normalize_messages_for_llm
from src.conversation_summary import compact_conversation_context
from src.skill_registry import build_skill_registry_from_names
from agents.agentv3.core.memory_update import run_memory_update_round
from src.utils.context_token_utils import estimate_messages_tokens, summarize_message_token_usage
from src.conversation_state_v3 import (
    add_assistant_turn,
    append_delegate_message,
    attach_shared_layers,
    build_api_payload,
    complete_delegate,
    create_delegate_entry,
    finalize_todolist_projection,
    is_waiting_for_user_input,
    rebuild_compiled_messages,
    set_conversation_status,
    set_delegate_active,
    update_tool_result_content,
)
from src.utils import ctx
from agents.agentv3.prompt_templates import (
    extract_original_task,
    build_sub_finalize_prompt,
    build_reflection_finalize_prompt,
    build_subtask_instruction,
    build_reflection_instruction,
    build_reject_subtask_prompt,
)
from agents.agentv3.system_prompt_utils import build_runtime_system_prompt
try:
    from backend.replay_runtime import checkpoint_runtime_state, record_runtime_event
except Exception:
    def checkpoint_runtime_state(*args, **kwargs):
        return None

    def record_runtime_event(*args, **kwargs):
        return None


DEFAULT_MAX_CONTEXT_TOKENS = 16000
DELEGATE_REMOVED_TOOL_KEYS = frozenset({
    "create_subtask",
    "reflection",
    "todolist",
    "todolist_create",
    "todolist_append",
    "todolist_update",
    "ask_user",
})

def _extract_delegate_payload_field(payload: str, tag: str) -> str:
    match = re.search(rf"<{tag}>\s*(.*?)\s*</{tag}>", str(payload or ""), flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _parse_delegate_payload(payload: str) -> Dict[str, str]:
    raw = str(payload or "")
    return {
        "title": _extract_delegate_payload_field(raw, "title"),
        "goal": _extract_delegate_payload_field(raw, "goal"),
        "todo": _extract_delegate_payload_field(raw, "todo"),
        "relevant_files": _extract_delegate_payload_field(raw, "relevant_files"),
        "criteria": _extract_delegate_payload_field(raw, "criteria"),
        "addition": _extract_delegate_payload_field(raw, "addition"),
    }


def _parse_tool_call_arguments(arguments: Any) -> Dict[str, Any]:
    if isinstance(arguments, dict):
        return arguments
    if not isinstance(arguments, str) or not arguments.strip():
        return {}
    try:
        parsed = json.loads(arguments)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _find_tool_call_arguments(
    messages: List[Dict[str, Any]],
    *,
    tool_call_id: Optional[str],
    tool_name: str,
) -> Dict[str, Any]:
    for msg in reversed(messages):
        for tool_call in reversed(msg.get("tool_calls") or []):
            function_info = tool_call.get("function") or {}
            if tool_call_id and tool_call.get("id") != tool_call_id:
                continue
            if not tool_call_id and function_info.get("name") != tool_name:
                continue
            return _parse_tool_call_arguments(function_info.get("arguments"))
    return {}


def _compose_delegate_execution_payload(payload: str, *, locale: Optional[str] = None) -> tuple[str, Dict[str, str]]:
    raw = str(payload or "")
    parsed_payload = _parse_delegate_payload(raw)
    is_zh = str(locale or "").lower().startswith("zh")

    def _label_value(value: str, zh_prefix: str, en_prefix: str) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        if is_zh:
            return text if text.startswith(zh_prefix) else f"{zh_prefix}{text}"
        return text if text.startswith(en_prefix) else f"{en_prefix}{text}"

    labeled_parts: List[str] = []
    visible_fields = [
        ("goal", "目标：", "Goal: "),
        ("todo", "待办事项：", "Todo: "),
        ("relevant_files", "相关文件：", "Relevant files: "),
        ("criteria", "验收标准：", "Criteria: "),
        ("addition", "补充信息：", "Additional info: "),
    ]
    for key, zh_prefix, en_prefix in visible_fields:
        labeled_value = _label_value(parsed_payload[key], zh_prefix, en_prefix)
        if labeled_value:
            labeled_parts.append(labeled_value)

    structured_payload = "\n".join(labeled_parts)
    if structured_payload:
        return structured_payload, parsed_payload
    if any(f"<{tag}" in raw.lower() for tag in ("title", "goal", "todo", "relevant_files", "criteria", "addition")):
        return "", parsed_payload
    return raw, parsed_payload


def init_ctx(
    session_id,
    config_path,
    config,
    llm,
    vqa_basellm,
    audio_basellm,
    streamer=None,
    memory_user_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    user_id: Optional[int] = None,
    sandbox_manager=None,
    stop_event=None,
) -> None:
    """设置全局变量，方便tool和其他模块调用"""
    ctx.session_id = session_id
    ctx.conversation_id = conversation_id or session_id
    ctx.memory_user_id = memory_user_id
    ctx.config_path = config_path
    ctx.config = config
    ctx.llm = llm
    ctx.vqa_basellm = vqa_basellm
    ctx.audio_basellm = audio_basellm
    ctx.streamer = streamer
    ctx.user_id = user_id
    ctx.sandbox_manager = sandbox_manager
    ctx.stop_event = stop_event


def estimate_tokens(messages: List[Dict[str, Any]]) -> int:
    """估算 messages 的 tokens 数量（简单按字符数估算，1 token ≈ 4 字符）"""
    total_chars = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            # 处理多模态消息
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    total_chars += len(item["text"])
    return total_chars // 4


def count_tokens_with_counter(messages: List[Dict[str, Any]]) -> int:
    """使用实际 messages 结构统计 tokens，包含 tool_calls 等上下文字段。"""
    return estimate_messages_tokens(
        messages,
        config=ctx.config if hasattr(ctx, "config") else None,
    )


def _extract_system_prompt(messages: List[Dict[str, Any]]) -> Optional[str]:
    for msg in messages:
        if msg.get("role") == "system":
            return msg.get("content")
    return None


def _find_latest_assistant_index(messages: List[Dict[str, Any]]) -> Optional[int]:
    for idx in range(len(messages) - 1, -1, -1):
        if messages[idx].get("role") == "assistant":
            return idx
    return None


def _messages_since_latest_assistant(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    last_assistant_index = _find_latest_assistant_index(messages)
    start_index = last_assistant_index + 1 if last_assistant_index is not None else 0
    return messages[start_index:]


def _collect_tool_messages_since_latest_assistant(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return the latest tool batch produced by the most recent assistant turn."""
    return [
        msg
        for msg in _messages_since_latest_assistant(messages)
        if msg.get("role") == "tool"
    ]


def _get_runtime_max_context_tokens(default: int = DEFAULT_MAX_CONTEXT_TOKENS) -> int:
    if hasattr(ctx, "config") and ctx.config:
        return ctx.config.get("runtime", {}).get("max_context_tokens", default)
    return default



def _extract_tagged_result(content: str, tag: str) -> Optional[str]:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def _extract_delegate_visible_result(kind: str, content: str) -> str:
    text = str(content or "").strip()
    tag = "reflection" if kind == "reflection" else "subtask_result"
    extracted = _extract_tagged_result(text, tag)
    if extracted is not None:
        return extracted
    # 兜底：如果模型漏掉了外层包裹标签但生成了子标签，自动包裹
    if re.search(r"<(?:original_task|findings|result|cite_files|todo)>", text):
        return f"<{tag}>\n{text}\n</{tag}>"
    return text


def _normalize_prompt_language(value: Optional[str]) -> Optional[str]:
    raw = str(value or "").strip().lower()
    if raw.startswith("zh"):
        return "zh"
    if raw.startswith("en"):
        return "en"
    return None


def build_delegate_tools(tools: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    filtered_tools: List[Dict[str, Any]] = []
    for tool in tools or []:
        schema_name = str(((tool.get("schema") or {}).get("function") or {}).get("name") or "").strip()
        config_key = str(tool.get("config_key") or schema_name).strip()
        if schema_name in DELEGATE_REMOVED_TOOL_KEYS or config_key in DELEGATE_REMOVED_TOOL_KEYS:
            continue
        filtered_tools.append(tool)
    return filtered_tools


def _runtime_identity_payload(
    *,
    agent_role: str,
    delegate_depth: int,
    agent_name: str,
    delegate_id: Optional[str] = None,
    parent_tool_call_id: Optional[str] = None,
) -> Dict[str, Any]:
    depth = int(delegate_depth)
    identity: Dict[str, Any] = {
        "agent_role": agent_role,
        "delegate_depth": depth,
        "agent_name": agent_name,
        "is_delegate": depth > 0,
    }
    if delegate_id:
        identity["delegate_id"] = delegate_id
    if parent_tool_call_id:
        identity["parent_tool_call_id"] = parent_tool_call_id
    return identity


def _apply_runtime_identity(
    agent_state: Dict[str, Any],
    *,
    agent_role: str,
    delegate_depth: int,
    agent_name: str,
    delegate_id: Optional[str] = None,
    parent_tool_call_id: Optional[str] = None,
) -> Dict[str, Any]:
    identity = _runtime_identity_payload(
        agent_role=agent_role,
        delegate_depth=delegate_depth,
        agent_name=agent_name,
        delegate_id=delegate_id,
        parent_tool_call_id=parent_tool_call_id,
    )
    agent_state["agent_role"] = identity["agent_role"]
    agent_state["delegate_depth"] = identity["delegate_depth"]
    agent_state["agent_name"] = identity["agent_name"]
    agent_state["is_delegate"] = identity["is_delegate"]
    agent_state["runtime_identity"] = deepcopy(identity)
    if delegate_id:
        agent_state["delegate_id"] = delegate_id
    else:
        agent_state.pop("delegate_id", None)
    if parent_tool_call_id:
        agent_state["parent_tool_call_id"] = parent_tool_call_id
    else:
        agent_state.pop("parent_tool_call_id", None)
    return identity


def _collect_agent_tool_config_keys(agent: BaseAgent) -> set[str]:
    enabled_config_keys: set[str] = set()
    for node in agent.nodes.values():
        enabled_config_keys.update(
            str(config_key).strip()
            for config_key in (node.tool_config_keys or {}).values()
            if str(config_key).strip()
        )
    return enabled_config_keys


def _scope_config_to_agent_tools(config: Optional[Dict[str, Any]], agent: BaseAgent) -> Dict[str, Any]:
    scoped_config = deepcopy(config or {})
    tools_cfg = scoped_config.get("tools")
    if not isinstance(tools_cfg, dict):
        return scoped_config

    enabled_config_keys = _collect_agent_tool_config_keys(agent)
    next_tools_cfg: Dict[str, Any] = {}
    for tool_name, tool_cfg in tools_cfg.items():
        normalized_name = str(tool_name).strip()
        if isinstance(tool_cfg, dict):
            next_tool_cfg = deepcopy(tool_cfg)
            next_tool_cfg["enabled"] = normalized_name in enabled_config_keys
        else:
            next_tool_cfg = {"enabled": normalized_name in enabled_config_keys}
        next_tools_cfg[tool_name] = next_tool_cfg
    scoped_config["tools"] = next_tools_cfg
    return scoped_config


class FinalizeNode(BaseNode):
    """用于生成最终答案/子任务总结的收尾节点（不调用工具）"""

    def __init__(
        self,
        name: str,
        llm,
        prompt_builder: Callable[[str, Dict[str, Any], str], str],
        tool_schemas: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(name=name, llm=llm, tools=None)
        self.prompt_builder = prompt_builder
        self.tool_schemas = deepcopy(tool_schemas or [])

    def run(self, state: Dict[str, Any]) -> None:
        if "message_records" in state:
            rebuild_compiled_messages(state)
        messages = state.get("messages", [])
        original_task = extract_original_task(messages)
        agent_name = state.get("agent_name", "")
        prompt = self.prompt_builder(original_task, state, agent_name)

        finalize_messages = normalize_messages_for_llm(
            list(messages) + [{"role": "user", "content": prompt}]
        )
        state[self.message_key] = list(finalize_messages)

        try:
            response = self.llm.completion(
                messages=finalize_messages,
                tools=self.tool_schemas if self.tool_schemas else None,
                tool_choice="none" if self.tool_schemas else None,
            )
            state["loops"] = state.get("loops", 0) + 1
            if "global_loops" in state:
                state["global_loops"] = state.get("global_loops", 0) + 1
            self.log_response(response)
            content = response.get("content", "")
            if "message_records" in state:
                consumed_tool_call_ids = self._collect_consumed_tool_call_ids(messages)
                assistant_record, _ = add_assistant_turn(state, response, source="finalize")
                scope = self._resolve_record_scope(state)
                assistant_record["scope"] = scope
                assistant_record["consumes_tool_call_ids"] = consumed_tool_call_ids
                record_runtime_event(
                    event_type="assistant_output",
                    state=state,
                    record=assistant_record,
                    scope=scope,
                    payload={"consumes_tool_call_ids": consumed_tool_call_ids},
                )
                rebuild_compiled_messages(state)
            else:
                messages.append(response)
                state["messages"] = messages
        except Exception as e:
            error_msg = f"Finalize 调用失败: {e}"
            self.logger.error(error_msg)
            messages.append({"role": "assistant", "content": error_msg, "tool_calls": []})
            state["messages"] = messages


class MainAgent(BaseAgent):
    """
    MainAgent - 主 Agent，支持收尾模式

    特性：
      - 支持 create_subtask 工具调用
      - 以 global_loops_limit 作为强制结束判定
    """
    _init_state: Dict[str, Any] = {
        "loops": 0,
        "active_node": 'main',
        "messages": [],
        "global_tool_call_count": 0,
        "global_loops": 0,
        "global_loops_limit": None,
        "limit_reason": None,
    }
    init_state = MappingProxyType(_init_state)

    def __init__(
        self,
        name: str,
        nodes: List[BaseNode],
        entry_point: str = "start",
        max_loops: int = 20,
    ):
        super().__init__(name=name, nodes=nodes, max_loops=max_loops, entry_point=entry_point)

    def _should_stop(self, state: Dict[str, Any], current_loops: int) -> bool:
        """检查是否应该停止，支持收尾模式"""
        global_limit = state.get("global_loops_limit", self.max_loops)
        if global_limit is None:
            global_limit = self.max_loops
        global_loops = state.get("global_loops", current_loops)
        if global_limit is not None and global_loops >= global_limit:
            state['limit_reason'] = "global_loops"
            self.logger.warning(
                f"⚠️ 达到全局 loops 上限 ({global_limit})，停止主流程"
            )
            return True
        return False

    def _on_finish(self, state: Dict[str, Any]) -> None:
        """记录终止原因"""
        if state.get("limit_reason") == "global_loops":
            self.logger.warning(f"⚠️ {self.name} 达到全局 loops 上限")
        else:
            self.logger.info(f"✅ {self.name} 执行完成")

    def _next_node(self, state: Dict[str, Any], current_node: Optional[str]) -> Optional[str]:
        """处理 create_subtask、tokens 检查，以及节点跳转。"""
        if current_node is None:
            return None
        if is_waiting_for_user_input(state):
            return None
        messages = state.get("messages", [])
        if not messages:
            return current_node
        last_message = messages[-1]

        latest_tool_batch = _collect_tool_messages_since_latest_assistant(messages)
        if any(msg.get("name") in {"create_subtask", "reflection"} for msg in latest_tool_batch):
            # 最近一轮工具调用里出现了委派/反思，立即把控制权交回 AgentV3 调度器。
            return None

        self._check_and_trim_context(state)
        messages = state.get("messages", [])
        if not messages:
            return current_node
        last_message = messages[-1]

        # 终止条件：有 todo_list 时仅在全部完成后结束
        if last_message.get('role') == 'assistant':
            return None
        return current_node

    def _check_and_trim_context(self, state: Dict[str, Any]) -> None:
        """上下文超阈值时自动执行 summary offload。"""
        max_context_tokens = _get_runtime_max_context_tokens()
        if max_context_tokens <= 0:
            return

        messages = state.get("messages", [])
        usage = summarize_message_token_usage(
            messages,
            config=ctx.config if hasattr(ctx, "config") else None,
        )
        system_tokens = int(usage.get("system_tokens") or 0)
        available_after_system = max(1, max_context_tokens - system_tokens)
        current_tokens = int(usage.get("non_system_tokens") or 0)
        if current_tokens < available_after_system:
            return

        self.logger.warning(
            (
                f"⚠️ messages non-system tokens ({current_tokens}) 超过可用阈值 "
                f"({available_after_system}, system={system_tokens}, max={max_context_tokens})，触发被动裁剪"
            )
        )
        # 压缩触发点先固定下来，记忆更新内部再从完整时间派生日期。
        memory_update_time = datetime.now().astimezone()

        try:
            compact_conversation_context(
                state=state,
                llm=getattr(ctx, "llm", None),
                config=getattr(ctx, "config", None),
            )
            self.logger.info("✅ 被动裁剪完成")
            try:
                run_memory_update_round(
                    state=state,
                    source_node=self.nodes.get("main"),
                    config=getattr(ctx, "config", None),
                    runtime_lang=(state.get("runtime_control") or {}).get("current_prompt_locale"),
                    memory_update_time=memory_update_time,
                    trigger="compaction",
                )
            except Exception as exc:
                self.logger.warning("压缩后的记忆更新失败（已跳过）: %s", exc)
        except Exception as exc:
            self.logger.error(f"❌ 被动裁剪失败: {exc}")


class _DelegateAgentBase(BaseAgent):
    _init_state: Dict[str, Any] = {
        "loops": 0,
        "active_node": "main",
        "messages": [],
        "global_loops": 0,
        "global_loops_limit": None,
        "limit_reason": None,
    }
    init_state = MappingProxyType(_init_state)

    finalize_prompt_builder: Callable[[str, Dict[str, Any], str], str]
    loop_limit_reason: str
    loop_limit_label: str
    finish_loop_message: str
    context_limit_reason: Optional[str] = None
    finish_context_message: Optional[str] = None
    context_limit_label: Optional[str] = None

    def __init__(
        self,
        name: str,
        nodes: List[BaseNode],
        entry_point: str = "start",
        max_loops: int = 5,
    ):
        super().__init__(name=name, nodes=nodes, max_loops=max_loops, entry_point=entry_point)
        self._ensure_finalize_node()

    def _should_stop(self, state: Dict[str, Any], current_loops: int) -> bool:
        if current_loops >= self.max_loops:
            state["limit_reason"] = self.loop_limit_reason
            self.logger.warning(f"⚠️ 达到{self.loop_limit_label} ({self.max_loops})，进入 finalize")
            return True
        return self._should_stop_for_context_limit(state)

    def _should_stop_for_context_limit(self, state: Dict[str, Any]) -> bool:
        if not self.context_limit_reason or not self.context_limit_label:
            return False

        max_context_tokens = _get_runtime_max_context_tokens()
        if max_context_tokens <= 0:
            return False

        usage = summarize_message_token_usage(
            state.get("messages", []),
            config=ctx.config if hasattr(ctx, "config") else None,
        )
        system_tokens = int(usage.get("system_tokens") or 0)
        available_after_system = max(1, max_context_tokens - system_tokens)
        current_tokens = int(usage.get("non_system_tokens") or 0)
        if current_tokens > available_after_system:
            state["limit_reason"] = self.context_limit_reason
            self.logger.warning(
                f"⚠️ 达到{self.context_limit_label} (available={available_after_system}, system={system_tokens})，进入 finalize"
            )
            return True
        return False

    def _on_finish(self, state: Dict[str, Any]) -> None:
        limit_reason = state.get("limit_reason")
        if limit_reason == self.loop_limit_reason:
            self.logger.warning(f"⚠️ {self.name} {self.finish_loop_message}")
            return
        if self.context_limit_reason and limit_reason == self.context_limit_reason and self.finish_context_message:
            self.logger.warning(f"⚠️ {self.name} {self.finish_context_message}")
            return
        self.logger.info(f"✅ {self.name} 执行完成")

    def _ensure_finalize_node(self) -> None:
        if "finalize" in self.nodes:
            return
        if not self.nodes:
            raise RuntimeError(f"{self.__class__.__name__} 初始化失败：未提供任何节点")
        primary_node = next(iter(self.nodes.values()))
        llm = primary_node.llm
        self.nodes["finalize"] = FinalizeNode(
            name="finalize",
            llm=llm,
            prompt_builder=self.finalize_prompt_builder,
            tool_schemas=primary_node.tool_schemas,
        )

    def _next_node(self, state: Dict[str, Any], current_node: Optional[str]) -> Optional[str]:
        if current_node is None:
            return None
        if is_waiting_for_user_input(state):
            return None
        messages = state.get("messages", [])
        if not messages:
            return current_node
        if messages[-1].get("role") == "assistant":
            return None
        return current_node


class SubtaskAgent(_DelegateAgentBase):
    """
    SubtaskAgent - 子任务 Agent

    特性：
      - 不支持 create_subtask（子任务不能再创建子任务）
      - 达到 subtask_max_loops 后直接停止
    """
    # Keep this as a plain callable when accessed from the instance.
    finalize_prompt_builder = staticmethod(build_sub_finalize_prompt)
    loop_limit_reason = "subtask_max_loops"
    loop_limit_label = "子任务深度限制"
    finish_loop_message = "因深度限制而终止"
    context_limit_reason = "subtask_max_context_tokens"
    context_limit_label = "子任务上下文 tokens 上限"
    finish_context_message = "因上下文 tokens 上限而终止"


class ReflectionAgent(_DelegateAgentBase):
    """
    ReflectionAgent - 反思 Agent

    特性：
      - 不支持 reflection 工具（避免自循环）
      - 达到 max_loops 后直接停止
    """
    # Keep this as a plain callable when accessed from the instance.
    finalize_prompt_builder = staticmethod(build_reflection_finalize_prompt)
    loop_limit_reason = "reflection_max_loops"
    loop_limit_label = "反思深度限制"
    finish_loop_message = "因反思深度限制而终止"

class AgentV3(BaseAgent):
    """
    AgentV3 是主/子 Agent 协同循环，通过 while 循环执行主/子 Agent 协同循环
    调用run函数时，需要传入初始状态
    一般情况：
      main_state 包含system prompt和user message
      subtask_states 只包含system prompt

    AgentV3 只负责调度，循环控制由内部 agent 自行处理：
      - main_agent 内部处理 global_loops_limit
      - subtask_agent 内部处理 subtask_max_loops 深度限制

    跳转子agent前检查：剩余loops >= subtask_max_loops，否则拒绝跳转并返回提示
    """
    _init_state: Dict[str, Any] = {
        "active_agent": "main_agent",
        "main_state": {},
        "subtask_states": {},
        "pending_subtasks": [],
        "active_subtask_id": None,
        "subtask_counter": 0,
        "reflection_states": {},
        "pending_reflections": [],
        "active_reflection_id": None,
        "reflection_counter": 0,
        "global_loops": 0,
        "waiting_user_input": False,
    }
    init_state = MappingProxyType[str, Any](_init_state)

    def __init__(
        self,
        name: str,
        main_agent: MainAgent,
        subtask_agent: SubtaskAgent,
        reflection_agent: ReflectionAgent,
        entry_point: str = "main_agent",
        delegate_parallelism: Optional[int] = None,
        enable_parallel_delegates: bool = True,
    ):
        super().__init__(name, [main_agent, subtask_agent, reflection_agent])
        self.main_agent = main_agent
        self.subtask_agent = subtask_agent
        self.reflection_agent = reflection_agent
        self.entry_point = entry_point
        self.delegate_parallelism = delegate_parallelism
        self.enable_parallel_delegates = enable_parallel_delegates
        self.state = None
        self.input_state = None

    def reset(self) -> None:
        self.state = deepcopy(dict(AgentV3.init_state))
        for node in self.nodes.values():
            node.reset()

    def _runtime(self) -> Dict[str, Any]:
        return self.state.setdefault("runtime_control", {}) if isinstance(self.state, dict) else {}

    def _delegate_scope(self, delegate_id: str, *, kind: str) -> str:
        prefix = "reflection" if kind == "reflection" else "subtask"
        return f"{prefix}:{delegate_id}"

    def _emit_subtask_patch(self, delegate_id: Optional[str]) -> None:
        if not delegate_id or not hasattr(ctx, "streamer") or ctx.streamer is None:
            return
        runtime = self._runtime()
        patch = runtime.get("subtasks", {}).get(delegate_id)
        if not isinstance(patch, dict):
            return
        msg_id = ctx.streamer.get_msg_id()
        ctx.streamer.put_chunk(
            msg_id,
            {
                "event": "subtask_patch",
                "subtask_patch": deepcopy(patch),
            },
            is_msg=False,
        )

    def _sync_live_conversation_state(self) -> None:
        state_update_callback = getattr(ctx, "state_update_callback", None)
        if callable(state_update_callback):
            state_update_callback(self.state)

    def _emit_runtime_projection_patch(self) -> None:
        if not hasattr(ctx, "streamer") or ctx.streamer is None:
            return
        self._sync_live_conversation_state()
        payload = build_api_payload(self.state)

        runtime_msg_id = ctx.streamer.get_msg_id()
        ctx.streamer.put_chunk(
            runtime_msg_id,
            {
                "event": "runtime_control",
                "runtime_control": payload.get("runtime_control") or {},
                "todolist": payload.get("todolist") or [],
            },
            is_msg=False,
        )

        projection_msg_id = ctx.streamer.get_msg_id()
        ctx.streamer.put_chunk(
            projection_msg_id,
            {
                "event": "projection_patch",
                "projections": payload.get("projections") or {},
                "todolist": payload.get("todolist") or [],
            },
            is_msg=False,
        )

    def _build_delegate_system_prompt(
        self,
        *,
        delegate_kind: str,
        payload: str,
        skill: str = "",
        delegate_depth: int = 1,
        delegate_id: Optional[str] = None,
        parent_tool_call_id: Optional[str] = None,
    ) -> Optional[str]:
        config = getattr(ctx, "config", None)
        if not isinstance(config, dict):
            return None

        delegate_agent = self.reflection_agent if delegate_kind == "reflection" else self.subtask_agent
        scoped_config = _scope_config_to_agent_tools(config, delegate_agent)
        runtime = self._runtime()
        language_override = _normalize_prompt_language(runtime.get("current_prompt_locale"))
        runtime_identity = _runtime_identity_payload(
            agent_role=delegate_kind,
            delegate_depth=delegate_depth,
            agent_name=delegate_id or f"{delegate_kind}_agent",
            delegate_id=delegate_id,
            parent_tool_call_id=parent_tool_call_id,
        )
        skill_registry = build_skill_registry_from_names(config, skill)
        return build_runtime_system_prompt(
            scoped_config,
            query=payload,
            session_id=getattr(ctx, "session_id", None),
            memory_user_id=getattr(ctx, "memory_user_id", None),
            conversation_id=getattr(ctx, "conversation_id", None),
            deep_research_enabled=False,
            include_deep_research_mode=False,
            language_override=language_override,
            state_var_overrides={
                "enable_skill_registry": bool(skill_registry),
                "SKILL_REGISTRY": skill_registry,
                "SKILL_REGISTRY_JSON": json.dumps(skill_registry, ensure_ascii=False, indent=2),
                **runtime_identity,
                "runtime_identity": deepcopy(runtime_identity),
            },
        )

    def _auto_finalize_todolist_on_finish(self) -> bool:
        runtime = self._runtime()
        if self.state.get("waiting_user_input") or self.state.get("stop_requested"):
            return False
        if runtime.get("conversation_status") != "idle":
            return False
        changed = finalize_todolist_projection(self.state)
        if changed:
            self._emit_runtime_projection_patch()
        return changed

    def _build_runtime_state(
        self,
        template: Dict[str, Any],
        current_state: Optional[Dict[str, Any]],
        *,
        global_loops: int,
        global_loops_limit: Optional[int],
    ) -> Dict[str, Any]:
        runtime_state = deepcopy(dict(template))
        runtime_state.update(current_state or {})
        runtime_state.setdefault("global_loops", global_loops)
        runtime_state.setdefault("global_loops_limit", global_loops_limit)
        return runtime_state

    def _get_active_delegate_state(
        self,
        *,
        active_id_key: str,
        states_key: str,
        state_label: str,
    ) -> tuple[str, Dict[str, Any]]:
        state = self.state
        runtime = self._runtime()
        active_id = state.get(active_id_key) or runtime.get(active_id_key)
        delegate_state = state[states_key].get(active_id)
        if delegate_state is None:
            raise RuntimeError(f"未找到{state_label}状态: {active_id}")
        return active_id, delegate_state

    def _resolve_active_agent_runtime(self) -> tuple[BaseAgent, Dict[str, Any]]:
        active_agent = self.state["active_agent"]
        if active_agent == "main_agent":
            return self.main_agent, self.state["main_state"]
        if active_agent == "subtask_agent":
            _, delegate_state = self._get_active_delegate_state(
                active_id_key="active_subtask_id",
                states_key="subtask_states",
                state_label="子任务",
            )
            return self.subtask_agent, delegate_state
        if active_agent == "reflection_agent":
            _, delegate_state = self._get_active_delegate_state(
                active_id_key="active_reflection_id",
                states_key="reflection_states",
                state_label="反思",
            )
            return self.reflection_agent, delegate_state
        raise RuntimeError(f"当前活跃的agent不存在: {active_agent}")

    def _sync_delegate_runtime_snapshot(
        self,
        delegate_id: Optional[str],
        delegate_state: Optional[Dict[str, Any]] = None,
        *,
        emit_patch: bool = True,
    ) -> None:
        if not delegate_id:
            return
        runtime_entry = self._runtime().get("subtasks", {}).get(delegate_id)
        if runtime_entry is None:
            return
        resolved_state = delegate_state
        if resolved_state is None:
            resolved_state = (
                self.state.get("subtask_states", {}).get(delegate_id)
                or self.state.get("reflection_states", {}).get(delegate_id)
            )
        if resolved_state is not None:
            runtime_entry["messages"] = deepcopy(resolved_state.get("messages", []))
        self._sync_live_conversation_state()
        if emit_patch:
            self._emit_subtask_patch(delegate_id)

    @contextmanager
    def _capture_delegate_progress(self, delegate_id: Optional[str]):
        if not delegate_id:
            yield
            return
        had_callback = hasattr(ctx, "delegate_progress_callback")
        previous_callback = getattr(ctx, "delegate_progress_callback", None)
        ctx.delegate_progress_callback = (
            lambda delegate_state: self._sync_delegate_runtime_snapshot(
                delegate_id,
                delegate_state,
                emit_patch=True,
            )
        )
        try:
            yield
        finally:
            if had_callback:
                ctx.delegate_progress_callback = previous_callback
            elif hasattr(ctx, "delegate_progress_callback"):
                delattr(ctx, "delegate_progress_callback")

    def _extract_delegate_return_content(self, delegate_id: str, content: str) -> str:
        entry = self._runtime().get("subtasks", {}).get(delegate_id, {})
        kind = entry.get("kind") or "subtask"
        return _extract_delegate_visible_result(kind, content)

    def run(self, input_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        主/子 Agent 协同循环：
        - main_agent 遇到 create_subtask 工具调用后，切换 subtask_agent 执行子任务
        - subtask_agent 完成后，将最终 assistant message 的 content 回填为 create_subtask 的 tool 结果
        - subtask_agent 完成后重置自身 messages/state, 并支持下一次子任务

        AgentV3 只负责调度，循环控制由内部 agent 自行处理
        """
        state = deepcopy(dict(AgentV3.init_state))
        state.update(input_state)
        state.pop("subtask_state", None)
        state.pop("reflection_state", None)
        # Ensure a concrete global_loops_limit is available for loop budgeting
        if state.get("global_loops_limit") is None:
            state["global_loops_limit"] = self.main_agent.max_loops
        state.setdefault("global_loops", 0)
        state["main_state"] = self._build_runtime_state(
            self.main_agent.init_state,
            state.get("main_state"),
            global_loops=state["global_loops"],
            global_loops_limit=None,
        )
        _apply_runtime_identity(
            state["main_state"],
            agent_role="main",
            delegate_depth=0,
            agent_name="main_agent",
        )
        if not isinstance(state.get("subtask_states"), dict):
            state["subtask_states"] = {}
        if not isinstance(state.get("reflection_states"), dict):
            state["reflection_states"] = {}
        if not isinstance(state.get("pending_subtasks"), list):
            state["pending_subtasks"] = []
        if not isinstance(state.get("pending_reflections"), list):
            state["pending_reflections"] = []
        state.setdefault("active_subtask_id", None)
        state.setdefault("active_reflection_id", None)
        # 恢复委派计数器：State-V3 持久化只存 runtime_control.subtask_counter，顶层不入快照。
        # resume 时仅靠 init_state 的 0 会复位计数器 → 新子任务复用 subtask_0 覆盖已有(大纲丢失)。
        # 从 runtime_control 恢复，并对现存 subtasks 的 id 取 max 兜底。
        _rc_restore = state.get("runtime_control") or {}
        _existing_delegates = _rc_restore.get("subtasks") or {}
        for _ck, _pfx in (("subtask_counter", "subtask"), ("reflection_counter", "reflection")):
            _base = state.get(_ck) or int(_rc_restore.get(_ck) or 0)
            _used = [int(_k.rsplit("_", 1)[-1]) for _k in _existing_delegates
                     if _k.startswith(_pfx + "_") and _k.rsplit("_", 1)[-1].isdigit()]
            state[_ck] = max([int(_base)] + [_u + 1 for _u in _used])
        state.setdefault("waiting_user_input", False)
        if "message_records" in state:
            attach_shared_layers(state["main_state"], state)
            rebuild_compiled_messages(state["main_state"])
        runtime = state.setdefault("runtime_control", {})
        runtime["active_agent"] = state.get("active_agent", "main_agent")
        runtime["global_loops"] = state.get("global_loops", 0)
        runtime["global_loops_limit"] = state.get("global_loops_limit")
        runtime.setdefault("pending_subtask_ids", [])
        runtime.setdefault("subtasks", {})
        if runtime.get("conversation_status") != "waiting_user_input":
            runtime["conversation_status"] = "running"
        self.state = state
        self.input_state = MappingProxyType[str, Any](deepcopy(state))

        while state["active_agent"] is not None:
            agent, agent_state = self._resolve_active_agent_runtime()
            active_agent_name = state["active_agent"]
            delegate_id = None
            if active_agent_name == "subtask_agent":
                delegate_id = state.get("active_subtask_id")
            elif active_agent_name == "reflection_agent":
                delegate_id = state.get("active_reflection_id")

            if active_agent_name == "main_agent":
                _apply_runtime_identity(
                    agent_state,
                    agent_role="main",
                    delegate_depth=0,
                    agent_name="main_agent",
                )
            elif delegate_id:
                delegate_kind = "reflection" if active_agent_name == "reflection_agent" else "subtask"
                _apply_runtime_identity(
                    agent_state,
                    agent_role=delegate_kind,
                    delegate_depth=int(agent_state.get("delegate_depth", 1) or 1),
                    agent_name=delegate_id,
                    delegate_id=delegate_id,
                    parent_tool_call_id=agent_state.get("tool_call_id"),
                )

            agent_state["global_loops"] = state.get("global_loops", 0)
            with self._capture_delegate_progress(delegate_id):
                agent.run(agent_state)
            if active_agent_name == "main_agent" and "message_records" in state:
                attach_shared_layers(state, agent_state)
            state["global_loops"] = agent_state.get("global_loops", state.get("global_loops", 0))
            runtime["global_loops"] = state.get("global_loops", 0)
            if state["active_agent"] in {"subtask_agent", "reflection_agent"}:
                active_id = state.get("active_subtask_id") or state.get("active_reflection_id")
                self._sync_delegate_runtime_snapshot(active_id, agent_state, emit_patch=False)

            # _post_process 会处理 agent 切换
            self._post_process()

        # Final sync
        if state.get("main_state"):
            state["global_loops"] = state["main_state"].get("global_loops", state.get("global_loops", 0))
        runtime["global_loops"] = state.get("global_loops", 0)
        if runtime.get("conversation_status") == "running":
            set_conversation_status(state, "idle")
        self._auto_finalize_todolist_on_finish()
        return state

    def _post_process(self, current_node: Optional[str] = None) -> None:
        """后处理，并决定下一个agent"""
        active_agent = self.state["active_agent"]
        if active_agent == "main_agent":
            self._handle_main_agent_post_process()
            return
        if active_agent == "subtask_agent":
            self._handle_subtask_post_process()
            return
        if active_agent == "reflection_agent":
            self._handle_reflection_post_process()
            return
        if active_agent == "delegate_batch":
            return
        raise RuntimeError(f"当前活跃的agent不存在: {active_agent}")

    def _handle_main_agent_post_process(self) -> None:
        if is_waiting_for_user_input(self.state["main_state"]):
            self.state["waiting_user_input"] = True
            set_conversation_status(self.state, "waiting_user_input")
            self.state["active_agent"] = None
            self._runtime()["active_agent"] = None
            return
        main_messages = self.state["main_state"]["messages"]
        if not main_messages:
            raise RuntimeError("主任务消息为空，无法进行后处理")

        self._enqueue_reflections_from_messages(main_messages)
        self._enqueue_subtasks_from_messages(main_messages)

        if self._dispatch_pending_work():
            return

        last_message = main_messages[-1]
        if last_message["role"] == "assistant":
            set_conversation_status(self.state, "idle")
            self.state["active_agent"] = None
            self._runtime()["active_agent"] = None
            return
        if last_message["role"] == "tool" and last_message.get("name") == "create_subtask":
            self.state["active_agent"] = "subtask_agent"
            self._runtime()["active_agent"] = "subtask_agent"
            return
        if last_message["role"] == "tool":
            self.logger.warning(f"⚠️ main_agent 因达到上限而退出，最后消息是 tool: {last_message.get('name')}")
            set_conversation_status(self.state, "idle")
            self.state["active_agent"] = None
            self._runtime()["active_agent"] = None
            return
        self.logger.warning(f"⚠️ main_agent 退出，最后消息角色: {last_message['role']}")
        set_conversation_status(self.state, "idle")
        self.state["active_agent"] = None
        self._runtime()["active_agent"] = None

    def _handle_subtask_post_process(self) -> None:
        active_subtask_id, subtask_state = self._get_active_delegate_state(
            active_id_key="active_subtask_id",
            states_key="subtask_states",
            state_label="子任务",
        )
        last_message = subtask_state["messages"][-1]
        runtime_entry = self._runtime().get("subtasks", {}).get(active_subtask_id)
        if runtime_entry is not None:
            runtime_entry["messages"] = deepcopy(subtask_state.get("messages", []))

        if last_message["role"] == "assistant":
            content = last_message.get("content", "")
            has_result_tag = self._extract_subtask_result(content) is not None
            if has_result_tag:
                self.logger.info(f"✅ 子任务 {active_subtask_id} 成功完成（检测到 <subtask_result> 标签）")
            else:
                self.logger.warning(f"⚠️ 子任务 {active_subtask_id} 结束但未检测到 <subtask_result> 标签，可能未按要求输出结果")
            subtask_state["is_success"] = has_result_tag
            self._complete_delegate_run(
                active_id_key="active_subtask_id",
                states_key="subtask_states",
                delegate_id=active_subtask_id,
                last_message=last_message,
            )
            if self.state.get("active_agent") != "delegate_batch" and not self._runtime().get("running_delegate_ids"):
                self._activate_main_agent()
            return

        error_role = last_message.get("role", "unknown")
        self.logger.error(f"❌ 子任务 {active_subtask_id} 异常结束，最后消息不是 assistant: {error_role}")
        subtask_state["is_success"] = False
        subtask_state["error"] = f"Subtask ended with non-assistant message: {error_role}"
        error_message = {
            "role": "assistant",
            "content": (
                "<subtask_result>\n"
                "<original_task>Error recovery</original_task>\n"
                "<findings>无</findings>\n"
                "<result>子任务执行失败</result>\n"
                "<cite_files></cite_files>\n"
                "<todo>请主线程检查该子任务并决定是否重试</todo>\n"
                "</subtask_result>"
            ),
        }
        self._complete_delegate_run(
            active_id_key="active_subtask_id",
            states_key="subtask_states",
            delegate_id=active_subtask_id,
            last_message=error_message,
        )
        if self.state.get("active_agent") != "delegate_batch":
            self._dispatch_pending_work()

    def _handle_reflection_post_process(self) -> None:
        active_reflection_id, reflection_state = self._get_active_delegate_state(
            active_id_key="active_reflection_id",
            states_key="reflection_states",
            state_label="反思",
        )
        last_message = reflection_state["messages"][-1]
        runtime_entry = self._runtime().get("subtasks", {}).get(active_reflection_id)
        if runtime_entry is not None:
            runtime_entry["messages"] = deepcopy(reflection_state.get("messages", []))
        if last_message["role"] != "assistant":
            raise RuntimeError(f"反思完成时，最后一个消息不是assistant: {last_message}")

        content = last_message.get("content", "")
        has_result_tag = self._extract_reflection_result(content) is not None
        if has_result_tag:
            self.logger.info(f"✅ 反思 {active_reflection_id} 完成（检测到 <reflection> 标签）")
        else:
            self.logger.warning(f"⚠️ 反思 {active_reflection_id} 结束但未检测到 <reflection> 标签")
        reflection_state["is_success"] = has_result_tag
        self._complete_delegate_run(
            active_id_key="active_reflection_id",
            states_key="reflection_states",
            delegate_id=active_reflection_id,
            last_message=last_message,
        )
        if self.state.get("active_agent") != "delegate_batch" and not self._runtime().get("running_delegate_ids"):
            self._activate_main_agent()

    def _activate_main_agent(self) -> None:
        self.state["active_agent"] = "main_agent"
        self.state["main_state"]["active_node"] = "main"
        runtime = self._runtime()
        runtime["active_agent"] = "main_agent"
        runtime["active_subtask_id"] = None
        runtime["running_delegate_ids"] = []

    def _write_tool_result_back_to_main(self, tool_call_id: Optional[str], content: str) -> None:
        if not tool_call_id:
            return
        next_payload = None
        if "message_records" in self.state:
            for record in reversed(self.state.get("message_records", [])):
                if record.get("type") != "tool_result" or record.get("tool_call_id") != tool_call_id:
                    continue
                current_payload = deepcopy(record.get("payload") or {})
                previous_result = current_payload.get("result")
                if previous_result != content:
                    if previous_result not in (None, "", content) and "original_result" not in current_payload:
                        current_payload["original_result"] = previous_result
                    current_payload["result"] = content
                next_payload = current_payload
                break
        for msg in reversed(self.state["main_state"]["messages"]):
            if msg.get("role") == "tool" and msg.get("tool_call_id") == tool_call_id:
                msg["content"] = content
                if "message_records" in self.state:
                    update_tool_result_content(
                        self.state,
                        tool_call_id=tool_call_id,
                        content=content,
                        payload=next_payload,
                    )
                return

    def _complete_delegate_run(
        self,
        *,
        active_id_key: str,
        states_key: str,
        delegate_id: str,
        last_message: Dict[str, Any],
    ) -> None:
        delegate_state = self.state[states_key].get(delegate_id)
        tool_call_id = delegate_state.get("tool_call_id") if delegate_state else None
        raw_content = str(last_message.get("content", "") or "")
        visible_content = self._extract_delegate_return_content(delegate_id, raw_content)
        runtime = self._runtime()
        runtime_entry = runtime.get("subtasks", {}).get(delegate_id) or {}
        delegate_kind = str(runtime_entry.get("kind") or ("reflection" if states_key == "reflection_states" else "subtask"))
        delegate_scope = self._delegate_scope(delegate_id, kind=delegate_kind)
        self._write_tool_result_back_to_main(tool_call_id, visible_content)
        summary_record = complete_delegate(
            self.state,
            delegate_id=delegate_id,
            status="succeeded" if "Error:" not in raw_content else "failed",
            content=visible_content,
            raw_content=raw_content,
        )
        if isinstance(summary_record, dict):
            summary_record["scope"] = delegate_scope
            record_runtime_event(
                event_type="subtask_finish" if delegate_kind == "subtask" else "reflection_finish",
                state=self.state,
                record=summary_record,
                tool_call_id=tool_call_id,
                subtask_id=delegate_id,
                scope=delegate_scope,
                payload={
                    "delegate_kind": delegate_kind,
                    "status": summary_record.get("payload", {}).get("subtask_status"),
                    "parent_tool_call_id": tool_call_id,
                },
            )
            checkpoint_runtime_state(
                checkpoint_kind="subtask_finish" if delegate_kind == "subtask" else "reflection_finish",
                state=self.state,
            )
        running_delegate_ids = runtime.get("running_delegate_ids")
        if isinstance(running_delegate_ids, list):
            runtime["running_delegate_ids"] = [item for item in running_delegate_ids if item != delegate_id]
        remaining_running = runtime.get("running_delegate_ids") or []
        runtime["active_subtask_id"] = remaining_running[0] if remaining_running else None
        runtime["pending_subtask_ids"] = list(runtime.get("pending_delegate_ids") or [])
        self._emit_subtask_patch(delegate_id)
        if "message_records" in self.state["main_state"]:
            rebuild_compiled_messages(self.state["main_state"])
        self.state[active_id_key] = None

    def _dispatch_pending_work(self) -> bool:
        """将当前轮次的全部 delegate 提升为 running，并按配置选择并发或串行执行。"""
        had_pending_work = bool(self.state.get("pending_reflections") or self.state.get("pending_subtasks"))
        delegate_ids = self._promote_pending_delegates_to_running()
        if not delegate_ids:
            return had_pending_work
        if not self.enable_parallel_delegates or len(delegate_ids) <= 1:
            return self._run_delegate_batch_sequential(delegate_ids)
        return self._run_delegate_batch_parallel(delegate_ids)

    def _promote_pending_delegates_to_running(self) -> List[str]:
        runtime = self._runtime()
        subtasks = runtime.get("subtasks", {})
        delegate_ids: List[str] = []

        while self.state.get("pending_reflections"):
            delegate_ids.append(self.state["pending_reflections"].pop(0))
        while self.state.get("pending_subtasks"):
            delegate_ids.append(self.state["pending_subtasks"].pop(0))

        if not delegate_ids:
            return []

        requested_delegate_ids = list(delegate_ids)
        delegate_ids = self._filter_delegate_ids_by_loop_budget(delegate_ids)
        if not delegate_ids:
            runtime["pending_delegate_ids"] = [
                delegate_id
                for delegate_id in runtime.get("pending_delegate_ids", [])
                if delegate_id not in requested_delegate_ids
            ]
            runtime["pending_subtask_ids"] = list(runtime.get("pending_delegate_ids") or [])
            self._activate_main_agent()
            return []

        runtime["pending_delegate_ids"] = [
            delegate_id
            for delegate_id in runtime.get("pending_delegate_ids", [])
            if delegate_id not in requested_delegate_ids
        ]
        runtime["pending_subtask_ids"] = list(runtime["pending_delegate_ids"])
        runtime["running_delegate_ids"] = list(delegate_ids)
        runtime["active_subtask_id"] = delegate_ids[0] if delegate_ids else None
        self.state["active_subtask_id"] = None
        self.state["active_reflection_id"] = None

        for delegate_id in delegate_ids:
            entry = subtasks.get(delegate_id)
            if isinstance(entry, dict):
                entry["status"] = "running"
            self._emit_subtask_patch(delegate_id)

        self.state["active_agent"] = "delegate_batch"
        runtime["active_agent"] = "delegate_batch"
        return delegate_ids

    def _delegate_budget_requirement(self, delegate_id: str) -> int:
        delegate_agent = self.reflection_agent if delegate_id.startswith("reflection_") else self.subtask_agent
        return max(1, int(delegate_agent.max_loops or 1))

    def _delegate_state_key(self, delegate_id: str) -> str:
        return "reflection_states" if delegate_id.startswith("reflection_") else "subtask_states"

    def _reject_delegate_for_loop_budget(
        self,
        delegate_id: str,
        *,
        remaining_loops: int,
        required_loops: int,
        rejected_count: int,
    ) -> None:
        states_key = self._delegate_state_key(delegate_id)
        delegate_state = self.state.get(states_key, {}).get(delegate_id)
        reject_msg = build_reject_subtask_prompt(
            remaining_loops=max(remaining_loops, 0),
            required_loops=required_loops,
            rejected_count=rejected_count,
        )
        if delegate_state:
            self._write_tool_result_back_to_main(delegate_state.get("tool_call_id"), reject_msg)
            delegate_state["is_rejected"] = True
            delegate_state["reject_reason"] = "insufficient_loops"
        runtime_entry = self._runtime().get("subtasks", {}).get(delegate_id)
        if runtime_entry is not None:
            runtime_entry["status"] = "rejected"
            runtime_entry["error"] = "insufficient_loops"
            runtime_entry["result"] = reject_msg
            self._emit_subtask_patch(delegate_id)

    def _filter_delegate_ids_by_loop_budget(self, delegate_ids: List[str]) -> List[str]:
        global_limit = self.state.get("global_loops_limit")
        if global_limit is None:
            return delegate_ids
        remaining_budget = int(global_limit) - int(self.state.get("global_loops", 0) or 0)
        runnable_ids: List[str] = []
        rejected: List[tuple[str, int, int]] = []
        for delegate_id in delegate_ids:
            required_loops = self._delegate_budget_requirement(delegate_id)
            if remaining_budget >= required_loops:
                runnable_ids.append(delegate_id)
                remaining_budget -= required_loops
                continue
            rejected.append((delegate_id, remaining_budget, required_loops))

        rejected_count = len(rejected)
        for delegate_id, remaining_loops, required_loops in rejected:
            self._reject_delegate_for_loop_budget(
                delegate_id,
                remaining_loops=remaining_loops,
                required_loops=required_loops,
                rejected_count=rejected_count,
            )
        return runnable_ids

    def _run_delegate_batch_parallel(self, delegate_ids: List[str]) -> bool:
        if not delegate_ids:
            return False

        configured_parallelism = self.delegate_parallelism
        if configured_parallelism is None:
            runtime_parallelism = (self._runtime().get("delegate_parallelism") if isinstance(self._runtime(), dict) else None)
            configured_parallelism = runtime_parallelism
        max_workers = max(1, min(len(delegate_ids), int(configured_parallelism or len(delegate_ids))))
        ctx_snapshot = self._snapshot_ctx_fields()
        results_by_id: Dict[str, Dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_delegate = {
                executor.submit(self._run_delegate_in_worker, delegate_id, ctx_snapshot): delegate_id
                for delegate_id in delegate_ids
            }
            for future in as_completed(future_to_delegate):
                delegate_id = future_to_delegate[future]
                try:
                    results_by_id[delegate_id] = future.result()
                except Exception as exc:
                    self.logger.error("并发 delegate 执行失败 %s: %s", delegate_id, exc, exc_info=True)
                    results_by_id[delegate_id] = self._build_failed_delegate_result(delegate_id, exc)

        batch_max_global_loops = self.state.get("global_loops", 0)
        for delegate_id in delegate_ids:
            result = results_by_id[delegate_id]
            states_key = result["states_key"]
            active_id_key = result["active_id_key"]
            delegate_state = deepcopy(result["delegate_state"])
            self.state[states_key][delegate_id] = delegate_state
            batch_max_global_loops = max(
                batch_max_global_loops,
                int(delegate_state.get("global_loops", batch_max_global_loops) or 0),
            )
            self._sync_delegate_runtime_snapshot(delegate_id, delegate_state, emit_patch=False)
            self._complete_delegate_run(
                active_id_key=active_id_key,
                states_key=states_key,
                delegate_id=delegate_id,
                last_message=result["last_message"],
            )

        self.state["global_loops"] = batch_max_global_loops
        self.state["main_state"]["global_loops"] = batch_max_global_loops
        self._activate_main_agent()
        return True

    def _run_delegate_batch_sequential(self, delegate_ids: List[str]) -> bool:
        if not delegate_ids:
            return False

        batch_max_global_loops = self.state.get("global_loops", 0)
        for delegate_id in delegate_ids:
            try:
                result = self._run_delegate_in_worker(delegate_id)
            except Exception as exc:
                self.logger.error("串行 delegate 执行失败 %s: %s", delegate_id, exc, exc_info=True)
                result = self._build_failed_delegate_result(delegate_id, exc)
            states_key = result["states_key"]
            active_id_key = result["active_id_key"]
            delegate_state = deepcopy(result["delegate_state"])
            self.state[states_key][delegate_id] = delegate_state
            batch_max_global_loops = max(
                batch_max_global_loops,
                int(delegate_state.get("global_loops", batch_max_global_loops) or 0),
            )
            self._sync_delegate_runtime_snapshot(delegate_id, delegate_state, emit_patch=False)
            self._complete_delegate_run(
                active_id_key=active_id_key,
                states_key=states_key,
                delegate_id=delegate_id,
                last_message=result["last_message"],
            )

        self.state["global_loops"] = batch_max_global_loops
        self.state["main_state"]["global_loops"] = batch_max_global_loops
        self._activate_main_agent()
        return True

    def _snapshot_ctx_fields(self) -> Dict[str, Any]:
        snapshot: Dict[str, Any] = {}
        for field_name in (
            "session_id",
            "conversation_id",
            "memory_user_id",
            "config_path",
            "config",
            "llm",
            "vqa_basellm",
            "audio_basellm",
            "streamer",
            "user_id",
            "sandbox_manager",
            "stop_event",
            "state_update_callback",
            "delegate_progress_callback",
            "result_dir",
        ):
            if hasattr(ctx, field_name):
                snapshot[field_name] = getattr(ctx, field_name)
        return snapshot

    def _apply_ctx_snapshot(self, snapshot: Optional[Dict[str, Any]]) -> None:
        for field_name, field_value in (snapshot or {}).items():
            setattr(ctx, field_name, field_value)

    def _run_delegate_in_worker(self, delegate_id: str, ctx_snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._apply_ctx_snapshot(ctx_snapshot)
        delegate_kind = "reflection" if delegate_id.startswith("reflection_") else "subtask"
        states_key = "reflection_states" if delegate_kind == "reflection" else "subtask_states"
        active_id_key = "active_reflection_id" if delegate_kind == "reflection" else "active_subtask_id"
        delegate_template = self.reflection_agent if delegate_kind == "reflection" else self.subtask_agent
        delegate_agent = deepcopy(delegate_template)
        source_state = self.state[states_key][delegate_id]
        delegate_state = deepcopy(source_state)
        _apply_runtime_identity(
            delegate_state,
            agent_role=delegate_kind,
            delegate_depth=int(delegate_state.get("delegate_depth", 1) or 1),
            agent_name=delegate_id,
            delegate_id=delegate_id,
            parent_tool_call_id=delegate_state.get("tool_call_id"),
        )
        delegate_state["global_loops"] = self.state.get("global_loops", 0)
        with self._capture_delegate_progress(delegate_id):
            delegate_agent.run(delegate_state)
        last_message = (delegate_state.get("messages") or [{"role": "assistant", "content": ""}])[-1]
        return {
            "delegate_id": delegate_id,
            "states_key": states_key,
            "active_id_key": active_id_key,
            "delegate_state": delegate_state,
            "last_message": last_message,
        }

    def _build_failed_delegate_result(self, delegate_id: str, exc: Exception) -> Dict[str, Any]:
        delegate_kind = "reflection" if delegate_id.startswith("reflection_") else "subtask"
        states_key = "reflection_states" if delegate_kind == "reflection" else "subtask_states"
        active_id_key = "active_reflection_id" if delegate_kind == "reflection" else "active_subtask_id"
        failed_state = deepcopy(self.state[states_key].get(delegate_id) or {})
        failed_state["is_success"] = False
        failed_state["error"] = str(exc)
        failed_state["global_loops"] = failed_state.get("global_loops", self.state.get("global_loops", 0))
        if delegate_kind == "reflection":
            content = (
                "<reflection>\n"
                "<original_task>Error recovery</original_task>\n"
                "<findings>无</findings>\n"
                f"<result>反思执行失败：{exc}</result>\n"
                "<cite_files></cite_files>\n"
                "<todo>请主线程检查该反思任务并决定是否重试</todo>\n"
                "</reflection>"
            )
        else:
            content = (
                "<subtask_result>\n"
                f"Error: Subtask execution failed: {exc}\n"
                "</subtask_result>"
            )
        failed_state.setdefault("messages", []).append({"role": "assistant", "content": content})
        return {
            "delegate_id": delegate_id,
            "states_key": states_key,
            "active_id_key": active_id_key,
            "delegate_state": failed_state,
            "last_message": {"role": "assistant", "content": content},
        }

    def _reject_pending_delegate_work(
        self,
        *,
        pending_key: str,
        states_key: str,
        reject_msg: str,
    ) -> List[str]:
        rejected_ids = self.state[pending_key].copy()
        self.state[pending_key] = []
        for delegate_id in rejected_ids:
            delegate_state = self.state[states_key].get(delegate_id)
            if not delegate_state:
                continue
            self._write_tool_result_back_to_main(delegate_state.get("tool_call_id"), reject_msg)
            delegate_state["is_rejected"] = True
            delegate_state["reject_reason"] = "insufficient_loops"
            runtime_entry = self._runtime().get("subtasks", {}).get(delegate_id)
            if runtime_entry is not None:
                runtime_entry["status"] = "rejected"
                runtime_entry["error"] = "insufficient_loops"
                runtime_entry["result"] = reject_msg
                self._emit_subtask_patch(delegate_id)
        self._activate_main_agent()
        return rejected_ids

    def _enqueue_subtasks_from_messages(self, messages: List[Dict[str, Any]]) -> None:
        self._enqueue_delegate_tasks(
            messages,
            tool_name="create_subtask",
            counter_key="subtask_counter",
            delegate_init_state=dict(self.subtask_agent.init_state),
            states_key="subtask_states",
            pending_key="pending_subtasks",
            delegate_prefix="subtask",
            instruction_builder=build_subtask_instruction,
            payload_key="current_subtask",
        )

    def _enqueue_reflections_from_messages(self, messages: List[Dict[str, Any]]) -> None:
        self._enqueue_delegate_tasks(
            messages,
            tool_name="reflection",
            counter_key="reflection_counter",
            delegate_init_state=dict(self.reflection_agent.init_state),
            states_key="reflection_states",
            pending_key="pending_reflections",
            delegate_prefix="reflection",
            instruction_builder=build_reflection_instruction,
            payload_key="current_reflection",
        )

    def _enqueue_delegate_tasks(
        self,
        messages: List[Dict[str, Any]],
        *,
        tool_name: str,
        counter_key: str,
        delegate_init_state: Dict[str, Any],
        states_key: str,
        pending_key: str,
        delegate_prefix: str,
        instruction_builder: Callable[[str], str],
        payload_key: str,
    ) -> None:
        state = self.state
        for msg in _messages_since_latest_assistant(messages):
            if msg.get("role") != "tool" or msg.get("name") != tool_name:
                continue
            tool_call_id = msg.get("tool_call_id")
            if tool_call_id and any(
                item.get("parent_tool_call_id") == tool_call_id
                for item in self._runtime().get("subtasks", {}).values()
            ):
                continue

            delegate_id = f"{delegate_prefix}_{state[counter_key]}"
            state[counter_key] += 1
            delegate_state = self._build_runtime_state(
                delegate_init_state,
                None,
                global_loops=state.get("global_loops", 0),
                global_loops_limit=state.get("global_loops_limit"),
            )
            delegate_state["messages"] = []

            payload = msg.get("content", "")
            resolved_payload, parsed_payload = _compose_delegate_execution_payload(
                payload,
                locale=(self._runtime().get("current_prompt_locale") or ""),
            )
            tool_args = _find_tool_call_arguments(messages, tool_call_id=tool_call_id, tool_name=tool_name)
            skill = str(tool_args.get("skill") or "").strip()
            kind = "reflection" if delegate_prefix == "reflection" else "subtask"
            parent_depth = int((state.get("main_state") or {}).get("delegate_depth", 0) or 0)
            delegate_depth = parent_depth + 1
            delegate_system_prompt = self._build_delegate_system_prompt(
                delegate_kind=kind,
                payload=resolved_payload,
                skill=skill,
                delegate_depth=delegate_depth,
                delegate_id=delegate_id,
                parent_tool_call_id=tool_call_id,
            )
            if delegate_system_prompt:
                delegate_state["messages"].append({"role": "system", "content": delegate_system_prompt})
            user_instruction = instruction_builder(resolved_payload)
            delegate_state["messages"].append({"role": "user", "content": user_instruction})
            delegate_state["active_node"] = "main"
            delegate_state["agent_name"] = delegate_id
            delegate_state["tool_call_id"] = tool_call_id
            delegate_state[payload_key] = resolved_payload
            runtime_identity = _apply_runtime_identity(
                delegate_state,
                agent_role=kind,
                delegate_depth=delegate_depth,
                agent_name=delegate_id,
                delegate_id=delegate_id,
                parent_tool_call_id=tool_call_id,
            )
            state[states_key][delegate_id] = delegate_state
            state[pending_key].append(delegate_id)
            entry = create_delegate_entry(
                self.state,
                kind=kind,
                instruction=resolved_payload,
                parent_tool_call_id=tool_call_id,
                title=parsed_payload["title"] or resolved_payload[:80],
                delegate_id=delegate_id,
            )
            entry["agent_role"] = kind
            entry["delegate_depth"] = runtime_identity["delegate_depth"]
            entry["runtime_identity"] = deepcopy(runtime_identity)
            entry["messages"] = deepcopy(delegate_state["messages"])
            delegate_scope = self._delegate_scope(delegate_id, kind=kind)
            record_runtime_event(
                event_type="subtask_dispatch" if kind == "subtask" else "reflection_dispatch",
                state=self.state,
                tool_call_id=tool_call_id,
                subtask_id=delegate_id,
                scope=delegate_scope,
                payload={
                    "delegate_id": delegate_id,
                    "delegate_kind": kind,
                    "instruction": resolved_payload,
                    "title": parsed_payload["title"] or resolved_payload[:80],
                    "parent_tool_call_id": tool_call_id,
                },
            )
            checkpoint_runtime_state(
                checkpoint_kind="subtask_dispatch" if kind == "subtask" else "reflection_dispatch",
                state=self.state,
            )
            self._emit_subtask_patch(delegate_id)

    def _extract_subtask_result(self, content: str) -> Optional[str]:
        """从内容中提取 <subtask_result> 标签内的内容；若漏掉外层但有子标签也算有效。"""
        extracted = _extract_tagged_result(content, "subtask_result")
        if extracted is not None:
            return extracted
        if re.search(r"<(?:original_task|findings|result|cite_files|todo)>", content):
            return content
        return None

    def _extract_reflection_result(self, content: str) -> Optional[str]:
        """从内容中提取 <reflection> 标签内的内容；若漏掉外层但有子标签也算有效。"""
        extracted = _extract_tagged_result(content, "reflection")
        if extracted is not None:
            return extracted
        if re.search(r"<(?:original_task|findings|result|cite_files|todo)>", content):
            return content
        return None
