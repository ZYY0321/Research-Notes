import json
import evaluation
import fixturelib as F

def main():
    cases = []
    params = dict(evaluation.PARAMS)
    for label in ["empty", "shortcut", "reference", "near_miss", "param_swap"]:
        cases.append(F.case(label, params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
