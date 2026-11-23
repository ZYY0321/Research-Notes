#!/usr/bin/env python3
"""给 invariant_rejudge.mts 准备输入：测试集 71 条（框级真值来自 Labelme）+ 双折叠真机自测存档（页级真值来自 标注.csv）。

  python3 scripts/截断检测/invariant_build_cases.py <out_dir>
"""
import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)


def iou_norm_vs_gt(bbox, gt_path):
    """bbox 是 0~1000 归一化；Labelme 是像素。返回与任一 GT 框的最大交并比和覆盖率。"""
    g = json.loads(Path(gt_path).read_text(encoding="utf-8"))
    w, h = g["imageWidth"], g["imageHeight"]
    x1, y1, x2, y2 = bbox[0] / 1000 * w, bbox[1] / 1000 * h, bbox[2] / 1000 * w, bbox[3] / 1000 * h
    best = 0.0
    for sh in g.get("shapes", []):
        xs = [p[0] for p in sh["points"]]
        ys = [p[1] for p in sh["points"]]
        gx1, gy1, gx2, gy2 = min(xs), min(ys), max(xs), max(ys)
        ix = max(0, min(x2, gx2) - max(x1, gx1))
        iy = max(0, min(y2, gy2) - max(y1, gy1))
        inter = ix * iy
        if inter <= 0:
            continue
        a = (x2 - x1) * (y2 - y1)
        b = (gx2 - gx1) * (gy2 - gy1)
        best = max(best, inter / max(1e-6, min(a, b)))
    return best


testset = json.loads((ROOT / "test-set/回归/测试集71_官方模型框.json").read_text(encoding="utf-8"))
ts_cases = []
for c in testset:
    gt = Path(c["layout"]).with_suffix(".json")
    boxes = []
    for b in c["boxes"]:
        if c["label"] == "normal":
            truth = "not_truncation"
        else:
            truth = "truncation" if gt.exists() and iou_norm_vs_gt(b["bbox"], gt) >= 0.3 else "not_truncation_or_mislabel"
        boxes.append({**b, "truth": truth})
    ts_cases.append({"id": c["id"], "label": c["label"], "layout": c["layout"], "boxes": boxes})
(OUT / "cases_testset71.json").write_text(json.dumps(ts_cases, ensure_ascii=False, indent=1), encoding="utf-8")

rows = list(csv.DictReader(open(ROOT / "test-set/自测集_双折叠真机/标注.csv", encoding="utf-8-sig")))
run_dirs = {}
for repo in ["验收/远端main", "验收/远端main-A"]:
    d = ROOT / repo / "local/harmonyArena/ux-detect-output"
    if d.exists():
        for name in os.listdir(d):
            run_dirs.setdefault(name, d / name)

st_cases = []
for r in rows:
    d = run_dirs.get(r["run"])
    f = d / "snapshot_ux.json" if d else None
    if not f or not f.exists():
        continue
    j = json.loads(f.read_text(encoding="utf-8"))
    for s in j.get("screens", []):
        snap = s.get("snapshot") or {}
        layout = snap.get("layoutDumpPath")
        if not layout or not Path(layout).exists():
            continue
        outcome = {}
        for key, final in (("issues", "kept"), ("removedIssues", "removed"), ("unresolvedIssues", "unresolved")):
            for it in s.get(key) or []:
                sv = it.get("slide_verify") or {}
                outcome[tuple(it["bbox"])] = (sv.get("slide_result"), final)
        model = (s.get("raw") or {}).get("issues") or s.get("modelIssues") or []
        boxes = []
        for b in model:
            sr, final = outcome.get(tuple(b["bbox"]), (None, None))
            boxes.append({"issue_type": b.get("issue_type", ""), "bbox": b["bbox"], "truncated_edges": b.get("truncated_edges"),
                          "slide_result": sr, "final": final,
                          "truth": "not_truncation" if r["truth"] == "normal" else "page_truncated"})
        st_cases.append({"id": f"{r['run']}:{s.get('mode')}", "label": r["truth"], "layout": layout, "boxes": boxes,
                         "app": r["app"], "page": r["page"]})
(OUT / "cases_selftest.json").write_text(json.dumps(st_cases, ensure_ascii=False, indent=1), encoding="utf-8")


def screen_cases(f, label, truth_of):
    j = json.loads(f.read_text(encoding="utf-8"))
    out = []
    for s in j.get("screens", []):
        layout = (s.get("snapshot") or {}).get("layoutDumpPath")
        if not layout or not Path(layout).exists():
            cand = f.parent / ("snapshot_window.json" if s.get("mode") in (None, "dual", "default") else f"snapshot_{s.get('mode')}_window.json")
            layout = str(cand) if cand.exists() else (str(f.parent / "snapshot_window.json") if (f.parent / "snapshot_window.json").exists() else None)
        if not layout:
            continue
        outcome = {}
        for key, final in (("issues", "kept"), ("removedIssues", "removed"), ("unresolvedIssues", "unresolved")):
            for it in s.get(key) or []:
                sv = it.get("slide_verify") or {}
                outcome[tuple(it["bbox"])] = (sv.get("slide_result"), final)
        model = (s.get("raw") or {}).get("issues") or s.get("modelIssues") or []
        boxes = []
        for b in model:
            sr, final = outcome.get(tuple(b["bbox"]), (None, None))
            boxes.append({"issue_type": b.get("issue_type", ""), "bbox": b["bbox"], "truncated_edges": b.get("truncated_edges") or ([b["slide_direction"]] if b.get("slide_direction") else None),
                          "slide_result": sr, "final": final, "truth": truth_of(b)})
        out.append({"id": f"{f.parent.name}:{s.get('mode')}", "label": label, "layout": layout, "boxes": boxes,
                    "app": f.parent.parent.parent.name, "page": f.parent.parent.name})
    return out


acc_cases = []
for f in sorted((ROOT / "验收/检测结果").rglob("snapshot_ux.json")):
    if "官方看图模型" in f.parts:
        continue
    rel = f.relative_to(ROOT / "验收/检测结果").parts
    cat = rel[1]
    if "normal" in cat:
        acc_cases += screen_cases(f, "normal", lambda b: "not_truncation")
    else:
        gtdir = ROOT / "test-set" / Path(*rel[:4])
        gts = [p for p in gtdir.glob("*.json")]
        gt = gts[0] if gts else None
        acc_cases += screen_cases(f, "truncated", lambda b, gt=gt: ("truncation" if gt and iou_norm_vs_gt(b["bbox"], gt) >= 0.3 else "not_truncation_or_mislabel"))
(OUT / "cases_acceptance0929.json").write_text(json.dumps(acc_cases, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"测试集 {len(ts_cases)} 条 / {sum(len(c['boxes']) for c in ts_cases)} 框；自测 {len(st_cases)} 屏 / {sum(len(c['boxes']) for c in st_cases)} 框；"
      f"9 月验收 {len(acc_cases)} 屏 / {sum(len(c['boxes']) for c in acc_cases)} 框")
