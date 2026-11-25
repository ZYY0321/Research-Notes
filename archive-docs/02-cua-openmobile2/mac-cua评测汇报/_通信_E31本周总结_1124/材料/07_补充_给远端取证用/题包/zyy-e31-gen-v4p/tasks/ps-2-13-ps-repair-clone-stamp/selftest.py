import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        background = tuple(params["samples"][0]["rgb"])
        pattern = (190, 40, 40)
        width, height = params["width"], params["height"]

        # empty: 没有产物
        F.remove(out)
        cases.append(F.case("empty", params, 0))

        # shortcut: 用别的程序生成的纯背景图，没有 Photoshop 署名
        F.write(out, F.solid(width, height, background, stamp=False))
        cases.append(F.case("shortcut", params, 0))

        # reference: 仿制图章正确覆盖后整幅为背景绿，Photoshop 存出
        F.write(out, F.solid(width, height, background, stamp=True))
        cases.append(F.case("reference", params, 1))

        # near_miss: 取样来源搞反了，把图案颜色涂满全图（邻近操作结果）
        F.write(out, F.solid(width, height, pattern, stamp=True))
        cases.append(F.case("near_miss", params, 0))

        # param_swap: 尺寸不对
        F.write(out, F.solid(width + 4, height, background, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
