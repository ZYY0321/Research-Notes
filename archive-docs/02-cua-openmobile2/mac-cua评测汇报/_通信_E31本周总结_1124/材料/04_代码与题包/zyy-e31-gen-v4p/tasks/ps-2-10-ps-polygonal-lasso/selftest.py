import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        artifact = os.path.join(directory, "ps-2-10-ps-polygonal-lasso.psd")
        F.remove(artifact)
        cases.append(F.case("empty", params, 0))
        F.write(artifact, F.solid(32, 24, (120, 80, 40), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(artifact, F.solid(32, 24, (120, 80, 40), stamp=True))
        cases.append(F.case("reference", params, 0))
        F.write(artifact, F.solid(32, 24, (120, 80, 200), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(artifact, F.solid(48, 24, (120, 80, 40), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
