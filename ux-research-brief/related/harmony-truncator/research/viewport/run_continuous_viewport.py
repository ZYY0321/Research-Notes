"""Capture responsive and frozen layouts across folds in one process per HAP."""

import argparse
from pathlib import Path
from truncator.common.storage import read, save
from truncator.execution.device.runtime import capture
from truncator.source.binding import active_records, select_record
from .run_frozen_viewport import set_posture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--mutated", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    selector = {"id": "responsive-target", "type": "Text"}
    observe = {
        "checks": [{"field": "id", "equals": selector["id"]}],
        "targets": [{"selector": selector}],
    }
    initial = {
        **observe,
        "reset_app_data": True,
        "settle_seconds": 3,
        "actions": [{"field": "id", "equals": "choose-responsive", "wait": 2}],
    }
    results = []
    profile = read(Path(args.baseline) / "profile.json")
    try:
        for label, run in (("responsive", args.baseline), ("frozen", args.mutated)):
            run = Path(run)
            profile = read(run / "profile.json")
            previous = None
            for posture, width, stage in (
                ("open", 2584, "wide"),
                ("close", 1264, "narrow"),
                ("open", 2584, "wide-return"),
            ):
                context = set_posture(profile, output, posture, width)
                folder = capture(
                    profile,
                    run,
                    "127.0.0.1:5555",
                    initial if previous is None else observe,
                    output,
                    continue_from=previous,
                )
                record = read(folder / "capture.json")
                if record["session"]["status"] != "verified":
                    raise RuntimeError(
                        "Capture did not identify its application process"
                    )
                node = select_record(
                    active_records(read(folder / "tree-before.json")), selector
                )
                results.append(
                    {
                        "variant": label,
                        "stage": stage,
                        "capture": str(folder),
                        "display_context": context,
                        "session": record["session"],
                        "hap_sha256": record["hap_sha256"],
                        "target": node["attributes"],
                        "continued_from": record.get("continued_from"),
                    }
                )
                save(output / "results.json", results)
                print(label, stage, str(folder), flush=True)
                previous = folder
    finally:
        set_posture(profile, output, "open", 2584)


if __name__ == "__main__":
    main()
