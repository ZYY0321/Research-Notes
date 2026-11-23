"""Audit a saved continuous fold sequence and compare its narrow tree to Dianping."""

import argparse
import json
from truncator.common.capture_files import capture_image
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from truncator.common.storage import read, save, digest
from truncator.imaging.geometry import rectangle
from research.production_evidence.comparison import inspect_target, compare_targets
from truncator.source.binding import active_records, select_record, bind_candidates
from truncator.source.project import scan
from truncator.planning.calibration import plan_for_target
from truncator.mutation.mutations import mutation_patches


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--cold-start-capture")
    args = parser.parse_args()
    root, output = Path(args.runs), Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    rows = read(root / "results.json")
    expected = [
        (variant, stage)
        for variant in ("responsive", "frozen")
        for stage in ("wide", "narrow", "wide-return")
    ]
    assert [(row["variant"], row["stage"]) for row in rows] == expected
    verified = []
    for offset in (0, 3):
        group = rows[offset : offset + 3]
        assert len({row["hap_sha256"] for row in group}) == 1
        assert len({json.dumps(row["session"], sort_keys=True) for row in group}) == 1
        for index, row in enumerate(group):
            folder = Path(row["capture"])
            record = read(folder / "capture.json")
            assert record["screenshot_sha256"] == digest(
                (capture_image(folder)).read_bytes()
            )
            assert record["session"] == row["session"]
            assert record["hap_sha256"] == row["hap_sha256"]
            assert record["session"]["status"] == "verified"
            before = select_record(
                active_records(read(folder / "tree-before.json")),
                {"id": "responsive-target"},
            )
            after = select_record(
                active_records(read(folder / "tree-after.json")),
                {"id": "responsive-target"},
            )
            assert before["attributes"] == after["attributes"] == row["target"]
            if index:
                previous = Path(group[index - 1]["capture"])
                assert record["continued_from"]["capture"] == str(previous)
                assert record["continued_from"]["capture_sha256"] == digest(
                    (previous / "capture.json").read_bytes()
                )
                events = [
                    json.loads(line)
                    for line in (folder.parent / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                ]
                commands = [
                    event["args"]
                    for event in events
                    if event.get("attempt") == folder.name and event.get("args")
                ]
                assert commands and not any(
                    set(command) & {"install", "start", "force-stop", "clean"}
                    for command in commands
                )
            original, visible = rectangle(row["target"]["origBounds"]), rectangle(
                row["target"]["bounds"]
            )
            loss = original[2] - visible[2]
            if row["variant"] == "frozen" and row["stage"] == "narrow":
                assert loss > 0, "Narrow cached viewport did not produce an exported right-edge loss"
            else:
                assert loss == 0, "A responsive or wide control unexpectedly lost its right edge"
            verified.append(
                {
                    **row,
                    "right_bound_loss_px": loss,
                    "sha256": {
                        name: digest((folder / name).read_bytes())
                        for name in (
                            "capture.json",
                            "tree-before.json",
                            "tree-after.json",
                            capture_image(folder).name,
                        )
                    },
                }
            )
    project = Path(__file__).resolve().parents[2]
    reference = read(
        project / "artifacts/dianping-frozen-viewport-comparison-20261117.json"
    )["reference"]
    for kind in ("tree", "screenshot"):
        assert digest(Path(reference[kind]).read_bytes()) == reference[kind + "_sha256"]
    narrow = Path(rows[4]["capture"])
    injected = inspect_target(
        narrow / "tree-before.json",
        capture_image(narrow),
        {"id": "responsive-target", "type": "Text"},
    )
    save(output / "commercial-comparison.json", compare_targets(reference, injected))
    baseline = Path(rows[0]["capture"])
    profile = read(baseline.parent / "profile.json")
    catalog = scan(profile)
    binding = next(
        row
        for row in bind_candidates(catalog, read(baseline / "tree-before.json"))[
            "bindings"
        ]
        if row["selector"].get("id") == "responsive-target"
    )
    previous_plan = read(narrow.parent / "plan.json")
    plan = plan_for_target(catalog, baseline, binding, previous_plan["operator"])[0]
    assert mutation_patches(plan) == mutation_patches(previous_plan)
    save(output / "current-plan.json", plan)
    cold = None
    if args.cold_start_capture:
        folder = Path(args.cold_start_capture)
        record = read(folder / "capture.json")
        node = select_record(
            active_records(read(folder / "tree-before.json")),
            {"id": "responsive-target"},
        )
        after = select_record(
            active_records(read(folder / "tree-after.json")),
            {"id": "responsive-target"},
        )
        assert node["attributes"] == after["attributes"]
        assert record["hap_sha256"] == rows[4]["hap_sha256"]
        assert (
            record["session"]["status"] == "verified"
            and record["session"] != rows[4]["session"]
        )
        assert (
            node["attributes"]["bounds"]
            == node["attributes"]["origBounds"]
            == rows[1]["target"]["bounds"]
        )
        assert record["screenshot_sha256"] == digest(
            (capture_image(folder)).read_bytes()
        )
        cold = {
            "capture": str(folder),
            "target": node["attributes"],
            "session": record["session"],
            "sha256": {
                name: digest((folder / name).read_bytes())
                for name in (
                    "capture.json",
                    "tree-before.json",
                    "tree-after.json",
                    capture_image(folder).name,
                )
            },
        }
    save(
        output / "verification.json",
        {
            "sampling": "one_live_process_per_variant",
            "operator": previous_plan["operator"],
            "cold_narrow_start": cold,
            "states": verified,
            "new_plan_patch_equivalent": True,
            "visual_review": "pending",
            "commercial_recovery": "historically_not_collected",
        },
    )
    canvas = Image.new("RGB", (2000, 840 if cold else 630), "#EEEEEE")
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 25)
    for row in rows:
        column = 0 if row["variant"] == "responsive" else 1
        line = ("wide", "narrow", "wide-return").index(row["stage"])
        x, y = column * 1000, line * 210
        ImageDraw.Draw(canvas).text(
            (x + 10, y + 10),
            row["variant"] + " / " + row["stage"],
            font=font,
            fill="black",
        )
        box = rectangle(row["target"]["origBounds"])
        with Image.open(capture_image(Path(row["capture"]))) as screenshot:
            left = max(0, box[0] - 15)
            crop = screenshot.crop(
                (left, box[1] - 10, min(screenshot.width, left + 980), box[3] + 10)
            )
            canvas.paste(crop, (x + 10, y + 60))
    canvas.save(output / "target-comparison.png")
    if cold:
        ImageDraw.Draw(canvas).text(
            (1010, 640), "same cached HAP / cold narrow start", font=font, fill="black"
        )
        box = rectangle(cold["target"]["origBounds"])
        with Image.open(capture_image(Path(cold["capture"]))) as screenshot:
            canvas.paste(
                screenshot.crop((box[0] - 10, box[1] - 10, box[2] + 10, box[3] + 10)),
                (1010, 690),
            )
        canvas.save(output / "target-comparison.png")
    print(output / "verification.json")


if __name__ == "__main__":
    main()
