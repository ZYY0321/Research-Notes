"""Bounded recovery evidence for scroll members of an ordinary combined package."""

from pathlib import Path
from truncator.planning.composition import capture_members
from truncator.imaging.content_transition import measure_transition
from truncator.execution.device.recovery_gestures import plan_swipe
from truncator.common.storage import digest, read, save


def verify_scroll_members(profile, run, initial, device, recipe, *, max_swipes=2):
    # Keep device execution out of offline report imports.
    from truncator.execution.device.runtime import capture

    if isinstance(max_swipes, bool) or not isinstance(max_swipes, int) or not 1 <= max_swipes <= 4:
        raise ValueError("Recovery swipe budget must be an integer from 1 to 4")
    run, initial = Path(run), Path(initial)
    plan = read(run / "plan.json")
    members = [p for p in capture_members(plan, recipe) if p["operator"] == "scroll-recovery"]
    if not members:
        return None
    output = initial / "scroll-recovery.json"
    result = {"plan_id": plan["id"], "budget_per_target": max_swipes, "members": [],
              "review": "pending", "policy": "collect recovery evidence; no automatic defect label"}
    for member in members:
        geometry = member["geometry"]
        selector = geometry["mutated_selector"]
        viewport_id = member["parameters"].get("viewport_id")
        axis = "horizontal" if member["parameters"]["scroll_direction"] == "Horizontal" else "vertical"
        row = {"mutation_id": member["id"], "axis": axis, "actions": [], "status": "pending"}
        result["members"].append(row)
        save(output, result)
        try:
            if not viewport_id:
                raise ValueError("Scroll plan has no viewport tracking ID")
            viewport = {"id": viewport_id, "type": "Scroll"}
            # Re-enter the route, even for the first target. A resumed campaign may
            # reuse a static capture while the live device is on another page.
            first = current = capture(profile, run, device, recipe, run.parent)
            row["initial"] = str(first)
            previous_delta = 0
            for step in range(max_swipes):
                gesture = plan_swipe(read(current / "tree-before.json"), selector, viewport, axis)
                if gesture["status"] != "planned":
                    row.update(status="unavailable", reason=gesture["reason"], gesture=gesture)
                    break
                action = {"kind": "swipe", "selector": viewport,
                          "from": gesture["from"], "to": gesture["to"], "wait": 1}
                continued_recipe = {"page_id": recipe["page_id"], "actions": [action],
                                    "checks": [{"selector": selector}], "settle_seconds": 2}
                after = capture(profile, run, device, continued_recipe, run.parent, continue_from=current)
                measurement = measure_transition(first, after, selector=selector,
                    viewport_selector=viewport, axis=axis, geometry=geometry)
                row["actions"].append({"step": step + 1, "before": str(current), "after": str(after),
                    "gesture": gesture, "measurement": measurement,
                    "capture_sha256": digest((after / "capture.json").read_bytes()),
                    "replay_sha256": digest((after / "replay.json").read_bytes())})
                current = after
                row["status"] = "measured"
                # Content coverage, not the full blank component extent, is the
                # useful stopping condition. Preserve the observation for review.
                if measurement.get("initial_and_current_cover_baseline_ink") or measurement.get("initial_and_current_cover_component"):
                    row["stop_reason"] = "coverage_observed"
                    break
                delta = measurement.get("delta_along_axis_px")
                if delta is not None and delta >= previous_delta - 2:
                    row["stop_reason"] = "no_forward_progress"
                    break
                if delta is not None:
                    previous_delta = delta
                save(output, result)
            if row["status"] == "measured":
                row.setdefault("stop_reason", "swipe_budget_exhausted")
        except (ValueError, OSError, RuntimeError, KeyError) as error:
            row.update(status="unavailable", reason=str(error))
        save(output, result)
    return output
