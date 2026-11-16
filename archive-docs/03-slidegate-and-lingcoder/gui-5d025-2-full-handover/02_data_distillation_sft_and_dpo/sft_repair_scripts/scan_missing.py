#!/usr/bin/env python3
"""Scan a batch dir: for each case, compare create_subtask count in main.json
vs number of subtask_*.json files. Report dropped subtasks + which stage."""
import json, sys, glob, os
from collections import Counter

def load(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return None

def cs_calls(main):
    out=[]
    for m in main.get("messages",[]):
        if m.get("role")!="assistant": continue
        for tc in (m.get("tool_calls") or []):
            fn=tc.get("function") or {}
            if fn.get("name")=="create_subtask":
                a=fn.get("arguments") or {}
                if isinstance(a,str):
                    try:a=json.loads(a)
                    except:a={}
                out.append((tc.get("id"), a.get("title") or ""))
    return out

def stage(title):
    t=title or ""
    if "大纲" in t or "风格" in t: return "outline/style"
    if "资产" in t or "素材" in t or "配图" in t: return "asset-planning"
    if "HTML" in t or "页面" in t and "复核" not in t and "重写" not in t: return "html-gen"
    if "复核" in t or "重写" in t or "review" in t.lower(): return "review/rewrite"
    if "研究" in t or "调研" in t or "检索" in t: return "research"
    return "other:"+t[:18]

def main():
    batch=sys.argv[1]
    res={"batch":os.path.basename(batch.rstrip("/")),
         "cases":0,"cases_with_main":0,"cases_missing":0,
         "total_created":0,"total_files":0,"total_dropped":0,
         "dropped_stage":Counter(),"dropped_ordinal":Counter(),
         "extra_files_cases":0,"examples":[]}
    for d in sorted(glob.glob(os.path.join(batch,"*"))):
        if not os.path.isdir(d): continue
        res["cases"]+=1
        mp=os.path.join(d,"main.json")
        if not os.path.exists(mp): continue
        main_j=load(mp)
        if not main_j: continue
        res["cases_with_main"]+=1
        created=cs_calls(main_j)
        subfiles=glob.glob(os.path.join(d,"subtask_*.json"))
        # parent ids present in exported subtask files
        present=set()
        for sf in subfiles:
            sj=load(sf)
            if sj: present.add(sj.get("parent_tool_call_id"))
        nfiles=len(subfiles)
        res["total_created"]+=len(created); res["total_files"]+=nfiles
        if nfiles>len(created): res["extra_files_cases"]+=1
        dropped=[(i,tid,title) for i,(tid,title) in enumerate(created) if tid not in present]
        if dropped:
            res["cases_missing"]+=1
            res["total_dropped"]+=len(dropped)
            for i,tid,title in dropped:
                res["dropped_stage"][stage(title)]+=1
                res["dropped_ordinal"][i]+=1   # 0-based position among created
            if len(res["examples"])<15:
                res["examples"].append({"case":os.path.basename(d),
                    "n_created":len(created),"n_files":nfiles,
                    "dropped":[{"ord":i,"title":t} for i,_,t in dropped]})
    res["dropped_stage"]=dict(res["dropped_stage"])
    res["dropped_ordinal"]=dict(res["dropped_ordinal"])
    print(json.dumps(res,ensure_ascii=False))

if __name__=="__main__": main()
