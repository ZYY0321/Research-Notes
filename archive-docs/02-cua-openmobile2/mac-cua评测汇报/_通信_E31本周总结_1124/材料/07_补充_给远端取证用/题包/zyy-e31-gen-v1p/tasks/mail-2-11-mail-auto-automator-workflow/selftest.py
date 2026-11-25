import json, copy, tempfile
import evaluation
import fixturelib as F

SUBJ = "E31-MAIL-2-11-HELLO"

def block(subject, to):
    return "SUBJECT=" + subject + "\nBODY=E31 automator bulk mail\nTO=" + to + "\nATTACH=\n----\n"

def with_dump(params, dump):
    p = copy.deepcopy(params)
    for c in p["checks"]:
        c["dump"] = dump
    return p

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(copy.deepcopy(evaluation.PARAMS), directory)
        good_dump = block(SUBJ, "alice.e31@example.com") + block(SUBJ, "bob.e31@example.com")
        # empty: 什么都没发
        cases.append(F.case("empty", with_dump(params, ""), 0))
        # shortcut: 没串成批量工作流程，只给一位联系人发了一封
        cases.append(F.case("shortcut", with_dump(params, block(SUBJ, "alice.e31@example.com")), 0))
        # reference: 每位联系人各一封，主题一致
        cases.append(F.case("reference", with_dump(params, good_dump), 1))
        # near_miss: 工作流程跑通、每人各一封，但没按要求设主题（留了例子里的默认主题）
        near_dump = block("Hello", "alice.e31@example.com") + block("Hello", "bob.e31@example.com")
        cases.append(F.case("near_miss", with_dump(params, near_dump), 0))
        # param_swap: 换一个主题参数，不该拿这套成品的分
        swap = with_dump(params, good_dump)
        for c in swap["checks"]:
            c["subject"] = "E31-MAIL-2-11-OTHER"
        cases.append(F.case("param_swap", swap, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
