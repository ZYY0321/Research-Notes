"""Measure a baseline, delegate cut selection, and bound/report the decision."""

import math
import re
from PIL import Image
from truncator.common.capture_files import capture_image
from truncator.source.binding import bind_candidates, select_record
from truncator.source.source_attributes import effective_attributes
from truncator.imaging.geometry import rectangle, overlap_translation
from truncator.imaging.visual import baseline_foreground, pixel_values
from truncator.mutation.operator_selection import SelectionContext, initial_selection
from truncator.mutation.operator_strategies import strategy_for

POLICY_VERSION = "baseline-rules-v9"


def text_bands(image_path, measurement, density):
    """Estimate visible text rows by horizontal ink projection on a flat background."""
    if measurement.get("status") != "measured":
        return []
    bounds = measurement["bounds_px"]
    with Image.open(image_path) as image:
        roi = image.convert("RGB").crop(tuple(round(value) for value in bounds))
    pixels = list(pixel_values(roi))
    background = measurement["background_rgb"]
    bands = []
    maximum_gap = max(1, round(density))
    for row in range(roi.height):
        occupied = any(
            max(abs(a - b) for a, b in zip(pixel, background))
            > measurement["tolerance"]
            for pixel in pixels[row * roi.width : (row + 1) * roi.width]
        )
        if occupied:
            y = round(bounds[1]) + row
            if bands and y - bands[-1][1] <= maximum_gap:
                bands[-1][1] = y + 1
            else:
                bands.append([y, y + 1])
    minimum_height = max(2, round(density))
    return [band for band in bands if band[1] - band[0] >= minimum_height]


def choose_occluder(catalog, baseline, edge):
    """Choose the nearest uniquely bound opaque source sibling deterministically."""
    catalog = {
        **catalog,
        "sites": catalog["sites"] + catalog.get("structural_sites", []),
    }
    from truncator.common.storage import read

    tree = read(baseline.capture_dir / "tree-before.json")
    bindings = bind_candidates(catalog, tree)["bindings"]
    sites = {site["id"]: site for site in catalog["sites"]}
    candidates = []
    for binding in bindings:
        site = sites[binding["site"]]
        if site["id"] == baseline.site["id"] or not site.get("parent_id"):
            continue
        if site["parent_id"] != baseline.site.get("parent_id"):
            continue
        record = select_record(baseline.records, binding["selector"])
        attrs = record["attributes"]
        color = attrs.get("backgroundColor", "")
        opaque = re.fullmatch(r"#(?:[fF]{2})?[0-9a-fA-F]{6}", color) is not None
        if (
            not opaque
            or float(attrs.get("opacity") or 1) != 1
            or attrs.get("visible") == "false"
        ):
            continue
        if not record["ancestors"] or not baseline.target["ancestors"]:
            continue
        if record["ancestors"][-1]["path"] != baseline.target["ancestors"][-1]["path"]:
            continue
        box = rectangle(attrs["bounds"])
        dx, dy = overlap_translation(
            baseline.bounds,
            box,
            edge,
            0.2
            * min(
                baseline.bounds[2] - baseline.bounds[0],
                baseline.bounds[3] - baseline.bounds[1],
            ),
        )
        candidates.append((math.hypot(dx, dy), site["id"], binding))
    if not candidates:
        raise ValueError("No uniquely bound opaque sibling available")
    return min(candidates, key=lambda item: (item[0], item[1]))[2]


def control_direction(baseline, axis="auto"):
    """Infer the reading axis from rendered text rows, preserving explicit choices."""
    if axis not in {"auto", "horizontal", "vertical"}:
        raise ValueError("Control axis must be auto, horizontal or vertical")
    measurement = baseline_foreground(baseline)
    bands = text_bands(capture_image(baseline.capture_dir), measurement, baseline.density)
    is_text = baseline.site["component"] == "Text" or (
        baseline.site["component"] == "Button"
        and bool(baseline.target["attributes"].get("text", "").strip())
    )
    if is_text and bands:
        inferred = "vertical" if len(bands) > 1 else "horizontal"
        basis = "rendered_text_rows"
    else:
        text = baseline.target["attributes"].get("text", "")
        inferred = "vertical" if is_text and "\n" in text else "horizontal"
        basis = "explicit_line_breaks" if inferred == "vertical" else "unresolved_horizontal_default"
    selected = inferred if axis == "auto" else axis
    return {"axis": selected, "edge": "bottom" if selected == "vertical" else "right",
            "inferred_axis": inferred, "basis": basis, "visible_text_bands_px": bands,
            "explicit_override": axis != "auto", "foreground": measurement}


def choose_parameters(baseline, operator, edge, occluder=None, *, color=None):
    strategy = strategy_for(operator)
    image_path = capture_image(baseline.capture_dir)
    is_text = baseline.site["component"] == "Text"
    measurement = None
    if strategy.measure_any_component or baseline.site["component"] in {"Text", "Image", "SymbolGlyph", "Button"}:
        attributes = {item["name"] for item in effective_attributes(baseline.site)}
        rounded = is_text and {"backgroundColor", "borderRadius"}.issubset(attributes)
        measurement = baseline_foreground(baseline, exclude_boundary=rounded)
    measured = measurement is not None and measurement["status"] == "measured"
    bands = text_bands(image_path, measurement, baseline.density) if measured and is_text else []
    context = SelectionContext(baseline, edge, image_path, measurement, bands, occluder, color)
    choice = initial_selection(context)
    strategy.select(context, choice)

    minimum = min(1.0, context.extent * 0.05)
    maximum = context.extent - minimum
    cuts = [max(minimum, min(maximum, value)) for value in choice.cuts]
    interval = sorted(cuts[:2])
    chosen = max(interval[0], min(interval[1], cuts[2]))
    return {
        "cut_px": chosen,
        "line_limit": choice.line_limit,
        "alignment_bounds": choice.alignment_bounds,
        "color": choice.color,
        "metadata": {
            "policy": POLICY_VERSION,
            "strategy": "single-pass",
            "basis": "foreground" if measured else "component",
            "rule": choice.rule,
            "cut_interval_px": interval,
            "selected_cut_px": chosen,
            "preferred_fraction": choice.fraction,
            "foreground_measurement": measurement,
            "text_padding": choice.padding_measurement,
            "overlay_background_measurement": choice.overlay_measurement,
            "overlay_color_source": choice.overlay_color_source,
            "visible_text_bands_px": bands,
            "selected_max_lines": choice.line_limit,
            "max_lines_interval": [1, len(bands) - 1] if choice.line_limit is not None else None,
            "fallback_reason": measurement["status"] if measurement and not measured else None,
            "assumptions": choice.assumptions,
            "evidence_source": "baseline-only",
        },
    }
