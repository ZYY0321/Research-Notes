import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = evaluation.PARAMS
        out = os.path.join(directory, "ps-2-8-frame-from-shape-text.psd")
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, b"8BPS")
        cases.append(F.case("shortcut", params, 0))
        F.write(out, b"8BPS" + b"\x00" * 64)
        cases.append(F.case("reference", params, 0))
        F.write(out, b"8BPS" + b"\x01" * 64)
        cases.append(F.case("near_miss", params, 0))
        F.write(out, b"8BPS" + b"\x02" * 32)
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
