"""Two-dimensional coverage in the unchanged component's local coordinates."""

import math
from PIL import Image, ImageDraw, ImageChops
from truncator.imaging.visual import foreground, pixel_values


def visible_regions(observations):
    regions = []
    for row in observations:
        original, visible, viewport = row["original"], row["visible"], row["viewport"]
        screen = row.get("screen_size")
        box = [
            max(original[0], visible[0], viewport[0], 0 if screen else original[0]),
            max(original[1], visible[1], viewport[1], 0 if screen else original[1]),
            min(
                original[2],
                visible[2],
                viewport[2],
                screen[0] if screen else original[2],
            ),
            min(
                original[3],
                visible[3],
                viewport[3],
                screen[1] if screen else original[3],
            ),
        ]
        if box[2] > box[0] and box[3] > box[1]:
            regions.append([box[i] - original[i % 2] for i in range(4)])
    return regions


def uncovered_area(target, regions):
    """Exact rectangle-union coverage; projections alone cannot establish it."""
    clipped = [
        [
            max(target[0], b[0]),
            max(target[1], b[1]),
            min(target[2], b[2]),
            min(target[3], b[3]),
        ]
        for b in regions
    ]
    clipped = [b for b in clipped if b[2] > b[0] and b[3] > b[1]]
    xs = sorted({target[0], target[2]} | {x for b in clipped for x in (b[0], b[2])})
    area = 0
    for left, right in zip(xs, xs[1:]):
        intervals = sorted(
            (b[1], b[3]) for b in clipped if b[0] <= left and b[2] >= right
        )
        end, height = target[1], 0
        for top, bottom in intervals:
            height += max(0, bottom - max(top, end))
            end = max(end, bottom)
        area += (right - left) * height
    return max(0, (target[2] - target[0]) * (target[3] - target[1]) - area)


def foreground_coverage(image_path, baseline_box, regions, *, measurement=None):
    measurement = (
        measurement if measurement is not None else foreground(image_path, baseline_box)
    )
    if measurement["status"] != "measured":
        return {"status": "unknown", "reason": measurement["status"]}
    with Image.open(image_path) as image:
        roi = image.convert("RGB").crop(tuple(round(v) for v in baseline_box))
    background = measurement["background_rgb"]
    mask = Image.new("L", roi.size)
    mask.putdata(
        [
            (
                255
                if max(abs(a - b) for a, b in zip(pixel, background))
                > measurement["tolerance"]
                else 0
            )
            for pixel in pixel_values(roi)
        ]
    )
    visible = Image.new("L", roi.size)
    draw = ImageDraw.Draw(visible)
    for box in regions:
        # A baseline pixel is covered when its centre lies in a half-open visible rectangle.
        left, top = math.ceil(box[0] - 0.5), math.ceil(box[1] - 0.5)
        right, bottom = math.ceil(box[2] - 0.5) - 1, math.ceil(box[3] - 0.5) - 1
        if right >= left and bottom >= top:
            draw.rectangle((left, top, right, bottom), fill=255)
    missing = ImageChops.subtract(mask, visible)
    count = sum(missing.histogram()[1:])
    total = sum(mask.histogram()[1:])
    return {
        "status": "covered" if count == 0 else "incomplete",
        "method": "baseline-foreground-2d-union-v1",
        "foreground_pixels": total,
        "uncovered_pixels": count,
        "uncovered_fraction": count / total,
        "uncovered_bounds_in_content_px": list(missing.getbbox()) if count else None,
        "channel_tolerance": measurement["tolerance"],
    }
