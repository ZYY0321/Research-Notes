import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        out = os.path.join(directory, "ps-2-28-ps-ts-sample-spindump.txt")
        # manual 题：五类夹具的期望分都是 0
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, b"placeholder file created without sampling anything\n")
        cases.append(F.case("shortcut", params, 0))
        F.write(out, b"Sampling process 123 for 10 seconds\nSample analysis of process 123 (Adobe Photoshop 2026)\nCall graph:\n    start -> main -> event loop\n")
        cases.append(F.case("reference", params, 0))
        F.write(out, b"Spindump\nProcess: Finder [456]\nDuration: 10.00s\n")
        cases.append(F.case("near_miss", params, 0))
        F.write(out, b"Crash report for Adobe Photoshop 2026 after it already quit\n")
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
