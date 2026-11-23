#!/usr/bin/env python3
"""Second pass: categorize the Symptom-A dangling file_actions and the
file_action->non-write-tool mispairings. Streams one jsonl, emits JSON summary."""
import json, sys

FA_OPEN="<file_action>"; FA_CLOSE="</file_action>"
LEAK_MARKERS=["</invoke>","<invoke","<function_calls","</function_calls","<parameter","antml:"]
WRITE_ISH={"write_file","execute_code","execute_shell_command"}

def main(path):
    agg={
      "path":path,
      "dangling_total":0,            # fa in content, no tool_calls
      "dangling_last":0,
      "dangling_notlast":0,
      "dangling_malformed_fa":0,     # open!=close (truncated)
      "dangling_invoke_leak":0,      # tool-call XML leaked into content
      "dangling_subtask_result":0,   # finalization turn (has <subtask_result>)
      "dangling_clean_stop":0,       # well-formed fa, no leak, no subtask_result -> pure stop
      "dangling_by_agent":{},        # main/subtask
      "ex_leak":[], "ex_subtask_result":[], "ex_clean_stop":[],
      # file_action WITH tool_calls but NONE is a write-ish tool (mispaired target)
      "fa_tc_nonwrite":0,
      "ex_fa_tc_nonwrite":[],
      "fa_tc_total":0,
    }
    def bump(d,k): d[k]=d.get(k,0)+1
    with open(path,encoding="utf-8") as fh:
        for lineno,line in enumerate(fh):
            line=line.strip()
            if not line: continue
            try: rec=json.loads(line)
            except Exception: continue
            cid=rec.get("case_id","?"); agent=rec.get("agent","?")
            msgs=rec.get("messages",[]) or []
            last=len(msgs)-1
            for j,m in enumerate(msgs):
                if m.get("role")!="assistant": continue
                c=m.get("content") or ""
                tcs=m.get("tool_calls") or []
                if FA_OPEN not in c: continue
                if not tcs:
                    agg["dangling_total"]+=1
                    bump(agg["dangling_by_agent"], agent)
                    if j==last: agg["dangling_last"]+=1
                    else: agg["dangling_notlast"]+=1
                    malformed = c.count(FA_OPEN)!=c.count(FA_CLOSE)
                    leak = any(mk in c for mk in LEAK_MARKERS)
                    subres = "<subtask_result>" in c
                    if malformed: agg["dangling_malformed_fa"]+=1
                    if leak:
                        agg["dangling_invoke_leak"]+=1
                        if len(agg["ex_leak"])<6: agg["ex_leak"].append([cid,agent,lineno,j,c[-70:]])
                    if subres:
                        agg["dangling_subtask_result"]+=1
                        if len(agg["ex_subtask_result"])<6: agg["ex_subtask_result"].append([cid,agent,lineno,j])
                    if (not leak) and (not subres) and (not malformed):
                        agg["dangling_clean_stop"]+=1
                        if len(agg["ex_clean_stop"])<8: agg["ex_clean_stop"].append([cid,agent,lineno,j,c[-70:]])
                else:
                    agg["fa_tc_total"]+=1
                    names={ (tc.get("function") or {}).get("name") for tc in tcs }
                    if not (names & WRITE_ISH):
                        agg["fa_tc_nonwrite"]+=1
                        if len(agg["ex_fa_tc_nonwrite"])<8:
                            agg["ex_fa_tc_nonwrite"].append([cid,agent,lineno,j,sorted(n for n in names if n)])
    print(json.dumps(agg,ensure_ascii=False))

if __name__=="__main__":
    main(sys.argv[1])
