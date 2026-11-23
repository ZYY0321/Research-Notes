"""Offline control measurements, review rendering and review submission."""

from truncator.common.capture_files import capture_image

from pathlib import Path
from truncator.common.storage import read, save, digest, contained
from truncator.common.locking import lock
from truncator.review.review_evidence import capture_hashes
from research.controls.replay import verify_interaction_replay


def evidence_identity(capture):
    folder = Path(capture)
    hashes = capture_hashes(folder)
    record = read(folder / "capture.json")
    return {
        "capture": str(folder.resolve()),
        "sha256": hashes,
        "hap_sha256": record.get("hap_sha256"),
    }


def directional_swipe(selector, axis, reverse=False):
    if axis not in {"horizontal", "vertical"}:
        raise ValueError("Unknown swipe axis")
    start, end = (
        ([0.85, 0.5], [0.15, 0.5])
        if axis == "horizontal"
        else ([0.5, 0.85], [0.5, 0.15])
    )
    if reverse:
        start, end = end, start
    return {
        "kind": "swipe",
        "selector": selector,
        "from": start,
        "to": end,
        "speed": 400,
        "wait": 2,
    }


def validate_interaction(action, *, root=None):
    """Bind each movement to its exact preceding frame and live process."""
    current_path = contained(root, action["capture"]) if root is not None else Path(action["capture"])
    previous_path = contained(root, action["before"]["capture"]) if root is not None else Path(action["before"]["capture"])
    current = evidence_identity(current_path)
    previous = evidence_identity(previous_path)
    if root is not None:
        current["capture"] = action["capture"]
        previous["capture"] = action["before"]["capture"]
    if (
        any(current[key] != action[key] for key in current)
        or any(previous[key] != action["before"][key] for key in previous)
    ):
        raise ValueError("Control interaction evidence changed")
    record = read(current_path / "capture.json")
    prior_record = read(previous_path / "capture.json")
    declared = action.get("actions")
    if declared is None and "action" in action:
        declared = [action["action"]]
    if declared is not None and declared != record.get("recipe", {}).get("actions"):
        raise ValueError("Declared interaction differs from captured recipe actions")
    if (
        record.get("continued_from")
        != {
            "capture": action["before"]["source_capture"] if root is not None else previous["capture"],
            "capture_sha256": previous["sha256"]["capture.json"],
        }
        or current["hap_sha256"] != previous["hap_sha256"]
        or record.get("session", {}).get("status") != "verified"
        or record["session"] != prior_record.get("session")
    ):
        raise ValueError("Control action must continue the preceding capture session")
    verify_interaction_replay(current_path, record.get("recipe", {}))


def interaction_measurement(initial, current, plan):
    from truncator.imaging.content_transition import measure_transition

    return measure_transition(
        initial, current,
        selector=plan["geometry"]["mutated_selector"],
        viewport_selector={"id": plan["parameters"]["viewport_id"]},
        axis=plan["control_group"]["axis"], geometry=plan["geometry"],
    )


def refresh_visual_interactions(result):
    """Recompute content identity and 2D coverage from the saved action evidence."""
    from truncator.planning.composition import validate_plan

    states = {s["state"]: s for s in result["states"]}
    for action in result["interactions"]:
        plan_file = Path(action["capture"]).parent / "plan.json"
        if not plan_file.exists():
            raise ValueError("Control action lacks its immutable source plan")
        plan = read(plan_file)
        validate_plan(plan)
        action["measurement"] = interaction_measurement(
            states[action["state"]]["capture"], action["capture"], plan
        )
        action["action_measurement"] = (
            action["measurement"]
            if action["before"]["capture"] == states[action["state"]]["capture"]
            else interaction_measurement(
                action["before"]["capture"], action["capture"], plan
            )
        )
    return result


def validate_visual_recovery(result, recovered_states):
    for state in recovered_states:
        if (
            len(
                [
                    a
                    for a in result["interactions"]
                    if a["state"] == state and a["stage"] == "forward"
                ]
            )
            != 1
        ):
            raise ValueError(
                "Recovered state requires exactly one forward action record"
            )
    for action in result["interactions"]:
        measurement = action.get("measurement", {})
        if action["state"] in recovered_states and action["stage"] == "forward":
            coverage = measurement.get("foreground_coverage", {})
            if (
                coverage.get("status") != "covered"
                or not measurement.get("same_extent")
                or not measurement.get("same_content")
            ):
                raise ValueError(
                    "Recovered state lacks complete two-dimensional foreground coverage"
                )
        observations = measurement.get("observations", [])
        if (
            action["state"] in recovered_states
            and action["stage"] == "forward"
            and observations
            and observations[0]["type"] in {"Image", "SymbolGlyph"}
        ):
            if measurement.get(
                "content_identity_basis"
            ) != "visible_pixels_against_baseline" or not measurement.get(
                "same_content"
            ):
                raise ValueError(
                    "Nontext recovery content is different or unverified; cannot accept recovery"
                )


def validate_control_behavior(result, claimed_states):
    """Check directional isolation and restoration for accepted action-based labels.

    Two pixels allow integer layout rounding, matching the extent comparison.
    A successful command or unchanged PID alone does not establish these properties.
    """
    axis = result["direction"]["axis"]
    along = 0 if axis == "horizontal" else 1
    if axis not in {"horizontal", "vertical"}:
        raise ValueError("Unknown control direction")
    states = {state["state"]: state for state in result["states"]}
    for state in claimed_states:
        actions = [a for a in result["interactions"] if a["state"] == state]
        expected = ["forward", "orthogonal", "return"] if state == "scroll" else ["forward"]
        if [a["stage"] for a in actions] != expected:
            raise ValueError("Control interaction sequence is incomplete or reordered")
        previous = states[state]["capture"]
        for action in actions:
            if action.get("status") != "captured" or action["before"]["capture"] != previous:
                raise ValueError("Control interaction does not continue the preceding stage")
            previous = action["capture"]
            gestures = action.get("actions", [])
            if len(gestures) != 1 or gestures[0].get("kind") != "swipe":
                raise ValueError("Control stage requires exactly one swipe")
            gesture = gestures[0]
            delta = [gesture["to"][i] - gesture["from"][i] for i in (0, 1)]
            moving = 1-along if action["stage"] == "orthogonal" else along
            sign = 1 if action["stage"] == "return" else -1
            if delta[1-moving] != 0 or delta[moving] * sign <= 0:
                raise ValueError("Control gesture disagrees with planned axis or direction")
            measurement = action["measurement"]
            step = action["action_measurement"]
            if not all(m.get("same_content") and m.get("same_extent") for m in (measurement, step)):
                raise ValueError("Control gesture changed content identity or extent")
            relative = measurement["relative_delta_xy_px"]
            if any(abs(v) > 2 for v in measurement["viewport_delta_xy_px"]):
                raise ValueError("Control viewport moved; target motion is confounded")
            if state == "clipped":
                if any(abs(v) > 2 for v in relative):
                    raise ValueError("Fixed control moved during its recovery probe")
                if measurement.get("foreground_coverage", {}).get("status") != "incomplete":
                    raise ValueError("Unrecovered fixed control lacks measured missing content")
            elif action["stage"] == "forward":
                if relative[along] >= -2 or abs(relative[1-along]) > 2:
                    raise ValueError("Scroll control did not move along its intended axis")
            elif action["stage"] == "orthogonal":
                if any(abs(v) > 2 for v in step["relative_delta_xy_px"]):
                    raise ValueError("Orthogonal swipe interfered with the control state")
            elif any(abs(v) > 2 for v in relative):
                raise ValueError("Return swipe did not restore the initial control position")


def write_group_review(output, result):
    from truncator.review.reporting.report_assets import document, escaped, json_block

    output = Path(output)
    body = '<p>按同一目标检查正常、裁切、滚动和留白状态。标签等待审核。</p><p><a href="review-template.json">当前采集的审核空模板</a></p>'
    if result.get("behavior_checks"):
        body += "<h2>方向、恢复与回位检查</h2>" + json_block(result["behavior_checks"])
    template = {
        "group_id": result["id"],
        "reviewer": "",
        "independent_review": True,
        "states": [],
    }
    for state in result["states"]:
        body += "<section><h2>" + escaped(state["state"]) + "</h2>"
        if state["status"] == "captured":
            folder = Path(state["capture"])
            body += (
                '<a href="'
                + folder.as_uri()
                + '">原始图树</a><p><img style="max-width:100%;max-height:600px" src="'
                + (capture_image(folder)).as_uri()
                + '"></p>'
            )
            template["states"].append(
                {
                    "state": state["state"],
                    "capture": state["capture"],
                    "sha256": state["sha256"],
                    "content_status": "uncertain",
                    "recovery_status": "not-tested",
                    "decision": "needs-review",
                    "reason": "",
                }
            )
        else:
            body += json_block(state)
        for action in result["interactions"]:
            if action["state"] == state["state"]:
                body += (
                    "<h3>"
                    + escaped(action["stage"])
                    + "</h3>"
                    + json_block(action.get("measurement", action))
                )
                if "action_measurement" in action:
                    body += "<h4>本次动作前后变化</h4>" + json_block(
                        action["action_measurement"]
                    )
                if action.get("capture"):
                    body += (
                        '<a href="'
                        + (capture_image(action["capture"])).as_uri()
                        + '">动作后原图</a>'
                    )
        body += "</section>"
    (output / "control-review.html").write_text(
        document("成组对照审核", body), encoding="utf-8"
    )
    save(output / "review-template.json", template)
    # Keep an independently filled review intact when a run is resumed.
    if not (output / "independent-review.json").exists():
        save(output / "independent-review.json", template)


def apply_group_review(destination, review_file):
    """Validate a complete review against its exact captures before applying it."""
    from truncator.review.review_policy import validate_observation_labels
    from truncator.execution.workflow import review

    output = Path(destination)
    submitted = read(review_file)
    result = read(output / "control-results.json")
    if not result.get("complete"):
        raise ValueError(
            "Complete the four-state group and its interactions before applying a group review"
        )
    if (
        submitted["group_id"] != result["id"]
        or not submitted.get("reviewer", "").strip()
    ):
        raise ValueError("Review needs the matching group ID and a named reviewer")
    states = {state["state"]: state for state in result["states"]}
    entries = submitted["states"]
    if len(entries) != len(states) or {entry["state"] for entry in entries} != set(
        states
    ):
        raise ValueError("Review must cover every state exactly once")
    for entry in entries:
        state = states[entry["state"]]
        identity = evidence_identity(entry["capture"])
        if (
            identity["capture"] != state["capture"]
            or identity["sha256"] != state["sha256"]
            or identity["sha256"] != entry["sha256"]
        ):
            raise ValueError("Review capture identity changed")
        validate_observation_labels(entry["content_status"], entry["recovery_status"])
        if (
            entry["decision"] not in {"accepted", "rejected", "needs-review"}
            or not entry["reason"].strip()
        ):
            raise ValueError(
                "Each state needs a supported decision and its evidence reason"
            )
    for action in result["interactions"]:
        validate_interaction(action)
    refresh_visual_interactions(result)
    validate_control_behavior(result, {
        entry["state"] for entry in entries
        if entry["decision"] == "accepted"
        and entry["recovery_status"] in {"recovered", "not-recovered"}
    })
    validate_visual_recovery(
        result,
        {
            e["state"]
            for e in entries
            if e["decision"] == "accepted" and e["recovery_status"] == "recovered"
        },
    )
    records = []
    with lock(output / "control-review.lock"):
        for entry in entries:
            evidence = [
                action["capture"]
                for action in result["interactions"]
                if action["state"] == entry["state"]
            ]
            record = review(
                entry["capture"],
                entry["decision"],
                submitted["reviewer"],
                entry["reason"],
                [],
                content_status=entry["content_status"],
                recovery_status=entry["recovery_status"],
                evidence_captures=evidence,
            )
            records.append({"state": entry["state"], "review": str(record)})
        save(
            output / "group-review-record.json",
            {
                "group_id": result["id"],
                "submitted_review": str(Path(review_file).resolve()),
                "submitted_sha256": digest(Path(review_file).read_bytes()),
                "records": records,
                "reviewer": submitted["reviewer"],
                "independent_review": submitted.get("independent_review", False),
            },
        )
    return records
