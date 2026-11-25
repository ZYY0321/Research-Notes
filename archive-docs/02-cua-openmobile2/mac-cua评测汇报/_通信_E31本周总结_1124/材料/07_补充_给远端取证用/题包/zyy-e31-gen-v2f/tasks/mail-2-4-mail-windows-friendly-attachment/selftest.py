import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        cases.append(F.case("empty", dict(params), 0))
        cases.append(F.case("shortcut", dict(params), 0))
        cases.append(F.case("reference", dict(params), 0))
        cases.append(F.case("near_miss", dict(params), 0))
        cases.append(F.case("param_swap", dict(params), 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
