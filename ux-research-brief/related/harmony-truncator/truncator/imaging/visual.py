"""Deterministic pixel measurements for calibration and capture diagnostics."""

from collections import Counter
from PIL import Image, ImageChops, ImageDraw
from truncator.imaging.geometry import rectangle
from truncator.common.validation import finite


def baseline_foreground(baseline, *, exclude_boundary=False):
    """Memoize pixel statistics within one validated planning snapshot."""
    from copy import deepcopy
    from truncator.common.capture_files import capture_image

    cache = getattr(baseline, "measurement_cache", None)
    key = ("foreground", exclude_boundary)
    if cache is not None and key in cache:
        return deepcopy(cache[key])
    result = foreground(capture_image(baseline.capture_dir), baseline.bounds,
                        exclude_boundary=exclude_boundary)
    if cache is not None:
        cache[key] = deepcopy(result)
    return result


def pixel_values(image):
    method = getattr(image, "get_flattened_data", image.getdata)
    return method()


def foreground(
    image_path, bounds, tolerance=40, minimum_background=0.7, *, exclude_boundary=False
):
    bounds = rectangle(bounds)
    with Image.open(image_path) as image:
        if (
            bounds[0] < 0
            or bounds[1] < 0
            or bounds[2] > image.width
            or bounds[3] > image.height
        ):
            raise ValueError("Measurement region exceeds screenshot")
        roi = image.convert("RGB").crop(tuple(round(v) for v in bounds))
    if not roi.width or not roi.height:
        return {"status": "empty", "foreground_pixels": 0, "reason": "subpixel_region"}
    colors = list(pixel_values(roi))
    buckets = Counter(tuple(channel // 8 for channel in pixel) for pixel in colors)
    bucket, count = buckets.most_common(1)[0]
    members = [
        pixel for pixel in colors if tuple(channel // 8 for channel in pixel) == bucket
    ]
    background = tuple(
        sorted(pixel[channel] for pixel in members)[len(members) // 2]
        for channel in range(3)
    )
    background_pixels = sum(
        max(abs(a - b) for a, b in zip(pixel, background)) <= tolerance
        for pixel in colors
    )
    confidence = background_pixels / len(colors)
    result = {
        "background_rgb": list(background),
        "background_fraction": confidence,
        "method": "dominant-flat-background",
        "tolerance": tolerance,
    }
    if confidence < minimum_background:
        # Tight glyph boxes can contain less than 70% background. Require
        # independent spatial evidence: both horizontal rims and the perimeter
        # must agree with the dominant flat colour. Do not lower the global
        # threshold for arbitrary pictures or gradient backgrounds.
        def agrees(pixel):
            return max(abs(a - b) for a, b in zip(pixel, background)) <= tolerance

        rims = [[roi.getpixel((x, y)) for x in range(roi.width)]
                for y in (0, roi.height - 1)]
        perimeter = rims[0] + rims[1] + [roi.getpixel((x, y))
                    for x in (0, roi.width - 1) for y in range(roi.height)]
        rim_fractions = [sum(map(agrees, rim)) / len(rim) for rim in rims]
        perimeter_fraction = sum(map(agrees, perimeter)) / len(perimeter)
        result.update(rim_background_fractions=rim_fractions,
                      perimeter_background_fraction=perimeter_fraction)
        if (minimum_background != 0.7 or confidence < 0.45
                or min(rim_fractions) < 0.95 or perimeter_fraction < 0.85):
            return {**result, "status": "unsupported_background"}
        result["method"] = "flat-background-supported-by-rims"
    mask = Image.new("L", roi.size)
    mask.putdata(
        [
            255 if max(abs(a - b) for a, b in zip(pixel, background)) > tolerance else 0
            for pixel in colors
        ]
    )
    if exclude_boundary:
        # Rounded text backgrounds expose the page at their corners. Remove those
        # border-connected regions before measuring the interior glyphs.
        initial_pixels = sum(mask.histogram()[1:])
        # A corner region or enclosing outline touches at least two sides.
        # Keep glyphs that merely reach one side of their tight component box.
        border = [(x, y) for x in range(roi.width) for y in (0, roi.height - 1)]
        border += [(x, y) for y in range(roi.height) for x in (0, roi.width - 1)]
        remaining = mask.copy()
        for point in border:
            if remaining.getpixel(point):
                before = remaining.copy()
                ImageDraw.floodfill(remaining, point, 0)
                region = ImageChops.subtract(before, remaining)
                left, top, right, bottom = region.getbbox()
                sides = sum((left == 0, top == 0, right == roi.width, bottom == roi.height))
                if sides >= 2:
                    mask.paste(0, mask=region)
        result["boundary_pixels_removed"] = initial_pixels - sum(mask.histogram()[1:])
        result["method"] = "dominant-flat-background-interior"
    box = mask.getbbox()
    pixels = sum(mask.histogram()[1:])
    result.update(foreground_pixels=pixels, status="measured" if box else "empty")
    if box:
        result["bounds_px"] = [
            box[0] + bounds[0],
            box[1] + bounds[1],
            box[2] + bounds[0],
            box[3] + bounds[1],
        ]
    return result


def adjacent_background(image_path, bounds, edge, density):
    """Measure a narrow exterior strip next to the planned occlusion edge."""
    x0, y0, x1, y1 = rectangle(bounds)
    thickness = max(2, round(2 * density))
    gap = max(1, round(0.5 * density))
    strips = {
        "top": [x0, y0 - gap - thickness, x1, y0 - gap],
        "bottom": [x0, y1 + gap, x1, y1 + gap + thickness],
        "left": [x0 - gap - thickness, y0, x0 - gap, y1],
        "right": [x1 + gap, y0, x1 + gap + thickness, y1],
    }
    region = strips[edge]
    with Image.open(image_path) as image:
        if (
            region[0] < 0
            or region[1] < 0
            or region[2] > image.width
            or region[3] > image.height
        ):
            raise ValueError("No screenshot area beside the overlay edge")
    measurement = foreground(image_path, region, tolerance=20, minimum_background=0.9)
    if measurement.get("background_fraction", 0) < 0.9:
        raise ValueError("Overlay edge has no locally uniform background")
    return {**measurement, "sample_bounds_px": region, "method": "adjacent-flat-strip"}


def content_penetration(component, content, edge, fraction):
    finite(fraction, "foreground_fraction")
    if not 0 < fraction < 1:
        raise ValueError("foreground_fraction must be between zero and one")
    component, content = rectangle(component), rectangle(content)
    if (
        content[0] < component[0]
        or content[1] < component[1]
        or content[2] > component[2]
        or content[3] > component[3]
    ):
        raise ValueError("Foreground must lie inside the component")
    if edge == "top":
        return content[1] - component[1] + fraction * (content[3] - content[1])
    if edge == "bottom":
        return component[3] - content[3] + fraction * (content[3] - content[1])
    if edge == "left":
        return content[0] - component[0] + fraction * (content[2] - content[0])
    if edge == "right":
        return component[2] - content[2] + fraction * (content[2] - content[0])
    raise ValueError("Unknown edge")


def changed_fraction(baseline, candidate, exclude=(), threshold=40):
    finite(threshold, "pixel_difference_threshold")
    if not 0 <= threshold <= 255:
        raise ValueError("Pixel threshold must be in [0,255]")
    with Image.open(baseline) as before, Image.open(candidate) as after:
        if before.size != after.size:
            return {"status": "size_mismatch", "changed_fraction": 1.0}
        delta = ImageChops.difference(before.convert("RGB"), after.convert("RGB"))
    from PIL import ImageDraw

    included = Image.new("L", delta.size, 255)
    draw = ImageDraw.Draw(included)
    for box in exclude:
        x0, y0, x1, y1 = rectangle(box)
        if x0 < 0 or y0 < 0 or x1 > delta.width or y1 > delta.height:
            raise ValueError("Excluded region exceeds screenshot")
        draw.rectangle((round(x0), round(y0), round(x1) - 1, round(y1) - 1), fill=0)
    count = sum(included.histogram()[1:])
    if count == 0:
        raise ValueError("Image check must include some pixels")
    red, green, blue = delta.split()
    maximum = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    binary = maximum.point([255 if value > threshold else 0 for value in range(256)])
    changed = ImageChops.multiply(binary, included).histogram()[255]
    return {
        "status": "measured",
        "changed_fraction": changed / count,
        "included_pixels": count,
        "threshold": threshold,
    }


def severity_policy(measurement, allowed=("partial", "complete", "unresolved")):
    valid = {"partial", "complete", "unresolved"}
    if not allowed or set(allowed) - valid:
        raise ValueError("Invalid allowed severity categories")
    return {
        "severity": measurement,
        "eligible": measurement in allowed,
        "allowed": list(allowed),
    }
