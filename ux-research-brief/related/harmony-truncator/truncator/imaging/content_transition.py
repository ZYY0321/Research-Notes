"""Measure content movement and visible coverage independently of operator plans."""

from truncator.common.capture_files import capture_image

from pathlib import Path
from PIL import Image
from truncator.source.binding import active_records, select_record
from truncator.imaging.geometry import rectangle
from truncator.common.storage import read, digest
from truncator.imaging.visual import foreground
from truncator.imaging.content_identity import compare_visible
from truncator.imaging.content_coverage import visible_regions, uncovered_area, foreground_coverage


def measure_transition(initial, current, *, selector, viewport_selector, axis, geometry):
    if axis not in {"horizontal", "vertical"}:
        raise ValueError("Unknown measurement axis")
    observations = []
    for folder in (initial, current):
        records = active_records(read(Path(folder) / "tree-before.json"))
        node = select_record(records, selector)
        viewport = select_record(node["ancestors"], viewport_selector)
        attrs = node["attributes"]
        observations.append(
            {
                "original": rectangle(attrs["origBounds"]),
                "visible": rectangle(attrs["bounds"]),
                "viewport": rectangle(viewport["attributes"]["bounds"]),
                "text": attrs.get("text"),
                "type": attrs.get("type"),
            }
        )
    for folder, row in zip((initial, current), observations):
        image_path = capture_image(folder)
        if image_path.exists():
            with Image.open(image_path) as image:
                row["screen_size"] = list(image.size)
    first, last = observations
    axis = 0 if axis == "horizontal" else 1
    same_content = first["text"] == last["text"] and first["type"] == last["type"]
    visual_identity = None
    if first["type"] in {"Text", "Button", "Image", "SymbolGlyph"}:
        if geometry.get("baseline_capture") and geometry.get("target_bounds_px"):
            baseline_image = capture_image(geometry["baseline_capture"])
            if (
                not geometry.get("baseline_image_sha256")
                or digest(baseline_image.read_bytes())
                != geometry["baseline_image_sha256"]
            ):
                raise ValueError(
                    "Content identity requires the unchanged planned baseline image"
                )
            visual_identity = [
                compare_visible(
                    capture_image(geometry["baseline_capture"]),
                    capture_image(folder),
                    geometry["target_bounds_px"],
                    row["original"],
                    row["visible"],
                    text=first["type"] in {"Text", "Button"},
                )
                for folder, row in zip((initial, current), observations)
            ]
            same_content = same_content and all(
                r["status"] == "matched" for r in visual_identity
            )
        else:
            visual_identity = [
                {"status": "unknown", "reason": "normal_rendering_missing"}
            ]
            same_content = False
    same_extent = all(
        abs(
            (first["original"][i + 2] - first["original"][i])
            - (last["original"][i + 2] - last["original"][i])
        )
        <= 2
        for i in (0, 1)
    )
    baseline_box = geometry.get("target_bounds_px")
    if baseline_box:
        same_extent = same_extent and all(
            abs(
                (first["original"][i + 2] - first["original"][i])
                - (baseline_box[i + 2] - baseline_box[i])
            )
            <= 2
            for i in (0, 1)
        )
    delta = [
        (last["original"][i] - last["viewport"][i])
        - (first["original"][i] - first["viewport"][i])
        for i in (0, 1)
    ]
    intervals = sorted(
        [
            max(0, row["visible"][axis] - row["original"][axis]),
            row["visible"][axis + 2] - row["original"][axis],
        ]
        for row in observations
    )
    regions = visible_regions(observations)
    component_box = [
        0,
        0,
        first["original"][2] - first["original"][0],
        first["original"][3] - first["original"][1],
    ]
    missing_area = uncovered_area(component_box, regions)
    covered = missing_area == 0
    result = {
        "same_content": same_content,
        "content_identity_basis": (
            "visible_pixels_against_baseline"
            if visual_identity is not None
            else "node_type_and_text"
        ),
        "visual_identity": visual_identity,
        "same_extent": same_extent,
        "relative_delta_xy_px": delta,
        "delta_along_axis_px": delta[axis],
        "delta_across_axis_px": delta[1 - axis],
        "viewport_delta_xy_px": [
            last["viewport"][i] - first["viewport"][i] for i in (0, 1)
        ],
        "visible_intervals_in_content_px": intervals,
        "visible_regions_in_content_px": regions,
        "uncovered_component_area_px2": missing_area,
        "initial_and_current_cover_component": covered and same_content and same_extent,
        "observations": observations,
        "content_recovery_review": "pending",
    }
    if "baseline_capture" in geometry:
        ink = foreground(
            capture_image(geometry["baseline_capture"]),
            geometry["target_bounds_px"],
        )
        if ink["status"] == "measured":
            interval = [
                ink["bounds_px"][axis] - geometry["target_bounds_px"][axis],
                ink["bounds_px"][axis + 2] - geometry["target_bounds_px"][axis],
            ]
            result["baseline_ink_interval_px"] = interval
            coverage = foreground_coverage(
                capture_image(geometry["baseline_capture"]),
                geometry["target_bounds_px"],
                regions,
                measurement=ink,
            )
            result["foreground_coverage"] = coverage
            result["initial_and_current_cover_baseline_ink"] = (
                same_content and same_extent and coverage["status"] == "covered"
            )
    return result

