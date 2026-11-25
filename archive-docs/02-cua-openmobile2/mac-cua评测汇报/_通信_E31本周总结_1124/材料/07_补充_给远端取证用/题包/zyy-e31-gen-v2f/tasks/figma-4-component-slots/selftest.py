import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        out = os.path.join(directory, "figma-4-component-slots.png")
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(16, 16, (200, 10, 10), rgba=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(16, 16, (200, 10, 10), rgba=True))
        cases.append(F.case("reference", params, 0))
        F.write(out, F.solid(16, 16, (10, 200, 10), rgba=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(20, 16, (200, 10, 10), rgba=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
