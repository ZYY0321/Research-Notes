"""Exercise window-edge-clip through the shopping application's normal pipeline."""

from pathlib import Path

from truncator.source.binding import bind_candidates
from truncator.planning.calibration import plan_for_target
from truncator.source.project import scan
from truncator.common.storage import read, save
from truncator.execution.workflow import batch


def main():
    project = Path(__file__).resolve().parents[2]
    baseline = Path("E:/HarmonyDev/MutationRuns/commerce-wide-baseline-20261113")
    capture = baseline / "capture-20261113-232514-52900"
    profile = read(baseline / "profile.json")
    catalog = scan(profile)
    bindings = bind_candidates(catalog, read(capture / "tree-before.json"))["bindings"]
    binding = next(item for item in bindings
                   if item["selector"].get("id") == "truncator_probe_4762c9008dc42248466e")
    plan = plan_for_target(catalog, capture, binding, "window-edge-clip", penetrations=[10])[0]
    filename = project / "artifacts/window-control-plan-20261117.json"
    save(filename, plan)
    results = batch(profile, [filename], "E:/HarmonyDev/MutationRuns/window-control-20261117",
                    "127.0.0.1:5555", read(capture / "capture.json")["recipe"])
    save(project / "artifacts/window-control-results-20261117.json", results)
    print([{key: row.get(key) for key in ("status", "run", "error")} for row in results])
    if any(row["status"] == "failed" for row in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
