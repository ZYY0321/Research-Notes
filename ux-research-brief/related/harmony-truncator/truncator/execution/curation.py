"""Rebuild and recapture applications after explicit defect-level review."""

import json
from pathlib import Path

from truncator.common.storage import digest, read, save
from truncator.common.locking import lock
from truncator.execution.workflow import batch

from truncator.review.review_policy import retained_plan
from truncator.review.review_evidence import validate_evidence
from truncator.review.curation_history import validated_history, carry_history


def rebuild_reviewed(run, review_file, destination, device):
    """Build once, replay all configured paths, then generate a new evidence report."""
    destination = Path(destination).resolve()
    with lock(
        destination.parent / (".curate-" + digest(str(destination))[:16] + ".lock")
    ):
        return _rebuild_reviewed(run, review_file, destination, device)


def _rebuild_reviewed(run, review_file, destination, device):
    run, destination = Path(run).resolve(), Path(destination).resolve()
    profile, plan = read(run / "profile.json"), read(run / "plan.json")
    review = read(review_file)
    build_record = read(run / "build.json")
    for relative, expected in plan["file_hashes"].items():
        if digest((Path(plan["source_root"]) / relative).read_bytes()) != expected:
            raise ValueError(
                "Baseline source changed since original planning: " + relative
            )
    if (
        digest((run / "project" / profile["hap"]).read_bytes())
        != build_record["hap_sha256"]
    ):
        raise ValueError("Original HAP changed since capture")
    curated = retained_plan(plan, review, build_record["hap_sha256"])
    validate_evidence(run, plan, review)
    validated_history(run, plan)
    if destination.is_relative_to(run) or run.is_relative_to(destination):
        raise ValueError("Review export and original run must be disjoint")
    inputs = {
        "source_run": str(run),
        "captures": review["captures"],
        "plan_id": curated["id"],
        "device": device,
        "profile": profile,
    }
    destination.mkdir(parents=True, exist_ok=True)
    inputs_file = destination / "curation-input.json"
    if inputs_file.exists():
        if read(inputs_file) != inputs:
            raise ValueError("Resume inputs differ from saved curation inputs")
    elif any(destination.iterdir()):
        raise ValueError("Existing output has no matching curation input record")
    else:
        save(inputs_file, inputs)
    save(destination / "parent-review.json", review)
    save(
        destination
        / "review-history"
        / (digest(json.dumps(review, sort_keys=True)) + ".json"),
        review,
    )
    save(
        destination / "curation.json",
        {
            "source_run": str(run),
            "parent_plan": plan["id"],
            "new_plan": curated["id"],
            "pending": [
                key
                for key, item in review["decisions"].items()
                if item["decision"] == "pending"
            ],
            "policy": "remove-only; retained parameters unchanged; recapture all paths",
        },
    )
    plan_file = destination / "plans" / (curated["id"] + ".json")
    save(plan_file, curated)
    application = {"application": profile["source"], "combined_plan": str(plan_file),
                   "planned_targets": len(curated["mutations"]), "pages": [], "status": "running"}
    save(destination / "results.json", [application])
    # One package build per invocation; each page then reuses that package.
    built = batch(profile, [plan_file], destination / "mutations")
    if built[0].get("run") and (Path(built[0]["run"]) / "prepared.json").exists():
        carry_history(run, Path(built[0]["run"]), plan, curated, review, build_record["hap_sha256"])
    reviewed_captures = {item["page"]: item for item in review["captures"]}
    for page in curated["pages"]:
        captured = read(
            run / reviewed_captures[page["name"]]["capture_id"] / "capture.json"
        )
        page = {**page, "recipe": captured["recipe"]}
        rows = built if built[0]["status"] == "failed" else batch(
            profile, [plan_file], destination / "mutations", device, page["recipe"]
        )
        application["pages"].append(
            {
                **page,
                "cases": [{"runs": rows}],
                "status": rows[0]["status"],
            }
        )
        save(destination / "results.json", [application])
    application["status"] = (
        "failed"
        if any(p["status"] == "failed" for p in application["pages"])
        else "captured"
    )
    save(destination / "results.json", [application])
    from truncator.review.reporting.evidence import generate_report

    generate_report(destination, [application])
    return application
