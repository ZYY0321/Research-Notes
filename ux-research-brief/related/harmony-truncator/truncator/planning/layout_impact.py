"""Record collateral layout changes for post-batch review without replanning."""

from truncator.common.capture_files import capture_image

from collections import defaultdict
from pathlib import Path
from truncator.source.binding import active_records
from truncator.imaging.geometry import rectangle
from truncator.common.storage import read, save
from truncator.planning.pages import resolve_page
from truncator.imaging.visual import changed_fraction
from PIL import Image


def compare_layout(before, after, regions):
    def indexed(tree):
        result = defaultdict(list)
        for record in active_records(tree):
            attrs = record["attributes"]
            if attrs.get("id") and attrs.get("bounds"):
                result[(attrs["id"], attrs.get("type"))].append(attrs)
        return result

    original, mutated = indexed(before), indexed(after)
    changes, ambiguous = [], []
    for key in sorted(original, key=str):
        if len(original[key]) != 1 or len(mutated.get(key, [])) > 1:
            ambiguous.append(list(key))
            continue
        old = original[key][0]
        new = mutated[key][0] if mutated.get(key) else None
        old_box = rectangle(old["bounds"])
        new_box = rectangle(new["bounds"]) if new else None
        if new_box and max(abs(a - b) for a, b in zip(old_box, new_box)) <= 2:
            continue
        boxes = [old_box] + ([new_box] if new_box else [])
        changes.append(
            {
                "id": key[0],
                "type": key[1],
                "before": old_box,
                "after": new_box,
                "outside_expected_regions": not all(
                    any(
                        region[0] <= box[0]
                        and region[1] <= box[1]
                        and region[2] >= box[2]
                        and region[3] >= box[3]
                        for region in regions
                    )
                    for box in boxes
                ),
            }
        )
    return {
        "changes": changes,
        "ambiguous_ids": ambiguous,
        "outside_expected_count": sum(c["outside_expected_regions"] for c in changes),
        "expected_regions": regions,
        "role": "post_batch_review",
    }


def record_layout_impact(plan, recipe, capture_dir):
    page = resolve_page(plan, recipe) if "pages" in plan else None
    pages = [page] if page else []
    result = []
    for page in pages:
        baseline = Path(page["baseline_capture"])
        decisions = plan.get("selection", {}).get("decisions", [])
        if decisions:
            regions = [
                decision["influence_regions"][page["name"]]
                for decision in decisions
                if decision["selected"] in page["mutation_ids"]
                and page["name"] in decision["influence_regions"]
            ]
        else:
            regions = (
                plan.get("selection", {})
                .get("influence_regions", {})
                .get(page["name"], [])
            )
        result.append(
            {
                "page": page["name"],
                **compare_layout(
                    read(baseline / "tree-before.json"),
                    read(Path(capture_dir) / "tree-before.json"),
                    regions,
                ),
            }
        )
        try:
            with Image.open(capture_image(baseline)) as image:
                width, height = image.size
            clipped = [
                [max(0, b[0]), max(0, b[1]), min(width, b[2]), min(height, b[3])]
                for b in regions
                if b[2] > 0 and b[3] > 0 and b[0] < width and b[1] < height
            ]
            result[-1]["outside_region_pixel_difference"] = changed_fraction(
                capture_image(baseline), capture_image(capture_dir), clipped
            )
        except (ValueError, OSError) as error:
            result[-1]["outside_region_pixel_difference"] = {
                "status": "unavailable",
                "error": str(error),
            }
    save(Path(capture_dir) / "layout-impact.json", {"pages": result})
