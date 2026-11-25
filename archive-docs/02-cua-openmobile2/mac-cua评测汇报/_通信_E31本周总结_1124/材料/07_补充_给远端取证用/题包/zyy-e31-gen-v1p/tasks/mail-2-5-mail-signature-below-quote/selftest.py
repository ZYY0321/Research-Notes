import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(dict(evaluation.PARAMS), directory)
        empty = dict(params)
        cases.append(F.case("empty", empty, 0))
        shortcut = dict(params)
        cases.append(F.case("shortcut", shortcut, 0))
        reference = dict(params)
        cases.append(F.case("reference", reference, 0))
        near_miss = dict(params)
        cases.append(F.case("near_miss", near_miss, 0))
        param_swap = dict(params)
        param_swap["reason"] = "其它题的说明"
        cases.append(F.case("param_swap", param_swap, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
