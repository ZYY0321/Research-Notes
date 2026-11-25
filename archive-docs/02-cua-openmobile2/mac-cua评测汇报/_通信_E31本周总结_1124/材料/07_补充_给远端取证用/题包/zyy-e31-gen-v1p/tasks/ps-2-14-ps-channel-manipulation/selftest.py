import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        seed = params["keep"]["path"]
        width, height = params["width"], params["height"]
        target = tuple(params["samples"][0]["rgb"])
        seed_color = (120, 80, 200)
        F.remove(out)
        F.remove(seed)
        cases.append(F.case("empty", params, 0))
        F.write(seed, F.solid(width, height, seed_color, stamp=False))
        F.write(out, F.solid(width, height, target, stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(width, height, target, stamp=True))
        cases.append(F.case("reference", params, 1))
        wrong_channel = (255, seed_color[1], seed_color[2])
        F.write(out, F.solid(width, height, wrong_channel, stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(height, width, target, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
