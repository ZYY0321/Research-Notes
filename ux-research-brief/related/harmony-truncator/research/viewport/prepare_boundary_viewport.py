"""Build a viewport-cache experiment without the fixture's outer clip constraint."""

import argparse
import difflib
import shutil
from pathlib import Path

from truncator.common.storage import read, save, digest
from truncator.source.project import prepare, scan
from truncator.execution.build import build
from truncator.execution.device.runtime import capture
from truncator.source.binding import bind_candidates
from truncator.planning.calibration import plan_for_target
from .run_frozen_viewport import set_posture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    project = Path(__file__).resolve().parents[2]
    fixture = project / "research/fixtures/directional-controls/Index.ets"
    original = fixture.read_text(encoding="utf-8")
    suffix = ".backgroundColor('#FFFFFF').clip(true)"
    if original.count(suffix) != 1:
        raise ValueError("Expected exactly one outer fixture clip")
    revised = original.replace(suffix, ".backgroundColor('#FFFFFF').clip(false)")
    source = root / "source"
    if not source.exists():
        shutil.copytree("E:/HarmonyDev/projects/ux-treepair-20261106", source,
                        ignore=shutil.ignore_patterns(".git", ".hvigor", "build", ".idea"))
        (source / "entry/src/main/ets/pages/Index.ets").write_text(revised, encoding="utf-8")
        manifest = read(source / "AppScope/app.json5")
        manifest["app"]["bundleName"] = "com.example.boundaryviewport"
        save(source / "AppScope/app.json5", manifest)
    if (source / "entry/src/main/ets/pages/Index.ets").read_text(encoding="utf-8") != revised:
        raise ValueError("Existing boundary fixture differs; use a fresh experiment directory")
    save(root / "fixture-change.json", {"original_fixture": str(fixture),
         "original_sha256": digest(original), "revised_sha256": digest(revised),
         "change": "Only outer Column clip(true) -> clip(false); Scroll clip(true) remains."})
    (root / "fixture.diff").write_text("".join(difflib.unified_diff(
        original.splitlines(keepends=True), revised.splitlines(keepends=True),
        fromfile="original/Index.ets", tofile="boundary/Index.ets")), encoding="utf-8")
    profile = {**read(project / "profiles/apps/ohbill.json"), "source": str(source),
               "bundle": "com.example.boundaryviewport",
               "files": {"local.properties": "hwsdk.dir=E:/HarmonyDev/DevEcoStudio/sdk\n"}}
    baseline = root / "baseline"
    if not (baseline / "prepared.json").exists():
        prepare(profile, baseline)
    if not (baseline / "build.json").exists():
        build(profile, baseline)
    print("Responsive baseline built", flush=True)
    selector = {"id": "responsive-target", "type": "Text"}
    recipe = {"reset_app_data": True, "settle_seconds": 3,
              "actions": [{"field": "id", "equals": "choose-responsive", "wait": 2}],
              "checks": [{"field": "id", "equals": selector["id"]}],
              "targets": [{"selector": selector}]}
    set_posture(profile, root, "open", 2584)
    normal = capture(profile, baseline, "127.0.0.1:5555", recipe, root)
    catalog = scan(profile)
    binding = next(row for row in bind_candidates(catalog, read(normal / "tree-before.json"))["bindings"]
                   if row["selector"] == selector)
    plan = plan_for_target(catalog, normal, binding, "cache-viewport-width")[0]
    save(root / "plan.json", plan)
    run = root / plan["id"]
    prepare(profile, run, plan)
    build(profile, run)
    save(root / "prepared-experiment.json", {"baseline": str(baseline), "mutated": str(run),
         "planning_capture": str(normal), "operator": plan["operator"]})
    print("Cache variant built:", run, flush=True)


if __name__ == "__main__":
    main()
