"""BaseAgent - 简单的 while 循环执行器"""
import logging
import json
import os
from copy import deepcopy
import inspect
from types import MappingProxyType
from typing import Any, Callable, Dict, List, Optional

from backend.replay_runtime import checkpoint_runtime_state, record_runtime_event
from src.base_llm import BaseLLM
from src.conversation_state_v3 import (
    add_assistant_turn,
    add_tool_result,
    add_user_input,
    build_api_payload,
    get_runtime_pending_ask_user_payload,
    is_waiting_for_user_input,
    mark_waiting_for_user_input,
    rebuild_compiled_messages,
)
from src.utils.tool_utils import _validate_tool_calls
from src.utils import ctx
from src.utils.cancellation import RunCancelledError, ensure_not_cancelled, is_stop_requested

# ---- Reasoning nudge (data-gen experiment) ----------------------------------
# After each tool-result round, insert a user text message prompting the model to
# think thoroughly before its next action, so every turn carries fresh (signed)
# extended thinking. Gated by env:
#   REASONING_NUDGE=1            -> locale-matched default text (zh/en)
#   REASONING_NUDGE="<text>"     -> custom nudge text
#   unset / 0 / false            -> disabled (production default)
_REASONING_NUDGE_EN = (
    "Please reason carefully and thoroughly about the next action to take, and then take it. "
    "Do not skip any detail in your reasoning."
)
_REASONING_NUDGE_ZH = "请先仔细、透彻地思考下一步要做什么，再执行。思考过程中不要跳过任何细节。"


def _nudge_has_cjk(text: str) -> bool:
    return any("一" <= ch <= "鿿" for ch in text)


def _resolve_reasoning_nudge(messages: List[Dict[str, Any]]) -> Optional[tuple]:
    """Return (nudge_text, locale) when the reasoning nudge is enabled, else None.

    The default text is locale-matched to the conversation (first user message) so an
    English nudge cannot flip a Chinese conversation's reply language (the output rules
    follow the latest user input's language)."""
    raw = os.environ.get("REASONING_NUDGE", "").strip()
    if not raw or raw.lower() in ("0", "false", "off", "no"):
        return None
    if raw.lower() not in ("1", "true", "on", "yes"):
        return raw, ("zh-CN" if _nudge_has_cjk(raw) else "en-US")
    for m in messages:
        if m.get("role") == "user":
            if _nudge_has_cjk(str(m.get("content") or "")[:600]):
                return _REASONING_NUDGE_ZH, "zh-CN"
            return _REASONING_NUDGE_EN, "en-US"
    return _REASONING_NUDGE_EN, "en-US"


_RUNTIME_IDENTITY_TOOL_CONFIG_KEYS = {
    "read",
    "write",
    "edit",
    "glob",
    "resource_search",
    "resource-search",
    "memory_search",
    "memory-search",
}


def _to_llm_message(message: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {
        "role": message.get("role"),
        "content": message.get("content", ""),
    }
    for key in ("name", "tool_call_id", "tool_calls", "provider_specific_fields", "thinking_content", "thinking_blocks"):
        if key in message:
            normalized[key] = deepcopy(message.get(key))
    return normalized


def normalize_messages_for_llm(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized_messages: List[Dict[str, Any]] = []
    for raw_message in messages or []:
        if not isinstance(raw_message, dict):
            continue
        message = _to_llm_message(raw_message)
        role = str(message.get("role") or "").strip()
        if role == "user" and normalized_messages and normalized_messages[-1].get("role") == "user":
            previous_content = str(normalized_messages[-1].get("content") or "").strip()
            current_content = str(message.get("content") or "").strip()
            if previous_content and current_content:
                normalized_messages[-1]["content"] = f"{previous_content}\n\n{current_content}"
            elif current_content:
                normalized_messages[-1]["content"] = current_content
            continue
        normalized_messages.append(message)
    return normalized_messages


class BaseNode:
    """
    无状态节点基类，管理 LLM 交互和工具分发
    内部不建议有循环调用LLM的逻辑
    输入state，进行inplace修改
    """
    def __init__(
        self,
        name: str,
        llm: BaseLLM,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_retries: int = 3,
        message_key: str = "messages",
    ):
        self.name = name
        self.llm = llm
        self.max_retries = max_retries
        self.message_key = message_key
        self.tool_schemas: List[Dict[str, Any]] = []
        self.tool_map: Dict[str, Callable] = {}
        self.tool_config_keys: Dict[str, str] = {}
        self.logger = logging.getLogger(f"{self.name}")
        
        if tools:
            for tool in tools:
                schema = tool["schema"]
                func = tool["function"]
                self.tool_schemas.append(schema)
                tool_name = schema.get("function", {}).get("name", "")
                if tool_name:
                    self.tool_map[tool_name] = func
                    self.tool_config_keys[tool_name] = tool.get("config_key", tool_name)

    def log_response(self, response: Dict[str, Any]) -> None:
        """记录 LLM 响应内容"""
        content = response.get("content", "")
        if content:
            self.logger.info(f"✅ content: {content}")
            
        if response.get("tool_calls"):
            tool_names = [tc.get("function", {}).get("name", "") for tc in response["tool_calls"]]
            self.logger.info(f"🔧 工具调用: {tool_names}")

    def _emit_stream_message(self, message: Dict[str, Any]) -> None:
        """将消息输出到 streamer（用于 backend 通信）"""
        if getattr(ctx, "suppress_stream", False):
            return
        if not hasattr(ctx, "streamer") or ctx.streamer is None:
            return
        try:
            msg_id = ctx.streamer.get_msg_id()
            ctx.streamer.put_chunk(msg_id, message, is_msg=True)
        except Exception as e:
            self.logger.warning(f"streamer 输出失败: {e}")

    def _emit_structured_state_chunks(self, state: Dict[str, Any], *records: Dict[str, Any]) -> None:
        if getattr(ctx, "suppress_stream", False):
            return
        if not hasattr(ctx, "streamer") or ctx.streamer is None:
            return
        if "message_records" not in state:
            return
        try:
            state_update_callback = getattr(ctx, "state_update_callback", None)
            if callable(state_update_callback):
                state_update_callback(state)
            for record in records:
                if not record:
                    continue
                msg_id = ctx.streamer.get_msg_id()
                ctx.streamer.put_chunk(
                    msg_id,
                    {
                        "event": "timeline_record",
                        "timeline_record": record,
                    },
                    is_msg=False,
                )
            payload = build_api_payload(state)
            msg_id = ctx.streamer.get_msg_id()
            ctx.streamer.put_chunk(
                msg_id,
                {
                    "event": "runtime_control",
                    "runtime_control": payload.get("runtime_control") or {},
                    "todolist": payload.get("todolist") or [],
                },
                is_msg=False,
            )
            msg_id = ctx.streamer.get_msg_id()
            ctx.streamer.put_chunk(
                msg_id,
                {
                    "event": "projection_patch",
                    "projections": payload.get("projections") or {},
                    "todolist": payload.get("todolist") or [],
                },
                is_msg=False,
            )
        except Exception as e:
            self.logger.warning(f"structured streamer 输出失败: {e}")

    def _emit_delegate_progress(self, state: Dict[str, Any]) -> None:
        """通知外层调度器同步 delegate 运行进度。"""
        callback = getattr(ctx, "delegate_progress_callback", None)
        if not callable(callback):
            return
        try:
            callback(state)
        except Exception as e:
            self.logger.warning(f"delegate progress 输出失败: {e}")

    def _resolve_record_scope(self, state: Dict[str, Any]) -> str:
        agent_name = str(state.get("agent_name") or "").strip()
        if agent_name.startswith("subtask_"):
            return f"subtask:{agent_name}"
        if agent_name.startswith("reflection_"):
            return f"reflection:{agent_name}"
        return "main"

    def _collect_consumed_tool_call_ids(self, messages: List[Dict[str, Any]]) -> List[str]:
        last_assistant_index = None
        for idx in range(len(messages) - 1, -1, -1):
            if messages[idx].get("role") == "assistant":
                last_assistant_index = idx
                break
        start_index = last_assistant_index + 1 if last_assistant_index is not None else 0
        consumed: List[str] = []
        seen: set[str] = set()
        for msg in messages[start_index:]:
            if msg.get("role") != "tool":
                continue
            tool_call_id = str(msg.get("tool_call_id") or "").strip()
            if not tool_call_id or tool_call_id in seen:
                continue
            seen.add(tool_call_id)
            consumed.append(tool_call_id)
        return consumed

    def _dispatch_tool(self, tool_call: Dict[str, Any], state: Dict[str, Any]) -> str:
        """分发并执行工具调用"""
        ensure_not_cancelled()
        function_info = tool_call.get("function", {})
        tool_name = function_info.get("name", "")
        tool_args = function_info.get("arguments", {})
        
        if isinstance(tool_args, str):
            try:
                tool_args = json.loads(tool_args)
            except json.JSONDecodeError as e:
                error_msg = f"工具 '{tool_name}' 参数解析失败: {e}"
                self.logger.error(error_msg)
                return error_msg
        
        # 验证工具是否存在
        if tool_name not in self.tool_map:
            error_msg = f"工具 '{tool_name}' 不存在，可用工具: {list(self.tool_map.keys())}"
            self.logger.error(error_msg)
            return error_msg
        
        func = self.tool_map[tool_name]
        
        try:
            signature_params = inspect.signature(func).parameters
            if "state" in signature_params:
                tool_args["state"] = state
            if "llm" in signature_params and "llm" not in tool_args:
                tool_args["llm"] = ctx.llm
            if "config" in signature_params and "config" not in tool_args:
                # 传递工具专属配置；指定工具额外继承 root 运行时身份字段。
                config_key = self.tool_config_keys.get(tool_name, tool_name)
                root_cfg = ctx.config if isinstance(getattr(ctx, "config", None), dict) else {}
                tool_cfg = root_cfg.get('tools', {}).get(config_key, {}).get('config', {}) if root_cfg else {}
                if isinstance(tool_cfg, dict):
                    tool_cfg = deepcopy(tool_cfg)
                else:
                    tool_cfg = {}
                if tool_name in _RUNTIME_IDENTITY_TOOL_CONFIG_KEYS or config_key in _RUNTIME_IDENTITY_TOOL_CONFIG_KEYS:
                    if isinstance(root_cfg.get("memory"), dict) and "memory" not in tool_cfg:
                        tool_cfg["memory"] = deepcopy(root_cfg["memory"])
                    for identity_key in ("user_id", "tenant_id"):
                        identity_value = root_cfg.get(identity_key)
                        if identity_value not in (None, "") and identity_key not in tool_cfg:
                            tool_cfg[identity_key] = identity_value
                    runtime_identity = state.get("runtime_identity") if isinstance(state, dict) else None
                    if not isinstance(runtime_identity, dict):
                        runtime_identity = {
                            key: state.get(key)
                            for key in (
                                "agent_role",
                                "delegate_depth",
                                "agent_name",
                                "delegate_id",
                                "parent_tool_call_id",
                            )
                            if isinstance(state, dict) and state.get(key) is not None
                        }
                    if runtime_identity:
                        tool_cfg.setdefault("runtime_identity", deepcopy(runtime_identity))
                        for identity_key, identity_value in runtime_identity.items():
                            if identity_value is not None and identity_key not in tool_cfg:
                                tool_cfg[identity_key] = deepcopy(identity_value)
                tool_args["config"] = tool_cfg
            self.logger.info(f"调用工具: tool_name: {tool_name}, 参数: {', '.join([f'{k}: {v}' for k, v in tool_args.items() if k!='state' and k!='llm' and k!='config'])}")

            result = func(**tool_args)
            self.logger.info(f"工具 '{tool_name}' 执行成功，结果: {result}")

            if isinstance(result, (dict, list)):
                result = json.dumps(result, ensure_ascii=False)
            return result
        except RunCancelledError:
            raise
        except Exception as e:
            error_msg = f"工具 '{tool_name}' 执行失败: {e}"
            self.logger.error(error_msg)
            return error_msg
    
    def call_with_tools(self, state: Dict[str, Any]) -> tuple[List[Dict[str, Any]], int]:
        """调用 LLM 并处理工具调用, 通常只调用1次或固定次数的LLM调用(workflow)"""
        # Main runtime is record-backed; delegate runtimes are message-only and skip
        # prompt compilation / summary / state injection.
        record_backed_runtime = "message_records" in state
        if record_backed_runtime:
            rebuild_compiled_messages(state)
        messages = state["messages"]

        def _refresh_messages_from_records() -> None:
            nonlocal messages
            if record_backed_runtime:
                messages = rebuild_compiled_messages(state)
            else:
                state["messages"] = messages

        def _append_assistant_message(
            message: Dict[str, Any],
            *,
            source: str = "runtime",
            emit_structured: bool = True,
            consumes_tool_call_ids: Optional[List[str]] = None,
        ) -> None:
            nonlocal messages
            if not record_backed_runtime:
                messages.append(message)
                state["messages"] = messages
                return

            assistant_record, tool_records = add_assistant_turn(state, message, source=source)
            scope = self._resolve_record_scope(state)
            assistant_record["scope"] = scope
            if consumes_tool_call_ids is not None:
                assistant_record["consumes_tool_call_ids"] = consumes_tool_call_ids
            record_runtime_event(
                event_type="assistant_output",
                state=state,
                record=assistant_record,
                scope=scope,
                payload=(
                    {"consumes_tool_call_ids": consumes_tool_call_ids}
                    if consumes_tool_call_ids is not None
                    else None
                ),
            )
            for tool_record in tool_records:
                tool_record["scope"] = scope
                record_runtime_event(
                    event_type="tool_call",
                    state=state,
                    record=tool_record,
                    scope=scope,
                )
            _refresh_messages_from_records()
            if emit_structured:
                self._emit_structured_state_chunks(state, assistant_record, *tool_records)

        def _normalize_tool_result_payload(result: Any) -> Any:
            if not isinstance(result, str):
                return result
            trimmed = result.strip()
            if not trimmed or trimmed[0] not in "{[":
                return result
            try:
                return json.loads(trimmed)
            except Exception:
                return result

        tool_parameters_by_name = {
            str((schema.get("function") or {}).get("name") or "").strip():
            deepcopy((schema.get("function") or {}).get("parameters") or {})
            for schema in self.tool_schemas
            if isinstance(schema, dict)
        }
        retry_count = 0
        response = None
        
        while retry_count <= self.max_retries:
            if is_stop_requested():
                state["stop_requested"] = True
                return state
            try:
                messages = normalize_messages_for_llm(messages)
                state[self.message_key] = messages
                response = self.llm.completion(
                    messages=messages,
                    tools=self.tool_schemas if self.tool_schemas else None
                )
                ensure_not_cancelled()
                # normalize usage key to keep a consistent name
                if "total_usage" not in response:
                    if "usage" in response:
                        response["total_usage"] = response.pop("usage")
                    elif "_usage" in response:
                        response["total_usage"] = response.pop("_usage")
                # track latest token usage from provider if available
                usage_val = response.get("total_usage")
                if usage_val is not None:
                    state["last_usage"] = usage_val
                state["loops"] = state.get("loops", 0) + 1
                if "global_loops" in state:
                    state["global_loops"] = state.get("global_loops", 0) + 1
                self.log_response(response)
            except RunCancelledError:
                state["stop_requested"] = True
                return state
            except Exception as e:
                # BaseLLM v2 self-retries the entire chain (models × attempts) internally.
                # If it raises, the chain is already exhausted — no point retrying here.
                chain_trace = getattr(e, "chain_trace", None)
                if chain_trace:
                    self.logger.error(f"LLM 调用失败（链路已耗尽），链路追踪: {chain_trace}; 错误: {e}")
                else:
                    self.logger.error(f"LLM 调用失败（BaseLLM 内部重试已耗尽）: {e}")
                error_response = {"role": "assistant", "content": f"LLM 调用失败: {e}"}
                _append_assistant_message(error_response, source="runtime_error")
                self._emit_delegate_progress(state)
                self._emit_stream_message(error_response)
                response = None
                break

            # 空响应且无工具调用时重试
            content = response.get("content", "")
            tool_calls = response.get("tool_calls")
            if (not content) and not tool_calls:
                retry_count += 1
                if retry_count <= self.max_retries:
                    self.logger.warning(f"LLM 返回空响应，重试 ({retry_count}/{self.max_retries})")
                    continue
                else:
                    self.logger.error("LLM 返回空响应，已达到最大重试次数")
                    error_response = {"role": "assistant", "content": "LLM 返回空响应，已达到最大重试次数"}
                    _append_assistant_message(error_response, source="runtime_error")
                    self._emit_delegate_progress(state)
                    response = None
                    break
            
            if _validate_tool_calls(response, tool_parameters_by_name=tool_parameters_by_name): # 验证LLM输出的tool_calls是否有效
                consumed_tool_call_ids = self._collect_consumed_tool_call_ids(messages)
                _append_assistant_message(
                    response,
                    consumes_tool_call_ids=consumed_tool_call_ids,
                )
                self._emit_delegate_progress(state)
                self._emit_stream_message(response)
                break
            
            retry_count += 1
            if retry_count <= self.max_retries:
                self.logger.warning(f"工具调用 arguments 验证失败，重试 ({retry_count}/{self.max_retries})")
            else:
                self.logger.error(f"工具调用 arguments 验证失败，已达到最大重试次数 {self.max_retries}")
            
            if response is None:
                self.logger.error("LLM 调用失败，无法获取有效响应")
                error_response = {"role": "assistant", "content": "LLM 调用失败，无法获取有效响应"}
                _append_assistant_message(error_response, source="runtime_error")
                self._emit_delegate_progress(state)
                self._emit_stream_message(error_response)
                break
            
        tool_calls = response.get("tool_calls", []) if response else []
        waiting_blocker: Optional[Dict[str, Optional[str]]] = None
        for tool_call in tool_calls:
            if is_stop_requested():
                state["stop_requested"] = True
                break
            tool_execution_blocked = waiting_blocker is not None
            if tool_execution_blocked:
                skipped_payload = {
                    "status": "skipped_due_to_waiting_for_user_input",
                    "blocked_by_tool_call_id": waiting_blocker.get("tool_call_id"),
                    "blocked_by_tool_name": waiting_blocker.get("tool_name"),
                    "request_id": waiting_blocker.get("request_id"),
                    "message": "This tool call was skipped because execution is waiting for user feedback from an earlier tool call.",
                }
                tool_result = json.dumps(skipped_payload, ensure_ascii=False)
                tool_result_payload = skipped_payload
            else:
                tool_result = self._dispatch_tool(tool_call, state)
                tool_result_payload = _normalize_tool_result_payload(tool_result)
                if is_stop_requested():
                    state["stop_requested"] = True
                    break
            tool_result_record = None
            if record_backed_runtime:
                tool_call_record = None
                for record in reversed(state.get("message_records", [])):
                    if record.get("type") == "tool_call" and record.get("tool_call_id") == tool_call.get("id", ""):
                        tool_call_record = record
                        break
                tool_result_record = add_tool_result(
                    state,
                    tool_name=tool_call.get("function", {}).get("name", ""),
                    tool_call_id=tool_call.get("id", ""),
                    content=tool_result,
                    parent_id=tool_call_record.get("id") if tool_call_record else None,
                    payload={"result": tool_result_payload},
                )
                if tool_result_record is not None:
                    tool_result_record["scope"] = self._resolve_record_scope(state)
                    record_runtime_event(
                        event_type="tool_result",
                        state=state,
                        record=tool_result_record,
                        scope=tool_result_record.get("scope"),
                    )
            tool_msg = {
                "role": "tool",
                "tool_call_id": tool_call.get("id", ""),
                "name": tool_call.get("function", {}).get("name", ""),
                "content": str(tool_result),
            }
            if record_backed_runtime:
                _refresh_messages_from_records()
            else:
                messages.append(tool_msg)
                state["messages"] = messages
            self._emit_delegate_progress(state)
            self._emit_stream_message(tool_msg)
            if record_backed_runtime and (not tool_execution_blocked) and is_waiting_for_user_input(state):
                pending_payload = get_runtime_pending_ask_user_payload(state)
                request_id = None
                if isinstance(pending_payload, dict):
                    request_id = pending_payload.get("request_id")
                mark_waiting_for_user_input(
                    state,
                    tool_result_record_id=tool_result_record.get("id") if tool_result_record else None,
                    request_id=request_id,
                )
                checkpoint_runtime_state(
                    checkpoint_kind="ask_user_wait",
                    state=state,
                )
                waiting_blocker = {
                    "tool_call_id": tool_call.get("id", ""),
                    "tool_name": tool_call.get("function", {}).get("name", ""),
                    "request_id": request_id,
                }
            if record_backed_runtime:
                self._emit_structured_state_chunks(state, tool_result_record or {})
            if is_waiting_for_user_input(state) and not record_backed_runtime:
                break
        _refresh_messages_from_records()
        # --- reasoning nudge: after a tool round (and not waiting for the user), insert a
        # user text prompting thorough thinking so the NEXT turn carries fresh signed thinking.
        if (
            tool_calls
            and not state.get("stop_requested")
            and not is_waiting_for_user_input(state)
        ):
            nudge = _resolve_reasoning_nudge(messages)
            if nudge is not None:
                nudge_text, nudge_locale = nudge
                if record_backed_runtime:
                    add_user_input(state, text=nudge_text, language=nudge_locale, source="reasoning_nudge")
                    _refresh_messages_from_records()
                else:
                    messages.append({"role": "user", "content": nudge_text})
                    state["messages"] = messages
        if response is not None and tool_calls and "global_tool_call_count" in state:
            state["global_tool_call_count"] += len(tool_calls)
        return state
    
    def run(self, state: Dict[str, Any]) -> None:
        """执行节点的完整逻辑流程"""
        self.call_with_tools(state)
        

class BaseAgent:
    """
    Agent 基类，通过 while 循环执行节点
    state: Dict[str, Any] = {
        "global_tool_call_count": int,
        "global_iterations": int,
        "active_node": str,
        "messages": List[Dict[str, Any]],
    }

    entry_point从input_state中获取
    """
    _init_state: Dict[str, Any] = {
        "global_tool_call_count": 0,
        "global_iterations": 0,
        "loops": 0,
        "active_node": 'main',
        "messages": [],
    }
    init_state = MappingProxyType(_init_state)
    
    def __init__(
        self,
        name: str = "agent",
        nodes: Optional[List[BaseNode]] = None,
        max_loops: Optional[int] = 20,
        entry_point: Optional[str] = None,
    ):
        if not nodes:
            raise ValueError("BaseAgent 初始化失败：未提供任何节点")
        self.name = name
        self.nodes = {node.name: node for node in nodes}
        self.state = None  # 初始状态从run函数传入
        self.max_loops = max_loops
        self.entry_point = entry_point

        self.logger = logging.getLogger(f"{self.name}")
    
    def reset(self) -> None:
        # mappingproxy 不能直接作为可变 state 使用，这里始终生成独立副本
        self.state = deepcopy(dict(self.init_state))
    
    def _next_node(self, state: Dict[str, Any], current_node: Optional[str]) -> Optional[str]:
        """决定下一个节点，子类可重写"""
        if current_node is None:
            return None
        if is_waiting_for_user_input(state):
            return None
        messages = state.get("messages", [])
        if not messages:
            return current_node
        last_message = messages[-1]
        if last_message.get("is_summary"):
            return None
        if last_message.get("role") == "assistant":
            return None
        return current_node

    def _post_process(self, current_node: Optional[str]) -> None:
        """后处理，并决定下一个节点"""
        state = self.state
        state["active_node"] = self._next_node(state, current_node)
            
    def _should_stop(self, state: Dict[str, Any], current_loops: int) -> bool:
        """检查是否应该停止，子类可重写"""
        if self.max_loops is None:
            return False
        return current_loops >= self.max_loops

    def _on_finish(self, state: Dict[str, Any]) -> None:
        """执行结束时的回调，子类可重写"""
        if self.max_loops is not None and state.get("loops", 0) >= self.max_loops:
            self.logger.warning(f"⚠️ {self.name} 达到最大模型调用次数 {self.max_loops}")
        else:
            self.logger.info(f"✅ {self.name} 执行完成")

    def _ensure_entry_point(self, state: Dict[str, Any]) -> None:
        """确保 active_node 可用，优先 entry_point."""
        if state.get("active_node") is not None:
            return
        if self.entry_point:
            state["active_node"] = self.entry_point
            return
        # fallback to existing state entry_point
        if state.get("entry_point"):
            state["active_node"] = state["entry_point"]
            return
        # fallback to first node
        if self.nodes:
            state["active_node"] = next(iter(self.nodes.keys()))

    
    def run(self, input_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行 Agent 工作流"""
        # do not copy input_state, keep the reference
        self.state = input_state
        state = self.state
        if state is None:
            self.reset()
            state = self.state

        self._ensure_entry_point(state)

        if state.get("active_node") is not None and state.get("active_node") != "finalize":
            if is_waiting_for_user_input(state):
                state["active_node"] = None
            else:
                messages = state.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if last_message.get("is_summary") or last_message.get("role") == "assistant":
                        state["active_node"] = None

        local_steps = 0
        
        active_node = state.get("active_node")
        self.logger.info(f"🚀 {self.name} 开始执行，入口节点: {active_node}")
        
        while state.get("active_node") is not None:
            if is_stop_requested():
                state["stop_requested"] = True
                state["active_node"] = None
                break
            current_loops = state.get("loops", 0)
            if state.get("active_node") != "finalize" and self._should_stop(state, current_loops):
                if "finalize" in self.nodes:
                    state["active_node"] = "finalize"
                    continue
                break

            active_node = state["active_node"]
            
            if active_node not in self.nodes:
                self.logger.error(f"{self.name} 节点 '{active_node}' 不存在")
                raise ValueError(f"{self.name} 节点 '{active_node}' 不存在")
            
            node = self.nodes[active_node]
            self.logger.info(f"📍 {self.name} 执行节点: {active_node}")
            
            try:
                ensure_not_cancelled()
                node.run(state)
            except RunCancelledError:
                state["stop_requested"] = True
                state["active_node"] = None
                break
            except Exception as e:
                self.logger.error(f"{self.name} 节点 '{active_node}' 执行失败: {e}")
                raise

            # 更新全局统计
            local_steps += 1
            if is_stop_requested():
                state["stop_requested"] = True
                state["active_node"] = None
                break
            
            self._post_process(active_node)

        self._on_finish(state)
        
        # 返回包含统计信息和更新后的配置的结果
        return state
