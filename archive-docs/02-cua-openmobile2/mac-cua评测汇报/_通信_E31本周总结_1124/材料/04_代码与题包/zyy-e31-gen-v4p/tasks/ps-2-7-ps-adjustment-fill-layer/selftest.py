import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        out = os.path.join(directory, "ps-2-7-ps-adjustment-fill-layer.psd")
        # empty: 什么都没有
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        # shortcut: 用别的程序写了一个没有署名的文件
        F.write(out, F.solid(32, 16, (70, 120, 180), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        # reference: 即使造出带署名的成品，manual 题也不给分
        F.write(out, F.solid(32, 16, (70, 120, 180), stamp=True))
        cases.append(F.case("reference", params, 0))
        # near_miss: 邻近操作——只改了像素颜色（相当于直接调整图像而不是加图层）
        F.write(out, F.solid(32, 16, (170, 120, 80), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        # param_swap: 换了尺寸的成品
        F.write(out, F.solid(48, 32, (70, 120, 180), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
