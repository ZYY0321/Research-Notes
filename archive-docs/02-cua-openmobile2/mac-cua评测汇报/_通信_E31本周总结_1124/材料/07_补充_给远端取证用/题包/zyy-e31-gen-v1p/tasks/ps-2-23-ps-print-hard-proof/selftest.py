import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        decoy = os.path.join(directory, "ps-2-23-ps-print-hard-proof.png")
        # 本题是人工核查题：硬打样的结果在纸面或打印队列，不在文件里，任何夹具都应得 0。
        cases.append(F.case("empty", params, 0))
        F.write(decoy, F.solid(32, 32, (10, 20, 30), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(decoy, F.solid(48, 32, (40, 160, 90), stamp=True))
        cases.append(F.case("reference", params, 0))
        F.write(decoy, F.solid(48, 32, (40, 160, 130), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(decoy, F.solid(32, 48, (40, 160, 90), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
