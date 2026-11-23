"""Count reviewed output, with duplicate-frame exclusion and explicit deficit targets."""

from truncator.common.capture_files import capture_image
from collections import Counter
from pathlib import Path
from truncator.common.storage import read, digest, contained
from truncator.mutation.operators import REGISTRY
from truncator.review.datasets.dataset_consensus import reconcile
from truncator.review.datasets.dataset_observations import reviewed_observation
from truncator.review.datasets.dataset_coverage import summarize_coverage
from truncator.review.datasets.dataset_revisions import capture_revision, select_revisions


def audit_exports(exports, targets=None, *, revisions="latest"):
    dimensions = {
        key: Counter() for key in ("component", "mechanism", "axis", "label")
    }
    rows, incomplete, excluded_scope = [], [], []
    revision_records = {}
    for export in exports:
        root = Path(export).resolve()
        if read(root / "export-status.json").get("complete") is not True:
            raise ValueError("Audit requires a complete export")
        manifest = read(root / "manifest.json")
        for sample in manifest["samples"]:
            folder = contained(root, sample["path"] + "/mutated" if "application" in sample else sample["id"])
            capture = read(folder / "capture.json")
            revision = capture_revision(folder, capture)
            if revision:
                if "application" in sample:
                    review = read(contained(root, "applications/" + sample["application"] + "/review.json"))
                    if review["plan_id"] != revision["plan_id"] or review["hap_sha256"] != revision["hap_sha256"]:
                        raise ValueError("Rebuild revision differs from its bound package review")
                existing = revision_records.setdefault(revision["key"], revision)
                if existing != revision:
                    raise ValueError("Conflicting rebuild ancestry for the same package")
            # Removing every mutation leaves an application version, not a defect target.
            if "application" in sample and not sample.get("mutations"):
                reviewed_observation(root, folder, sample, None)
                continue
            session = capture.get("session", {})
            bundle = session.get("process", {}).get("bundle") if session.get("status") == "verified" else None
            if not isinstance(bundle, str) or not bundle.strip():
                bundle = None
            members = sample.get("mutations") or [None]
            for member in members:
                content, recovery = reviewed_observation(root, folder, sample, member)
                label = (
                    "negative"
                    if content == "complete"
                    or (content == "clipped" and recovery == "recovered")
                    else (
                        "positive"
                        if content == "clipped" and recovery == "not-recovered"
                        else "unresolved"
                    )
                )
                mechanism = member["mechanism"] if member else "normal"
                if (
                    REGISTRY.get(mechanism, {}).get("task_role")
                    == "out_of_scope"
                ):
                    excluded_scope.append(
                        {
                            "sample": sample["id"],
                            "mutation": member["id"],
                            "mechanism": mechanism,
                        }
                    )
                    continue
                edge = member.get("edge", "unknown") if member else "unknown"
                axis = (
                    "horizontal"
                    if edge in {"left", "right"}
                    else "vertical" if edge in {"top", "bottom"} else "unknown"
                )
                row = {
                    "export": str(root),
                    "sample": sample["id"],
                    "revision": revision["key"] if revision else None,
                    "capture_sha256": digest((folder / "capture.json").read_bytes()),
                    "application_bundle": bundle,
                    "target_key": member["id"] if member else "baseline",
                    "evidence_sha256": {name: digest(path.read_bytes()) for name, path in
                                        (("screenshot", capture_image(folder)),
                                         ("tree-before.json", folder / "tree-before.json"),
                                         ("tree-after.json", folder / "tree-after.json"))},
                    "content_status": content, "recovery_status": recovery,
                    "mutation": member["id"] if member else None,
                    "component": (
                        member.get("component", "unknown")
                        if member
                        else sample.get("component", "unknown")
                    ),
                    "mechanism": mechanism,
                    "axis": axis,
                    "label": label,
                }
                rows.append(row)
    units, duplicates, conflicts = reconcile(rows)
    units, version_report = select_revisions(units, revision_records, revisions)
    for row in units:
        if row["consensus"] == "conflicting":
            incomplete.append({"sample": row["sample"], "reason": "conflicting_exported_reviews"})
            continue
        for name in dimensions:
            dimensions[name][row[name]] += 1
        if row["label"] == "unresolved":
            incomplete.append({"sample": row["sample"], "reason": "content_or_recovery_not_confirmed"})
    deficits = {}
    for dimension, quotas in (targets or {}).items():
        if dimension not in dimensions or not isinstance(quotas, dict):
            raise ValueError("Unknown balance dimension")
        for category, quota in quotas.items():
            if isinstance(quota, bool) or not isinstance(quota, int) or quota < 0:
                raise ValueError("Balance quotas must be nonnegative integers")
            missing = max(0, quota - dimensions[dimension][category])
            if missing:
                deficits.setdefault(dimension, {})[category] = missing
    return {
        "unit": "reviewed target-state; dimensions are separate marginals, not additive quotas",
        "counts": {k: dict(v) for k, v in dimensions.items()},
        "coverage": summarize_coverage(units),
        "revisions": version_report,
        "units": units,
        "duplicates_excluded": duplicates,
        "conflicts": conflicts,
        "count_policy": "Count each consistent target-state once; contradictory observations require review and do not fill quotas.",
        "excluded_scope": sorted(excluded_scope, key=lambda row: (row["sample"], row["mutation"])),
        "unresolved_labels": incomplete,
        "targets": targets or {},
        "deficits": deficits,
    }


def rank_replenishment(candidates, audit):
    """Rank remaining applicable plans; composition must still enforce all spatial/source constraints."""
    deficits = audit["deficits"]
    ranked, excluded = [], []
    used = {u["mutation"] for u in audit["units"] if u["mutation"]}
    for plan in candidates:
        role = (
            REGISTRY.get(plan["operator"], {}).get("task_role")
        )
        if plan["id"] in used or role not in {"truncation_candidate", "normal_control"}:
            excluded.append(
                {
                    "plan": plan["id"],
                    "reason": "already_observed_or_outside_truncation_scope",
                }
            )
            continue
        edge = plan.get("geometry", {}).get("edge")
        values = {
            "component": plan["site"]["component"],
            "mechanism": plan["operator"],
            "axis": (
                "horizontal"
                if edge in {"left", "right"}
                else "vertical" if edge in {"top", "bottom"} else "unknown"
            ),
        }
        score = sum(deficits.get(k, {}).get(v, 0) for k, v in values.items())
        if score:
            ranked.append(
                {"plan": plan["id"], "score": score, "expected_dimensions": values}
            )
    return {
        "candidates": sorted(ranked, key=lambda r: (-r["score"], r["plan"])),
        "excluded": excluded,
        "status": "proposals_require_composition_build_capture_and_review",
        "note": "Positive/negative outcomes are not predicted from operator names.",
    }
