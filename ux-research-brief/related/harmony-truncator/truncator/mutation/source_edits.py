"""Source attribute edits and layout wrappers shared by operator strategies."""

import json
import json5
from truncator.common.validation import finite, positive
from truncator.source.source_attributes import effective_attributes, attribute_text


def attribute_edits(site, desired):
    """Return absolute, non-overlapping argument replacements and one insertion."""
    edits, additions = [], []
    effective = {a["name"]: a for a in effective_attributes(site)}
    for name, value in desired.items():
        matches = [a for a in site["attributes"] if a["name"] == name]
        if len(matches) > 1:
            raise ValueError("Ambiguous duplicate attribute " + name)
        if matches and effective.get(name, {}).get("origin") != "style":
            attr = matches[0]
            edits.append((attr["start"], attr["end"], value))
        else:
            additions.append("." + name + "(" + value + ")")
    if additions:
        edits.append((site["end"], site["end"], "".join(additions)))
    return edits


def replace_attributes(site, desired, tracking_id=None):
    if tracking_id:
        if any(a["name"] == "id" for a in site["attributes"]):
            raise ValueError("Tracking ID must preserve an existing source ID")
        desired = {**desired, "id": json.dumps(tracking_id)}
    result = site["snippet"]
    for start, end, value in sorted(attribute_edits(site, desired), reverse=True):
        start, end = start - site["start"], end - site["start"]
        result = result[:start] + value + result[end:]
    return result


def vector(x, y):
    return "{ x: " + str(finite(x, "x")) + ", y: " + str(finite(y, "y")) + " }"


def reject_layout_conflicts(site, parameters):
    conflicts = {
        "constraintSize",
        "layoutWeight",
        "aspectRatio",
        "alignRules",
        "anchor",
        "transform",
        "scale",
        "rotate",
        "offset",
        "position",
        "translate",
    }
    if "resolved_aspect_ratio" in parameters:
        positive(parameters["resolved_aspect_ratio"], "resolved_aspect_ratio")
        conflicts.remove("aspectRatio")
    found = sorted(conflicts & {a["name"] for a in effective_attributes(site)})
    if found and not parameters.get("replace_layout", False):
        raise ValueError(
            "Existing layout expressions require explicit replace_layout: "
            + ", ".join(found)
        )
    unsupported = set(found) - {"position", "translate"}
    if unsupported:
        raise ValueError(
            "Unresolved layout constraints: " + ", ".join(sorted(unsupported))
        )


def pinned(site, p):
    reject_layout_conflicts(site, p)
    result = {
        "width": str(positive(p["child_width"], "child_width")),
        "height": str(positive(p["child_height"], "child_height")),
        "flexShrink": "0",
    }
    if "resolved_aspect_ratio" in p:
        result["aspectRatio"] = str(p["resolved_aspect_ratio"])
    return result


def wrapper_layout(site):
    child_attributes, wrapper_attributes = {}, []
    for name, reset in {"margin": "0", "alignSelf": "ItemAlign.Auto"}.items():
        matches = [a for a in effective_attributes(site) if a["name"] == name]
        if len(matches) > 1:
            raise ValueError("Ambiguous duplicate attribute " + name)
        if matches:
            child_attributes[name] = reset
            wrapper_attributes.append("." + name + "(" + attribute_text(matches[0]) + ")")
    return child_attributes, "".join(wrapper_attributes)


def reject_changed_padding_reference(site, parameters):
    """A narrower wrapper changes percentage padding, including top/bottom.

    Keep this at the rendering boundary so explicitly supplied plans receive the
    same check as automatic plans. Preserved-slot and same-width wrappers do not
    change width in this way and are outside this guard.
    """
    if parameters.get("width", 80) == parameters.get("child_width"):
        return
    matches = [a for a in effective_attributes(site) if a["name"] == "padding"]
    if not matches:
        return
    if len(matches) != 1:
        raise ValueError("Ambiguous duplicate attribute padding")
    attribute = matches[0]
    try:
        value = (attribute["value"] if attribute.get("status") == "resolved"
                 else json5.loads(attribute_text(attribute)))
    except ValueError as error:
        raise ValueError("Changed wrapper width requires statically resolved padding") from error
    def percentage(item):
        if isinstance(item, dict):
            return any(percentage(v) for v in item.values())
        return isinstance(item, str) and "%" in item
    if percentage(value):
        raise ValueError("Changed wrapper width would change percentage padding; choose a same-width mechanism")
