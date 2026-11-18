"""Execute the task protocol through a generic guest transport."""
from __future__ import annotations

import json
import copy
from pathlib import Path
import shlex
import uuid
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

from mac_cua.infrastructure.guest import Guest, GuestTransportError
from mac_cua.foundation.runtime import ResolvedRuntime
from mac_cua.foundation.interfaces import GuestTransport, RuntimeAdapter
from mac_cua.foundation.contracts import ISOLATION_PREPARED, ISOLATION_READY, phase_result, validate
from mac_cua.foundation.execution import valid_score
from mac_cua.tasks import runtime as task_runtime
from mac_cua.privacy import redact
from mac_cua.resources import guest_script
from mac_cua.tasks.packages import PHASES, Task
from mac_cua.util import atomic_json


class TaskPhaseError(GuestTransportError):
    """A guest responded, but the task phase did not complete successfully."""

    def __init__(self, phase: str, status: str):
        self.phase_status = status
        super().__init__(f"Task {phase}: {status}")


class TaskExecutor:
    def __init__(self, provider, vm_name: str | None = None, *, secrets: dict | None = None, runtime_adapter: RuntimeAdapter | None = None):
        self.guest: GuestTransport = Guest(provider, vm_name, secrets=secrets) if vm_name is not None else provider
        self.secrets = secrets if secrets is not None else {}
        self.runtime = ResolvedRuntime()
        self.runtime_task_sha256 = None
        self.journal = None
        self.application_state = {}
        self.application_context = []
        self.isolation_receipts = {}
        self.runtime_adapter = runtime_adapter
        self.bindings = {}

    def bind_attempt(self, journal, directory: Path) -> None:
        self.journal = journal
        self.attempt_directory = Path(directory)
        state = self.attempt_directory / "applications/state.json"
        self.application_state = json.loads(state.read_text()) if state.exists() else {}
        isolation = self.attempt_directory / "applications/isolation.json"
        self.isolation_receipts = json.loads(isolation.read_text()) if isolation.exists() else {}

    def _save_isolation(self) -> None:
        atomic_json(self.attempt_directory / "applications/isolation.json",
                    redact(self.isolation_receipts, self.secrets))

    def _account_principals(self, app) -> list[str]:
        principals = []
        for name in app.raw.get("accounts", []):
            binding = self.bindings.get(name)
            if not isinstance(binding, dict) or not binding.get("principal"):
                raise TaskPhaseError("ready", "missing_account_principal")
            principals.append(binding["principal"])
        return sorted(set(principals))

    def _check_isolation(self, app, hook: str, result: dict) -> None:
        declaration = getattr(app, "external_state", {"isolation": "unverified", "retention": "unknown"})
        mode = declaration["isolation"]
        if mode in {"unverified", "local_only"} or hook not in {"ready", "prepare"}:
            return
        receipt = result.get("isolation")
        principals = self._account_principals(app)
        if (not isinstance(receipt, dict) or receipt.get("mode") != mode
                or sorted(receipt.get("principals", [])) != principals):
            raise TaskPhaseError(hook, "isolation_identity_mismatch")
        if redact(receipt, self.secrets) != receipt:
            raise TaskPhaseError(hook, "isolation_contains_credential")
        record = self.isolation_receipts[app.id]
        if hook == "ready":
            if receipt.get("permissions_checked") is not True:
                raise TaskPhaseError(hook, "permissions_not_checked")
            if mode == "dedicated_identity" and receipt.get("fresh_verified") is not True:
                raise TaskPhaseError(hook, "dedicated_identity_not_fresh")
            record.update(status="ready", ready=copy.deepcopy(receipt))
        else:
            if record.get("status") != "ready" or receipt.get("retention") != declaration["retention"]:
                raise TaskPhaseError(hook, "isolation_readiness_missing")
            if mode == "attempt_scope":
                key = receipt.get("resource_key")
                resource = (self.journal.read().get("resources", {}).get(key)
                            if self.journal is not None and isinstance(key, str) else None)
                if (not resource or resource.get("object_id") != receipt.get("scope_id")
                        or resource.get("status") != "retained"):
                    raise TaskPhaseError(hook, "scope_creation_not_acknowledged")
            elif "resource_key" in receipt:
                raise TaskPhaseError(hook, "unexpected_scope_resource")
            record.update(status="prepared", prepare=copy.deepcopy(receipt))
        self._save_isolation()

    @staticmethod
    def _cloud_recovery(app, hook: str) -> bool:
        return (hook == "recover" and app.raw.get("protocol") == "app-package-v3"
                and app.external_state["isolation"] in {"attempt_scope", "dedicated_identity"})

    def _check_recovery_isolation(self, app) -> None:
        """A cloud recovery may inspect only the scope prepared by this attempt."""
        declaration = app.external_state
        record = self.isolation_receipts.get(app.id)
        if (not isinstance(record, dict) or record.get("protocol") != "app-package-v3"
                or record.get("isolation") != declaration["isolation"]
                or record.get("retention") != declaration["retention"]
                or record.get("status") != "prepared"):
            raise TaskPhaseError("recover", "original_isolation_receipt_missing")
        ready, prepared = record.get("ready"), record.get("prepare")
        try:
            validate(ready, ISOLATION_READY, label="Original isolation ready receipt")
            validate(prepared, ISOLATION_PREPARED, label="Original isolation prepare receipt")
        except ValueError as error:
            raise TaskPhaseError("recover", "original_isolation_receipt_invalid") from error
        mode = declaration["isolation"]
        if (ready["mode"] != mode or prepared["mode"] != mode
                or sorted(ready["principals"]) != sorted(prepared["principals"])
                or (self.bindings and sorted(ready["principals"]) != self._account_principals(app))
                or prepared["retention"] != declaration["retention"]
                or (mode == "dedicated_identity" and ready.get("fresh_verified") is not True)
                or redact(record, self.secrets) != record):
            raise TaskPhaseError("recover", "original_isolation_receipt_invalid")
        if mode == "attempt_scope":
            key = prepared.get("resource_key")
            resource = (self.journal.read().get("resources", {}).get(key)
                        if self.journal is not None and isinstance(key, str) else None)
            if (not isinstance(resource, dict) or resource.get("object_id") != prepared["scope_id"]
                    or resource.get("status") != "retained" or resource.get("policy") != "retain"):
                raise TaskPhaseError("recover", "original_scope_mismatch")
        elif "resource_key" in prepared:
            raise TaskPhaseError("recover", "original_isolation_receipt_invalid")

    def lifecycle(self, task: Task, hook: str) -> dict:
        results = {}
        failures = []
        if hook == "recover":
            for app in task.applications:
                if self._cloud_recovery(app, hook):
                    self._check_recovery_isolation(app)
        for app in task.applications:
            if app.id not in self.isolation_receipts:
                state = getattr(app, "external_state", {"isolation": "unverified", "retention": "unknown"})
                self.isolation_receipts[app.id] = {"protocol": app.raw.get("protocol", "app-package-v2"),
                    "isolation": state["isolation"], "retention": state["retention"],
                    "status": "unverified" if state["isolation"] == "unverified" else
                              "local_vm_only" if state["isolation"] == "local_only" else "pending"}
        self._save_isolation()
        apps = reversed(task.applications) if hook == "cleanup" else task.applications
        for app in apps:
            if hook not in app.raw.get("hooks", {}):
                continue
            output = self.attempt_directory / "applications" / app.id / hook
            readonly_recovery = self._cloud_recovery(app, hook)
            original_state = copy.deepcopy(self.application_state.get(app.id, {}))
            original_journal = self.journal.read() if readonly_recovery else None
            try:
                result = self._phase(task, hook, output, copy.deepcopy(original_state), application=app)
            except Exception as error:
                if hook != "cleanup":
                    raise
                failures.append(app.id + ": " + str(error))
                continue
            if result.get("ready") is False or result.get("stable") is False or result["status"] != "completed":
                if hook == "cleanup":
                    failures.append(app.id + ": application_not_ready")
                    continue
                raise TaskPhaseError(hook, "application_not_ready")
            if not isinstance(result.get("state", {}), dict):
                if hook == "cleanup":
                    failures.append(app.id + ": invalid_application_state")
                    continue
                raise TaskPhaseError(hook, "invalid_application_state")
            if readonly_recovery:
                if self.journal.read() != original_journal:
                    raise TaskPhaseError(hook, "recovery_resource_journal_changed")
                if result.get("state", original_state) != original_state:
                    raise TaskPhaseError(hook, "recovery_application_state_changed")
            self._check_isolation(app, hook, result)
            self.application_state[app.id] = copy.deepcopy(result.get("state", self.application_state.get(app.id, {})))
            atomic_json(self.attempt_directory / "applications/state.json", redact(self.application_state, self.secrets))
            if result.get("agent_context"):
                self.application_context.append(result["agent_context"])
            results[app.id] = result
        if failures:
            raise TaskPhaseError(hook, "; ".join(failures))
        return results

    def _events(self, directory: str, *, allow_resource_events: bool = True) -> None:
        source = """import json,sys
from pathlib import Path
p=json.load(sys.stdin); root=Path(p['directory'])/'events'
rows=[]
for f in sorted(root.glob('*.json')):
 if f.is_symlink() or f.stat().st_size>65536: raise ValueError('Invalid event')
 if p.get('reject_all') or not f.with_suffix('.ack').exists(): rows.append(json.loads(f.read_text()))
print(json.dumps({'events':rows}))
"""
        rows = self.guest.rpc(source, {"directory": directory,
                                       "reject_all": not allow_resource_events})["events"]
        if rows and not allow_resource_events:
            raise TaskPhaseError("recover", "resource_events_forbidden")
        for event in rows:
            if redact(event, self.secrets) != event:
                raise GuestTransportError("Resource event contains credential content")
            ack = self.journal.acknowledge(event)
            self.guest.rpc("import json,sys,os\nfrom pathlib import Path\np=json.load(sys.stdin); f=Path(p['path']); t=f.with_suffix('.ack-partial'); t.write_text(json.dumps(p['ack'])); os.replace(t,f); print('{}')",
                {"path": directory + "/events/" + ack["event_id"] + ".ack", "ack": ack})

    def _execute(self, payload: dict, timeout: int, *, allow_resource_events: bool = True) -> dict:
        if self.journal is None:
            return self.guest.rpc(guest_script("task_phase.py"), payload, timeout=timeout + 30)
        # SSH channels are independent. The phase waits for host acknowledgements
        # through files, so no credentials/listening service is added to the guest.
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.guest.rpc, guest_script("task_phase.py"), payload, timeout=timeout + 30)
            while not future.done():
                self._events(payload["directory"], allow_resource_events=allow_resource_events)
                time.sleep(0.2)
            self._events(payload["directory"], allow_resource_events=allow_resource_events)
            return future.result()

    def prepare_runtime(self, task: Task, bindings: dict, output: Path) -> dict:
        self.bindings = copy.deepcopy(bindings)
        self.runtime = task_runtime.prepare(task, self.guest, bindings, output, self.runtime_adapter)
        self.runtime_task_sha256 = task.sha256
        self._refresh_secrets()
        return self.runtime.as_dict()

    def _refresh_secrets(self):
        if self.runtime_adapter is not None:
            self.runtime_adapter.refresh_secrets(self.guest, self.runtime, self.secrets)

    def _phase(self, task: Task, phase: str, output: Path, state: dict, *, application=None) -> dict:
        output.mkdir(parents=True, exist_ok=True)
        remote = "/private/tmp/mac-cua-task-" + uuid.uuid4().hex
        readonly_recovery = application is not None and self._cloud_recovery(application, phase)
        receipt = {"status": "transport_error", "phase": phase, "remote_directory": remote,
                   "task_sha256": task.sha256}
        try:
            self.guest.command("mkdir -p " + shlex.quote(remote))
            files = application.phase_files(phase) if application else task.phase_files(phase)
            for local, relative in files:
                self.guest.upload(local, remote + "/" + relative)
            if self.journal is not None and not readonly_recovery:
                with tempfile.TemporaryDirectory() as temp:
                    helper = Path(temp) / "resource_events.py"
                    helper.write_text(guest_script("resource_events.py"))
                    self.guest.upload(helper, remote + "/resource_events.py")
            if application is None:
                with tempfile.TemporaryDirectory() as temp:
                    for name in ("task_api.py", "task_entry.py"):
                        helper = Path(temp) / name
                        helper.write_text(guest_script(name))
                        self.guest.upload(helper, remote + "/" + name)
            settings = self.guest.settings()
            context = {"protocol": task.raw["protocol"], "task_id": task.id, "phase": phase,
                       "workspace": settings["workspace"], "resources": remote, "state": copy.deepcopy(state),
                       "guest": settings, "runtime": self.runtime.as_dict(), "applications": copy.deepcopy(self.application_state)}
            if self.journal is not None:
                context.update(attempt_id=self.journal.identity["attempt_id"],
                    resource_namespace=self.journal.identity["namespace"],
                    resource_journal=self.journal.read())
                if not readonly_recovery:
                    context["resource_events"] = remote + "/events"
            spec = application.raw["hooks"][phase] if application else task.raw.get(phase, {})
            if application:
                context.update(application_id=application.id, parameters={k: application.parameters[k]
                    for k in spec.get("parameters", []) if k in application.parameters},
                    external_state=application.external_state,
                    isolation_receipt=copy.deepcopy(self.isolation_receipts.get(application.id, {})))
            if application is None:
                context["task_phase"] = {
                    "entry": PHASES[phase] if task.phase_entry(phase) is not None else None,
                    "args": spec.get("args", {}),
                }
            timeout = spec.get("timeout_seconds", 180)
            receipt.update(self._execute({"directory": remote, "entry": "entry.py" if application else "task_entry.py",
                "context": context, "timeout_seconds": timeout}, timeout,
                allow_resource_events=not readonly_recovery))
            if receipt['status'] == 'completed':
                try:
                    receipt['result'] = phase_result(receipt['result'], phase)
                    if receipt['result']['status'] == 'failed':
                        receipt['status'] = 'failed'
                except ValueError as error:
                    receipt.update(status='invalid_result', error=str(error))
        finally:
            try:
                self._refresh_secrets()
            except GuestTransportError as error:
                receipt.pop("result", None)
                receipt["credential_refresh_error"] = type(error).__name__
            for name in (() if receipt.get("credential_refresh_error") else ("stdout.log", "stderr.log")):
                try:
                    self.guest.download(remote + "/" + name, output / name)
                    (output / name).write_bytes(redact((output / name).read_bytes(), self.secrets))
                except Exception as error:
                    receipt.setdefault("log_errors", []).append(type(error).__name__)
            # Setup implementation is not agent input; evaluation arrives only after stop.
            try:
                self.guest.command("rm -rf " + shlex.quote(remote))
            except GuestTransportError as error:
                receipt["cleanup_error"] = str(error)
            atomic_json(output / "phase.json", redact(receipt, self.secrets))
        if receipt["status"] != "completed":
            raise TaskPhaseError(phase, receipt['status'])
        if receipt.get("credential_refresh_error"):
            raise GuestTransportError("Could not load refreshed runtime credentials for evidence redaction")
        if receipt.get("cleanup_error"):
            raise GuestTransportError("Could not remove private task phase files")
        return receipt["result"]

    def setup(self, task: Task, output_dir: Path) -> dict:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        if self.runtime_task_sha256 != task.sha256:
            self.prepare_runtime(task, self.bindings, output_dir.parent / "runtime")
        requirements = task.requirements
        if requirements.get("commands") or requirements.get("python_modules"):
            readiness = self.guest.rpc(
                "import importlib.util,json,shutil,sys\np=json.load(sys.stdin)\n"
                "def module(name):\n try:return importlib.util.find_spec(name) is not None\n except (ImportError,ValueError,AttributeError):return False\n"
                "print(json.dumps({'commands':{x:shutil.which(x) is not None for x in p.get('commands',[])},"
                "'python_modules':{x:module(x) for x in p.get('python_modules',[])}}))", requirements)
            atomic_json(output_dir / "readiness.json", readiness)
            if any(not available for entries in readiness.values() for available in entries.values()):
                raise TaskPhaseError("setup", "requirements_unavailable")
        uploads = []
        for local, destination in task.fixture_uploads():
            target = self.guest.expand(destination)
            self.guest.upload(local, target)
            uploads.append({"guest_path": target, "local_path": str(local)})
        result = self._phase(task, "setup", output_dir, {})
        if not isinstance(result.get("state", {}), dict) or not isinstance(result.get("agent_context", ""), str):
            raise GuestTransportError("Invalid initialization state or agent_context")
        patch = result.get("runtime", {})
        if redact(patch, self.secrets) != patch:
            raise GuestTransportError("Initialization runtime result contains credential content")
        self.runtime = task_runtime.finalize(task, self.guest, self.runtime, patch, output_dir.parent / "runtime", self.runtime_adapter)
        result = {"status": "completed", "runtime": self.runtime.as_dict(), "state": result.get("state", {}),
                  "agent_context": "\n\n".join([*self.application_context, result.get("agent_context", "")]).strip(), "uploads": uploads,
                  "details": result.get("details", {})}
        atomic_json(output_dir / "setup.json", redact(result, self.secrets))
        return result

    def score(self, task: Task, output_dir: Path) -> dict:
        output_dir = Path(output_dir)
        try:
            setup = json.loads((output_dir.parent / "setup/setup.json").read_text())
            self.runtime = ResolvedRuntime.from_dict(setup.get("runtime", {}))
            value = self._phase(task, "evaluation", output_dir, setup.get("state", {}))
            score = value.get("score")
            if value["status"] == "not_evaluated":
                result = value
            elif value["status"] != "graded":
                result = {**value, "status": "evaluator_error", "score": None}
            elif not valid_score(value):
                raise ValueError("Evaluation requires a finite score in [0, 1]")
            else:
                result = {**value, "status": "graded", "score": score}
        except (GuestTransportError, OSError, ValueError) as error:
            result = {"status": "evaluator_error", "score": None, "error": str(error),
                      "error_kind": "phase_execution" if isinstance(error, TaskPhaseError) else
                                    "transport" if isinstance(error, GuestTransportError) else "invalid_result"}
            if isinstance(error, TaskPhaseError):
                result["phase_status"] = error.phase_status
        result.update(task_id=task.id, task_sha256=task.sha256)
        atomic_json(output_dir / "score.json", redact(result, self.secrets))
        return result
