"""Reproduce the November 17 six-page audit from supplied original captures."""

from pathlib import Path
from truncator.common.capture_files import capture_image

from research.production_evidence.comparison import inspect_target, compare_targets
from truncator.common.storage import save, read


def main():
    project = Path(__file__).resolve().parents[2]
    experiments = project.parent / "2026-11-12_鸿蒙缺陷注入方案" / "实验"
    output = project / "artifacts" / "real-case-local-audit-20261117"
    selectors = {
        "02": {"type": "tab", "text": "人脸识别"},
        "03": {"type": "image", "origBounds": "[1575,39][1791,189]"},
        "04": {"type": "Text", "text": "火车票", "hostWindowId": "82"},
        "05": {"type": "Text", "text": "收藏/浏览", "hostWindowId": "193"},
        "06": {"type": "Text", "text": "登录58同城享受更多精彩服务"},
    }
    records = []
    for directory in sorted((experiments / "真截断实例").iterdir()):
        identifier = directory.name[:2]
        record = {"case": directory.name, "directory": str(directory),
                  "provided_description": (directory / "说明.txt").read_text(encoding="utf-8-sig").strip()}
        if identifier == "01":
            record.update(status="target_unresolved", findings=[
                "Screenshot shows bottom-edge loss of the orange login button.",
                "Supplied description calls it top-edge clipping.",
                "No uniquely bound login button found in the supplied Web subtree.",
            ])
        else:
            result = inspect_target(next(directory.glob("layout*")),
                                    next(directory.glob("screenshot.*")), selectors[identifier])
            save(output / (identifier + "-target.json"), result)
            record.update(status="structural_evidence_extracted", selector=selectors[identifier])
        records.append(record)
    save(output / "manifest.json", {
        "cases": records, "independent_human_review": False,
        "reference_origin": "user_supplied_commercial_app_captures",
        "injected_origin": "our_source_mutations_run_in_open_source_shopping_app",
        "previous_audit": str(project / "artifacts" / "real-case-audit-20261117"),
        "target_correction": "Case 04 now binds the visibly clipped train-ticket Text. "
                             "The previous Scroll selection describes page context.",
    })
    injected = experiments / "captures" / "00-line_clip" / "mutated"
    synthetic = inspect_target(injected / "tree-before.json", capture_image(injected),
                               {"id": "target", "type": "Text"})
    reference_dir = next((experiments / "真截断实例").glob("06*"))
    reference = inspect_target(reference_dir / "layout_tree.json", reference_dir / "screenshot.png",
                               selectors["06"])
    save(output / "58-versus-line-clip.json", compare_targets(reference, synthetic))
    export = Path("E:/HarmonyDev/MutationRuns/commerce-priority-export-20261114/applications")
    application = next(export.iterdir())
    plan = read(application / "plan.json")
    comparisons = []
    for member in plan["mutations"]:
        page_number = next(index for index, page in enumerate(plan["pages"], 1)
                           if member["id"] in page["mutation_ids"])
        path = application / "paths" / str(page_number) / "mutated"
        evidence = inspect_target(path / "tree-before.json", capture_image(path),
                                  member["geometry"]["mutated_selector"])
        filename = "injected-" + member["id"] + ".json"
        save(output / filename, evidence)
        for identifier in selectors:
            real = read(output / (identifier + "-target.json"))
            comparison = compare_targets(real, evidence)
            comparisons.append({"real_case": identifier, "mutation_id": member["id"],
                                "operator": member["operator"], "injected_evidence": filename,
                                "reference_evidence": identifier + "-target.json",
                                "feature_comparison": comparison["feature_comparison"],
                                 "local_feature_comparison": comparison["local_feature_comparison"],
                                 "local_assessment": comparison["local_assessment"],
                                "mechanism_assessment": comparison["mechanism_assessment"]})
    save(output / "commerce-comparison-matrix.json", comparisons)
    summary = {
        "comparison_count": len(comparisons),
        "status_counts": {status: sum(row["local_assessment"]["status"] == status
                                      for row in comparisons)
                          for status in ("structural_candidate", "different", "incomplete")},
        "structural_candidates": [{key: row[key] for key in (
            "real_case", "mutation_id", "operator", "reference_evidence", "injected_evidence")}
            for row in comparisons if row["local_assessment"]["status"] == "structural_candidate"],
        "interpretation": "Candidate means equality of the specified local exported relations. "
                          "Visual content and recovery must be reviewed separately. "
                          "Counts are pair comparisons, not numbers of validated operators.",
    }
    save(output / "summary.json", summary)
    print(output)
    print(summary["status_counts"])


if __name__ == "__main__":
    main()
