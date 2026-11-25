import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        note = os.path.join(directory, "ps-2-28-ps-ts-macos-format-open.txt")
        F.remove(note)
        cases.append(F.case("empty", params, 0))
        F.write(note, b"shortcut note")
        cases.append(F.case("shortcut", params, 0))
        F.write(note, "\u5df2\u6309\u5b98\u65b9\u65b9\u5411\u6392\u67e5\uff0c\u6587\u4ef6\u5df2\u80fd\u5728 Photoshop \u6253\u5f00".encode("utf-8"))
        cases.append(F.case("reference", params, 0))
        F.write(note, b"near miss note")
        cases.append(F.case("near_miss", params, 0))
        F.write(note, b"param swap note")
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
