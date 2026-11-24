import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        white = (255, 255, 255)
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, white, stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(width, height, white, stamp=True))
        cases.append(F.case("reference", params, 1))
        light_gray = (250, 250, 250)
        F.write(out, F.solid(width, height, light_gray, stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(height, width, white, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
