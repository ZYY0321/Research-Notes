"""Pure review decisions and retained plans shared by rebuild and export."""

import json

from truncator.planning.composition import combined_edits, validate_plan
from truncator.common.storage import digest

DECISIONS = {"keep", "remove", "pending"}
CONTENT_STATUSES = {"clipped", "complete", "uncertain"}
RECOVERY_STATUSES = {"recovered", "not-recovered", "not-tested", "inconclusive", "not-applicable"}


def validate_observation_labels(content_status, recovery_status):
    if content_status is None and recovery_status is None:
        return
    if content_status not in CONTENT_STATUSES or recovery_status not in RECOVERY_STATUSES:
        raise ValueError("Content and recovery status must both be explicitly supported values")
    if content_status == "complete" and recovery_status not in {"not-applicable", "not-tested"}:
        raise ValueError("Complete content does not require recovery")


def review_template(plan, hap_sha256, captures=None):
    result = {
        "schema_version": 2 if captures is not None else 1,
        "plan_id": plan["id"],
        "hap_sha256": hap_sha256,
        "decisions": {
            member["id"]: {"decision": "pending", "note": ""}
            for member in plan.get("mutations", [plan])
        },
    }
    if captures is not None:
        result["captures"] = captures
    return result


def retained_plan(plan, review, hap_sha256):
    validate_plan(plan)
    if "mutations" not in plan:
        raise ValueError("Defect-level curation requires a combined application plan")
    if (
        review.get("schema_version") not in {1, 2}
        or review.get("plan_id") != plan["id"]
    ):
        raise ValueError("Review belongs to a different plan or unsupported schema")
    if review.get("hap_sha256") != hap_sha256:
        raise ValueError("Review belongs to a different application package")
    decisions = review.get("decisions", {})
    members = {member["id"]: member for member in plan["mutations"]}
    if set(decisions) != set(members):
        raise ValueError("Review must contain exactly the mutation IDs of this package")
    for item in decisions.values():
        if not isinstance(item, dict) or item.get("decision") not in DECISIONS:
            raise ValueError("Unsupported review decision")
        if not isinstance(item.get("note", ""), str):
            raise ValueError("Review notes must be text")
        validate_observation_labels(item.get("content_status"), item.get("recovery_status"))
    retained = [
        member
        for key, member in members.items()
        if decisions[key]["decision"] != "remove"
    ]
    retained_ids = {member["id"] for member in retained}
    patches, hashes = combined_edits(retained)
    # Notes are deliberately absent from the plan and cannot affect the edits.
    result = {
        "schema_version": 3,
        "source_root": plan["source_root"],
        "mutations": retained,
        "patches": patches,
        "file_hashes": hashes,
        "pages": [
            {
                **page,
                "mutation_ids": [
                    key for key in page["mutation_ids"] if key in retained_ids
                ],
            }
            for page in plan["pages"]
        ],
        "selection": plan.get("selection", {}),
        "curation": {
            "parent_plan_id": plan["id"],
            "parent_hap_sha256": hap_sha256,
            "removed_mutations": sorted(set(members) - retained_ids),
            "ancestors": [*plan.get("curation", {}).get("ancestors", []),
                          {"plan_id": plan["id"], "hap_sha256": hap_sha256}],
        },
        "review": "pending",
    }
    result["id"] = digest(json.dumps(result, sort_keys=True))[:20]
    validate_plan(result)
    return result


