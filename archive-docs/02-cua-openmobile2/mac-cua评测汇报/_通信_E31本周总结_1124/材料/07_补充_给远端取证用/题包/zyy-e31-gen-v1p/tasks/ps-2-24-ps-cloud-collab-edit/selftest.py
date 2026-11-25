import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        # 不可评分题：无论本机处于什么状态，score 都是 0。
        cases.append(F.case("empty", params, 0))
        # shortcut：即使有人在输出目录放了无关文件，也不得分。
        F.write(directory + "/ps-2-24-ps-cloud-collab-edit.txt", b"cloud saved")
        cases.append(F.case("shortcut", params, 0))
        # reference：就算真的完成了云文档协作，本机也核不到，仍是 0。
        cases.append(F.case("reference", params, 0))
        # near_miss：只把文档存成本地 PSD 而没走云文档，同样是 0。
        F.write(directory + "/local-only.psd", b"8BPS")
        cases.append(F.case("near_miss", params, 0))
        # param_swap：换别的文件名或内容也一样是 0。
        F.write(directory + "/other.txt", b"collab")
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
