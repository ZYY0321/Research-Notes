"""Sample-specific realism reviews, separate from visual acceptance and operator provenance."""

from truncator.common.capture_files import capture_image

import time
from pathlib import Path
from truncator.common.storage import read, save, digest
from truncator.common.locking import lock
from truncator.review.review_evidence import capture_hashes

LEVELS = {"production-supported", "mechanism-control", "unresolved"}


def template(capture, *, plan_file=None):
    from truncator.planning.composition import capture_members

    capture = Path(capture)
    plan_file = (
        Path(plan_file) if plan_file is not None else capture.parent / "plan.json"
    )
    plan = read(plan_file) if plan_file.exists() else None
    members = (
        capture_members(plan, read(capture / "capture.json").get("recipe", {}))
        if plan
        else []
    )
    return {
        "identity": identity(capture, plan_file=plan_file),
        "level": "unresolved",
        "reviewer": "",
        "rationale": "",
        "evidence": [],
        "targets": {
            m["id"]: {
                key: ""
                for key in (
                    "coding_mistake",
                    "trigger",
                    "tree_comparison",
                    "repair_observation",
                    "comparison_sha256",
                )
            }
            for m in members
        },
    }


def identity(capture, *, plan_file=None):
    capture = Path(capture)
    hashes = capture_hashes(capture)
    plan = Path(plan_file) if plan_file is not None else capture.parent / "plan.json"
    return {
        "files": hashes,
        "plan_sha256": digest(plan.read_bytes()) if plan.exists() else None,
    }


def validate(review, capture, *, exported=False):
    capture = Path(capture).resolve()
    plan_file = capture / "plan.json" if exported else capture.parent / "plan.json"
    if review.get("identity") != identity(capture, plan_file=plan_file):
        raise ValueError("Case review is not bound to the current capture and plan")
    if review.get("level") not in LEVELS or not review.get("reviewer", "").strip():
        raise ValueError("Case review requires a supported level and reviewer")
    if not review.get("rationale", "").strip():
        raise ValueError("Case review requires an explanation")
    if review["level"] == "production-supported":
        targets = template(capture, plan_file=plan_file)["targets"]
        if not targets or set(review.get("targets", {})) != set(targets):
            raise ValueError(
                "Production review must cover exactly the visible mutation targets"
            )
        for target in review["targets"].values():
            for key in (
                "coding_mistake",
                "trigger",
                "tree_comparison",
                "repair_observation",
            ):
                if not isinstance(target.get(key), str) or not target[key].strip():
                    raise ValueError("Production case review missing " + key)
        roles = {r.get("role") for r in review.get("evidence", [])}
        if not {"independent-source", "tree-comparison", "repair"} <= roles:
            raise ValueError(
                "Production case needs independent source, tree comparison and repair evidence"
            )
    attachments = {}
    for item in review.get("evidence", []):
        path = Path(item["path"])
        if exported:
            if path.is_absolute() or not (capture / path).resolve().is_relative_to(
                capture
            ):
                raise ValueError("Exported case evidence must stay inside the sample")
            path = capture / path
        elif not path.is_absolute():
            raise ValueError("Source case evidence requires absolute paths")
        if digest(path.read_bytes()) != item["sha256"]:
            raise ValueError("Case supporting evidence changed")
        attachments[item["sha256"]] = path
    if review["level"] == "production-supported":
        validate_comparisons(review, capture, plan_file, attachments)
    return review


def validate_comparisons(review, capture, plan_file, attachments):
    """Bind every production claim to a recomputable comparison of this target."""
    from truncator.planning.composition import capture_members
    from research.production_evidence.comparison import verify_bound_comparison

    members = capture_members(read(plan_file), read(capture / "capture.json").get("recipe", {}))
    comparison_hashes = {
        item["sha256"] for item in review["evidence"] if item.get("role") == "tree-comparison"
    }
    for member in members:
        sha = review["targets"][member["id"]].get("comparison_sha256")
        if not isinstance(sha, str) or sha not in comparison_hashes:
            raise ValueError("Production target requires comparison_sha256 bound to tree-comparison evidence")
        comparison = read(attachments[sha])
        reference = comparison.get("reference", {})
        try:
            tree = attachments[reference["tree_sha256"]]
            image = attachments[reference["screenshot_sha256"]]
        except KeyError as exc:
            raise ValueError("Comparison requires attached reference tree and screenshot") from exc
        selector = member.get("geometry", {}).get("mutated_selector")
        if not selector:
            raise ValueError("Production comparison requires the planned mutated_selector")
        verify_bound_comparison(comparison, tree, image, capture / "tree-before.json",
                                capture_image(capture), selector)


def verify_exported_case(folder):
    folder = Path(folder)
    return validate(read(folder / "case-review.json"), folder, exported=True)


def record_case_review(capture, submitted):
    capture = Path(capture).resolve()
    review = validate(read(submitted), capture)
    with lock(capture / "case-review.lock"):
        path = capture / ("case-review-" + str(time.time_ns()) + ".json")
        save(path, review)
    return path


def export_case_review(capture, destination):
    import shutil

    files = sorted(Path(capture).glob("case-review-*.json"))
    if not files:
        return {"level": "unresolved", "reason": "sample_specific_review_missing"}
    review = validate(read(files[-1]), capture)
    exported = {**review, "evidence": []}
    for index, item in enumerate(review.get("evidence", [])):
        relative = "case-evidence/" + str(index) + Path(item["path"]).suffix
        target = Path(destination) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item["path"], target)
        if digest(target.read_bytes()) != item["sha256"]:
            raise ValueError("Case evidence changed during export")
        exported["evidence"].append({**item, "path": relative})
    save(Path(destination) / "case-review.json", exported)
    return {
        "level": review["level"],
        "reviewer": review["reviewer"],
        "review": "case-review.json",
    }
