import json
import evaluation
import fixturelib as F

def main():
    cases = []
    base = dict(evaluation.PARAMS)

    empty = dict(base)
    cases.append(F.case("empty", empty, 0))

    shortcut = dict(base)
    shortcut["note"] = "claimed-done-without-check"
    cases.append(F.case("shortcut", shortcut, 0))

    reference = dict(base)
    reference["note"] = "server-settings-verified-per-prompts"
    cases.append(F.case("reference", reference, 0))

    near_miss = dict(base)
    near_miss["note"] = "checked-account-information-panel-instead"
    cases.append(F.case("near_miss", near_miss, 0))

    param_swap = dict(base)
    param_swap["note"] = "checked-different-account"
    cases.append(F.case("param_swap", param_swap, 0))

    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
