"""Structured diagnostics from captured evidence, independent of review decisions."""

from truncator.common.capture_files import capture_image

from pathlib import Path
from truncator.common.storage import read, save
from truncator.imaging.geometry import rectangle
from truncator.imaging.visual import foreground, severity_policy
from truncator.review.consistency import inspect_exported_strips


def diagnose(plan, capture_dir, allowed_severity=("partial", "complete", "unresolved")):
    folder = Path(capture_dir)
    geometry = plan.get("geometry")
    if not geometry:
        return None
    observation = read(folder / "geometry-observation.json")
    result = {"flags": [], "severity": "unresolved", "visual_review": "pending"}
    changed_viewport = observation.get("image_comparison") == "screen_size_changed"
    window_experiment = plan["operator"] in {"freeze-viewport-width", "cache-viewport-width"}
    if changed_viewport and not window_experiment:
        # Measured vp sizes and preserved slots belong to the planning viewport.
        # A different window may introduce an unintended width/layout change.
        result["flags"].append("baseline_viewport_changed")
        result["required_action"] = "replan_for_current_viewport"
    if observation.get("status") != "measured":
        result["flags"].append("measurement_failed")
    elif (
        plan["operator"].startswith("sibling-")
        and observation.get("intersection_area_px") == 0
    ):
        result["flags"].append("intended_target_not_intersected")
    elif plan["operator"] in {
        "fixed-parent-clip",
        "translate-clip",
        "ancestor-translate-clip",
        "child-overflow-clip",
        "window-edge-clip",
    } and not any(observation["clipped_edges_px"].values()):
        result["flags"].append("geometry_not_triggered")
    if plan["operator"] == "window-edge-clip" and observation.get("window_boundary_match") is False:
        result["flags"].append("window_boundary_not_reached")
    if plan["operator"] == "viewport-width-mismatch" and observation.get("viewport_width_mismatch_observed") is False:
        result["flags"].append("viewport_width_mismatch_not_observed")
    attrs = observation.get("target", {})
    losses = observation.get("clipped_edges_px", {})
    if any(losses.values()) and not changed_viewport:
        baseline_image = capture_image(geometry["baseline_capture"])
        consistency = inspect_exported_strips(baseline_image, capture_image(folder),
                                               geometry["target_bounds_px"], rectangle(attrs["origBounds"]),
                                               rectangle(attrs["bounds"]))
        result["exported_strip_checks"] = consistency
        if any(row.get("ink_visible_outside_exported_bounds") for row in consistency["strips"]):
            result["flags"].append("ink_visible_outside_exported_bounds")
        if geometry.get("edge") and not losses.get(geometry["edge"], 0):
            result["flags"].append("exported_loss_direction_differs_from_plan")
    difference = observation.get("baseline_target_roi_mean_absolute_pixel_difference")
    if attrs.get("type") == "Text" and not changed_viewport:
        before = foreground(
            capture_image(geometry["baseline_capture"]),
            geometry["target_bounds_px"],
        )
        after = foreground(capture_image(folder), rectangle(attrs["bounds"]))
        result.update(baseline_foreground=before, captured_foreground=after)
        if before["status"] == "measured" and after["status"] in {"measured", "empty"}:
            same_background = (
                max(
                    abs(a - b)
                    for a, b in zip(before["background_rgb"], after["background_rgb"])
                )
                <= 20
            )
            if same_background:
                retained = after["foreground_pixels"] / before["foreground_pixels"]
                result["foreground_pixel_ratio"] = retained
                if after["foreground_pixels"] == 0:
                    result["severity"] = "complete"
                elif retained < 0.95:
                    result["severity"] = "partial"
                    if observation.get("bounds_equal"):
                        result["flags"].append("foreground_loss_with_equal_bounds")
                else:
                    result["flags"].append("no_foreground_loss_evidence")
                    if any(losses.values()):
                        result["flags"].append("exported_bounds_shrink_without_foreground_loss")
        if plan["operator"] == "overlay-occlusion" and before["status"] == "measured":
            actual = before["background_rgb"]
            color = plan["parameters"]["color"]
            expected = [int(color[i : i + 2], 16) for i in (1, 3, 5)]
            result["overlay_background_channel_difference"] = max(
                abs(a - b) for a, b in zip(actual, expected)
            )
    if plan["operator"] == "freeze-viewport-width" and not observation.get("window_narrowed"):
        result["flags"].append("narrow_window_trigger_pending")
    if difference is not None and difference < 2 and result["severity"] == "unresolved":
        result["flags"].append("target_roi_almost_unchanged")
        result["unchanged_roi_threshold"] = 2
    result["severity_policy"] = severity_policy(result["severity"], allowed_severity)
    save(folder / "diagnostics.json", result)
    return result


def assess_capture(capture_dir):
    """Translate stored measurements into a candidate-selection action."""
    capture_dir = Path(capture_dir)
    assessment = None
    diagnostic_file = capture_dir / "diagnostics.json"
    if diagnostic_file.exists():
        diagnostics = read(diagnostic_file)
        retry_flags = {
            "geometry_not_triggered",
            "intended_target_not_intersected",
            "target_roi_almost_unchanged",
            "no_foreground_loss_evidence",
            "measurement_failed",
        }
        retry = bool(
            retry_flags.intersection(diagnostics.get("flags", []))
        ) or not diagnostics.get("severity_policy", {}).get("eligible", True)
        assessment = {
            "capture": str(capture_dir),
            "next_action": ("replan_for_current_viewport" if "baseline_viewport_changed" in diagnostics.get("flags", [])
                            else "try_other_candidate" if retry else "review_candidate"),
            "diagnostics": diagnostics,
        }
        quality_file = capture_dir / "image-quality.json"
        if quality_file.exists():
            quality = read(quality_file)
            assessment["image_quality"] = quality
            if not quality.get("passed", True) and assessment["next_action"] != "replan_for_current_viewport":
                assessment["next_action"] = "inspect_non_target_changes"
    return assessment


def select_candidate(report):
    """Rank historical diagnostics for offline analysis of saved experiments."""
    ranking = {"partial": 0, "complete": 1, "unresolved": 2}
    candidates = []
    for row in report:
        assessment = row.get("assessment")
        if (
            row["status"] != "captured"
            or not assessment
            or assessment["next_action"] != "review_candidate"
        ):
            continue
        diagnostic = assessment["diagnostics"]
        if diagnostic.get("status") == "unavailable":
            continue
        candidates.append(
            {
                "run": row["run"],
                "capture": assessment["capture"],
                "severity": diagnostic.get("severity", "unresolved"),
            }
        )
    candidates.sort(key=lambda candidate: ranking[candidate["severity"]])
    return {
        "preference": list(ranking),
        "selected": candidates[0] if candidates else None,
        "candidates": candidates,
        "decision": "review_required" if candidates else "no_measured_candidate",
    }
