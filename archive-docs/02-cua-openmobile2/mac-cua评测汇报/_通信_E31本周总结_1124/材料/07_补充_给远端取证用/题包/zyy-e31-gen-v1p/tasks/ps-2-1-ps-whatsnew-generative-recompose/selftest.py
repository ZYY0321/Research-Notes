import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        out = os.path.join(directory, "ps-2-1-ps-whatsnew-generative-recompose.png")
        # manual 题：不管磁盘上有什么文件，score 永远是 0
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        # 捷径件：别的程序生成的平涂 PNG，仍然 0 分
        F.write(out, F.solid(32, 32, (10, 20, 30), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        # 参考件：带 Photoshop 署名的导出 PNG，manual 题也给 0 分
        F.write(out, F.solid(32, 32, (10, 20, 30), stamp=True))
        cases.append(F.case("reference", params, 0))
        # 近错件：只改了颜色（相当于只做了调色而非构图重排），同样 0 分
        F.write(out, F.solid(32, 32, (10, 20, 70), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        # 换参件：只改了尺寸（相当于做了放大而非构图重排），同样 0 分
        F.write(out, F.solid(48, 32, (10, 20, 30), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
