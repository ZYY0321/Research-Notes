"""Configuration-driven, resumable cross-project experiments."""

from pathlib import Path
from truncator.source.binding import bind_candidates
from truncator.execution.campaign_source import prepare_application
from truncator.execution.device.runtime import capture, latest_capture
from truncator.common.storage import read, save
from truncator.execution.workflow import batch
from truncator.planning.calibration import plan_from_baseline
from truncator.planning.baseline import load_baseline
from truncator.planning.campaign_policy import effective_page, selected_operators, validate_campaign
from truncator.planning.composition import select_combination, compose


def save_campaign_results(destination, results):
    save(destination / "results.json", results)
    applications = []
    for application in results:
        if application.get("combined_plan"):
            page_runs = [
                {"page": page["name"], **run}
                for page in application["pages"]
                for case in page.get("cases", [])
                for run in case.get("runs", [])
            ]
            if page_runs:
                applications.append(
                    {
                        "plan": application["combined_plan"],
                        "run": page_runs[0]["run"],
                        "application": page_runs[0].get("application"),
                        "page_captures": page_runs,
                    }
                )
            continue
        for page in application.get("pages", [application]):
            for case in page.get("cases", []):
                for run in case.get("runs", []):
                    applications.append({**run, "page": page.get("name", "default")})
    save(
        destination / "review-queue.json",
        {"policy": "post-batch", "applications": applications},
    )


def run_combined_application(application, folder, device, record, checkpoint):
    """Collect every baseline first, then prepare/build one multi-defect application."""
    profile = read(application["profile"])
    profile, catalog, baseline = prepare_application(profile, application, folder)
    save(folder / "catalog.json", catalog)
    record["source_choice"] = str(folder / "source-choice.json")
    page_specs = application.get("pages", [application])
    if not isinstance(page_specs, list) or not page_specs:
        raise ValueError("pages must be a nonempty list")
    record["pages"] = []
    candidates, planning_failures = [], []
    sites = {site["id"]: site for site in catalog["sites"]}
    for index, spec in enumerate(page_specs):
        page = effective_page(application, spec)
        name = page.get("name", "page-" + str(index + 1))
        if any(p["name"] == name for p in record["pages"]):
            raise ValueError("Page names must be unique")
        recipe = read(page["recipe"])
        recipe = {**recipe, "page_id": page.get("page_id", recipe.get("page_id", name))}
        if not isinstance(recipe["page_id"], str) or not recipe["page_id"].strip():
            raise ValueError("page_id must be a nonempty string")
        if any(
            p["recipe"].get("page_id") == recipe["page_id"] for p in record["pages"]
        ):
            raise ValueError("Page IDs must be unique")
        capture_dir = latest_capture(baseline, device, recipe)
        if capture_dir is None:
            capture_dir = capture(profile, baseline, device, recipe, folder)
        page_record = {
            "name": name,
            "recipe": recipe,
            "baseline_capture": str(capture_dir),
            "cases": [],
            "status": "baseline_captured",
        }
        record["pages"].append(page_record)
        bindings = bind_candidates(
            catalog, read(capture_dir / "tree-before.json"), page.get("file", "")
        )
        save(folder / "pages" / str(index + 1) / "bindings.json", bindings)
        allowed = selected_operators(page, "combined")
        for binding in sorted(bindings["bindings"], key=lambda b: b["site"]):
            try:
                target_baseline = load_baseline(catalog, capture_dir, binding, page.get("px_per_vp"))
            except (ValueError, OSError, RuntimeError, KeyError, StopIteration) as error:
                planning_failures.append({"page": name, "site": binding["site"],
                                          "stage": "baseline", "reason": str(error)})
                continue
            for operator in allowed:
                if operator not in sites[binding["site"]]["operators"]:
                    continue
                try:
                    candidate = plan_from_baseline(
                        catalog,
                        target_baseline,
                        operator,
                        budget=1,
                    )[0]
                    candidates.append(candidate)
                except (
                    ValueError,
                    OSError,
                    RuntimeError,
                    KeyError,
                    StopIteration,
                ) as error:
                    planning_failures.append(
                        {
                            "page": name,
                            "site": binding["site"],
                            "operator": operator,
                            "reason": str(error),
                        }
                    )
        checkpoint()
    selected, selection = select_combination(
        candidates,
        record["pages"],
        application.get("max_total", 12),
        application.get("max_per_page", 3),
        application.get("max_area_ratio", 0.30),
        application.get("seed", 0),
    )
    selection["planning_failures"] = planning_failures
    save(folder / "selection.json", selection)
    combined = compose(selected, record["pages"], selection)
    plan_file = folder / "plans" / (combined["id"] + ".json")
    save(plan_file, combined)
    record["combined_plan"] = str(plan_file)
    record["planned_targets"] = len(selected)
    # Compile each combined package once; a failed build must not repeat for every route.
    built = batch(profile, [plan_file], folder / "mutations")
    for page_record in record["pages"]:
        runs = built if built[0]["status"] == "failed" else batch(
            profile, [plan_file], folder / "mutations", device, page_record["recipe"]
        )
        page_record["cases"] = [{"runs": runs}]
        page_record["mutation_ids"] = next(
            p["mutation_ids"]
            for p in combined["pages"]
            if p["name"] == page_record["name"]
        )
        page_record["status"] = runs[0]["status"]
        if device and page_record["status"] == "captured" and application.get("verify_recovery", True):
            from truncator.execution.device.recovery import verify_scroll_members
            assessment = runs[0].get("assessment") or {}
            if assessment.get("capture"):
                evidence = verify_scroll_members(profile, runs[0]["run"], assessment["capture"],
                                                 device, page_record["recipe"])
                if evidence:
                    page_record["recovery_evidence"] = str(evidence)
        checkpoint()
    record["status"] = (
        "failed"
        if any(p["status"] == "failed" for p in record["pages"])
        else "captured"
    )


def campaign(specification, destination, device):
    policy = validate_campaign(specification)
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    saved = destination / "campaign.json"
    if saved.exists() and read(saved) != specification:
        raise ValueError("Campaign configuration differs from saved run")
    saved_policy = destination / "operator-policy.json"
    if saved_policy.exists() and read(saved_policy) != policy:
        raise ValueError("Operator policy differs from saved run; use a new campaign directory")
    save(saved, specification)
    save(saved_policy, policy)
    results = []
    for index, application in enumerate(specification["applications"]):
        folder = destination / ("app-" + str(index + 1))
        folder.mkdir(exist_ok=True)
        record = {"application": application["profile"], "pages": []}
        results.append(record)
        try:
            run_combined_application(
                application, folder, device, record,
                lambda: save_campaign_results(destination, results),
            )
        except (ValueError, OSError, RuntimeError, KeyError) as error:
            record.update(status="failed", error=str(error))
        save_campaign_results(destination, results)
    from truncator.review.reporting.evidence import generate_report

    generate_report(destination, results)
    return results
