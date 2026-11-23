"""Pure pixel-space geometry. No filesystem, SDK or device dependencies."""

import re
from truncator.common.validation import positive, finite

EDGES = ("left", "right", "top", "bottom")


def rectangle(value):
    if isinstance(value, str):
        if not re.fullmatch(r"\[-?\d+,-?\d+\]\[-?\d+,-?\d+\]", value):
            raise ValueError("Invalid dump rectangle: " + value)
        value = list(map(int, re.findall(r"-?\d+", value)))
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("Rectangle requires four coordinates")
    x0, y0, x1, y1 = value
    for coordinate in value:
        finite(coordinate, "coordinate")
    positive(x1 - x0, "rectangle width")
    positive(y1 - y0, "rectangle height")
    return list(value)


def crossing_translation(target, parent, edge, penetration):
    target, parent = rectangle(target), rectangle(parent)
    positive(penetration, "penetration_px")
    if edge == "left":
        return parent[0] - target[0] - penetration, 0
    if edge == "right":
        return parent[2] - target[2] + penetration, 0
    if edge == "top":
        return 0, parent[1] - target[1] - penetration
    if edge == "bottom":
        return 0, parent[3] - target[3] + penetration
    raise ValueError("Unknown edge")


def overlap_translation(target, cover, edge, penetration):
    target, cover = rectangle(target), rectangle(cover)
    positive(penetration, "penetration_px")
    cx = (target[0] + target[2] - cover[0] - cover[2]) / 2
    cy = (target[1] + target[3] - cover[1] - cover[3]) / 2
    if edge == "top":
        return cx, target[1] + penetration - cover[3]
    if edge == "bottom":
        return cx, target[3] - penetration - cover[1]
    if edge == "left":
        return target[0] + penetration - cover[2], cy
    if edge == "right":
        return target[2] - penetration - cover[0], cy
    raise ValueError("Unknown edge")
