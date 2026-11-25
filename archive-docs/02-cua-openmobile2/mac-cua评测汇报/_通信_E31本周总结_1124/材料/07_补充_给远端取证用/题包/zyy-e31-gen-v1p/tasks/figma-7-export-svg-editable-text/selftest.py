import json, os, copy, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = copy.deepcopy(evaluation.PARAMS)
        out = os.path.join(directory, "figma-7-export-svg-editable-text.svg")
        for check in params["checks"]:
            check["path"] = out
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, "E31 Editable\n".encode("utf-8"))
        cases.append(F.case("shortcut", params, 0))
        svg_reference = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="32" viewBox="0 0 64 32"><text x="4" y="20" font-family="Inter" font-size="12">E31 Editable</text></svg>'
        F.write(out, svg_reference.encode("utf-8"))
        cases.append(F.case("reference", params, 1))
        svg_outlined = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="32" viewBox="0 0 64 32"><path d="M4 20L10 8L16 20ZM20 20L26 8L32 20Z" fill="#000000"/></svg>'
        F.write(out, svg_outlined.encode("utf-8"))
        cases.append(F.case("near_miss", params, 0))
        svg_swapped = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="32" viewBox="0 0 64 32"><text x="4" y="20" font-family="Inter" font-size="12">Other Label</text></svg>'
        F.write(out, svg_swapped.encode("utf-8"))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
