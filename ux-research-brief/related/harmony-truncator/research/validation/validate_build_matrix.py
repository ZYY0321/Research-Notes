"""Build original and automatically selected baselines; persist every outcome."""

import argparse
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from truncator.execution.campaign_source import prepare_application, prepare_baseline
from truncator.common.storage import read, save


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(args.out).resolve()
    results = []
    for filename in args.profiles:
        profile = read(filename)
        folder = root / Path(filename).stem
        for mode in ("original", "automatic"):
            started = time.time()
            row = {"profile": filename, "mode": mode}
            try:
                if mode == "original":
                    run = folder / "original"
                    prepare_baseline(profile, run)
                else:
                    _, catalog, run = prepare_application(profile, {}, folder / "automatic")
                    row["source_choice"] = read(folder / "automatic/source-choice.json")["mode"]
                    row["sites"] = len(catalog["sites"])
                row.update(status="built", run=str(run), build=read(run / "build.json"))
            except Exception as error:
                row.update(status="failed", error=str(error))
            row["seconds"] = time.time() - started
            results.append(row)
            save(root / "build-matrix.json", results)
            print(Path(filename).stem, mode, row["status"], round(row["seconds"], 1), flush=True)
    return int(any(row["status"] != "built" for row in results))


if __name__ == "__main__":
    raise SystemExit(main())
