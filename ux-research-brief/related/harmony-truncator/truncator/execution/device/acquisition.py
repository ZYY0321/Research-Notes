"""Bounded screenshot acquisition and target consistency validation."""

from pathlib import Path
import shutil
import time
from PIL import Image
from truncator.common.storage import save, digest
from truncator.imaging.visual import changed_fraction
from truncator.common.validation import finite
from truncator.source.binding import active_records, select_record
from truncator.execution.device.waiting import wait_for_tree
from truncator.common.capture_files import SNAPSHOT_NAME, TREE_FILES


def target_state(tree, targets):
    """Compare only the requested targets, leaving unrelated animations free to run."""
    records = active_records(tree)
    states = []
    ready = True
    fields = (
        "id",
        "type",
        "text",
        "originalText",
        "bounds",
        "origBounds",
        "visible",
        "opacity",
        "clip",
    )
    for target in targets:
        selector = target["selector"]
        try:
            record = select_record(records, selector)
            attrs = record["attributes"]
            expected = target.get("expected_text")
            if expected and expected != (
                attrs.get("originalText") or attrs.get("text")
            ):
                raise ValueError("Loop instance content changed since baseline")
            states.append(
                {
                    "selector": selector,
                    "attributes": {key: attrs.get(key) for key in fields},
                }
            )
        except ValueError as error:
            ready = False
            states.append({"selector": selector, "error": str(error)})
    return ready, states


def acquire(attempt, hdc, tree, check=None, targets=None):
    attempt = Path(attempt)
    config = check or {}
    targets = targets or []
    tries = config.get("attempts", 3 if targets else 1)
    if isinstance(tries, bool) or not isinstance(tries, int) or not 1 <= tries <= 5:
        raise ValueError("Capture attempts must be an integer from 1 to 5")
    delay = finite(config.get("delay_seconds", 1), "delay_seconds")
    limit = finite(config.get("max_changed_fraction", 0.01), "max_changed_fraction")
    if not 0 <= delay <= 10 or not 0 <= limit <= 1:
        raise ValueError("Invalid image check thresholds")
    if check and not config.get("baseline_image"):
        raise ValueError("Image check requires baseline_image")
    enforcement = config.get("enforcement", "advisory")
    if enforcement not in {"advisory", "strict"}:
        raise ValueError("Image check enforcement must be advisory or strict")
    checks = []
    for index in range(tries):
        folder = attempt / "frames" / str(index)
        folder.mkdir(parents=True)
        waiting = None
        if targets:
            before, waiting = wait_for_tree(
                tree, lambda value: target_state(value, targets), timeout=15
            )
            save(folder / "target-wait.json", waiting)
        else:
            before = tree()
        save(folder / "tree-before.json", before)
        before_ready, before_state = target_state(before, targets)
        remote = "/data/local/tmp/truncator-" + digest(str(folder))[:12] + ".png"
        hdc("shell", "snapshot_display", "-f", remote, "-t", "png")
        image_path = folder / SNAPSHOT_NAME
        # Read the post-snapshot tree before the host transfer to shorten the gap.
        after = tree()
        save(folder / "tree-after.json", after)
        hdc("file", "recv", remote, str(image_path))
        after_ready, after_state = target_state(after, targets)
        targets_passed = before_ready and after_ready and before_state == after_state
        target_check = {
            "passed": targets_passed,
            "before": before_state,
            "after": after_state,
        }
        save(folder / "target-consistency.json", target_check)
        measurement = {"status": "decoded"}
        try:
            with Image.open(image_path) as image:
                image.load()
                if image.format != "PNG":
                    raise OSError("Native PNG acquisition returned another image format")
                measurement["format"] = image.format
        except (OSError, SyntaxError) as error:
            measurement = {"status": "decode_failed", "error": str(error)}
        if check and measurement["status"] == "decoded":
            measurement = changed_fraction(
                config["baseline_image"],
                image_path,
                config.get("exclude_rectangles", []),
                config.get("threshold", 40),
            )
        passed = measurement.get("changed_fraction", 0) <= limit and measurement[
            "status"
        ] not in {"size_mismatch", "decode_failed"}
        advisory_capture = (
            enforcement == "advisory"
            and index + 1 == tries
            and measurement["status"] == "measured"
        )
        checks.append(
            {
                "frame": index,
                "measurement": measurement,
                "passed": passed and targets_passed,
                "image_passed": passed,
                "targets": target_check,
                "target_wait": waiting,
            }
        )
        save(
            attempt / "image-quality.json",
            {
                "configuration": config,
                "target_policy": {
                    "targets": targets,
                    "attempts": tries,
                    "wait_seconds": 15,
                },
                "checks": checks,
                "passed": passed and targets_passed,
                "review_required": not passed or not targets_passed,
            },
        )
        if targets_passed and (passed or advisory_capture):
            for name in (SNAPSHOT_NAME, *TREE_FILES):
                shutil.copy2(folder / name, attempt / name)
            return before, after
        if index + 1 < tries:
            time.sleep(delay)
    raise RuntimeError(
        "Image quality or target consistency check failed after bounded retries; "
        "all frames preserved"
    )
