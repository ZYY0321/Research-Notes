"""Choose target-adjacent swipe tracks that avoid observed clickable regions."""
from truncator.source.binding import active_records, select_record
from truncator.imaging.geometry import rectangle


def plan_swipe(tree, target_selector, viewport_selector, axis, reverse=False):
    if axis not in {"horizontal", "vertical"}:
        raise ValueError("Recovery swipe axis must be horizontal or vertical")
    records = active_records(tree)
    target = select_record(records, target_selector)
    viewport = select_record(target["ancestors"], viewport_selector)
    bounds = rectangle(viewport["attributes"]["bounds"])
    box = rectangle(target["attributes"]["bounds"])
    along = 0 if axis == "horizontal" else 1
    across = 1 - along
    # Pixel margins are explicit planning heuristics, not platform touch slop.
    margin, nearby, minimum = 8, 32, 48
    screen = rectangle(records[0]["attributes"]["bounds"])
    screen_inset = max(24, min(96, round(min(screen[2]-screen[0], screen[3]-screen[1]) * .05)))
    safe = [max(bounds[i] + margin, screen[i] + screen_inset) for i in (0, 1)] + [
        min(bounds[i + 2] - margin, screen[i + 2] - screen_inset) for i in (0, 1)]
    lo, hi = safe[along], safe[along + 2]
    cross_lo = max(safe[across], box[across] - nearby)
    cross_hi = min(safe[across + 2], box[across + 2] + nearby)
    center = (box[along] + box[along + 2]) / 2
    cross_center = (box[across] + box[across + 2]) / 2
    visibility_budget = (bounds[along + 2] - box[along] - margin if reverse
                         else box[along + 2] - bounds[along] - margin)
    blockers = []
    for record in records:
        attrs = record["attributes"]
        if attrs.get("clickable") != "true" or attrs.get("visible") == "false":
            continue
        try:
            rect = rectangle(attrs["bounds"])
        except ValueError:
            continue
        blockers.append(rect)
    lanes = {round(max(cross_lo, min(cross_hi, cross_center))), round(cross_lo), round(cross_hi)}
    for rect in blockers:
        lanes.update((rect[across] - margin - 1, rect[across + 2] + margin + 1))
    candidates = []
    for lane in sorted(lanes):
        if not cross_lo <= lane <= cross_hi:
            continue
        intervals = [(lo, hi)]
        for rect in blockers:
            if rect[across] - margin <= lane <= rect[across + 2] + margin:
                start, end = rect[along] - margin, rect[along + 2] + margin
                intervals = [(a, b) for left, right in intervals for a, b in
                             ((left, min(right, start - 1)), (max(left, end + 1), right)) if b > a]
        for left, right in intervals:
            if right - left < minimum or visibility_budget < minimum:
                continue
            distance = max(left - box[along + 2], box[along] - right, 0)
            if distance > nearby:
                continue
            travel = min(visibility_budget, max(minimum, min(right - left, (hi - lo) * .6)))
            mid = max(left + travel / 2, min(right - travel / 2, center))
            candidates.append((abs(lane - cross_center) + distance, -travel, lane,
                               round(mid - travel / 2), round(mid + travel / 2)))
    result = {"axis": axis, "target_bounds": box, "viewport_bounds": bounds,
              "screen_bounds": screen, "screen_inset_px": screen_inset,
              "visibility_budget_px": visibility_budget,
              "margin_px": margin, "nearby_px": nearby, "minimum_distance_px": minimum,
              "clickable_regions": blockers}
    if not candidates:
        return {**result, "status": "unavailable", "reason": "no_target_adjacent_click_free_track"}
    _, _, lane, low, high = min(candidates)
    start, end = [0, 0], [0, 0]
    start[across] = end[across] = lane
    start[along], end[along] = (low, high) if reverse else (high, low)
    def relative(point):
        return [(point[i] - bounds[i]) / (bounds[i + 2] - bounds[i]) for i in (0, 1)]
    return {**result, "status": "planned", "from": relative(start), "to": relative(end),
            "pixel_from": start, "pixel_to": end}
