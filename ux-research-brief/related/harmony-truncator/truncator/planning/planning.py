"""Construct source mutation plans from a validated runtime baseline."""

from truncator.common.capture_files import capture_image

import json
from dataclasses import dataclass
from truncator.common.storage import digest
from truncator.common.validation import positive
from truncator.mutation.mutations import plans, mutation_patches
from truncator.planning.baseline import load_baseline
from truncator.imaging.geometry import EDGES, rectangle
from truncator.source.binding import parent_binding, ancestor_binding, source_selectors, select_record
from truncator.imaging.visual import baseline_foreground, content_penetration
from truncator.mutation.operators import FOREGROUND_OPERATORS
from truncator.mutation.operator_strategies import strategy_for
from truncator.mutation.operator_geometry import Context
from truncator.source.source_attributes import effective_attributes


@dataclass(frozen=True)
class LayoutRelations:
    sites: list
    parent_bounds: list
    occluder_bounds: list | None
    occluder: dict | None


def _related_geometry(catalog, baseline, operator, occluder):
    site, target = baseline.site, baseline.target
    records, box = baseline.records, baseline.bounds
    related, parent_box, cover_box = [], box, None
    cover = None
    strategy = strategy_for(operator)
    if strategy.relation == "viewport":
        viewport, runtime_viewport = ancestor_binding(catalog, site, target, "Scroll")
        parent_box = rectangle(runtime_viewport["attributes"]["bounds"])
        selectors = source_selectors(catalog, viewport)
        related.append({"role": "viewport", "site": viewport,
                        "selector": selectors[0] if selectors else {"type": "Scroll"}})
        if viewport.get("parent_id") and strategy.expand_viewport_parent:
            container, runtime_container = parent_binding(catalog, viewport, runtime_viewport)
            related.append({"role": "viewport_parent", "site": container,
                            "bounds_px": rectangle(runtime_container["attributes"]["bounds"])})
    if strategy.relation == "window_parent":
        parent, runtime_parent = parent_binding(catalog, site, target)
        parent_box = rectangle(runtime_parent["attributes"]["bounds"])
        related.append({"role": "window_parent", "site": parent})
    if strategy.relation == "clipping_parent":
        parent, runtime_parent = parent_binding(catalog, site, target)
        parent_box = rectangle(runtime_parent["attributes"]["bounds"])
        related.append({"role": "clipping_parent", "site": parent})
    if strategy.relation in {"sibling", "positioned_sibling"}:
        if not occluder:
            raise ValueError("A bound existing sibling is required")
        cover_site = next(
            s
            for s in catalog["sites"] + catalog.get("structural_sites", [])
            if s["id"] == occluder["site"]
        )
        cover = select_record(records, occluder["selector"])
        if not site.get("parent_id") or site["parent_id"] != cover_site.get(
            "parent_id"
        ):
            raise ValueError("Occluder must be a direct source sibling")
        if target["ancestors"][-1]["path"] != cover["ancestors"][-1]["path"]:
            raise ValueError("Occluder must share the runtime coordinate parent")
        if strategy.relation == "positioned_sibling":
            parent, runtime_parent = parent_binding(catalog, site, target)
            if parent["component"] not in {"Stack", "Row", "Column"} or any(
                a["name"] == "padding" for a in effective_attributes(parent)
            ):
                raise ValueError(
                    "Absolute sibling positioning requires a supported parent without padding"
                )
            parent_box = rectangle(runtime_parent["attributes"]["bounds"])
        cover_box = rectangle(cover["attributes"]["bounds"])
        related.append({"role": "occluder", "site": cover_site})
    return LayoutRelations(related, parent_box, cover_box, cover)


def geometry_plans(
    catalog,
    capture_dir,
    binding,
    operator,
    density,
    penetrations,
    edge="top",
    budget=3,
    color=None,
    occluder=None,
    foreground_fraction=None,
    *,
    line_limit=None,
    alignment_bounds=None,
    stabilize_layout=False,
):
    baseline = load_baseline(catalog, capture_dir, binding, density)
    return geometry_from_baseline(
        catalog, baseline, operator, penetrations, edge, budget, color, occluder,
        foreground_fraction, line_limit=line_limit, alignment_bounds=alignment_bounds,
        stabilize_layout=stabilize_layout,
    )


def geometry_from_baseline(
    catalog, baseline, operator, penetrations, edge="top", budget=3,
    color=None, occluder=None, foreground_fraction=None, *, line_limit=None,
    alignment_bounds=None, stabilize_layout=False,
):
    """Internal planning stage: reuse an already validated baseline snapshot."""
    if (edge not in EDGES or not isinstance(budget, int)
            or isinstance(budget, bool) or budget < 1):
        raise ValueError("Invalid edge or search budget")
    if line_limit is not None and (
        operator != "ellipsis-lines"
        or isinstance(line_limit, bool)
        or not isinstance(line_limit, int)
        or line_limit < 1
    ):
        raise ValueError("line_limit requires ellipsis-lines and a positive integer")
    if alignment_bounds is not None:
        alignment_bounds = rectangle(alignment_bounds)
        if not operator.startswith("sibling-"):
            raise ValueError("Content alignment requires a sibling occlusion operator")
        content_penetration(baseline.bounds, alignment_bounds, edge, 0.5)
    capture_dir = baseline.capture_dir
    capture_record = baseline.capture_record
    binding, density = baseline.binding, baseline.density
    site, target, box = baseline.site, baseline.target, baseline.bounds
    mutated_selector = baseline.mutated_selector
    color_source = "explicit" if color is not None else "dump_opaque_background"
    width, height = box[2] - box[0], box[3] - box[1]
    content_measurement = None
    if foreground_fraction is not None:
        if site["component"] != "Text" or operator not in FOREGROUND_OPERATORS:
            raise ValueError(
                "Foreground calibration requires Text with fixed layout clipping or overlay"
            )
        content_measurement = baseline_foreground(baseline)
        if content_measurement["status"] != "measured":
            raise ValueError(
                "Foreground calibration unavailable: " + content_measurement["status"]
            )
        penetrations = [
            content_penetration(
                box, content_measurement["bounds_px"], edge, foreground_fraction
            )
        ]
        if operator == "overlay-occlusion" and color is None:
            color = "#" + "".join(
                f"{channel:02X}" for channel in content_measurement["background_rgb"]
            )
            color_source = "baseline_flat_region"
    relations = _related_geometry(catalog, baseline, operator, occluder)
    related = relations.sites
    results = []
    for cut in list(dict.fromkeys(penetrations))[:budget]:
        positive(cut, "penetration_px")
        extent = width if edge in {"left", "right"} else height
        if cut >= extent:
            raise ValueError("Penetration must leave part of the target visible")
        p = strategy_for(operator).parameters(
            Context(baseline, relations, cut, edge, color, alignment_bounds),
            stabilize=stabilize_layout,
        )
        if line_limit is not None:
            p["lines"] = line_limit
        if "instance_index" in binding:
            p["instance_index"] = binding["instance_index"]
        if "instance_key" in binding:
            p["instance_key"] = binding["instance_key"]
        plan = plans(catalog, 0, 1, operator, p, site_id=site["id"])[0]
        plan.update(
            schema_version=2,
            mechanism=operator,
            visual_categories=["cropped_content"],
            related_sites=related,
            max_source_sites=1 + len(related),
            geometry={
                "strategy": "measured-boundary",
                "selector": binding["selector"],
                "mutated_selector": mutated_selector,
                "source_binding": binding,
                "baseline_capture": str(capture_dir),
                "baseline_image_sha256": capture_record["screenshot_sha256"],
                "baseline_tree_sha256": digest(
                    (capture_dir / "tree-before.json").read_bytes()
                ),
                "target_bounds_px": box,
                "parent_bounds_px": relations.parent_bounds,
                "occluder_bounds_px": relations.occluder_bounds,
                "occluder_binding": occluder,
                "px_per_vp": density,
                "density_source": binding.get("density_source", "explicit calibration"),
                "overlay_color_source": (
                    color_source if operator == "overlay-occlusion" else None
                ),
                "edge": edge,
                "penetration_px": cut,
                "budget": budget,
                "search_values_px": list(penetrations),
                "units": {"tree": "px", "source": "vp"},
            },
        )
        if "occlusion" in operator:
            plan["visual_categories"].append("container_overlap")
        if operator == "window-edge-clip":
            plan["geometry"]["window_bounds_px"] = p["window_bounds_px"]
            plan["geometry"]["host_window_id"] = p["host_window_id"]
            plan["geometry"]["translation_delta_px"] = p["translation_delta_px"]
        if operator in {"viewport-width-mismatch", "freeze-viewport-width", "cache-viewport-width"}:
            plan["geometry"]["viewport_width_px"] = p["viewport_width"] * density
            plan["geometry"]["viewport_selector"] = related[0]["selector"]
            plan["geometry"]["planning_assumption"] = (
                "Target left offset scales with viewport width and target intrinsic width stays fixed. "
                "Verify the resulting target and viewport bounds after rendering.")
            if operator == "freeze-viewport-width":
                plan["geometry"]["trigger_condition"] = "same-package-in-narrower-window"
                plan["geometry"]["planning_assumption"] = "Preserve the measured baseline viewport width in vp; verify again after window narrowing."
                plan["geometry"]["penetration_px"] = 0
                plan["geometry"]["search_values_px"] = []
                plan["geometry"]["parameter_basis"] = "measured_baseline_viewport_width"
        if operator == "cache-viewport-width":
            plan["geometry"].update(
                trigger_condition="continuous-window-narrowing-after-first-layout",
                planning_assumption="Cache the first positive runtime viewport width; parent remains responsive.",
                penetration_px=0, search_values_px=[], parameter_basis="first_runtime_layout_width",
            )
        if plan.get("construction_intent"):
            plan["visual_categories"] = []
        if content_measurement is not None:
            plan["geometry"]["foreground_calibration"] = {
                **content_measurement,
                "requested_fraction": foreground_fraction,
            }
        if alignment_bounds is not None:
            plan["geometry"]["alignment_bounds_px"] = alignment_bounds
        plan["file_hashes"] = {
            s["file"]: catalog["files"][s["file"]]
            for s in [site] + [r["site"] for r in related]
        }
        plan["patches"] = mutation_patches(plan)
        plan.pop("id")
        plan["id"] = digest(json.dumps(plan, sort_keys=True))[:20]
        results.append(plan)
    return results
