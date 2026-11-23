"""Read-only audit of Codex native rollout trace schema 1.

This indexes native JSON without rewriting it. Native inference payloads are
Codex's normalized records, not captured HTTP bytes or an SFT dataset. ``valid``
means structurally valid; an interrupted prefix can be valid but not complete.
No external image URL or file is fetched. Image validation decodes the data URL
and checks its format signature, not the complete raster pixel stream.
"""
from __future__ import annotations

import base64
import binascii
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from urllib.parse import unquote, unquote_to_bytes, urlsplit

MAX_MANIFEST_BYTES = 1024 * 1024
MAX_EVENT_BYTES = 64 * 1024 * 1024
MAX_PAYLOAD_BYTES = 256 * 1024 * 1024
MAX_TREE_DEPTH = 128
MAX_TREE_NODES = 2_000_000
NATIVE_EVIDENCE_POLICY = 'codex-native-v2'
_ID = re.compile(r"[A-Za-z0-9_.:/-]{1,256}\Z")
_TYPES = {
    "rollout_started", "rollout_ended", "thread_started", "thread_ended",
    "codex_turn_started", "codex_turn_ended", "inference_started",
    "inference_completed", "inference_failed", "tool_call_started", "tool_call_ended",
    "protocol_event_observed", "compaction_started", "compaction_completed",
    "compaction_ended", "compaction_failed",
    # These additional schema-1 variants are identified in the pinned 0.147.0
    # binary. Their fields are not inferred from the smaller native probe.
    "inference_cancelled", "mcp_tool_call_correlation_assigned",
    "tool_call_runtime_started", "tool_call_runtime_ended", "code_cell_started",
    "code_cell_initial_response", "code_cell_ended", "compaction_request_started",
    "compaction_request_completed", "compaction_request_failed", "compaction_installed",
    "agent_result_observed",
}
_INTERRUPTED = {"timeout", "timed_out", "interrupted", "cancelled", "canceled", "terminated", "killed", "host_timeout", "transport_timeout"}
_AGENT_STATUSES = _INTERRUPTED | {"completed", "failed", "error", "agent_error", "exited", "startup_error", "supervisor_error", "transport_error"}
_COUNT_NAMES = (
    "events", "payloads", "inferences_started", "inferences_completed", "inferences_failed", "inferences_cancelled",
    "requests", "responses", "tool_calls_started", "tool_calls_ended", "compaction_events",
    "threads", "developer_messages", "tool_definitions", "images", "data_url_images",
    "decoded_data_url_images", "external_url_images", "local_sidecar_images",
    "unavailable_image_references", "unknown_events",
    "tool_call_runtime_started", "tool_call_runtime_ended", "code_cell_started",
    "code_cell_initial_response", "code_cell_ended", "compaction_request_started",
    "compaction_request_completed", "compaction_request_failed", "compaction_installed",
    "mcp_tool_call_correlation_assigned", "agent_result_observed",
)


def _identifier(value):
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def _strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("non-finite JSON number")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def _walk(value):
    """Bound work without silently truncating a deeply nested payload."""
    stack = [(value, 0)]
    visited = 0
    while stack:
        item, depth = stack.pop()
        visited += 1
        if depth > MAX_TREE_DEPTH or visited > MAX_TREE_NODES:
            raise ValueError("JSON traversal limit")
        yield item
        if isinstance(item, dict):
            stack.extend((child, depth + 1) for child in reversed(list(item.values())))
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in reversed(item))


def _image_signature(data, mime):
    signatures = {
        "image/png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/jpeg": data.startswith(b"\xff\xd8\xff"),
        "image/gif": data.startswith((b"GIF87a", b"GIF89a")),
        "image/webp": len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP",
    }
    return signatures.get(mime)  # Unknown formats are explicitly unverified.


class _Audit:
    def __init__(self, root, agent_status):
        self.root = root
        self.agent_status = agent_status if isinstance(agent_status, str) and agent_status in _AGENT_STATUSES else None
        self.interrupted = self.agent_status in _INTERRUPTED
        self.diagnostics = []
        self.bundles = []
        self.counts = Counter({name: 0 for name in _COUNT_NAMES})
        self.inferences = []
        self.compactions = []
        self.images = []
        self.observed_threads = set()
        self.invalid = False

    def diagnostic(self, code, path, *, invalid=True, seq=None):
        # Never include exception strings or values copied from model content.
        entry = {"code": code, "path": path, "severity": "error" if invalid else "warning"}
        if seq is not None:
            entry["seq"] = seq
        self.diagnostics.append(entry)
        self.invalid |= invalid

    def safe_path(self, bundle, value, *, context, directory=False):
        if not isinstance(value, str) or len(value) > 4096 or "\\" in value or any(ord(c) < 32 for c in value):
            self.diagnostic("unsafe_path", context)
            return None
        parts = PurePosixPath(value)
        if not value or parts.is_absolute() or any(p in {".", ".."} for p in value.split("/")) or "//" in value:
            self.diagnostic("unsafe_path", context)
            return None
        current = bundle
        try:
            for part in parts.parts:
                current = current / part
                info = current.lstat()
                if stat.S_ISLNK(info.st_mode):
                    self.diagnostic("symlink_forbidden", context)
                    return None
            if not (current.is_dir() if directory else current.is_file()):
                self.diagnostic("unexpected_path_type", context)
                return None
        except OSError:
            self.diagnostic("referenced_path_missing_or_unreadable", context)
            return None
        return current

    def read_json(self, path, limit, context):
        try:
            with path.open("rb") as handle:
                raw = handle.read(limit + 1)
            if len(raw) > limit:
                self.diagnostic("json_size_limit_exceeded", context)
                return None
            value = _strict_json(raw)
            return value, {"path": path.relative_to(self.root).as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        except (OSError, ValueError, UnicodeError, RecursionError):
            self.diagnostic("json_unreadable_or_invalid", context)
            return None

    def scan_image(self, value, bundle, context):
        self.counts["images"] += 1
        info = {"payload_path": context, "index": len(self.images), "replayable": False}
        self.images.append(info)
        if not isinstance(value, str) or not value:
            info["kind"] = "unresolved"
            self.counts["unavailable_image_references"] += 1
            self.diagnostic("image_reference_unresolved", context, invalid=False)
            return
        if value.startswith("data:"):
            info["kind"] = "data_url"
            self.counts["data_url_images"] += 1
            try:
                header, data = value.split(",", 1)
                mime = header[5:].split(";", 1)[0].lower()
                decoded = base64.b64decode(data, validate=True) if header.endswith(";base64") else unquote_to_bytes(data)
                if not decoded:
                    raise ValueError("empty image")
                if mime == "application/octet-stream":
                    # Some MCP tools return PNG bytes with a generic MIME type.
                    # Infer only a known image signature, preserving raw payloads.
                    info["declared_mime"] = mime
                    mime = next((candidate for candidate in ("image/png", "image/jpeg", "image/gif", "image/webp")
                                 if _image_signature(decoded, candidate) is True), "")
                if not mime.startswith("image/"):
                    raise ValueError("image MIME or recognized image signature required")
                signature = _image_signature(decoded, mime)
                if signature is False:
                    raise ValueError("image signature mismatch")
            except (ValueError, binascii.Error, UnicodeError):
                self.diagnostic("image_data_url_invalid", context)
                return
            info.update(bytes=len(decoded), sha256=hashlib.sha256(decoded).hexdigest(), mime=mime if signature is not None else "unrecognized_image_mime", signature_verified=signature is True, replayable=signature is True)
            self.counts["decoded_data_url_images"] += 1
            if signature is None:
                self.diagnostic("image_format_unverified", context, invalid=False)
            return
        try:
            parsed = urlsplit(value)
        except ValueError:
            self.diagnostic("image_reference_invalid", context)
            return
        if parsed.scheme in {"http", "https"}:
            info["kind"] = "external_url"
            self.counts["external_url_images"] += 1
            self.diagnostic("image_external_url_not_fetched", context, invalid=False)
            return
        self.counts["local_sidecar_images"] += 1
        info["kind"] = "local_sidecar"
        # Absolute guest paths/file URLs are not paths on the auditing host.
        candidate = unquote(parsed.path) if parsed.scheme == "file" else value
        if parsed.scheme not in {"", "file"} or parsed.netloc or PurePosixPath(candidate).is_absolute():
            self.counts["unavailable_image_references"] += 1
            self.diagnostic("image_file_not_bundle_local", context, invalid=False)
            return
        before = len(self.diagnostics)
        sidecar = self.safe_path(bundle, candidate, context=context)
        if sidecar is None:
            self.counts["unavailable_image_references"] += 1
            # Missing sidecars are a replay limitation; unsafe paths remain invalid.
            for diagnostic in self.diagnostics[before:]:
                if diagnostic["code"] == "referenced_path_missing_or_unreadable":
                    diagnostic["severity"] = "warning"
            self.invalid = any(d["severity"] == "error" for d in self.diagnostics)
            return
        try:
            with sidecar.open("rb") as handle:
                raw = handle.read(MAX_PAYLOAD_BYTES + 1)
            if len(raw) > MAX_PAYLOAD_BYTES:
                self.diagnostic("image_size_limit_exceeded", context)
                return
            known = any(_image_signature(raw, mime) is True for mime in ("image/png", "image/jpeg", "image/gif", "image/webp"))
            info.update(sidecar_path=sidecar.relative_to(self.root).as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), signature_verified=known, replayable=known)
            if not known:
                self.diagnostic("image_format_unverified", context, invalid=False)
        except OSError:
            self.diagnostic("image_sidecar_unreadable", context)

    def scan_content(self, value, bundle, context):
        try:
            for item in _walk(value):
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "message" and item.get("role") == "developer":
                    self.counts["developer_messages"] += 1
                if item.get("type") == "additional_tools" and isinstance(item.get("tools"), list):
                    self.counts["tool_definitions"] += len(item["tools"])
                if isinstance(item.get("type"), str) and item["type"] in {"input_image", "image_url"}:
                    image = item.get("image_url", item.get("url", item.get("file_id")))
                    if isinstance(image, dict):
                        image = image.get("url")
                    self.scan_image(image, bundle, context)
                elif item.get("type") == "image" and isinstance(item.get("data"), str):
                    self.scan_image("data:" + str(item.get("mimeType", "image/unknown")) + ";base64," + item["data"], bundle, context)
            if isinstance(value, dict) and isinstance(value.get("tools"), list):
                self.counts["tool_definitions"] += len(value["tools"])
        except (ValueError, RecursionError):
            self.diagnostic("json_traversal_limit_exceeded", context)

    def bundle(self, bundle):
        relative = bundle.relative_to(self.root).as_posix()
        manifest_path = self.safe_path(bundle, "manifest.json", context=relative + "/manifest.json")
        if manifest_path is None:
            return
        loaded = self.read_json(manifest_path, MAX_MANIFEST_BYTES, relative + "/manifest.json")
        if loaded is None:
            return
        manifest, manifest_ref = loaded
        if not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
            self.diagnostic("unsupported_manifest_schema", relative + "/manifest.json")
            return
        if any(not _identifier(manifest.get(key)) for key in ("trace_id", "rollout_id", "root_thread_id")):
            self.diagnostic("manifest_identity_invalid", relative + "/manifest.json")
            return
        event_path = self.safe_path(bundle, manifest.get("raw_event_log"), context=relative + "/manifest.json:raw_event_log")
        payload_dir = self.safe_path(bundle, manifest.get("payloads_dir"), context=relative + "/manifest.json:payloads_dir", directory=True)
        record = {"path": relative, "manifest": manifest_ref, "trace_id": manifest["trace_id"], "rollout_id": manifest["rollout_id"], "root_thread_id": manifest["root_thread_id"], "event_log": event_path.relative_to(self.root).as_posix() if event_path else None, "payloads": [], "inferences": [], "compactions": [], "thread_ids": [], "incomplete_inference_call_ids": [], "cancelled_inference_call_ids": [], "incomplete_tool_call_ids": [], "rollout_ended": False, "complete": False}
        self.bundles.append(record)
        if event_path is None or payload_dir is None:
            return
        calls, tools, threads_started, threads_ended = {}, {}, set(), set()
        turns_started, turns_ended = set(), set()
        payload_ids, payload_paths = {}, {}
        rollout_started = False
        diagnostic_start = len(self.diagnostics)
        expected_seq = 1
        closed = False
        event_hash = hashlib.sha256()
        event_size = 0
        try:
            with event_path.open("rb") as handle:
                while True:
                    raw = handle.readline(MAX_EVENT_BYTES + 1)
                    if not raw:
                        break
                    event_hash.update(raw)
                    event_size += len(raw)
                    context = record["event_log"]
                    seq = expected_seq
                    expected_seq += 1
                    if len(raw) > MAX_EVENT_BYTES:
                        self.diagnostic("event_line_size_limit_exceeded", context, seq=seq)
                        break
                    try:
                        event = _strict_json(raw)
                    except (ValueError, UnicodeError, RecursionError):
                        self.diagnostic("event_json_invalid", context, seq=seq)
                        continue
                    self.counts["events"] += 1
                    if not isinstance(event, dict) or type(event.get("schema_version")) is not int or event["schema_version"] != 1:
                        self.diagnostic("unsupported_event_schema", context, seq=seq)
                        continue
                    if type(event.get("seq")) is not int or event["seq"] != seq:
                        self.diagnostic("event_sequence_invalid", context, seq=seq)
                    if event.get("rollout_id") != manifest["rollout_id"]:
                        self.diagnostic("event_rollout_identity_mismatch", context, seq=seq)
                    payload = event.get("payload")
                    if not isinstance(payload, dict) or not _identifier(payload.get("type")):
                        self.diagnostic("event_payload_invalid", context, seq=seq)
                        continue
                    typ = payload["type"]
                    if closed:
                        self.diagnostic("event_after_rollout_ended", context, seq=seq)
                    for key in ("thread_id", "codex_turn_id"):
                        if key not in event or (event[key] is not None and not _identifier(event[key])):
                            self.diagnostic("event_identity_invalid", context, seq=seq)
                        if key in payload and (not _identifier(payload[key]) or (event.get(key) is not None and payload[key] != event[key])):
                            self.diagnostic("event_payload_identity_mismatch", context, seq=seq)
                    thread = event.get("thread_id") or payload.get("thread_id")
                    if _identifier(thread):
                        self.observed_threads.add(thread)
                        if thread not in record["thread_ids"]:
                            record["thread_ids"].append(thread)
                    refs = []
                    try:
                        for item in _walk(payload):
                            if not isinstance(item, dict) or "raw_payload_id" not in item:
                                continue
                            if not _identifier(item["raw_payload_id"]) or not isinstance(item.get("kind"), dict) or not _identifier(item["kind"].get("type")):
                                self.diagnostic("payload_reference_invalid", context, seq=seq)
                                continue
                            ref_path = self.safe_path(bundle, item.get("path"), context=context + ":payload_reference")
                            if ref_path is None:
                                continue
                            if not ref_path.is_relative_to(payload_dir):
                                self.diagnostic("payload_reference_outside_payloads_dir", context, seq=seq)
                                continue
                            identity = (item["path"], item["kind"]["type"])
                            raw_id = item["raw_payload_id"]
                            if raw_id in payload_ids and payload_ids[raw_id] != identity:
                                self.diagnostic("payload_reference_identity_conflict", context, seq=seq)
                                continue
                            payload_ids[raw_id] = identity
                            if ref_path in payload_paths:
                                ref = payload_paths[ref_path]
                                if ref["raw_payload_id"] != raw_id or ref["kind"] != identity[1]:
                                    self.diagnostic("payload_path_identity_conflict", context, seq=seq)
                            else:
                                result = self.read_json(ref_path, MAX_PAYLOAD_BYTES, ref_path.relative_to(self.root).as_posix())
                                if result is None:
                                    continue
                                value, metadata = result
                                ref = dict(metadata, raw_payload_id=raw_id, kind=identity[1])
                                payload_paths[ref_path] = ref
                                record["payloads"].append(ref)
                                self.counts["payloads"] += 1
                                if identity[1] == "inference_request":
                                    self.counts["requests"] += 1
                                if identity[1] == "inference_response":
                                    self.counts["responses"] += 1
                                self.scan_content(value, bundle, metadata["path"])
                            refs.append(ref)
                    except (ValueError, RecursionError):
                        self.diagnostic("event_traversal_limit_exceeded", context, seq=seq)
                    if typ not in _TYPES:
                        self.counts["unknown_events"] += 1
                        self.diagnostic("unrecognized_event_type", context, invalid=False, seq=seq)
                    if typ.startswith("compaction_"):
                        self.counts["compaction_events"] += 1
                        checkpoint = {"bundle": relative, "seq": seq, "event_type": typ,
                                      "thread_id": thread if _identifier(thread) else None,
                                      "codex_turn_id": event.get("codex_turn_id") if _identifier(event.get("codex_turn_id")) else None,
                                      "payloads": refs}
                        for key in ("compaction_id", "compaction_request_id"):
                            if _identifier(payload.get(key)):
                                checkpoint[key] = payload[key]
                        record["compactions"].append(checkpoint)
                        self.compactions.append(checkpoint)
                    if typ in _COUNT_NAMES:
                        self.counts[typ] += 1
                    if typ == "rollout_started":
                        if rollout_started or seq != 1 or payload.get("trace_id") != manifest["trace_id"] or payload.get("root_thread_id") != manifest["root_thread_id"]:
                            self.diagnostic("rollout_start_invalid", context, seq=seq)
                        rollout_started = True
                    elif typ == "rollout_ended":
                        record["rollout_ended"] = True
                        closed = True
                    elif typ == "thread_started":
                        if not _identifier(thread) or thread in threads_started:
                            self.diagnostic("thread_start_invalid", context, seq=seq)
                        elif thread:
                            threads_started.add(thread)
                    elif typ == "thread_ended":
                        if thread not in threads_started or thread in threads_ended:
                            self.diagnostic("thread_end_unpaired", context, seq=seq)
                        else:
                            threads_ended.add(thread)
                    elif typ in {"codex_turn_started", "codex_turn_ended"}:
                        turn_id = event.get("codex_turn_id")
                        if not _identifier(thread) or not _identifier(turn_id):
                            self.diagnostic("turn_identity_invalid", context, seq=seq)
                            continue
                        pair = (thread, turn_id)
                        if typ == "codex_turn_started":
                            if pair in turns_started or thread not in threads_started or thread in threads_ended:
                                self.diagnostic("turn_start_invalid", context, seq=seq)
                            turns_started.add(pair)
                        else:
                            if pair not in turns_started or pair in turns_ended:
                                self.diagnostic("turn_end_unpaired", context, seq=seq)
                            turns_ended.add(pair)
                    elif typ.startswith("inference_") and typ in _TYPES:
                        self.counts[{"inference_started": "inferences_started", "inference_completed": "inferences_completed", "inference_failed": "inferences_failed", "inference_cancelled": "inferences_cancelled"}[typ]] += 1
                        call_id = payload.get("inference_call_id")
                        if not _identifier(call_id) or not _identifier(event.get("thread_id")) or not _identifier(event.get("codex_turn_id")):
                            self.diagnostic("inference_identity_invalid", context, seq=seq)
                            continue
                        if typ == "inference_started":
                            if (event["thread_id"], event["codex_turn_id"]) not in turns_started or (event["thread_id"], event["codex_turn_id"]) in turns_ended:
                                self.diagnostic("inference_turn_not_active", context, seq=seq)
                            if call_id in calls:
                                self.diagnostic("inference_start_duplicate", context, seq=seq)
                                continue
                            call = {"bundle": relative, "inference_call_id": call_id, "thread_id": event["thread_id"], "codex_turn_id": event["codex_turn_id"], "start_seq": seq, "end_seq": None, "request": None, "response": None, "response_is_partial": False, "status": "incomplete"}
                            matching = [ref for ref in refs if ref["kind"] == "inference_request"]
                            if len(matching) != 1:
                                self.diagnostic("inference_request_reference_missing_or_ambiguous", context, seq=seq)
                            else:
                                call["request"] = matching[0]
                            calls[call_id] = call
                            record["inferences"].append(call)
                            self.inferences.append(call)
                        else:
                            call = calls.get(call_id)
                            if call is None or call["end_seq"] is not None:
                                self.diagnostic("inference_end_unpaired", context, seq=seq)
                                continue
                            if call["thread_id"] != event["thread_id"] or call["codex_turn_id"] != event["codex_turn_id"]:
                                self.diagnostic("inference_end_identity_mismatch", context, seq=seq)
                            call.update(end_seq=seq, status={"inference_completed": "completed", "inference_failed": "failed", "inference_cancelled": "cancelled"}[typ])
                            matching = [ref for ref in refs if ref["kind"] == "inference_response"]
                            partial = payload.get("partial_response_payload")
                            if partial is not None:
                                partial_id = partial.get("raw_payload_id") if isinstance(partial, dict) else None
                                if (not _identifier(partial_id) or len(matching) != 1
                                        or matching[0]['raw_payload_id'] != partial_id):
                                    self.diagnostic("partial_response_reference_missing_or_ambiguous", context, seq=seq)
                                else:
                                    call['response_is_partial'] = True
                            if len(matching) > 1:
                                self.diagnostic("inference_response_reference_missing_or_ambiguous", context, seq=seq)
                            response = payload.get('response_payload')
                            if typ == "inference_completed" and (
                                    len(matching) != 1 or not isinstance(response, dict)
                                    or response.get('raw_payload_id') != matching[0]['raw_payload_id']):
                                self.diagnostic("inference_response_reference_missing_or_ambiguous", context, seq=seq)
                            elif matching:
                                call["response"] = matching[0]
                    elif typ in {"tool_call_started", "tool_call_ended"}:
                        self.counts["tool_calls_started" if typ == "tool_call_started" else "tool_calls_ended"] += 1
                        tool_id = payload.get("tool_call_id")
                        if not _identifier(tool_id):
                            self.diagnostic("tool_identity_invalid", context, seq=seq)
                        elif typ == "tool_call_started":
                            if tool_id in tools:
                                self.diagnostic("tool_start_duplicate", context, seq=seq)
                            else:
                                tools[tool_id] = {"ended": False, "thread_id": event.get("thread_id"), "codex_turn_id": event.get("codex_turn_id")}
                        elif tool_id not in tools or tools[tool_id]["ended"]:
                            self.diagnostic("tool_end_unpaired", context, seq=seq)
                        else:
                            if any(tools[tool_id][key] != event.get(key) for key in ("thread_id", "codex_turn_id")):
                                self.diagnostic("tool_end_identity_mismatch", context, seq=seq)
                            tools[tool_id]["ended"] = True
        except OSError:
            self.diagnostic("event_log_unreadable", record["event_log"])
        record["event_log_scanned_bytes"] = event_size
        record["event_log_scanned_sha256"] = event_hash.hexdigest()
        if not rollout_started:
            self.diagnostic("rollout_start_missing", record["event_log"])
        record["incomplete_inference_call_ids"] = [key for key, call in calls.items() if call["end_seq"] is None]
        record["cancelled_inference_call_ids"] = [key for key, call in calls.items() if call["status"] == "cancelled"]
        record["incomplete_tool_call_ids"] = [key for key, call in tools.items() if not call["ended"]]
        record["unended_thread_ids"] = sorted(threads_started - threads_ended)
        record["unended_turns"] = [{"thread_id": thread, "codex_turn_id": turn} for thread, turn in sorted(turns_started - turns_ended)]
        missing_starts = set(record["thread_ids"]) - threads_started
        if missing_starts:
            self.diagnostic("thread_start_missing", record["event_log"])
        if closed and manifest["root_thread_id"] not in threads_started:
            self.diagnostic("root_thread_start_missing", record["event_log"])
        prefix = not closed or bool(record["incomplete_inference_call_ids"] or record["incomplete_tool_call_ids"] or record["unended_thread_ids"] or record["unended_turns"])
        if prefix:
            self.diagnostic("incomplete_trace_prefix", record["event_log"], invalid=False)
        if closed and (record["incomplete_inference_call_ids"] or record["incomplete_tool_call_ids"]) and not self.interrupted:
            self.diagnostic("closed_rollout_has_unfinished_calls", record["event_log"])
        # Terminal failures/cancellations are execution facts. Only missing or
        # invalid evidence makes their recorded lifecycle incomplete.
        record["complete"] = not prefix and not any(d["severity"] == "error" for d in self.diagnostics[diagnostic_start:])

    def run(self, session_ids):
        if self.root.is_symlink():
            self.diagnostic("trace_root_unsafe_or_not_directory", ".")
            return self.result("invalid", session_ids)
        if not self.root.exists():
            self.diagnostic("trace_root_missing", ".", invalid=False)
            return self.result("missing", session_ids)
        if self.root.is_symlink() or not self.root.is_dir():
            self.diagnostic("trace_root_unsafe_or_not_directory", ".")
            return self.result("invalid", session_ids)
        found = []
        try:
            def raise_walk_error(error):
                raise error

            for directory, dirs, files in os.walk(self.root, followlinks=False, onerror=raise_walk_error):
                path = Path(directory)
                for name in dirs[:]:
                    child = path / name
                    if child.is_symlink():
                        self.diagnostic("symlink_forbidden", child.relative_to(self.root).as_posix())
                        dirs.remove(name)
                for name in files:
                    child = path / name
                    if child.is_symlink():
                        self.diagnostic("symlink_forbidden", child.relative_to(self.root).as_posix())
                if "manifest.json" in files:
                    found.append(path)
                    dirs.clear()
                elif path.name.startswith("trace-"):
                    self.diagnostic("bundle_manifest_missing", path.relative_to(self.root).as_posix())
        except OSError:
            self.diagnostic("trace_directory_unreadable", ".")
        for bundle in sorted(found):
            self.bundle(bundle)
        if not found and not self.invalid:
            self.diagnostic("trace_bundles_missing", ".", invalid=False)
        identities = [(bundle["trace_id"], bundle["rollout_id"]) for bundle in self.bundles]
        if len(set(identities)) != len(identities):
            self.diagnostic("duplicate_bundle_identity", ".")
        self.counts["threads"] = len(self.observed_threads)
        return self.result("invalid" if self.invalid else "valid" if self.bundles else "missing", session_ids)

    def result(self, status, session_ids):
        expected = None
        if session_ids is not None:
            if not isinstance(session_ids, list) or any(not _identifier(value) for value in session_ids):
                self.diagnostic("expected_session_identity_invalid", ".")
                status = "invalid"
            else:
                expected = sorted(set(session_ids))
        missing = sorted(set(expected or []) - self.observed_threads)
        coverage = {"status": "unknown" if expected is None else "incomplete" if missing else "complete", "expected": expected, "observed": sorted(self.observed_threads), "missing": missing if expected is not None else None}
        if missing:
            self.diagnostic("expected_sessions_missing", ".", invalid=False)
        replayable = all(image["replayable"] for image in self.images)
        complete = status == "valid" and bool(self.bundles) and all(b["complete"] for b in self.bundles) and not missing and replayable and not self.counts["unknown_events"]
        # Reasons describe evidence gaps, never an unsuccessful model response.
        reasons = [dict(value) for value in self.diagnostics if value['severity'] == 'error'
                   or value['code'] in {'incomplete_trace_prefix',
                       'expected_sessions_missing', 'unrecognized_event_type', 'trace_root_missing', 'trace_bundles_missing'}]
        if not replayable:
            reasons.append({'code': 'image_replay_unavailable', 'path': '.'})
        if not complete and not reasons:
            reasons.append({'code': 'native_trace_not_complete', 'path': '.', 'status': status})
        return {
            "schema_version": 1, "policy": NATIVE_EVIDENCE_POLICY, "status": status,
            "complete": complete,
            "completeness_reasons": [] if complete else reasons,
            "diagnostics": self.diagnostics, "bundles": self.bundles,
            "counts": dict(self.counts), "inferences": self.inferences,
            "compactions": self.compactions,
            "session_coverage": coverage, "images": self.images,
            "image_replay": {"self_contained": replayable if status == "valid" else False if not replayable else None, "validation": "data_url_decoding_and_format_signature_only; external_references_not_fetched; raster_pixels_not_decoded"},
            "termination": {"agent_status": self.agent_status, "interrupted": self.interrupted, "incomplete_inferences": sum(len(b["incomplete_inference_call_ids"]) for b in self.bundles), "cancelled_inferences": self.counts["inferences_cancelled"], "rollouts_without_end": sum(not b["rollout_ended"] for b in self.bundles)},
            "scope": "Native normalized Codex payload index; no payload conversion, HTTP wire capture, or SFT-readiness claim.",
            "limits": {"manifest_bytes": MAX_MANIFEST_BYTES, "event_line_bytes": MAX_EVENT_BYTES, "payload_bytes": MAX_PAYLOAD_BYTES, "json_tree_depth": MAX_TREE_DEPTH, "json_tree_nodes": MAX_TREE_NODES},
        }


def audit_trace(root: Path, *, session_ids: list[str] | None = None, agent_status: str | None = None) -> dict:
    """Audit all bundles below ``root`` without modifying or fetching anything.

    ``session_ids=None`` means expected coverage is unknown. ``complete`` also
    requires closed lifecycle records, all expected sessions, and locally
    available, decodable image references; it does not assert training fitness.
    Diagnostics contain paths/codes/sequence numbers, never request bodies.
    """
    return _Audit(Path(root), agent_status).run(session_ids)
