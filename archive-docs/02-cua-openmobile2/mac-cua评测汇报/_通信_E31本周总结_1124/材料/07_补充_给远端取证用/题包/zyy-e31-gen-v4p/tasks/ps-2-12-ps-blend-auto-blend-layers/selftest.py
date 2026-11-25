import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        # manual 题：五类夹具 score 全部期望 0
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        # shortcut：别的程序直接写出同名 PNG（无 Photoshop 署名）
        F.write(out, F.solid(32, 32, (120, 60, 200), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        # reference：带 Photoshop 署名的保存结果；manual 仍为 0
        F.write(out, F.solid(32, 32, (120, 60, 200), stamp=True))
        cases.append(F.case("reference", params, 0))
        # near_miss：邻近操作——把单张输入照片原样另存到目标路径，没有做 Auto-Blend 合成
        F.write(out, F.solid(32, 32, (0, 128, 255), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        # param_swap：存到了错误的文件名，目标路径为空
        F.remove(out)
        F.write(out + ".wrong.png", F.solid(32, 32, (120, 60, 200), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
