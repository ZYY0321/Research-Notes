import json
import logging
import re
from typing import Any, Dict, List, Optional

from agents.agentv3.core.context_pipeline import publish_live_state_snapshot_if_available
from agents.agentv3.core.qa_chunk_save import maybe_save_final_qa_chunk, maybe_save_waiting_ask_user_qa_chunk
from src.conversation_state_v3 import (
    add_assistant_turn,
    compile_messages_with_temporary_user_inputs,
    extract_persistable_state,
    sanitize_assistant_output_text,
    set_conversation_status,
)


logger = logging.getLogger(__name__)


def _extract_messages_for_export(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = []
    if isinstance(state, dict):
        main_state = state.get("main_state")
        if isinstance(main_state, dict):
            messages = main_state.get("messages", []) or []
        if not messages:
            messages = state.get("messages", []) or []
    return list(messages)


def _resolve_instruction_locale(locale: Optional[str]) -> str:
    return "zh-CN" if str(locale or "").lower().startswith("zh") else "en-US"


def _build_functional_instruction_inputs(
    *,
    runtime_lang: Optional[str],
    function_name: str,
    instructions: List[str],
) -> List[Dict[str, Any]]:
    resolved_locale = _resolve_instruction_locale(runtime_lang)
    instruction_inputs: List[Dict[str, Any]] = []
    total = len(instructions)
    for index, instruction in enumerate(instructions):
        text = str(instruction or "").strip()
        if not text:
            continue
        instruction_inputs.append(
            {
                "text": text,
                "input_kind": "functional_instruction",
                "payload": {
                    "function_name": function_name,
                    "instruction_scope": "temporary",
                    "instruction_mode": "single" if total == 1 else "multi",
                    "instruction_index": index,
                    "instruction_count": total,
                },
                "language": resolved_locale,
                "source": "derived_prompt",
            }
        )
    return instruction_inputs


def _run_derived_prompt(
    llm: Any,
    *,
    state: Dict[str, Any],
    runtime_lang: Optional[str],
    function_name: str,
    instructions: List[str],
) -> str:
    derived_messages = compile_messages_with_temporary_user_inputs(
        state,
        temporary_inputs=_build_functional_instruction_inputs(
            runtime_lang=runtime_lang,
            function_name=function_name,
            instructions=instructions,
        ),
    )
    response = llm.completion(messages=derived_messages)
    return str((response or {}).get("content") or "").strip()


def _fallback_conversation_title(
    *,
    state: Dict[str, Any],
    query: str,
    runtime_lang: Optional[str],
) -> str:
    fallback = str(query or "").strip()
    if not fallback:
        source_state = extract_persistable_state(state)
        for record in reversed(source_state.get("message_records") or []):
            if record.get("type") != "user_input":
                continue
            candidate = str(record.get("text") or "").strip()
            if candidate:
                fallback = candidate
                break
            uploads = record.get("uploads") or []
            if uploads:
                upload_names = [str(item.get("name") or "").strip() for item in uploads if isinstance(item, dict)]
                fallback = next((name for name in upload_names if name), "")
                if fallback:
                    break
    if fallback:
        return fallback[:30] + ("..." if len(fallback) > 30 else "")
    return "新对话" if _resolve_instruction_locale(runtime_lang).startswith("zh") else "New conversation"


def _generate_conversation_title(
    llm: Any,
    *,
    state: Dict[str, Any],
    runtime_lang: Optional[str],
    query: str,
) -> str:
    instruction = (
        "请基于以上上下文，为这段对话生成一个纯文本短标题。"
        "标题只反映用户目标和 assistant 面向用户说过的内容；"
        "忽略内部编排细节（内部文件路径、目录变量、工件文件名、工具/函数/skill/脚本名、阶段名、id、协议字段、JSON 事件块等）。"
        "要求：不超过18个字，不要引号，不要编号，不要解释。"
        if _resolve_instruction_locale(runtime_lang).startswith("zh")
        else (
            "Based on the conversation above, generate a short plain-text title. "
            "Base the title only on the user's goal and on user-visible assistant content; "
            "ignore internal orchestration details (internal file paths, directory variables, artifact filenames, "
            "tool/function/skill/script names, stage labels, ids, protocol fields, JSON event blocks, etc.). "
            "Requirements: keep it concise, do not use quotes, numbering, or explanations."
        )
    )
    try:
        title = _run_derived_prompt(
            llm,
            state=state,
            runtime_lang=runtime_lang,
            function_name="conversation_title",
            instructions=[instruction],
        )
        title = re.sub(r'^[\"“”\'\s]+|[\"“”\'\s]+$', "", title).strip()
        if title:
            return title[:40]
    except Exception as exc:
        logger.warning("conversation title generation failed: %s", exc)
    return _fallback_conversation_title(state=state, query=query, runtime_lang=runtime_lang)


def _generate_next_questions(
    llm: Any,
    *,
    state: Dict[str, Any],
    runtime_lang: Optional[str],
) -> List[str]:
    lang = str(runtime_lang or "").lower()
    instruction = (
        "请基于以上上下文，推荐 2-3 个下一问。"
        "下一问只基于用户目标和 assistant 面向用户说过的内容；"
        "忽略内部编排细节（内部文件路径、目录变量、工件文件名、工具/函数/skill/脚本名、阶段名、id、协议字段、JSON 事件块等）。"
        "只返回 JSON 数组字符串，例如 [\"问题1\",\"问题2\"]。"
        if lang.startswith("zh")
        else (
            'Recommend 2-3 plausible follow-up questions based on the context above. '
            'Base the questions only on the user goal and user-visible assistant content; '
            'ignore internal orchestration details (internal file paths, directory variables, artifact filenames, '
            'tool/function/skill/script names, stage labels, ids, protocol fields, JSON event blocks, etc.). '
            'Return only a JSON array string such as ["Q1","Q2"].'
        )
    )
    try:
        raw = _run_derived_prompt(
            llm,
            state=state,
            runtime_lang=runtime_lang,
            function_name="next_questions",
            instructions=[instruction],
        )
        data = json.loads(raw)
        if isinstance(data, list):
            cleaned = [str(item).strip() for item in data if str(item).strip()]
            return cleaned[:3]
    except Exception as exc:
        logger.warning("next question generation failed: %s", exc)
    return []


def _resolve_conversation_title(
    llm: Any,
    *,
    state: Dict[str, Any],
    query: str,
    runtime_lang: Optional[str],
    preferred_title: Optional[str] = None,
) -> str:
    preferred = str(preferred_title or "").strip()
    if preferred:
        return preferred[:40]
    session_metadata = state.setdefault("session_metadata", {})
    existing = str(session_metadata.get("conversation_title") or "").strip()
    if existing:
        return existing[:40]
    return _generate_conversation_title(
        llm,
        state=state,
        query=query,
        runtime_lang=runtime_lang,
    )


def _build_latest_response_meta(
    *,
    state: Dict[str, Any],
    next_questions: List[str],
) -> Optional[Dict[str, Any]]:
    cleaned_questions = [str(item).strip() for item in next_questions if str(item).strip()]
    if not cleaned_questions:
        return None

    persisted_state = extract_persistable_state(state)
    for record in reversed(persisted_state.get("message_records") or []):
        if record.get("type") != "assistant_output" or record.get("hidden"):
            continue
        assistant_record_id = str(record.get("id") or "").strip()
        if not assistant_record_id:
            continue
        return {
            "assistant_record_id": assistant_record_id,
            "next_questions": cleaned_questions[:3],
        }
    return None


def _ensure_final_response_recorded(state: Dict[str, Any], final_response: str) -> Optional[Dict[str, Any]]:
    if "message_records" not in state:
        return None

    sanitized_response = sanitize_assistant_output_text(final_response)
    if not sanitized_response:
        return None

    latest_assistant = None
    for record in reversed(state.get("message_records") or []):
        if record.get("type") != "assistant_output" or record.get("hidden"):
            continue
        latest_assistant = record
        break

    if isinstance(latest_assistant, dict) and str(latest_assistant.get("text") or "") == sanitized_response:
        return latest_assistant

    assistant_record, _ = add_assistant_turn(
        state,
        {"content": sanitized_response, "tool_calls": []},
        source="assistant",
    )
    assistant_record["scope"] = "main"
    return assistant_record


def finalize_session_result(
    *,
    case: Dict[str, Any],
    components: Dict[str, Any],
    session_ctx: Dict[str, Any],
    state: Dict[str, Any],
) -> Dict[str, Any]:
    conversation_id = session_ctx["conversation_id"]
    runtime_lang = session_ctx["runtime_lang"]
    runtime_conf = session_ctx["runtime_conf"]
    raw_query = session_ctx["raw_query"]
    log = session_ctx["log"]

    if state.get("stop_requested"):
        set_conversation_status(state, "terminated")
        publish_live_state_snapshot_if_available(state, conversation_id=conversation_id)
        log.info("[%s] run stopped by user request", conversation_id)
        return {
            "success": False,
            "stopped": True,
            "response": "",
            "state": extract_persistable_state(state),
            "tool_schemas": {
                "main": session_ctx.get("main_tool_schemas") or [],
                "delegate": session_ctx.get("delegate_tool_schemas") or [],
            },
        }

    # 导出消息时跳过 system，避免把临时 system prompt 再次写回历史载荷。
    final_messages = _extract_messages_for_export(state)
    non_system_messages = [
        message for message in final_messages if isinstance(message, dict) and message.get("role") != "system"
    ]

    conversation_title = _resolve_conversation_title(
        components["llm"],
        state=state,
        query=raw_query,
        runtime_lang=runtime_lang,
        preferred_title=case.get("conversation_title"),
    )
    waiting_user_input = bool((state.get("runtime_control") or {}).get("conversation_status") == "waiting_user_input")
    final_response = ""
    if not waiting_user_input:
        for message in reversed(state["main_state"]["messages"]):
            if message.get("role") == "assistant":
                final_response = message.get("content", "")
                break
        if not final_response and state["main_state"]["messages"]:
            final_response = state["main_state"]["messages"][-1].get("content", "")

        # 兼容旧 prompt 约定：如果最终回复包了 <result>，只返回标签内部正文。
        result_match = re.search(r"<result>(.*?)</result>", final_response, re.DOTALL)
        if result_match:
            final_response = result_match.group(1).strip()
        _ensure_final_response_recorded(state, final_response)
        try:
            save_result = maybe_save_final_qa_chunk(
                state=state,
                session_ctx=session_ctx,
                final_response=final_response,
                waiting_user_input=waiting_user_input,
            )
            if save_result.get("saved"):
                log.info("[%s] QA chunk save accepted", conversation_id)
            else:
                reason = save_result.get("reason")
                if reason == "queued":
                    log.info("[%s] QA chunk save queued", conversation_id)
                elif str(reason or "").startswith("skipped_input_kind:") or reason == "internal_agent":
                    log.info("[%s] QA chunk save skipped: %s", conversation_id, reason)
                elif reason not in {
                    "disabled",
                    "empty_assistant_text",
                    "missing_user_text",
                    "waiting_user_input",
                }:
                    log.warning("[%s] QA chunk save skipped/failed: %s", conversation_id, reason)
        except Exception as exc:
            log.warning("[%s] QA chunk save failed without affecting response: %s", conversation_id, exc)
    else:
        try:
            save_result = maybe_save_waiting_ask_user_qa_chunk(
                state=state,
                session_ctx=session_ctx,
                waiting_user_input=waiting_user_input,
            )
            if save_result.get("saved"):
                log.info("[%s] QA chunk save accepted", conversation_id)
            else:
                reason = save_result.get("reason")
                if reason == "queued":
                    log.info("[%s] QA chunk save queued", conversation_id)
                elif reason not in {
                    "disabled",
                    "missing_user_text",
                    "waiting_user_input",
                    "not_waiting_user_input",
                    "no_pending_ask_user",
                    "empty_ask_user_question",
                }:
                    log.warning("[%s] QA chunk save skipped/failed: %s", conversation_id, reason)
        except Exception as exc:
            log.warning("[%s] QA chunk save failed without affecting response: %s", conversation_id, exc)

    state["session_metadata"]["conversation_title"] = conversation_title
    publish_live_state_snapshot_if_available(state, conversation_id=conversation_id)
    persisted_state = extract_persistable_state(state)

    tool_schemas = {
        "main": session_ctx.get("main_tool_schemas") or [],
        "delegate": session_ctx.get("delegate_tool_schemas") or [],
    }

    return {
        "success": not waiting_user_input,
        "response": final_response,
        "latest_response_meta": None,
        "state": persisted_state,
        "tool_schemas": tool_schemas,
    }
