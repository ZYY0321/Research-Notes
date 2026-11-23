"""Execute configured route actions once, with bounded observation waits."""

import time
from truncator.execution.device.replay import missing_checks, action_arguments, resolve_action, action_matches
from truncator.common.storage import save, event


def replay_route(recipe, hdc, wait_observation, attempt, run, replay_steps):
    setup_actions = recipe.get("setup_actions", [])
    actions = setup_actions + recipe.get("actions", [])
    for action_index, action in enumerate(actions):
        step = {
            "index": action_index,
            "phase": "setup" if action_index < len(setup_actions) else "route",
            "action": action,
            "status": "locating",
        }
        replay_steps.append(step)
        save(attempt / "replay.json", replay_steps)

        def locate_action(value):
            found = action_matches(value, action)
            identity = [(n.get("id"), n.get("bounds"), n.get("text")) for n in found]
            return len(found) == 1, identity

        current, location_wait = wait_observation(
            locate_action,
            action.get(
                "selector_timeout",
                recipe.get("selector_timeout", 3 if action.get("optional") else 10),
            ),
            recipe.get("poll_interval", 0.5),
            action.get("stable_samples", 2),
            initial=action_index == 0,
        )
        step["location_wait"] = location_wait
        save(attempt / f"action-before-{action_index:03d}.json", current)
        matches = action_matches(current, action)
        step["matches"] = matches
        if not matches and action.get("optional", False):
            step["status"] = "optional_absent"
            save(attempt / "replay.json", replay_steps)
            event(
                run,
                "optional-action-absent",
                action=action,
                attempt=attempt.name,
            )
            continue
        if len(matches) != 1 or not location_wait["ready"]:
            step["status"] = "selector_failed"
            save(attempt / "replay.json", replay_steps)
            raise RuntimeError(
                "Recipe target was absent, ambiguous or unstable at timeout: "
                + str(action)
            )
        try:
            resolved, gesture_plan = resolve_action(action, current)
        except ValueError as error:
            step.update(status="planning_failed", planning_error=str(error))
            save(attempt / "replay.json", replay_steps)
            raise
        if gesture_plan is not None:
            step["gesture_plan"] = gesture_plan
        arguments = action_arguments(resolved, matches[0]["bounds"])
        step.update(status="dispatching", arguments=arguments)
        save(attempt / "replay.json", replay_steps)
        hdc(
            "shell",
            "uitest",
            "uiInput",
            *arguments,
        )
        time.sleep(action.get("wait", 2))
        step["status"] = "dispatched"
        save(attempt / "replay.json", replay_steps)
        if action.get("checks"):

            def check_action(value):
                missing = missing_checks(value, action["checks"])
                return not missing, missing

            after_action, checkpoint_wait = wait_observation(
                check_action,
                action.get("checkpoint_timeout", recipe.get("checkpoint_timeout", 10)),
                recipe.get("poll_interval", 0.5),
            )
            step["checkpoint_wait"] = checkpoint_wait
            save(attempt / f"action-after-{action_index:03d}.json", after_action)
            missing = missing_checks(after_action, action["checks"])
            step.update(
                status="checkpoint_failed" if missing else "checkpoint_passed",
                missing_checks=missing,
            )
            save(attempt / "replay.json", replay_steps)
            if missing:
                raise RuntimeError("Action checkpoint missing: " + str(missing))
