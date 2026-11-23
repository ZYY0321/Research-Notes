"""Audit captured campaign targets and produce paired crops; never assign labels."""

import argparse
from truncator.common.capture_files import capture_image
from pathlib import Path

from PIL import Image, ImageDraw
from truncator.source.binding import active_records, select_record
from truncator.imaging.geometry import rectangle
from truncator.review.review_evidence import capture_hashes
from truncator.common.storage import read, save, digest


def verify(root, destination):
    root, destination = Path(root), Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    for application in read(root / "results.json"):
        app = Path(application["application"]).stem
        for page in application.get("pages", [application]):
            for case in page.get("cases", []):
                for run in case.get("runs", []):
                    if run.get("status") != "captured":
                        continue
                    plan = read(run["plan"])
                    capture = Path(run["assessment"]["capture"])
                    assert read(capture.parent / "plan.json") == plan
                    geometry = plan["geometry"]
                    baseline = Path(geometry["baseline_capture"])
                    for name, expected in (
                        (capture_image(baseline).name, geometry["baseline_image_sha256"]),
                        ("tree-before.json", geometry["baseline_tree_sha256"]),
                    ):
                        assert digest((baseline / name).read_bytes()) == expected
                    hashes = capture_hashes(capture)
                    record = read(capture / "capture.json")
                    assert hashes[capture_image(capture).name] == record["screenshot_sha256"]
                    hap_hash = digest(Path(run["application"]["hap"]).read_bytes())
                    assert hap_hash == record["hap_sha256"] == run["application"]["hap_sha256"]
                    attributes = [select_record(active_records(read(capture / name)),
                        geometry["mutated_selector"])["attributes"]
                        for name in ("tree-before.json", "tree-after.json")]
                    stable = all(attributes[0].get(k) == attributes[1].get(k)
                        for k in ("bounds", "origBounds", "text", "type", "id", "clip", "scrollable"))
                    assert stable, "Target changed across screenshot capture"
                    canvas = Image.new("RGB", (1600, 300), "#eeeeee")
                    draw = ImageDraw.Draw(canvas)
                    for x, source, box, label in (
                        (10, baseline, geometry["target_bounds_px"], "baseline"),
                        (810, capture, rectangle(attributes[0]["bounds"]), plan["operator"]),
                    ):
                        with Image.open(capture_image(source)) as image:
                            crop = image.convert("RGB").crop((max(0, round(box[0])-25),
                                max(0, round(box[1])-30), min(image.width, round(box[2])+25),
                                min(image.height, round(box[3])+40)))
                        crop.thumbnail((780, 240))
                        canvas.paste(crop, (x, 50))
                        draw.text((x, 12), label, fill="black", font_size=22)
                    preview = destination / (app + "-" + plan["id"] + ".png")
                    canvas.save(preview)
                    rows.append({"app": app, "operator": plan["operator"],
                        "capture": str(capture), "baseline": str(baseline), "plan": run["plan"],
                        "capture_files": hashes, "hap_sha256": hap_hash, "target": attributes[0],
                        "target_stable": stable, "preview": str(preview.resolve()),
                        "diagnostics": read(capture / "diagnostics.json"), "visual_review": "pending"})
    save(destination / "verification.json", rows)
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    print("Verified captures:", len(verify(args.runs, args.out)))
