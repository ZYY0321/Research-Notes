import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        out = os.path.join(directory, "ps-2-19-ps-new-guide-menu.png")
        # 不可评分题：五类夹具的 score 都应为 0。
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(48, 32, (200, 200, 200), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(48, 32, (200, 200, 200), stamp=True))
        cases.append(F.case("reference", params, 0))
        F.write(out, F.solid(48, 32, (0, 255, 255), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(32, 48, (200, 200, 200), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
