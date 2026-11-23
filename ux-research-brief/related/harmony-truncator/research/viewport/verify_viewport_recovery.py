"""Recompute the cached viewport's bounded swipe trial from truncator.common.capture_files import capture_image
from raw captures."""

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from truncator.common.storage import read, save, digest
from truncator.source.binding import active_records, select_record
from research.controls.evidence import evidence_identity, validate_interaction
from truncator.imaging.content_transition import measure_transition
from truncator.imaging.content_identity import compare_visible
from truncator.imaging.content_coverage import visible_regions, foreground_coverage
from truncator.execution.device.replay import action_arguments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root, output = Path(args.runs), Path(args.out)
    result = read(root / "results.json")
    if not result["complete"]:
        raise ValueError("Recovery trial is incomplete")
    if digest(Path(result["plan"]).read_bytes()) != result["plan_sha256"]:
        raise ValueError("Recovery trial plan changed")
    plan = read(result["plan"])
    geometry = plan["geometry"]
    selector = geometry["mutated_selector"]
    baseline = Path(geometry["baseline_capture"])
    if digest((capture_image(baseline)).read_bytes()) != geometry["baseline_image_sha256"]:
        raise ValueError("Planned baseline changed")
    for key in ("wide", "initial"):
        if evidence_identity(result[key]["capture"]) != result[key]:
            raise ValueError("Initial capture changed")
    validate_interaction({**result["initial"], "before": result["wide"]})
    stages = ["horizontal-forward", "horizontal-return", "vertical-forward",
              "horizontal-after-vertical", "vertical-return"]
    if [a["stage"] for a in result["actions"]] != stages:
        raise ValueError("Recovery trial stages differ")
    rows, observations = [], []
    previous = result["initial"]
    for action in result["actions"]:
        if action["before"] != previous:
            raise ValueError("Action chain skipped a preceding capture")
        validate_interaction(action)
        folder = Path(action["capture"])
        for key, origin in (("measurement", result["initial"]["capture"]),
                            ("action_measurement", previous["capture"])):
            measured = measure_transition(origin, folder, selector=selector,
                viewport_selector=result["viewport_selector"], axis="horizontal", geometry=geometry)
            if measured != action[key]:
                raise ValueError("Stored movement/coverage differs from recomputed observation")
        measurement = action["measurement"]
        if not measurement["same_content"] or not measurement["same_extent"]:
            raise ValueError("Content or component extent changed")
        current = measurement["observations"][-1]
        before = select_record(active_records(read(folder / "tree-before.json")), selector)
        after = select_record(active_records(read(folder / "tree-after.json")), selector)
        if before["attributes"] != after["attributes"]:
            raise ValueError("Target changed across screenshot capture")
        replay = read(folder / "replay.json")
        if digest((folder / "replay.json").read_bytes()) != action["replay_sha256"]:
            raise ValueError("Replay log changed")
        if (len(replay) != 1 or replay[0]["action"] != action["action"]
                or replay[0]["arguments"] != action["dispatched_arguments"]
                or action_arguments(action["action"], replay[0]["matches"][0]["bounds"])
                != action["dispatched_arguments"]):
            raise ValueError("Dispatched swipe differs from its bound viewport action")
        identity = compare_visible(capture_image(baseline), capture_image(folder),
                                   geometry["target_bounds_px"], current["original"], current["visible"])
        if identity["status"] != "matched":
            raise ValueError("Visible content pixels differ from baseline")
        rows.append({"stage": action["stage"], "capture": action["capture"],
                     "delta_xy_px": action["action_measurement"]["relative_delta_xy_px"],
                     "coverage": measurement.get("foreground_coverage", {
                         "status": "unknown", "reason": "baseline_foreground_not_measurable"}),
                     "pixel_identity": identity,
                     "observation": current})
        observations.extend(measurement["observations"])
        previous = evidence_identity(folder)
    coverage = foreground_coverage(capture_image(baseline), geometry["target_bounds_px"],
                                   visible_regions(observations))
    if coverage != result["combined_foreground_coverage"]:
        raise ValueError("Combined coverage differs")
    output.mkdir(parents=True, exist_ok=True)
    save(output / "verification.json", {"source_results": str((root / "results.json").resolve()),
         "source_results_sha256": digest((root / "results.json").read_bytes()), "actions": rows,
         "combined_foreground_coverage": coverage, "same_process_and_package": True,
         "exact_swipe_arguments_verified": True, "visual_review": "pending",
         "scope": "Five recorded gestures inside the same narrow viewport; no claim about all possible interactions."})
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
    canvas = Image.new("RGB", (1100, 190 * (len(rows) + 1)), "#EEEEEE")
    frames = [{"stage": "initial narrow", "capture": result["initial"]["capture"],
               "observation": result["actions"][0]["measurement"]["observations"][0]}] + rows
    for index, row in enumerate(frames):
        box = row["observation"]["original"]
        ImageDraw.Draw(canvas).text((10, index * 190 + 10), row["stage"], font=font, fill="black")
        with Image.open(capture_image(Path(row["capture"]))) as image:
            crop = image.crop((max(0, box[0] - 10), max(0, box[1] - 10),
                               min(image.width, box[2] + 10), min(image.height, box[3] + 10)))
            canvas.paste(crop, (10, index * 190 + 50))
    canvas.save(output / "target-comparison.png")
    print("Verified gestures:", len(rows), "foreground coverage:", coverage["status"],
          "remaining foreground pixels:", coverage.get("uncovered_pixels", "unmeasured"))


if __name__ == "__main__":
    main()
