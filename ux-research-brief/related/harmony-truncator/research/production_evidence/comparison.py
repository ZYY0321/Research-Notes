"""Evidence-preserving comparison of real and injected runtime layout targets."""

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from truncator.source.binding import tree_records, select_record
from truncator.imaging.geometry import rectangle
from research.production_evidence.boundary_comparison import flag, window_id, compare_boundaries


def load_tree(path):
    path = Path(path)
    if path.suffix.lower() != ".xml":
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def convert(element):
        return {
            "attributes": dict(element.attrib),
            "children": [convert(child) for child in element],
        }

    return convert(ET.parse(path).getroot())


def box_or_none(value):
    if value in (None, ""):
        return None
    try:
        return rectangle(value)
    except ValueError:
        return None


def edge_losses(original, visible):
    if original is None or visible is None:
        return None
    return dict(zip(
        ("left", "right", "top", "bottom"),
        (max(0, visible[0] - original[0]),
         max(0, original[2] - visible[2]),
         max(0, visible[1] - original[1]),
         max(0, original[3] - visible[3])),
    ))


def node_evidence(record):
    attributes = dict(record["attributes"])
    bounds = box_or_none(attributes.get("bounds"))
    original = box_or_none(attributes.get("origBounds"))
    return {
        "path": record["path"],
        "attributes": attributes,
        "bounds_px": bounds,
        "orig_bounds_px": original,
        "exported_edge_loss_px": edge_losses(original, bounds),
        "missing_fields": [key for key in (
            "bounds", "origBounds", "clip", "scrollable", "hostWindowId"
        ) if attributes.get(key) in (None, "")],
    }


def inspect_target(tree_path, screenshot_path, selector):
    """Keep all windows and ancestors. Exported bounds are not glyph bounds."""
    if not isinstance(selector, dict) or not selector:
        raise ValueError("Target selector must be a nonempty attribute mapping")
    tree_path, screenshot_path = Path(tree_path), Path(screenshot_path)
    records = tree_records(load_tree(tree_path))
    target = select_record(records, selector)
    with Image.open(screenshot_path) as image:
        width, height = image.size
    evidence = node_evidence(target)
    original = evidence["orig_bounds_px"]
    bounds = evidence["bounds_px"]
    losses = evidence["exported_edge_loss_px"]
    ratios = None
    if original is not None and losses is not None:
        width_target, height_target = original[2] - original[0], original[3] - original[1]
        ratios = {
            edge: value / (width_target if edge in {"left", "right"} else height_target)
            for edge, value in losses.items()
        }
    ancestors = [node_evidence(record) for record in target["ancestors"]]
    same_parent = [record for record in records
                   if record is not target and record["ancestors"]
                   and target["ancestors"]
                   and record["ancestors"][-1] is target["ancestors"][-1]]
    overlaps = []
    for sibling in same_parent:
        sibling_box = box_or_none(sibling["attributes"].get("bounds"))
        if sibling_box is None:
            continue
        overlap_width = min(bounds[2], sibling_box[2]) - max(bounds[0], sibling_box[0])
        overlap_height = min(bounds[3], sibling_box[3]) - max(bounds[1], sibling_box[1])
        if overlap_width > 0 and overlap_height > 0:
            overlaps.append({**node_evidence(sibling),
                             "intersection_area_px": overlap_width * overlap_height})
    return {
        "schema_version": 1,
        "tree": str(tree_path.resolve()),
        "tree_sha256": hashlib.sha256(tree_path.read_bytes()).hexdigest(),
        "screenshot": str(screenshot_path.resolve()),
        "screenshot_sha256": hashlib.sha256(screenshot_path.read_bytes()).hexdigest(),
        "image_size_px": [width, height],
        "selector": selector,
        "target": evidence,
        "ancestors": ancestors,
        "overlapping_siblings": overlaps,
        "exported_edge_loss_ratio": ratios,
        "orig_outside_screen_px": edge_losses(original, [0, 0, width, height]),
        "visual_content_loss": "unreviewed",
        "recovery": "unmeasured",
    }


def structural_features(evidence):
    target = evidence["target"]
    ancestors = evidence["ancestors"]
    losses = target["exported_edge_loss_px"]
    return {
        "target_type": target["attributes"].get("type"),
        "target_clip": flag(target["attributes"].get("clip")),
        "target_scrollable": flag(target["attributes"].get("scrollable")),
        "exported_loss_edges": None if losses is None else sorted(
            edge for edge, value in losses.items() if value > 0
        ),
        "ancestor_types": [node["attributes"].get("type") for node in ancestors],
        "clipping_ancestor_types": [node["attributes"].get("type") for node in ancestors
                                    if flag(node["attributes"].get("clip")) == "true"],
        "scrollable_ancestor_types": [node["attributes"].get("type") for node in ancestors
                                      if flag(node["attributes"].get("scrollable")) == "true"],
        "overlapping_sibling_count": len(evidence["overlapping_siblings"]),
    }


def local_relations(evidence):
    """Describe exported geometry around the target, retaining boundary witnesses.

    Boundary alignment is an observation. It does not assign a rendering cause.
    Exact pixel alignment is used within each capture, never across devices.
    """
    target = evidence["target"]
    bounds = target["bounds_px"]
    original = target["orig_bounds_px"]
    losses = target["exported_edge_loss_px"]
    ancestors = evidence["ancestors"]
    parent = ancestors[-1] if ancestors else None
    width, height = evidence["image_size_px"]
    screen = [0, 0, width, height]
    edge_indices = {"left": 0, "top": 1, "right": 2, "bottom": 3}
    witnesses = {}
    window = window_id(target["attributes"].get("hostWindowId"))
    if losses is not None:
        for edge, loss in losses.items():
            if loss <= 0:
                continue
            index = edge_indices[edge]
            candidates = []
            for ancestor in reversed(ancestors):
                attributes = ancestor["attributes"]
                box = ancestor["bounds_px"]
                same_window = window is not None and window_id(attributes.get("hostWindowId")) == window
                if box is None or flag(attributes.get("clip")) != "true" or not same_window:
                    continue
                cross = (1, 3) if edge in {"left", "right"} else (0, 2)
                overlap = min(bounds[cross[1]], box[cross[1]]) - max(bounds[cross[0]], box[cross[0]])
                if box[index] == bounds[index] and overlap > 0:
                    candidates.append({
                        "path": ancestor["path"], "type": attributes.get("type"),
                        "scrollable": flag(attributes.get("scrollable")),
                        "bounds_px": box,
                    })
            witnesses[edge] = candidates
    parent_box = parent["bounds_px"] if parent else None
    parent_losses = edge_losses(original, parent_box)
    features = {
        "target_type": target["attributes"].get("type") or None,
        "target_clip": flag(target["attributes"].get("clip")),
        "target_scrollable": flag(target["attributes"].get("scrollable")),
        "bounds_equal_orig": None if bounds is None or original is None else bounds == original,
        "exported_loss_edges": None if losses is None else sorted(
            edge for edge, loss in losses.items() if loss > 0),
        "loss_at_screen_edges": None if losses is None else sorted(
            edge for edge, loss in losses.items()
            if loss > 0 and bounds[edge_indices[edge]] == screen[edge_indices[edge]]),
        "parent_type": parent["attributes"].get("type") or None if parent else None,
        "parent_clip": flag(parent["attributes"].get("clip")) if parent else None,
        "parent_scrollable": flag(parent["attributes"].get("scrollable")) if parent else None,
        "orig_exceeds_parent_edges": None if parent_losses is None else sorted(
            edge for edge, loss in parent_losses.items() if loss > 0),
        "nearest_aligned_clip_ancestors": None if losses is None or not window else {
            edge: {"type": nodes[0]["type"], "scrollable": nodes[0]["scrollable"]}
            if nodes else None for edge, nodes in witnesses.items()},
        "overlapping_direct_sibling_count": len(evidence["overlapping_siblings"]),
    }
    return {"features": features, "aligned_clip_ancestor_witnesses": witnesses}


def compare_targets(reference, injected):
    left, right = structural_features(reference), structural_features(injected)
    local_left, local_right = local_relations(reference), local_relations(injected)
    local_comparison = {
        key: {"reference": value, "injected": local_right["features"][key],
              "equal": None if value is None or local_right["features"][key] is None
              else value == local_right["features"][key]}
        for key, value in local_left["features"].items()
    }
    differences = [key for key, row in local_comparison.items() if row["equal"] is False]
    unknown = [key for key, row in local_comparison.items() if row["equal"] is None]
    return {
        "schema_version": 1,
        "reference": reference,
        "injected": injected,
        "feature_comparison": {
            key: {"reference": left[key], "injected": right[key],
                  "equal": None if left[key] is None or right[key] is None
                  else left[key] == right[key]}
            for key in left
        },
        "mechanism_assessment": "requires_visual_and_behavioral_review",
        "local_relations": {"reference": local_left, "injected": local_right},
        "local_feature_comparison": local_comparison,
        "boundary_comparison": compare_boundaries(reference, injected, local_left, local_right),
        "local_assessment": {
            "status": "different" if differences else "incomplete" if unknown else "structural_candidate",
            "different_fields": differences,
            "unknown_fields": unknown,
            "visual_review_required": True,
            "recovery_review_required": True,
        },
    }


def verify_bound_comparison(comparison, reference_tree, reference_image,
                            injected_tree, injected_image, target_selector):
    """Recompute a claimed match from its raw files, including the planned target.

    Paths in historical reports are provenance only. Callers supply verified local
    files, so the same check works after exporting and moving a sample package.
    """
    if comparison.get("schema_version") != 1:
        raise ValueError("Unsupported target comparison schema")
    evidence = []
    for name, tree, image in (
        ("reference", reference_tree, reference_image),
        ("injected", injected_tree, injected_image),
    ):
        recorded = comparison.get(name, {})
        selector = recorded.get("selector")
        if not isinstance(selector, dict) or not selector:
            raise ValueError("Comparison requires an explicit target selector")
        actual = inspect_target(tree, image, selector)
        if name == "injected":
            planned = inspect_target(tree, image, target_selector)
            if actual["target"]["path"] != planned["target"]["path"]:
                raise ValueError("Comparison does not describe the planned mutation target")
        # Retain only historical path strings; hashes, nodes and relationships
        # must still equal a fresh extraction from the supplied raw files.
        for key in ("tree", "screenshot"):
            actual[key] = recorded.get(key)
        evidence.append(actual)
    rebuilt = compare_targets(*evidence)
    if rebuilt != comparison:
        raise ValueError("Comparison does not match the current raw image/tree evidence")
    boundary_status = rebuilt["boundary_comparison"]["status"]
    if (boundary_status != "observed_boundary_relations_match"
            and not (boundary_status == "no_exported_boundary_loss"
                     and rebuilt["local_assessment"]["status"] == "structural_candidate")):
        raise ValueError("Comparison has unresolved structural differences or missing fields")
    return rebuilt
