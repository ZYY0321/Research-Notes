"""Verify compatible mixed operators together, using the same source revision."""

from pathlib import Path
from truncator.common.storage import read, save, digest
from truncator.planning.composition import select_combination, compose, source_conflict
from truncator.source.project import prepare
from truncator.execution.build import build
from truncator.execution.device.runtime import capture
from truncator.source.binding import active_records, select_record
from truncator.imaging.geometry import rectangle
from research.controls.evidence import (
    directional_swipe,
    evidence_identity,
    validate_interaction,
)


def main():
    root = Path("E:/HarmonyDev/MutationRuns/content-controls-20261118")
    profile = read(root / "baseline/profile.json")
    baseline = read(root / "baseline-capture.json")["capture"]
    recipe = read(root / "recipe.json")
    candidates = []
    for name, state in (
        ("symbol", "whitespace"),
        ("image", "clipped"),
        ("button-visible", "scroll"),
    ):
        folder = root / (name + "-plans")
        definition = read(folder / "control-group.json")
        row = next(row for row in definition["states"] if row["state"] == state)
        candidates.append(read(folder / row["plan"]))
    pages = [{"name": "controls", "recipe": recipe, "baseline_capture": baseline}]
    selected, selection = select_combination(
        candidates, pages, max_total=3, max_per_page=3
    )
    assert len(selected) == 3, selection
    # A competing mutation at the same image is an actual conflicting candidate.
    folder = root / "image-plans"
    alternate = next(
        row
        for row in read(folder / "control-group.json")["states"]
        if row["state"] == "scroll"
    )
    assert source_conflict(candidates[1], read(folder / alternate["plan"]))
    combined = compose(selected, pages, selection)
    output = root / "combined-visible"
    output.mkdir(exist_ok=True)
    save(output / "plan.json", combined)
    run = output / combined["id"]
    if not (run / "prepared.json").exists():
        prepare(profile, run, combined)
    if not (run / "build.json").exists():
        build(profile, run)
    initial = capture(profile, run, "127.0.0.1:5555", recipe, output)
    button = next(p for p in candidates if p["site"]["component"] == "Button")
    replay = {
        "checks": recipe["checks"],
        "actions": [
            directional_swipe({"id": button["parameters"]["viewport_id"]}, "vertical")
        ],
    }
    after = capture(
        profile, run, "127.0.0.1:5555", replay, output, continue_from=initial
    )
    action = {**evidence_identity(after), "before": evidence_identity(initial)}
    validate_interaction(action)
    result = {
        "plan": str(output / "plan.json"),
        "selection": selection,
        "initial": evidence_identity(initial),
        "button_scroll": action,
        "same_target_conflict_rejected": True,
        "comparisons": [],
    }
    for plan in candidates:
        name = plan["geometry"]["selector"]["id"].removeprefix("control-")
        state = plan["control_group"]["state"]
        group = read(root / ("button-visible" if name == "button" else name) / "control-results.json")
        single = next(s for s in group["states"] if s["state"] == state)
        selector = plan["geometry"]["mutated_selector"]
        attrs = []
        for cap in (single["capture"], initial, after):
            attrs.append(
                select_record(
                    active_records(read(Path(cap) / "tree-before.json")), selector
                )["attributes"]
            )
        fields = ("type", "text", "bounds", "origBounds", "clip", "scrollable")
        assert all(attrs[0].get(k) == attrs[1].get(k) for k in fields)
        if name != "button":
            assert all(attrs[1].get(k) == attrs[2].get(k) for k in fields)
        else:
            assert (
                rectangle(attrs[2]["origBounds"])[1]
                < rectangle(attrs[1]["origBounds"])[1]
            )
        result["comparisons"].append(
            {
                "component": plan["site"]["component"],
                "operator": plan["operator"],
                "single_capture": single["capture"],
                "fields": fields,
                "single_equals_combined": True,
                "observations": attrs,
            }
        )
    save(output / "verification.json", result)
    print(output / "verification.json", flush=True)


if __name__ == "__main__":
    main()
