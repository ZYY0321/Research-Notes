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
        near = dict(params)
        cases.append(F.case("near_miss", near, 0))
        swap = dict(params)
        swap["grade_note"] = "param swap: 另一类 Suggestions 动作"
        cases.append(F.case("param_swap", swap, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
