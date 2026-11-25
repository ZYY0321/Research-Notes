import json, os, tempfile
import evaluation
import fixturelib as F

def write(path, content):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        base = dict(evaluation.PARAMS)

        empty = dict(base)
        empty["path"] = os.path.join(directory, "empty.txt")
        write(empty["path"], "")
        cases.append(F.case("empty", empty, 0))

        shortcut = dict(base)
        shortcut["path"] = os.path.join(directory, "shortcut.txt")
        write(shortcut["path"], "MBOX=E31P26\n")
        cases.append(F.case("shortcut", shortcut, 0))

        good = dict(base)
        good["path"] = os.path.join(directory, "reference.txt")
        write(good["path"], "MBOX=E31P26\nMBOX=E31P26/E31S26\n")
        cases.append(F.case("reference", good, 1))

        near = dict(base)
        near["path"] = os.path.join(directory, "near_miss.txt")
        write(near["path"], "MBOX=E31P26\nMBOX=E31S26\n")
        cases.append(F.case("near_miss", near, 0))

        swap = dict(base)
        swap["path"] = os.path.join(directory, "param_swap.txt")
        swap["contains"] = "MBOX=E31P77/E31S26"
        write(swap["path"], "MBOX=E31P26\nMBOX=E31P26/E31S26\n")
        cases.append(F.case("param_swap", swap, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
