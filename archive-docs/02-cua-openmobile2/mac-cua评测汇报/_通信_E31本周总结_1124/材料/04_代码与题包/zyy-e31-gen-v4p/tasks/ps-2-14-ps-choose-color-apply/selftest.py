import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        color = tuple(params["samples"][0]["rgb"])
        width, height = params["width"], params["height"]
        seed_color = (60, 60, 60)

        # empty: 没有产物
        F.remove(out)
        cases.append(F.case("empty", params, 0))

        # shortcut: 别的程序生成了颜色正确的 PNG，但没有 Photoshop 署名
        F.write(out, F.solid(width, height, color, stamp=False))
        cases.append(F.case("shortcut", params, 0))

        # reference: Photoshop 署名、整幅画面都是指定颜色
        F.write(out, F.solid(width, height, color, stamp=True))
        cases.append(F.case("reference", params, 1))

        # near_miss: 打开种子图后没把选定颜色用上去就直接保存（仍是种子底色）
        F.write(out, F.solid(width, height, seed_color, stamp=True))
        cases.append(F.case("near_miss", params, 0))

        # param_swap: 把颜色通道顺序弄反（用成了 RGB(180,119,31)）
        swapped = (color[2], color[1], color[0])
        F.write(out, F.solid(width, height, swapped, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
