"""Add trace IDs in an isolated source copy before normal-page acquisition."""

from pathlib import Path
import shutil
from truncator.source.project import scan
from truncator.mutation.mutations import apply_patches
from truncator.common.storage import save, contained, digest
from truncator.source.source_attributes import effective_attributes


def instrument(profile, destination):
    destination = Path(destination).resolve()
    source = Path(profile["source"]).resolve()
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError("Instrumented copy and original source must be disjoint")
    destination.mkdir(parents=True, exist_ok=False)
    catalog = scan(profile)
    edits, entries, skipped = [], [], []
    loop_edits = {}
    for site in catalog["sites"]:
        try:
            attributes = effective_attributes(site)
        except ValueError as error:
            skipped.append({"site": site["id"], "reason": str(error)})
            continue
        if any(a["name"] == "id" for a in attributes):
            skipped.append({"site": site["id"], "reason": "existing_id_preserved"})
            continue
        prefix = "truncator_probe_" + site["id"]
        expression = "'" + prefix + "'"
        loops = site.get("loops", [])
        builder_keys = site.get("builder_keys", [])
        if site.get("global_builder"):
            skipped.append(
                {"site": site["id"], "reason": "global_builder_scope_unsupported"}
            )
            continue
        if site.get("shared_builder") and not builder_keys:
            skipped.append({"site": site["id"], "reason": "builder_without_scalar_key"})
            continue
        if (
            len(loops) > 1
            or builder_keys
            or any(loop.get("key_expression") for loop in loops)
        ):
            names = [key.split(".")[0] for key in builder_keys] + [
                name for loop in loops for name in loop["names"]
            ]
            if len(names) != len(set(names)) or (
                any(name in {"ForEach", "LazyForEach"} for name in site["context"])
                and not loops
            ):
                skipped.append(
                    {
                        "site": site["id"],
                        "reason": "shadowed_or_unsupported_instance_scope",
                    }
                )
                continue
            parts = [
                "encodeURIComponent(String(" + name + "))" for name in builder_keys
            ]
            for loop in loops:
                if loop.get("key_expression"):
                    parts.append(
                        "encodeURIComponent(String(" + loop["key_expression"] + "))"
                    )
                    continue
                index_name = loop["index_name"] or "__truncatorIndex_" + loop["key"]
                if not loop["index_name"]:
                    loop_edits[(site["file"], loop["key"])] = {
                        "file": site["file"],
                        "start": loop["parameters_end"],
                        "end": loop["parameters_end"],
                        "before": "",
                        "after": ", " + index_name + ": number",
                    }
                parts.append("String(" + index_name + ")")
            prefix = "truncator_context_" + site["id"] + "_"
            expression = "'" + prefix + "' + " + " + '|' + ".join(parts)
        elif site["repeated"]:
            loop = site.get("loop")
            if not loop:
                skipped.append(
                    {"site": site["id"], "reason": "unsupported_nested_or_custom_loop"}
                )
                continue
            index_name = loop["index_name"] or "__truncatorIndex_" + loop["key"]
            if not loop["index_name"]:
                loop_edits[(site["file"], loop["key"])] = {
                    "file": site["file"],
                    "start": loop["parameters_end"],
                    "end": loop["parameters_end"],
                    "before": "",
                    "after": ", " + index_name + ": number",
                }
            prefix += "_"
            expression = "'" + prefix + "' + String(" + index_name + ")"
        edits.append(
            {
                "file": site["file"],
                "start": site["end"],
                "end": site["end"],
                "before": "",
                "after": ".id(" + expression + ")",
            }
        )
        entries.append(
            {
                "original_site": site["id"],
                "file": site["file"],
                "line": site["line"],
                "component": site["component"],
                "probe_prefix": prefix,
                "repeated": site["repeated"] or bool(builder_keys),
                "identity_basis": [
                    "item_key" if loop.get("key_expression") else "index"
                    for loop in loops
                ]
                + (["builder_parameters"] if builder_keys else []),
            }
        )
    edits.extend(loop_edits.values())
    copied = destination / "source"
    shutil.copytree(
        source,
        copied,
        ignore=shutil.ignore_patterns(
            ".git",
            ".hvigor",
            "build",
            ".idea",
            "screenshots",
            "node_modules",
            "oh_modules",
        ),
    )
    for relative in sorted({edit["file"] for edit in edits}):
        path = contained(copied, relative)
        original = path.read_bytes().decode("utf-8")
        if digest(original) != catalog["files"][relative]:
            raise ValueError("Source changed while instrumenting " + relative)
        updated = apply_patches(original, [e for e in edits if e["file"] == relative])
        path.write_bytes(updated.encode("utf-8"))
    result = {
        **profile,
        "source": str(copied),
        "instrumentation": str(destination / "source-map.json"),
    }
    parsed = scan(result)
    changed = {edit["file"] for edit in edits}
    if any(d["file"] in changed for d in parsed["diagnostics"]):
        raise ValueError("Trace instrumentation introduced parse diagnostics")
    save(
        destination / "source-map.json",
        {
            "original_source": str(source),
            "instrumented_source": str(copied),
            "entries": entries,
            "skipped": skipped,
            "patches": edits,
            "original_files": catalog["files"],
        },
    )
    save(destination / "profile.json", result)
    save(destination / "catalog.json", parsed)
    return result
