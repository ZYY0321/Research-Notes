"""Verify continuous display-recovery controls and render target crops for review."""

import argparse
from truncator.common.capture_files import capture_image
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from research.controls.evidence import evidence_identity, validate_interaction
from truncator.imaging.geometry import rectangle
from truncator.source.binding import active_records, select_record
from truncator.common.storage import read, save


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--groups", nargs="+", help="Explicit group directories within runs")
    args = parser.parse_args()
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for group in sorted(Path(args.runs).glob("*/control-results.json")):
        if args.groups and group.parent.name not in args.groups:
            continue
        result = read(group)
        definition = read(group.parent / "control-group.json")
        assert result["complete"] and result["interaction_mode"] == "continuous_session"
        states = {state["state"]: state for state in result["states"]}
        assert set(states) == {"normal", "clipped", "scroll", "whitespace"}
        for state in states.values():
            identity = evidence_identity(state["capture"])
            assert all(identity[key] == state[key] for key in identity)
        expected = [
            ("clipped", "forward"),
            ("scroll", "forward"),
            ("scroll", "orthogonal"),
            ("scroll", "return"),
        ]
        assert [(a["state"], a["stage"]) for a in result["interactions"]] == expected
        previous = {name: state["capture"] for name, state in states.items()}
        frames = [
            ("normal", states["normal"]),
            ("clipped", states["clipped"]),
            ("scroll", states["scroll"]),
            ("whitespace", states["whitespace"]),
        ]
        for action in result["interactions"]:
            validate_interaction(action)
            assert action["before"]["capture"] == previous[action["state"]]
            previous[action["state"]] = action["capture"]
            record = read(Path(action["capture"]) / "capture.json")
            assert len(record["recipe"]["actions"]) == 1
            assert not record["recipe"].get("setup_actions")
            assert not record["recipe"].get("reset_app_data")
            frames.append((action["state"] + " / " + action["stage"], action))
        baseline = states["normal"]["capture"]
        node = select_record(
            active_records(read(Path(baseline) / "tree-before.json")),
            definition["selector"],
        )
        box = rectangle(node["attributes"]["origBounds"])
        crop_box = (max(0, box[0] - 10), max(0, box[1] - 10), box[2] + 10, box[3] + 10)
        scale = min(1, 880 / (crop_box[2] - crop_box[0]))
        height = round((crop_box[3] - crop_box[1]) * scale) + 55
        canvas = Image.new("RGB", (1800, height * 4), "#EEEEEE")
        draw = ImageDraw.Draw(canvas)
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
        for index, (label, frame) in enumerate(frames):
            x, y = index % 2 * 900, index // 2 * height
            draw.text((x + 10, y + 5), label, font=font, fill="black")
            with Image.open(capture_image(Path(frame["capture"]))) as image:
                crop = image.crop(crop_box)
                crop = crop.resize(
                    (round(crop.width * scale), round(crop.height * scale))
                )
                canvas.paste(crop, (x + 10, y + 40))
        canvas.save(output / (group.parent.name + ".png"))
        results.append(
            {
                "group": str(group.parent.resolve()),
                "axis": result["direction"]["axis"],
                "verified_states": len(states),
                "verified_actions": len(result["interactions"]),
                "interactions": [
                    {
                        "state": a["state"],
                        "stage": a["stage"],
                        "action_delta_xy_px": a["action_measurement"][
                            "relative_delta_xy_px"
                        ],
                        "initial_delta_xy_px": a["measurement"]["relative_delta_xy_px"],
                    }
                    for a in result["interactions"]
                ],
                "visual_review": "pending",
            }
        )
    if not results:
        raise ValueError("No completed control groups found")
    if args.groups and {Path(r["group"]).name for r in results} != set(args.groups):
        raise ValueError("Requested group is missing")
    save(output / "verification.json", results)
    print(output / "verification.json")


if __name__ == "__main__":
    main()
