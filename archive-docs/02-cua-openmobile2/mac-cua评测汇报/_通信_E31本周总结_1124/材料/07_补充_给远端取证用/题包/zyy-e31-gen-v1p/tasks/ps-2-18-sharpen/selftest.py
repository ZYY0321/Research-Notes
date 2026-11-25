import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        seed_path = os.path.join(directory, "ps-2-18-sharpen-seed.png")
        params["differ_from"] = dict(params["differ_from"])
        params["differ_from"]["path"] = seed_path
        out = params["path"]
        width, height = params["width"], params["height"]
        seed_color = (120, 120, 120)
        sharp_color = (180, 180, 180)
        F.write(seed_path, F.solid(width, height, seed_color, stamp=False))
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, sharp_color, stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(width, height, sharp_color, stamp=True))
        cases.append(F.case("reference", params, 1))
        F.write(out, F.solid(width, height, seed_color, stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(width + 4, height, sharp_color, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
