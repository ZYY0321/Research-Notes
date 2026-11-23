#!/usr/bin/env python3
"""汇总 invariant_rejudge.mts 的输出，写 结果.md。

  python3 scripts/截断检测/invariant_summary.py <dir>

框级真值：
- 测试集 71 条：正常页的框都不是截断；截断页按 Labelme 框交叠判。g05 左端「ArkUI实践」Labelme 标了截断，
  但它在可横滑的 Scroll 里、左滑能看全，按「内容能不能拿到」的定义不算截断（截图标注和定义不一致的例子）。
- 自测存档：正常页的框都不是截断；截断页按文字逐个定（下面 TRUE_TEXTS），对不上的不计。
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

D = Path(sys.argv[1])
TRUE_TEXTS = {"以上是全部更新内容", "设置", "HMOS代码工坊", "我的", "收藏/浏览", "旅行助手", "行程/订单"}
NOT_TEXTS = {"找 住 宿"}
DEFINITION_FIX = {("testset:bifold_xml_truncated_sample_g05_s1", "ArkUI实践")}


def load(name):
    return [json.loads(l) for l in (D / name).read_text(encoding="utf-8").splitlines() if l.strip()]


cases = {c["id"]: c for c in json.loads((D / "cases_selftest.json").read_text(encoding="utf-8"))}
rows = []
for r in load("out_testset71.jsonl"):
    text = (r.get("detail") or {}).get("text")
    t = r["truth"]
    if (r["id"], text) in DEFINITION_FIX:
        t = "not_truncation"
    elif t == "not_truncation_or_mislabel":
        t = None
    rows.append({**r, "src": "测试集71", "truth2": t, "key": (r["id"], r["box_index"])})
for r in load("out_acceptance0929.jsonl"):
    text = (r.get("detail") or {}).get("text")
    t = r["truth"]
    if text == "ArkUI实践":
        t = "not_truncation"
    elif t == "not_truncation_or_mislabel":
        t = None
    rows.append({**r, "src": "9月验收", "truth2": t, "key": ("9月验收", r["id"][:15], r["id"].split(":")[-1], text, r["issue_type"])})
for r in load("out_selftest.jsonl"):
    text = (r.get("detail") or {}).get("text")
    c = cases[r["id"]]
    t = r["truth"]
    if t == "page_truncated":
        t = "truncation" if text in TRUE_TEXTS else "not_truncation" if text in NOT_TEXTS else None
    if c["app"] == "样例App" and text == "提交":
        t = None
    mode = r["id"].split(":")[-1]
    rows.append({**r, "src": "自测存档", "truth2": t, "key": (c["app"], c["page"][:12], mode, text, r["issue_type"])})

rows = [r for r in rows if r["truth2"]]
uniq = {}
for r in rows:
    uniq.setdefault(r["key"], r)
U = list(uniq.values())

out = []
w = out.append
w("类型：材料 ｜ 归属：2026-11-10 恒定关系重判（P2） ｜ 状态：第一版\n")
w("# 只用恒定关系重判存档：结果\n")
w("脚本：`scripts/截断检测/invariant_build_cases.py`、`invariant_rejudge.mts`、`invariant_summary.py`。布局解析沿用交付仓 B 版 `layout.ts`，判据是独立写的一条关系，不调用交付仓的判定规则。\n")
w(f"框数：{len(rows)}（去重后 {len(U)}；去重按 App、页面、屏态、文字、类型）。来源：测试集 71 条的官方模型框；双折叠真机自测存档的模型框（带当时的滑动结果）。\n")


def table(rs, title):
    w(f"\n## {title}\n")
    by = Counter((r["pred"], r["truth2"]) for r in rs)
    n = len(rs)
    dec = [r for r in rs if r["pred"] != "undecided"]
    w(f"- 布局树能下结论的：{len(dec)}/{n}（{len(dec) / max(1, n):.0%}）；其余落在盲区。")
    v = [r for r in rs if r["pred"] == "truncation"]
    h = [r for r in rs if r["pred"] == "not_truncation"]
    vt = sum(r["truth2"] == "truncation" for r in v)
    ht = sum(r["truth2"] == "not_truncation" for r in h)
    w(f"- 判「违反」（截断）：{len(v)}，其中真截断 {vt}。判「成立」（能拿到）：{len(h)}，其中真不是截断 {ht}。")
    tt = [r for r in rs if r["truth2"] == "truncation"]
    w(f"- 真截断框 {len(tt)}：判违反 {sum(r['pred'] == 'truncation' for r in tt)}，落盲区 {sum(r['pred'] == 'undecided' for r in tt)}，判成立 {sum(r['pred'] == 'not_truncation' for r in tt)}。")
    w("\n| 类别 | 不是截断 | 真截断 |\n|---|---|---|")
    cls = defaultdict(Counter)
    for r in rs:
        cls[r["cls"]][r["truth2"]] += 1
    for k in sorted(cls, key=lambda x: (x.split(":")[0], -sum(cls[x].values()))):
        w(f"| {k} | {cls[k]['not_truncation']} | {cls[k]['truncation']} |")


table(rows, "全部框")
table(U, "去重后")
for src in ("测试集71", "9月验收", "自测存档"):
    table([r for r in U if r["src"] == src], f"去重后 · {src}")

st = [r for r in U if r["src"] in ("自测存档", "9月验收") and r.get("slide_result")]
w("\n## 和当时真机滑动结果对照（自测存档，去重后）\n")
w("滑动结果：scrollable = 框里变了、当可滑出；confirmed = 框里没变、当确认截断；其余是滑失败或没滑。\n")
w("| 恒定关系 | 真值 | scrollable | confirmed | 其他 |\n|---|---|---|---|---|")
m = defaultdict(Counter)
for r in st:
    s = r["slide_result"]
    m[(r["pred"], r["truth2"])][s if s in ("scrollable", "confirmed") else "其他"] += 1
for k in sorted(m):
    w(f"| {k[0]} | {k[1]} | {m[k]['scrollable']} | {m[k]['confirmed']} | {m[k]['其他']} |")

w("\n## 关系和滑动说法相反的框（去重后）\n")
w("| 来源 | 文字 | 关系 | 滑动 | 真值 |\n|---|---|---|---|---|")
for r in st:
    p, s = r["pred"], r["slide_result"]
    if (p == "truncation" and s == "scrollable") or (p == "not_truncation" and s == "confirmed"):
        w(f"| {r['key'][0]} {r['key'][1]} {r['key'][2]} | {r['key'][3]} | {r['cls']} | {s} | {r['truth2']} |")

(D / "结果.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
