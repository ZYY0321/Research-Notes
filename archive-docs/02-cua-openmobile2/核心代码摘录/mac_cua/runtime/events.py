"""Pure event, usage and model observations."""
import json
from pathlib import Path
from typing import Any

def parse_events(path: Path) -> dict:
    """The exec stream's usage covers the primary thread; never infer child usage."""
    summaries: list[dict] = []
    errors: list[Any] = []
    answer = None
    thread_id = None
    invalid_lines = 0
    if path.exists():
        with path.open(errors="replace") as stream:
            for line in stream:
                try:
                    event = json.loads(line)
                except (ValueError, TypeError):
                    invalid_lines += bool(line.strip())
                    continue
                if not isinstance(event, dict):
                    invalid_lines += 1
                    continue
                if event.get("type") == "thread.started":
                    thread_id = event.get("thread_id")
                if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
                    summaries.append(event["usage"])
                if event.get("type") in {"error", "turn.failed"}:
                    errors.append(event.get("error", event.get("message", event)))
                item = event.get("item") or {}
                if event.get("type") == "item.completed" and isinstance(item, dict) and item.get("type") == "agent_message":
                    answer = item.get("text")
    usage = None
    if summaries:
        fields = {key for record in summaries for key in record}
        usage = {key: sum(record[key] for record in summaries)
                 if all(isinstance(record.get(key), (float, int)) for record in summaries)
                 else None for key in fields}
    return {"thread_id": thread_id, "usage": usage, "usage_scope": "primary_thread",
            "usage_events": summaries, "errors": errors, "final_answer": answer,
            "invalid_event_lines": invalid_lines}


def session_usage(sessions_dir: Path) -> list[dict]:
    summaries = []
    for path in sorted(sessions_dir.rglob("*.jsonl")) if sessions_dir.exists() else []:
        session_id = None
        source = None
        usage = None
        contexts = []
        invalid_lines = 0
        for line in path.read_text(errors="replace").splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                invalid_lines += bool(line.strip())
                continue
            if not isinstance(event, dict):
                invalid_lines += 1
                continue
            if not isinstance(event.get("payload"), dict):
                if event.get("type") == "turn_context":
                    contexts.append({"turn_id": None, "model": None, "effort": None})
                continue
            payload = event["payload"]
            if event.get("type") == "session_meta":
                session_id = payload.get("id")
                source = payload.get("source")
            if event.get("type") == "turn_context":
                # Codex 0.147's observed rollout uses "model" and "effort".
                # Missing observations are never filled from configuration.
                contexts.append({"turn_id": payload.get("turn_id"),
                                 "model": payload.get("model") if isinstance(payload.get("model"), str) and payload["model"] else None,
                                 "effort": payload.get("effort") if isinstance(payload.get("effort"), str) and payload["effort"] else None})
            if event.get("type") == "event_msg" and payload.get("type") == "token_count":
                info = payload.get("info")
                if isinstance(info, dict) and isinstance(info.get("total_token_usage"), dict):
                    usage = info["total_token_usage"]
        summaries.append({"session_id": session_id, "source": source, "usage": usage,
                          "model_contexts": contexts,
                          "invalid_event_lines": invalid_lines,
                          "rollout": str(path.relative_to(sessions_dir))})
    return summaries


def model_audit(records: list[dict], agent_cfg: dict, *, collection_complete: bool) -> dict:
    """Diagnostic only: observed model deviations never rewrite grader scores."""
    expected = {"model": agent_cfg.get("model", "gpt-5.6-luna"),
                "effort": agent_cfg.get("reasoning_effort", "medium")}
    differences, unknown = [], []
    observed_contexts = 0
    if not collection_complete:
        unknown.append({"reason": "collection_incomplete"})
    if not records:
        unknown.append({"reason": "no_rollouts"})
    for record in records:
        identity = {key: record.get(key) for key in ("session_id", "collection_root", "rollout")}
        contexts = record.get("model_contexts", [])
        if record.get("invalid_event_lines"):
            unknown.append({**identity, "reason": "invalid_rollout_json",
                            "count": record["invalid_event_lines"]})
        if not contexts:
            unknown.append({**identity, "reason": "no_turn_context"})
        for index, context in enumerate(contexts):
            observed_contexts += 1
            location = {**identity, "turn_context_index": index, "turn_id": context.get("turn_id")}
            for field, value in expected.items():
                actual = context.get(field)
                if actual is None:
                    unknown.append({**location, "field": field, "reason": "not_observed"})
                elif actual != value:
                    differences.append({**location, "field": field, "expected": value, "observed": actual})
    return {"status": "mismatch" if differences else "unknown" if unknown else "observed_match",
            "expected": expected, "collection_complete": collection_complete,
            "rollout_count": len(records), "observed_context_count": observed_contexts,
            "differences": differences, "unknown": unknown,
            "score_modified": False}
