"""Resolve task-owned runtime declarations and materialize their frozen resources."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shlex
import tempfile
import uuid

from mac_cua.foundation.runtime import ResolvedRuntime, apply_dynamic, relative_path, validate_bindings, validate_runtime, merge_runtime
from mac_cua.infrastructure.guest import GuestTransportError
from mac_cua.resources import guest_script
from mac_cua.util import atomic_json, sha256_file


def resource_path(root: Path, source: str) -> Path:
    relative_path(source)
    path = root / source
    if (not path.resolve().is_relative_to(root.resolve()) or not path.exists()
            or any(p.is_symlink() for p in (path, *path.parents))):
        raise ValueError("Runtime resource missing, outside package, or linked")
    entries = [path] if path.is_file() else sorted(path.rglob("*"))
    if any(p.is_symlink() or not (p.is_file() or p.is_dir()) for p in entries):
        raise ValueError("Runtime resources must be regular files/directories")
    if not any(p.is_file() for p in entries):
        raise ValueError("Runtime resource directory is empty")
    return path


def resource_hash(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(path).as_posix().encode() + b"\0")
            digest.update(bytes.fromhex(sha256_file(item)))
    return digest.hexdigest()


def declaration(root: Path, raw: object) -> tuple[dict, set[Path]]:
    if not isinstance(raw, dict):
        raise ValueError("runtime must be an object")
    inline = copy.deepcopy(raw)
    profiles = inline.pop("profiles", [])
    if not isinstance(profiles, list) or not all(isinstance(x, str) for x in profiles) or len(profiles) != len(set(profiles)):
        raise ValueError("Runtime profiles must be unique package file paths")
    sources = set()
    parts = []
    for name in profiles:
        path = resource_path(root, name)
        if not path.is_file():
            raise ValueError("Runtime profile must be a JSON file")
        sources.add(path)
        parts.append(validate_runtime(json.loads(path.read_text())))
    parts.append(validate_runtime(inline))
    merged = merge_runtime(parts)
    for is_skill, row in [(True, r) for r in merged["skills"].values()] + [(False, r) for r in merged["files"]]:
        if "source" not in row:
            continue
        path = resource_path(root, row["source"])
        if is_skill and not path.is_dir():
            raise ValueError("Skill pack source must be a directory")
        digest = resource_hash(path)
        if row.get("sha256", digest) != digest:
            raise ValueError("Package runtime resource hash mismatch")
        row["sha256"] = digest
        sources.update([path] if path.is_file() else (p for p in path.rglob("*") if p.is_file()))
    return merged, sources


def binding_requirements(spec: dict) -> dict[str, set[str]]:
    required = {}
    def add(name, kinds):
        required[name] = required.get(name, set(kinds)) & set(kinds)
        if not required[name]:
            raise ValueError("Runtime binding has conflicting resource kinds")
    for server in spec["mcp_servers"].values():
        if "credential" in server:
            add(server["credential"], {"oauth"})
    for row in spec["skills"].values():
        if "binding" in row:
            add(row["binding"], {"directory"})
    for row in spec["files"]:
        if "binding" in row:
            add(row["binding"], {"file", "directory"})
    for value in spec["env"].values():
        if isinstance(value, dict):
            add(value["binding"], {"secret"})
    return required


def preflight_runtime(spec: dict, bindings: dict) -> list[dict]:
    validate_bindings(bindings)
    rows = []
    for name, kinds in binding_requirements(spec).items():
        binding = bindings.get(name)
        configured = bool(binding and binding["kind"] in kinds)
        rows.append({"kind": "runtime_bindings", "name": name, "configured": configured,
                     "available": None if configured else False,
                     "status": "unverified" if configured else "missing_or_wrong_kind"})
    return rows


def _rpc(guest, payload, output: Path, name: str, adapter) -> dict:
    try:
        if adapter is None:
            raise GuestTransportError("Runtime extensions require an injected backend runtime adapter")
        value = adapter.materialize(guest, payload)
    except GuestTransportError as error:
        atomic_json(output / name, {"status": "transport_error", "error_type": type(error).__name__})
        raise
    atomic_json(output / name, value)
    if value.get("status") != "completed":
        raise GuestTransportError("Task runtime preparation failed: " + value.get("error", "unknown"))
    return value


def _expand(value, directory: str, python: str):
    if isinstance(value, str):
        return value.replace("${runtime}", directory).replace("${python}", python)
    if isinstance(value, list):
        return [_expand(x, directory, python) for x in value]
    if isinstance(value, dict):
        return {key: _expand(item, directory, python) for key, item in value.items()}
    return value


def prepare(task, guest, bindings: dict, output: Path, adapter=None) -> ResolvedRuntime:
    spec = task.runtime
    missing = [r for r in preflight_runtime(spec, bindings) if r["available"] is False]
    if missing:
        raise GuestTransportError("Missing task runtime bindings: " + ", ".join(r["name"] for r in missing))
    output.mkdir(parents=True, exist_ok=True)
    if not any(spec[k] for k in ('mcp_servers', 'skills', 'env', 'files', 'proxy_bypass')):
        runtime = ResolvedRuntime()
        atomic_json(output / "prepared.json", runtime.as_dict())
        return runtime
    root = "/private/tmp/mac-cua-runtime-" + uuid.uuid4().hex
    guest.command("mkdir -m 700 " + shlex.quote(root))
    resources = []
    skills = []
    for kind, rows in (("skills", spec["skills"].items()), ("files", ((r["destination"], r) for r in spec["files"]))):
        for name, row in rows:
            destination = root + "/" + kind + "/" + name
            if "source" in row:
                local = task.resource_path(row["source"])
                items = [(local, "")] if local.is_file() else [(p, p.relative_to(local).as_posix()) for p in sorted(local.rglob("*")) if p.is_file()]
                for file, suffix in items:
                    target = destination + ("/" + suffix if suffix else "")
                    guest.command("mkdir -p " + shlex.quote(str(Path(target).parent)))
                    guest.upload(file, target)
                source = destination
            else:
                source = bindings[row["binding"]]["path"]
            resources.append({"kind": kind, "name": name, "source": source, "destination": destination,
                              "sha256": row["sha256"], "executable": row.get("executable", False)})
            if kind == "skills":
                skills.append({"name": name, "path": destination, "sha256": row["sha256"]})
    selected_bindings = {name: bindings[name] for name in binding_requirements(spec)}
    spec = _expand(spec, root, guest.settings().get("python_binary", "/usr/local/bin/python3.11"))
    receipt = _rpc(guest, {"action": "prepare", "directory": root, "resources": resources,
                          "spec": spec, "bindings": selected_bindings}, output, "preparation.json", adapter)
    servers = {name: {k: v for k, v in server.items() if k != "credential"} for name, server in spec["mcp_servers"].items()}
    runtime = ResolvedRuntime(directory=root, mcp_servers=servers, skills=skills, credentials_file=receipt.get("credentials_file"),
                              env={name: value for name, value in spec["env"].items() if isinstance(value, str)},
                              proxy_bypass=spec["proxy_bypass"], secret_env=receipt.get("secret_env", {}), resources=receipt.get("resources", {}))
    atomic_json(output / "prepared.json", runtime.as_dict())
    return runtime


def finalize(task, guest, runtime: ResolvedRuntime, patch: object, output: Path, adapter=None) -> ResolvedRuntime:
    spec = apply_dynamic(task.runtime, patch)
    if runtime.directory is None:
        resolved = ResolvedRuntime()
        atomic_json(output / "effective.json", resolved.as_dict())
        return resolved
    spec = _expand(spec, runtime.directory, guest.settings().get("python_binary", "/usr/local/bin/python3.11"))
    servers = {name: {key: value for key, value in server.items() if key != "credential"}
               for name, server in spec["mcp_servers"].items()}
    env = {name: value for name, value in spec["env"].items() if isinstance(value, str)}
    receipt = _rpc(guest, {"action": "finalize", "directory": runtime.directory,
                          "mcp_servers": servers, "env": env, "secret_env": runtime.secret_env}, output, "verification.json", adapter)
    for row in receipt.get("generated_files", []):
        relative_path(row["path"])
        target = output / "generated" / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as temporary:
            downloaded = Path(temporary) / "resource"
            guest.download(runtime.directory + "/generated/" + row["path"], downloaded)
            if sha256_file(downloaded) != row["sha256"]:
                raise GuestTransportError("Generated runtime file changed during collection")
            target.write_bytes(downloaded.read_bytes())
    resolved = ResolvedRuntime(directory=runtime.directory, mcp_servers=servers, skills=runtime.skills,
                               env=env, secret_env=runtime.secret_env, proxy_bypass=spec["proxy_bypass"],
                               credentials_file=runtime.credentials_file, resources=runtime.resources)
    atomic_json(output / "effective.json", resolved.as_dict())
    return resolved
