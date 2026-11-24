import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        out = os.path.join(directory, "ps-2-8-artboard-add-to-doc.psd")
        # empty: 什么都没产出
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        # shortcut: 用别的程序写了一个假 PSD 顶替
        with open(out, "wb") as handle:
            handle.write(b"not-a-real-psd")
        cases.append(F.case("shortcut", params, 0))
        # reference: 即便 Photoshop 真的保存了带画板的 PSD，manual 题也判 0
        with open(out, "wb") as handle:
            handle.write(b"8BPS" + b"\x00" * 22 + b"artboard-added")
        cases.append(F.case("reference", params, 0))
        # near_miss: 邻近操作——新建了一个画板文档另存，而不是给已有文档加画板
        with open(out, "wb") as handle:
            handle.write(b"8BPS" + b"\x00" * 22 + b"new-artboard-doc")
        cases.append(F.case("near_miss", params, 0))
        # param_swap: 把种子文档原样另存，没有追加任何画板
        with open(out, "wb") as handle:
            handle.write(b"8BPS" + b"\x00" * 22)
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
