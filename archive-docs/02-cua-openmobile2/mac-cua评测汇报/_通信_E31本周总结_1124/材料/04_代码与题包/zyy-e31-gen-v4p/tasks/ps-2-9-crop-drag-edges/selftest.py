import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        color = (120, 180, 220)
        width, height = 48, 32
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, color, stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(width, height, color, stamp=True))
        cases.append(F.case("reference", params, 1))
        wrong_color = (120, 180, 180)
        F.write(out, F.solid(width, height, wrong_color, stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(width + 8, height, color, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
