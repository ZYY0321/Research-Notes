"""Physical display context used to prevent cross-posture capture reuse."""

import re


def display_context(dump):
    dimensions = set(
        re.findall(r"\[DISPLAY INFO\]\s+Width:\s+(\d+)\s+Height:\s+(\d+)", dump)
    )
    densities = set(re.findall(r"^VirtualPixelRatio:\s+([\d.]+)", dump, re.MULTILINE))
    folds = set(re.findall(r"^DisplayFoldStatus:\s+(\w+)", dump, re.MULTILINE))
    if len(dimensions) != 1 or len(densities) != 1 or len(folds) > 1:
        return None
    width, height = next(iter(dimensions))
    return {
        "screen_size": [int(width), int(height)],
        "px_per_vp": float(next(iter(densities))),
        "fold_status": next(iter(folds), None),
    }
