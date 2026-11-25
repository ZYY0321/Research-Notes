import json
import evaluation
import fixturelib as F

def main():
    cases = []
    params = evaluation.PARAMS
    
    cases.append(F.case("empty", params, 0))
    cases.append(F.case("shortcut", params, 0))
    cases.append(F.case("reference", params, 0))
    cases.append(F.case("near_miss", params, 0))
    cases.append(F.case("param_swap", params, 0))
    
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
