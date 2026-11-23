"""Persist and validate the review trail shared by rebuild and delivery."""

import json
import shutil
from truncator.common.storage import read, save, digest


def validated_history(run, plan):
    ancestors = plan.get("curation", {}).get("ancestors", [])
    edges = {
        (parent["plan_id"], parent["hap_sha256"]):
            ancestors[index + 1]["plan_id"] if index + 1 < len(ancestors) else plan["id"]
        for index, parent in enumerate(ancestors)
    }
    seen, records = set(), []
    for path in sorted((run / "curation-history").glob("*.json")):
        entry = read(path)
        review = entry["review"]
        checksum = digest(json.dumps(review, sort_keys=True))
        if checksum != entry["review_sha256"] or checksum != path.stem:
            raise ValueError("Curation review history changed")
        parent = (entry["parent_plan_id"], entry["parent_hap_sha256"])
        if (edges.get(parent) != entry["child_plan_id"]
                or review["plan_id"] != parent[0] or review["hap_sha256"] != parent[1]
                or sorted(entry["removed_mutations"]) != sorted(
                    key for key, item in review["decisions"].items() if item["decision"] == "remove")):
            raise ValueError("Curation review history does not match adjacent rebuild versions")
        seen.add(parent)
        records.append((path.name, entry))
    if seen != set(edges):
        raise ValueError("Curation review history is incomplete")
    return records


def carry_history(parent_run, child_run, parent_plan, child_plan, review, hap_sha256):
    records = validated_history(parent_run, parent_plan)
    review_hash = digest(json.dumps(review, sort_keys=True))
    entry = {"parent_plan_id": parent_plan["id"], "parent_hap_sha256": hap_sha256,
             "child_plan_id": child_plan["id"], "source_run": str(parent_run),
             "removed_mutations": child_plan["curation"]["removed_mutations"],
             "review_sha256": review_hash, "review": review}
    for name, record in [*records, (review_hash + ".json", entry)]:
        target = child_run / "curation-history" / name
        if target.exists() and read(target) != record:
            raise ValueError("Existing curation history differs from the recorded review")
        save(target, record)
    validated_history(child_run, child_plan)


def export_history(run, destination, plan):
    for name, entry in validated_history(run, plan):
        source = run / "curation-history" / name
        target = destination / "curation-history" / name
        target.parent.mkdir(exist_ok=True)
        shutil.copy2(source, target)
        if read(target) != entry:
            raise ValueError("Curation history changed during export")
