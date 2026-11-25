import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        out = os.path.join(directory, "figma-4-create-component.png")
        color = (30, 144, 255)
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(32, 32, color, rgba=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(32, 32, color, rgba=True))
        cases.append(F.case("reference", params, 0))
        F.write(out, F.solid(32, 32, (30, 144, 95), rgba=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(48, 32, color, rgba=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
