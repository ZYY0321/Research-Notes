"""Deterministic source/runtime matching and local layout context."""

import re
import json5
from pathlib import Path
from truncator.common.storage import read
from truncator.imaging.geometry import rectangle
from truncator.source.source_attributes import effective_attributes, attribute_text


def tree_records(tree):
    result = []

    def visit(node, path, ancestors):
        if isinstance(node, list):
            for i, child in enumerate(node):
                visit(child, path + [i], ancestors)
        elif isinstance(node, dict):
            if "attributes" in node:
                record = {
                    "attributes": node["attributes"],
                    "path": path,
                    "ancestors": ancestors,
                }
                result.append(record)
                ancestors = ancestors + [record]
            for key, child in node.items():
                if key != "attributes":
                    visit(child, path + [key], ancestors)

    visit(tree, [], [])
    return result


def select_record(records, selector):
    matches = [
        r
        for r in records
        if all(r["attributes"].get(k) == v for k, v in selector.items())
    ]
    if len(matches) != 1:
        raise ValueError(
            "Runtime selector must match once, matched "
            + str(len(matches))
            + ": "
            + str(selector)
        )
    rectangle(matches[0]["attributes"]["bounds"])
    return matches[0]


def literal(expression):
    if len(expression) >= 2 and expression[0] in "\"'":
        try:
            value = json5.loads(expression)
            return value if isinstance(value, str) else None
        except ValueError:
            pass
    return None


def source_selectors(catalog, site):
    try:
        attributes = effective_attributes(site)
    except ValueError:
        return []
    ids = [a for a in attributes if a["name"] == "id"]
    if len(ids) == 1 and literal(ids[0].get("text", "")):
        return [{"id": literal(attribute_text(ids[0])), "type": site["component"]}]
    if site["component"] != "Text" or len(site.get("arguments", [])) != 1:
        return []
    arg = site["arguments"][0]
    text = literal(arg)
    if text is not None:
        return [{"text": text, "type": "Text"}]
    match = re.fullmatch(r"\$r\(['\"]app\.string\.([\w]+)['\"]\)", arg)
    if not match:
        return []
    source = Path(catalog["root"]) / site["file"]
    values = set()
    # Resolve the resource namespace of the source module, without model inference.
    for ancestor in source.parents:
        resources = ancestor / "resources"
        if resources.is_dir():
            for resource in sorted(resources.glob("*/element/string.json")):
                try:
                    for item in read(resource).get("string", []):
                        if item.get("name") == match[1] and isinstance(
                            item.get("value"), str
                        ):
                            values.add(item["value"])
                except (ValueError, OSError):
                    continue
            break
        if ancestor == Path(catalog["root"]):
            break
    if not values:
        # HAR resources are merged into the application resource namespace.
        manifest = Path(catalog["root"]) / "build-profile.json5"
        if manifest.exists():
            modules = json5.loads(manifest.read_text(encoding="utf-8-sig")).get(
                "modules", []
            )
            for module in modules:
                resources = (
                    Path(catalog["root"]) / module["srcPath"] / "src/main/resources"
                )
                for resource in sorted(resources.glob("*/element/string.json")):
                    for item in read(resource).get("string", []):
                        if item.get("name") == match[1] and isinstance(
                            item.get("value"), str
                        ):
                            values.add(item["value"])
    return [{"text": text, "type": "Text"} for text in sorted(values)]


def active_records(tree):
    """Restrict a focused modal capture to its dialog subtree."""
    records = tree_records(tree)
    dialogs = [
        record
        for record in records
        if record["attributes"].get("type") == "Dialog"
        and record["attributes"].get("visible") == "true"
    ]
    focused = [
        record for record in dialogs if record["attributes"].get("focused") == "true"
    ]
    selected = focused if len(focused) == 1 else dialogs
    if len(selected) == 1:
        path = selected[0]["path"]
        records = [record for record in records if record["path"][: len(path)] == path]
    return [
        record for record in records if record["attributes"].get("visible") != "false"
    ]


def bind_candidates(catalog, tree, file_filter=""):
    records = active_records(tree)
    bindings, rejected = [], []
    for site in catalog["sites"]:
        if file_filter not in site["file"]:
            continue
        if site["repeated"] and site.get("probe"):
            prefix = site["probe"]["prefix"]
            instances = [
                r
                for r in records
                if r["attributes"].get("type") == site["component"]
                and (
                    r["attributes"].get("id", "").startswith(prefix)
                    if "key_expression" in site["probe"]
                    else re.fullmatch(
                        re.escape(prefix) + r"\d+", r["attributes"].get("id", "")
                    )
                )
            ]
            for record in instances:
                attrs = record["attributes"]
                selector = {"id": attrs["id"], "type": site["component"]}
                try:
                    selected = select_record(records, selector)
                    bindings.append(
                        {
                            "site": site["id"],
                            "selector": selector,
                            "path": selected["path"],
                            "bounds": attrs["bounds"],
                            **(
                                {"instance_key": attrs["id"][len(prefix) :]}
                                if "key_expression" in site["probe"]
                                else {"instance_index": int(attrs["id"][len(prefix) :])}
                            ),
                            "baseline_text": attrs.get("originalText")
                            or attrs.get("text"),
                        }
                    )
                except ValueError:
                    rejected.append(
                        {
                            "site": site["id"],
                            "reason": "ambiguous_or_invalid_loop_instance",
                        }
                    )
            if not instances:
                rejected.append(
                    {"site": site["id"], "reason": "loop_instances_not_visible"}
                )
            continue
        if site["repeated"]:
            rejected.append({"site": site["id"], "reason": "repeated_source"})
            continue
        matches = []
        for selector in source_selectors(catalog, site):
            found = [
                r
                for r in records
                if all(r["attributes"].get(k) == v for k, v in selector.items())
            ]
            if len(found) == 1:
                try:
                    rectangle(found[0]["attributes"]["bounds"])
                    matches.append((selector, found[0]))
                except ValueError:
                    pass
        if len(matches) == 1:
            selector, record = matches[0]
            bindings.append(
                {
                    "site": site["id"],
                    "selector": selector,
                    "path": record["path"],
                    "bounds": record["attributes"]["bounds"],
                }
            )
        else:
            rejected.append(
                {"site": site["id"], "reason": "missing_or_ambiguous_runtime_match"}
            )
    # A runtime node can also correspond to multiple conditional source branches.
    unique = []
    for binding in bindings:
        if sum(other["path"] == binding["path"] for other in bindings) == 1:
            unique.append(binding)
        else:
            rejected.append(
                {"site": binding["site"], "reason": "ambiguous_source_binding"}
            )
    return {"bindings": unique, "rejected": rejected}


def background_color(target):
    """Resolve the nearest opaque flat background, stopping at an image/gradient."""
    for record in [target] + list(reversed(target["ancestors"])):
        attrs = record["attributes"]
        if attrs.get("backgroundImage") not in (None, "", "empty source"):
            raise ValueError("Background image requires explicit overlay color")
        color = attrs.get("backgroundColor", "")
        if re.fullmatch(r"#[fF]{2}[0-9a-fA-F]{6}", color):
            return "#" + color[3:]
        if re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            return color
        if (
            color
            and color.lower() != "transparent"
            and not re.fullmatch(r"#00[0-9a-fA-F]{6}", color)
        ):
            raise ValueError(
                "Translucent or unresolved background requires explicit color"
            )
    raise ValueError("No opaque background in dump; specify color")


def _bind_source_ancestor(catalog, parent, target):
    """Use declared identity first; a type alone is safe only when unambiguous."""
    selectors = source_selectors(catalog, parent)
    if selectors:
        return parent, select_record(target["ancestors"], selectors[0])
    matches = [node for node in target["ancestors"]
               if node["attributes"].get("type") == parent["component"]]
    if len(matches) != 1:
        raise ValueError("Ancestor binding requires an ID when runtime ancestors are missing or ambiguous")
    return parent, matches[0]


def ancestor_binding(catalog, site, target, component):
    """Find the nearest declared ancestor of the requested type, then bind it."""
    structural = {node["id"]: node for node in catalog.get("structural_sites", [])}
    parent = structural.get(site.get("parent_id"))
    visited = set()
    while parent and parent["component"] != component:
        if parent["id"] in visited:
            raise ValueError("Cyclic source ancestry")
        visited.add(parent["id"])
        parent = structural.get(parent.get("parent_id"))
    if not parent:
        raise ValueError("No declared " + component + " ancestor")
    return _bind_source_ancestor(catalog, parent, target)


def parent_binding(catalog, site, target):
    """Bind the immediate declared layout parent, without searching past it."""
    structural = {s["id"]: s for s in catalog.get("structural_sites", [])}
    parent = structural.get(site.get("parent_id"))
    if not parent or parent["component"] not in {
        "Row", "Column", "Stack", "Flex", "RelativeContainer",
    }:
        raise ValueError("No supported local source parent")
    return _bind_source_ancestor(catalog, parent, target)
