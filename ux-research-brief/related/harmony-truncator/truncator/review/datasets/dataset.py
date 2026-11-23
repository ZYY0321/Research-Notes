from pathlib import Path
import shutil
from truncator.common.storage import read, save, digest
from truncator.planning.composition import capture_members
from truncator.review.datasets.delivery import export_reviewed_applications
from truncator.review.datasets.export_transaction import export_transaction
from truncator.review.review_policy import validate_observation_labels
from truncator.review.review_evidence import validate_single_review
from truncator.common.capture_files import capture_image, evidence_files


def export_dataset(runs, destination):
    with export_transaction(runs, destination) as staging:
        count = _write_dataset(runs, staging)
        from truncator.review.datasets.dataset_balance import audit_exports
        audit = audit_exports([staging])
        for unit in audit["units"]:
            unit["export"] = "."
            for source in unit["sources"]:
                source["export"] = "."
        for duplicate in audit["duplicates_excluded"]:
            duplicate["export"] = "."
        for conflict in audit["conflicts"]:
            for observation in conflict["observations"]:
                observation["export"] = "."
        for item in audit["revisions"]["excluded_target_states"]:
            item["export"] = "."
        save(staging / "balance.json", audit)
        return count


def _write_dataset(runs, destination):
    """Discover and export ordinary reviewed captures and application packages."""
    save(destination / "export-status.json", {"complete": False})
    applications, samples, handled = export_reviewed_applications(runs, destination)
    for capture_record in sorted(Path(runs).glob("**/capture-*/capture.json")):
        folder = capture_record.parent
        if folder.parent.resolve() in handled:
            continue
        sample = export_capture(folder, destination)
        if sample is not None:
            samples.append(sample)
    save(
        destination / "manifest.json",
        {
            "schema_version": 2 if applications else 1,
            "applications": applications,
            "samples": samples,
            "split_policy": "Unassigned; group by app/page before evaluation",
        },
    )
    save(
        destination / "export-status.json",
        {"complete": True, "sample_count": len(samples)},
    )
    return len(samples)


def export_capture(folder, destination):
    """Validate and copy one accepted capture; return its manifest entry."""
    folder, destination = Path(folder), Path(destination)
    capture_record = folder / "capture.json"
    reviews = sorted(folder.glob("review-*.json"))
    if not reviews or read(reviews[-1])["decision"] != "accepted":
        return None
    review = read(reviews[-1])
    validate_observation_labels(review.get("content_status"), review.get("recovery_status"))
    for required in evidence_files(folder):
        if not (folder / required).is_file():
            raise ValueError(
                "Accepted sample missing evidence: " + str(folder / required)
            )
    validate_single_review(folder, review)
    run = folder.parent
    identity = digest(str(folder.resolve()))[:20]
    target = destination / identity
    target.mkdir()
    for name in [
        *evidence_files(folder),
        "targets.json",
        "geometry-observation.json",
        "display.json",
        "diagnostics.json",
        "image-quality.json",
    ]:
        if (folder / name).exists():
            shutil.copy2(folder / name, target / name)
    exported_evidence = []
    for index, evidence in enumerate(review.get("evidence_captures", []), 1):
        source = Path(evidence["capture"])
        if set(evidence["sha256"]) != set(evidence_files(source)):
            raise ValueError("Additional evidence must contain image, trees and capture record")
        package = read(capture_record).get("hap_sha256")
        if not package or read(source / "capture.json").get("hap_sha256") != package:
            raise ValueError("Additional evidence belongs to a different application package")
        relative = "evidence-captures/" + str(index)
        extra = target / relative
        extra.mkdir(parents=True)
        for name, checksum in evidence["sha256"].items():
            if digest((source / name).read_bytes()) != checksum:
                raise ValueError("Reviewed additional evidence changed")
            shutil.copy2(source / name, extra / name)
        exported_evidence.append({**evidence, "capture": relative})
    exported_review = dict(review)
    if exported_evidence:
        exported_review["evidence_captures"] = exported_evidence
    save(target / "review.json", exported_review)
    for name in [
        "plan.json",
        "mutation.diff",
        "profile.json",
        "adaptations.json",
        "build.json",
    ]:
        if (run / name).exists():
            shutil.copy2(run / name, target / name)
    plan = read(run / "plan.json") if (run / "plan.json").exists() else None
    active = (
        capture_members(plan, read(capture_record).get("recipe", {}))
        if plan
        else []
    )
    for member in active:
        geometry = member.get("geometry")
        if not geometry:
            continue
        baseline = Path(geometry["baseline_capture"])
        expected = {
            capture_image(baseline).name: geometry["baseline_image_sha256"],
            "tree-before.json": geometry["baseline_tree_sha256"],
        }
        for name, checksum in expected.items():
            if digest((baseline / name).read_bytes()) != checksum:
                raise ValueError(
                    "Baseline evidence changed: " + str(baseline / name)
                )
        paired = (
            target / "baselines" / member["id"]
            if "mutations" in plan
            else target / "baseline"
        )
        paired.mkdir(parents=True)
        for name in [
            *evidence_files(baseline),
            "display.json",
        ]:
            if (baseline / name).exists():
                shutil.copy2(baseline / name, paired / name)
    profile = read(run / "profile.json") if (run / "profile.json").exists() else {}
    return {
        "id": identity,
        "source_run": str(run),
        "baseline": plan is None,
        "split_group": profile.get("bundle", "unknown")
        + "/"
        + (
            "combined"
            if plan and "mutations" in plan
            else plan["site"]["file"] if plan else "baseline"
        ),
        "mechanism": (
            "combined"
            if plan and "mutations" in plan
            else plan.get("mechanism", plan["operator"]) if plan else None
        ),
        "mutations": [
            {
                "id": member.get("id"),
                "mechanism": member["operator"],
                "file": member["site"]["file"],
                "component": member["site"]["component"],
                "edge": member.get("geometry", {}).get("edge", "unknown"),
            }
            for member in active
        ],
        "reviewer": review["reviewer"],
        "component": plan["site"]["component"] if plan and "site" in plan else "unknown",
        **({"content_status": review["content_status"],
            "recovery_status": review["recovery_status"]}
           if "content_status" in review else {}),
    }
