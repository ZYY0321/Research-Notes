"""Contract-driven near-miss audit for semantic verifiers.

The audit synthesizes one positive fixture from each reviewed contract, then
removes one semantic requirement at a time.  A contract that still passes a
mutant has an observable false-accept weakness.  This is intentionally an
offline, deterministic companion to the browser smoke test.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

from bench_env.env.base import Observation
from bench_env.task.hybrid_tools_0815_explore.verifier_v1 import evaluate_contract, load_contracts
from bench_env.task.judge import JudgeInput


_SELECTOR = re.compile(r"^(?P<field>[^[]+)\[(?P<key>[^=]+)=(?P<value>[^]]+)\]$")
_MISSING = object()


def _container(state: dict[str, Any], source: str) -> Any:
    if source == "apps":
        return state.setdefault("apps", {})
    if source == "os":
        return state.setdefault("os", {})
    raise ValueError(f"unsupported mutable source: {source}")


def _set_path(root: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".") if path else []
    current: Any = root
    for index, part in enumerate(parts[:-1]):
        next_is_index = parts[index + 1].isdigit()
        selector = _SELECTOR.match(part)
        if selector:
            if not isinstance(current, dict):
                raise ValueError(f"selector {part!r} requires an object in {path!r}")
            rows = current.setdefault(selector.group("field"), [])
            row = next((r for r in rows if str(r.get(selector.group("key"))) == selector.group("value")), None)
            if row is None:
                row = {selector.group("key"): selector.group("value")}
                rows.append(row)
            current = row
        elif part.isdigit():
            if not isinstance(current, list):
                raise ValueError(f"index {part!r} requires a list in {path!r}")
            item_index = int(part)
            while len(current) <= item_index:
                current.append([] if next_is_index else {})
            # A selector assertion may already have created a different entity
            # at this position. Preserve it and insert the ordered entity that
            # this numeric-path assertion describes (for example tags.0.id).
            leaf = parts[index + 1]
            if (
                index + 1 == len(parts) - 1
                and isinstance(current[item_index], dict)
                and leaf in current[item_index]
                and current[item_index][leaf] != value
            ):
                current.insert(item_index, {})
            if not isinstance(current[item_index], (dict, list)):
                current[item_index] = [] if next_is_index else {}
            current = current[item_index]
        else:
            if not isinstance(current, dict):
                raise ValueError(f"field {part!r} requires an object in {path!r}")
            wanted_type = list if next_is_index else dict
            if not isinstance(current.get(part), wanted_type):
                current[part] = wanted_type()
            current = current[part]
    if parts:
        last = parts[-1]
        last_selector = _SELECTOR.match(last)
        if last_selector:
            if not isinstance(current, dict):
                raise ValueError(f"selector {last!r} requires an object in {path!r}")
            rows = current.setdefault(last_selector.group("field"), [])
            row = {last_selector.group("key"): last_selector.group("value")}
            if isinstance(value, dict):
                row.update(copy.deepcopy(value))
            rows[:] = [
                candidate for candidate in rows
                if not isinstance(candidate, dict)
                or str(candidate.get(last_selector.group("key"))) != last_selector.group("value")
            ]
            rows.append(row)
        elif last.isdigit():
            if not isinstance(current, list):
                raise ValueError(f"index {last!r} requires a list in {path!r}")
            item_index = int(last)
            while len(current) <= item_index:
                current.append(None)
            current[item_index] = copy.deepcopy(value)
        elif isinstance(current, dict):
            current[last] = copy.deepcopy(value)
        else:
            raise ValueError(f"field {last!r} requires an object in {path!r}")


def _delete_path(root: dict[str, Any], path: str) -> None:
    parts = path.split(".") if path else []
    current: Any = root
    for part in parts[:-1]:
        selector = _SELECTOR.match(part)
        if selector:
            rows = current.get(selector.group("field"), []) if isinstance(current, dict) else []
            current = next((r for r in rows if str(r.get(selector.group("key"))) == selector.group("value")), {})
        elif part.isdigit():
            index = int(part)
            current = current[index] if isinstance(current, list) and 0 <= index < len(current) else {}
        else:
            current = current.get(part, {}) if isinstance(current, dict) else {}
    if parts:
        last = parts[-1]
        last_selector = _SELECTOR.match(last)
        if last_selector and isinstance(current, dict):
            rows = current.get(last_selector.group("field"), [])
            if isinstance(rows, list):
                current[last_selector.group("field")] = [
                    row for row in rows
                    if not isinstance(row, dict)
                    or str(row.get(last_selector.group("key"))) != last_selector.group("value")
                ]
        elif last.isdigit() and isinstance(current, list):
            index = int(last)
            if 0 <= index < len(current):
                current[index] = None
        elif isinstance(current, dict):
            current.pop(last, None)


def _different(value: Any) -> Any:
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value + 1
    if isinstance(value, str):
        return f"{value}__near_miss"
    if isinstance(value, list):
        return [] if value else ["__near_miss"]
    if isinstance(value, dict):
        return {}
    return "__near_miss"


def _positive_and_bad(assertion: dict[str, Any]) -> tuple[Any, Any, Any, str] | None:
    """Return initial, positive, mutant and mutation category."""
    op, expected = assertion.get("op", "eq"), assertion.get("expected")
    if op == "eq":
        return _different(expected), expected, _different(expected), "field"
    if op == "contains":
        positive = [expected]
        return [], positive, [], "collection" if not isinstance(expected, str) else "field"
    if op == "not_contains":
        return [], [], [expected], "collection"
    if op == "absent":
        return None, _MISSING, "__unexpected_present", "field"
    if op == "changed":
        return "__initial", "__changed", "__initial", "field"
    if op == "nonempty":
        return [], ["__present"], [], "collection"
    if op == "new_contains":
        return [], [expected], [], "collection"
    if op == "new_contains_exactly_once":
        return [], [expected], [expected, expected], "collection"
    # Relationship and regex operators need structurally coordinated fixtures;
    # report them as uncovered rather than pretending a weak fixture is proof.
    return None


def _input(init_state: dict[str, Any], final_state: dict[str, Any], route: dict[str, Any]) -> JudgeInput:
    return JudgeInput(
        init_obs=Observation(state=init_state, route=route),
        last_obs=Observation(state=final_state, route=route),
        answer=None,
    )


def audit_contract(task_id: str, contract: dict[str, Any]) -> dict[str, Any]:
    assertions = contract.get("assertions") or []
    init_state: dict[str, Any] = {"apps": {}, "os": {}}
    final_state: dict[str, Any] = {"apps": {}, "os": {}}
    route: dict[str, Any] = {}
    generated: list[dict[str, Any]] = []
    positive_values: dict[tuple[str, str], Any] = {}

    for index, assertion in enumerate(assertions):
        source = assertion.get("source", "apps")
        fixture = _positive_and_bad(assertion)
        if source not in {"apps", "os"} or fixture is None:
            continue
        initial, positive, mutant_value, category = fixture
        path = str(assertion.get("path") or "")
        if initial is not _MISSING:
            _set_path(_container(init_state, source), path, initial)
        key = (source, path)
        if assertion.get("op") in {"contains", "new_contains", "new_contains_exactly_once"} and key in positive_values:
            existing = positive_values[key]
            positive = list(existing if isinstance(existing, list) else [existing]) + list(
                positive if isinstance(positive, list) else [positive]
            )
        elif assertion.get("op") == "not_contains" and key in positive_values:
            positive = positive_values[key]
        positive_values[key] = positive
        if positive is _MISSING:
            _delete_path(_container(final_state, source), path)
        else:
            _set_path(_container(final_state, source), path, positive)
        generated.append({
            "assertion_index": index,
            "field": assertion.get("field") or f"{source}.{path}",
            "source_path": f"{source}.{path}" if path else source,
            "op": assertion.get("op", "eq"),
            "category": category,
            "mutation_types": [category] + (["partial_completion"] if len(assertions) > 1 else []),
            "mutant_value": mutant_value,
        })

    positive_checks = evaluate_contract(task_id, _input(copy.deepcopy(init_state), copy.deepcopy(final_state), route))
    positive_pass = bool(positive_checks) and all(check["passed"] for check in positive_checks)
    mutants = []
    if positive_pass:
        for mutation in generated:
            assertion = assertions[mutation["assertion_index"]]
            mutated = copy.deepcopy(final_state)
            _set_path(_container(mutated, assertion.get("source", "apps")), str(assertion.get("path") or ""), mutation["mutant_value"])
            checks = evaluate_contract(task_id, _input(copy.deepcopy(init_state), mutated, route))
            erroneously_passed = bool(checks) and all(check["passed"] for check in checks)
            mutants.append({**mutation, "erroneously_passed": erroneously_passed})

    assertion_paths = {item["source_path"] for item in generated}
    expected_changes = list(contract.get("expected_changes") or [])
    covered_changes = [
        change for change in expected_changes
        if any(change == path or change.startswith(path + ".") or path.startswith(change + ".") for path in assertion_paths)
    ]
    return {
        "task_id": task_id,
        "constraints": [
            {"field": a.get("field"), "source": a.get("source", "apps"), "path": a.get("path", ""), "op": a.get("op", "eq"), "expected": a.get("expected")}
            for a in assertions
        ],
        "positive_fixture_passed": positive_pass,
        "generated_mutations": mutants,
        "wrongly_passing_mutations": [m for m in mutants if m["erroneously_passed"]],
        "semantic_constraint_coverage": {
            "covered": len(generated), "total": len(assertions),
            "ratio": len(generated) / len(assertions) if assertions else 0.0,
        },
        "expected_change_coverage": {
            "covered": len(covered_changes), "total": len(expected_changes),
            "ratio": len(covered_changes) / len(expected_changes) if expected_changes else 1.0,
            "uncovered": [change for change in expected_changes if change not in covered_changes],
        },
    }


def audit_contracts(task_ids: list[str] | None = None) -> dict[str, Any]:
    contracts = load_contracts()
    selected = task_ids or sorted(contracts)
    tasks = [audit_contract(task_id, contracts[task_id]) for task_id in selected]
    generated = sum(len(task["generated_mutations"]) for task in tasks)
    wrong = sum(len(task["wrongly_passing_mutations"]) for task in tasks)
    covered = sum(task["semantic_constraint_coverage"]["covered"] for task in tasks)
    total = sum(task["semantic_constraint_coverage"]["total"] for task in tasks)
    return {
        "schema_version": "1.0",
        "summary": {
            "tasks": len(tasks), "positive_fixtures_passed": sum(t["positive_fixture_passed"] for t in tasks),
            "mutations_generated": generated, "wrongly_passing_mutations": wrong,
            "semantic_constraint_coverage": covered / total if total else 0.0,
        },
        "tasks": tasks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id", nargs="*")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_contracts(args.task_id or None)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 1 if report["summary"]["wrongly_passing_mutations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
