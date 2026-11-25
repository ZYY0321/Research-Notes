import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        color = tuple(params["samples"][0]["rgb"])
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, color, rgba=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(width, height, color, rgba=True))
        cases.append(F.case("reference", params, 1))
        wrong_color = (color[0], color[1], color[2] - 30)
        F.write(out, F.solid(width, height, wrong_color, rgba=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(height, width, color, rgba=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
