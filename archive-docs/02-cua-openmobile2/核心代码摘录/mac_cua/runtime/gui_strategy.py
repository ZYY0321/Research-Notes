"""Codex-owned GUI strategies; the platform sees only the Agent adapter."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import PurePosixPath
import shlex

from mac_cua.resources import data_path, guest_script

NODE_VERSION = "v22.22.1"
CUA_ADAPTER = guest_script('cua_adapter.py')
CUA_EVIDENCE = guest_script('cua_evidence.py')
CUA_REPL = guest_script('cua_repl.mjs')
CUA_BROWSER = guest_script('cua_browser.py')
CUA_SKILL = data_path('skills/mac-cua/SKILL.md').read_text()


@dataclass(frozen=True)
class GuiStrategy:
    name: str
    mcp_name: str
    optional_evidence: tuple[str, ...] = ()

    def validate_paths(self, cua_binary: str, python_binary: str, node_binary: str) -> None:
        if not PurePosixPath(cua_binary).is_absolute():
            raise ValueError('cua_binary must be an absolute guest executable path')

    def config_fragments(self, cua_binary: str, python_binary: str, node_binary: str) -> tuple[str, str]:
        raise NotImplementedError

    def resources(self) -> dict[str, str]:
        return {}

    def launch_payload(self, guest: dict) -> dict:
        return {'gui_strategy': self.name}

    def required_guest(self, guest: dict) -> dict:
        return {}

    def version_checks(self) -> dict[str, str]:
        return {}

    def self_test(self, provider, vm: str, guest: dict, *, budget=None) -> dict:
        return {}

    def build_prompt(self, instruction: str, timeout_seconds: int) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class ReplStrategy(GuiStrategy):
    name: str = 'repl'
    mcp_name: str = 'cua_repl'
    optional_evidence: tuple[str, ...] = ('cua-evidence/', 'browser-control/')

    def build_prompt(self, instruction: str, timeout_seconds: int) -> str:
        return _repl_prompt(instruction, timeout_seconds)

    def validate_paths(self, cua_binary: str, python_binary: str, node_binary: str) -> None:
        super().validate_paths(cua_binary, python_binary, node_binary)
        for key, value in (('python_binary', python_binary), ('node_binary', node_binary)):
            if not PurePosixPath(value).is_absolute():
                raise ValueError(f'{key} must be an absolute guest executable path')

    def config_fragments(self, cua_binary: str, python_binary: str, node_binary: str) -> tuple[str, str]:
        q = lambda value: json.dumps(value, ensure_ascii=False)
        return ('''[features.code_mode]
enabled = true
direct_only_tool_namespaces = ["mcp__cua_repl"]
''', f'''[mcp_servers.cua_repl]
command = {q(python_binary)}
args = ["-u", "MAC_CUA_ADAPTER_PATH", "--driver", {q(cua_binary)}, "--node", {q(node_binary)}, "--evidence-dir", "MAC_CUA_EVIDENCE_PATH"]
required = true
startup_timeout_sec = 60
tool_timeout_sec = 150
''')

    def resources(self) -> dict[str, str]:
        return {'cua_adapter.py': CUA_ADAPTER, 'cua_evidence.py': CUA_EVIDENCE, 'cua_repl.mjs': CUA_REPL,
                'cua_browser.py': CUA_BROWSER, 'cua-skill.md': CUA_SKILL}

    def launch_payload(self, guest: dict) -> dict:
        return {**super().launch_payload(guest), 'cua_adapter_source': CUA_ADAPTER,
                'cua_evidence_source': CUA_EVIDENCE,
                'cua_repl_source': CUA_REPL, 'cua_skill': CUA_SKILL,
                'cua_browser_source': CUA_BROWSER,
                'node_binary': guest.get('node_binary', '/usr/local/bin/node')}

    def required_guest(self, guest: dict) -> dict:
        result = {'node_binary': guest.get('node_binary', '/usr/local/bin/node'), 'node_version': NODE_VERSION}
        keys = ('browser_python_binary', 'browser_harness_version', 'browser_harness_source_commit')
        if any(guest.get(key) for key in keys):
            if not all(guest.get(key) for key in keys):
                raise ValueError('Incomplete browser runtime metadata')
            result.update({key: guest[key] for key in keys})
        return result

    def version_checks(self) -> dict[str, str]:
        return {'node_binary': NODE_VERSION}

    def self_test(self, provider, vm: str, guest: dict, *, budget=None) -> dict:
        node = guest.get('node_binary', '/usr/local/bin/node')
        response = provider.ssh(vm, shlex.join([node, '--input-type=module', '-', '--self-test']),
                                input=CUA_REPL.encode(), timeout=budget.rpc_timeout() if budget else 30)
        actual = response.stdout.decode().strip() if isinstance(response.stdout, bytes) else response.stdout.strip()
        if response.returncode or actual != 'CUA_REPL_OK':
            raise RuntimeError('Guest CUA REPL self-test failed')
        result = {'cua_repl_self_test': 'passed'}
        if guest.get('browser_python_binary'):
            probe = '''import importlib.metadata as m,importlib.util,json,pathlib,browser_harness
if importlib.util.find_spec('browser_harness.dom') is None:
    raise RuntimeError('Install current numbered-DOM browser-harness build')
print(json.dumps({'version':m.version('browser-harness'), 'source_commit':json.loads(pathlib.Path(browser_harness.__file__).with_name('_build_info.json').read_text())['source_commit']}))'''
            checked = provider.ssh(vm, shlex.join([guest['browser_python_binary'], '-c', probe]), timeout=budget.rpc_timeout() if budget else 30)
            if checked.returncode:
                raise RuntimeError('Guest browser runtime self-test failed')
            actual = json.loads(checked.stdout)
            if actual != {'version':guest['browser_harness_version'], 'source_commit':guest['browser_harness_source_commit']}:
                raise RuntimeError('Guest browser runtime identity mismatch')
            result['browser_runtime_self_test'] = 'passed'
        return result


@dataclass(frozen=True)
class DirectStrategy(GuiStrategy):
    name: str = 'direct'
    mcp_name: str = 'cua'

    def build_prompt(self, instruction: str, timeout_seconds: int) -> str:
        return _direct_prompt(instruction, timeout_seconds)

    def config_fragments(self, cua_binary: str, python_binary: str, node_binary: str) -> tuple[str, str]:
        return ('', f'''[mcp_servers.cua]
command = {json.dumps(cua_binary, ensure_ascii=False)}
args = ["mcp"]
required = true
startup_timeout_sec = 60
tool_timeout_sec = 120
''')


STRATEGIES: dict[str, GuiStrategy] = {'repl': ReplStrategy(), 'direct': DirectStrategy()}


def select_strategy(value: dict | str) -> GuiStrategy:
    name = value.get('gui_strategy', 'repl') if isinstance(value, dict) else value
    try:
        return STRATEGIES[name]
    except (KeyError, TypeError) as error:
        raise ValueError('Codex GUI strategy must be repl or direct') from error


def _check_prompt(instruction: str, timeout_seconds: int) -> None:
    if not instruction.strip():
        raise ValueError("A nonempty original task instruction is required")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")


def _direct_prompt(instruction: str, timeout_seconds: int) -> str:
    _check_prompt(instruction, timeout_seconds)
    return f'''You are operating a real, isolated macOS virtual machine. Complete the user's task autonomously and verify the resulting files or application state.

You may freely combine GUI observation and actions through the cua MCP tools with shell commands, code execution, file operations, APIs/network access, and any other available capabilities. Choose methods according to the task. There is no required GUI action count or preferred interaction modality. The selected GUI MCP is mcp__cua; use its available tools directly when using that interface.

You may use subagents for useful independent work. All agents share this VM, its files, and the same desktop; coordinate GUI actions to avoid simultaneous interference. Subagents must use the configured model and reasoning effort: do not override either setting when spawning or messaging an agent, and do not modify the configured model or reasoning effort. Keep all memory and working notes within this task. Do not use information or memory from other tasks.

Work without waiting for a human response. When finished, state what you completed and any unresolved limitations concisely. Leave the task's files and application state available for inspection.

Original user task:
{instruction}
'''


def _repl_prompt(instruction: str, timeout_seconds: int) -> str:
    _check_prompt(instruction, timeout_seconds)
    return f'''You are operating a real, isolated macOS virtual machine. Complete the user's task autonomously and verify the resulting files or application state.

You may freely combine GUI observation and actions through the cua MCP tools with shell commands, code execution, file operations, APIs/network access, and any other available capabilities. Choose methods according to the task. There is no required GUI action count or preferred interaction modality.

Shell execution and verification:
Call functions.exec with JavaScript that invokes tools.exec_command; functions.exec
itself runs JavaScript, not shell syntax. Commands run inside the evaluation VM,
not on the host. No Terminal App window is needed. For example:
```javascript
const result = await tools.exec_command({{
  cmd: 'test -f "$HOME/Desktop/hello-mac-cua.txt" && cat "$HOME/Desktop/hello-mac-cua.txt"',
  yield_time_ms: 10000,
  max_output_tokens: 2000
}});
text(result);
```
Use the actual task's output path, not this illustrative filename. Set workdir
explicitly when a command depends on its working directory, and quote shell paths.
Prefer read-only shell checks to verify GUI-produced artifacts: file existence,
actual saved contents (including missing/duplicated text), format, or metadata.
Inspect the command's exit_code and output; file existence alone is not proof of
correct content. Combine file checks with AX/screenshots when visual or application
state matters. Respect explicit task restrictions: shell verification supplements,
not replaces, required GUI actions or reopening the file in its application.
If exec_command returns session_id, the command is still running; use
functions.exec to call tools.write_stdin({{session_id: actualSessionId, chars: "",
yield_time_ms: 1000, max_output_tokens: 2000}}) and text its result. Poll the existing
session rather than rerunning the command. If functions.exec itself yields a cell ID,
resume it with functions.wait as instructed by that tool. Do not confuse these IDs
with each other or with cua_repl bindings.

Before the first GUI call, read $CODEX_HOME/skills/mac-cua/SKILL.md for API documentation
and usage rules. The cua_repl MCP server exposes
js(code, title?, timeout_ms?) and js_reset() as direct model tools. Call
mcp__cua_repl.js / mcp__cua_repl.js_reset directly, never through functions.exec.
CUA tools are unavailable inside functions.exec; use it for shell commands and
file operations. When using the selected GUI MCP, send those actions through cua_repl.
CLI, application scripting and other task-allowed methods remain available. Tool text/images return
directly to the model without an outer forwarding wrapper. JS variables persist inside js.
First call (also after reset) must only select an app/browser or discover state with
let TextEdit = await cua.getApp("TextEdit"); or await cua.getState();
For configured Chrome tasks: let browser = await cua.getBrowser("chrome");
Read the returned initial state before continuing. Await every action.
Use concrete app variable names (TextEdit, Safari), never app/app1; reuse each app reference.
Use listWindows() to inspect app windows; the adapter resolves the current window automatically.
AX observations return the active app menu, matching attached sheet/popover, or verified current window.
AX and screenshots never activate windows. Attached-surface input requires a verified AX chain
and foreground app; keyboard input also needs fresh focused-control evidence. Observe after actions.
Omit timeout_ms for the 60-second cell budget; allow at least 30 seconds for GUI actions
and 60 seconds for combined actions plus observation, including internal driver checks.
After dialogs/window changes or errors, observe again before input; never reuse old coordinates.
Screenshots are driver-returned target images, not an app-wide composite; sheet images may include other surfaces.
Use TextEdit.getAXState(), getScreenshot(), getAXStateAndScreenshot(); emit:false retains data
without emitting it. Use nodeRepl.write and nodeRepl.emitImage for explicit output.
Consecutive coordinates/keys are allowed while the window frame is unchanged; element IDs
require a new observation after mutations. Observe actual effects before retrying.
AX IDs are zero-based positions in each app's latest snapshot, not permanent identities.
Prefer default diff observations and reuse the app reference. Apply displayed diffs
before using IDs; request disableDiffing:true only when a full snapshot is needed.
On macOS, use setValue(index, value) only for a writable editable control in an
ordinary current window. Never use setValue in native Open, Save, or Go to Folder
dialogs, including attached sheets and supplemental panels. Focus their filename,
path, or search field, select its existing contents when needed, and use paste; observe
afterward before continuing. Use typeText for insertion/appending or keyboard-driven
input behavior. Paste supports plain text only and leaves it on the clipboard without
restoring previous contents. Do not use setValue for rich/custom controls, canvases,
non-editable elements, stale indexes, or Linux Computer Use.
Observe after paste errors; do not replay. selectText and performSecondaryAction remain unsupported.
Configured Chrome pages use Browser/Tab APIs through the same cua_repl; native surfaces use App APIs.
Browser coordinates use viewport CSS pixels. Observe after changes; never fall back or replay on browser errors.
Browser tasks use one Agent; multi_agent is disabled for their execution.
Do not enumerate ALL_TOOLS or dump driver schemas. Timeout/reset clears JS bindings,
not application changes. Subagents have separate JS sessions but share the desktop;
coordinate ownership and never issue simultaneous GUI operations.

You may use subagents for useful independent work. All agents share this VM, its files, and the same desktop; coordinate GUI actions to avoid simultaneous interference. Subagents must use the configured model and reasoning effort: do not override either setting when spawning or messaging an agent, and do not modify the configured model or reasoning effort. Keep all memory and working notes within this task. Do not use information or memory from other tasks.

Work without waiting for a human response. When finished, state what you completed and any unresolved limitations concisely. Leave the task's files and application state available for inspection.

Original user task:
{instruction}
'''
