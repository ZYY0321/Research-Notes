"""Explicit rebuild ancestry, independent of export paths and wall-clock ordering."""

from truncator.common.storage import read
from truncator.planning.composition import validate_plan


def capture_revision(folder, capture):
    """Identify the exact plan + built package; absent provenance stays unlinked."""
    path = folder / "plan.json"
    if not path.exists() or not capture.get("hap_sha256"):
        return None
    plan = read(path)
    if "mutations" not in plan:
        return None
    validate_plan(plan)
    key = plan["id"] + ":" + capture["hap_sha256"]
    ancestors = [entry["plan_id"] + ":" + entry["hap_sha256"]
                 for entry in plan.get("curation", {}).get("ancestors", [])]
    if key in ancestors or len(ancestors) != len(set(ancestors)):
        raise ValueError("Cyclic or repeated rebuild ancestry")
    return {"key": key, "plan_id": plan["id"], "hap_sha256": capture["hap_sha256"],
            "ancestors": ancestors}


def select_revisions(units, revisions, mode):
    if mode not in {"latest", "all"}:
        raise ValueError("Revision mode must be latest or all")
    # A contradictory child must not replace an older reviewed result.
    disputed = {u.get("revision") for u in units if u["consensus"] == "conflicting"}
    eligible = {key: value for key, value in revisions.items() if key not in disputed}
    superseded = {ancestor for value in eligible.values() for ancestor in value["ancestors"]}
    leaves = set(eligible) - superseded
    forks = {}
    for leaf in sorted(leaves):
        for ancestor in eligible[leaf]["ancestors"]:
            forks.setdefault(ancestor, []).append(leaf)
    excluded = [u for u in units if mode == "latest" and u.get("revision") in superseded]
    selected = [u for u in units if mode == "all" or u.get("revision") not in superseded]
    return selected, {
        "mode": mode,
        "versions": [revisions[key] for key in sorted(revisions)],
        "latest_versions": sorted(leaves),
        "superseded_versions": sorted(set(revisions) & superseded),
        "excluded_target_states": [{"export": u["export"], "sample": u["sample"],
                                    "mutation": u["mutation"], "revision": u["revision"]} for u in excluded],
        "branches": {key: values for key, values in sorted(forks.items()) if len(values) > 1},
        "policy": "Only explicit plan-and-HAP ancestry supersedes a version. Keep unrelated batches and all terminal branches; conflicting descendants do not replace ancestors.",
    }
