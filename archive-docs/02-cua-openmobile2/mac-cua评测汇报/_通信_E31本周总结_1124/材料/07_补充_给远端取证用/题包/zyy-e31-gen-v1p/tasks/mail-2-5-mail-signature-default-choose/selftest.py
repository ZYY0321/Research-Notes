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
        shortcut["dump"] = "SUBJECT=Signature Test\nBODY=Email without signature\nTO=\nATTACH=\n----\n"
        cases.append(F.case("shortcut", shortcut, 0))
        
        good = dict(params)
        good["dump"] = "SUBJECT=Signature Test\nBODY=Email text. SignatureA-Content\nTO=\nATTACH=\n----\n"
        cases.append(F.case("reference", good, 1))
        
        near = dict(params)
        near["dump"] = "SUBJECT=Signature Test\nBODY=Email text. SignatureB-Content\nTO=\nATTACH=\n----\n"
        cases.append(F.case("near_miss", near, 0))
        
        other = dict(params)
        other["body_contains"] = "SignatureB-Content"
        other["dump"] = good["dump"]
        cases.append(F.case("param_swap", other, 0))
        
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
