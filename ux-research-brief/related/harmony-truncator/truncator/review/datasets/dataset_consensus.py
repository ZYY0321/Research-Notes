"""Order-independent reconciliation of repeated exported target observations."""

from collections import defaultdict
import json

FIELDS = ("component", "mechanism", "axis", "label", "content_status", "recovery_status", "revision")
UNKNOWN = {None, "unknown", "unresolved", "uncertain", "not-tested", "inconclusive"}


def reconcile(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["capture_sha256"], row["target_key"])].append(row)
    units, duplicates, conflicts = [], [], []
    for key, variants in sorted(groups.items(), key=lambda pair: str(pair[0])):
        variants.sort(key=lambda row: (row["export"], row["sample"], json.dumps(row, sort_keys=True)))
        representative = max(variants, key=lambda r: (r.get("label") not in UNKNOWN,
            sum(r.get(k) not in UNKNOWN for k in ("content_status", "recovery_status"))))
        unit = {**representative, "sources": [{"export": r["export"], "sample": r["sample"]} for r in variants]}
        differences = {}
        for field in FIELDS:
            values = sorted({r.get(field) for r in variants if r.get(field) not in UNKNOWN})
            if len(values) > 1:
                differences[field] = values
            elif values and field not in {"content_status", "recovery_status", "label"}:
                unit[field] = values[0]
        payloads = {json.dumps(r.get("evidence_sha256"), sort_keys=True) for r in variants}
        if len(payloads) > 1:
            differences["evidence_sha256"] = sorted(payloads)
        unit["consensus"] = "conflicting" if differences else "consistent"
        if differences:
            conflicts.append({"capture_sha256": key[0], "target_key": key[1],
                              "differences": differences, "observations": variants})
        duplicates.extend({"export": r["export"], "sample": r["sample"]} for r in variants[1:])
        units.append(unit)
    return units, duplicates, conflicts
