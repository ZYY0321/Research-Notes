"""Build and capture matched controls in the existing open-source shopping app."""

import json
from pathlib import Path

from truncator.source.binding import bind_candidates
from truncator.planning.calibration import plan_for_target
from truncator.source.project import scan
from truncator.common.storage import read, save
from truncator.execution.workflow import batch


def main():
    project = Path(__file__).resolve().parents[2]
    baseline = Path("E:/HarmonyDev/MutationRuns/commerce-wide-baseline-20261113")
    capture = baseline / "capture-20261113-232634-158600"
    profile = read(baseline / "profile.json")
    catalog = scan(profile)
    bindings = bind_candidates(catalog, read(capture / "tree-before.json"))["bindings"]
    plans_dir = project / "artifacts" / "service-control-plans-20261117"
    recipes = read(capture / "capture.json")["recipe"]
    # The new nested Scroll makes a type-only selector ambiguous. Bind the
    # existing page viewport for this fixed-device reproduction recipe.
    recipes["actions"][1] = {
        **recipes["actions"][1],
        "selector": {"type": "Scroll", "bounds": "[0,107][2584,1610]"},
    }
    requests = [
        ("scroll-recovery", "truncator_probe_bf0e7db549458b6420b3_0"),
        ("fixed-parent-clip", "truncator_probe_bf0e7db549458b6420b3_0"),
        ("whitespace-clip", "truncator_probe_bf0e7db549458b6420b3_0"),
    ]
    files = []
    for operator, target_id in requests:
        binding = next(item for item in bindings if item["selector"].get("id") == target_id)
        plan = plan_for_target(catalog, capture, binding, operator, edge="right")[0]
        path = plans_dir / (operator + ".json")
        save(path, plan)
        files.append(path)
    results = batch(profile, files, "E:/HarmonyDev/MutationRuns/service-controls-20261117",
                    "127.0.0.1:5555", recipes)
    save(project / "artifacts" / "service-control-results-20261117.json", results)
    print(json.dumps([{key: item.get(key) for key in ("plan", "run", "status", "error")}
                      for item in results], ensure_ascii=False, indent=2))
    if any(item["status"] == "failed" for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
