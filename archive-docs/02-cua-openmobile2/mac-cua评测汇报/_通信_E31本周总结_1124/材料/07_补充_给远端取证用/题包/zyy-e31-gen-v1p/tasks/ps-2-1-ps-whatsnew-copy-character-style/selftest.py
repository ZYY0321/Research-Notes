import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        out = os.path.join(directory, "ps-2-1-ps-whatsnew-copy-character-style.psd")
        # empty：什么产物都没有，manual 题 score 恒为 0
        cases.append(F.case("empty", params, 0))
        # shortcut：只写一个声称完成的文本文件冒充产物，仍是 0
        F.write(out, b"done: copied character style")
        cases.append(F.case("shortcut", params, 0))
        # reference：造一个带 PSD 文件头、看起来像保存结果的产物，manual 题也是 0
        F.write(out, b"8BPS" + b"\x00\x01" + b"SOURCE TARGET same character style")
        cases.append(F.case("reference", params, 0))
        # near_miss：邻近操作——保存了 PSD 但没有拷贝样式（两个文字块样式仍不同），同样 0
        F.write(out, b"8BPS" + b"\x00\x01" + b"SOURCE styleA TARGET styleB untouched")
        cases.append(F.case("near_miss", params, 0))
        # param_swap：把产物存到了别的文件名下，同样 0
        swapped = os.path.join(directory, "ps-2-1-wrong-name.psd")
        F.write(swapped, b"8BPS" + b"\x00\x01" + b"SOURCE TARGET same character style")
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
