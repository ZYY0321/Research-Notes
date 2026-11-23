"""One native Codex session inside an already prepared, disposable guest VM."""
from __future__ import annotations

from mac_cua.resources import guest_script
from mac_cua.foundation.runtime import ResolvedRuntime, reject_global_extensions
from mac_cua.foundation.execution import CollectionResult
from mac_cua.foundation.preparation import PreparationBudget, execution_policy
from mac_cua.infrastructure.cua import wait_default_ready
from mac_cua.infrastructure.guest import Guest
from mac_cua.runtime.gui_strategy import CUA_ADAPTER, CUA_REPL, CUA_SKILL, NODE_VERSION
from mac_cua.runtime.model_adaptor import select_strategy, reasoning_summary, uses_messages

import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import threading
import time
from mac_cua.privacy import redact
from urllib.parse import urlsplit
import uuid

from mac_cua.util import atomic_json
from mac_cua.runtime.trace_export import POLICY as TRACE_POLICY, trace_enabled

def gui_strategy(agent_cfg: dict) -> str:
    return select_strategy(agent_cfg).name


def load_credentials(config) -> dict:
    from mac_cua.credentials import load_secrets
    return load_secrets(config)


def build_codex_config(agent_cfg: dict, base_url: str, cua_binary: str,
                       runtime: ResolvedRuntime | None = None, *,
                       python_binary: str = '/usr/local/bin/python3.11',
                       node_binary: str = '/usr/local/bin/node') -> str:
    """Build a Codex 0.153.4 config; authentication is exclusively an env lookup."""
    reject_global_extensions(agent_cfg)
    runtime = runtime or ResolvedRuntime()
    strategy = select_strategy(agent_cfg)
    browser_url = runtime.env.get('MAC_CUA_BROWSER_CDP_URL')
    if browser_url and strategy.name != 'repl':
        raise ValueError('Browser runtime requires the repl GUI strategy')
    if agent_cfg.get("id", "codex") != "codex":
        raise ValueError("Codex adapter requires agent.id=codex")
    parsed = urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("OPENAI_BASE_URL must be an absolute HTTP(S) API base URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("OPENAI_BASE_URL must not contain credentials, query, or fragment")
    strategy.validate_paths(cua_binary, python_binary, node_binary)
    code_mode, gui_config = strategy.config_fragments(cua_binary, python_binary, node_binary)
    if browser_url:
        gui_config = gui_config.replace('"MAC_CUA_EVIDENCE_PATH"]',
            '"MAC_CUA_EVIDENCE_PATH", "--browser-config", "MAC_CUA_BROWSER_CONFIG_PATH"]')
    if any(skill.get("name") == "mac-cua" for skill in runtime.skills):
        raise ValueError("Task skills cannot replace the built-in mac-cua skill")
    q = lambda value: json.dumps(value, ensure_ascii=False)
    model = agent_cfg.get("model", "gpt-5.6-luna")
    effort = agent_cfg.get("reasoning_effort", "medium")
    summary = agent_cfg.get("reasoning_summary", "auto")
    if summary not in ("auto", "concise", "detailed", "none"):
        raise ValueError("Codex agent.reasoning_summary must be auto, concise, detailed, or none")
    summary = reasoning_summary(model, summary)
    threads = int(agent_cfg.get("max_subagents", 3))
    if threads < 1:
        raise ValueError("max_subagents must be positive")
    from mac_cua.runtime.extensions import extension_config
    extra = extension_config(runtime)
    credential_config = 'mcp_oauth_credentials_store = "file"\n' if runtime.credentials_file else ""
    return f'''{credential_config}model = {q(model)}
model_provider = "evaluation"
model_reasoning_effort = {q(effort)}
model_reasoning_summary = {q(summary)}
approval_policy = "never"
sandbox_mode = "danger-full-access"
web_search = {q("disabled" if uses_messages(model) else "live")}

[analytics]
enabled = false

[features]
multi_agent = {str(not bool(browser_url) and not uses_messages(model)).lower()}
memories = false
shell_snapshot = false

{code_mode}
[agents]
enabled = true
max_concurrent_threads_per_session = {threads}
default_subagent_model = {q(model)}
default_subagent_reasoning_effort = {q(effort)}

[memories]
generate_memories = false
use_memories = false

[model_providers.evaluation]
name = "Evaluation Responses API"
base_url = {q(base_url.rstrip('/'))}
wire_api = "responses"
env_key = "OPENAI_API_KEY"
requires_openai_auth = false
stream_max_retries = 8
request_max_retries = 6

{gui_config}
''' + extra


def build_prompt(instruction: str, timeout_seconds: int, *, strategy: str | dict = "repl",
                 skill_names: tuple[str, ...] = ()) -> str:
    prompt = select_strategy(strategy).build_prompt(instruction, timeout_seconds)
    names = tuple(dict.fromkeys(skill_names))
    if names:
        paths = "\n".join(f"- $CODEX_HOME/skills/{name}/SKILL.md" for name in names)
        prompt += ("\nBefore starting the task, read each declared task or application skill "
                   "below and follow its instructions:\n" + paths + "\n")
    return prompt


# This source is self-contained: the guest does not need this Python package.
# In particular, launch JSON (including the key) is never written to disk.
GUEST_SUPERVISOR = guest_script('agent-guest_supervisor.py')


def identity(config) -> dict:
    """Execution-affecting Codex identity; no credentials or repository-wide hash."""
    import hashlib
    from mac_cua.runtime import extensions, model_adaptor, gui_strategy as gui_strategy_module
    from mac_cua.infrastructure import cua as cua_module
    agent = config.agent if hasattr(config, "agent") else config
    strategy = select_strategy(agent)
    payloads = [('agent.py', Path(__file__).read_bytes()),
                ('gui_strategy.py', Path(gui_strategy_module.__file__).read_bytes()),
                ('extensions.py', Path(extensions.__file__).read_bytes()),
                ('infrastructure/cua.py', Path(cua_module.__file__).read_bytes()),
                ('cua-observation.py', cua_module.OBSERVATION_SCRIPT.encode()),
                ('agent-guest_supervisor.py', GUEST_SUPERVISOR.encode())]
    payloads.append(('model_adaptor.py', Path(model_adaptor.__file__).read_bytes()))
    payloads.extend((name, content.encode()) for name, content in strategy.resources().items())
    digest = hashlib.sha256()
    for name, raw in payloads:
        digest.update(name.encode() + b'\0')
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return {"id": "codex", "version": "1", "gui_strategy": strategy.name,
            "payload_sha256": digest.hexdigest(),
            "optional_evidence": list(strategy.optional_evidence)}


def requirements(config) -> dict:
    agent = config.agent if hasattr(config, "agent") else config
    guest = config.guest if hasattr(config, "guest") else {}
    result = {"python_binary": guest.get("python_binary", "/usr/local/bin/python3.11"),
              "codex_binary": guest.get("codex_binary", "/usr/local/bin/codex"),
              "codex_version": agent.get("codex_version", "0.153.4"),
              "cua_binary": guest.get("cua_binary", "/usr/local/bin/cua-driver"),
              "cua_driver_version": agent.get("cua_driver_version", "0.25.0")}
    result.update(select_strategy(agent).required_guest(guest))
    return {"guest": result, "inventory": {}, "gui_strategy": select_strategy(agent).name}


def validate_config(config) -> None:
    agent = config.agent if hasattr(config, "agent") else config
    if agent.get('id', 'codex') != 'codex':
        raise ValueError('Codex adapter requires agent.id=codex')
    select_strategy(agent)
    if agent.get("reasoning_summary", "auto") not in ("auto", "concise", "detailed", "none"):
        raise ValueError("Codex agent.reasoning_summary must be auto, concise, detailed, or none")
    for key in ('model', 'reasoning_effort'):
        if key in agent and (not isinstance(agent[key], str) or not agent[key].strip()):
            raise ValueError(f'Codex agent.{key} must be a nonempty string')
    reasoning_summary(agent.get("model", ""), agent.get("reasoning_summary", "auto"))
    for key in ('timeout_seconds', 'max_subagents'):
        if key in agent and (type(agent[key]) is not int or agent[key] < 1):
            raise ValueError(f'Codex agent.{key} must be a positive integer')


class AgentRunner:
    def __init__(self, config, provider):
        self.config = config
        self.provider = provider
        self.shared_dir = None
        self.on_prepared = None
        self.runtime = ResolvedRuntime()
        from mac_cua.runtime.extensions import CodexRuntimeAdapter
        self.runtime_adapter = CodexRuntimeAdapter()

    identity = staticmethod(identity)
    @staticmethod
    def audit_evidence(output, record):
        from mac_cua.runtime.collection import audit_saved_evidence
        return audit_saved_evidence(output, record)

    @staticmethod
    def evidence_contract(config):
        return {'policy': 'codex-native-v2', 'required_kinds': ['trace', 'events', 'sessions']}
    requirements = staticmethod(requirements)
    validate_config = staticmethod(validate_config)

    def _guest(self) -> dict:
        from mac_cua.infrastructure.guest import guest_settings
        return guest_settings(self.config)

    def guest_settings(self) -> dict:
        return self._guest()

    def prepare_shared(self, output: Path, secrets: dict) -> None:
        if self.config.agent.get('rollout_trace', True) is not True:
            raise ValueError('Codex evaluation requires rollout_trace=true')
        output.mkdir(parents=True, exist_ok=True)
        strategy = select_strategy(self.config.agent)
        (output / 'prompt-template.txt').write_text(strategy.build_prompt('{instruction}', self.config.agent.get('timeout_seconds', 1200)))
        (output / 'supervisor.py').write_text(GUEST_SUPERVISOR)
        for name, content in strategy.resources().items():
            (output / name).write_text(content)
        guest = self._guest()
        settings = build_codex_config(self.config.agent, secrets.get('OPENAI_BASE_URL') or 'https://api.openai.com/v1',
                                      guest.get('cua_binary', '/usr/local/bin/cua-driver'),
                                      python_binary=guest.get('python_binary', '/usr/local/bin/python3.11'),
                                      node_binary=guest.get('node_binary', '/usr/local/bin/node'))
        if self.config.data.get('network', {}).get('api_transport') in {'host-connect', 'controller-connect'}:
            settings += '\n[shell_environment_policy]\nexclude = ["HTTPS_PROXY", "https_proxy"]\n'
        (output / 'codex-base.toml').write_text(settings)

    def prepare(self, vm: str, *, budget: PreparationBudget | None = None) -> dict:
        budget = budget or PreparationBudget(execution_policy(self.config.data))
        versions = {}
        guest = self._guest()
        strategy = select_strategy(self.config.agent)
        expected_versions = {'python_binary': '3.11',
                             'codex_binary': self.config.agent.get('codex_version', '0.153.4'),
                             'cua_binary': self.config.agent.get('cua_driver_version', '0.25.0')}
        expected_versions.update(strategy.version_checks())
        required = requirements(self.config)['guest']
        for key, expected in expected_versions.items():
            result = budget.execute('runtime.version.' + key, lambda: self.provider.ssh(
                vm, shlex.join([guest.get(key, required[key]), '--version']), timeout=budget.rpc_timeout()))
            value = result.stdout.decode(errors='replace') if isinstance(result.stdout, bytes) else result.stdout
            if result.returncode or (value.strip() != expected if key == 'node_binary' else expected not in value):
                raise RuntimeError('Guest runtime unavailable or incompatible: ' + key)
            versions[key] = value.strip()
        versions.update(budget.execute('runtime.self_test', lambda: strategy.self_test(self.provider, vm, guest, budget=budget)))
        versions["cua_readiness"] = wait_default_ready(Guest(self.provider, vm, settings=guest), budget=budget)
        return versions

    def stop(self, vm: str, remote: str, output: Path, secrets: dict) -> dict:
        remote = remote['directory'] if isinstance(remote, dict) else remote
        python = self._guest().get('python_binary', '/usr/local/bin/python3.11')
        result = self.provider.ssh(vm, shlex.join([python, remote + '/supervisor.py', 'stop']), timeout=25)
        if result.returncode:
            raise RuntimeError('Agent stop could not be confirmed')
        state = self._read_state(vm, remote, output, secrets)
        state['remote_run_dir'] = remote
        state['recovery'] = {'directory': remote}
        return state

    def recover(self, vm: str, remote: str, output: Path, secrets: dict) -> dict:
        return self.stop(vm, remote, output, secrets)

    def confirm_agent_stop(self, vm, state, output, secrets) -> dict:
        handle = state.get('recovery')
        native = self.stop(vm, handle, output, secrets) if handle else state
        return {'stopped': self._safe_to_grade(native), 'native': native}

    def collect_result(self, vm, state, output, secrets) -> CollectionResult:
        from mac_cua.runtime.collection import normalize_collection
        native = dict(state)
        if state.get('recovery'):
            native['remote_run_dir'] = state['recovery']['directory']
        return normalize_collection(self.collect(vm, native, output, secrets), output)

    def finalize_evidence(self, output: Path) -> None:
        import shutil
        (output / 'control.json').unlink(missing_ok=True)
        receipt = output / 'runtime-transfer.json'
        if receipt.exists() and json.loads(receipt.read_text()).get('events') == 'complete':
            shutil.rmtree(output / 'guest', ignore_errors=True)
        for file in output.rglob('*.log'):
            if file.is_file() and file.stat().st_size == 0:
                file.unlink()

    @staticmethod
    def safe_to_grade(state: dict) -> bool:
        return AgentRunner._safe_to_grade(state)

    def run(self, vm_name: str, instruction: str, output_dir: Path, secrets: dict,
            *, collect: bool = True) -> dict:
        """Execute once; defer large archives with collect=False for time-sensitive graders."""
        from mac_cua.infrastructure.network import api_transport
        base_url = secrets.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        diagnostic = Path(output_dir) / 'diagnostics/model-transport.json'
        if diagnostic.exists():
            raise ValueError('Model transport was already opened for this attempt')
        atomic_json(diagnostic, {'schema_version': 1, 'status': 'active',
                                'transport': {'mode': self.config.data.get('network', {}).get('api_transport', 'direct')}})
        tunnel = None
        try:
            with api_transport(self.config, self.provider, vm_name, base_url) as tunnel:
                if tunnel:
                    from base64 import b64encode
                    from urllib.parse import unquote, urlsplit
                    # Keep these in the caller's mapping for deferred archive collection,
                    # including failures after launch. They never enter argv or artifacts.
                    proxy_url = tunnel.url
                    secrets['proxy_url_secret'] = proxy_url
                    parsed = urlsplit(proxy_url)
                    if parsed.username is not None and parsed.password is not None:
                        username, password = unquote(parsed.username), unquote(parsed.password)
                        secrets['proxy_username_secret'] = username
                        secrets['proxy_password_secret'] = password
                        secrets['proxy_basic_secret'] = b64encode(f'{username}:{password}'.encode()).decode()
                result = self._run(vm_name, instruction, output_dir, secrets, collect=collect,
                                   proxy_url=tunnel.url if tunnel else None)
        finally:
            transport = tunnel.record() if tunnel else {'mode': self.config.data.get('network', {}).get('api_transport', 'direct')}
            status = 'complete' if tunnel and transport.get('closed') or transport['mode'] == 'direct' else 'partial'
            atomic_json(diagnostic, {'schema_version': 1, 'status': status, 'transport': transport})
        result['api_transport'] = transport
        from mac_cua.foundation.evidence import reference
        result['diagnostics'] = [reference(Path(output_dir).parent, diagnostic, 'diagnostics')]
        result = redact(result, secrets)
        atomic_json(Path(output_dir) / ("control.json" if self.shared_dir else "agent-result.json"), result)
        return result

    def _run(self, vm_name: str, instruction: str, output_dir: Path, secrets: dict,
             *, collect: bool = True, proxy_url: str | None = None) -> dict:
        output_dir = Path(output_dir)
        output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        api_key = secrets.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing")
        base_url = secrets.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        cfg = self.config.agent
        strategy = select_strategy(cfg)
        export_trace = trace_enabled(cfg)
        guest = self._guest()
        timeout = int(cfg.get("timeout_seconds", 1200))
        from mac_cua.runtime.live_output import LiveOutput
        live_output = LiveOutput.from_env(vm_name)
        prompt = build_prompt(instruction, timeout, strategy=cfg,
                              skill_names=tuple(skill["name"] for skill in self.runtime.skills))
        codex_config = build_codex_config(cfg, base_url, guest.get("cua_binary", "/usr/local/bin/cua-driver"),
                                          self.runtime,
                                          python_binary=guest.get("python_binary", "/usr/local/bin/python3.11"),
                                          node_binary=guest.get("node_binary", "/usr/local/bin/node"))
        if proxy_url:
            # The proxy is only for the CLI's model transport. Shell tools keep
            # their ordinary networking, including arbitrary public websites.
            codex_config += '\n[shell_environment_policy]\nexclude = ["HTTPS_PROXY", "https_proxy"]\n'
        # A compatible resumed batch may use a new connection address or a
        # compatible supervisor implementation. Preserve its original shared
        # files, and seal the actual runtime bytes with this attempt instead.
        runtime_dir = output_dir / "runtime"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        (runtime_dir / "prompt.txt").write_text(prompt)
        resources = [("codex-config.toml", codex_config), ("supervisor.py", GUEST_SUPERVISOR)]
        resources.extend(strategy.resources().items())
        for name, content in resources:
            file = runtime_dir / name
            if file.exists() and file.read_text() != content:
                raise ValueError("Attempt runtime configuration changed")
            if not file.exists():
                file.write_text(content)
        supervisor = runtime_dir / "supervisor.py"
        remote = f"/tmp/mac-cua-agent-{uuid.uuid4().hex}"
        python = guest.get("python_binary", "/usr/local/bin/python3.11")
        if self.on_prepared:
            self.on_prepared({'directory': remote})
        prepared = self.provider.ssh(vm_name, "mkdir -m 700 " + shlex.quote(remote), timeout=30)
        if prepared.returncode:
            raise RuntimeError("Cannot create the guest agent runtime directory")
        self.provider.upload(vm_name, supervisor, remote + "/supervisor.py")
        launch = {"api_key": api_key, "base_url": base_url, "codex_config": codex_config,
                  "codex_binary": guest.get("codex_binary", "/usr/local/bin/codex"),
                  "codex_version": cfg.get("codex_version", "0.153.4"),
                  "workspace": guest["workspace"], "prompt": prompt, "timeout_seconds": timeout,
                  "https_proxy": proxy_url, "rollout_trace": export_trace}
        launch.update(strategy.launch_payload(guest))
        launch["api_proxy_bypass_names"] = sorted(set(self.config.data.get("network", {}).get("api_proxy_bypass_names", [])) | set(self.runtime.proxy_bypass))
        launch["mcp_credentials_file"] = self.runtime.credentials_file
        launch["mcp_servers"] = self.runtime.mcp_servers
        launch["skill_packs"] = self.runtime.skills
        launch["runtime_env"] = self.runtime.env
        if self.runtime.env.get('MAC_CUA_BROWSER_CDP_URL'):
            fields = ('browser_python_binary', 'browser_harness_version', 'browser_harness_source_commit')
            if any(not guest.get(key) for key in fields):
                raise ValueError('Browser runtime missing from personal image; install the fixed backend first')
            launch['browser_config'] = {'python': guest[fields[0]], 'version': guest[fields[1]],
                'source_commit': guest[fields[2]], 'url': self.runtime.env['MAC_CUA_BROWSER_CDP_URL']}
        launch["runtime_secret_env"] = self.runtime.secret_env
        command = shlex.join([python, remote + "/supervisor.py"])
        argv = (self.provider.transport(vm_name, self.guest_settings(), secrets).process_argv(command)
                if hasattr(self.provider, 'transport') else self.provider.ssh_argv(vm_name, command))
        started = time.monotonic()
        host_reason = None
        transport = None
        readers = []
        host_env = {key: value for key, value in getattr(self.provider, 'env', os.environ).items()
                    if not re.search(r"api_key|access_token|auth_token|secret|password", key, re.I)
                    and key not in secrets}
        try:
            # Provider env contains only SSH/controller connection context; model keys
            # travel in this process's stdin, never its argv or host environment.
            transport = subprocess.Popen(argv, env=host_env, stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            def copy(source, target, display=False):
                with target.open("wb") as log:
                    for line in iter(source.readline, b""):
                        line = redact(line, secrets)
                        log.write(line)
                        log.flush()
                        if display and live_output is not None:
                            live_output.feed(line)
            readers = [threading.Thread(target=copy, args=(transport.stdout, output_dir / "events.jsonl", True), daemon=True),
                       threading.Thread(target=copy, args=(transport.stderr, output_dir / "stderr.log"), daemon=True)]
            for reader in readers:
                reader.start()
            transport.stdin.write(json.dumps(launch).encode())
            transport.stdin.close()
            try:
                transport.wait(timeout=timeout + 90)
            except subprocess.TimeoutExpired:
                host_reason = "transport_timeout"
            except KeyboardInterrupt:
                host_reason = "interrupted"
        except (OSError, subprocess.SubprocessError) as error:
            host_reason = "transport_error"
            (output_dir / "transport-error.txt").write_text(redact(str(error), secrets))
        finally:
            if transport is not None and transport.poll() is None:
                try:
                    self.provider.ssh(vm_name, command + " stop", timeout=15)
                except Exception:
                    pass
                try:
                    transport.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    transport.terminate()
                    try:
                        transport.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        transport.kill()
                        transport.wait(timeout=5)
            if transport is not None:
                for reader in readers:
                    reader.join(timeout=5)
        result = {"status": host_reason or "transport_error"}
        try:
            result.update(self._read_state(vm_name, remote, output_dir, secrets))
        except Exception as error:
            result["status_collection_error"] = redact(f"{type(error).__name__}: {error}", secrets)
        if not self._safe_to_grade(result) and result["status"] != "startup_error":
            # A crashed SSH/supervisor may leave descendants alive. Make one
            # cleanup attempt, without ever replaying the model invocation.
            try:
                self.provider.ssh(vm_name, command + " stop", timeout=20)
                result.update(self._read_state(vm_name, remote, output_dir, secrets))
            except Exception as error:
                result["cleanup_error"] = redact(f"{type(error).__name__}: {error}", secrets)
        if host_reason:
            result["host_termination_reason"] = host_reason
        # Even parsing a large JSONL can delay an mtime-sensitive grader. Keep the
        # already streamed files intact and enrich event/usage data after grading.
        result.update({"thread_id": None, "usage": None, "usage_scope": "primary_thread",
                       "usage_events": [], "errors": [], "final_answer": None,
                       "invalid_event_lines": None, "session_usage": [], "subagent_usage": []})
        result["transport_returncode"] = transport.returncode if transport is not None else None
        result["host_duration_seconds"] = time.monotonic() - started
        result["remote_run_dir"] = remote
        result["archive_error"] = None
        result["collection_status"] = "pending"
        result["rollout_trace"] = {"enabled": export_trace, "policy": TRACE_POLICY,
                                   "status": "pending" if export_trace else "disabled"}
        result["recovery"] = {"directory": remote}
        result["agent_id"] = "codex"
        result["gui_strategy"] = strategy.name
        result['browser_enabled'] = bool(self.runtime.env.get('MAC_CUA_BROWSER_CDP_URL'))
        result["safe_to_grade"] = self._safe_to_grade(result)
        result = redact(result, secrets)
        atomic_json(output_dir / ("control.json" if self.shared_dir else "agent-result.json"), result)
        return self.collect(vm_name, result, output_dir, secrets) if collect else result

    @staticmethod
    def _safe_to_grade(result: dict) -> bool:
        if result.get("status") == "startup_error":
            return True  # The supervisor version check failed before launching Codex.
        cleanup = result.get("cleanup")
        return (isinstance(cleanup, dict) and cleanup.get("remaining_pids") == []
                and (not (result.get('browser_enabled') or 'browser' in cleanup)
                     or cleanup.get('browser', {}).get('stopped') is True))

    def _read_state(self, vm_name: str, remote: str, output_dir: Path, secrets: dict) -> dict:
        """Fetch only bounded control JSON, never events, session data, or an archive."""
        source = '''import json,pathlib,sys
root=pathlib.Path(sys.argv[1])
result={'browser_enabled':(root/'browser-config.json').exists()}
for name in ("status", "cleanup"):
    path=root/(name+".json")
    if path.exists():
        if path.stat().st_size > 1024*1024:
            raise ValueError("Control state exceeds 1 MiB")
        value=json.loads(path.read_text())
        if not isinstance(value,dict):
            raise ValueError("Control state must be an object")
        result[name]=value
print(json.dumps(result))
'''
        python = self._guest().get("python_binary", "/usr/local/bin/python3.11")
        response = self.provider.ssh(vm_name, shlex.join([python, "-c", source, remote]), timeout=15)
        if response.returncode:
            raise RuntimeError("Guest control state could not be read")
        states = json.loads(response.stdout)
        if not isinstance(states, dict):
            raise ValueError("Malformed guest control state response")
        states = redact(states, secrets)
        for name in ("status", "cleanup"):
            if name in states:
                if not isinstance(states[name], dict):
                    raise ValueError("Malformed guest control state record")
                atomic_json(output_dir / "guest" / (name + ".json"), states[name])
        result = dict(states.get("status") or {})
        if states.get("browser_enabled"):
            result["browser_enabled"] = True
        if "cleanup" in states:
            result["cleanup"] = states["cleanup"]
        return result

    def collect(self, vm_name: str, result: dict, output_dir: Path, secrets: dict) -> dict:
        from mac_cua.runtime.collection import collect
        value = collect(self, vm_name, result, output_dir, secrets)
        if self.shared_dir is None:
            atomic_json(Path(output_dir) / "agent-result.json", value)
        return value
