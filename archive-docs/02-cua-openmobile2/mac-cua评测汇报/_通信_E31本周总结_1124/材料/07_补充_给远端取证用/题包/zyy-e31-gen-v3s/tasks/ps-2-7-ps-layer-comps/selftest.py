import json, tempfile
import evaluation
import fixturelib as F
import e31_grade_psd as P

CASES = [('empty', None, 0), ('shortcut', {'sign': 'stock', 'layers': [[]], 'resources': {1065: b'\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'}}, 0), ('reference', {'sign': '2026', 'layers': [[]], 'resources': {1065: b'\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'}}, 1), ('near_miss', {'sign': '2026', 'layers': [[]]}, 0), ('param_swap', {'sign': '2026', 'layers': [[]], 'resources': {1066: b'\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'}}, 0)]


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
