#!/usr/bin/env python3
"""Confirm problems 1/2/3 in the RAW result.jsonl (not the exports).
For each case: main trajectory = top-level 'messages';
subtask trajectories = state.runtime_control.subtasks[*].messages.
Also collects paradox stats: for dangling file_action, did an earlier turn
in the SAME trajectory actually write (real tool call)? and did the case succeed?"""
import json, sys, glob, os
from collections import Counter

FA="<file_action>"
WRITE_ISH={"write_file","execute_code","execute_shell_command"}

def variant(c):
    cn="文件操作预播报协议" in c; en="File Action Protocol" in c; tag=FA in c
    if cn and en and tag: return "canonical"
    if (not cn) and (not en) and tag: return "incomplete(tag-only)"
    if (not cn) and en and tag: return "bigEN"
    if not (cn or en or tag): return "no-protocol-at-all"
    return f"other({int(cn)}{int(en)}{int(tag)})"

def scan_traj(msgs, agg, src):
    """src = 'main' or 'subtask'. Returns nothing; mutates agg."""
    last_asst_idx=max((i for i,m in enumerate(msgs) if m.get("role")=="assistant"), default=-1)
    wrote_before=False
    for i,m in enumerate(msgs):
        if m.get("role")!="assistant": continue
        c=m.get("content") or ""
        tcs=m.get("tool_calls") or []
        names={ (tc.get("function") or {}).get("name") for tc in tcs }
        # problem 2: write_file w/o file_action
        if "write_file" in names:
            agg["wf_calls"]+=sum(1 for tc in tcs if (tc.get("function") or {}).get("name")=="write_file")
            if FA not in c:
                agg["wf_no_fa"]+=sum(1 for tc in tcs if (tc.get("function") or {}).get("name")=="write_file")
        # problem 3: file_action w/o toolcall
        if FA in c:
            agg["fa_msgs"]+=1
            if not tcs:
                agg["fa_dangling"]+=1
                agg[f"fa_dangling_{src}"]+=1
                if "<subtask_result>" in c: agg["fa_dangling_has_subresult"]+=1
                if i==last_asst_idx: agg["fa_dangling_is_last"]+=1
                if wrote_before: agg["fa_dangling_wrote_earlier"]+=1  # paradox: real write already done
        if names & WRITE_ISH:
            wrote_before=True

def main():
    batch=sys.argv[1]; cap=int(sys.argv[2]) if len(sys.argv)>2 else 100000
    agg=Counter()
    agg_extra={"sys_variant_main":Counter(),"sys_variant_sub":Counter()}
    cases=sorted(d for d in glob.glob(os.path.join(batch,"*")) if os.path.isdir(d))
    scanned=0
    for d in cases:
        if scanned>=cap: break
        rp=os.path.join(d,"result.jsonl")
        if not os.path.exists(rp): continue
        try:
            rec=json.loads(open(rp,encoding="utf-8").read())
        except Exception:
            agg["parse_err"]+=1; continue
        scanned+=1
        # case success / html
        succ=bool(((rec.get("result") or {}).get("success")))
        agg["cases"]+=1
        if succ: agg["cases_success"]+=1
        # main
        main_msgs=rec.get("messages") or []
        if main_msgs:
            sysm=next((m for m in main_msgs if m.get("role")=="system"),None)
            if sysm: agg_extra["sys_variant_main"][variant(sysm.get("content") or "")]+=1
            case_dangling_before=agg["fa_dangling"]
            scan_traj(main_msgs, agg, "main")
        # subtasks
        subs=((rec.get("state") or {}).get("runtime_control") or {}).get("subtasks") or {}
        for sid,sub in subs.items():
            sm=sub.get("messages") or []
            sysm=next((m for m in sm if m.get("role")=="system"),None)
            if sysm: agg_extra["sys_variant_sub"][variant(sysm.get("content") or "")]+=1
            scan_traj(sm, agg, "subtask")
        # does this successful case contain a dangling fa? (paradox at case level)
        if agg["fa_dangling"]>case_dangling_before:
            agg["cases_with_dangling_fa"]+=1
            if succ: agg["cases_with_dangling_fa_AND_success"]+=1
    out={"batch":os.path.basename(batch.rstrip("/")),"scanned":scanned,
         "agg":dict(agg),
         "sys_variant_main":dict(agg_extra["sys_variant_main"]),
         "sys_variant_sub":dict(agg_extra["sys_variant_sub"])}
    print(json.dumps(out,ensure_ascii=False))

if __name__=="__main__": main()
