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

        # shortcut: 只填了主题和收件人就按发送，正文没按要求写
        shortcut = dict(params)
        shortcut["dump"] = "SUBJECT=E31-M212 Suggestions Send\nBODY=nope\nTO=e31-m212@example.com\nATTACH=\n----\n"
        cases.append(F.case("shortcut", shortcut, 0))

        # reference: Suggestions 触发发信后，Sent 里有对应主题、收件人、正文的信
        good = dict(params)
        good["dump"] = "SUBJECT=E31-M212 Suggestions Send\nBODY=hello E31-M212-SENT-BODY line\nTO=e31-m212@example.com\nATTACH=\n----\n"
        cases.append(F.case("reference", good, 1))

        # near_miss: 邻近操作——信写好了但只存成草稿没发出去，收件人未落上
        near = dict(params)
        near["dump"] = "SUBJECT=E31-M212 Suggestions Send\nBODY=hello E31-M212-SENT-BODY line\nTO=\nATTACH=\n----\n"
        cases.append(F.case("near_miss", near, 0))

        # param_swap: 换了主题参数，原参考件不应再得分
        other = dict(params)
        other["subject"] = "E31-M212 Other Subject"
        other["dump"] = good["dump"]
        cases.append(F.case("param_swap", other, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
