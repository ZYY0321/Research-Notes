"""E20 collectable list: tasks scored 1 whose structured label says collect directly or after masking, plus a 10-item spot-check sample.

python3 collect_list.py  ->  analysis/可收清单_E20.md
Reads raw/<batch>/*.json and analysis/标签/*.json. The 美图 production batch (raw/e20-mb) is included once it has been pulled.
"""
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCHES = {"E20A-ds-sky-wps-jy-1109": ("A WPS+剪映基础题", "https://内网地址:16443/results/%s/cases/%s"),
           "E20B-ds-sky-e14-1109": ("B 对照应用", "https://内网地址:16443/results/%s/cases/%s"),
           "E20C-ds-sky-e12paired-1109": ("C 受阻配对", "https://内网地址:16443/results/%s/cases/%s"),
           "e20-mb": ("D 美图（生产机）", "http://内网地址:18081/runs/%s/cases/%s")}
APP = {"wb": "WPS 表格", "jb": "剪映", "mb": "美图", "lo": "LibreOffice", "ob": "OBS/Obsidian", "wp": "WPS 文字/演示",
       "e1": "WPS 表格（受阻配对）"}
KIND = {"direct": "直接收", "mask": "遮掉后收"}


def websearch_errors(r):
    return sum(1 for s in r["steps"] if s["kind"] == "error" and "web search" in s.get("text", ""))


def main():
    rows, pulled, scored = [], [], collections.Counter()
    for batch, (name, view) in BATCHES.items():
        d = ROOT / "raw" / batch
        if not d.exists():
            continue
        pulled.append(name)
        for p in sorted(d.glob("*.json")):
            r = json.loads(p.read_text())
            if r.get("score") != 1:
                continue
            scored[name] += 1
            lp = ROOT / "analysis" / "标签" / p.name
            lab = json.loads(lp.read_text()) if lp.exists() else None
            if not lab or lab.get("collectable") not in KIND:
                continue
            c = r.get("counts") or {}
            rows.append(dict(batch=name, app=APP.get(r["task_id"][:2], r["task_id"][:2]), type=r.get("scenario") or "—",
                             task=r["task_id"], kind=lab["collectable"], mask=(lab.get("mask_steps") or "").strip(),
                             reason=(lab.get("collectable_reason") or "").replace("|", "/").replace("\n", " "),
                             steps=len(r["steps"]), gui=c.get("gui", 0), shell=c.get("shell", 0), osa=c.get("osascript", 0),
                             images=c.get("images", 0), ws=websearch_errors(r), done=lab.get("task_done"),
                             link=view % (r["run_id"], r["task_id"]), md="逐条/%s.md" % p.stem))

    L = ["类型：材料 ｜ 归属：E20 DeepSeek 批量覆盖 ｜ 状态：脚本 `scripts/collect_list.py` 生成，不手改；分数来自评分器，能否收来自 TokenHub 标签（未独立复核、未人工抽查）",
         "", "# E20 可收清单（DeepSeek v4.1-flash · Sky · 默认只用 GUI 提示 · effort high）", "",
         "条件：评分 1 分，且结构化标签判「直接收」或「遮掉后收」。已纳入：%s。" % "、".join(pulled), ""]
    by_b = collections.Counter((x["batch"], x["kind"]) for x in rows)
    L += ["| 批次 | 1 分 | 直接收 | 遮掉后收 | 合计可收 |", "|---|---|---|---|---|"]
    for batch, (name, _) in BATCHES.items():
        if name in pulled:
            L.append("| %s | %d | %d | %d | %d |" % (name, scored[name], by_b[(name, "direct")], by_b[(name, "mask")],
                                                     by_b[(name, "direct")] + by_b[(name, "mask")]))
    L.append("| 合计 | %d | %d | %d | %d |" % (sum(scored.values()), sum(1 for x in rows if x["kind"] == "direct"),
                                               sum(1 for x in rows if x["kind"] == "mask"), len(rows)))

    by_app = collections.defaultdict(list)
    for x in rows:
        by_app[x["app"]].append(x)
    L += ["", "按应用和题型：", ""]
    for app in sorted(by_app):
        t = collections.Counter(x["type"] for x in by_app[app])
        L.append("- **%s**（%d）：%s" % (app, len(by_app[app]), "、".join("%s %d" % kv for kv in t.most_common())))

    sample, seen = [], set()
    for kind in ("direct", "mask"):
        for app in sorted(by_app):
            for x in sorted(by_app[app], key=lambda x: (-x["steps"], x["task"])):
                if x["kind"] == kind and (app, x["type"]) not in seen:
                    sample.append(x); seen.add((app, x["type"])); break
    for x in sorted(rows, key=lambda x: (-x["steps"], x["task"])):
        if len(sample) >= 10:
            break
        if (x["app"], x["type"]) not in seen:
            sample.append(x); seen.add((x["app"], x["type"]))
    sample = sample[:10]
    L += ["", "## 建议先抽查的 10 条", "",
          "每个应用各挑直接收、遮掉后收各一条，题型不重复，同类里优先步数多的（更容易暴露问题）。看完这 10 条觉得标签靠谱，再决定整批交。", ""]
    for x in sample:
        L.append("- [%s](%s)（%s · %s · %s，%d 步%s）[分析](%s)：%s%s" % (
            x["task"], x["link"], x["app"], x["type"], KIND[x["kind"]], x["steps"],
            "，遮第 %s 步" % x["mask"] if x["mask"] else "", x["md"], x["reason"][:120],
            "（有 %d 次联网断连）" % x["ws"] if x["ws"] else ""))

    L += ["", "## 全部可收（按应用、题型）", "",
          "列：步数 = 记录里的步骤数；GUI/命令行/AppleScript = 调用次数；截图 = 返回给模型的图片数。", "",
          "| 应用 | 题型 | 题 | 收法 | 遮哪些步 | 步数 | GUI | 命令行 | AppleScript | 截图 | 联网断连 | 理由 | 分析 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in sorted(rows, key=lambda x: (x["app"], x["type"], x["task"])):
        L.append("| %s | %s | [%s](%s) | %s | %s | %d | %d | %d | %d | %d | %s | %s | [看](%s) |" % (
            x["app"], x["type"], x["task"], x["link"], KIND[x["kind"]], x["mask"] or "—", x["steps"], x["gui"], x["shell"],
            x["osa"], x["images"], x["ws"] or "", x["reason"][:80], x["md"]))
    out = ROOT / "analysis" / "可收清单_E20.md"
    out.write_text("\n".join(L) + "\n")
    print("wrote", out, len(rows), "rows;", dict(scored))


if __name__ == "__main__":
    main()
