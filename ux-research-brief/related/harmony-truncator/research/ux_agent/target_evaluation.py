"""Target-level diagnostics; keep visible clipping separate from recoverability.

The edge check is a declared geometric proxy, not a glyph-level IoU metric.
Only reviewed targets contribute to the final target confusion matrix.
"""
from collections import Counter
from pathlib import Path

from truncator.imaging.geometry import rectangle
from truncator.common.storage import read, save


def intersection(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def truth(row):
    if row.get("content_status") == "complete" or row.get("recovery_status") == "recovered":
        return False
    if row.get("content_status") == "clipped" and row.get("recovery_status") == "not-recovered":
        return True
    return None


def match_candidate(candidate, target, edge, tolerance):
    bounds = rectangle(target["bounds"])
    box = candidate["bbox_px"]
    area = max(0, box[2] - box[0]) * max(0, box[3] - box[1])
    overlap = intersection(box, bounds)
    binding = (candidate.get("layout") or {}).get("binding") or {}
    # Exact ID plus compatible geometry is stronger than shared display text.
    same_binding = bool(target.get("id") and binding.get("id") == target["id"]
                        and binding.get("bounds") == bounds)
    associated = overlap > 0 and (same_binding or (area > 0 and overlap / area >= 0.5))
    edge_hit = None
    if edge:
        band = list(bounds)
        if edge == "left": band[0], band[2] = bounds[0] - tolerance, bounds[0] + tolerance
        elif edge == "right": band[0], band[2] = bounds[2] - tolerance, bounds[2] + tolerance
        elif edge == "top": band[1], band[3] = bounds[1] - tolerance, bounds[1] + tolerance
        elif edge == "bottom": band[1], band[3] = bounds[3] - tolerance, bounds[3] + tolerance
        else: raise ValueError("Unknown loss edge")
        # A whole-component box cannot localize a particular missing edge.
        axis = 0 if edge in {"left", "right"} else 1
        localized = box[axis + 2] - box[axis] <= max(2 * tolerance, (bounds[axis + 2] - bounds[axis]) * 0.5)
        edge_hit = associated and localized and intersection(box, band) > 0
    return {"associated": associated, "edge_hit": edge_hit, "binding_matches": same_binding,
            "candidate_coverage": overlap / area if area else 0}


def evaluate_row(row, edge=None, tolerance=8):
    expected = truth(row)
    candidates = [{**c, **match_candidate(c, row["target"], edge, tolerance)} for c in row["candidates"]]
    associated = [c for c in candidates if c["associated"]]
    localized = [c for c in associated if c["edge_hit"]] if edge else associated
    final = [c for c in localized if c["retained"]]
    # Negative targets have no defect edge to localize: any associated retained
    # complaint is a target false alarm, including the wrong side of that target.
    predicted = bool(final if expected is True else [c for c in associated if c["retained"]])
    usable = row.get("target_stable_around_png", False) and row.get("agent_success") is True
    outcome = ("unscored" if expected is None or not usable or (expected and not edge)
               else ("TP" if predicted else "FN") if expected else ("FP" if predicted else "TN"))
    failure = "detector_error_or_unverified" if row.get("agent_success") is not True else None
    if outcome == "FN":
        failure = ("no_candidate" if not candidates else "other_target" if not associated else
                   "wrong_edge" if not localized else
                   "layout_suppression" if all((c.get("layout") or {}).get("verdict") == "ok" for c in localized)
                   else "slide_or_final_suppression")
    elif outcome == "FP":
        failure = "recoverable_flagged" if row.get("recovery_status") == "recovered" else "complete_content_flagged"
    return {**row, "expected_edge": edge, "edge_tolerance_px": tolerance,
            "candidates": candidates, "expected_final_defect": expected,
            "candidate_target_hit": bool(associated), "candidate_edge_hit": bool(localized) if edge else None,
            "outcome": outcome, "failure_stage": failure}


def summarize(rows):
    def metrics(group):
        counts = Counter(r["outcome"] for r in group)
        tp, fp, fn, tn = (counts[k] for k in ("TP", "FP", "FN", "TN"))
        return {"observations": len(group), "counts": dict(counts),
                "precision": tp / (tp + fp) if tp + fp else None,
                "recall": tp / (tp + fn) if tp + fn else None,
                "false_positive_rate": fp / (fp + tn) if fp + tn else None,
                "failure_stages": dict(Counter(r["failure_stage"] for r in group if r["failure_stage"]))}
    return {"all_reviewed_targets": metrics(rows),
            "text_scope": metrics([r for r in rows if r["component"] in {"Text", "Button"}]),
            "nontext_controls": metrics([r for r in rows if r["component"] not in {"Text", "Button"}]),
            "by_component_axis": {f"{kind}/{axis}": metrics([r for r in rows if r["component"] == kind and r["axis"] == axis])
                                  for kind, axis in sorted({(r["component"], r["axis"]) for r in rows})}}


def evaluate_live(summary, destination):
    rows = []
    for row in read(summary)["target_observations"]:
        plan_file = Path(row["evidence"]).parent / "run/plan.json"
        plan = read(plan_file) if plan_file.exists() else {}
        edge = plan.get("geometry", {}).get("edge")
        # One percent of the short display side, minimum 4px. Record sensitivity
        # separately so this engineering tolerance is not a hidden scoring knob.
        result = read(Path(row["evidence"]) / "result.json")["screens"][0]
        size = result["snapshot"]["coordSpace"]
        tolerance = max(4, min(size["width"], size["height"]) * .01)
        rows.append(evaluate_row(row, edge, tolerance))
    report = {"protocol": "target association plus planned-edge localization; review labels retained",
              "limitations": "Geometric edge proxy, no manual glyph boxes; predictions outside reviewed targets are not scored. Image/SymbolGlyph separate from original text prompt.",
              "metrics": summarize(rows), "observations": rows,
              "tolerance_sensitivity": {str(scale): summarize([
                  evaluate_row(row, row["expected_edge"], row["edge_tolerance_px"] * scale) for row in rows])
                  for scale in (.5, 2)}}
    save(destination, report)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("summary", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    report = evaluate_live(args.summary, args.destination)
    print(report["metrics"])
