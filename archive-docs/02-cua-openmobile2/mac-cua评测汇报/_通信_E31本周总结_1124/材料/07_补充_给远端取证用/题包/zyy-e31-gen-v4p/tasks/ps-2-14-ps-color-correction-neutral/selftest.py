import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        neutral = (128, 128, 128)
        cast = (128, 128, 178)
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, neutral, stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(width, height, neutral, stamp=True))
        cases.append(F.case("reference", params, 1))
        F.write(out, F.solid(width, height, cast, stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(width + 4, height, neutral, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
