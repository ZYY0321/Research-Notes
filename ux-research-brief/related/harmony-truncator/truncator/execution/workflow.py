"""Persistent batch execution and human review records."""

from truncator.common.capture_files import capture_image

from pathlib import Path
import time
import math
from truncator.source.project import prepare

from truncator.execution.build import build
from truncator.execution.device.runtime import capture, latest_capture
from truncator.common.storage import read, save, digest
from truncator.common.locking import lock
from PIL import Image


def batch(profile, plan_files, output, device=None, recipe=None, *, force_capture=False):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = []
    for filename in sorted(plan_files):
        run = None
        assessment = None
        application = None
        stage = "plan"
        try:
            plan = read(filename)
            plan_id = plan["id"]
            if (not isinstance(plan_id, str) or not plan_id
                    or plan_id in {".", ".."} or any(c in plan_id for c in '/\\:')):
                raise ValueError("Invalid plan ID for run directory")
            run = output / plan_id
            if run.resolve().parent != output:
                raise ValueError("Plan run escapes the batch workspace")
            stage = "prepare"
            if not run.exists():
                prepare(profile, run, plan)
            else:
                if read(run / "profile.json") != profile or (
                    (run / "plan.json").exists() and read(run / "plan.json") != plan
                ):
                    raise ValueError("Resume inputs differ from immutable run record")
                if not (run / "prepared.json").exists():
                    if (run / "build.json").exists() or list(
                        run.glob("capture-*/capture.json")
                    ):
                        raise ValueError("Prepared record missing from a completed run")
                    backup = output / (
                        "incomplete-" + plan["id"] + "-" + str(time.time_ns())
                    )
                    if (
                        run.resolve().parent != output
                        or backup.resolve().parent != output
                    ):
                        raise ValueError(
                            "Incomplete preparation escapes the run workspace"
                        )
                    run.rename(backup)
                    prepare(profile, run, plan)
                elif not (run / "plan.json").exists():
                    raise ValueError("Prepared mutation run is missing its plan")
            if not (run / "build.json").exists():
                stage = "build"
                build(profile, run)
            stage = "verify_package"
            if profile.get("hap"):
                hap = run / "project" / profile["hap"]
                checksum = digest(hap.read_bytes())
                if checksum != read(run / "build.json")["hap_sha256"]:
                    raise ValueError("Built HAP differs from saved build record")
                application = {
                    "hap": str(hap),
                    "hap_sha256": checksum,
                    "source_project": str(run / "project"),
                    "mutation_diff": str(run / "mutation.diff"),
                    "bundle": profile.get("bundle"),
                    "recipe": recipe,
                    "review": "pending",
                }
            if device:
                stage = "capture"
                selected_capture = latest_capture(run, device, recipe, force=force_capture)
                if selected_capture is None:
                    selected_capture = capture(profile, run, device, recipe, output)
                assessment = {
                    "capture": str(selected_capture),
                    "next_action": "post_batch_review",
                }
                for name in ("diagnostics", "image-quality", "geometry-observation"):
                    evidence_file = selected_capture / (name + ".json")
                    if evidence_file.exists():
                        assessment[name] = read(evidence_file)
            report.append(
                {
                    "plan": str(filename),
                    "run": str(run) if run is not None else None,
                    "status": "captured" if device else "built",
                    "assessment": assessment,
                    "application": application,
                }
            )
        except Exception as error:
            report.append(
                {
                    "plan": str(filename),
                    "run": str(run) if run is not None else None,
                    "status": "failed",
                    "failed_stage": stage,
                    "error": str(error),
                    "application": application,
                }
            )
        save(output / "batch-results.json", report)
        save(
            output / "review-queue.json",
            {"policy": "post-batch", "applications": report},
        )
    return report


def review(capture_dir, decision, reviewer, reason, boxes, *,
           content_status=None, recovery_status=None, evidence_captures=()):
    from truncator.review.review_policy import validate_observation_labels
    from truncator.review.review_evidence import capture_hashes

    validate_observation_labels(content_status, recovery_status)
    if decision not in {"accepted", "rejected", "needs-review"}:
        raise ValueError("Unknown review decision")
    capture_dir = Path(capture_dir)
    record = read(capture_dir / "capture.json")
    screenshot = capture_image(capture_dir)
    hashes = capture_hashes(capture_dir)
    if not reviewer.strip() or not reason.strip():
        raise ValueError("Reviewer and evidence reason are required")
    evidence = []
    for directory in evidence_captures:
        directory = Path(directory).resolve()
        other = read(directory / "capture.json")
        if not record.get("hap_sha256") or other.get("hap_sha256") != record["hap_sha256"]:
            raise ValueError("Additional evidence must use the same application package")
        evidence.append({"capture": str(directory), "sha256": capture_hashes(directory)})
    with Image.open(screenshot) as image:
        width, height = image.size
    for box in boxes:
        if (
            len(box) != 4
            or any(
                isinstance(x, bool)
                or not isinstance(x, (int, float))
                or not math.isfinite(x)
                for x in box
            )
            or box[0] < 0
            or box[1] < 0
            or box[2] <= box[0]
            or box[3] <= box[1]
            or box[2] > width
            or box[3] > height
        ):
            raise ValueError("Invalid pixel box")
    with lock(capture_dir / "review.lock"):
        path = capture_dir / ("review-" + str(time.time_ns()) + ".json")
        save(
            path,
            {
                "decision": decision,
                "reviewer": reviewer,
                "reason": reason,
                "boxes_px": boxes,
                "screenshot_sha256": record["screenshot_sha256"],
                "capture_files": hashes,
                "time": time.time(),
                **({"content_status": content_status, "recovery_status": recovery_status}
                   if content_status is not None else {}),
                **({"evidence_captures": evidence} if evidence else {}),
            },
        )
    return path


def status(root):
    return [
        {
            "run": str(path),
            "prepared": (path / "prepared.json").exists(),
            "built": (path / "build.json").exists(),
            "captures": len(list(path.glob("capture-*/capture.json"))),
            "failures": len(list(path.glob("capture-*/failure.json"))),
        }
        for path in sorted(
            {record.parent for record in Path(root).rglob("profile.json")}
        )
        if (path / "prepared.json").exists()
    ]
