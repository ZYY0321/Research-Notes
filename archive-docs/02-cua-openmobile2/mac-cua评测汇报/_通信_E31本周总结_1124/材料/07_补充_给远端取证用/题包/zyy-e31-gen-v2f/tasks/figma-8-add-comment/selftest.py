import json, tempfile, os
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        note = os.path.join(directory, "figma-8-add-comment.txt")
        # empty: 什么都没做
        cases.append(F.case("empty", params, 0))
        # shortcut: 只写了留档 txt，没有在 Figma 里发评论，manual 仍为 0
        F.write(note, "E31 review: please double-check the spacing here".encode("utf-8"))
        cases.append(F.case("shortcut", params, 0))
        # reference: 人工核查题，程序评分永远 0
        cases.append(F.case("reference", params, 0))
        # near_miss: 邻近操作（比如只拖了多人光标、开了分支，没发评论），manual 仍为 0
        F.write(note, "opened branch, no comment posted".encode("utf-8"))
        cases.append(F.case("near_miss", params, 0))
        # param_swap: 换了评论文字也一样，manual 仍为 0
        F.write(note, "some other comment text".encode("utf-8"))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
