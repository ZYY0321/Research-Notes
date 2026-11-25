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
        shortcut["dump"] = "SUBJECT=E31-MAIL-BCC-DRAFT\nBODY=wrong content\nTO=\nBCC=bcctest@e31.example.com\nATTACH=\n----\n"
        cases.append(F.case("shortcut", shortcut, 0))
        good = dict(params)
        good["dump"] = "SUBJECT=E31-MAIL-BCC-DRAFT\nBODY=This is a test message for BCC draft.\nTO=\nBCC=bcctest@e31.example.com\nATTACH=\n----\n"
        cases.append(F.case("reference", good, 1))
        near = dict(params)
        near["dump"] = "SUBJECT=E31-MAIL-BCC-DRAFT\nBODY=This is a message for BCC draft.\nTO=\nBCC=bcctest@e31.example.com\nATTACH=\n----\n"
        cases.append(F.case("near_miss", near, 0))
        other = dict(params)
        other["subject"] = "E31-OTHER"
        other["dump"] = good["dump"]
        cases.append(F.case("param_swap", other, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
