import json, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        out = directory + "/ps-2-7-ps-layer-comps.psd"
        # 不可评分题：五类夹具 score 都应为 0
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        # 捷径：用别的程序随手写一个同名假 PSD
        F.write(out, b"8BPS" + b"\x00" * 32)
        cases.append(F.case("shortcut", params, 0))
        # 参考：即便真做了（Photoshop 存出带图层复合的 PSD），程序也读不出图层复合，score 仍为 0
        F.write(out, b"8BPS" + b"\x00" * 64)
        cases.append(F.case("reference", params, 0))
        # 近错：邻近操作（只改了图层名、没创建图层复合）保存的 PSD
        F.write(out, b"8BPS" + b"\x00" * 48)
        cases.append(F.case("near_miss", params, 0))
        # 换参数：存成了别的格式
        F.write(directory + "/ps-2-7-ps-layer-comps.png", b"\x89PNG\r\n\x1a\n")
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
