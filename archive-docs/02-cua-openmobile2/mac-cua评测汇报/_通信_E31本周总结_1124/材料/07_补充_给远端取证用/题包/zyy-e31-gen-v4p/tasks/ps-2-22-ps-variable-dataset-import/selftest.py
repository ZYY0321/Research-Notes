import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        out = os.path.join(directory, "ps-2-22-ps-variable-dataset-import.psd")
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, b"8BPS-shortcut-fake")
        cases.append(F.case("shortcut", params, 0))
        F.write(out, b"8BPS-reference-like")
        cases.append(F.case("reference", params, 0))
        F.write(out, b"8BPS-near-miss")
        cases.append(F.case("near_miss", params, 0))
        F.write(out, b"8BPS-param-swap")
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
