import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        sepia = tuple(params["samples"][0]["rgb"])
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, sepia, stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(width, height, sepia, stamp=True))
        cases.append(F.case("reference", params, 1))
        cool = (sepia[2], sepia[1], sepia[0])
        F.write(out, F.solid(width, height, cool, stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(width + 4, height, sepia, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
