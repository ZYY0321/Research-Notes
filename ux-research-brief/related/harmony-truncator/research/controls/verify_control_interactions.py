"""Replay identical swipes against the paired parent and scroll constructions."""

import copy
from pathlib import Path

from truncator.source.binding import active_records, select_record
from truncator.imaging.geometry import rectangle
from truncator.execution.device.runtime import capture
from truncator.common.storage import read, save


def main():
    project = Path(__file__).resolve().parents[2]
    results = read(project / "artifacts" / "service-control-results-20261117.json")
    output = project / "artifacts" / "service-control-interactions-20261117.json"
    evidence = []
    for result in results:
        run = Path(result["run"])
        plan = read(run / "plan.json")
        if plan["operator"] not in {"scroll-recovery", "fixed-parent-clip"}:
            continue
        initial = Path(result["assessment"]["capture"])
        selector = plan["geometry"]["mutated_selector"]
        recipe = read(initial / "capture.json")["recipe"]
        before = select_record(active_records(read(initial / "tree-before.json")), selector)
        for name, end_x in (("middle", 0.65), ("tail", 0.15)):
            replay = copy.deepcopy(recipe)
            replay["actions"].append({"kind": "swipe", "selector": selector,
                                      "from": [0.85, 0.5], "to": [end_x, 0.5],
                                      "speed": 400, "wait": 3})
            try:
                directory = capture(read(run / "profile.json"), run, "127.0.0.1:5555",
                                    replay, run.parent)
            except (RuntimeError, ValueError) as error:
                evidence.append({"operator": plan["operator"], "stage": name,
                                 "status": "failed", "error": str(error), "run": str(run)})
                save(output, evidence)
                print(plan["operator"], name, str(error), flush=True)
                continue
            after = select_record(active_records(read(directory / "tree-before.json")), selector)
            original = rectangle(before["attributes"]["origBounds"])
            current = rectangle(after["attributes"]["origBounds"])
            evidence.append({"operator": plan["operator"], "plan_id": plan["id"],
                             "hap_sha256": read(run / "build.json")["hap_sha256"],
                             "stage": name, "initial": str(initial), "capture": str(directory),
                             "selector": selector, "original_bounds_before": original,
                             "original_bounds_after": current,
                             "delta_x_px": current[0] - original[0],
                             "text_before": before["attributes"].get("text"),
                             "text_after": after["attributes"].get("text"),
                             "visual_review": "pending"})
            save(output, evidence)
            print(plan["operator"], name, evidence[-1]["delta_x_px"], flush=True)


if __name__ == "__main__":
    main()
