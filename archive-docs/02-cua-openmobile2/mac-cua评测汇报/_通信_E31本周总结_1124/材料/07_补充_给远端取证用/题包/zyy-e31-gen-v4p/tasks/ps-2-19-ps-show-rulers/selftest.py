import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(32, 16, (30, 120, 200), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(32, 16, (30, 120, 200), stamp=True))
        cases.append(F.case("reference", params, 0))
        F.write(out, F.solid(32, 16, (200, 120, 30), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(16, 32, (30, 120, 200), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
