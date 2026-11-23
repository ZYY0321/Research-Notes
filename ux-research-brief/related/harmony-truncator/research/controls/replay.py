"""Recheck archived control interactions from saved dispatch evidence."""
from pathlib import Path
from truncator.common.storage import read
from truncator.execution.device.replay import action_matches, resolve_action, action_arguments, missing_checks


def verify_interaction_replay(folder, recipe):
    """Reconstruct executed interaction coordinates from pre-action observations.

    A recipe alone is not evidence of dispatch. Recovery actions must have run;
    an absent optional setup action may be skipped with its empty observation.
    """
    setup = recipe.get("setup_actions", [])
    actions = setup + recipe.get("actions", [])
    if not actions:
        return
    folder = Path(folder)
    try:
        steps = read(folder / "replay.json")
        if len(steps) != len(actions):
            raise ValueError("Interaction replay action count differs from recipe")
        for index, (action, step) in enumerate(zip(actions, steps)):
            phase = "setup" if index < len(setup) else "route"
            if step.get("index") != index or step.get("phase") != phase or step.get("action") != action:
                raise ValueError("Interaction replay order or action differs from recipe")
            tree = read(folder / f"action-before-{index:03d}.json")
            matches = action_matches(tree, action)
            if step.get("matches") != matches:
                raise ValueError("Interaction replay target differs from pre-action tree")
            if phase == "setup" and action.get("optional") and not matches and step.get("status") == "optional_absent":
                continue
            if len(matches) != 1 or not step.get("location_wait", {}).get("ready"):
                raise ValueError("Interaction replay target was absent, ambiguous or unstable")
            if step.get("status") not in {"dispatched", "checkpoint_passed"}:
                raise ValueError("Interaction replay does not prove dispatch")
            resolved, plan = resolve_action(action, tree)
            if step.get("gesture_plan") != plan:
                raise ValueError("Interaction gesture plan differs from pre-action tree")
            if step.get("arguments") != action_arguments(resolved, matches[0]["bounds"]):
                raise ValueError("Interaction replay coordinates differ from observed target")
            if action.get("checks"):
                if (step.get("status") != "checkpoint_passed"
                    or not step.get("checkpoint_wait", {}).get("ready")
                    or missing_checks(read(folder / f"action-after-{index:03d}.json"), action["checks"])):
                    raise ValueError("Interaction replay checkpoint is unverified")
    except OSError as error:
        raise ValueError("Interaction replay evidence is missing or unreadable") from error
