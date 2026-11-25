import json, tempfile
import evaluation
import fixturelib as F

SAMPLE = """Sampling process 4242 for 3 seconds with 1 millisecond of run time between samples
Call graph:
    800 Thread_1
    + 800 start (in dyld) + 0
    +   700 main (in Adobe Photoshop 2026) + 20
    +     400 run (in AppKit) + 8
Binary Images:
       0x1000 - 0x2000 com.adobe.Photoshop
"""
NOTE = "我看了 Photoshop 的 call graph，也提到了 Binary Images，但这不是取样输出。\n"
HEADINGS = "Sampling process 1 for 1 seconds\nCall graph:\nBinary Images:\n"


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(dict(evaluation.PARAMS), directory)
        out = params["path"]
        if not str(out).startswith(directory):
            raise SystemExit("path escaped the temp directory")
        F.remove(out)
        results.append(F.case("empty", params, 0))
        F.write(out, F.solid(8, 8, (1, 2, 3), stamp=False))
        results.append(F.case("shortcut", params, 0))
        F.write(out, SAMPLE)
        results.append(F.case("reference", params, 1))
        F.write(out, NOTE)
        results.append(F.case("near_miss", params, 0))
        F.write(out, HEADINGS)
        results.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
