import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        shot = os.path.join(directory, "ps-2-19-ps-show-alignment-grid.png")
        F.remove(shot)
        cases.append(F.case("empty", params, 0))
        F.write(shot, F.solid(32, 32, (200, 200, 200), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(shot, F.solid(32, 32, (200, 200, 200), stamp=True))
        cases.append(F.case("reference", params, 0))
        F.write(shot, F.solid(32, 32, (120, 120, 120), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(shot, F.solid(48, 32, (200, 200, 200), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
