"""Baseline-only selection and immutable composition of multiple source mutations."""

from truncator.common.capture_files import capture_image

from collections import Counter
import json
import random
from pathlib import Path
from PIL import Image

from truncator.source.binding import active_records, select_record, parent_binding
from truncator.source.source_attributes import numeric_attribute
from truncator.imaging.geometry import rectangle
from truncator.mutation.mutations import mutation_patches
from truncator.mutation.operators import REGISTRY, mutate
from truncator.common.storage import digest, read
from truncator.execution.device.replay import action_arguments, matches_selector
from truncator.planning.pages import resolve_page


def capture_members(plan, recipe):
    if "mutations" not in plan:
        return [plan]
    page = resolve_page(plan, recipe)
    ids = set(page["mutation_ids"]) if page else set()
    return [member for member in plan["mutations"] if member["id"] in ids]


def validate_plan(plan):
    if plan.get("schema_version", 1) >= 2:
        expected = digest(
            json.dumps({k: v for k, v in plan.items() if k != "id"}, sort_keys=True)
        )[:20]
        if plan["id"] != expected:
            raise ValueError("Immutable plan checksum mismatch")
    if "mutations" in plan:
        if not plan["mutations"] and not plan.get("curation"):
            raise ValueError("Combined plan has no mutations")
        for member in plan["mutations"]:
            validate_plan(member)
            if (
                Path(member["source_root"]).resolve()
                != Path(plan["source_root"]).resolve()
            ):
                raise ValueError("Combined mutations belong to different projects")
        patches, hashes = combined_edits(plan["mutations"])
        if patches != plan["patches"] or hashes != plan["file_hashes"]:
            raise ValueError("Combined edits differ from constituent plans")
    else:
        replacement = mutate(plan["site"], plan["operator"], plan["parameters"])
        if replacement != plan["replacement"]:
            raise ValueError("Plan replacement does not match operator")
        if "patches" in plan and mutation_patches(plan) != plan["patches"]:
            raise ValueError("Plan patches do not match operator")


def combined_edits(plans):
    patches, hashes, sites = [], {}, set()
    for plan in plans:
        if plan["site"]["id"] in sites:
            raise ValueError("Multiple mutations at the same source target")
        sites.add(plan["site"]["id"])
        for filename, checksum in plan.get(
            "file_hashes", {plan["site"]["file"]: plan["file_sha256"]}
        ).items():
            if filename in hashes and hashes[filename] != checksum:
                raise ValueError("Mutations use different source revisions")
            hashes[filename] = checksum
        patches.extend(mutation_patches(plan))
    patches.sort(key=lambda edit: (edit["file"], edit["start"], edit["end"]))
    for previous, current in zip(patches, patches[1:]):
        if previous["file"] == current["file"] and (
            current["start"] < previous["end"] or current["start"] == previous["start"]
        ):
            raise ValueError("Combined source patches overlap")
    return patches, hashes


def intersects(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def union(boxes):
    return [
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    ]


def source_conflict(a, b):
    left = [a["site"]] + [r["site"] for r in a.get("related_sites", [])]
    right = [b["site"]] + [r["site"] for r in b.get("related_sites", [])]
    site_conflict = any(
        x["file"] == y["file"]
        and (x["id"] == y["id"] or (x["start"] < y["end"] and y["start"] < x["end"]))
        for x in left
        for y in right
    )
    # State declarations may sit outside both target snippets. Reserve insertions too.
    patch_conflict = any(
        x["file"] == y["file"]
        and (x["start"] == y["start"] or (x["start"] < y["end"] and y["start"] < x["end"]))
        for x in a.get("patches", [])
        for y in b.get("patches", [])
    )
    return site_conflict or patch_conflict


def footprint(plan, records):
    """Reserve a local layout container for reflow, and the whole moved cover."""
    target = select_record(records, plan["geometry"]["selector"])
    box = rectangle(target["attributes"]["bounds"])
    if plan["parameters"].get("preserve_slot") or plan["operator"] in {
        "translate-clip",
        "overlay-occlusion",
    }:
        return box
    boxes = [box]
    if plan["operator"] in {"viewport-width-mismatch", "freeze-viewport-width", "cache-viewport-width"}:
        viewport = plan["geometry"]["parent_bounds_px"]
        boxes.extend([viewport, [viewport[0], viewport[1],
                                 viewport[0] + plan["geometry"]["viewport_width_px"], viewport[3]]])
        if plan["parameters"].get("expand_container"):
            container = next(row for row in plan["related_sites"] if row["role"] == "viewport_parent")
            parent_box = container.get("bounds_px")
            if parent_box is None:
                viewport_record = select_record(records, plan["geometry"]["viewport_selector"])
                viewport_site = next(row["site"] for row in plan["related_sites"] if row["role"] == "viewport")
                _, runtime_parent = parent_binding(
                    {"structural_sites": [container["site"]]}, viewport_site, viewport_record)
                parent_box = rectangle(runtime_parent["attributes"]["bounds"])
            boxes.extend([parent_box, [parent_box[0], parent_box[1],
                                      parent_box[0] + plan["geometry"]["viewport_width_px"], parent_box[3]]])
    if plan["operator"] == "window-edge-clip":
        parent = plan["geometry"]["parent_bounds_px"]
        moving = parent if plan["parameters"].get("move_parent") else box
        dx, dy = plan["geometry"].get("translation_delta_px", [
            plan["parameters"]["x"] * plan["geometry"]["px_per_vp"],
            plan["parameters"]["y"] * plan["geometry"]["px_per_vp"],
        ])
        boxes.extend([parent, [moving[0] + dx, moving[1] + dy,
                               moving[2] + dx, moving[3] + dy]])
    if target["ancestors"]:
        boxes.append(rectangle(target["ancestors"][-1]["attributes"]["bounds"]))
    cover = plan["geometry"].get("occluder_binding")
    if cover:
        cover_box = rectangle(
            select_record(records, cover["selector"])["attributes"]["bounds"]
        )
        parameters = plan["parameters"]
        density = plan["geometry"]["px_per_vp"]
        cover_site = next(
            r["site"] for r in plan["related_sites"] if r["role"] == "occluder"
        )
        if plan["operator"] == "sibling-position-occlusion":
            parent = rectangle(target["ancestors"][-1]["attributes"]["bounds"])
            margin = numeric_attribute(
                cover_site, "margin", ["top", "right", "bottom", "left"]
            )
            x = parent[0] + (parameters["x"] + margin["left"]) * density
            y = parent[1] + (parameters["y"] + margin["top"]) * density
            dx, dy = x - cover_box[0], y - cover_box[1]
        else:
            old = numeric_attribute(cover_site, "translate", ["x", "y"])
            dx = (parameters["x"] - old["x"]) * density
            dy = (parameters["y"] - old["y"]) * density
        moved = [
            cover_box[0] + dx,
            cover_box[1] + dy,
            cover_box[2] + dx,
            cover_box[3] + dy,
        ]
        boxes.extend([cover_box, moved])
    return union(boxes)


def suitability(plan, regions):
    """Prefer mutations whose predicted influence stays local to the target."""
    box = plan["geometry"]["target_bounds_px"]
    target_area = (box[2] - box[0]) * (box[3] - box[1])
    influence = max((b[2] - b[0]) * (b[3] - b[1]) for b in regions.values())
    # A large containing layout makes reflow/ancestor edits less suitable.
    score = min(1.0, 4 * target_area / max(1, influence))
    policy = plan["geometry"].get("automatic", {})
    if plan["site"]["component"] == "Text" and policy.get("basis") == "component":
        score *= 0.8
    if plan["operator"] == "parent-clip":
        # An unpinned child may wrap or shrink with the new parent.
        score *= 0.65
    if plan["operator"] in {"ancestor-translate-clip", "child-overflow-clip"}:
        score *= 0.85
    return score


def navigation_region(action, record):
    box = rectangle(record["attributes"]["bounds"])
    if action.get("kind", "click") != "swipe":
        return box
    coordinates = [float(value) for value in action_arguments(action, box)[1:5]]
    x1, y1, x2, y2 = coordinates
    margin = max(4, min(box[2] - box[0], box[3] - box[1]) * 0.01)
    return [
        min(x1, x2) - margin,
        min(y1, y2) - margin,
        max(x1, x2) + margin,
        max(y1, y2) + margin,
    ]


def select_combination(
    candidates, pages, max_total=12, max_per_page=3, max_area_ratio=0.30, seed=0
):
    if any(
        isinstance(n, bool) or not isinstance(n, int) or n < 1
        for n in (max_total, max_per_page)
    ):
        raise ValueError("Mutation budgets must be positive integers")
    if not 0 < max_area_ratio <= 1:
        raise ValueError("max_area_ratio must be in (0, 1]")
    records = {
        p["name"]: active_records(
            read(Path(p["baseline_capture"]) / "tree-before.json")
        )
        for p in pages
    }
    occupied = {p["name"]: [] for p in pages}
    protected = {}
    navigation_actions = [
        action
        for page in pages
        for action in page["recipe"].get("setup_actions", [])
        + page["recipe"].get("actions", [])
    ]
    screen_areas = {}
    for page in pages:
        name = page["name"]
        with Image.open(capture_image(page["baseline_capture"])) as image:
            screen_areas[name] = image.width * image.height
        protected[name] = [
            navigation_region(action, r)
            for action in navigation_actions
            for r in records[name]
            if matches_selector(r["attributes"], action)
        ]
    rng = random.Random(seed)
    selected, rejected, decisions = [], [], []
    families, operators, components = Counter(), Counter(), Counter()
    remaining = sorted(candidates, key=lambda plan: plan["id"])
    target_order = sorted({p["site"]["id"] for p in candidates})
    rng.shuffle(target_order)
    target_components = {p["site"]["id"]: p["site"]["component"] for p in candidates}
    while remaining and len(selected) < max_total:
        # Balance accepted targets, so rejected icon candidates do not consume a quota.
        target = min(target_order, key=lambda key: components[target_components[key]])
        target_order.remove(target)
        alternatives = [p for p in remaining if p["site"]["id"] == target]
        remaining = [p for p in remaining if p["site"]["id"] != target]
        eligible = []
        for plan in alternatives:
            reason, regions = combination_conflict(
                plan,
                selected,
                records,
                occupied,
                protected,
                screen_areas,
                max_per_page,
                max_area_ratio,
            )
            if reason:
                rejected.append(
                    {
                        "plan": plan["id"],
                        "site": target,
                        "operator": plan["operator"],
                        "reason": reason,
                    }
                )
            else:
                eligible.append((plan, regions, suitability(plan, regions)))
        if not eligible:
            continue
        best_score = max(item[2] for item in eligible)
        shortlist = [item for item in eligible if item[2] >= best_score * 0.8]
        weights = [
            1
            / (
                (1 + operators[p["operator"]])
                * (1 + families[REGISTRY[p["operator"]]["mechanism_family"]])
            )
            for p, _, _ in shortlist
        ]
        plan, regions, score = rng.choices(shortlist, weights=weights, k=1)[0]
        decisions.append(
            {
                "site": target,
                "selected": plan["id"],
                "suitability": score,
                "eligible_operators": [p["operator"] for p, _, _ in shortlist],
                "alternatives": [
                    {
                        "plan": p["id"],
                        "operator": p["operator"],
                        "instance_index": p["parameters"].get("instance_index"),
                        **(
                            {"instance_key": p["parameters"]["instance_key"]}
                            if "instance_key" in p["parameters"]
                            else {}
                        ),
                        "suitability": s,
                        "influence_regions": r,
                    }
                    for p, r, s in eligible
                ],
                "influence_regions": regions,
                "rule": "within 80% of best locality score; seeded inverse-frequency sampling",
            }
        )
        selected.append(plan)
        families[REGISTRY[plan["operator"]]["mechanism_family"]] += 1
        operators[plan["operator"]] += 1
        components[plan["site"]["component"]] += 1
        for name, region in regions.items():
            occupied[name].append(region)
    return selected, {
        "rejected": rejected,
        "unexamined_due_to_total_budget": len(remaining),
        "decisions": decisions,
        "seed": seed,
        "influence_regions": occupied,
        "protected_navigation_regions": protected,
        "operators": dict(operators),
        "mechanism_families": dict(families),
        "components": dict(components),
        "candidate_components": dict(Counter(target_components.values())),
        "balance_policy": "least represented accepted component first; locality and conflict checks remain mandatory",
        "limits": {
            "max_total": max_total,
            "max_per_page": max_per_page,
            "max_area_ratio": max_area_ratio,
        },
    }


def combination_conflict(
    plan,
    selected,
    records,
    occupied,
    protected,
    screen_areas,
    max_per_page,
    max_area_ratio,
):
    reason, regions = None, {}
    if any(source_conflict(plan, other) for other in selected):
        reason = "source_target_or_ancestor_conflict"
    else:
        for name, current in records.items():
            matches = [
                r
                for r in current
                if all(
                    r["attributes"].get(k) == v
                    for k, v in plan["geometry"]["selector"].items()
                )
            ]
            if not matches:
                continue
            if len(matches) != 1:
                reason = "shared_component_has_multiple_runtime_instances"
                break
            region = footprint(plan, current)
            regions[name] = region
            area = sum((b[2] - b[0]) * (b[3] - b[1]) for b in occupied[name] + [region])
            if len(occupied[name]) >= max_per_page:
                reason = "page_mutation_budget"
            elif any(intersects(region, b) for b in occupied[name]):
                reason = "page_influence_regions_overlap"
            elif any(intersects(region, b) for b in protected[name]):
                reason = "navigation_action_region"
            elif area > screen_areas[name] * max_area_ratio:
                reason = "page_influence_area_budget"
            if reason:
                break
    return reason, regions


def compose(plans, pages, selection):
    if not plans:
        raise ValueError("No compatible mutations available")
    patches, hashes = combined_edits(plans)
    page_records = []
    for page in pages:
        records = active_records(
            read(Path(page["baseline_capture"]) / "tree-before.json")
        )
        identifiers = [
            p["id"]
            for p in plans
            if any(
                all(
                    r["attributes"].get(k) == v
                    for k, v in p["geometry"]["selector"].items()
                )
                for r in records
            )
        ]
        page_records.append(
            {
                "name": page["name"],
                "recipe": page["recipe"],
                "baseline_capture": page["baseline_capture"],
                "mutation_ids": identifiers,
            }
        )
    result = {
        "schema_version": 3,
        "source_root": plans[0]["source_root"],
        "mutations": plans,
        "patches": patches,
        "file_hashes": hashes,
        "pages": page_records,
        "selection": selection,
        "review": "pending",
    }
    result["id"] = digest(json.dumps(result, sort_keys=True))[:20]
    validate_plan(result)
    return result
