"""Describe physical evidence and application coverage without inventing new labels."""

from collections import defaultdict


def _counts(rows):
    def evidence(row, names):
        return tuple(row["evidence_sha256"][name] for name in names)

    images = ("screenshot",)
    image_trees = (*images, "tree-before.json", "tree-after.json")
    return {
        "target_states": len(rows),
        "captures": len({(r["capture_sha256"], evidence(r, image_trees)) for r in rows}),
        "image_tree_sets": len({evidence(r, image_trees) for r in rows}),
        "screenshot_files": len({evidence(r, images) for r in rows}),
        "verified_applications": len({r["application_bundle"] for r in rows if r["application_bundle"]}),
        "target_states_without_verified_application": sum(not r["application_bundle"] for r in rows),
    }


def summarize_coverage(units):
    """Keep target counts separate from shared frames, repeated captures and apps.

    A capture means its bound metadata + image + both trees. Identical pixels with
    different trees remain different image/tree sets. Bundle identity comes only
    from the process in the reviewed capture, never from a mutable export profile.
    These counts do not claim independent defect mechanisms or production apps.
    """
    rows = [row for row in units if row["consensus"] == "consistent"]
    applications, cells = defaultdict(list), defaultdict(list)
    for row in rows:
        if row["application_bundle"]:
            applications[row["application_bundle"]].append(row)
        cells[(row["component"], row["axis"])].append(row)
    return {
        **_counts(rows),
        "excluded_conflicting_target_states": len(units) - len(rows),
        "by_application": {bundle: _counts(items) for bundle, items in sorted(applications.items())},
        "by_component_axis": [
            {"component": component, "axis": axis, **_counts(items)}
            for (component, axis), items in sorted(cells.items())
        ],
        "policy": (
            "Consistent target observations only. Shared frames and repeated captures do not create new applications; "
            "byte-identical screenshots with different trees remain separate image/tree sets. "
            "Applications are verified bundle identities, not counts of independent production defects. "
        ),
    }
