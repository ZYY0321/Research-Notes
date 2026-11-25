import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        marker = os.path.join(directory, "ps-2-3-ps-content-credentials-social.txt")
        # 不可评分题：五类夹具 score 都应为 0
        F.remove(marker)
        cases.append(F.case("empty", params, 0))
        F.write(marker, b"linked")
        cases.append(F.case("shortcut", params, 0))
        F.write(marker, b"social account linked in Content Credentials")
        cases.append(F.case("reference", params, 0))
        F.write(marker, b"different social account linked")
        cases.append(F.case("near_miss", params, 0))
        F.write(marker, b"content credentials enabled but no account linked")
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
