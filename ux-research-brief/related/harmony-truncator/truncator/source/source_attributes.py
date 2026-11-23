"""Parse static source attribute values; independent of runtime node binding."""

import json5
from truncator.common.validation import finite


def effective_attributes(site):
    """Return final chain values, including statically expanded shared styles."""
    styles = site.get("styles")
    if styles is None:
        return site["attributes"]
    if styles.get("unresolved"):
        reason = styles["unresolved"][0]["reason"]
        raise ValueError("Unresolved shared style: " + reason)
    return styles["attributes"]


def attribute_text(attribute):
    """Get an expression safe in the component's original source scope."""
    if "text" not in attribute:
        raise ValueError("Unresolved shared attribute: " + attribute["name"])
    return attribute["text"]


def style_dependencies(site):
    return site.get("styles", site.get("padding", {})).get("dependencies", {})


def numeric_attribute(site, name, keys, default=0):
    matches = [a for a in effective_attributes(site) if a["name"] == name]
    if not matches:
        return {key: default for key in keys}
    if len(matches) != 1:
        raise ValueError("Ambiguous " + name + " expression")
    try:
        attribute = matches[0]
        value = (attribute["value"] if attribute.get("status") == "resolved"
                 else json5.loads(attribute_text(attribute)))
    except ValueError as error:
        raise ValueError(
            "Resolve dynamic " + name + " before geometry calibration"
        ) from error
    if isinstance(value, (int, float)) and name in {"margin", "padding"}:
        return {key: finite(value, name) for key in keys}
    if not isinstance(value, dict) or set(value) - set(keys):
        raise ValueError("Unsupported " + name + " coordinate expression")
    return {key: finite(value.get(key, default), name + "." + key) for key in keys}
