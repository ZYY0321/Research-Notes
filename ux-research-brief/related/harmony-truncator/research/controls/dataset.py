"""Optional export of archived four-state experiments; reuses core capture validation."""
from pathlib import Path
from truncator.common.storage import read, save, digest
from truncator.review.datasets.dataset import export_capture
from truncator.review.datasets.export_transaction import export_transaction
from research.controls.export import export_control_group

def export_dataset(runs, destination):
    with export_transaction(runs, destination) as staging:
        return _write_group(runs, staging)

def _write_group(runs, destination):
    group_file = Path(runs) / "control-results.json"
    group = read(group_file) if group_file.exists() else None
    group_states = {}
    if group:
        from research.controls.evidence import (
            evidence_identity, validate_interaction, refresh_visual_interactions,
            validate_visual_recovery, validate_control_behavior,
        )
        if not group.get("complete"):
            raise ValueError("Control group has missing states or failed interactions")
        names = [state["state"] for state in group["states"]]
        if len(names) != 4 or set(names) != {"normal", "clipped", "scroll", "whitespace"}:
            raise ValueError("Control export requires four unique states")
        for state in group["states"]:
            identity = evidence_identity(state["capture"])
            if any(identity[key] != state[key] for key in identity):
                raise ValueError("Control group evidence changed")
            folder = Path(state["capture"]).resolve()
            reviews = sorted(folder.glob("review-*.json"))
            if not reviews or read(reviews[-1])["decision"] != "accepted":
                raise ValueError("Every control state requires an accepted review")
            group_states[folder] = state
        for action in group["interactions"]:
            validate_interaction(action)
        refresh_visual_interactions(group)
        labels = {
            state["state"]: read(sorted(folder.glob("review-*.json"))[-1]).get("recovery_status")
            for folder, state in group_states.items()
        }
        validate_control_behavior(group, {
            state for state, label in labels.items()
            if label in {"recovered", "not-recovered"}
        })
        recovered = {state for state, label in labels.items() if label == "recovered"}
        validate_visual_recovery(group, recovered)

    if not group:
        raise ValueError("Expected a historical control-results.json")
    save(destination / "export-status.json", {"complete": False})
    samples = [export_capture(folder, destination) for folder in group_states]
    if any(sample is None for sample in samples):
        raise ValueError("Every control state requires an accepted review")
    manifest = {"schema_version": 1, "applications": [], "samples": samples,
                "split_policy": "Unassigned; group by app/page before evaluation"}
    locations = {folder: digest(str(folder))[:20] for folder in group_states}
    expected = set(locations.values())
    if {sample["id"] for sample in manifest["samples"]} != expected:
        raise ValueError("Control directory must contain exactly its four reviewed states")
    definition_file = Path(runs) / "control-group.json"
    definition = read(definition_file) if definition_file.exists() else {}
    for folder, state in group_states.items():
        sample = next(s for s in manifest["samples"] if s["id"] == locations[folder])
        profile = read(folder.parent / "profile.json")
        sample.update(control_group_id=group["id"], control_state=state["state"],
                      control_axis=group["direction"]["axis"],
                      component=definition.get("selector", {}).get("type", "unknown"),
                      split_group=profile.get("bundle", "unknown") + "/" + definition.get("source_file", "controls"))
    manifest["control_groups"] = [{"id": group["id"], "direction": group["direction"],
                                   "sample_ids": [s["id"] for s in manifest["samples"]]}]
    save(destination / "manifest.json", manifest)
    export_control_group(group, destination, locations)
    save(destination / "export-status.json", {"complete": True, "sample_count": len(samples)})
    return len(samples)
