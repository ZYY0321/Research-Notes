"""Run controlled native-width and ArkWeb cases through the existing pipeline."""

from pathlib import Path
import shutil

from truncator.source.binding import bind_candidates
from truncator.planning.calibration import plan_for_target
from truncator.source.project import prepare, scan
from truncator.execution.build import build
from truncator.execution.device.runtime import capture, latest_capture
from truncator.common.storage import read, save
from truncator.execution.workflow import batch


def main():
    project = Path(__file__).resolve().parents[2]
    fixture = project / "research/fixtures/layout-reference"
    output = Path("E:/HarmonyDev/MutationRuns/layout-reference-clipped-root-20261117")
    source = output / "source"
    if not source.exists():
        shutil.copytree("E:/HarmonyDev/projects/ux-treepair-20261106", source,
                        ignore=shutil.ignore_patterns(".git", ".hvigor", "build", ".idea"))
        shutil.copyfile(fixture / "Index.ets", source / "entry/src/main/ets/pages/Index.ets")
        raw = source / "entry/src/main/resources/rawfile"
        raw.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(fixture / "reference.html", raw / "reference.html")
        shutil.copyfile(source / "AppScope/resources/base/media/app_icon.svg", raw / "app_icon.svg")
        manifest = read(source / "AppScope/app.json5")
        manifest["app"]["bundleName"] = "com.example.layoutreference"
        save(source / "AppScope/app.json5", manifest)
    for filename, relative in (
        ("Index.ets", "entry/src/main/ets/pages/Index.ets"),
        ("reference.html", "entry/src/main/resources/rawfile/reference.html"),
    ):
        if (fixture / filename).read_bytes() != (source / relative).read_bytes():
            raise ValueError("Fixture changed after this experiment was created: " + filename)
    toolchain = read(project / "profiles/apps/ohbill.json")
    profile = {**toolchain, "source": str(source), "bundle": "com.example.layoutreference",
               "files": {"local.properties": "hwsdk.dir=E:/HarmonyDev/DevEcoStudio/sdk\n"}}
    baseline = output / "baseline"
    if not (baseline / "prepared.json").exists():
        prepare(profile, baseline)
    if not (baseline / "build.json").exists():
        build(profile, baseline)
    cases = [
        ("native", "viewport-width-mismatch", {"id": "wide-target", "type": "Text"}, "right", 100,
         {"actions": [], "checks": [{"field": "id", "equals": "wide-target"}]}),
        ("web", "window-edge-clip", {"id": "web-view", "type": "Web"}, "top", 64,
         {"actions": [{"field": "id", "equals": "choose-web", "wait": 5}],
          "checks": [{"field": "id", "equals": "web-view"}, {"equals": "网页已加载"}]}),
    ]
    results = []
    catalog = scan(profile)
    for name, operator, selector, edge, penetration, steps in cases:
        recipe = {"reset_app_data": True, "settle_seconds": 5, **steps,
                  "targets": [{"selector": selector}]}
        normal = latest_capture(baseline, "127.0.0.1:5555", recipe)
        if normal is None:
            normal = capture(profile, baseline, "127.0.0.1:5555", recipe, output)
        bindings = bind_candidates(catalog, read(normal / "tree-before.json"))["bindings"]
        binding = next(item for item in bindings if item["selector"] == selector)
        plan = plan_for_target(catalog, normal, binding, operator, edge=edge,
                               penetrations=[penetration])[0]
        filename = output / (name + "-plan.json")
        save(filename, plan)
        runs = batch(profile, [filename], output / name, "127.0.0.1:5555", recipe)
        results.append({"case": name, "baseline": str(normal), "runs": runs})
        save(output / "results.json", results)
        save(project / "artifacts/layout-reference-clipped-root-results-20261117.json", results)
        print(name, [{key: row.get(key) for key in ("status", "run", "error")} for row in runs], flush=True)
        if any(row["status"] == "failed" for row in runs):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
