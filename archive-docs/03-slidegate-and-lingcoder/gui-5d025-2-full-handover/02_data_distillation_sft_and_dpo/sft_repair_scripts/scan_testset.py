#!/usr/bin/env python3
"""Measure file_action behavior of a model on a testset (main.json + subtask_*.json per case)."""
import json, sys, glob, os
from collections import Counter
FA_O="<file_action>"; FA_C="</file_action>"
LEAK=["</invoke>","<invoke","antml:invoke"]
WRITE={"write_file","execute_code","execute_shell_command"}
def scan_traj(msgs, agg, model_is_author=True):
    last_idx=max((i for i,m in enumerate(msgs) if m.get("role")=="assistant"), default=-1)
    for i,m in enumerate(msgs):
        if m.get("role")!="assistant": continue
        agg["assistant_msgs"]+=1
        c=m.get("content") or ""; tcs=m.get("tool_calls") or []
        names=[(tc.get("function") or {}).get("name") for tc in tcs]
        for tc in tcs:
            n=(tc.get("function") or {}).get("name")
            if n=="write_file":
                agg["wf_calls"]+=1
                if FA_O in c: agg["wf_with_fa"]+=1
            if n=="execute_code":
                agg["ec_calls"]+=1
                if FA_O in c: agg["ec_with_fa"]+=1
        if FA_O in c:
            agg["fa_msgs"]+=1
            if tcs:
                agg["fa_paired"]+=1
                if any(nm in WRITE for nm in names): agg["fa_paired_write"]+=1
            else:
                agg["fa_dangling"]+=1
                if i==last_idx: agg["dangling_last"]+=1
                if "<subtask_result>" in c: agg["dangling_subresult"]+=1
                if any(mk in c for mk in LEAK) or c.count(FA_O)!=c.count(FA_C): agg["dangling_leak"]+=1
def main():
    tset=sys.argv[1]
    agg=Counter(); cases=0
    for d in sorted(glob.glob(os.path.join(tset,"*"))):
        if not os.path.isdir(d): continue
        if not os.path.exists(os.path.join(d,"main.json")): continue
        cases+=1
        for f in [os.path.join(d,"main.json")]+sorted(glob.glob(os.path.join(d,"subtask_*.json"))):
            if not os.path.exists(f): continue
            try: j=json.load(open(f,encoding="utf-8"))
            except: continue
            scan_traj(j.get("messages") or [], agg)
    print(json.dumps({"testset":os.path.basename(tset.rstrip("/")),"cases":cases,"agg":dict(agg)},ensure_ascii=False))
if __name__=="__main__": main()
