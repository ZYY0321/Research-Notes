import json, tempfile
import evaluation
import fixturelib as F

TIFF_II = b"II*\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00"
TIFF_MM = b"MM\x00*\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00"
PSD_SEED = b"8BPS\x00\x01" + b"\x00" * 6 + b"\x00\x03\x00\x00\x00\x10\x00\x00\x00\x10\x00\x08\x00\x03" + b"\x00" * 14


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, PSD_SEED)
        cases.append(F.case("shortcut", params, 0))
        F.write(out, TIFF_II)
        cases.append(F.case("reference", params, 1))
        F.write(out, F.solid(16, 16, (30, 90, 160), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, TIFF_MM)
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))


if __name__ == "__main__":
    main()
