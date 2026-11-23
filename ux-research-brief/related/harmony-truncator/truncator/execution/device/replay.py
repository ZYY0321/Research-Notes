"""Translate bounded, component-relative recipe actions into uitest arguments."""

from truncator.source.binding import active_records, select_record
from truncator.imaging.geometry import rectangle
from truncator.common.validation import finite


def action_matches(tree, action):
    if "recovery_target" in action:
        try:
            target = select_record(active_records(tree), action["recovery_target"])
        except ValueError:
            return []
        nodes = [record["attributes"] for record in target["ancestors"]]
    else:
        nodes = actionable_nodes(tree)
    return [node for node in nodes if matches_selector(node, action)]


def resolve_action(action, tree):
    if "recovery_target" not in action:
        return action, None
    from truncator.execution.device.recovery_gestures import plan_swipe
    if action.get("kind") != "swipe":
        raise ValueError("Recovery target requires a swipe")
    plan = plan_swipe(tree, action["recovery_target"], selector_for(action),
                      action["axis"], action.get("reverse", False))
    if plan["status"] != "planned":
        raise ValueError("Recovery swipe unavailable: " + plan["reason"])
    return {**action, "from": plan["from"], "to": plan["to"]}, plan


def selector_for(action):
    selector = action.get("selector")
    if selector is None:
        selector = {action.get("field", "text"): action["equals"]}
    if (
        not isinstance(selector, dict)
        or not selector
        or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in selector.items()
        )
    ):
        raise ValueError("Recipe selector must contain nonempty attribute criteria")
    return selector


def matches_selector(attributes, action):
    return all(
        attributes.get(key) == value for key, value in selector_for(action).items()
    )


def action_arguments(action, bounds):
    left, top, right, bottom = rectangle(bounds)
    kind = action.get("kind", "click")
    if kind == "click":
        return ["click", str(int((left + right) // 2)), str(int((top + bottom) // 2))]
    if kind != "swipe":
        raise ValueError("Unsupported recipe action " + kind)
    coordinates = []
    for point in (action.get("from", [0.5, 0.8]), action.get("to", [0.5, 0.2])):
        if not isinstance(point, list) or len(point) != 2:
            raise ValueError("Swipe points must be two relative coordinates")
        x, y = [finite(value, "swipe coordinate") for value in point]
        if not 0 < x < 1 or not 0 < y < 1:
            raise ValueError("Swipe coordinates must be inside the selected component")
        coordinates.extend(
            [
                str(round(left + (right - left) * x)),
                str(round(top + (bottom - top) * y)),
            ]
        )
    if coordinates[:2] == coordinates[2:]:
        raise ValueError("Swipe must travel a nonzero distance")
    speed = finite(action.get("speed", 600), "swipe speed")
    if not 200 <= speed <= 40000:
        raise ValueError("uitest swipe speed must be between 200 and 40000")
    return ["swipe", *coordinates, str(round(speed))]


def actionable_nodes(value):
    return [record["attributes"] for record in active_records(value)]


def missing_checks(value, checks):
    current = actionable_nodes(value)
    return [
        check
        for check in checks
        if not any(matches_selector(n, check) for n in current)
    ]
