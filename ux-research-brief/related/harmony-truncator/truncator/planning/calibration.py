"""Baseline-only parameter planning and explicit reproduction schedules."""

from truncator.common.capture_files import capture_image

import json
from truncator.common.storage import digest
from truncator.imaging.visual import baseline_foreground
from truncator.common.validation import finite
from truncator.planning.planning import geometry_from_baseline
from truncator.mutation.operators import REGISTRY, FOREGROUND_OPERATORS
from truncator.planning.baseline import load_baseline
from truncator.planning.parameter_policy import choose_parameters, choose_occluder, control_direction


def _validate_request(operator, penetrations, ratios, foreground_fraction):
    supplied = sum(value is not None for value in (penetrations, ratios, foreground_fraction))
    if supplied > 1:
        raise ValueError("Specify only one of penetrations, ratios or foreground_fraction")
    if operator not in REGISTRY:
        raise ValueError("Unknown construction operator: " + str(operator))
    if operator in {"freeze-viewport-width", "cache-viewport-width"} and supplied:
        raise ValueError("Viewport width operators use initial width; cut schedules do not apply")


def plan_for_target(
    catalog,
    capture_dir,
    binding,
    operator,
    *,
    density=None,
    edge=None,
    budget=3,
    color=None,
    occluder=None,
    penetrations=None,
    ratios=None,
    foreground_fraction=None,
):
    """Shared CLI/campaign entry point for automatic and explicit parameters."""
    _validate_request(operator, penetrations, ratios, foreground_fraction)
    baseline = load_baseline(catalog, capture_dir, binding, density)
    return plan_from_baseline(
        catalog, baseline, operator, edge=edge, budget=budget, color=color,
        occluder=occluder, penetrations=penetrations, ratios=ratios,
        foreground_fraction=foreground_fraction,
    )


def plan_from_baseline(
    catalog, baseline, operator, *, edge=None, budget=3, color=None, occluder=None,
    penetrations=None, ratios=None, foreground_fraction=None,
):
    """Plan another mechanism for the same already validated target."""
    _validate_request(operator, penetrations, ratios, foreground_fraction)
    if edge is None and operator in {"scroll-recovery", "whitespace-clip"}:
        edge = control_direction(baseline)["edge"]
    if edge is None and (REGISTRY[operator].get("construction_intent")
                         or operator in {"window-edge-clip", "viewport-width-mismatch", "freeze-viewport-width"}):
        edge = REGISTRY[operator]["default_edge"]
    if penetrations is None and foreground_fraction is None:
        return _automatic_plans(
            catalog,
            baseline,
            operator,
            edge,
            budget,
            color,
            occluder,
            ratios,
        )
    return geometry_from_baseline(
        catalog,
        baseline,
        operator,
        [1] if penetrations is None else penetrations,
        edge or "top",
        budget,
        color,
        occluder,
        foreground_fraction,
    )


def automatic_plans(
    catalog,
    capture_dir,
    binding,
    operator,
    density=None,
    edge=None,
    budget=3,
    color=None,
    occluder=None,
    ratios=None,
):
    baseline = load_baseline(catalog, capture_dir, binding, density)
    return _automatic_plans(catalog, baseline, operator, edge, budget, color, occluder, ratios)


def _automatic_plans(catalog, baseline, operator, edge, budget, color, occluder, ratios):
    capture_dir = baseline.capture_dir
    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 1:
        raise ValueError("Invalid search budget")
    if edge is None:
        edge = (control_direction(baseline)["edge"]
                if operator in {"scroll-recovery", "whitespace-clip"} else REGISTRY[operator]["default_edge"])
    if operator in {"freeze-viewport-width", "cache-viewport-width"}:
        if ratios is not None:
            raise ValueError("Viewport width operators use initial width; ratio schedules do not apply")
        return geometry_from_baseline(catalog, baseline, operator, [1], edge, 1)
    if operator in {"width-clip", "line-clip", "ellipsis-width"} and edge in {
        "top",
        "bottom",
    }:
        edge = "right"
    if ratios is None:
        if operator in {"height-clip", "ellipsis-lines"}:
            edge = "bottom"
        if operator.startswith("sibling-") and occluder is None:
            occluder = choose_occluder(catalog, baseline, edge)
        decision = choose_parameters(baseline, operator, edge, occluder, color=color)
        plan = geometry_from_baseline(
            catalog,
            baseline,
            operator,
            [decision["cut_px"]],
            edge,
            1,
            color if color is not None else decision["color"],
            occluder,
            line_limit=decision["line_limit"],
            alignment_bounds=decision["alignment_bounds"],
            stabilize_layout=True,
        )[0]
        plan["geometry"]["automatic"] = decision["metadata"]
        if decision["color"] is not None and color is None:
            plan["geometry"]["overlay_color_source"] = decision["metadata"][
                "overlay_color_source"
            ]
        plan.pop("id")
        plan["id"] = digest(json.dumps(plan, sort_keys=True))[:20]
        return [plan]
    record, box = baseline.target, baseline.bounds
    extent = box[2] - box[0] if edge in {"left", "right"} else box[3] - box[1]
    content = None
    supports_foreground = (
        record["attributes"].get("type") == "Text" and operator in FOREGROUND_OPERATORS
    )
    if supports_foreground:
        content = baseline_foreground(baseline)
    use_foreground = content is not None and content["status"] == "measured"
    ratios = list(ratios)
    for ratio in ratios:
        finite(ratio, "ratio")
        if not 0 < ratio < 1:
            raise ValueError("Ratios must be between zero and one")
    result = []
    seen = set()
    for ratio in list(dict.fromkeys(ratios))[:budget]:
        plan = geometry_from_baseline(
            catalog,
            baseline,
            operator,
            [extent * ratio],
            edge,
            1,
            color,
            occluder,
            ratio if use_foreground else None,
        )[0]
        patch_hash = digest(json.dumps(plan["patches"], sort_keys=True))
        if patch_hash in seen:
            continue
        seen.add(patch_hash)
        plan["geometry"]["automatic"] = {
            "basis": "foreground" if use_foreground else "component",
            "ratio": ratio,
            "ratios": list(ratios),
            "budget": budget,
            "foreground_measurement": content,
            "fallback_reason": (
                content["status"] if content and not use_foreground else None
            ),
        }
        plan.pop("id")
        plan["id"] = digest(json.dumps(plan, sort_keys=True))[:20]
        result.append(plan)
    if not result:
        raise ValueError("No parameter candidates")
    return result
