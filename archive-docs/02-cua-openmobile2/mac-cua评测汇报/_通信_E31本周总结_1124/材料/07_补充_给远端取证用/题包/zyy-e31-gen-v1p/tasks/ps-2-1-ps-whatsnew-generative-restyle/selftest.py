import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        out = os.path.join(directory, "ps-2-1-ps-whatsnew-generative-restyle.png")
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(48, 32, (120, 120, 120), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(48, 32, (30, 80, 160), stamp=True))
        cases.append(F.case("reference", params, 0))
        F.write(out, F.solid(48, 32, (120, 120, 120), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(32, 48, (30, 80, 160), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
