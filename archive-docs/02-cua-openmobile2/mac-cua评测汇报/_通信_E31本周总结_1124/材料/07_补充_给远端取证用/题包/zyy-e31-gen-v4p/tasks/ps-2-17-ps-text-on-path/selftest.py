import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        seed = params["differ_from"]["path"]
        width, height = params["width"], params["height"]
        seed_color = (245, 245, 245)
        text_color = (40, 40, 60)
        F.write(seed, F.solid(width, height, seed_color, stamp=False))
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, text_color, stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(width, height, text_color, stamp=True))
        cases.append(F.case("reference", params, 1))
        F.write(out, F.solid(width, height, seed_color, stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(width - 8, height, text_color, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
