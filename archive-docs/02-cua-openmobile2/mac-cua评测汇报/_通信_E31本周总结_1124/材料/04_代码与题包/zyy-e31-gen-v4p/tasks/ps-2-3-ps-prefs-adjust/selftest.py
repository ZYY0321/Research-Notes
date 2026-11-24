import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = evaluation.PARAMS
        # 不可评分题：无论环境里有什么，score 恒为 0，五类夹具期望都是 0。
        cases.append(F.case("empty", params, 0))
        cases.append(F.case("shortcut", params, 0))
        cases.append(F.case("reference", params, 0))
        cases.append(F.case("near_miss", params, 0))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
