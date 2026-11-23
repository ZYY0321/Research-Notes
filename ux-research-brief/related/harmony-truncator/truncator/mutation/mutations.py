"""Deterministic mutation plans and patch generation, without project execution."""

import json
import random
from truncator.common.storage import digest
from truncator.mutation.operators import (
    mutate,
    REGISTRY,
)
from truncator.mutation.source_edits import attribute_edits, vector, reject_layout_conflicts
from truncator.common.validation import finite, positive
from truncator.mutation.viewport_cache import cache_patches


def plans(catalog, seed, count, operator, parameters, file_filter="", site_id=None):
    candidates = sorted(
        [
            s
            for s in catalog["sites"]
            if operator in s["operators"]
            and (
                not s["repeated"]
                or (
                    s.get("probe")
                    and ("instance_index" in parameters or "instance_key" in parameters)
                )
            )
            and file_filter in s["file"]
            and (site_id is None or s["id"] == site_id)
        ],
        key=lambda s: s["id"],
    )
    if count < 1 or count > len(candidates):
        raise ValueError(
            "Requested count exceeds applicable unique sites: " + str(len(candidates))
        )
    rng = random.Random(seed)
    selected = rng.sample(candidates, count)
    result = []
    for site in selected:
        sampled = {
            key: rng.choice(value) if isinstance(value, list) else value
            for key, value in parameters.items()
        }
        replacement = mutate(site, operator, sampled)
        plan = {
            "schema_version": 1,
            "seed": seed,
            "operator": operator,
            "parameters": sampled,
            "parameter_domain": parameters,
            "site": site,
            "source_root": catalog["root"],
            "catalog_sha256": digest(json.dumps(catalog, sort_keys=True)),
            "file_sha256": catalog["files"][site["file"]],
            "replacement": replacement,
            "max_source_sites": 1,
            "review": "pending",
            "instance_budget": 1,
        }
        if "construction_intent" in REGISTRY[operator]:
            plan["construction_intent"] = REGISTRY[operator]["construction_intent"]
            plan["outcome"] = "unverified"
        plan["id"] = digest(json.dumps(plan, sort_keys=True))[:20]
        result.append(plan)
    return result


def mutation_patches(plan):
    site = plan["site"]
    replacement = mutate(site, plan["operator"], plan["parameters"])
    roles = [r["role"] for r in plan.get("related_sites", [])]
    required = REGISTRY[plan["operator"]].get("related_role")
    if plan["operator"] == "window-edge-clip" and plan["parameters"].get("move_parent"):
        required = "window_parent"
    expected_roles = [required] if required else []
    if plan["operator"] in {"viewport-width-mismatch", "freeze-viewport-width"} and plan["parameters"].get("expand_container"):
        expected_roles.append("viewport_parent")
    if roles != expected_roles:
        raise ValueError(
            "Operator related sites must be "
            + str(expected_roles)
            + "; use geometry-plan"
        )
    edits = []
    if replacement != site["snippet"]:
        # A repeated-instance rewrite is an if/else statement, not an expression.
        # Consume only the scanned statement terminator; retain intervening comments.
        suffix = site.get("statement_suffix", "") if site["repeated"] else ""
        if suffix and not suffix.endswith(";"):
            raise ValueError("Invalid source statement terminator")
        edits.append(
            {
                "file": site["file"],
                "start": site["start"],
                "end": site["end"] + len(suffix),
                "before": site["snippet"] + suffix,
                "after": replacement + suffix[:-1],
            }
        )
    for related in plan.get("related_sites", []):
        other = related["site"]
        if other["repeated"] or digest(other["snippet"]) != other["sha256"]:
            raise ValueError("Invalid or repeated related source site")
        p = plan["parameters"]
        if plan["operator"] == "cache-viewport-width" and related["role"] == "viewport":
            edits.extend(cache_patches(other))
            continue
        if related["role"] == "clipping_parent":
            desired = {"clip": "true"}
            if p.get("freeze_parent"):
                reject_layout_conflicts(
                    other,
                    {
                        key: value
                        for key, value in p.items()
                        if key != "resolved_aspect_ratio"
                    },
                )
                desired.update(
                    width=str(positive(p["parent_width"], "parent_width")),
                    height=str(positive(p["parent_height"], "parent_height")),
                )
        elif related["role"] in {"viewport", "viewport_parent"}:
            reject_layout_conflicts(other, p)
            desired = {"width": str(positive(p["viewport_width"], "viewport_width"))}
        elif related["role"] == "window_parent":
            reject_layout_conflicts(other, p)
            desired = {"translate": vector(p["x"], p["y"])}
        elif related["role"] == "occluder":
            reject_layout_conflicts(other, p)
            name = (
                "position"
                if plan["operator"] == "sibling-position-occlusion"
                else "translate"
            )
            desired = {
                name: vector(p["x"], p["y"]),
                "zIndex": str(finite(p["z_index"], "z_index")),
            }
        else:
            raise ValueError("Unknown related site role")
        for start, end, value in attribute_edits(other, desired):
            edits.append(
                {
                    "file": other["file"],
                    "start": start,
                    "end": end,
                    "before": other["snippet"][
                        start - other["start"] : end - other["start"]
                    ],
                    "after": value,
                }
            )
    return edits


def apply_patches(original, edits):
    ordered = sorted(edits, key=lambda e: (e["start"], e["end"]))
    previous_end = -1
    previous_start = -1
    for edit in ordered:
        start, end = edit["start"], edit["end"]
        if (
            start < previous_end
            or start == previous_start
            or start < 0
            or end < start
            or end > len(original)
        ):
            raise ValueError("Overlapping or invalid patch intervals")
        if original[start:end] != edit["before"]:
            raise ValueError("Source snippet changed since plan")
        previous_start, previous_end = start, end
    for edit in reversed(ordered):
        original = original[: edit["start"]] + edit["after"] + original[edit["end"] :]
    return original
