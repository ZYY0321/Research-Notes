import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(dict(evaluation.PARAMS), directory)
        empty = dict(params)
        empty["dump"] = ""
        cases.append(F.case("empty", empty, 0))
        shortcut = dict(params)
        shortcut["dump"] = "SUBJECT=Re: Weekly notes\nBODY=E31-MAIL-2-4-REPLY\nTO=\nATTACH=\n----\n"
        cases.append(F.case("shortcut", shortcut, 0))
        good = dict(params)
        good["dump"] = "SUBJECT=Re: E31-MAIL-2-4-REPLY\nBODY=Got it, thanks.\nTO=\nATTACH=\n----\n"
        cases.append(F.case("reference", good, 1))
        near = dict(params)
        near["dump"] = "SUBJECT=Re: E31-MAIL-2-3-NOTE\nBODY=Got it, thanks.\nTO=\nATTACH=\n----\n"
        cases.append(F.case("near_miss", near, 0))
        other = dict(params)
        other["subject"] = "Re: E31-MAIL-9-9-OTHER"
        other["dump"] = good["dump"]
        cases.append(F.case("param_swap", other, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
