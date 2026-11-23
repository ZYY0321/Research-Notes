"""Reinspect archived comparison pairs from unchanged source images and trees."""

import argparse
from pathlib import Path

from research.production_evidence.comparison import inspect_target, compare_targets
from truncator.common.storage import read, save, digest


def recheck(paths, output):
    output = Path(output)
    rows = []
    for filename in paths:
        filename = Path(filename).resolve()
        previous = read(filename)
        observations = {}
        for side in ("reference", "injected"):
            source = previous[side]
            for kind in ("tree", "screenshot"):
                if digest(Path(source[kind]).read_bytes()) != source[kind + "_sha256"]:
                    raise ValueError("Archived comparison source changed: " + source[kind])
            observations[side] = inspect_target(source["tree"], source["screenshot"], source["selector"])
        comparison = compare_targets(observations["reference"], observations["injected"])
        destination = filename.stem + "-" + digest(str(filename))[:8] + ".json"
        save(output / destination, comparison)
        boundary = comparison["boundary_comparison"]
        rows.append({
            "source_comparison": str(filename),
            "source_comparison_sha256": digest(filename.read_bytes()),
            "rechecked_comparison": destination,
            "reference_selector": observations["reference"]["selector"],
            "boundary_status": boundary["status"],
            "boundary_differences": boundary["different_fields"],
            "boundary_unknowns": boundary["unknown_fields"],
            "local_differences": comparison["local_assessment"]["different_fields"],
            "source_hashes_verified": True,
        })
    save(output / "verification.json", {
        "pairs": rows,
        "method": "Reinspect original files after checking archived SHA256; compare boundary constraints without voting by field count.",
        "commercial_behavior": "historic interaction evidence unavailable; no new behavioral verdict",
        "visual_labels": "unchanged; retain existing per-pair visual reviews",
    })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparisons", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    for row in recheck(args.comparisons, args.out):
        print(Path(row["source_comparison"]).name, row["boundary_status"], row["boundary_differences"])


if __name__ == "__main__":
    main()
