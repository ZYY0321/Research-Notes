import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    params = evaluation.PARAMS
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        out = os.path.join(directory, "ps-2-1-ps-whatsnew-prompt-to-edit.png")
        # manual 题：五类夹具 score 都应为 0
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(32, 32, (200, 120, 60), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(32, 32, (220, 110, 50), stamp=True))
        cases.append(F.case("reference", params, 0))
        F.write(out, F.solid(32, 32, (60, 120, 200), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(48, 32, (220, 110, 50), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
