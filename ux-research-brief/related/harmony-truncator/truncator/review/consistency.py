"""Pixel checks for exported-boundary disagreements, with explicit prerequisites."""

from PIL import Image
from truncator.imaging.visual import foreground, pixel_values


def inspect_exported_strips(
    baseline_image, current_image, baseline_box, original, visible
):
    sizes = [(box[2] - box[0], box[3] - box[1]) for box in (baseline_box, original)]
    if any(abs(a - b) > 1 for a, b in zip(*sizes)):
        return {
            "status": "unavailable",
            "reason": "target_extent_changed",
            "strips": [],
        }
    strips = {
        "left": [original[0], original[1], visible[0], original[3]],
        "right": [visible[2], original[1], original[2], original[3]],
        "top": [original[0], original[1], original[2], visible[1]],
        "bottom": [original[0], visible[3], original[2], original[3]],
    }
    result = []
    with Image.open(baseline_image) as before, Image.open(current_image) as after:
        before, after = before.convert("RGB"), after.convert("RGB")
        for edge, box in strips.items():
            box = [round(x) for x in box]
            if box[2] <= box[0] or box[3] <= box[1]:
                continue
            if (
                box[0] < 0
                or box[1] < 0
                or box[2] > after.width
                or box[3] > after.height
            ):
                result.append({"edge": edge, "status": "outside_screenshot"})
                continue
            dx, dy = baseline_box[0] - original[0], baseline_box[1] - original[1]
            reference = [
                round(box[0] + dx),
                round(box[1] + dy),
                round(box[2] + dx),
                round(box[3] + dy),
            ]
            measured = foreground(baseline_image, reference)
            row = {
                "edge": edge,
                "bounds_px": box,
                "baseline_bounds_px": reference,
                "baseline_foreground": measured,
                "status": measured["status"],
            }
            if measured["status"] == "measured":
                background = measured["background_rgb"]
                a, b = before.crop(reference), after.crop(box)
                if a.size != b.size:
                    row["status"] = "rounding_size_mismatch"
                else:
                    ink = [
                        (p, q)
                        for p, q in zip(pixel_values(a), pixel_values(b))
                        if max(abs(x - y) for x, y in zip(p, background))
                        > measured["tolerance"]
                    ]
                    matching = sum(
                        max(abs(x - y) for x, y in zip(p, q)) <= 25 for p, q in ink
                    )
                    row.update(
                        ink_pixels=len(ink),
                        matching_ink_fraction=matching / max(1, len(ink)),
                        ink_visible_outside_exported_bounds=len(ink) >= 10
                        and matching / len(ink) >= 0.8,
                    )
            result.append(row)
    return {"status": "measured", "strips": result, "visual_review": "pending"}
