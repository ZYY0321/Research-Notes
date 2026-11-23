#!/usr/bin/env python3
"""Extract specific messages from a jsonl trajectory by line number.
Usage: extract.py <file> <lineno> <msg_start> <msg_end>
Prints role, content(trunc), reasoning presence, tool_calls for msgs in [start,end].
"""
import json, sys

def get_line(path, lineno):
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i == lineno:
                return json.loads(line)
    return None

def show(path, lineno, ms, me):
    rec = get_line(path, lineno)
    if rec is None:
        print("NO SUCH LINE"); return
    msgs = rec.get("messages", [])
    print(f"CASE={rec.get('case_id')} agent={rec.get('agent')} subtask_id={rec.get('subtask_id')} "
          f"subtask_kind={rec.get('subtask_kind')} status={rec.get('status')} "
          f"total_steps={rec.get('total_steps')} n_msgs={len(msgs)} last_idx={len(msgs)-1}")
    for j in range(max(0,ms), min(len(msgs), me+1)):
        m = msgs[j]
        role = m.get("role")
        c = m.get("content")
        c = "" if c is None else c
        rc = m.get("reasoning_content")
        tcs = m.get("tool_calls") or []
        print(f"\n--- msg[{j}] role={role} content_len={len(c)} has_reasoning={rc is not None} n_tool_calls={len(tcs)} "
              f"success={m.get('success')} name={m.get('name')} ---")
        if c:
            print("CONTENT:", repr(c[:900]))
        for tc in tcs:
            fn = tc.get("function") or {}
            args = fn.get("arguments")
            aps = json.dumps(args, ensure_ascii=False) if isinstance(args,(dict,list)) else str(args)
            print(f"  TOOLCALL {fn.get('name')} id={tc.get('id')} args={aps[:220]}")

if __name__ == "__main__":
    show(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
