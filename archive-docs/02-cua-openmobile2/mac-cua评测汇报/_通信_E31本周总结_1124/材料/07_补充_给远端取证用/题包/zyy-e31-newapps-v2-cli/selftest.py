#!/usr/bin/env python3
"""Check the v2 package. Does not launch apps or call osascript."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import io
import json
import sys
import types
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import build_v2

ROOT = Path(__file__).resolve().parent
SRC = build_v2.SRC
FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("OK  ", name)
        return
    FAILURES.append(name)
    print("FAIL", name, detail)


def forbid_osascript(*_args, **_kwargs):
    raise AssertionError("selftest must not call osascript")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hashes(root: Path) -> dict:
    found = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if path.name == ".DS_Store" or "__pycache__" in rel.parts:
            continue
        if rel.parts[:1] in {("build_v2.py",), ("selftest.py",)}:
            continue
        if path.name in {"build_v2.py", "selftest.py"}:
            continue
        found[str(rel)] = file_hash(path)
    return found


def install_task_api():
    module = types.ModuleType("task_api")

    class BaseSetup:
        pass

    module.BaseSetup = BaseSetup
    sys.modules["task_api"] = module


def load_setup(path: Path):
    install_task_api()
    name = "e31v2_setup_" + path.parent.name.replace("-", "_")
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    module.subprocess.run = forbid_osascript
    return module


def script_constant(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CLEAR_MAIL_SCRIPT":
                    return ast.literal_eval(node.value)
    raise AssertionError("CLEAR_MAIL_SCRIPT missing in %s" % path)


def main():
    before = tree_hashes(SRC)
    build_v2.build()
    after = tree_hashes(SRC)
    check("v1_unchanged", before == after, sorted(set(before) ^ set(after))[:8])

    suite = json.loads((ROOT / "suite.json").read_text(encoding="utf-8"))
    src_suite = json.loads((SRC / "suite.json").read_text(encoding="utf-8"))
    check("suite32", len(suite["tasks"]) == 32, len(suite["tasks"]))
    check("suite_keys", set(suite) == {"schema_version", "tasks", "metadata"})
    check("suite_name", suite["metadata"].get("package") == build_v2.PACKAGE)
    check("suite_lists", suite["metadata"]["gradeable_tasks"] == src_suite["metadata"]["gradeable_tasks"])
    check("manual_lists", suite["metadata"]["manual_tasks"] == src_suite["metadata"]["manual_tasks"])
    check("task_order", suite["tasks"] == src_suite["tasks"])
    check("not_v1_note", "AppleScript 和其它脚本" not in suite["metadata"]["note"])

    shared_same = []
    for name in ("e31_grade.py", "seed_mailcom.py"):
        if file_hash(ROOT / "shared" / name) != file_hash(SRC / "shared" / name):
            shared_same.append(name)
    check("shared_unchanged", not shared_same, shared_same)

    mail_scripts = []
    for rel in suite["tasks"]:
        task_path = ROOT / rel
        src_path = SRC / rel
        task = json.loads(task_path.read_text(encoding="utf-8"))
        src_task = json.loads(src_path.read_text(encoding="utf-8"))
        instruction = task["instruction"]
        check(task["id"] + "_prefix", instruction.startswith(build_v2.NEW_PREFIX))
        check(
            task["id"] + "_rest",
            instruction[len(build_v2.NEW_PREFIX):] == src_task["instruction"][len(build_v2.OLD_PREFIX):],
        )
        check(task["id"] + "_suite", task["metadata"].get("suite") == build_v2.PACKAGE)
        check(task["id"] + "_batch", task["metadata"].get("batch") == build_v2.BATCH)
        check(task["id"] + "_eval_same", task["evaluation"] == src_task["evaluation"])
        check(task["id"] + "_setup_files", task["setup"] == src_task["setup"])
        for key, value in src_task["metadata"].items():
            if key in {"batch", "round"}:
                continue
            check(task["id"] + "_meta_" + key, task["metadata"].get(key) == value)
        ast.parse((task_path.parent / "initial_setup.py").read_text(encoding="utf-8"))
        ast.parse((task_path.parent / "evaluation.py").read_text(encoding="utf-8"))
        eval_same = file_hash(task_path.parent / "evaluation.py") == file_hash(src_path.parent / "evaluation.py")
        check(task["id"] + "_evaluation_file", eval_same)
        setup_path = task_path.parent / "initial_setup.py"
        src_setup = src_path.parent / "initial_setup.py"
        setup_text = setup_path.read_text(encoding="utf-8")
        if task["id"] in build_v2.MAIL_GRADEABLE:
            check(task["id"] + "_has_clear", "def clear_e31_mail():" in setup_text and "clear_e31_mail()" in setup_text)
            check(task["id"] + "_logs", "e31-mail-clear attempt=" in setup_text and "mail_cleared" in setup_text)
            mail_scripts.append(script_constant(setup_path))
        else:
            check(task["id"] + "_no_clear", "def clear_e31_mail" not in setup_text)
            check(task["id"] + "_setup_same", file_hash(setup_path) == file_hash(src_setup))

    check("mail_six", len(mail_scripts) == 6, len(mail_scripts))
    check("mail_script_same", len(set(mail_scripts)) == 1)
    script = mail_scripts[0] if mail_scripts else ""
    tell = script.find('tell application "Mail"')
    subject = script.find('subject contains "E31"')
    delete_at = script.find("delete (")
    end = script.rfind("end tell")
    check("script_inside_tell", 0 <= tell < subject < delete_at < end)
    check("script_one_tell", script.count('tell application "Mail"') == 1 and script.count("end tell") == 1)
    check("script_no_quit", "quit" not in script.lower() and "kill" not in script.lower())
    check("script_no_recipients", "to recipients" not in script)
    check("script_matches_builder", script == build_v2.CLEAR_MAIL_SCRIPT)

    setup = load_setup(ROOT / "tasks" / "mail-draft-save" / "initial_setup.py")
    setup.CLEAR_SYNC_SECONDS = 0
    setup.run_osascript = forbid_osascript
    raised = False
    try:
        setup.clear_e31_mail()
    except AssertionError as exc:
        raised = "osascript" in str(exc)
    check("mock_raises", raised)

    fresh = load_setup(ROOT / "tasks" / "mail-draft-recipient" / "initial_setup.py")
    fresh.CLEAR_SYNC_SECONDS = 0
    seen = []

    def fake(script_text, timeout=60):
        seen.append((script_text, timeout))
        return "4\n", None

    fresh.run_osascript = fake
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        total = fresh.clear_e31_mail()
    log = out.getvalue()
    check("mock_total", total == 4 * fresh.CLEAR_PASSES, total)
    check("mock_log", "e31-mail-clear attempt=1 deleted=4" in log and "e31-mail-clear total=%s" % total in log, log)
    check("mock_script", seen and seen[0][0] == fresh.CLEAR_MAIL_SCRIPT and "osascript" not in err.getvalue())

    broken = load_setup(ROOT / "tasks" / "mail-flag" / "initial_setup.py")
    broken.CLEAR_SYNC_SECONDS = 0

    def fail_script(_script, timeout=60):
        return None, "syntax error sample"

    broken.run_osascript = fail_script
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        total = broken.clear_e31_mail()
    check("error_total", total == 0, total)
    check("error_log", "deleted=error" in out.getvalue() and "syntax error sample" in err.getvalue())

    print("---")
    if FAILURES:
        print(len(FAILURES), "failures")
        for name in FAILURES:
            print(" -", name)
        return 1
    print("all ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
