"""Export a reviewed application once, together with its exact path evidence."""

from truncator.common.capture_files import capture_image
from pathlib import Path
import shutil

from truncator.review.review_policy import retained_plan
from truncator.review.review_evidence import recorded_review, validate_evidence
from truncator.common.storage import read, save, digest, contained
from truncator.review.curation_history import export_history


def reviewed_runs(root):
    return sorted(
        {
            path.parent.resolve()
            for path in Path(root).rglob("review-decisions-*.json")
            if (path.parent / "plan.json").is_file()
            and (path.parent / "profile.json").is_file()
        }
    )


def export_reviewed_applications(runs, destination):
    applications, samples, handled = [], [], set()
    for run in reviewed_runs(runs):
        review = recorded_review(run)
        plan, profile = read(run / "plan.json"), read(run / "profile.json")
        checksum = read(run / "build.json")["hap_sha256"]
        retained_plan(plan, review, checksum)
        captures = validate_evidence(run, plan, review)
        if any(item["decision"] != "keep" for item in review["decisions"].values()):
            raise ValueError(
                "Application still has removed or pending defects; rebuild and review before export: "
                + str(run)
            )
        hap = contained(run / "project", profile["hap"])
        if digest(hap.read_bytes()) != checksum:
            raise ValueError("Reviewed HAP changed")
        identity = plan["id"] + "-" + checksum[:12]
        target = Path(destination) / "applications" / identity
        target.mkdir(parents=True, exist_ok=False)
        shutil.copy2(hap, target / "app.hap")
        save(target / "review.json", review)
        export_history(run, target, plan)
        for name in (
            "plan.json",
            "mutation.diff",
            "profile.json",
            "build.json",
            "adaptations.json",
        ):
            if (run / name).exists():
                shutil.copy2(run / name, target / name)
        source_files = []
        post = read(run / "post-scan.json")
        for relative, expected in plan["file_hashes"].items():
            before = contained(plan["source_root"], relative)
            after = contained(run / "project", relative)
            if (
                digest(before.read_bytes()) != expected
                or digest(after.read_bytes()) != post["files"][relative]
            ):
                raise ValueError("Source evidence changed: " + relative)
            for kind, source in (("before", before), ("after", after)):
                output = contained(target / "source" / kind, relative)
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, output)
            source_files.append(relative)
        paths = []
        pages = {page["name"]: page for page in plan["pages"]}
        for index, capture in enumerate(captures, 1):
            page = pages[capture["page"]]
            folder = target / "paths" / str(index)
            folder.mkdir(parents=True)
            executed_recipe = read(run / capture["capture_id"] / "capture.json")[
                "recipe"
            ]
            save(folder / "recipe.json", executed_recipe)
            shutil.copytree(run / capture["capture_id"], folder / "mutated")
            shutil.copy2(run / "plan.json", folder / "mutated/plan.json")
            baseline = Path(page["baseline_capture"])
            if folder.resolve().is_relative_to(baseline.resolve()):
                raise ValueError("Export destination must be outside baseline evidence")
            for member in plan["mutations"]:
                geometry = member.get("geometry", {})
                if (
                    geometry.get("baseline_capture")
                    and Path(geometry["baseline_capture"]).resolve()
                    == baseline.resolve()
                ):
                    for name, key in (
                        (capture_image(baseline).name, "baseline_image_sha256"),
                        ("tree-before.json", "baseline_tree_sha256"),
                    ):
                        if digest((baseline / name).read_bytes()) != geometry[key]:
                            raise ValueError("Normal baseline evidence changed")
            shutil.copytree(baseline, folder / "baseline")
            item = {
                "id": identity + "/" + str(index),
                "page": page["name"],
                "application": identity,
                "mutation_ids": page["mutation_ids"],
                "path": folder.relative_to(destination).as_posix(),
                "reviewer": review.get("reviewer", "unspecified"),
                "mutations": [{"id": m["id"], "mechanism": m["operator"],
                               "component": m["site"].get("component", "unknown"),
                               "edge": m.get("geometry", {}).get("edge", "unknown")}
                              for m in plan["mutations"] if m["id"] in page["mutation_ids"]],
                "device": capture["device"],
                "target_observations": {
                    key: {field: review["decisions"][key][field]
                          for field in ("content_status", "recovery_status")}
                    for key in page["mutation_ids"]
                    if "content_status" in review["decisions"][key]
                },
            }
            paths.append(item)
            samples.append(item)
        application = {
            "id": identity,
            "plan_id": plan["id"],
            "hap_sha256": checksum,
            "hap": (target / "app.hap").relative_to(destination).as_posix(),
            "source_run": str(run),
            "source_files": source_files,
            "mutation_ids": [m["id"] for m in plan["mutations"]],
            "paths": paths,
        }
        save(target / "manifest.json", application)
        applications.append(application)
        handled.add(run)
    return applications, samples, handled
