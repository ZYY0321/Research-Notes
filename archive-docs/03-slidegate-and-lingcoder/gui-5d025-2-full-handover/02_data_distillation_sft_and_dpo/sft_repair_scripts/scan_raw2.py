#!/usr/bin/env python3
"""Classify every dangling file_action in RAW result.jsonl into sub-classes:
 - finalization: has <subtask_result> (legit subtask terminal, not a break)
 - gateway_leak: malformed fa (open!=close) or </invoke>/<invoke leak (real tool-call parse failure)
 - clean_stop: well-formed fa, no subtask_result, no leak
Also: is the case terminal-success?"""
import json, sys, glob, os
from collections import Counter
FA_O="<file_action>"; FA_C="</file_action>"
def classify(c):
    leak = ("</invoke>" in c) or ("<invoke" in c) or ("antml:invoke" in c) or (c.count(FA_O)!=c.count(FA_C))
    sub = "<subtask_result>" in c
    if sub and not leak: return "finalization"
    if leak: return "gateway_leak"
    return "clean_stop"
def trajs(rec):
    yield ("main", rec.get("messages") or [])
    for sid,s in ((rec.get("state") or {}).get("runtime_control",{}).get("subtasks") or {}).items():
        yield (sid, s.get("messages") or [])
def main():
    batch=sys.argv[1]; cap=int(sys.argv[2]) if len(sys.argv)>2 else 100000
    agg=Counter(); n=0
    for d in sorted(glob.glob(os.path.join(batch,"*"))):
        if n>=cap: break
        rp=os.path.join(d,"result.jsonl")
        if not os.path.isdir(d) or not os.path.exists(rp): continue
        try: rec=json.loads(open(rp,encoding="utf-8").read())
        except: continue
        n+=1
        succ=bool((rec.get("result") or {}).get("success"))
        for src,msgs in trajs(rec):
            for m in msgs:
                if m.get("role")!="assistant": continue
                c=m.get("content") or ""
                if FA_O in c and not (m.get("tool_calls")):
                    cls=classify(c)
                    agg[cls]+=1
                    agg[f"{cls}__{'main' if src=='main' else 'subtask'}"]+=1
                    if succ: agg[f"{cls}__success"]+=1
    print(json.dumps({"batch":os.path.basename(batch.rstrip('/')),"scanned":n,"agg":dict(agg)},ensure_ascii=False))
if __name__=="__main__": main()
