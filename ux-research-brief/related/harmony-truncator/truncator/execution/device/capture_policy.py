"""Version the implementation that produces and validates a capture."""

from pathlib import Path
from truncator.common.storage import digest

RULE_VERSION = "native-png-target-consistency-v3"
IMPLEMENTATION_FILES = (
    "execution/device/runtime.py",
    "execution/device/acquisition.py",
    "common/capture_files.py",
    "execution/device/failure_evidence.py",
    "planning/pages.py",
    "execution/device/route_runner.py",
    "execution/device/replay.py",
    "execution/device/startup.py",
    "execution/device/waiting.py",
    "source/binding.py",
    "execution/device/device_context.py",
    "review/observation.py",
    "planning/layout_impact.py",
    "review/diagnostics.py",
    "review/consistency.py",
    "imaging/visual.py",
    "execution/device/capture_policy.py",
    "planning/composition.py",
    "imaging/geometry.py",
    "common/validation.py",
    "execution/device/commands.py",
)


def implementation_identity():
    root = Path(__file__).parents[2]
    files = {name: digest((root / name).read_bytes()) for name in IMPLEMENTATION_FILES}
    return {
        "rule_version": RULE_VERSION,
        "implementation_sha256": digest(str(sorted(files.items()))),
    }


# Fixed for the lifetime of this Python process, including a long-running batch.
CURRENT_CAPTURE_POLICY = implementation_identity()


def current_capture(record):
    return record.get("capture_policy") == CURRENT_CAPTURE_POLICY
