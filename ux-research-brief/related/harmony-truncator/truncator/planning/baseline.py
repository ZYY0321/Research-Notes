"""Validate an unmodified capture and resolve the target's planning context."""

from truncator.common.capture_files import capture_image

from dataclasses import dataclass, field
from pathlib import Path
from truncator.common.storage import read, digest, contained
from truncator.common.validation import positive
from truncator.imaging.geometry import rectangle
from truncator.source.binding import active_records, select_record, literal
from truncator.source.source_attributes import style_dependencies, effective_attributes


@dataclass(frozen=True)
class Baseline:
    capture_dir: Path
    capture_record: dict
    binding: dict
    density: float
    records: list
    target: dict
    site: dict
    tracking_id: str | None
    mutated_selector: dict
    bounds: list
    measurement_cache: dict = field(default_factory=dict, repr=False, compare=False)


def load_baseline(catalog, capture_dir, binding, density):
    capture_dir = Path(capture_dir).resolve()
    if density is None:
        display = read(capture_dir / "display.json")
        density = display.get("px_per_vp")
        binding = {**binding, "density_source": display.get("source")}
    positive(density, "px_per_vp")
    capture_record = read(capture_dir / "capture.json")
    if (
        digest((capture_image(capture_dir)).read_bytes())
        != capture_record["screenshot_sha256"]
    ):
        raise ValueError("Baseline screenshot hash mismatch")
    baseline_run = capture_dir.parent
    if (baseline_run / "prepared.json").exists() and not read(
        baseline_run / "prepared.json"
    )["baseline"]:
        raise ValueError("Geometry calibration requires an unmutated baseline")
    records = active_records(read(capture_dir / "tree-before.json"))
    target = select_record(records, binding["selector"])
    after = select_record(
        active_records(read(capture_dir / "tree-after.json")), binding["selector"]
    )
    if target["attributes"] != after["attributes"]:
        raise ValueError("Target changed across baseline screenshot")
    site = next(s for s in catalog["sites"] if s["id"] == binding["site"])
    dependencies = style_dependencies(site)
    for relative, expected in dependencies.items():
        baseline_source = baseline_run / "project"
        if baseline_source.exists() and digest(contained(baseline_source, relative).read_bytes()) != expected:
            raise ValueError("Baseline style dependency differs from catalog: " + relative)
    ids = [a for a in effective_attributes(site) if a["name"] == "id"]
    if site.get("probe") and ("instance_index" in binding or "instance_key" in binding):
        expected_id = site["probe"]["prefix"] + str(
            binding.get("instance_key", binding.get("instance_index"))
        )
        if binding["selector"].get("id") != expected_id:
            raise ValueError("Loop instance selector differs from trace ID")
        tracking_id = None
        mutated_selector = {"id": expected_id, "type": site["component"]}
    elif ids:
        if len(ids) != 1 or not literal(ids[0].get("text", "")):
            raise ValueError(
                "Dynamic or duplicate ID requires explicit instance handling"
            )
        tracking_id = None
        mutated_selector = {"id": literal(ids[0]["text"]), "type": site["component"]}
    else:
        tracking_id = "truncator_" + site["id"]
        if any(
            a.get("text", "").strip("\"'") == tracking_id
            for s in catalog["sites"] + catalog.get("structural_sites", [])
            for a in s["attributes"]
            if a["name"] == "id"
        ):
            raise ValueError("Generated tracking ID collides with source ID")
        mutated_selector = {"id": tracking_id, "type": site["component"]}
    if (baseline_run / "post-scan.json").exists() and read(
        baseline_run / "post-scan.json"
    )["files"].get(site["file"]) != catalog["files"][site["file"]]:
        raise ValueError("Baseline source differs from catalog")
    box = rectangle(target["attributes"]["bounds"])
    original = rectangle(target["attributes"].get("origBounds") or box)
    if any(abs(a - b) > 1 for a, b in zip(box, original)):
        raise ValueError("Target is already clipped in the baseline")
    return Baseline(
        capture_dir=capture_dir,
        capture_record=capture_record,
        binding=binding,
        density=density,
        records=records,
        target=target,
        site=site,
        tracking_id=tracking_id,
        mutated_selector=mutated_selector,
        bounds=box,
    )
