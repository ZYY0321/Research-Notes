import json
import evaluation
import fixturelib as F

def main():
    cases = []
    base = dict(evaluation.PARAMS)
    cases.append(F.case("empty", dict(base), 0))
    cases.append(F.case("shortcut", dict(base), 0))
    cases.append(F.case("reference", dict(base), 0))
    cases.append(F.case("near_miss", dict(base), 0))
    cases.append(F.case("param_swap", dict(base), 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
