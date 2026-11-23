"""Remove only the injected clip call in isolated upstream app copies."""
import argparse
import shutil
from pathlib import Path

from truncator.source.binding import active_records, select_record
from truncator.execution.build import build
from truncator.mutation.mutations import apply_patches, mutation_patches
from truncator.source.project import prepare
from truncator.execution.device.runtime import capture
from truncator.common.storage import read, save, digest


def run(output, device):
    root = Path(__file__).resolve().parents[2]
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for old in read(root / "artifacts/application-recovery-20261118/results.json"):
        if old["name"] not in {"ohbill", "wechat_harmonyos", "multishopping"}:
            continue
        original = Path(old["plan"]).parent
        plan, profile = read(original / "plan.json"), read(original / "profile.json")
        initial = Path(old["initial"]["capture"])
        recipe = read(initial / "capture.json")["recipe"]
        row = {"application": old["name"], "operator": plan["operator"],
               "original_plan": str(original / "plan.json"), "states": [], "status": "started"}
        results.append(row)
        save(output / "results.json", results)
        try:
            folder = output / old["name"]
            source = folder / "source-without-added-clip"
            shutil.copytree(profile["source"], source, ignore=shutil.ignore_patterns(
                ".git", ".hvigor", "build", ".idea", "node_modules", "oh_modules"))
            patches = mutation_patches(plan)
            assert len(patches) == 1, "Only single-site clip ablation is supported"
            patch = dict(patches[0])
            # Inspect the patch shape rather than silently changing an upstream clip.
            assert plan["replacement"].count(".clip(true)") == 1
            assert ".clip(" not in plan["site"]["snippet"]
            print(old["name"], "patch keys", list(patch), flush=True)
            for key, value in patch.items():
                if value == plan["replacement"]:
                    patch[key] = value.replace(".clip(true)", "")
            assert patch != patches[0]
            path = source / patch["file"]
            before = path.read_bytes().decode("utf-8")
            assert digest(before) == plan["file_sha256"]
            path.write_bytes(apply_patches(before, [patch]).encode("utf-8"))
            save(folder / "ablation.json", {"original_plan_sha256": digest((original / "plan.json").read_bytes()),
                "removed": ".clip(true)", "patch": patch, "source_sha256": digest(path.read_bytes()),
                "purpose": "Controlled causality probe; not a new production defect or operator."})
            derived = {**profile, "source": str(source)}
            variant = folder / "without-added-clip"
            prepare(derived, variant)
            build(derived, variant)
            selector = plan["geometry"]["mutated_selector"]
            normal = Path(plan["geometry"]["baseline_capture"])
            baseline_run = normal.parent
            states = [("normal", baseline_run, read(baseline_run / "profile.json"),
                       read(normal / "capture.json")["recipe"], plan["geometry"]["selector"]),
                      ("injected", original, profile, recipe, selector),
                      ("without-added-clip", variant, derived, recipe, selector)]
            for name, app, config, route, target in states:
                cap = capture(config, app, device, route, output)
                attrs = select_record(active_records(read(cap / "tree-before.json")), target)["attributes"]
                row["states"].append({"state": name, "capture": str(cap), "selector": target,
                                      "target": attrs, "run": str(app)})
                save(output / "results.json", results)
            row["status"] = "complete"
        except Exception as exc:
            row.update(status="error", error=str(exc))
        save(output / "results.json", results)
        print(row["application"], row["status"], row.get("error", ""), flush=True)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--device", default="127.0.0.1:5555")
    args = parser.parse_args()
    run(args.out, args.device)
