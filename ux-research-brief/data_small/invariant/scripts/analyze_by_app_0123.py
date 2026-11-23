#!/usr/bin/env python3
"""Offline counts for invariant 179 boxes and open-close 849 groups.

Reads only local files. Writes only under /tmp/ana_0123/.
Rerun: python3 /tmp/ana_0123/analyze_0123.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path("/tmp/ana_0123")
INV = Path("/Users/zhangyingying/UX-Agent/docs/材料/2026-11-10_恒定关系重判")
CATALOG = Path("/Users/zhangyingying/UX-Agent/docs/截断检测/测试集与测试/页面复现说明/路径清单.csv")
OC = Path("/Users/zhangyingying/UX-Agent/docs/开合检测/交付/打包_2026-11-17_双折叠开合/02_打标结果_vlm_judge_1029_gpt")
FAIL_CSV = Path("/Users/zhangyingying/UX-Agent/docs/开合检测/交付/打包_2026-11-17_双折叠开合/03_模型判异常_给我过/fail_266_索引.csv")
OC_DOC = Path("/Users/zhangyingying/UX-Agent/docs/开合检测/交付/打包_2026-11-17_双折叠开合/01_口径与规则/2026-11-17_双折叠开合数据口径与打标说明.md")

# Copied from 验收/远端main/local/harmonyArena/scripts/testset/build_catalog.py APP_ZH.
# Used only when a testset stem is absent from 路径清单.csv.
APP_ZH = {
    "alipay": "支付宝",
    "amap": "高德",
    "bilibili": "哔哩哔哩",
    "ctrip": "携程",
    "dianping": "大众点评",
    "didi": "滴滴",
    "dingding": "钉钉",
    "douyin": "抖音",
    "fanqie": "番茄小说",
    "iqiyi": "爱奇艺",
    "jd": "京东",
    "kuaishou": "快手",
    "kugou": "酷狗",
    "meituan": "美团",
    "qq": "QQ",
    "qqmusic": "QQ音乐",
    "railway12306": "铁路12306",
    "taobao": "淘宝",
    "tencentmeeting": "腾讯会议",
    "tencentnews": "腾讯新闻",
    "tencentvideo": "腾讯视频",
    "toutiao": "今日头条",
    "uc": "UC",
    "vipshop": "唯品会",
    "wechat": "微信",
    "wecom": "企业微信",
    "weibo": "微博",
    "wps": "WPS",
    "xianyu": "闲鱼",
    "xiaohongshu": "小红书",
    "ximalaya": "喜马拉雅",
    "zhihu": "知乎",
}

TRUE_TEXTS = {"以上是全部更新内容", "设置", "HMOS代码工坊", "我的", "收藏/浏览", "旅行助手", "行程/订单"}
NOT_TEXTS = {"找 住 宿"}
DEFINITION_FIX = {("testset:bifold_xml_truncated_sample_g05_s1", "ArkUI实践")}

PRED_ZH = {"truncation": "截断", "not_truncation": "能拿到", "undecided": "不能下结论"}
TRUTH_ZH = {"truncation": "真截断", "not_truncation": "不是截断"}
SRC_CODE = {"测试集71": "testset71", "9月验收": "acceptance0929", "自测存档": "selftest"}
SRC_ORDER = {"testset71": 0, "selftest": 1, "acceptance0929": 2}

# 结果.md「去重后」类别表，用来核对复算，不是计数来源。
EXPECT_CLS = {
    "all": {
        "成立:切口是可滚视口的边": (64, 0),
        "成立:翻页容器露出邻页": (10, 0),
        "成立:裁切者里面有可滚视口": (3, 0),
        "盲区:树上看不出被切（自裁切/省略号/模型误标）": (26, 6),
        "盲区:被兄弟组件盖住（树上无裁切）": (10, 6),
        "盲区:内容不在树里（自绘或框对不上节点）": (11, 5),
        "盲区:只裁掉行框边缘（<15%）": (8, 2),
        "盲区:找不到裁切者": (0, 2),
        "违反:裁切者跟着内容动（中间没有可动视口）": (0, 26),
    },
    "testset71": {
        "成立:切口是可滚视口的边": (10, 0),
        "成立:翻页容器露出邻页": (2, 0),
        "盲区:树上看不出被切（自裁切/省略号/模型误标）": (6, 3),
        "盲区:内容不在树里（自绘或框对不上节点）": (3, 3),
        "盲区:被兄弟组件盖住（树上无裁切）": (1, 1),
        "盲区:只裁掉行框边缘（<15%）": (1, 1),
        "盲区:找不到裁切者": (0, 1),
        "违反:裁切者跟着内容动（中间没有可动视口）": (0, 8),
    },
    "acceptance0929": {
        "成立:切口是可滚视口的边": (14, 0),
        "成立:翻页容器露出邻页": (2, 0),
        "盲区:被兄弟组件盖住（树上无裁切）": (4, 1),
        "盲区:树上看不出被切（自裁切/省略号/模型误标）": (0, 3),
        "盲区:内容不在树里（自绘或框对不上节点）": (0, 2),
        "盲区:只裁掉行框边缘（<15%）": (0, 1),
        "盲区:找不到裁切者": (0, 1),
        "违反:裁切者跟着内容动（中间没有可动视口）": (0, 8),
    },
    "selftest": {
        "成立:切口是可滚视口的边": (40, 0),
        "成立:翻页容器露出邻页": (6, 0),
        "成立:裁切者里面有可滚视口": (3, 0),
        "盲区:树上看不出被切（自裁切/省略号/模型误标）": (20, 0),
        "盲区:被兄弟组件盖住（树上无裁切）": (5, 4),
        "盲区:内容不在树里（自绘或框对不上节点）": (8, 0),
        "盲区:只裁掉行框边缘（<15%）": (7, 0),
        "违反:裁切者跟着内容动（中间没有可动视口）": (0, 10),
    },
}


def load_jsonl(path):
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_cases(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = [c["id"] for c in data]
    dup = sorted(i for i, n in Counter(ids).items() if n > 1)
    # invariant_summary.py uses last-wins dict for selftest.
    by_id = {}
    for c in data:
        by_id[c["id"]] = c
    return data, by_id, dup


def load_catalog():
    out = {}
    dups = []
    for line in CATALOG.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("文件名"):
            continue
        parts = line.split(",")
        if len(parts) < 5:
            continue
        stem, device, app, screen, category = parts[:5]
        if stem in out:
            dups.append(stem)
        out[stem] = {"device": device, "app": app, "screen": screen, "category": category}
    return out, dups


def esc(v):
    s = "" if v is None else str(v)
    return s.replace("\r", " ").replace("\n", " ").replace("|", "/")


def cut(v, n):
    s = esc(v)
    if len(s) <= n:
        return s
    return s[: n - 1] + "…"


def pct(n, d):
    if not d:
        return "0/0"
    return "%d/%d（%.1f%%）" % (n, d, 100.0 * n / d)


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(esc(c) for c in row) + " |")
    return "\n".join(lines)


def write_csv(path, dicts, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for d in dicts:
            w.writerow({k: d.get(k, "") for k in fields})


def text_of(r):
    return (r.get("detail") or {}).get("text")


def clipper_of(r):
    return (r.get("detail") or {}).get("clipper") or ""


def parse_stem(stem):
    m = re.fullmatch(
        r"(phone|tablet|bifold|widefold|trifold)_xml_(normal|truncated)_(.+)_g(\d+)_s(\d+)",
        stem,
    )
    if not m:
        return None
    return {
        "device_en": m.group(1),
        "polarity": m.group(2),
        "slug": m.group(3),
        "page": "g" + m.group(4),
        "shot": "s" + m.group(5),
    }


def display_app(app_raw, slug):
    if slug == "sample" or app_raw in ("样例App", "HMOS代码工坊"):
        return "样例App"
    return app_raw or slug or "?"


def correct_of(pred, truth):
    if pred == "undecided":
        return "未判"
    if pred == truth:
        return "对"
    return "错"


def summarize(rows):
    dec = [r for r in rows if r["pred"] != "undecided"]
    trunc = [r for r in rows if r["pred"] == "truncation"]
    ok = [r for r in rows if r["pred"] == "not_truncation"]
    blind = [r for r in rows if r["pred"] == "undecided"]
    tt = [r for r in rows if r["truth2"] == "truncation"]
    return {
        "n": len(rows),
        "decidable": len(dec),
        "correct": sum(1 for r in dec if r["pred"] == r["truth2"]),
        "wrong": sum(1 for r in dec if r["pred"] != r["truth2"]),
        "blind": len(blind),
        "pred_trunc": len(trunc),
        "pred_ok": len(ok),
        "pred_trunc_true": sum(1 for r in trunc if r["truth2"] == "truncation"),
        "pred_ok_true": sum(1 for r in ok if r["truth2"] == "not_truncation"),
        "true_trunc": len(tt),
        "true_trunc_blind": sum(1 for r in tt if r["pred"] == "undecided"),
        "true_trunc_as_ok": sum(1 for r in tt if r["pred"] == "not_truncation"),
        "true_trunc_as_trunc": sum(1 for r in tt if r["pred"] == "truncation"),
    }


def cls_pairs(rows):
    c = defaultdict(lambda: [0, 0])
    for r in rows:
        idx = 0 if r["truth2"] == "not_truncation" else 1
        c[r["cls"]][idx] += 1
    return {k: (v[0], v[1]) for k, v in c.items()}


def build_invariant():
    mismatches = []
    catalog, cat_dups = load_catalog()
    if cat_dups:
        mismatches.append("路径清单重复文件名 %d 个，后者覆盖前者" % len(cat_dups))

    ts_cases, _, ts_dups = load_cases(INV / "cases_testset71.json")
    st_cases_list, st_by_id, st_dups = load_cases(INV / "cases_selftest.json")
    acc_cases, acc_by_id, acc_dups = load_cases(INV / "cases_acceptance0929.json")
    if ts_dups:
        mismatches.append("cases_testset71 重复 id: %s" % ts_dups)
    if st_dups:
        mismatches.append("cases_selftest 重复 id: %s" % st_dups)
    if acc_dups:
        mismatches.append("cases_acceptance0929 重复 id: %s" % acc_dups)

    ts_by_id = {c["id"]: c for c in ts_cases}
    catalog_miss = []

    def enrich(src_zh, r, case, slug, app_raw, page, screen, device):
        text = text_of(r)
        app = display_app(app_raw, slug)
        if src_zh == "测试集71":
            key = (r["id"], r["box_index"])
        elif src_zh == "9月验收":
            key = ("9月验收", r["id"][:15], r["id"].split(":")[-1], text, r["issue_type"])
        else:
            key = (case["app"], case["page"][:12], r["id"].split(":")[-1], text, r["issue_type"])
        return {
            "src_zh": src_zh,
            "source": SRC_CODE[src_zh],
            "app": app,
            "app_raw": app_raw,
            "slug": slug,
            "page": page,
            "screen": screen,
            "device": device,
            "text": text if text is not None else "",
            "text_key": text,
            "issue_type": r.get("issue_type") or "",
            "pred": r["pred"],
            "pred_zh": PRED_ZH.get(r["pred"], r["pred"]),
            "truth_raw": r.get("truth") or "",
            "truth2": r["truth2"],
            "truth_zh": TRUTH_ZH.get(r["truth2"], ""),
            "origin": r["origin"],
            "correct": correct_of(r["pred"], r["truth2"]) if r["truth2"] else "",
            "cls": r.get("cls") or "",
            "id": r["id"],
            "box_index": r["box_index"],
            "bbox": " ".join(str(x) for x in (r.get("bbox") or [])),
            "slide_result": r.get("slide_result") or "",
            "clipper": clipper_of(r),
            "label": r.get("label") or "",
            "key": key,
            "key_repr": repr(key),
            "layout": (case or {}).get("layout") or "",
        }

    kept_src = []
    dropped = []

    for r in load_jsonl(INV / "out_testset71.jsonl"):
        text = text_of(r)
        raw = r["truth"]
        if (r["id"], text) in DEFINITION_FIX:
            t = "not_truncation"
            origin = "定义改标"
        elif raw == "not_truncation_or_mislabel":
            t = None
            origin = "交叠不足丢弃"
        elif raw == "not_truncation" and r.get("label") == "normal":
            t = raw
            origin = "正常页整页"
        elif raw == "truncation":
            t = raw
            origin = "Labelme交叠"
        else:
            t = raw
            origin = "测试集其他:%s/%s" % (r.get("label"), raw)
        rr = dict(r)
        rr["truth2"] = t
        rr["origin"] = origin
        case = ts_by_id.get(r["id"])
        stem = r["id"][len("testset:") :] if r["id"].startswith("testset:") else r["id"]
        parsed = parse_stem(stem) or {}
        cat = catalog.get(stem)
        if cat is None:
            catalog_miss.append(stem)
        slug = parsed.get("slug") or ""
        app_raw = (cat or {}).get("app") or APP_ZH.get(slug, slug or "?")
        page = parsed.get("page") or (Path(case["layout"]).parent.name if case and case.get("layout") else "")
        screen = (cat or {}).get("screen") or parsed.get("shot") or ""
        device = (cat or {}).get("device") or parsed.get("device_en") or ""
        row = enrich("测试集71", rr, case, slug, app_raw, page, screen, device)
        if t:
            kept_src.append(row)
        else:
            row["drop_reason"] = origin
            dropped.append(row)

    for r in load_jsonl(INV / "out_acceptance0929.jsonl"):
        text = text_of(r)
        raw = r["truth"]
        if text == "ArkUI实践":
            t = "not_truncation"
            origin = "定义改标"
        elif raw == "not_truncation_or_mislabel":
            t = None
            origin = "交叠不足丢弃"
        elif raw == "not_truncation" and r.get("label") == "normal":
            t = raw
            origin = "正常页整页"
        elif raw == "truncation":
            t = raw
            origin = "Labelme交叠"
        else:
            t = raw
            origin = "验收其他:%s/%s" % (r.get("label"), raw)
        rr = dict(r)
        rr["truth2"] = t
        rr["origin"] = origin
        case = acc_by_id[r["id"]]
        slug = case.get("app") or ""
        layout = case.get("layout") or ""
        m = re.search(
            r"(phone|tablet|bifold|widefold|trifold)_xml_(normal|truncated)/([^/]+)/(g\d+)/",
            layout,
        )
        device = m.group(1) if m else ""
        page = case.get("page") or (m.group(4) if m else "")
        app_raw = APP_ZH.get(slug, slug or "?")
        screen = r["id"].split(":")[-1]
        row = enrich("9月验收", rr, case, slug, app_raw, page, screen, device)
        if t:
            kept_src.append(row)
        else:
            row["drop_reason"] = origin
            dropped.append(row)

    for r in load_jsonl(INV / "out_selftest.jsonl"):
        text = text_of(r)
        case = st_by_id[r["id"]]
        raw = r["truth"]
        if raw == "page_truncated":
            if text in TRUE_TEXTS:
                t = "truncation"
                origin = "自测文字白名单真截断"
            elif text in NOT_TEXTS:
                t = "not_truncation"
                origin = "自测文字白名单不是截断"
            else:
                t = None
                origin = "自测截断页文字不在白名单"
        elif raw == "not_truncation":
            t = raw
            origin = "正常页整页"
        else:
            t = raw
            origin = "自测其他:%s" % raw
        if case.get("app") == "样例App" and text == "提交":
            t = None
            origin = "样例App文字提交被丢弃"
        rr = dict(r)
        rr["truth2"] = t
        rr["origin"] = origin
        row = enrich(
            "自测存档",
            rr,
            case,
            "",
            case.get("app") or "?",
            case.get("page") or "",
            r["id"].split(":")[-1],
            "",
        )
        if t:
            kept_src.append(row)
        else:
            row["drop_reason"] = origin
            dropped.append(row)

    groups = {}
    order = []
    for row in kept_src:
        k = row["key"]
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append(row)
    uniq = []
    merge_rows = []
    for k in order:
        members = groups[k]
        keep = dict(members[0])
        keep["dedup_n"] = len(members)
        preds = sorted(set(m["pred"] for m in members))
        truths = sorted(set(m["truth2"] for m in members))
        pages = sorted(set(m["page"] for m in members))
        apps = sorted(set(m["app_raw"] for m in members))
        ids = sorted(set(m["id"] for m in members))
        keep["dedup_pred_conflict"] = "是" if len(preds) > 1 else ""
        keep["dedup_truth_conflict"] = "是" if len(truths) > 1 else ""
        keep["dedup_pages"] = " || ".join(pages)
        keep["dedup_ids"] = " || ".join(ids)
        uniq.append(keep)
        if len(members) > 1:
            merge_rows.append(
                {
                    "source": keep["source"],
                    "app": keep["app"],
                    "dedup_n": len(members),
                    "pred_values": "|".join(preds),
                    "truth_values": "|".join(truths),
                    "pred_conflict": keep["dedup_pred_conflict"],
                    "truth_conflict": keep["dedup_truth_conflict"],
                    "pages": keep["dedup_pages"],
                    "ids": keep["dedup_ids"],
                    "kept_id": keep["id"],
                    "kept_box": keep["box_index"],
                    "text": keep["text"],
                    "issue_type": keep["issue_type"],
                    "key": keep["key_repr"],
                }
            )

    # checks against 结果.md
    def check(name, got, exp):
        if got != exp:
            mismatches.append("%s: 复算 %s，结果.md %s" % (name, got, exp))

    check("过滤后框数", len(kept_src), 259)
    check("去重后", len(uniq), 179)
    check("丢弃", len(dropped), 6)
    sm = summarize(uniq)
    check("能下结论", sm["decidable"], 103)
    check("判截断", sm["pred_trunc"], 26)
    check("判截断且真截断", sm["pred_trunc_true"], 26)
    check("判能拿到", sm["pred_ok"], 77)
    check("判能拿到且不是截断", sm["pred_ok_true"], 77)
    check("对", sm["correct"], 103)
    check("错", sm["wrong"], 0)
    check("真截断", sm["true_trunc"], 47)
    check("真截断盲区", sm["true_trunc_blind"], 21)
    check("真截断被判能拿到", sm["true_trunc_as_ok"], 0)
    for code, exp_n, exp_dec, exp_tr, exp_ok, exp_tt, exp_bb in (
        ("testset71", 40, 20, 8, 12, 17, 9),
        ("acceptance0929", 36, 24, 8, 16, 16, 8),
        ("selftest", 103, 59, 10, 49, 14, 4),
    ):
        sub = summarize([r for r in uniq if r["source"] == code])
        check(code + " 框", sub["n"], exp_n)
        check(code + " 能下结论", sub["decidable"], exp_dec)
        check(code + " 判截断", sub["pred_trunc"], exp_tr)
        check(code + " 判能拿到", sub["pred_ok"], exp_ok)
        check(code + " 真截断", sub["true_trunc"], exp_tt)
        check(code + " 真截断盲区", sub["true_trunc_blind"], exp_bb)

    def check_cls(tag, rows, expect):
        got = cls_pairs(rows)
        if got != expect:
            mismatches.append("%s 类别表不一致\n  复算 %s\n  结果.md %s" % (tag, got, expect))

    check_cls("去重后", uniq, EXPECT_CLS["all"])
    for code in ("testset71", "acceptance0929", "selftest"):
        check_cls(code, [r for r in uniq if r["source"] == code], EXPECT_CLS[code])

    unknown_apps = sorted(set(r["app"] for r in uniq if r["app"] in ("", "?", None)))
    if unknown_apps:
        mismatches.append("有框没有 App 名")
    if catalog_miss:
        mismatches.append("测试集 stem 不在路径清单: %s" % sorted(set(catalog_miss)))

    # 人工标注框，不进入 179
    human_rows = load_jsonl(INV / "out_testset71_人工标注框.jsonl")
    human_cross = Counter((r["pred"], r["truth"]) for r in human_rows)
    expect_human = {
        ("not_truncation", "not_truncation"): 16,
        ("not_truncation", "truncation"): 2,
        ("truncation", "truncation"): 9,
        ("undecided", "not_truncation"): 11,
        ("undecided", "truncation"): 10,
    }
    if dict(human_cross) != expect_human or human_cross.get(("truncation", "not_truncation"), 0) != 0:
        mismatches.append("人工标注框交叉表 %s" % dict(human_cross))
    human_disagree = [r for r in human_rows if r["pred"] == "not_truncation" and r["truth"] == "truncation"]

    return {
        "uniq": uniq,
        "dropped": dropped,
        "merges": merge_rows,
        "mismatches": mismatches,
        "summary": sm,
        "catalog_miss": catalog_miss,
        "st_case_n": len(st_cases_list),
        "human_n": len(human_rows),
        "human_disagree": human_disagree,
        "raw_counts": {
            "testset71": sum(1 for r in uniq if False),
        },
    }


def agg_rows(rows):
    sm = summarize(rows)
    sm["apps_all"] = sorted(set(r["app"] for r in rows))
    return sm


def write_invariant(pack):
    uniq = pack["uniq"]
    sm = pack["summary"]
    lines = []
    w = lines.append
    w("# 恒定关系：去重后 179 框按 App / 来源")
    w("")
    w("复现：`python3 /tmp/ana_0123/analyze_0123.py`")
    w("")
    w("计数只读本地文件，没有改仓库，没有调接口。去重键和真值覆盖照 `invariant_summary.py`：先丢掉它会丢掉的框，再按它的键 `setdefault` 留第一条。")
    w("")
    w("读入：")
    w("")
    w("- `/Users/zhangyingying/UX-Agent/docs/材料/2026-11-10_恒定关系重判/` 的 `out_*.jsonl`、`cases_*.json`")
    w("- `/Users/zhangyingying/UX-Agent/scripts/截断检测/invariant_summary.py`（去重键、TRUE_TEXTS、定义改标）")
    w("- `/Users/zhangyingying/UX-Agent/docs/截断检测/测试集与测试/页面复现说明/路径清单.csv`（测试集 App、屏态）")
    w("- `sample`、路径清单里的「HMOS代码工坊」、自测标注里的「样例App」在汇总表合成一行「样例App」。框级 csv 保留材料原名。除此之外不合并别名。")
    w("")
    if pack["mismatches"]:
        w("和 `结果.md` 的核对有差额，见文末。下面的表仍是这次从 jsonl 算出来的数。")
    else:
        w("和 `结果.md` 去重后的总数、分来源总数、类别表一致：过滤后 259，去重 179，能下结论 103，判截断 26 全是真截断，判能拿到 77 全是不是截断，真截断 47，其中盲区 21。")
    w("")
    w("## 1. 去重后的框")
    w("")
    w("来源文件用 `testset71` / `selftest` / `acceptance0929`。`out_testset71_人工标注框.jsonl` 有 48 条，汇总脚本没有读它，所以不在这 179 里。")
    w("")
    w("判定：截断 / 能拿到 / 不能下结论。不能下结论即盲区，是否对记「未判」，不计入对的数。人工真值是进入这 179 所用的口径真值，第 5 节写每一种是从哪来的。")
    w("")
    w("去重键和结果.md 那句「按 App、页面、屏态、文字、类型」不完全是同一件事，179 是按脚本的键复算的：")
    w("")
    w("- testset71：`(案例 id, 框号)`，框和框之间不合并。")
    w("- selftest：`(标注 App, 页面名前 12 字, single/dual, 文字, 问题类型)`。")
    w("- acceptance0929：`(\"9月验收\", id 前 15 个字符, single/dual, 文字, 问题类型)`。")
    w("- 三个来源的键对不上，不会跨来源并成一条。代表行是该键在文件里的第一条。")
    w("")
    merges = pack["merges"]
    conflict = [m for m in merges if m["pred_conflict"] or m["truth_conflict"]]
    page_mix = [m for m in merges if " || " in m["pages"]]
    w("合并成一条的键有 %d 个。其中组内 pred 或真值不一致的有 %d 个；组内完整页面名不止一个的有 %d 个（页面只取前 12 字时会碰到）。明细在 `/tmp/ana_0123/A_invariant_dedup_merges.csv`。" % (
        len(merges), len(conflict), len(page_mix),
    ))
    w("")
    if page_mix:
        w("页面名被前 12 字并到一起的例子（最多 8 组）：")
        w("")
        w(md_table(
            ["来源", "App", "条数", "页面", "文字", "留下的 id"],
            [[m["source"], m["app"], m["dedup_n"], cut(m["pages"], 80), cut(m["text"], 20), m["kept_id"]] for m in page_mix[:8]],
        ))
        w("")
    show = sorted(uniq, key=lambda r: (SRC_ORDER[r["source"]], r["app"], r["page"], r["id"], r["box_index"]))
    w(md_table(
        ["来源", "App", "页面", "屏态", "文字", "判定", "人工真值", "是否对", "id", "框号"],
        [[
            r["source"], r["app"], cut(r["page"], 42), r["screen"], cut(r["text"], 24) or "（无文字）",
            r["pred_zh"], r["truth_zh"] + ("（定义改标）" if r["origin"] == "定义改标" else ""),
            r["correct"], r["id"], r["box_index"],
        ] for r in show],
    ))
    w("")
    w("全字段在 `/tmp/ana_0123/A_invariant_boxes.csv`（含材料原名、真值来源、类别、去重条数）。")
    w("")

    def app_table(rows):
        by = defaultdict(list)
        for r in rows:
            by[r["app"]].append(r)
        out = []
        for app, rs in sorted(by.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            s = summarize(rs)
            raws = Counter(r["app_raw"] for r in rs)
            out.append({
                "app": app,
                "raw_names": " + ".join("%s %d" % (a, n) for a, n in sorted(raws.items())),
                **s,
            })
        return out

    apps = app_table(uniq)
    dec_apps = [a for a in apps if a["decidable"]]
    dec_apps_sorted = sorted(dec_apps, key=lambda a: (-a["decidable"], a["app"]))
    top_n = dec_apps_sorted[0]["decidable"]
    tops = [a for a in dec_apps_sorted if a["decidable"] == top_n]
    top3 = sum(a["decidable"] for a in dec_apps_sorted[:3])
    w("## 2. 按 App")
    w("")
    w("能下结论的 103 个框落在 %d 个 App 上。179 个框一共 %d 个 App。" % (len(dec_apps), len(apps)))
    w("")
    top_desc = "、".join("%s %d 个" % (a["app"], a["decidable"]) for a in tops)
    w("最大的 App 是 %s，占 103 的 %s。前 3 名合计 %s。" % (
        top_desc, pct(top_n, 103), pct(top3, 103),
    ))
    w("")
    tt_apps = [a for a in apps if a["true_trunc"]]
    tt_apps_sorted = sorted(tt_apps, key=lambda a: (-a["true_trunc"], a["app"]))
    w("真截断 47 个的 App 分布：" + "；".join(
        "%s %d（盲区 %d）" % (a["app"], a["true_trunc"], a["true_trunc_blind"]) for a in tt_apps_sorted
    ) + "。")
    w("")
    w("对的数只数能下结论且 pred 和口径真值相同的框。盲区数是判定为不能下结论的框，含真截断和不是截断。")
    w("")
    w(md_table(
        ["App", "框数", "能下结论", "对", "错", "盲区", "真截断", "真截断在盲区", "占103"],
        [[
            a["app"], a["n"], a["decidable"], a["correct"], a["wrong"], a["blind"],
            a["true_trunc"], a["true_trunc_blind"],
            pct(a["decidable"], 103) if a["decidable"] else "0",
        ] for a in apps] + [[
            "合计", sm["n"], sm["decidable"], sm["correct"], sm["wrong"], sm["blind"],
            sm["true_trunc"], sm["true_trunc_blind"], pct(sm["decidable"], 103),
        ]],
    ))
    w("")
    alias_rows = [a for a in apps if " + " in a["raw_names"] or a["app"] == "样例App"]
    if any(a["app"] == "样例App" for a in apps):
        a = next(x for x in apps if x["app"] == "样例App")
        w("样例App 这一行的材料原名：%s。路径清单把同一套 sample/g01–g06 写成 HMOS代码工坊，自测标注写成样例App，验收 cases 里的 slug 是 sample。" % a["raw_names"])
        w("")
    both_pairs = []
    names = set(a["app"] for a in apps)
    for a, b in (("番茄", "番茄小说"), ("B站", "哔哩哔哩")):
        if a in names and b in names:
            both_pairs.append((a, b))
    if both_pairs:
        w("下面两对名字在材料里同时出现，主表没有合并。框数是：")
        for a, b in both_pairs:
            na = next(x["n"] for x in apps if x["app"] == a)
            nb = next(x["n"] for x in apps if x["app"] == b)
            da = next(x["decidable"] for x in apps if x["app"] == a)
            db = next(x["decidable"] for x in apps if x["app"] == b)
            w("- %s %d 框（能下结论 %d），%s %d 框（能下结论 %d）。合成一个的话，179 的 App 数少 1，103 覆盖的 App 数%s。" % (
                a, na, da, b, nb, db,
                "少 1" if da and db else "不变（有一个能下结论为 0）" if (da or db) else "不变",
            ))
        w("")
    w("表文件：`/tmp/ana_0123/A_invariant_by_app.csv`。")
    w("")

    w("## 3. 按来源")
    w("")
    src_rows = []
    for code in ("testset71", "selftest", "acceptance0929"):
        s = summarize([r for r in uniq if r["source"] == code])
        src_rows.append((code, s))
    w("103 个能下结论的框里，testset71 %d，selftest %d，acceptance0929 %d。" % (
        src_rows[0][1]["decidable"], src_rows[1][1]["decidable"], src_rows[2][1]["decidable"],
    ))
    w("")
    w(md_table(
        ["来源", "框数", "能下结论", "对", "错", "盲区", "真截断", "真截断在盲区", "占103"],
        [[
            code, s["n"], s["decidable"], s["correct"], s["wrong"], s["blind"],
            s["true_trunc"], s["true_trunc_blind"], pct(s["decidable"], 103),
        ] for code, s in src_rows] + [[
            "合计", sm["n"], sm["decidable"], sm["correct"], sm["wrong"], sm["blind"],
            sm["true_trunc"], sm["true_trunc_blind"], pct(103, 103),
        ]],
    ))
    w("")
    w("人工标注框不是这张表的一行。它是另一份 48 条，见第 5 节。")
    w("")
    w("表文件：`/tmp/ana_0123/A_invariant_by_source.csv`。")
    w("")

    w("## 4. 看过第一轮才加的滚动方向规则，和点名的两个框")
    w("")
    w("`结果.md` 写：第一版判错的 2 个是大众点评「商场购物」和京东金刚区，错在滚动方向；补了规则以后改对。同段还写，包装层不算裁切者、滚动方向规则，都是看了第一轮结果后改的。9 月验收是这一版才加进样本的，调判据时没看过，所以那 2 个错例不在 acceptance0929。")
    w("")
    w("滚动方向规则不在某一条框的字段里。它在 `/Users/zhangyingying/UX-Agent/scripts/截断检测/invariant_rejudge.mts` 的 `axisMatches`：裁切者宽 ≥ 4 倍高按横向，高 ≥ 4 倍宽按竖向，然后再看布局树导出的滚动轴。现在的 jsonl 已是补规则之后的判定，没有「改前 pred」。日志 `docs/日志/2026-11-09.md` 说第一版备份在 `/tmp/结果_v1.md`，这个路径现在不存在，材料目录里也没有第一版 jsonl。因此不能从现有文件重算出「哪一条的 pred 被这条规则从截断改成能拿到」。下面只列文字或页面名对得上的框，以及它们现在的判定。")
    w("")
    w("包装层那条规则同样没有逐框改前记录。这里不把任何框指认为被那条规则改对。")
    w("")

    mall = [r for r in uniq if r["text"] == "商场购物"]
    mall_all = [r for r in uniq + pack["dropped"] if r["text"] == "商场购物"]
    w("### 大众点评「商场购物」")
    w("")
    if not mall_all:
        w("四个 out jsonl 里没有文字等于「商场购物」的框。")
    else:
        w("文字等于「商场购物」的框，去重后 %d 条，含被丢弃的一共 %d 条。来源和 App 如下。" % (len(mall), len(mall_all)))
        w("")
        w(md_table(
            ["来源", "App", "材料原名", "页面", "屏态", "当前判定", "当前类别", "口径真值", "是否对", "裁切者", "id", "框号"],
            [[r["source"], r["app"], r["app_raw"], r["page"], r["screen"], r["pred_zh"], r["cls"], r["truth_zh"], r["correct"], r["clipper"], r["id"], r["box_index"]] for r in mall_all],
        ))
    w("")
    king = [r for r in uniq if r["app"] == "京东" and ("金刚" in r["page"] or "金刚" in r["text"])]
    king_drop = [r for r in pack["dropped"] if r["app"] == "京东" and ("金刚" in (r["page"] or "") or "金刚" in (r["text"] or ""))]
    w("### 京东金刚区")
    w("")
    w("没有文字等于「金刚区」或「金刚」的框。页面名含「金刚」的框都在 selftest、App 为京东（材料原名也是京东）。去重后 %d 条，另有丢弃 %d 条。这是页面名对得上的范围。哪一条是第一轮判错的那一条，文件里没有记录。" % (len(king), len(king_drop)))
    w("")
    if king or king_drop:
        w(md_table(
            ["在179里", "来源", "App", "页面", "屏态", "文字", "类型", "当前判定", "当前类别", "裁切者", "id", "框号"],
            [[
                "是" if r in king else "丢弃",
                r["source"], r["app"], cut(r["page"], 36), r["screen"], cut(r["text"], 16) or "（无文字）",
                r["issue_type"], r["pred_zh"], r["cls"], r["clipper"], r["id"], r["box_index"],
            ] for r in king + king_drop],
        ))
        w("")
    home = [r for r in uniq if r["app"] == "京东" and r["id"].startswith("20261106-043220-230")]
    w("`docs/日志/2026-11-06.md` 把京东首页 run `20261106-043220-230` 称作折叠屏金刚区，但 cases 里的 page 是「首页」，不含「金刚」二字。该 run 在去重后留下的框：")
    w("")
    if home:
        w(md_table(
            ["来源", "页面", "屏态", "文字", "类型", "当前判定", "当前类别", "裁切者", "id", "框号"],
            [[r["source"], r["page"], r["screen"], cut(r["text"], 16) or "（无文字）", r["issue_type"], r["pred_zh"], r["cls"], r["clipper"], r["id"], r["box_index"]] for r in home],
        ))
    else:
        w("去重后的 179 里没有这个 run id。")
    w("")
    w("验收和测试集里还有京东首页服务入口（京东拍卖、京东宠物、京东服务、赚红包等），裁切者也是 List。它们不叫「商场购物」的那一对：验收是和规则同一版加进来的，测试集页面名是 g01，不是金刚区。不把它们写成那 2 个错例。")
    w("")

    w("## 5. 人工真值复原到哪一步")
    w("")
    w("179 条都有口径真值，否则汇总脚本会把它们丢掉。这个真值能从 out jsonl 的 `truth` 字段，加上 `invariant_summary.py` 里的覆盖规则重算出来。它不是 179 个框各自一份独立的人工框级标注。分来源如下。")
    w("")
    origin_order = [
        "正常页整页",
        "Labelme交叠",
        "定义改标",
        "自测文字白名单真截断",
        "自测文字白名单不是截断",
    ]
    w("| 真值来源 | 179 里的框 | 其中能下结论 | 含义 |")
    w("|---|---:|---:|---|")
    origin_meaning = {
        "正常页整页": "页级标注是正常页。构建脚本把该页每个模型框写成不是截断，没有逐框人工标签。",
        "Labelme交叠": "截断页上，构建时和 Labelme 框交叠 ≥ 0.3，jsonl 的 truth 为截断。Labelme 文件不在本材料目录，这里只有比较后的标签。",
        "定义改标": "文件 truth 仍是截断（Labelme）。汇总脚本把文字「ArkUI实践」改成不是截断。结果.md 说明这是定义和截图标注不一致。",
        "自测文字白名单真截断": "jsonl 的 truth 只是页级 page_truncated。框级「真截断」是因为文字落在脚本的 TRUE_TEXTS。",
        "自测文字白名单不是截断": "页级是截断页，文字落在脚本的 NOT_TEXTS（「找 住 宿」），写成不是截断。",
    }
    oc = Counter(r["origin"] for r in uniq)
    oc_dec = Counter(r["origin"] for r in uniq if r["pred"] != "undecided")
    seen = set(oc)
    for name in origin_order:
        if name in seen or name in origin_meaning:
            w("| %s | %d | %d | %s |" % (name, oc.get(name, 0), oc_dec.get(name, 0), origin_meaning.get(name, "")))
            seen.discard(name)
    for name in sorted(seen):
        w("| %s | %d | %d | （脚本归到这一类，含义见上面对应分支） |" % (name, oc[name], oc_dec.get(name, 0)))
    w("")
    w("TRUE_TEXTS = %s。" % "、".join(sorted(TRUE_TEXTS)))
    w("")
    w("NOT_TEXTS = %s。" % "、".join(sorted(NOT_TEXTS)))
    w("")
    w("自测截断页上，文字不在这两张表里的框被丢掉，不进入 179。样例App 且文字是「提交」的也丢掉。这次丢掉 %d 条，原因：" % len(pack["dropped"]))
    w("")
    drop_c = Counter(r["origin"] for r in pack["dropped"])
    for k, n in drop_c.most_common():
        w("- %s：%d" % (k, n))
    w("")
    w("丢掉的逐条在 `/tmp/ana_0123/A_invariant_dropped.csv`。")
    w("")
    overrides = [r for r in uniq if r["origin"] == "定义改标"]
    w("定义改标进入 179 的有 %d 条。103 全对是对改标之后的真值而言。若改回文件里的 Labelme 标签（截断），这几条里判成「能拿到」的，按文件原值就是不一致。" % len(overrides))
    w("")
    if overrides:
        w(md_table(
            ["来源", "App", "页面", "文字", "文件 truth", "口径真值", "当前判定", "按口径", "按文件原值", "id", "框号"],
            [[
                r["source"], r["app"], r["page"], r["text"], r["truth_raw"], r["truth_zh"], r["pred_zh"],
                r["correct"], correct_of(r["pred"], r["truth_raw"] if r["truth_raw"] in TRUTH_ZH else r["pred"]),
                r["id"], r["box_index"],
            ] for r in overrides],
        ))
        w("")
    w("所以：标签值可以复原；缺的是自测截断页的逐框人工标注文件（只有脚本里的文字表），以及正常页「每个框都不是截断」这条页级假定。Labelme 原框不在本目录，只有交叠之后写入 jsonl 的截断/不是截断。")
    w("")
    w("### 人工标注框（不在 179 内）")
    w("")
    w("`out_testset71_人工标注框.jsonl` 共 %d 条。汇总脚本不读这份文件。按文件里的 truth / pred 交叉计数，和结果.md 文末补充表一致：假截断（不是截断）27 = 判能拿到 16 + 判截断 0 + 盲区 11；真截断 21 = 判能拿到 2 + 判截断 9 + 盲区 10。" % pack["human_n"])
    w("")
    hd = pack["human_disagree"]
    if hd:
        w("文件 truth 为截断、pred 为能拿到的 %d 条，文字是：%s。" % (
            len(hd), "、".join("%s @ %s#%s" % ((text_of(r) or "（无文字）"), r["id"], r["box_index"]) for r in hd),
        ))
        w("")
    w("这 2 条结果.md 写成样例 g05 左端「ArkUI实践」，按定义应改标。它们属于这份 48 条，不是上面 179 的定义改标行，除非同一案例也出现在模型框那份里。")
    w("")
    w("## 核对")
    w("")
    if pack["mismatches"]:
        w("有差额：")
        w("")
        for m in pack["mismatches"]:
            w("- " + m.replace("\n", " "))
    else:
        w("过滤后 259、去重 179、分来源 40/103/36、能下结论 103、类别表、人工标注框 48 的交叉表，都和结果.md 相同。")
    w("")

    text = "\n".join(lines)
    (OUT / "A_invariant_by_app.md").write_text(text, encoding="utf-8")

    write_csv(OUT / "A_invariant_by_app.csv", apps, [
        "app", "raw_names", "n", "decidable", "correct", "wrong", "blind",
        "true_trunc", "true_trunc_blind", "true_trunc_as_ok", "pred_trunc", "pred_ok",
    ])
    src_csv = []
    for code, s in src_rows:
        src_csv.append({"source": code, **s})
    src_csv.append({"source": "合计", **sm})
    write_csv(OUT / "A_invariant_by_source.csv", src_csv, [
        "source", "n", "decidable", "correct", "wrong", "blind",
        "true_trunc", "true_trunc_blind", "pred_trunc", "pred_ok",
    ])
    box_fields = [
        "source", "app", "app_raw", "slug", "page", "screen", "device", "text", "issue_type",
        "pred", "pred_zh", "truth_raw", "truth2", "truth_zh", "origin", "correct", "cls",
        "id", "box_index", "bbox", "slide_result", "clipper", "label", "dedup_n",
        "dedup_pred_conflict", "dedup_truth_conflict", "dedup_pages", "dedup_ids", "key_repr", "layout",
    ]
    write_csv(OUT / "A_invariant_boxes.csv", show, box_fields)
    write_csv(OUT / "A_invariant_dropped.csv", pack["dropped"], [
        "source", "app", "app_raw", "page", "screen", "text", "issue_type", "id", "box_index",
        "truth_raw", "origin", "pred", "cls",
    ])
    write_csv(OUT / "A_invariant_dedup_merges.csv", merges, [
        "source", "app", "dedup_n", "pred_values", "truth_values", "pred_conflict", "truth_conflict",
        "pages", "ids", "kept_id", "kept_box", "text", "issue_type", "key",
    ])
    return sm, apps


def parse_hits(hits):
    codes = []
    raw_extra = []
    if not isinstance(hits, list):
        return ["UNPARSED"], [repr(hits)]
    for h in hits:
        if not isinstance(h, str):
            codes.append("UNPARSED")
            raw_extra.append(repr(h))
            continue
        found = re.findall(r"P[1-6]", h)
        if not found:
            codes.append("UNPARSED")
            raw_extra.append(h)
        else:
            codes.extend(found)
            if h not in found:
                raw_extra.append(h)
    return codes, raw_extra


def write_open_close():
    mismatches = []
    runs = sorted(p for p in OC.iterdir() if p.is_dir())
    groups = []
    extra_json = []
    for run in runs:
        prefix = run.name.split("_uniform_")[0]
        if "_uniform_" not in run.name:
            mismatches.append("run 名不含 _uniform_: %s" % run.name)
        all_json = sorted(run.glob("*.json"))
        t_json = [p for p in all_json if re.fullmatch(r"t\d+\.json", p.name)]
        if len(all_json) != len(t_json):
            extra_json.append((run.name, sorted(set(p.name for p in all_json) - set(p.name for p in t_json))))
        nums = []
        for p in t_json:
            j = json.loads(p.read_text(encoding="utf-8"))
            codes, extra = parse_hits(j.get("hits"))
            # preserve order, unique
            seen = []
            for c in codes:
                if c not in seen:
                    seen.append(c)
            result = str(j.get("result") or "").strip()
            groups.append({
                "run": run.name,
                "prefix": prefix,
                "test": p.stem,
                "test_n": int(p.stem[1:]),
                "result": result,
                "cut10": str(j.get("result_cut10") or "").strip(),
                "cut20": str(j.get("result_cut20") or "").strip(),
                "hits": seen,
                "hits_raw": j.get("hits"),
                "hit_extra": extra,
                "notes": j.get("notes") or "",
                "not_covered": j.get("not_covered") or "",
                "bucket": (j.get("_meta") or {}).get("bucket"),
                "model": (j.get("_meta") or {}).get("model"),
                "keys": sorted(j.keys()),
                "meta_keys": sorted((j.get("_meta") or {}).keys()),
            })
            nums.append(int(p.stem[1:]))
        if nums:
            missing = [i for i in range(min(nums), max(nums) + 1) if i not in set(nums)]
            if missing or min(nums) != 1:
                groups.append({
                    "_gap": True,
                    "run": run.name,
                    "missing": missing,
                    "min": min(nums),
                    "max": max(nums),
                    "n": len(nums),
                })

    gaps = [g for g in groups if g.get("_gap")]
    groups = [g for g in groups if not g.get("_gap")]
    n = len(groups)
    by_result = Counter(g["result"] for g in groups)
    fail = [g for g in groups if g["result"] == "fail"]
    prefixes = sorted(set(g["prefix"] for g in groups))

    with FAIL_CSV.open(encoding="utf-8-sig", newline="") as f:
        fail_rows = list(csv.DictReader(f))
    run_zh = defaultdict(set)
    for r in fail_rows:
        run_zh[r["run"]].add(r["app"])
    mixed = {k: v for k, v in run_zh.items() if len(v) != 1}
    if mixed:
        mismatches.append("fail 索引同一 run 多个中文名: %s" % mixed)

    # hos has zero fails; Chinese name is in the package prose, not in the json.
    HOS_ZH = "去哪儿"
    prefix_zh = {}
    prefix_zh_src = {}
    for pre in prefixes:
        names = set()
        for run, zs in run_zh.items():
            if run.split("_uniform_")[0] == pre:
                names |= zs
        if len(names) == 1:
            prefix_zh[pre] = next(iter(names))
            prefix_zh_src[pre] = "fail_266_索引.csv 的 app 列"
        elif len(names) == 0 and pre == "hos":
            prefix_zh[pre] = HOS_ZH
            prefix_zh_src[pre] = "口径说明里的「hos（去哪儿）」；该前缀 fail=0，索引里没有行"
        elif len(names) == 0:
            prefix_zh[pre] = "（索引和口径都没有中文名）"
            prefix_zh_src[pre] = "缺失"
            mismatches.append("前缀 %s 没有中文名" % pre)
        else:
            prefix_zh[pre] = " / ".join(sorted(names))
            prefix_zh_src[pre] = "同一前缀在索引里有多个中文名"
            mismatches.append("前缀 %s 多个中文名 %s" % (pre, names))

    # summary.json is a check, not the source of counts
    summary = json.loads((OC / "summary.json").read_text(encoding="utf-8"))
    if summary.get("n") != n:
        mismatches.append("summary.json n=%s，json 文件 %d" % (summary.get("n"), n))
    for k, v in summary.get("counts", {}).items():
        got = by_result.get(k, 0) if k in ("fail", "pass", "uncertain", "invalid") else None
        if k == "other":
            got = sum(v for name, v in by_result.items() if name not in ("fail", "pass", "uncertain", "invalid"))
        if k == "error":
            continue
        if got is not None and got != v:
            mismatches.append("summary counts %s: 文件 %s，summary %s" % (k, got, v))

    def blank_hit_fail():
        return sum(1 for g in fail if not g["hits"])

    if blank_hit_fail():
        mismatches.append("fail 但 hits 为空: %d" % blank_hit_fail())
    nonempty_nonfail = [g for g in groups if g["result"] != "fail" and g["hits"]]
    if nonempty_nonfail:
        mismatches.append("非 fail 但 hits 非空: %d" % len(nonempty_nonfail))

    code_names = ["P1", "P2", "P3", "P4", "P5", "P6"]
    code_count = {c: sum(1 for g in fail if c in g["hits"]) for c in code_names}
    only_p1 = [g for g in fail if g["hits"] == ["P1"]]
    unparsed = [g for g in fail if "UNPARSED" in g["hits"] or g["hit_extra"]]
    gray = [g for g in fail if g["cut10"] == "fail" and g["cut20"] == "pass"]

    # per app / per run
    def pack_stats(rs):
        rs_fail = [g for g in rs if g["result"] == "fail"]
        d = Counter(g["result"] for g in rs)
        return {
            "n": len(rs),
            "fail": d.get("fail", 0),
            "pass": d.get("pass", 0),
            "invalid": d.get("invalid", 0),
            "uncertain": d.get("uncertain", 0),
            "other": sum(v for k, v in d.items() if k not in ("fail", "pass", "invalid", "uncertain")),
            "only_p1": sum(1 for g in rs_fail if g["hits"] == ["P1"]),
            **{c: sum(1 for g in rs_fail if c in g["hits"]) for c in code_names},
        }

    app_rows = []
    for pre in sorted(prefixes, key=lambda p: (-sum(1 for g in groups if g["prefix"] == p), p)):
        rs = [g for g in groups if g["prefix"] == pre]
        run_names = sorted(set(g["run"] for g in rs))
        st = pack_stats(rs)
        judged = st["fail"] + st["pass"]
        app_rows.append({
            "prefix": pre,
            "app_zh": prefix_zh[pre],
            "zh_source": prefix_zh_src[pre],
            "n_runs": len(run_names),
            "runs": " ".join(run_names),
            "judged": judged,
            "fail_rate_all": (st["fail"] / st["n"]) if st["n"] else 0,
            "fail_rate_judged": (st["fail"] / judged) if judged else 0,
            **st,
        })
        sj = (summary.get("by_app") or {}).get(pre)
        if sj:
            for fld in ("n", "fail", "pass", "invalid", "uncertain"):
                if sj.get(fld, 0) != st[fld]:
                    mismatches.append("summary by_app %s %s: 文件 %s，summary %s" % (pre, fld, st[fld], sj.get(fld)))
        elif pre in (summary.get("by_app") or {}):
            pass
        else:
            mismatches.append("summary.json 没有前缀 %s" % pre)

    run_rows = []
    for run in runs:
        rs = [g for g in groups if g["run"] == run.name]
        st = pack_stats(rs)
        judged = st["fail"] + st["pass"]
        pre = run.name.split("_uniform_")[0]
        nums = sorted(g["test_n"] for g in rs)
        missing = [i for i in range(1, (nums[-1] if nums else 0) + 1) if i not in set(nums)]
        run_rows.append({
            "run": run.name,
            "prefix": pre,
            "app_zh": prefix_zh[pre],
            "test_min": nums[0] if nums else "",
            "test_max": nums[-1] if nums else "",
            "missing_tests": " ".join(str(i) for i in missing),
            "judged": judged,
            "fail_rate_all": (st["fail"] / st["n"]) if st["n"] else 0,
            "fail_rate_judged": (st["fail"] / judged) if judged else 0,
            **st,
        })

    # fail index set compare
    json_fail_keys = set((g["run"], g["test"]) for g in fail)
    csv_fail_keys = set((r["run"], r["test"]) for r in fail_rows)
    if json_fail_keys != csv_fail_keys:
        mismatches.append("fail 组与索引不一致：只在 json %d，只在 csv %d" % (
            len(json_fail_keys - csv_fail_keys), len(csv_fail_keys - json_fail_keys),
        ))
    csv_gray = sum(1 for r in fail_rows if r.get("only_gray_cut10_fail") == "是")

    # key uniformity
    key_set = set(tuple(g["keys"]) for g in groups)
    meta_set = set(tuple(g["meta_keys"]) for g in groups)
    models = Counter(g["model"] for g in groups)
    buckets = Counter(g["bucket"] for g in groups)

    needles = {
        "bili": ["哔哩哔哩", "哔哩"],
        "dianping": ["大众点评", "点评"],
        "hmeituan": ["美团"],
        "hmos": ["知乎"],
        "hongmeng": ["大麦"],
        "hos": ["去哪儿", "去哪"],
        "hosapp": ["唯品会"],
        "idlefish4ohos": ["闲鱼"],
        "life": ["58同城"],
        "mall": ["京东"],
        "news_toutiao": ["今日头条", "头条"],
        "news_tx": ["腾讯新闻"],
        "stage": ["微博"],
        "xhs_hos": ["小红书"],
    }

    def note_has(g, words):
        blob = g["notes"] + "\n" + g["not_covered"]
        return any(w in blob for w in words)

    note_counts = {}
    for pre in prefixes:
        rs = [g for g in groups if g["prefix"] == pre]
        if pre == "news":
            note_counts[pre] = {
                "头条": sum(1 for g in rs if note_has(g, needles["news_toutiao"])),
                "腾讯新闻": sum(1 for g in rs if note_has(g, needles["news_tx"])),
                "n": len(rs),
            }
        else:
            words = needles.get(pre, [])
            note_counts[pre] = {
                "命中": sum(1 for g in rs if words and note_has(g, words)),
                "n": len(rs),
                "词": "、".join(words),
            }

    lines = []
    w = lines.append
    w("# 开合 849 组打标分布")
    w("")
    w("复现：`python3 /tmp/ana_0123/analyze_0123.py`")
    w("")
    w("每一组是一个 `tNN.json`。result、hits、result_cut10、result_cut20 都从该 json 读。`summary.json`、`summary.md`、`fail_266_索引.csv` 只做核对，不作为计数来源。规则原文用来解释 P1–P6 是什么，没有按规则重判。")
    w("")
    w("目录：`/Users/zhangyingying/UX-Agent/docs/开合检测/交付/打包_2026-11-17_双折叠开合/02_打标结果_vlm_judge_1029_gpt/`")
    w("")
    w("## 1. 规模")
    w("")
    w("- run 目录 %d 个。每个目录名都含 `_uniform_`，前缀取这之前的一段。" % len(runs))
    w("- 前缀 %d 个，映射成 %d 个中文名。`news` 的中文名就是索引里的「%s」，json 里没有字段可以再拆成今日头条和腾讯新闻，所以 App 数按 13 计，不按 14。" % (
        len(prefixes), len(set(prefix_zh.values())), prefix_zh.get("news", ""),
    ))
    w("- 组数 %d。材料写的是 849。差额：%d。" % (n, n - 849))
    w("- fail %d，pass %d，invalid %d，uncertain %d，其他 %d。材料写 fail 约 266。差额：fail %d。" % (
        by_result.get("fail", 0), by_result.get("pass", 0), by_result.get("invalid", 0),
        by_result.get("uncertain", 0),
        sum(v for k, v in by_result.items() if k not in ("fail", "pass", "invalid", "uncertain")),
        by_result.get("fail", 0) - 266,
    ))
    if not gaps and all(not r["missing_tests"] for r in run_rows):
        w("- 各 run 的 t 编号都从 t01 连续到最后一号，没有缺号。组数等于文件数。")
    else:
        w("- 编号缺口：")
        for r in run_rows:
            if r["missing_tests"] or r["test_min"] not in (1, "1"):
                w("  - %s min=%s max=%s 缺 %s" % (r["run"], r["test_min"], r["test_max"], r["missing_tests"] or "无"))
    if extra_json:
        w("- run 目录里还有不是 tNN.json 的 json：%s" % extra_json)
    else:
        w("- run 目录里的 json 都是 `t` 加数字，没有别的 json。")
    w("- `_meta.model`：%s。`_meta.bucket`：%s。" % (
        "、".join("%s %d" % (k, v) for k, v in models.most_common()),
        "、".join("%s %d" % (k, v) for k, v in buckets.most_common()),
    ))
    w("")
    w("## 2. 按 App")
    w("")
    w("同一前缀的多个 run 已合并。分 run 的数在第 5 节和 `/tmp/ana_0123/B_open_close_by_run.csv`。")
    w("")
    w("fail 率两列都给：`fail/组数` 的分母含 invalid；`fail/已判定` 的分母是 fail+pass。去哪儿几乎全是 invalid，两列差很多。")
    w("")
    w(md_table(
        ["前缀", "中文名", "run数", "组数", "fail", "pass", "invalid", "uncertain", "fail/组数", "fail/已判定", "只P1"],
        [[
            a["prefix"], a["app_zh"], a["n_runs"], a["n"], a["fail"], a["pass"], a["invalid"], a["uncertain"],
            pct(a["fail"], a["n"]),
            pct(a["fail"], a["judged"]) if a["judged"] else "0/0",
            a["only_p1"],
        ] for a in sorted(app_rows, key=lambda a: (-a["fail"], a["prefix"]))] + [[
            "合计", "%d 个前缀" % len(app_rows), len(runs), n,
            by_result.get("fail", 0), by_result.get("pass", 0), by_result.get("invalid", 0), by_result.get("uncertain", 0),
            pct(by_result.get("fail", 0), n),
            pct(by_result.get("fail", 0), by_result.get("fail", 0) + by_result.get("pass", 0)),
            len(only_p1),
        ]],
    ))
    w("")
    w("中文名来源：")
    w("")
    for a in sorted(app_rows, key=lambda x: x["prefix"]):
        w("- `%s` → %s。%s。" % (a["prefix"], a["app_zh"], a["zh_source"]))
    w("")
    w("备注抽查只用来看中文名是否出现在 notes / not_covered 里，不用来改上表，也不用来分页面类型。一句备注可以两个词都不写。")
    w("")
    w(md_table(
        ["前缀", "抽查", "组数"],
        [[
            pre,
            "、".join("%s %s" % (k, v) for k, v in note_counts[pre].items() if k != "n"),
            note_counts[pre]["n"],
        ] for pre in sorted(note_counts)],
    ))
    w("")
    w("`news` 这一行的「头条」「腾讯新闻」是备注里出现该词的组数，不是拆开后的 App 组数。")
    w("")
    w("表文件：`/tmp/ana_0123/B_open_close_849.csv`。")
    w("")

    w("## 3. fail 组的 hit 码")
    w("")
    w("只统计 result=fail 的组。一组可以同时命中多条，所以下面的组数相加大于 fail 组数。码从 hits 数组里用 P1–P6 抽出。")
    w("")
    w(md_table(
        ["码", "含该码的 fail 组"],
        [[c, code_count[c]] for c in code_names],
    ))
    w("")
    w("只命中 P1 一条（hits 解析后恰好是 [P1]）的 fail 组：%d。材料写约 201。差额：%d。" % (len(only_p1), len(only_p1) - 201))
    w("")
    w("fail 组 %d 里，含 P1 的 %d，不含 P1 的 %d。" % (
        len(fail), code_count["P1"], len(fail) - code_count["P1"],
    ))
    others = [g for g in fail if g["hits"] != ["P1"]]
    combo = Counter(tuple(g["hits"]) for g in fail)
    w("")
    w("hits 组合（解析后，去重保序）：")
    w("")
    w(md_table(
        ["hits", "组数"],
        [[" ".join(k) if k else "（空）", v] for k, v in combo.most_common()],
    ))
    w("")
    prose = [g for g in fail if g["hit_extra"]]
    if prose:
        w("有 %d 条 hits 不是裸编号，原文并进了说明。解析时只取其中的 P 码。" % len(prose))
        w("")
        w(md_table(
            ["run", "test", "解析", "原文"],
            [[g["run"], g["test"], " ".join(g["hits"]), cut(" || ".join(g["hit_extra"]), 80)] for g in prose],
        ))
        w("")
    if unparsed:
        w("解析失败 %d 条。" % len([g for g in fail if "UNPARSED" in g["hits"]]))
        w("")
    w("灰区核对（不是另做的分类）：result=fail 且 result_cut10=fail 且 result_cut20=pass 的组有 %d。索引 README 写 30，索引列 only_gray_cut10_fail=是 的行有 %d。" % (len(gray), csv_gray))
    w("")
    w("表文件：`/tmp/ana_0123/B_open_close_hits.csv`。")
    w("")

    w("## 4. 页面类型")
    w("")
    w("推不出。")
    w("")
    w("849 个 json 的顶层键都是同一组：%s。" % "、".join(sorted(next(iter(key_set))) if len(key_set) == 1 else []))
    if len(key_set) != 1:
        w("顶层键并不完全一样，有 %d 种。" % len(key_set))
    w("")
    w("`_meta` 的键都是：%s。没有页面名、模板号、页面类型。" % (
        "、".join(sorted(next(iter(meta_set)))) if len(meta_set) == 1 else "多种",
    ))
    w("")
    w("这个打包目录下没有布局树。截图文件名在 `_meta` 里是 `tNN_1_folded.png` 这种，也没有页面类型。notes 是自由文本，没有按首页 / 详情 / 搜索 / 列表 / 弹层去分类，避免编出一列 fail 率。")
    w("")

    w("## 5. 同一 App 的多个 run 是否合并")
    w("")
    w("第 2 节按前缀合并了。dianping 有 %d 个 run，合并后是上表那一行（大众点评）。分开的数：" % sum(1 for r in run_rows if r["prefix"] == "dianping"))
    w("")
    multi = [a for a in app_rows if a["n_runs"] > 1]
    w("前缀对应多个 run 的有 %d 个：%s。" % (
        len(multi), "、".join("%s %d 个 run" % (a["prefix"], a["n_runs"]) for a in sorted(multi, key=lambda a: a["prefix"])),
    ))
    w("")
    w(md_table(
        ["run", "前缀", "中文名", "组数", "fail", "pass", "invalid", "fail/组数", "只P1"],
        [[
            r["run"], r["prefix"], r["app_zh"], r["n"], r["fail"], r["pass"], r["invalid"],
            pct(r["fail"], r["n"]), r["only_p1"],
        ] for r in run_rows],
    ))
    w("")
    w("表文件：`/tmp/ana_0123/B_open_close_by_run.csv`。")
    w("")
    w("## 核对")
    w("")
    if json_fail_keys == csv_fail_keys:
        w("fail 的 (run, test) 与 `fail_266_索引.csv` 的 266 行一一对应。")
    else:
        w("fail 的 (run, test) 与索引不一致。")
    if not mismatches:
        w("与 `summary.json` 的总数和分前缀 n/fail/pass/invalid/uncertain 一致。")
    else:
        w("差额：")
        for m in mismatches:
            w("- " + m)
    w("")
    (OUT / "B_open_close_849.md").write_text("\n".join(lines), encoding="utf-8")

    write_csv(OUT / "B_open_close_849.csv", sorted(app_rows, key=lambda a: (-a["fail"], a["prefix"])), [
        "prefix", "app_zh", "zh_source", "n_runs", "runs", "n", "fail", "pass", "invalid", "uncertain", "other",
        "judged", "fail_rate_all", "fail_rate_judged", "only_p1", "P1", "P2", "P3", "P4", "P5", "P6",
    ])
    write_csv(OUT / "B_open_close_by_run.csv", run_rows, [
        "run", "prefix", "app_zh", "n", "fail", "pass", "invalid", "uncertain", "other",
        "judged", "fail_rate_all", "fail_rate_judged", "only_p1", "P1", "P2", "P3", "P4", "P5", "P6",
        "test_min", "test_max", "missing_tests",
    ])
    hit_csv = [{"code": c, "fail_groups": code_count[c]} for c in code_names]
    hit_csv.append({"code": "only_P1", "fail_groups": len(only_p1)})
    hit_csv.append({"code": "fail_groups", "fail_groups": len(fail)})
    hit_csv.append({"code": "gray_cut10_fail_cut20_pass", "fail_groups": len(gray)})
    write_csv(OUT / "B_open_close_hits.csv", hit_csv, ["code", "fail_groups"])
    # combo detail
    write_csv(
        OUT / "B_open_close_hit_combos.csv",
        [{"hits": " ".join(k), "n": v} for k, v in combo.most_common()],
        ["hits", "n"],
    )
    return {
        "n": n,
        "runs": len(runs),
        "prefixes": len(prefixes),
        "fail": by_result.get("fail", 0),
        "only_p1": len(only_p1),
        "mismatches": mismatches,
        "code_count": code_count,
        "gray": len(gray),
        "app_rows": app_rows,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pack = build_invariant()
    write_invariant(pack)
    oc = write_open_close()
    print("A mismatches", len(pack["mismatches"]))
    for m in pack["mismatches"]:
        print(" A", m)
    print("A uniq", len(pack["uniq"]), "dropped", len(pack["dropped"]), "merges", len(pack["merges"]))
    print("B", {k: oc[k] for k in ("n", "runs", "prefixes", "fail", "only_p1", "gray")})
    print("B codes", oc["code_count"])
    print("B mismatches", len(oc["mismatches"]))
    for m in oc["mismatches"]:
        print(" B", m)
    apps = {}
    # print concentration from the csv we can recompute quickly
    from collections import defaultdict as dd
    by = dd(int)
    by_dec = dd(int)
    for r in pack["uniq"]:
        by[r["app"]] += 1
        if r["pred"] != "undecided":
            by_dec[r["app"]] += 1
    print("apps", len(by), "dec_apps", sum(1 for v in by_dec.values() if v))
    for a, n in sorted(by_dec.items(), key=lambda kv: -kv[1]):
        if n:
            print(" dec", n, a)
    if pack["mismatches"] or oc["mismatches"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
