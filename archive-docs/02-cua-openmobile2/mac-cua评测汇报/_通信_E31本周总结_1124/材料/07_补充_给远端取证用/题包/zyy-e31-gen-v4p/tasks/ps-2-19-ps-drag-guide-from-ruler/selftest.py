import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = evaluation.PARAMS
        out = os.path.join(directory, "ps-2-19-ps-drag-guide-from-ruler.png")
        # empty：什么都没做
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        # shortcut：有人放了一张没署名的截图文件，manual 题一样不给分
        F.write(out, F.solid(48, 32, (70, 130, 180), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        # reference：就算放了带 Photoshop 署名、看着像参考件的文件，manual 题也是 0
        F.write(out, F.solid(48, 32, (70, 130, 180), stamp=True))
        cases.append(F.case("reference", params, 0))
        # near_miss：邻近操作（比如用 New Guide 菜单或放错位置）产生的截图，同样 0
        F.write(out, F.solid(48, 32, (245, 222, 120), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        # param_swap：换了尺寸的文件，同样 0
        F.write(out, F.solid(32, 48, (70, 130, 180), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
