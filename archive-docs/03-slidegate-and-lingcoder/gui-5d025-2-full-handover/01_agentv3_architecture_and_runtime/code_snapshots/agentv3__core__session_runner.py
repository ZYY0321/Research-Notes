import logging
import threading
from typing import Any, Dict, Optional, Tuple

from agents.agentv3.core.context_pipeline import (
    prepare_runtime_state,
    publish_live_state_snapshot_if_available,
    start_retrieved_context_prefetch,
)
from agents.agentv3.core.postprocess import finalize_session_result
from agents.agentv3.core.session_setup import prepare_session
from src.utils.cancellation import RunCancelledError, ensure_not_cancelled


logger = logging.getLogger(__name__)


def _sandbox_keepalive_interval(timeout: Any) -> float:
    try:
        interval = float(timeout) // 2
    except (TypeError, ValueError):
        interval = 60.0
    return max(1.0, interval)


def _ping_sandbox_session(client: Any, session_id: str) -> Any:
    get_session_status = getattr(client, "get_session_status", None)
    if callable(get_session_status):
        return get_session_status(session_id)

    request = getattr(client, "_request", None)
    if callable(request):
        return request("GET", f"/sessions/{session_id}/get_session_status")

    raise AttributeError("sandbox client does not support session status checks")


def _start_sandbox_keepalive(
    *,
    sandbox_manager: Any,
    session_id: str,
    conversation_id: str,
    log: logging.Logger,
) -> Optional[Tuple[threading.Event, threading.Thread]]:
    client = getattr(sandbox_manager, "client", None)
    if client is None or not session_id:
        return None

    stop_event = threading.Event()
    interval = _sandbox_keepalive_interval(getattr(sandbox_manager, "timeout", None))

    def _keepalive_loop() -> None:
        while not stop_event.wait(interval):
            try:
                _ping_sandbox_session(client, session_id)
            except Exception as exc:
                log.warning("[%s] 沙盒 keepalive 失败: %s", conversation_id, exc)

    thread = threading.Thread(
        target=_keepalive_loop,
        name=f"sandbox-keepalive-{session_id}",
        daemon=True,
    )
    thread.start()
    return stop_event, thread


def _stop_sandbox_keepalive(
    keepalive: Optional[Tuple[threading.Event, threading.Thread]]
) -> None:
    if keepalive is None:
        return
    stop_event, thread = keepalive
    stop_event.set()
    thread.join(timeout=1.0)


def run_single_case(
    case: Dict[str, Any],
    components: Dict[str, Any],
    conversation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """执行单个用例，支持绝对路径的文件."""
    session_ctx = prepare_session(case, components, conversation_id=conversation_id)
    retrieved_context_future = start_retrieved_context_prefetch(
        config=session_ctx.get("conf"),
        runtime_conf=session_ctx.get("runtime_conf"),
        runtime_lang=session_ctx.get("runtime_lang"),
        query=session_ctx.get("raw_query"),
        llm=components.get("llm"),
    )
    if retrieved_context_future is not None:
        session_ctx["retrieved_context_future"] = retrieved_context_future

    runtime_session_id = session_ctx["runtime_session_id"]
    resolved_conversation_id = session_ctx["conversation_id"]
    sandbox_manager = session_ctx["sandbox_manager"]
    log = session_ctx["log"]
    sandbox_keepalive = _start_sandbox_keepalive(
        sandbox_manager=sandbox_manager,
        session_id=runtime_session_id,
        conversation_id=resolved_conversation_id,
        log=log,
    )

    try:
        turn_ctx = prepare_runtime_state(case, components, session_ctx)
        session_ctx.update(turn_ctx)
        state = turn_ctx["state"]

        ensure_not_cancelled()
        state = session_ctx["agent"].run(state)
        publish_live_state_snapshot_if_available(state, conversation_id=resolved_conversation_id)

        return finalize_session_result(
            case=case,
            components=components,
            session_ctx=session_ctx,
            state=state,
        )
    except RunCancelledError as exc:
        log.info("[%s] Agent run cancelled: %s", resolved_conversation_id, exc)
        return {"success": False, "error": str(exc), "stopped": True}
    except Exception as exc:
        log.error("[%s] Agent 运行异常: %s", resolved_conversation_id, exc, exc_info=True)
        return {"success": False, "error": str(exc)}
    finally:
        _stop_sandbox_keepalive(sandbox_keepalive)
        try:
            sandbox_manager.release_workspace(session_id=runtime_session_id)
        except Exception as release_err:
            log.warning(
                "[%s] 释放沙盒失败（已忽略）: %s",
                resolved_conversation_id,
                release_err,
                exc_info=True,
            )
