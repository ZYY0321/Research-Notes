import json
import evaluation
import fixturelib as F

def main():
    cases = []
    # manual 题：五类夹具 score 都应为 0
    empty = dict(evaluation.PARAMS)
    cases.append(F.case("empty", empty, 0))
    shortcut = dict(evaluation.PARAMS)
    cases.append(F.case("shortcut", shortcut, 0))
    reference = dict(evaluation.PARAMS)
    cases.append(F.case("reference", reference, 0))
    near_miss = dict(evaluation.PARAMS)
    cases.append(F.case("near_miss", near_miss, 0))
    param_swap = dict(evaluation.PARAMS)
    param_swap["grade_note"] = "其它面板（如 General、Viewing）不算达成"
    cases.append(F.case("param_swap", param_swap, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
