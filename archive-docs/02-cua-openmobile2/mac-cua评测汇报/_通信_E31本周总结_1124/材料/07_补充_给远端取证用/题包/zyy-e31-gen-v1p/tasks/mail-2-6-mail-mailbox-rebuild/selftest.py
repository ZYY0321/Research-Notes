import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        # 不可评分题：五类夹具 score 都应为 0
        empty = dict(params)
        cases.append(F.case("empty", empty, 0))
        shortcut = dict(params)
        cases.append(F.case("shortcut", shortcut, 0))
        reference = dict(params)
        cases.append(F.case("reference", reference, 0))
        near = dict(params)
        cases.append(F.case("near_miss", near, 0))
        swap = dict(params)
        swap["grade_note"] = "param swap: 换成别的邮箱也一样不可评分"
        cases.append(F.case("param_swap", swap, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
