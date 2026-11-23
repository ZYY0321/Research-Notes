"""Tree-derived measurements kept separate from the human visual decision."""

from truncator.common.capture_files import capture_image

from pathlib import Path
from PIL import Image, ImageChops, ImageStat
from truncator.source.binding import active_records, select_record
from truncator.planning.composition import capture_members
from truncator.planning.pages import resolve_page
from truncator.review.diagnostics import diagnose
from truncator.planning.layout_impact import record_layout_impact
from truncator.imaging.geometry import rectangle
from truncator.common.storage import read, save


def observe(plan, capture_dir, save_result=True, baseline_capture=None):
    geometry = plan.get("geometry")
    if not geometry:
        return None
    capture_dir = Path(capture_dir)
    records = active_records(read(capture_dir / "tree-before.json"))
    result = {
        "mechanism": plan["operator"],
        "visual_review": "pending",
        "planned_penetration_px": geometry["penetration_px"],
    }
    try:
        selector = geometry.get("mutated_selector", geometry["selector"])
        target = select_record(records, selector)
        after = select_record(
            active_records(read(capture_dir / "tree-after.json")), selector
        )
        attrs = target["attributes"]
        bounds, orig = rectangle(attrs["bounds"]), rectangle(attrs["origBounds"])
        result.update(
            target=attrs,
            target_stable=attrs == after["attributes"],
            bounds_equal=bounds == orig,
            clipped_edges_px={
                "left": max(0, bounds[0] - orig[0]),
                "top": max(0, bounds[1] - orig[1]),
                "right": max(0, orig[2] - bounds[2]),
                "bottom": max(0, orig[3] - bounds[3]),
            },
        )
        if plan["operator"] == "window-edge-clip":
            root = next((node for node in target["ancestors"]
                         if node["attributes"].get("type") == "root"
                         and node["attributes"].get("hostWindowId") == attrs.get("hostWindowId")), None)
            window_box = rectangle(root["attributes"]["bounds"]) if root else None
            edge = geometry["edge"]
            index = {"left": 0, "top": 1, "right": 2, "bottom": 3}[edge]
            result["window_bounds_px"] = window_box
            result["window_boundary_match"] = None if window_box is None else (
                result["clipped_edges_px"][edge] > 0 and bounds[index] == window_box[index])
        if plan["operator"] in {"viewport-width-mismatch", "freeze-viewport-width"}:
            viewport = select_record(target["ancestors"], geometry.get("viewport_selector", {"type": "Scroll"}))
            viewport_bounds = rectangle(viewport["attributes"]["bounds"])
            viewport_original = rectangle(viewport["attributes"]["origBounds"])
            result["viewport"] = viewport["attributes"]
            result["viewport_width_mismatch_observed"] = (
                viewport_original[2] - viewport_original[0] > viewport_bounds[2] - viewport_bounds[0]
                and result["clipped_edges_px"]["right"] > 0 and bounds[2] == viewport_bounds[2])
            display_path = capture_dir / "display.json"
            display = read(display_path) if display_path.exists() else {}
            current_density = display.get("px_per_vp", geometry["px_per_vp"])
            current_width_vp = (viewport_bounds[2] - viewport_bounds[0]) / current_density
            baseline_width_vp = (geometry["parent_bounds_px"][2] - geometry["parent_bounds_px"][0]) / geometry["px_per_vp"]
            result["viewport_width_vp"] = current_width_vp
            result["baseline_viewport_width_vp"] = baseline_width_vp
            result["window_narrowed"] = current_width_vp < baseline_width_vp - 0.5
        if geometry.get("occluder_binding"):
            cover = select_record(records, geometry["occluder_binding"]["selector"])
            cover_box = rectangle(cover["attributes"]["bounds"])
            result["occluder"] = cover["attributes"]
            result["intersection_area_px"] = max(
                0, min(bounds[2], cover_box[2]) - max(bounds[0], cover_box[0])
            ) * max(0, min(bounds[3], cover_box[3]) - max(bounds[1], cover_box[1]))
        baseline = Path(baseline_capture or geometry["baseline_capture"])
        result["baseline_capture"] = str(baseline)
        with Image.open(capture_image(baseline)) as before_image, Image.open(
            capture_image(capture_dir)
        ) as after_image:
            if before_image.size != after_image.size:
                result["image_comparison"] = "screen_size_changed"
            else:
                roi = geometry["target_bounds_px"]
                if baseline_capture:
                    normal = select_record(
                        active_records(read(baseline / "tree-before.json")),
                        geometry["selector"],
                    )
                    roi = rectangle(normal["attributes"]["bounds"])
                delta = ImageChops.difference(
                    before_image.convert("RGB").crop(roi),
                    after_image.convert("RGB").crop(roi),
                )
                result["baseline_target_roi_mean_absolute_pixel_difference"] = (
                    sum(ImageStat.Stat(delta).mean) / 3
                )
        result["status"] = "measured"
    except (ValueError, OSError, KeyError) as error:
        result.update(status="measurement_failed", error=str(error))
    if save_result:
        save(capture_dir / "geometry-observation.json", result)
    return result


def record_observations(saved_plan, recipe, attempt):
    """Write diagnostics independently of the mutation selection and build stages."""
    active_plans = capture_members(saved_plan, recipe)
    try:
        record_layout_impact(saved_plan, recipe, attempt)
    except (ValueError, OSError, KeyError) as error:
        save(
            attempt / "layout-impact.json",
            {"status": "unavailable", "error": str(error)},
        )
    page = resolve_page(saved_plan, recipe) if "pages" in saved_plan else None
    observation_baseline = page["baseline_capture"] if page else None
    if "mutations" in saved_plan:
        save(
            attempt / "geometry-observation.json",
            {
                "mutations": [
                    {
                        "id": p["id"],
                        **observe(
                            p,
                            attempt,
                            save_result=False,
                            baseline_capture=observation_baseline,
                        ),
                    }
                    for p in active_plans
                ],
                "visual_review": "pending",
            },
        )
    else:
        observe(saved_plan, attempt)
    try:
        diagnose(
            saved_plan,
            attempt,
            recipe.get("allowed_severity", ("partial", "complete", "unresolved")),
        )
    except (ValueError, OSError, KeyError) as error:
        save(
            attempt / "diagnostics.json",
            {"status": "unavailable", "error": str(error)},
        )
