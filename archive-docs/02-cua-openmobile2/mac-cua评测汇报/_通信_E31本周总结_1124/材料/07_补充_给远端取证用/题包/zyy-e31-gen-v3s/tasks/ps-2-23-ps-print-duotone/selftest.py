import json, tempfile
import evaluation
import fixturelib as F
import e31_grade_psd as P

CASES = [('empty', None, 0), ('shortcut', {'sign': 'stock', 'mode': 8, 'channels': 1, 'color': b'\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00', 'layers': [[]]}, 0), ('reference', {'sign': '2026', 'mode': 8, 'channels': 1, 'color': b'\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00', 'layers': [[]]}, 1), ('near_miss', {'sign': '2026', 'mode': 1, 'channels': 1, 'layers': [[]]}, 0), ('param_swap', {'sign': '2026', 'mode': 3, 'channels': 3, 'layers': [[]]}, 0)]


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(dict(evaluation.PARAMS), directory)
        out = params["path"]
        if not str(out).startswith(directory):
            raise SystemExit("path escaped the temp directory")
        for name, kwargs, expect in CASES:
            if kwargs is None:
                F.remove(out)
            else:
                F.write(out, P.build_psd(**kwargs))
            results.append(F.case(name, params, expect))
    print("RESULT " + json.dumps({"cases": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
