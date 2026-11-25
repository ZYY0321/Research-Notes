import json, os, tempfile
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = dict(evaluation.PARAMS)
        note = os.path.join(directory, "figma-1-figma-tour-file-utilities.txt")
        # empty: 什么也没做
        cases.append(F.case("empty", params, 0))
        # shortcut: 只建了个空文件就说看完了
        with open(note, "w", encoding="utf-8") as handle:
            handle.write("")
        cases.append(F.case("shortcut", params, 0))
        # reference: 认真查看后写了区域名称与位置，manual 题照样是 0，等人工确认
        with open(note, "w", encoding="utf-8") as handle:
            handle.write("File utilities：文件相关实用功能区域，位于 Figma Design 界面顶部文件菜单附近。")
        cases.append(F.case("reference", params, 0))
        # near_miss: 查看的是 Explore 探索浏览区域，不是 File utilities 的主题
        with open(note, "w", encoding="utf-8") as handle:
            handle.write("Explore：探索浏览区域。")
        cases.append(F.case("near_miss", params, 0))
        # param_swap: 把说明写到了别的文件名
        other = os.path.join(directory, "figma-1-figma-tour-explore.txt")
        with open(other, "w", encoding="utf-8") as handle:
            handle.write("File utilities：文件相关实用功能区域。")
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
