"""Compare observed boundary constraints without inferring pixels or source causes."""


def flag(value):
    """Normalize native JSON booleans and dumpLayout XML boolean strings."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower()
    return None


def window_id(value):
    return None if value is None or value == "" else str(value)


def boundary_signature(evidence, relations):
    features = relations["features"]
    target = evidence["target"]["attributes"]
    window = window_id(target.get("hostWindowId"))
    witnesses = relations["aligned_clip_ancestor_witnesses"]
    unknown = []
    envelopes = []
    if window is None:
        unknown.append({"path": evidence["target"]["path"], "field": "hostWindowId"})
    scroll_context = []
    ancestors = evidence["ancestors"]
    roots = [index for index, node in enumerate(ancestors)
             if node["attributes"].get("type") == "root"]
    for index in reversed(range(len(ancestors))):
        ancestor = ancestors[index]
        attributes = ancestor["attributes"]
        # XML envelope nodes describe provenance, not a UI component.
        if not attributes.get("type") and ancestor["bounds_px"] is None:
            continue
        # dumpLayout may wrap its typed window root in an empty full-screen record.
        if (roots and index < roots[0] and not attributes.get("type")
                and ancestor["bounds_px"] == [0, 0, *evidence["image_size_px"]]
                and all(attributes.get(key) in (None, "") for key in
                        ("hostWindowId", "clip", "scrollable", "id", "accessibilityId", "text"))):
            envelopes.append({"path": ancestor["path"], "reason": "empty_screen_envelope_before_typed_window_root"})
            continue
        ancestor_window = window_id(attributes.get("hostWindowId"))
        if window is not None and ancestor_window is not None and ancestor_window != window:
            continue
        for field in ("clip", "scrollable"):
            if flag(attributes.get(field)) is None:
                unknown.append({"path": ancestor["path"], "field": field})
        if ancestor_window is None:
            unknown.append({"path": ancestor["path"], "field": "hostWindowId"})
        if flag(attributes.get("clip")) == "true" and ancestor["bounds_px"] is None:
            unknown.append({"path": ancestor["path"], "field": "bounds"})
        if flag(attributes.get("scrollable")) == "true":
            if not attributes.get("type"):
                unknown.append({"path": ancestor["path"], "field": "type"})
            scroll_context.append({
                "path": ancestor["path"], "type": attributes.get("type"),
                "clip": flag(attributes.get("clip")),
                "aligned_loss_edges": sorted(edge for edge, nodes in witnesses.items()
                                             if any(n["path"] == ancestor["path"] for n in nodes)),
            })
    modes = {edge: sorted({"scrollable" if node["scrollable"] == "true"
                          else "fixed" if node["scrollable"] == "false" else "unknown"
                          for node in nodes}) for edge, nodes in witnesses.items()}
    # Keep all witness paths separately. Repeated framework wrappers do not become votes.
    context = [(node["type"], node["clip"] or "unknown", node["aligned_loss_edges"])
               for node in scroll_context]
    return {
        "features": {
            "target_type": features["target_type"],
            "target_clip": features["target_clip"],
            "target_scrollable": features["target_scrollable"],
            "exported_loss_edges": features["exported_loss_edges"],
            "loss_at_screen_edges": features["loss_at_screen_edges"],
            "aligned_boundary_modes": modes if window is not None else None,
            "scroll_context": [{"type": kind, "clip": clip, "aligned_loss_edges": list(edges)}
                               for kind, clip, edges in context] if not unknown else None,
        },
        "aligned_boundary_witnesses": witnesses,
        "scroll_ancestor_witnesses": scroll_context,
        "unknown_ancestor_fields": unknown,
        "excluded_export_envelopes": envelopes,
    }


def compare_boundaries(reference, injected, reference_relations, injected_relations):
    left = boundary_signature(reference, reference_relations)
    right = boundary_signature(injected, injected_relations)
    rows = {key: {"reference": value, "injected": right["features"][key],
                  "equal": None if value is None or right["features"][key] is None
                  else value == right["features"][key]}
            for key, value in left["features"].items()}
    differences = [key for key, row in rows.items() if row["equal"] is False]
    unknown = [key for key, row in rows.items() if row["equal"] is None]
    loss_edges = left["features"]["exported_loss_edges"]
    status = ("different" if differences else "incomplete" if unknown else
              "observed_boundary_relations_match" if loss_edges else "no_exported_boundary_loss")
    return {
        "status": status,
        "features": rows,
        "different_fields": differences,
        "unknown_fields": unknown,
        "reference": left, "injected": right,
        "interpretation": "Compare lost edges, screen boundaries, all aligned clip constraints and scroll ancestry; no similarity score.",
        "visual_content_loss": "requires_separate_review",
        "recovery_behavior": "requires_action_evidence; scrollable does not specify usable direction or reachability",
        "source_cause": "not_observable_from_static_tree",
    }
