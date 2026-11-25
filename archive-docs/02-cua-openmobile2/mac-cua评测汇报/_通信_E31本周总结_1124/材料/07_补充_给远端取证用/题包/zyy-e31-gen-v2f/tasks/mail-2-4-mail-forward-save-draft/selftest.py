import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(dict(evaluation.PARAMS), directory)
        good_dump = "SUBJECT=Fwd: E31-MAIL-2-4 status report\nBODY=\nTO=e31.forward.target@example.com\nATTACH=\n----\n"
        empty = dict(params)
        empty["dump"] = ""
        cases.append(F.case("empty", empty, 0))
        shortcut = dict(params)
        shortcut["dump"] = "SUBJECT=Fwd: E31-MAIL-2-4 status report\nBODY=\nTO=\nATTACH=\n----\n"
        cases.append(F.case("shortcut", shortcut, 0))
        good = dict(params)
        good["dump"] = good_dump
        cases.append(F.case("reference", good, 1))
        near = dict(params)
        near["dump"] = "SUBJECT=Re: E31-MAIL-2-4 status report\nBODY=\nTO=sender.e31@example.com\nATTACH=\n----\n"
        cases.append(F.case("near_miss", near, 0))
        other = dict(params)
        other["to_contains"] = "wrong.target@example.com"
        other["dump"] = good_dump
        cases.append(F.case("param_swap", other, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
