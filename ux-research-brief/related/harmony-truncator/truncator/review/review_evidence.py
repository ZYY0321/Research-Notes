"""Persist review records and verify their exact capture evidence."""

import json
import time
from pathlib import Path

from truncator.common.storage import digest, read, save, contained
from truncator.review.review_policy import retained_plan
from truncator.planning.pages import resolve_page, page_id
from truncator.common.capture_files import capture_image, evidence_files


def capture_hashes(capture):
    """Identify the complete image/tree observation, checking its recorded image."""
    capture = Path(capture)
    hashes = {name: digest((capture / name).read_bytes()) for name in evidence_files(capture)}
    if read(capture / "capture.json")["screenshot_sha256"] != hashes[capture_image(capture).name]:
        raise ValueError("Reviewed screenshot changed")
    return hashes


def validate_single_review(capture, review, *, exported=False):
    """Require the exact primary and recovery evidence seen by the reviewer."""
    capture = Path(capture)
    expected = review.get("capture_files")
    if not isinstance(expected, dict) or set(expected) != set(evidence_files(capture)):
        raise ValueError("Review lacks four-file capture binding; review the current evidence again")
    actual = capture_hashes(capture)
    if actual != expected or review.get("screenshot_sha256") != actual[capture_image(capture).name]:
        raise ValueError("Reviewed capture changed")
    package = read(capture / "capture.json").get("hap_sha256")
    for evidence in review.get("evidence_captures", []):
        folder = contained(capture, evidence["capture"]) if exported else Path(evidence["capture"])
        if not package or read(folder / "capture.json").get("hap_sha256") != package:
            raise ValueError("Reviewed additional evidence belongs to another application package")
        if evidence.get("sha256") != capture_hashes(folder):
            raise ValueError("Reviewed additional evidence changed")


def capture_identity(run, page, capture):
    run, capture = Path(run).resolve(), Path(capture).resolve()
    if capture.parent != run or not capture.name.startswith("capture-"):
        raise ValueError("Reviewed capture must belong to the selected run")
    record = read(capture / "capture.json")
    if resolve_page({"pages": [page]}, record.get("recipe", {})) is None:
        raise ValueError("Reviewed capture recipe differs from page " + page["name"])
    if record.get("page_id") is not None and record["page_id"] != page_id(page):
        raise ValueError("Reviewed capture page_id differs from the selected page")
    hashes = capture_hashes(capture)
    return {
        "page": page["name"],
        "capture_id": capture.name,
        "device": record.get("device"),
        "recipe_sha256": digest(json.dumps(record["recipe"], sort_keys=True)),
        "files": hashes,
    }


def validate_evidence(run, plan, review):
    if review.get("schema_version") != 2 or "captures" not in review:
        raise ValueError(
            "Review lacks exact capture evidence; regenerate the report and review its images"
        )
    captures = review["captures"]
    pages = {page["name"]: page for page in plan["pages"]}
    if (
        not isinstance(captures, list)
        or len(captures) != len(pages)
        or {item.get("page") for item in captures} != set(pages)
    ):
        raise ValueError("Review must bind every configured page exactly once")
    for item in captures:
        page = pages[item["page"]]
        actual = capture_identity(run, page, Path(run) / item["capture_id"])
        if actual != item:
            raise ValueError("Reviewed evidence changed for page " + page["name"])
        capture_record = read(Path(run) / item["capture_id"] / "capture.json")
        resolved = resolve_page(plan, capture_record["recipe"])
        if resolved is None or page_id(resolved) != page_id(page):
            raise ValueError(
                "Reviewed capture does not uniquely identify page " + page["name"]
            )
        if (
            capture_record.get("hap_sha256", review["hap_sha256"])
            != review["hap_sha256"]
        ):
            raise ValueError("Reviewed capture belongs to a different HAP")
    return captures


def recorded_review(run):
    files = sorted(Path(run).glob("review-decisions-*.json"))
    return read(files[-1]) if files else None


def record_review(run, review_file):
    run = Path(run).resolve()
    plan, profile = read(run / "plan.json"), read(run / "profile.json")
    checksum = read(run / "build.json")["hap_sha256"]
    if digest((run / "project" / profile["hap"]).read_bytes()) != checksum:
        raise ValueError("Application package changed since build")
    review = read(review_file)
    retained_plan(plan, review, checksum)
    captures = validate_evidence(run, plan, review)
    result = {**review, "captures": captures, "recorded_at": time.time()}
    path = run / ("review-decisions-" + str(time.time_ns()) + ".json")
    save(path, result)
    return path
