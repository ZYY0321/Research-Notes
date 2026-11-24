import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = evaluation.PARAMS
        # 不可评分题：五类夹具 score 全部应为 0。
        cases.append(F.case("empty", params, 0))
        # shortcut：旁路造一个同名 PNG 也不该得分。
        stray = os.path.join(directory, "ps-2-23-ps-print-soft-proof.png")
        F.write(stray, F.solid(48, 32, (120, 60, 30), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        # reference：即使有带 Photoshop 署名的成品文件，manual 仍为 0。
        F.write(stray, F.solid(48, 32, (120, 60, 30), stamp=True))
        cases.append(F.case("reference", params, 0))
        # near_miss：邻近操作（硬打样/导出打印样张）留下的文件同样不计分。
        F.write(stray, F.solid(48, 32, (30, 60, 120), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        # param_swap：换尺寸的产物也不计分。
        F.write(stray, F.solid(32, 48, (120, 60, 30), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
