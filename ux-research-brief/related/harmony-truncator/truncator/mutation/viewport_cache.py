"""Source edits for a first-layout width cache with an omitted resize update."""

from truncator.mutation.source_edits import attribute_edits, reject_layout_conflicts
from truncator.source.source_attributes import effective_attributes, attribute_text


def cache_patches(site):
    owner = site.get("owner", {})
    if "@Component" not in owner.get("decorators", []) or any(
        decorator.startswith("@ComponentV2")
        for decorator in owner.get("decorators", [])
    ):
        raise ValueError("Width caching requires an enclosing V1 @Component struct")
    if (
        site.get("repeated")
        or site.get("shared_builder")
        or "build" not in site["context"]
    ):
        raise ValueError("Width caching requires a unique viewport in build()")
    reject_layout_conflicts(site, {})
    if any(a["name"] == "onAreaChange"
           for a in site["attributes"] + effective_attributes(site)):
        raise ValueError(
            "Width caching preserves existing onAreaChange handlers; target unsupported"
        )
    widths = [a for a in effective_attributes(site) if a["name"] == "width"]
    if len(widths) != 1 or not attribute_text(widths[0]).strip():
        raise ValueError("Width caching requires one explicit baseline width")
    field = "truncatorCachedWidth_" + site["id"]
    if field in owner.get("members", []):
        raise ValueError("Width cache state name already exists")
    position = owner["insert"]
    if not 0 <= position < site["start"]:
        raise ValueError("Invalid component state insertion position")
    state = "this." + field
    desired = {
        "width": f"{state} > 0 ? {state} : ({attribute_text(widths[0])})",
        "onAreaChange": (
            "(_oldArea: Area, newArea: Area) => { "
            f"if ({state} === 0 && Number(newArea.width) > 0) {{ "
            f"{state} = Number(newArea.width); }} }}"
        ),
    }
    patches = [
        {
            "file": site["file"],
            "start": position,
            "end": position,
            "before": "",
            "after": f"\n  @State {field}: number = 0;\n",
        }
    ]
    for start, end, after in attribute_edits(site, desired):
        patches.append(
            {
                "file": site["file"],
                "start": start,
                "end": end,
                "before": site["snippet"][start - site["start"] : end - site["start"]],
                "after": after,
            }
        )
    return patches
