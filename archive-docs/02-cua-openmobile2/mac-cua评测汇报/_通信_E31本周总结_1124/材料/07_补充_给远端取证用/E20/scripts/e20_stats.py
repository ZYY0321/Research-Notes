"""E20 tables: per batch/app/type outcomes, why tasks failed, blocked-channel behaviour, collectability, notable behaviours.

python3 e20_stats.py   ->  analysis/统计_E20.md
Reads raw/<batch>/*.json (compact records) and analysis/标签/*.json (structured labels; only quote-verified events count).
"""
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCHES = {"E20A-ds-sky-wps-jy-1109": "A WPS+剪映基础题", "E20B-ds-sky-e14-1109": "B 对照应用",
           "E20C-ds-sky-e12paired-1109": "C 受阻配对", "e20-mb": "D 美图（生产机）"}
APP = {"wb": "WPS 表格", "jb": "剪映", "mb": "美图", "lo": "LibreOffice", "ob": "OBS/Obsidian", "wp": "WPS 文字/演示",
       "e1": "WPS 表格（受阻配对）"}
CLUSTER_VIEW = "https://内网地址:16443/results/%s/cases/%s"
PROD_VIEW = "http://内网地址:18081/runs/%s/cases/%s"


class _View:
    """VIEW % (run_id, task_id): cluster links for A/B/C, production viewer for the 美图 batch (run ids are UUIDs, not run-*)."""
    def __mod__(self, args):
        run, task = args
        return (CLUSTER_VIEW if str(run).startswith("run-") else PROD_VIEW) % (run, task)


VIEW = _View()


def outcome(r):
    if r.get("agent_status") == "not_started":
        return "未开跑"
    s = r.get("score")
    return "1 分" if s == 1 else "0 分" if s == 0 else "无分"


def websearch_errors(r):
    return sum(1 for s in r["steps"] if s["kind"] == "error" and "web search" in s.get("text", ""))


def pct(a, b):
    return "—" if not b else "%d%%" % round(100 * a / b)


def main():
    recs = []
    for batch in BATCHES:
        for p in sorted((ROOT / "raw" / batch).glob("*.json")):
            r = json.loads(p.read_text())
            lab_p = ROOT / "analysis" / "标签" / p.name
            lab = json.loads(lab_p.read_text()) if lab_p.exists() else None
            recs.append((batch, r, lab, p.stem))
    L = ["类型：材料 ｜ 归属：E20 DeepSeek 批量覆盖 ｜ 状态：脚本 `scripts/e20_stats.py` 生成，不手改；分数来自评分器，标签来自 TokenHub（摘录已核对原文），未独立复核",
         "", "环境：公共集群 main，Sky 后端 + Sky 默认只用 GUI 提示，DeepSeek v4.1-flash（火山）effort high，单题 3600 秒，每题 1 次。", ""]

    L += ["## 1. 总体", "", "| 批次 | 题数 | 1 分 | 0 分 | 无分 | 未开跑（集群基础设施） | 1 分 / 开跑 | 有联网搜索断连 |", "|---|---|---|---|---|---|---|---|"]
    for batch, name in BATCHES.items():
        rs = [r for b, r, _, _ in recs if b == batch]
        c = collections.Counter(outcome(r) for r in rs)
        started = len(rs) - c["未开跑"]
        ws = sum(1 for r in rs if websearch_errors(r))
        L.append("| %s | %d | %d | %d | %d | %d | %s | %d |" % (name, len(rs), c["1 分"], c["0 分"], c["无分"], c["未开跑"],
                                                              pct(c["1 分"], started), ws))
    L += ["", "联网搜索断连与结果（只算开跑的题）：", "", "| 批次 | 有断连：条数 / 1 分 | 无断连：条数 / 1 分 |", "|---|---|---|"]
    for batch, name in BATCHES.items():
        rs = [r for b, r, _, _ in recs if b == batch and outcome(r) != "未开跑"]
        w = [r for r in rs if websearch_errors(r)]; n = [r for r in rs if not websearch_errors(r)]
        L.append("| %s | %d / %d（%s） | %d / %d（%s） |" % (name, len(w), sum(r.get("score") == 1 for r in w), pct(sum(r.get("score") == 1 for r in w), len(w)),
                                                         len(n), sum(r.get("score") == 1 for r in n), pct(sum(r.get("score") == 1 for r in n), len(n))))
    L += ["", "未开跑原因（结果里的错误信息）："]
    nr = collections.Counter()
    for b, r, _, _ in recs:
        if outcome(r) == "未开跑":
            nr[(r.get("errors") or ["（无记录）"])[0][:80] if r.get("errors") else "（无记录）"] += 1
    L += ["- %s ×%d" % (k, v) for k, v in nr.most_common()]

    L += ["", "## 2. 按应用和题型（只算开跑的题；题型按题数排序）", ""]
    by = collections.defaultdict(list)
    for b, r, lab, stem in recs:
        if outcome(r) == "未开跑":
            continue
        by[(APP.get(r["task_id"][:2], r["task_id"][:2]), r.get("scenario") or "—")].append((r, lab, stem, b))
    for app in sorted(set(k[0] for k in by)):
        L += ["### " + app, "", "| 题型 | 开跑 | 1 分 | 成功率 | 0 分的题（查看器） |", "|---|---|---|---|---|"]
        for (a, sc), items in sorted(((k, v) for k, v in by.items() if k[0] == app), key=lambda kv: (-len(kv[1]), kv[0][1])):
            ones = sum(1 for r, *_ in items if r.get("score") == 1)
            fails = [(r, b) for r, _, _, b in items if r.get("score") != 1]
            links = "、".join("[%s](%s)" % (r["task_id"], VIEW % (r["run_id"], r["task_id"])) for r, b in fails[:6])
            L.append("| %s | %d | %d | %s | %s |" % (sc, len(items), ones, pct(ones, len(items)), links + (" 等" if len(fails) > 6 else "")))
        L.append("")

    labeled = [(b, r, lab) for b, r, lab, _ in recs if lab and outcome(r) != "未开跑"]
    L += ["## 3. 受阻事件（标签，摘录核对过原文的才计）", "",
          "| 批次 | 有标签条数 | 事件数 | " + " | ".join(["app", "gui_backend", "framework", "model_bridge", "model", "task_or_grader", "unknown"]) +
          " | 静默失败 | 换了路 | 换路后解决 |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for batch, name in BATCHES.items():
        ev = [e for b, r, lab in labeled if b == batch for e in lab.get("blockers", []) if e.get("quote_ok")]
        c = collections.Counter(e.get("layer") for e in ev)
        sw = [e for e in ev if e.get("switch_to") not in (None, "none", "give_up_and_report")]
        L.append("| %s | %d | %d | %s | %s | %d | %s |" % (
            name, sum(1 for b, *_ in labeled if b == batch), len(ev),
            " | ".join(str(c[k]) for k in ["app", "gui_backend", "framework", "model_bridge", "model", "task_or_grader", "unknown"]),
            pct(sum(1 for e in ev if e.get("silent")), len(ev)), len(sw), pct(sum(1 for e in sw if e.get("resolved")), len(sw))))
    L += ["", "最常见的受阻类型（全部批次，前 15）："]
    kinds = collections.Counter("%s/%s" % (e.get("layer"), e.get("kind")) for _, _, lab in labeled for e in lab.get("blockers", []) if e.get("quote_ok"))
    L += ["- %s ×%d" % (k, v) for k, v in kinds.most_common(15)]
    sw_all = collections.Counter(e.get("switch_to") for _, _, lab in labeled for e in lab.get("blockers", [])
                                 if e.get("quote_ok") and e.get("layer") != "model" and e.get("switch_to") not in (None, "none"))
    L += ["", "非模型层受阻后换到了什么：" + "；".join("%s ×%d" % kv for kv in sw_all.most_common())]

    L += ["", "## 4. 受阻配对题（C）逐题", "", "| 题 | 结果 | 受阻事件（层/类型/察觉步-首现步/换到/解决） | 查看器 |", "|---|---|---|---|"]
    for b, r, lab, stem in sorted((x for x in recs if x[0] == "E20C-ds-sky-e12paired-1109"), key=lambda x: x[1]["task_id"]):
        evs = []
        for e in (lab or {}).get("blockers", []):
            if not e.get("quote_ok"):
                continue
            lag = (e["detected_step"] - e["first_step"]) if isinstance(e.get("detected_step"), int) and isinstance(e.get("first_step"), int) else "?"
            evs.append("%s/%s/%s/%s/%s" % (e.get("layer"), e.get("kind"), lag, e.get("switch_to"), "是" if e.get("resolved") else "否"))
        L.append("| %s | %s | %s | [看](%s) |" % (r["task_id"], outcome(r), "；".join(evs) or "—", VIEW % (r["run_id"], r["task_id"])))

    L += ["", "## 5. 能否收（标签）", "", "| 批次 | 直接收 | 遮掉后收 | 不收 | 1 分但标签判未完成 | 非 1 分但标签判完成 |", "|---|---|---|---|---|---|"]
    for batch, name in BATCHES.items():
        rows = [(r, lab) for b, r, lab in labeled if b == batch]
        c = collections.Counter(lab.get("collectable") for _, lab in rows)
        a = sum(1 for r, lab in rows if r.get("score") == 1 and lab.get("task_done") in ("no", "partial"))
        z = sum(1 for r, lab in rows if r.get("score") != 1 and lab.get("task_done") == "yes")
        L.append("| %s | %d | %d | %d | %d | %d |" % (name, c["direct"], c["mask"], c["no"], a, z))

    L += ["", "## 6. 行为（出现该行为的轨迹数 / 有标签条数）", ""]
    types = ["artifact_self_check", "false_success_caught", "false_success_claimed", "side_effect_disclosed",
             "side_effect_undisclosed", "constraint_kept", "constraint_violated", "risky_or_destructive_action",
             "repeat_without_new_info", "stale_id_or_misclick", "refused_to_fabricate", "honest_failure_report", "used_noncanonical_path"]
    L += ["| 行为 | " + " | ".join(BATCHES.values()) + " |", "|---|" + "---|" * len(BATCHES)]
    for t in types:
        cells = []
        for batch in BATCHES:
            rows = [lab for b, r, lab in labeled if b == batch]
            k = sum(1 for lab in rows if any(x.get("type") == t and x.get("quote_ok") for x in lab.get("behaviors", [])))
            cells.append("%d/%d" % (k, len(rows)))
        L.append("| %s | %s |" % (t, " | ".join(cells)))
    qa = sum((lab.get("_quotes") or {}).get("all", 0) for _, _, lab in labeled)
    qo = sum((lab.get("_quotes") or {}).get("ok", 0) for _, _, lab in labeled)
    L += ["", "摘录核对：%d/%d 段能在原始记录里找到。" % (qo, qa)]
    out = ROOT / "analysis" / "统计_E20.md"
    out.write_text("\n".join(L) + "\n")
    print("wrote", out, len(recs), "records,", len(labeled), "labeled")


if __name__ == "__main__":
    main()
