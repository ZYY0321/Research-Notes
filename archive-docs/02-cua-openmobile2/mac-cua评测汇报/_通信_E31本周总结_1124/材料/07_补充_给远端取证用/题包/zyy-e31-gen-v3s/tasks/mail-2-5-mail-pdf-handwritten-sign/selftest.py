import json, tempfile
import evaluation
import fixturelib as F

INK = b"%PDF-1.4\n1 0 obj << /Type /Annot /Subtype /Ink /Rect [0 0 10 10] >> endobj\n%%EOF\n"
LINK = b"%PDF-1.4\n1 0 obj << /Type /Annot /Subtype /Link /Rect [0 0 10 10] >> endobj\n%%EOF\n"
HIGH = b"%PDF-1.4\n1 0 obj << /Type /Annot /Subtype /Highlight /Rect [0 0 10 10] >> endobj\n%%EOF\n"


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(dict(evaluation.PARAMS), directory)
        out = params["path"]
        if not str(out).startswith(directory):
            raise SystemExit("path escaped the temp directory")
        F.remove(out)
        results.append(F.case("empty", params, 0))
        F.write(out, F.solid(16, 16, (0, 0, 0), stamp=False))
        results.append(F.case("shortcut", params, 0))
        F.write(out, INK)
        results.append(F.case("reference", params, 1))
        F.write(out, LINK)
        results.append(F.case("near_miss", params, 0))
        F.write(out, HIGH)
        results.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
