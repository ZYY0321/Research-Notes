"""Compare responsive and fixed-width HAPs in the emulator's real folded states."""

import time
from pathlib import Path
from truncator.common.storage import read, save, digest
from truncator.source.project import scan, prepare
from truncator.execution.build import build
from truncator.execution.device.runtime import capture
from truncator.source.binding import bind_candidates
from truncator.planning.calibration import plan_for_target
from truncator.execution.device.commands import command
from truncator.execution.device.device_context import display_context


def set_posture(profile, output, posture, expected_width):
    command(
        [
            "E:/HarmonyDev/DevEcoStudio/tools/emulator/Emulator.exe",
            "-instance",
            "UX_WideFold_API23",
            "-foldedState",
            posture,
        ],
        output / (posture + "-command.log"),
        timeout=30,
    )
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        text, _ = command(
            [
                profile["hdc"],
                "-t",
                "127.0.0.1:5555",
                "shell",
                "hidumper",
                "-s",
                "DisplayManagerService",
                "-a",
                "-a",
            ],
            output / (posture + "-display-" + str(time.time_ns()) + ".log"),
            timeout=10,
        )
        context = display_context(text)
        if context and context["screen_size"][0] == expected_width:
            return context
        time.sleep(0.5)
    raise RuntimeError("Display did not reach requested posture")


def main():
    project = Path(__file__).resolve().parents[2]
    baseline = Path("E:/HarmonyDev/MutationRuns/directional-controls-20261117/baseline")
    profile = read(baseline / "profile.json")
    output = Path("E:/HarmonyDev/MutationRuns/frozen-viewport-20261117")
    output.mkdir(parents=True, exist_ok=True)
    selector = {"id": "responsive-target", "type": "Text"}
    recipe = {
        "reset_app_data": True,
        "settle_seconds": 3,
        "actions": [{"field": "id", "equals": "choose-responsive", "wait": 2}],
        "checks": [{"field": "id", "equals": selector["id"]}],
        "targets": [{"selector": selector}],
    }
    results = []
    try:
        set_posture(profile, output, "open", 2584)
        normal = capture(profile, baseline, "127.0.0.1:5555", recipe, output)
        results.append({"state": "normal-wide", "capture": str(normal)})
        catalog = scan(profile)
        binding = next(
            row
            for row in bind_candidates(catalog, read(normal / "tree-before.json"))[
                "bindings"
            ]
            if row["selector"] == selector
        )
        plan = plan_for_target(catalog, normal, binding, "freeze-viewport-width")[0]
        save(output / "plan.json", plan)
        run = output / plan["id"]
        if not (run / "prepared.json").exists():
            prepare(profile, run, plan)
        if not (run / "build.json").exists():
            build(profile, run)
        for name, application, posture, width in (
            ("fixed-wide", run, "open", 2584),
            ("normal-narrow", baseline, "close", 1264),
            ("fixed-narrow", run, "close", 1264),
            ("fixed-wide-return", run, "open", 2584),
        ):
            context = set_posture(profile, output, posture, width)
            cap = capture(profile, application, "127.0.0.1:5555", recipe, output)
            results.append(
                {"state": name, "capture": str(cap), "display_context": context}
            )
            save(output / "results.json", results)
            print(name, str(cap), flush=True)
        hashes = {
            read(Path(row["capture"]) / "capture.json")["hap_sha256"]
            for row in results
            if row["state"].startswith("fixed-")
        }
        assert len(hashes) == 1
        hap = run / "project" / profile["hap"]
        assert hashes == {digest(hap.read_bytes())}
        save(
            project / "artifacts/frozen-viewport-results-20261117.json",
            {
                "plan": str(output / "plan.json"),
                "states": results,
                "same_mutated_hap": True,
                "hap_sha256": next(iter(hashes)),
                "visual_review": "pending",
                "commercial_pair": "unreviewed",
            },
        )
    finally:
        set_posture(profile, output, "open", 2584)


if __name__ == "__main__":
    main()
