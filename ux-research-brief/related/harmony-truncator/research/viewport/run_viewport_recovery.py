"""Probe horizontal loss in a cached vertical viewport in one live process."""

import argparse
from truncator.common.capture_files import capture_image
from pathlib import Path

from truncator.common.storage import read, save, digest
from truncator.execution.device.runtime import capture
from truncator.planning.composition import validate_plan
from research.controls.evidence import directional_swipe, evidence_identity, validate_interaction
from truncator.imaging.content_transition import measure_transition
from truncator.imaging.content_coverage import visible_regions, foreground_coverage
from .run_frozen_viewport import set_posture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root, output = Path(args.experiment), Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=False)
    run = Path(read(root / "prepared-experiment.json")["mutated"])
    plan, profile = read(run / "plan.json"), read(run / "profile.json")
    validate_plan(plan)
    geometry = plan["geometry"]
    if digest((capture_image(Path(geometry["baseline_capture"]))).read_bytes()) != geometry["baseline_image_sha256"]:
        raise ValueError("Planned baseline changed")
    selector = geometry["mutated_selector"]
    viewport = {"id": "responsive-viewport"}
    observe = {"checks": [{"field": "id", "equals": selector["id"]}],
               "targets": [{"selector": selector}]}
    initial_recipe = {**observe, "reset_app_data": True, "settle_seconds": 3,
                      "actions": [{"field": "id", "equals": "choose-responsive", "wait": 2}]}
    actions = [
        ("horizontal-forward", directional_swipe(viewport, "horizontal")),
        ("horizontal-return", directional_swipe(viewport, "horizontal", reverse=True)),
        ("vertical-forward", {**directional_swipe(viewport, "vertical"),
                              "from": [0.5, 0.55], "to": [0.5, 0.50], "speed": 200}),
        ("horizontal-after-vertical", directional_swipe(viewport, "horizontal")),
        ("vertical-return", {**directional_swipe(viewport, "vertical", reverse=True),
                             "from": [0.5, 0.50], "to": [0.5, 0.55], "speed": 200}),
    ]
    result = {"plan": str(run / "plan.json"), "plan_sha256": digest((run / "plan.json").read_bytes()),
              "viewport_selector": viewport, "loss_axis": "horizontal", "actions": [], "complete": False}
    save(output / "results.json", result)
    try:
        set_posture(profile, output, "open", 2584)
        wide = capture(profile, run, "127.0.0.1:5555", initial_recipe, output)
        result["wide"] = evidence_identity(wide)
        set_posture(profile, output, "close", 1264)
        initial = capture(profile, run, "127.0.0.1:5555", observe, output, continue_from=wide)
        result["initial"] = evidence_identity(initial)
        validate_interaction({**result["initial"], "before": result["wide"]})
        save(output / "results.json", result)
        previous = initial
        observations = []
        for stage, action in actions:
            current = capture(profile, run, "127.0.0.1:5555", {**observe, "actions": [action]},
                              output, continue_from=previous)
            row = {"stage": stage, "action": action, "before": evidence_identity(previous),
                   **evidence_identity(current)}
            validate_interaction(row)
            for key, origin in (("measurement", initial), ("action_measurement", previous)):
                row[key] = measure_transition(origin, current, selector=selector,
                    viewport_selector=viewport, axis="horizontal", geometry=geometry)
            replay = read(current / "replay.json")
            if len(replay) != 1 or replay[0]["status"] not in {"dispatched", "checkpoint_passed"}:
                raise ValueError("Expected one successfully dispatched viewport action")
            row["dispatched_arguments"] = replay[0]["arguments"]
            row["replay_sha256"] = digest((current / "replay.json").read_bytes())
            observations.extend(row["measurement"]["observations"])
            result["actions"].append(row)
            save(output / "results.json", result)
            print(stage, row["action_measurement"]["relative_delta_xy_px"], flush=True)
            previous = current
        result["combined_foreground_coverage"] = foreground_coverage(
            capture_image(Path(geometry["baseline_capture"])),
            geometry["target_bounds_px"], visible_regions(observations))
        result["complete"] = True
        save(output / "results.json", result)
    finally:
        set_posture(profile, output, "open", 2584)


if __name__ == "__main__":
    main()
