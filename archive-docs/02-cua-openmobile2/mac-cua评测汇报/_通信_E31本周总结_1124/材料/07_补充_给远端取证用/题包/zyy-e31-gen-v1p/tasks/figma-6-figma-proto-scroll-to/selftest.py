import json, tempfile, os
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        out = os.path.join(directory, "figma-6-figma-proto-scroll-to.png")
        # manual 题：五类夹具 score 都应为 0
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(32, 16, (240, 240, 240), rgba=True))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(32, 16, (30, 120, 220), rgba=True))
        cases.append(F.case("reference", params, 0))
        F.write(out, F.solid(32, 16, (30, 120, 180), rgba=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(16, 32, (30, 120, 220), rgba=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
