"""Summarize explicit campaign/curation batches, including failures before export."""
from collections import Counter
from pathlib import Path
from truncator.common.storage import read
from truncator.review.review_evidence import recorded_review


def _batch_records(root):
    results = read(root / "results.json") if (root / "results.json").exists() else []
    if (root / "campaign.json").exists():
        configured = read(root / "campaign.json")["applications"]
    elif (root / "curation.json").exists():
        curation = read(root / "curation.json")
        plan_path = root / "plans" / (curation["new_plan"] + ".json")
        plan = read(plan_path)
        configured = [{"pages": plan["pages"]}]
        if results:
            results[0] = {**results[0], "combined_plan": str(plan_path)}
    elif (root / "results.json").exists():
        configured = [{} for _ in results]
    else:
        raise ValueError("Run summary requires a campaign, curation or results record: " + str(root))
    return configured, results


def _package_rows(actual):
    rows = [row for page in actual.get("pages", []) for case in page.get("cases", [])
            for row in case.get("runs", [])]
    # A package may already be built when the first page has not been recorded.
    if actual.get("combined_plan"):
        plan_path = Path(actual["combined_plan"])
        checkpoint = plan_path.parent.parent / "mutations/batch-results.json"
        if checkpoint.exists():
            rows.extend(row for row in read(checkpoint) if Path(row["plan"]).stem == plan_path.stem)
    return rows


def _package_summary(row):
    run = Path(row["run"]).resolve()
    plan = read(run / "plan.json") if (run / "plan.json").exists() else {}
    built = read(run / "build.json") if (run / "build.json").exists() else {}
    review = recorded_review(run)
    decisions = Counter(item["decision"] for item in (review or {}).get("decisions", {}).values())
    return {"run": str(run), "plan_id": plan.get("id"),
            "planned_targets": len(plan.get("mutations", [])),
            "build": "succeeded" if built.get("hap_sha256") else "failed-or-not-built",
            "hap_sha256": built.get("hap_sha256"),
            "review_decisions": dict(decisions), "review_recorded": review is not None}


def summarize_runs(runs):
    roots = sorted({Path(path).resolve() for path in runs}, key=str)
    applications, packages, reasons = [], {}, Counter()
    for root in roots:
        configured, results = _batch_records(root)
        for index, config in enumerate(configured):
            actual = results[index] if index < len(results) else {}
            pages = actual.get("pages", [])
            page_specs = config.get("pages", [config]) if config else pages
            outcomes = []
            for page_index, page_spec in enumerate(page_specs):
                name = page_spec.get("name", "page-" + str(page_index + 1))
                found = next((p for p in pages if p["name"] == name), {})
                outcomes.append({"page": name, "status": found.get("status", "not-started"),
                                 "planned_target_appearances": len(found.get("mutation_ids", []))})
            for row in _package_rows(actual):
                if row.get("run") and str(Path(row["run"]).resolve()) not in packages:
                    package = _package_summary(row)
                    packages[package["run"]] = package
            status = actual.get("status", "running" if actual else "not-started")
            applications.append({"batch": str(root), "application": config.get("profile", actual.get("application")),
                                 "status": status, "pages": outcomes, "error": actual.get("error")})
            if actual.get("error"):
                reasons[actual["error"]] += 1
    page_rows = [page for app in applications for page in app["pages"]]
    return {
        "batches": [str(root) for root in roots],
        "application_attempts": len(applications),
        "application_status": dict(Counter(app["status"] for app in applications)),
        "configured_page_attempts": len(page_rows),
        "page_status": dict(Counter(page["status"] for page in page_rows)),
        "unique_package_runs": len(packages),
        "build_status": dict(Counter(run["build"] for run in packages.values())),
        "planned_targets": sum(run["planned_targets"] for run in packages.values()),
        "recorded_review_decisions": dict(sum((Counter(run["review_decisions"]) for run in packages.values()), Counter())),
        "application_errors": dict(reasons),
        "applications": applications, "packages": list(packages.values()),
        "policy": "Execution attempts across explicitly selected batches; repeated batch paths and shared package runs count once. Page denominator is configured routes only. Historical rebuild attempts remain visible; use dataset-audit for latest reviewed deliverable counts.",
    }
