"""Run and independently recheck bounded swipes on existing injected applications."""

import argparse
from truncator.common.capture_files import capture_image
from pathlib import Path

from truncator.source.binding import active_records, select_record
from truncator.imaging.content_identity import compare_visible
from truncator.imaging.content_transition import measure_transition
from research.controls.evidence import evidence_identity, validate_interaction
from truncator.imaging.geometry import rectangle
from truncator.execution.device.replay import action_arguments, resolve_action
from truncator.execution.device.runtime import capture
from truncator.common.storage import read, save, digest


def target(folder, selector):
    return select_record(active_records(read(Path(folder) / "tree-before.json")), selector)


def measure(initial, current, plan, anchor):
    geometry = plan["geometry"]
    selector = geometry["mutated_selector"]
    row = measure_transition(initial, current, selector=selector,
        viewport_selector=anchor, axis="vertical", geometry=geometry)
    # This comparison checks stability of the injected rendering, not completeness.
    before, after = target(initial, selector), target(current, selector)
    row["injected_render_identity"] = compare_visible(
        capture_image(Path(initial)), capture_image(Path(current)),
        rectangle(before["attributes"]["origBounds"]),
        rectangle(after["attributes"]["origBounds"]), rectangle(after["attributes"]["bounds"]))
    return row


def run(specification, output, device):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    save(output / "specification.json", specification)
    results = []
    for spec in specification:
        application = Path(spec["run"])
        plan_file = application / "plan.json"
        plan, profile = read(plan_file), read(application / "profile.json")
        selector = plan["geometry"]["mutated_selector"]
        row = {"name": spec["name"], "plan": str(plan_file), "plan_sha256": digest(plan_file.read_bytes()),
               "anchor": spec["anchor"], "actions": [], "complete": False}
        results.append(row)
        save(output / "results.json", results)
        try:
            initial = capture(profile, application, device, spec["recipe"], output)
            row["initial"] = evidence_identity(initial)
            select_record(target(initial, selector)["ancestors"], spec["anchor"])
            previous = initial
            for stage, action in spec["actions"]:
                # The same ancestor must still contain the target before dispatch.
                select_record(target(previous, selector)["ancestors"], spec["anchor"])
                recipe = {"checks": [{"selector": selector}], "targets": [{"selector": selector}],
                          "actions": [action], "settle_seconds": 2}
                current = capture(profile, application, device, recipe, output, continue_from=previous)
                entry = {"stage": stage, "action": action, "before": evidence_identity(previous),
                         **evidence_identity(current)}
                validate_interaction(entry)
                entry["measurement"] = measure(initial, current, plan, spec["anchor"])
                entry["replay_sha256"] = digest((current / "replay.json").read_bytes())
                row["actions"].append(entry)
                save(output / "results.json", results)
                print(spec["name"], stage, entry["measurement"]["relative_delta_xy_px"], flush=True)
                previous = current
            row["complete"] = True
        except (ValueError, RuntimeError, OSError, KeyError) as error:
            row["error"] = str(error)
        save(output / "results.json", results)
    return results


def verify(output):
    output = Path(output)
    results, specs = read(output / "results.json"), read(output / "specification.json")
    if len(results) != len(specs):
        raise ValueError("Application list changed")
    verified = []
    for row, spec in zip(results, specs):
        if row["name"] != spec["name"] or row["anchor"] != spec["anchor"]:
            raise ValueError("Trial identity differs from specification")
        plan_file = Path(spec["run"]) / "plan.json"
        if str(plan_file) != row["plan"] or digest(plan_file.read_bytes()) != row["plan_sha256"]:
            raise ValueError("Immutable plan changed")
        if len(row["actions"]) > len(spec["actions"]) or row["complete"] != (len(row["actions"]) == len(spec["actions"])):
            raise ValueError("Trial completion contradicts recorded actions")
        if not row["complete"] and not row.get("error"):
            raise ValueError("Trial has not reached a recorded terminal state")
        if "initial" not in row:
            if row["actions"]:
                raise ValueError("Recorded actions lack an initial capture")
            verified.append({"name": row["name"], "actions_verified": 0,
                             "planned_actions": len(spec["actions"]), "trial_complete": False,
                             "error": row["error"], "same_process": None, "visual_review": "unavailable"})
            continue
        initial = row["initial"]
        if evidence_identity(initial["capture"]) != initial:
            raise ValueError("Initial evidence changed")
        plan = read(plan_file)
        geometry = plan["geometry"]
        baseline = Path(geometry["baseline_capture"])
        for filename, checksum in ((capture_image(baseline).name, geometry["baseline_image_sha256"]),
                                   ("tree-before.json", geometry["baseline_tree_sha256"])):
            if digest((baseline / filename).read_bytes()) != checksum:
                raise ValueError("Planned baseline changed")
        application = Path(spec["run"])
        profile = read(application / "profile.json")
        hap_hash = digest((application / "project" / profile["hap"]).read_bytes())
        if hap_hash != initial["hap_sha256"] or hap_hash != read(application / "build.json")["hap_sha256"]:
            raise ValueError("Trial package differs from built application")
        if read(Path(initial["capture"]) / "capture.json")["recipe"] != spec["recipe"]:
            raise ValueError("Initial route differs from specification")
        selector = plan["geometry"]["mutated_selector"]
        previous = initial
        for entry, (stage, action) in zip(row["actions"], spec["actions"]):
            if entry["stage"] != stage or entry["action"] != action or entry["before"] != previous:
                raise ValueError("Swipe sequence changed")
            validate_interaction(entry)
            folder = Path(entry["capture"])
            before = target(previous["capture"], selector)
            select_record(before["ancestors"], spec["anchor"])
            replay = read(folder / "replay.json")
            if digest((folder / "replay.json").read_bytes()) != entry["replay_sha256"]:
                raise ValueError("Replay log changed")
            if (len(replay) != 1 or replay[0]["status"] != "dispatched"
                or replay[0]["action"] != action or len(replay[0]["matches"]) != 1
                or replay[0]["arguments"] != action_arguments(resolve_action(action, read(folder / "action-before-000.json"))[0], replay[0]["matches"][0]["bounds"])):
                raise ValueError("Swipe dispatch differs from plan")
            located = select_record(active_records(read(folder / "action-before-000.json")), selector)
            anchor = select_record(located["ancestors"], spec["anchor"])
            if anchor["attributes"] != replay[0]["matches"][0]:
                raise ValueError("Gesture anchor is not the target's observed ancestor")
            measured = measure(initial["capture"], folder, plan, spec["anchor"])
            if measured != entry["measurement"]:
                raise ValueError("Saved measurement differs from raw evidence")
            current = target(folder, selector)["attributes"]
            after = select_record(active_records(read(folder / "tree-after.json")), selector)["attributes"]
            if current != after:
                raise ValueError("Target unstable during capture")
            previous = evidence_identity(folder)
        verified.append({"name": row["name"], "actions_verified": len(row["actions"]),
                         "planned_actions": len(spec["actions"]), "trial_complete": row["complete"],
                         "error": row.get("error"), "same_process": True if row["actions"] else None,
                         "visual_review": "pending"})
    save(output / "verification.json", verified)
    return verified


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--spec")
    parser.add_argument("--device", default="127.0.0.1:5555")
    args = parser.parse_args()
    if args.spec:
        run(read(args.spec), args.out, args.device)
    checked = verify(args.out)
    print(checked)
    raise SystemExit(0 if all(row["trial_complete"] for row in checked) else 1)
