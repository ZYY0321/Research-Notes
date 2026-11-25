import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        seed = os.path.join(directory, "ps-2-18-neural-filter-seed.png")
        params["differ_from"] = dict(params["differ_from"], path=seed)
        params["keep"] = dict(params["keep"], path=seed)
        out = params["path"]
        width, height = params["width"], params["height"]
        base = (120, 90, 60)
        filtered = (160, 130, 100)
        F.write(seed, F.solid(width, height, base, stamp=False))
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, base, stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(width, height, filtered, stamp=True))
        cases.append(F.case("reference", params, 1))
        F.write(out, F.solid(width, height, base, stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(width + 4, height, filtered, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
