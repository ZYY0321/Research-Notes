import json, plistlib, tempfile
import evaluation
import fixturelib as F


def dump(path, obj):
    with open(path, "wb") as handle:
        plistlib.dump(obj, handle, fmt=plistlib.FMT_XML)


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(dict(evaluation.PARAMS), directory)
        paths = params["paths"]
        if not paths or any(not str(path).startswith(directory) for path in paths):
            raise SystemExit("path escaped the temp directory")
        target = paths[0]
        F.remove(target)
        results.append(F.case("empty", params, 0))
        F.write(target, "SignaturePlacedAboveQuotedText false")
        results.append(F.case("shortcut", params, 0))
        dump(target, {"SignaturePlacedAboveQuotedText": False})
        results.append(F.case("reference", params, 1))
        dump(target, {"SignaturePlacedAboveQuotedText": True})
        results.append(F.case("near_miss", params, 0))
        dump(target, {"AlwaysMatchDefaultFont": False})
        results.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
