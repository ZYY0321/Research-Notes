import json, tempfile
import evaluation
import fixturelib as F


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(dict(evaluation.PARAMS), directory)
        out = params["path"]
        if not str(out).startswith(directory):
            raise SystemExit("path escaped the temp directory")
        F.remove(out)
        results.append(F.case("empty", params, 0))
        F.write(out, F.solid(800, 600, (20, 40, 80), stamp=False))
        results.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(800, 600, (20, 40, 80), stamp=True))
        results.append(F.case("reference", params, 1))
        F.write(out, F.solid(800, 599, (20, 40, 80), stamp=True))
        results.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(600, 800, (20, 40, 80), stamp=True))
        results.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
