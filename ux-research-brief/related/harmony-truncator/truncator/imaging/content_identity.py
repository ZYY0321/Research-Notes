"""Compare visible content in component coordinates against its normal rendering."""

from pathlib import Path
from collections import Counter
from PIL import Image, ImageChops, ImageFilter
from truncator.common.storage import digest
from truncator.imaging.visual import pixel_values


def compare_visible(reference, current, reference_box, original, visible, *, text=False):
    paths = [Path(reference), Path(current)]
    if not all(p.is_file() for p in paths):
        return {"status": "unknown", "reason": "screenshot_missing"}
    if any(
        abs((reference_box[i + 2] - reference_box[i]) - (original[i + 2] - original[i]))
        > 2
        for i in (0, 1)
    ):
        return {"status": "unknown", "reason": "component_extent_changed"}
    with Image.open(paths[0]) as a, Image.open(paths[1]) as b:
        a, b = a.convert("RGB"), b.convert("RGB")
        # Compare only the jointly available content; exclude the clipping edge's AA pixels.
        left = max(0, visible[0] - original[0], -original[0], -reference_box[0]) + 2
        top = max(0, visible[1] - original[1], -original[1], -reference_box[1]) + 2
        right = (
            min(
                reference_box[2] - reference_box[0],
                visible[2] - original[0],
                a.width - reference_box[0],
                b.width - original[0],
            )
            - 2
        )
        bottom = (
            min(
                reference_box[3] - reference_box[1],
                visible[3] - original[1],
                a.height - reference_box[1],
                b.height - original[1],
            )
            - 2
        )
        if right <= left or bottom <= top:
            return {"status": "unknown", "reason": "no_common_visible_region"}
        region = [round(x) for x in (left, top, right, bottom)]

        def crop(image, origin):
            return image.crop(tuple(region[i] + round(origin[i % 2]) for i in range(4)))

        ac, bc = crop(a, reference_box), crop(b, original)
        pixels = list(pixel_values(ac))
        background = Counter(pixels).most_common(1)[0][0]
        if text:
            # Text centering can change rasterization by a fraction of a pixel
            # after vp rounding. Require foreground support in a 1px neighborhood
            # in both directions, rather than accepting a percentage of lost glyphs.
            def ink(image):
                channels = ImageChops.difference(
                    image, Image.new("RGB", image.size, background)
                ).split()
                maximum = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
                return maximum.point(lambda value: 255 if value > 40 else 0), maximum

            (expected, expected_contrast), (observed, observed_contrast) = ink(ac), ink(bc)
            if min(expected.size) <= 2:
                return {"status": "unknown", "reason": "insufficient_visible_detail"}
            # The outer ring supplies neighborhood support. It cannot itself be
            # judged: pixels beyond the jointly visible crop are unavailable.
            interior = (1, 1, expected.width - 1, expected.height - 1)
            detail = sum(expected.crop(interior).histogram()[1:])
            if detail < 16:
                return {"status": "unknown", "reason": "insufficient_visible_detail"}
            missing = ImageChops.subtract(expected, observed.filter(ImageFilter.MaxFilter(3)))
            extra = ImageChops.subtract(observed, expected.filter(ImageFilter.MaxFilter(3)))
            missing_count, extra_count = (sum(mask.crop(interior).histogram()[1:]) for mask in (missing, extra))
            strong_disagreements = sum(
                sum(ImageChops.darker(mask, contrast.point(lambda value: 255 if value > 80 else 0))
                    .crop(interior).histogram()[1:])
                for mask, contrast in ((missing, expected_contrast), (extra, observed_contrast))
            )
            status = ("matched" if missing_count == extra_count == 0 else
                      "different" if strong_disagreements else "unknown")
            return {
                "status": status,
                "reason": "low_contrast_ink_disagreement" if status == "unknown" else None,
                "method": "component-coordinate-text-ink-v1",
                "content_region_px": region, "detail_pixels": detail,
                "missing_pixels": missing_count, "extra_pixels": extra_count,
                "strong_disagreement_pixels": strong_disagreements,
                "uncertain_contrast_limit": 80,
                "spatial_tolerance_px": 1, "channel_tolerance": 40,
                "comparison_border_px": 3,
                "sha256": [digest(p.read_bytes()) for p in paths],
            }
        compared = [
            (x, y)
            for x, y in zip(pixels, pixel_values(bc))
            if max(abs(v - w) for v, w in zip(x, background)) > 40
            or max(abs(v - w) for v, w in zip(y, background)) > 40
        ]
        if len(compared) < 16:
            return {"status": "unknown", "reason": "insufficient_visible_detail"}
        mismatches = sum(
            max(abs(v - w) for v, w in zip(x, y)) > 40 for x, y in compared
        )
        ratio = mismatches / len(compared)
        return {
            "status": "matched" if ratio <= 0.10 else "different",
            "method": "component-coordinate-visible-pixels-v1",
            "content_region_px": region,
            "detail_pixels": len(compared),
            "mismatch_fraction": ratio,
            "threshold": 0.10,
            "channel_tolerance": 40,
            "sha256": [digest(p.read_bytes()) for p in paths],
        }
