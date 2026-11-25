import json, tempfile
import evaluation
import fixturelib as F

EMOJI = "\U0001F389"

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(dict(evaluation.PARAMS), directory)

        empty = dict(params)
        empty["dump"] = ""
        cases.append(F.case("empty", empty, 0))

        # 走捷径：建了草稿、主题对，但只在正文打了表情的英文名，没插入字符本身
        shortcut = dict(params)
        shortcut["dump"] = "SUBJECT=E31-MAIL25-EMOJI\nBODY=party popper tada\nTO=\nATTACH=\n----\n"
        cases.append(F.case("shortcut", shortcut, 0))

        good = dict(params)
        good["dump"] = "SUBJECT=E31-MAIL25-EMOJI\nBODY=hello " + EMOJI + " world\nTO=\nATTACH=\n----\n"
        cases.append(F.case("reference", good, 1))

        # 邻近操作：把表情插进了主题而不是正文，正文没有该字符
        near = dict(params)
        near["dump"] = "SUBJECT=E31-MAIL25-EMOJI " + EMOJI + "\nBODY=hello world\nTO=\nATTACH=\n----\n"
        cases.append(F.case("near_miss", near, 0))

        # 换参数：另一封主题不同的草稿里有表情
        other = dict(params)
        other["subject"] = "E31-MAIL25-OTHER"
        other["dump"] = good["dump"]
        cases.append(F.case("param_swap", other, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
