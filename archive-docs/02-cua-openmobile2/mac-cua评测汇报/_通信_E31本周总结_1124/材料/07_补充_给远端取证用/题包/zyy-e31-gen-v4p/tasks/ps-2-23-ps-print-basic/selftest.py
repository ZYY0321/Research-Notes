import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    params = evaluation.PARAMS
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        # manual 题：无论桌面上留下什么文件，程序评分恒为 0，五类夹具全部期望 0。
        out = os.path.join(directory, "ps-2-23-ps-print-basic.png")
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        # shortcut：别的程序凭空生成一个同名小图，也不该得分。
        F.write(out, F.solid(48, 32, (200, 80, 40), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        # reference：即便真用 Photoshop 存出带署名的文件，打印动作本身没有文件级结果，仍为 0。
        F.write(out, F.solid(48, 32, (200, 80, 40), stamp=True))
        cases.append(F.case("reference", params, 0))
        # near_miss：邻近操作（例如另存导出而不是打印）留下的产物，同样 0。
        F.write(out, F.solid(48, 32, (40, 80, 200), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        # param_swap：换了尺寸的产物，同样 0。
        F.write(out, F.solid(32, 48, (200, 80, 40), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
