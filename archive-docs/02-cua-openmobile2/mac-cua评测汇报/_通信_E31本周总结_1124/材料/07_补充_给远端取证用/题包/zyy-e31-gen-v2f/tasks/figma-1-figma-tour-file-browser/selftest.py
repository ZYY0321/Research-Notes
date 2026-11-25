import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        note = os.path.join(directory, "figma-1-figma-tour-file-browser.txt")
        F.remove(note)
        cases.append(F.case("empty", params, 0))
        F.write(note, b"")
        cases.append(F.case("shortcut", params, 0))
        F.write(note, "\u5728\u6587\u4ef6\u6d4f\u89c8\u5668\u91cc\u770b\u5230\u4e86\u6700\u8fd1\u6587\u4ef6\u5217\u8868".encode("utf-8"))
        cases.append(F.case("reference", params, 0))
        F.write(note, "\u6253\u5f00\u4e86\u4e00\u4e2a\u8bbe\u8ba1\u6587\u4ef6".encode("utf-8"))
        cases.append(F.case("near_miss", params, 0))
        F.write(note, "\u65b0\u5efa\u4e86\u4e00\u4e2a\u6587\u4ef6".encode("utf-8"))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
