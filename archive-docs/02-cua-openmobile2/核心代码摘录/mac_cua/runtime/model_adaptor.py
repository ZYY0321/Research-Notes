"""Measured Codex model-route differences; other routes retain their native behavior.

This is not an HTTP client. Codex owns evaluation requests; checks.py owns probes.
Exact Huoshan and Claude routes have measured compatibility overrides.
Claude delegates HTTP translation to a task-local guest bridge.
"""
from __future__ import annotations

import base64
import struct
import zlib

from mac_cua.runtime import gui_strategy

CLAUDE_MESSAGES = "claude-opus-5-5/awsb_L/sfa"


def uses_messages(model: str) -> bool:
    return isinstance(model, str) and model.lower() == CLAUDE_MESSAGES.lower()


def validate_messages_config(agent: dict) -> None:
    """Reject unsupported Claude effort before preparing a guest or HTTP request."""
    if uses_messages(agent.get("model", "")):
        effort = agent.get("reasoning_effort", "medium")
        if effort not in ("low", "medium", "high"):
            raise ValueError("Claude Messages reasoning_effort must be low, medium, or high")


DEEPSEEK_HUOSHAN = "deepseek-v4.1-flash-1017/huoshan/huoshan"


def is_deepseek(model: str) -> bool:
    return isinstance(model, str) and model.lower() == DEEPSEEK_HUOSHAN


def reasoning_summary(model: str, configured: str) -> str:
    if uses_messages(model):
        return "auto"
    if not is_deepseek(model):
        return configured
    if configured not in ("auto", "none"):
        raise ValueError("DeepSeek Huoshan supports reasoning_summary=auto or none only; "
                         "concise/detailed are unsupported. Reasoning effort is unchanged.")
    # Codex omission defaults to auto: explicit none omits the unsupported HTTP field.
    return "none"


class _DeepSeekStrategy:
    """Wrap only the selected route, leaving shared strategy text/resources untouched."""

    def __init__(self, strategy):
        self._strategy = strategy

    def __getattr__(self, name):
        return getattr(self._strategy, name)

    def config_fragments(self, *args):
        _, gui = self._strategy.config_fragments(*args)
        return "[features.code_mode]\nenabled = false\n", gui

    def build_prompt(self, instruction: str, timeout_seconds: int) -> str:
        # Transform framework instructions only, never the original user instruction.
        template = self._strategy.build_prompt("{instruction}", timeout_seconds)
        if self.name == "repl":
            start = template.index("Shell execution and verification:\n")
            end = template.index("Before the first GUI call", start)
            template = template[:start] + _DIRECT_SHELL + template[end:]
            template = template.replace(
                "mcp__cua_repl.js / mcp__cua_repl.js_reset directly, never through functions.exec.\n"
                "CUA tools are unavailable inside functions.exec; use it for shell commands and\n"
                "file operations.",
                "mcp__cua_repl.js / mcp__cua_repl.js_reset directly.")
        return template.replace("{instruction}", instruction)

    def resources(self):
        resources = dict(self._strategy.resources())
        if "cua_adapter.py" in resources:
            resources["cua_adapter.py"] = _direct_adapter(resources["cua_adapter.py"])
        if "cua-skill.md" in resources:
            resources["cua-skill.md"] = _direct_skill(resources["cua-skill.md"])
        return resources

    def launch_payload(self, guest):
        payload = self._strategy.launch_payload(guest)
        if "cua_adapter_source" in payload:
            payload["cua_adapter_source"] = _direct_adapter(payload["cua_adapter_source"])
        if "cua_skill" in payload:
            payload["cua_skill"] = _direct_skill(payload["cua_skill"])
        return payload


class _MessagesStrategy(_DeepSeekStrategy):
    def resources(self):
        from mac_cua.resources import guest_script
        return {**super().resources(), 'anthropic_messages.py': guest_script('anthropic_messages.py')}

    def launch_payload(self, guest):
        return {**super().launch_payload(guest),
                'messages_bridge_source': self.resources()['anthropic_messages.py']}


def select_strategy(value: dict | str):
    if isinstance(value, dict):
        validate_messages_config(value)
    strategy = gui_strategy.select_strategy(value)
    if isinstance(value, dict) and uses_messages(value.get("model", "")):
        return _MessagesStrategy(strategy)
    if isinstance(value, dict) and is_deepseek(value.get("model", "")):
        return _DeepSeekStrategy(strategy)
    return strategy


def _direct_adapter(source: str) -> str:
    # INSTRUCTIONS is exposed both by MCP initialize and tools/list. Adapt the
    # deployed copy as well as the hashed resource; leave driver logic untouched.
    return source.replace(
        "Call cua_repl.js and cua_repl.js_reset directly, never through functions.exec.\n"
        "Use js for GUI actions; functions.exec is for non-CUA tools, not shell/osascript GUI work.",
        "Call cua_repl.js and cua_repl.js_reset directly.\n"
        "Use js for GUI actions; call exec_command and write_stdin directly for non-CUA work, "
        "not shell/osascript GUI work.")


def _direct_skill(skill: str) -> str:
    return skill.replace(
        "CUA is unavailable inside\n`functions.exec`; that tool remains available for shell/file operations.",
        "For shell/file operations, call exec_command and write_stdin directly using their tool schemas."
    ).replace(
        "Use `functions.exec`\nwith `tools.exec_command` as described by those tools.",
        "Call `exec_command` directly; poll running sessions with `write_stdin`.")


_DIRECT_SHELL = '''Shell execution and verification:
Call exec_command directly with JSON arguments, not JavaScript. For example:
```json
{"cmd": "ls -l ~/Desktop", "yield_time_ms": 10000, "max_output_tokens": 2000}
```
Commands run inside the evaluation VM, not on the host; no Terminal App window is needed.
Use the actual task's output path. Set workdir explicitly when needed and quote shell paths.
Prefer read-only checks of GUI-produced artifacts: actual contents, format and metadata,
not just file existence. Inspect exit_code and output. Combine checks with AX/screenshots
where visual state matters. Respect the task's restrictions: shell verification does not
replace required GUI actions or reopening files in their application.
If exec_command returns session_id, call write_stdin directly with that session_id,
chars="", yield_time_ms=1000 and max_output_tokens=2000. Poll the existing session;
do not rerun the command. Shell session IDs are unrelated to cua_repl bindings.

'''


def probe_reasoning(agent_cfg: dict) -> dict:
    if is_deepseek(agent_cfg["model"]):
        reasoning_summary(agent_cfg["model"], agent_cfg.get("reasoning_summary", "auto"))
    # Preserve target-branch probes for GPT/GLM: effort only, without summary.
    return {"effort": agent_cfg["reasoning_effort"]}


def probe_output(model: str) -> str | list[dict]:
    if not is_deepseek(model):
        return "ok"

    def chunk(kind, value):
        return (struct.pack(">I", len(value)) + kind + value +
                struct.pack(">I", zlib.crc32(kind + value) & 0xffffffff))

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 128, 128, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress((b"\x00" + b"\x00\x00\xff" * 128) * 128)) + chunk(b"IEND", b"")
    return [{"type": "input_text", "text": "Inspect this tool-result image. Reply with its dominant color only, in lowercase English."},
            {"type": "input_image", "image_url": "data:image/png;base64," + base64.b64encode(png).decode()}]


def probe_completed(model: str, response: dict) -> bool:
    completed = response.get("status") == "completed"
    messages = [item for item in response.get("output", []) if item.get("type") == "message"]
    if not is_deepseek(model):
        return completed and bool(messages)
    answer = "".join(part.get("text", "") for item in messages for part in item.get("content", [])
                     if part.get("type") == "output_text")
    if not completed or answer.strip().lower() != "blue":
        raise ValueError("Responses probe 2 did not identify the tool-result image as blue")
    return True
