"""Read-only host checks and a small explicit Responses capability probe."""
from __future__ import annotations

import base64
import json
import platform
import shutil
import subprocess
import struct
import zlib
from pathlib import Path

import httpx

from mac_cua.images.profiles.macarena import adapter
discover_tasks, _bundle_root = adapter.legacy.discover_tasks, adapter.legacy._bundle_root
from mac_cua.config import Config
from mac_cua.foundation.records import now
from mac_cua.credentials import load_secrets
from mac_cua.runtime.model_adaptor import probe_reasoning, probe_output, probe_completed, uses_messages
from mac_cua.privacy import redact
from mac_cua.util import atomic_json


def verify_bundle() -> dict:
    from mac_cua.util import sha256_file
    root = _bundle_root()
    manifest = json.loads((root / "provenance.json").read_text())
    suite = json.loads((root / "suite.json").read_text())
    selected = {Path(path).parent.name for path in suite["tasks"]}
    included = {name: record for name, record in manifest["files"].items()
                if not name.startswith(("tasks/", "vm_files/")) or Path(name).stem in selected}
    mismatches = [name for name, record in included.items()
        if not (root / name).is_file() or sha256_file(root / name) != record["sha256"]]
    return {"ok": not mismatches, "files_checked": len(included),
            "mismatches": mismatches, "upstream_commit": manifest["upstream_commit"]}


def doctor(config: Config) -> dict:
    commands = {"orchard": [config.orchard["binary"], "--version"]}
    if config.data.get("_host"):
        commands["tart"] = [config.data["_host"]["tart_binary"], "--version"]
    versions = {}
    for name, args in commands.items():
        try:
            p = subprocess.run(args, capture_output=True, text=True, timeout=15)
            versions[name] = {"ok": p.returncode == 0, "version": (p.stdout + p.stderr).strip()}
        except (OSError, subprocess.TimeoutExpired) as exc:
            versions[name] = {"ok": False, "error": str(exc)}
    space = shutil.disk_usage(config.root)
    return {"platform": platform.platform(), "architecture": platform.machine(),
            "python": platform.python_version(), "free_disk_bytes": space.free,
            "versions": versions, "task_count": len(discover_tasks()),
            "bundle": verify_bundle(), "image_download_complete": (config.paths.official_download / "download-complete.json").exists(),
            "baseline_frozen": (config.paths.state / "baseline.json").exists(),
            "env_file_present": (config.root / ".env").exists()}


def model_check(config: Config) -> dict:
    """Two tiny Responses calls verify image input and a complete function-call turn."""
    secrets = load_secrets(config)
    if uses_messages(config.agent['model']):
        from mac_cua.runtime.messages_check import model_check as messages_model_check
        return _save_model_check(config, messages_model_check(config, secrets), secrets)
    # A valid deterministic 128px red PNG, with no guest or host content.
    def chunk(kind, value):
        return struct.pack(">I", len(value)) + kind + value + struct.pack(">I", zlib.crc32(kind + value) & 0xffffffff)
    raw = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 128, 128, 8, 2, 0, 0, 0))
    raw += chunk(b"IDAT", zlib.compress((b"\x00" + b"\xff\x00\x00" * 128) * 128)) + chunk(b"IEND", b"")
    png = base64.b64encode(raw).decode()
    request = {"model": config.agent["model"], "reasoning": probe_reasoning(config.agent),
               "input": [{"role": "user", "content": [{"type": "input_text", "text": "This is a capability check. Inspect the attached image, then call capability_probe with its dominant color name in lowercase English as value."},
                                                       {"type": "input_image", "image_url": "data:image/png;base64," + png}]}],
               "tools": [{"type": "function", "name": "capability_probe", "description": "A local compatibility probe; no external effects.",
                          "parameters": {"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"], "additionalProperties": False}, "strict": True}],
               "tool_choice": {"type": "function", "name": "capability_probe"}, "max_output_tokens": 512, "store": False}
    policy = config.agent.get("response_model_policy", "strict")
    expected_model = config.agent.get("expected_response_model", config.agent["model"])
    result = {"checked_at": now(), "requested_model": config.agent["model"],
              "response_model_policy": policy, "expected_response_model": expected_model if policy == "strict" else None, "ok": False, "calls": []}
    endpoint = secrets["OPENAI_BASE_URL"].rstrip("/") + "/responses"
    headers = {"Authorization": "Bearer " + secrets["OPENAI_API_KEY"]}
    try:
        with httpx.Client(timeout=180, follow_redirects=False) as client:
            response = client.post(endpoint, json=request, headers=headers)
            result["calls"].append({"http_status": response.status_code})
            if response.is_error:
                result["calls"][-1]["error_body"] = response.text[:4000]
            response.raise_for_status()
            data = response.json()
            result["calls"][-1].update({k: data.get(k) for k in ("id", "model", "status", "usage", "error")})
            if policy == "strict" and data.get("model") != expected_model:
                raise ValueError(f"Responses probe 1 returned model {data.get('model')!r}; "
                                 f"requested_model is {result['requested_model']!r}, expected_response_model is {expected_model!r}; model substitution is not allowed")
            calls = [v for v in data.get("output", []) if v.get("type") == "function_call" and v.get("name") == "capability_probe"]
            if len(calls) != 1 or json.loads(calls[0]["arguments"]).get("value") != "red":
                raise ValueError("Responses did not return the requested valid function call")
            follow = {k: v for k, v in request.items() if k != "tool_choice"}
            follow["input"] = request["input"] + data["output"] + [{"type": "function_call_output", "call_id": calls[0]["call_id"], "output": probe_output(config.agent["model"])}]
            follow["tool_choice"] = "none"
            response = client.post(endpoint, json=follow, headers=headers)
            result["calls"].append({"http_status": response.status_code})
            if response.is_error:
                result["calls"][-1]["error_body"] = response.text[:4000]
            response.raise_for_status()
            data = response.json()
            result["calls"][-1].update({k: data.get(k) for k in ("id", "model", "status", "usage", "error")})
            if policy == "strict" and data.get("model") != expected_model:
                raise ValueError(f"Responses probe 2 returned model {data.get('model')!r}; "
                                 f"requested_model is {result['requested_model']!r}, expected_response_model is {expected_model!r}; model substitution is not allowed")
            result["ok"] = probe_completed(config.agent["model"], data)
    except Exception as exc:
        result["error"] = redact(f"{type(exc).__name__}: {exc}", secrets)
    return _save_model_check(config, result, secrets)


def _save_model_check(config, result, secrets):
    """Persist the same redacted latest result and history for every protocol."""
    result = redact(result, secrets)
    atomic_json(config.paths.state / "model-check.json", result)
    history = config.paths.state / "model-check-history.jsonl"
    with history.open("a") as stream:
        stream.write(json.dumps(result) + "\n")
    return result
