"""Device capture lifecycle and completed-capture reuse."""

from truncator.common.capture_files import capture_image

from pathlib import Path
import json
import re
import time
import tempfile
from truncator.common.storage import save, read, event, digest
from truncator.common.locking import lock
from truncator.execution.device.replay import actionable_nodes, missing_checks, matches_selector
from truncator.execution.device.route_runner import replay_route
from truncator.execution.device.commands import command
from truncator.review.observation import record_observations
from truncator.source.binding import active_records, select_record
from truncator.execution.device.waiting import wait_for_tree
from truncator.execution.device.device_context import display_context
from truncator.execution.device.startup import (
    start_application,
    retry_exited_application,
    validate_startup,
    process_identity,
    continuing_session,
)
from truncator.planning.pages import resolve_page, page_id
from truncator.execution.device.capture_policy import CURRENT_CAPTURE_POLICY, current_capture
from truncator.planning.composition import capture_members


def latest_capture(run, device, recipe, *, force=False):
    """Find the most recent completed capture matching the replay inputs."""
    if force:
        return None
    current_context = None
    profile_path = Path(run) / "profile.json"
    if profile_path.exists() and read(profile_path).get("hdc"):
        profile = read(profile_path)
        try:
            output, _ = command(
                [
                    profile["hdc"],
                    "-t",
                    device,
                    "shell",
                    "hidumper",
                    "-s",
                    "DisplayManagerService",
                    "-a",
                    "-a",
                ],
                Path(run) / ("reuse-context-" + str(time.time_ns()) + ".log"),
                timeout=60,
            )
            current_context = display_context(output)
        except (RuntimeError, OSError):
            return None
        if current_context is None:
            return None
    for path in sorted(Path(run).glob("capture-*/capture.json"), reverse=True):
        record = read(path)
        if record.get("continued_from"):
            continue
        if not current_capture(record):
            continue
        if record.get("device") == device and record.get("recipe") == recipe:
            build_path = Path(run) / "build.json"
            if (
                build_path.exists()
                and record.get("hap_sha256") is not None
                and record.get("hap_sha256") != read(build_path)["hap_sha256"]
            ):
                continue
            if (
                current_context is not None
                and record.get("display_context") != current_context
            ):
                continue
            return path.parent
    return None


def capture(profile, run, device, recipe, output_root, *, continue_from=None):
    run = Path(run).resolve()
    validate_startup(recipe)
    if read(run / "profile.json") != profile:
        raise ValueError("Capture profile differs from prepared run")
    saved_plan = read(run / "plan.json") if (run / "plan.json").exists() else None
    active_plans = capture_members(saved_plan, recipe) if saved_plan else []
    capture_page = (
        resolve_page(saved_plan, recipe)
        if saved_plan and "pages" in saved_plan
        else None
    )
    lock_root = Path(tempfile.gettempdir()) / "harmony-truncator" / "locks"
    with lock(lock_root / ("device-" + digest(device)[:16] + ".lock")):
        attempt = run / (
            "capture-"
            + time.strftime("%Y%m%d-%H%M%S")
            + "-"
            + str(time.time_ns() % 1000000)
        )
        attempt.mkdir()
        counter = 0
        replay_steps = []
        device_ready = False

        def hdc(*args, timeout=60):
            nonlocal counter
            counter += 1
            result, meta = command(
                [profile["hdc"], "-t", device, *args],
                attempt / f"command-{counter:03d}.log",
                timeout=timeout,
            )
            event(run, "device-command", args=list(args), attempt=attempt.name, **meta)
            return result

        def tree():
            remote = "/data/local/tmp/truncator-" + digest(str(attempt))[:12] + ".json"
            for retry in range(3):
                output = hdc("shell", "uitest", "dumpLayout", "-p", remote)
                if "DumpLayout saved" in output:
                    return json.loads(hdc("shell", "cat", remote))
                time.sleep(2)
            raise RuntimeError("dumpLayout failed after three attempts: " + output)

        def wait_observation(
            predicate, timeout, interval, stable_samples=1, *, initial=False
        ):
            waits = []
            while True:
                current, result = wait_for_tree(
                    tree, predicate, timeout, interval, stable_samples
                )
                waits.append(result)
                if result["ready"] or not initial or continue_from is not None:
                    break
                save(attempt / f"startup-observation-{len(waits):03d}.json", current)
                save(attempt / "startup-waits.json", waits)
                if not retry_exited_application(
                    profile, recipe, hdc, attempt, sleep=time.sleep
                ):
                    break
            if len(waits) > 1:
                save(attempt / "startup-waits.json", waits)
                result = {**result, "startup_waits": waits}
            return current, result

        try:
            build_record = json.loads((run / "build.json").read_text(encoding="utf-8"))
            hap = run / "project" / profile["hap"]
            if digest(hap.read_bytes()) != build_record["hap_sha256"]:
                raise ValueError("HAP changed after build")
            session_start = None
            previous = (
                Path(continue_from).resolve() if continue_from is not None else None
            )
            if previous is not None:
                session_start = continuing_session(
                    profile, recipe, hdc, previous, device, build_record["hap_sha256"]
                )
            else:
                hdc("install", str(hap))
                start_application(profile, recipe, hdc, attempt, sleep=time.sleep)
            device_ready = True
            replay_route(recipe, hdc, wait_observation, attempt, run, replay_steps)

            def check_page(value):
                missing = missing_checks(value, recipe.get("checks", []))
                return not missing, missing

            before, page_wait = wait_observation(
                check_page,
                recipe.get("checkpoint_timeout", 10),
                recipe.get("poll_interval", 0.5),
                initial=not replay_steps,
            )
            save(attempt / "page-wait.json", page_wait)
            save(attempt / "tree-before.json", before)
            session = {"status": "unavailable"}
            try:
                observed_process = process_identity(profile, hdc)
                if session_start is not None and observed_process != session_start:
                    raise RuntimeError(
                        "Application process changed during route replay"
                    )
                session_start = observed_process
                session = {"status": "verified", "process": session_start}
            except RuntimeError as error:
                if previous is not None:
                    raise
                session["reason"] = str(error)
            capture_targets = []
            for active_plan in active_plans:
                geometry = active_plan.get("geometry")
                if geometry:
                    target = {
                        "selector": geometry.get(
                            "mutated_selector", geometry["selector"]
                        )
                    }
                    binding = geometry.get("source_binding", {})
                    expected = binding.get("baseline_text")
                    if (
                        "instance_index" in binding or "instance_key" in binding
                    ) and expected:
                        target["expected_text"] = expected
                    capture_targets.append(target)
            for check in recipe.get("checks", []):
                if not any(
                    matches_selector(n, check) for n in actionable_nodes(before)
                ):
                    raise RuntimeError("Page checkpoint missing: " + str(check))
            save(attempt / "tree-before.json", before)
            context = None
            try:
                display_dump = hdc(
                    "shell", "hidumper", "-s", "DisplayManagerService", "-a", "-a"
                )
                context = display_context(display_dump)
                densities = sorted(
                    set(
                        float(v)
                        for v in re.findall(
                            r"^VirtualPixelRatio:\s+([\d.]+)",
                            display_dump,
                            re.MULTILINE,
                        )
                    )
                )
                save(
                    attempt / "display.json",
                    {
                        "status": "measured" if len(densities) == 1 else "ambiguous",
                        "px_per_vp": densities[0] if len(densities) == 1 else None,
                        "source": "DisplayManagerService VirtualPixelRatio",
                        "values": densities,
                    },
                )
            except RuntimeError as error:
                save(
                    attempt / "display.json",
                    {"status": "unavailable", "error": str(error)},
                )
            from truncator.execution.device.acquisition import acquire

            before, after = acquire(
                attempt, hdc, tree, recipe.get("image_check"), capture_targets
            )
            if (
                session_start is not None
                and process_identity(profile, hdc) != session_start
            ):
                raise RuntimeError(
                    "Application process changed during screenshot acquisition"
                )
            if context:
                from PIL import Image

                with Image.open(capture_image(attempt)) as screenshot:
                    if list(screenshot.size) != context["screen_size"]:
                        raise RuntimeError("Display dimensions changed during capture")
            targets = []
            for selector in recipe.get("targets", []):
                matched = [
                    n for n in actionable_nodes(before) if matches_selector(n, selector)
                ]
                if len(matched) != selector.get("count", 1):
                    raise RuntimeError(
                        "Target instance budget mismatch: " + str(selector)
                    )
                targets.extend(matched)
            save(attempt / "targets.json", targets)
            for check in recipe.get("checks", []):
                if not any(
                    matches_selector(n, check) for n in actionable_nodes(before)
                ):
                    raise RuntimeError("Page changed during screenshot acquisition")
            for active_plan in active_plans:
                geometry = active_plan.get("geometry")
                if geometry:
                    selector = geometry.get("mutated_selector", geometry["selector"])
                    select_record(active_records(before), selector)
                    select_record(active_records(after), selector)
            record = {
                "status": "captured",
                "hap_sha256": build_record["hap_sha256"],
                "review": "pending",
                "trees_equal": before == after,
                "screenshot_sha256": digest((capture_image(attempt)).read_bytes()),
                "device": device,
                "recipe": recipe,
                "session": session,
                "display_context": context,
                "capture_policy": CURRENT_CAPTURE_POLICY,
                "page_id": (
                    page_id(capture_page) if capture_page else recipe.get("page_id")
                ),
            }
            if previous is not None:
                record["continued_from"] = {
                    "capture": str(previous),
                    "capture_sha256": digest((previous / "capture.json").read_bytes()),
                }
            if saved_plan:
                record_observations(saved_plan, recipe, attempt)
            save(attempt / "capture.json", record)
            event(run, "captured", attempt=attempt.name, **record)
            return attempt
        except Exception as error:
            failure = {"error": str(error), "failed_at": time.time()}
            if replay_steps:
                failure["last_replay_step"] = replay_steps[-1]
            save(attempt / "failure.json", failure)
            if device_ready:
                try:
                    from truncator.execution.device.failure_evidence import observe_failure

                    failure["diagnostics"] = observe_failure(
                        attempt, lambda *args: hdc(*args, timeout=10)
                    )
                except Exception as diagnostic_error:
                    failure["diagnostics"] = {"status": "unavailable", "error": str(diagnostic_error)}
            else:
                failure["diagnostics"] = {"status": "not-attempted", "reason": "device_session_not_established"}
            save(attempt / "failure.json", failure)
            event(run, "capture-failed", attempt=attempt.name, error=str(error))
            raise
