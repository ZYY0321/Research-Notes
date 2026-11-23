"""Portable control action evidence, independent of original run directories."""
import copy
from pathlib import Path

from truncator.common.storage import read, save, digest, contained
from truncator.review.review_evidence import capture_hashes
from research.controls.evidence import validate_interaction, interaction_measurement, validate_control_behavior, validate_visual_recovery
from truncator.planning.composition import validate_plan
from truncator.common.capture_files import evidence_files


def interaction_files(recipe, folder):
    files = set(evidence_files(folder))
    actions = recipe.get("setup_actions", []) + recipe.get("actions", [])
    if actions:
        files.add("replay.json")
    for index, action in enumerate(actions):
        files.add(f"action-before-{index:03d}.json")
        if action.get("checks"):
            files.add(f"action-after-{index:03d}.json")
    return files


def export_control_group(group, destination, locations):
    destination = Path(destination)
    result = {"schema_version": 1, "id": group["id"], "direction": group["direction"],
              "interaction_mode": "continuous_session", "states": [], "interactions": []}
    locations = dict(locations)
    locations.update({Path(action["capture"]).resolve(): f"group-interactions/{index}"
                      for index, action in enumerate(group["interactions"])})

    def relocate(entry):
        return {**entry, "capture": locations[Path(entry["capture"]).resolve()],
                "source_capture": entry["capture"]}

    result["states"] = [relocate(state) for state in group["states"]]
    for action in group["interactions"]:
        source = Path(action["capture"])
        exported = relocate(action)
        exported["before"] = relocate(action["before"])
        target = contained(destination, exported["capture"])
        target.mkdir(parents=True)
        recipe = read(source / "capture.json").get("recipe", {})
        files = interaction_files(recipe, source)
        exported["evidence_files"] = {}
        for name in sorted(files):
            data = (source / name).read_bytes()
            checksum = digest(data)
            if name in action["sha256"] and checksum != action["sha256"][name]:
                raise ValueError("Control interaction changed during export")
            (target / name).write_bytes(data)
            exported["evidence_files"][name] = checksum
        result["interactions"].append(exported)
    save(destination / "control-group.json", result)


def verify_control_group(root, manifest):
    """Recheck local observations, dispatch and recovery; never read source paths."""
    root = Path(root)
    declarations = manifest.get("control_groups", [])
    if not declarations:
        if any(sample.get("control_group_id") for sample in manifest["samples"]):
            raise ValueError("Control samples lack their group declaration")
        return
    group = read(root / "control-group.json")
    if group.get("schema_version") != 1:
        raise ValueError("Control export lacks portable action evidence; export again")
    if len(declarations) != 1 or declarations[0]["id"] != group["id"] or declarations[0]["direction"] != group["direction"]:
        raise ValueError("Control group declaration changed")
    samples = {sample["control_state"]: sample for sample in manifest["samples"]}
    states = {state["state"]: state for state in group["states"]}
    if len(group["states"]) != 4 or set(states) != {"normal", "clipped", "scroll", "whitespace"} or set(samples) != set(states):
        raise ValueError("Portable control group requires four unique states")
    if set(declarations[0]["sample_ids"]) != {s["id"] for s in samples.values()}:
        raise ValueError("Control group sample membership changed")
    labels = {}
    for name, state in states.items():
        sample = samples[name]
        if state["capture"] != sample["id"] or sample["control_group_id"] != group["id"] or sample["control_axis"] != group["direction"]["axis"]:
            raise ValueError("Control state identity changed")
        folder = contained(root, state["capture"])
        if capture_hashes(folder) != state["sha256"]:
            raise ValueError("Portable control initial evidence changed")
        labels[name] = read(folder / "review.json").get("recovery_status")
    for action in group["interactions"]:
        folder = contained(root, action["capture"])
        if set(action["evidence_files"]) != interaction_files(read(folder / "capture.json").get("recipe", {}), folder):
            raise ValueError("Portable action evidence inventory is incomplete")
        for filename, checksum in action["evidence_files"].items():
            if digest(contained(folder, filename).read_bytes()) != checksum:
                raise ValueError("Portable action evidence changed")
        validate_interaction(action, root=root)
        initial = contained(root, states[action["state"]]["capture"])
        plan = read(initial / "plan.json")
        validate_plan(plan)
        plan = copy.deepcopy(plan)
        plan["geometry"]["baseline_capture"] = str(initial / "baseline")
        action["measurement"] = interaction_measurement(initial, folder, plan)
        before = contained(root, action["before"]["capture"])
        action["action_measurement"] = action["measurement"] if before == initial else interaction_measurement(before, folder, plan)
    validate_control_behavior(group, {name for name, label in labels.items() if label in {"recovered", "not-recovered"}})
    validate_visual_recovery(group, {name for name, label in labels.items() if label == "recovered"})
