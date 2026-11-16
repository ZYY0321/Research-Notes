#!/usr/bin/env python3
"""Build a balanced+shuffled backfill input jsonl (2000 cases) from the damaged rerun buckets.
Types (mode-axis × files-axis): nt-query / t-query / nt-files / t-files.
Balanced across the 4 types (capped by availability), then globally shuffled so any prefix
stays roughly balanced (survives mid-run stop / sandbox mass-failure)."""
import json, random, os
random.seed(20260714)
ROOT="/home/wangbo4/Workspace/Prjs/xhx_agent_v3"
TARGET=2000
def load(f):
    rows=[]
    for line in open(f,encoding="utf-8"):
        line=line.strip()
        if line: rows.append(json.loads(line))
    return rows
def typ(r):
    m=r.get("mode")
    tmpl = str(m).startswith("template") if m else False
    files = bool(r.get("files"))
    return ("template" if tmpl else "no-template", "files" if files else "query")
buckets={"q":load(f"{ROOT}/data/test_inputs/ppt_rerun_damaged_query_20260714.jsonl"),
         "t":load(f"{ROOT}/data/test_inputs/ppt_rerun_damaged_template_20260714.jsonl"),
         "f":load(f"{ROOT}/data/test_inputs/ppt_rerun_damaged_filebased_20260714.jsonl")}
# group by 4-type, deduping id globally (a query damaged in BOTH modes appears in 2 pools;
# runner uses id as output dir -> must be unique). Scarce (files) types keep priority.
by_type={}
seen_ids=set()
TYPE_ORDER=[("template","files"),("no-template","files"),("template","query"),("no-template","query")]
tmp={}
for rows in buckets.values():
    for r in rows:
        tmp.setdefault(typ(r), []).append(r)
for k in TYPE_ORDER:
    for r in tmp.get(k, []):
        if r.get("id") in seen_ids: continue
        seen_ids.add(r["id"]); by_type.setdefault(k, []).append(r)
avail={k:len(v) for k,v in by_type.items()}

# capped-balanced allocation summing to TARGET
types=sorted(by_type.keys())
alloc={k:0 for k in types}
remaining=TARGET; active=set(types)
# iteratively give equal share, capping at availability
while remaining>0 and active:
    share=remaining//len(active)
    if share==0:
        # distribute the last few to the largest-availability active types
        for k in sorted(active, key=lambda x: avail[x]-alloc[x], reverse=True):
            if remaining<=0: break
            if alloc[k]<avail[k]: alloc[k]+=1; remaining-=1
        break
    changed=False
    for k in list(active):
        room=avail[k]-alloc[k]
        take=min(share, room)
        alloc[k]+=take; remaining-=take
        if take>0: changed=True
        if alloc[k]>=avail[k]: active.discard(k)
    if not changed: break

# sample per type, combine, shuffle
picked=[]
for k in types:
    pool=by_type[k][:]
    random.shuffle(pool)
    picked.extend(pool[:alloc[k]])
random.shuffle(picked)

# verify filebased attachments exist (avoid input-side mass failure)
fb_missing=set(); fb_total=0
for r in picked:
    for fp in (r.get("files") or []):
        fb_total+=1
        if not os.path.exists(fp): fb_missing.add(fp)

out=f"{ROOT}/data/test_inputs/ppt_backfill_2000_balanced_20260714.jsonl"
with open(out,"w",encoding="utf-8") as fh:
    for r in picked:
        # keep only original runner-facing fields (drop nothing added; rows are already original)
        fh.write(json.dumps(r,ensure_ascii=False)+"\n")

# stats
from collections import Counter
c=Counter(typ(r) for r in picked)
print("=== availability per type ==="); [print(f"  {k}: {avail[k]}") for k in types]
print("\n=== ALLOCATED (total %d) ==="%len(picked))
for k in types: print(f"  {k}: {c[k]}")
tmpl_tot=sum(v for (m,_),v in c.items() if m=="template")
files_tot=sum(v for (_,fl),v in c.items() if fl=="files")
print(f"\naxis 无模板/有模板 : {len(picked)-tmpl_tot} / {tmpl_tot}")
print(f"axis query/带文件 : {len(picked)-files_tot} / {files_tot}")
# prefix balance sanity: first 200
pre=Counter(typ(r) for r in picked[:200])
print("\nfirst-200 prefix balance:", dict(pre))
print(f"\nfilebased attachments: {len(fb_missing)} distinct MISSING of {fb_total} refs")
# dedup check
ids=[r.get("id") for r in picked]
print("unique ids:", len(set(ids)), "/", len(ids))
print("\nOUTPUT:", out)
