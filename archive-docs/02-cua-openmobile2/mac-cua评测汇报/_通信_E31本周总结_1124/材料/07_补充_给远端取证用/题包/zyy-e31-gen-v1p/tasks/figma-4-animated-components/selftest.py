import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        out = directory + "/figma-4-animated-components.png"
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(24, 12, (30, 144, 255), rgba=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(24, 12, (30, 144, 255), rgba=True))
        cases.append(F.case("reference", params, 0))
        F.write(out, F.solid(24, 12, (30, 104, 255), rgba=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(28, 16, (30, 144, 255), rgba=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
