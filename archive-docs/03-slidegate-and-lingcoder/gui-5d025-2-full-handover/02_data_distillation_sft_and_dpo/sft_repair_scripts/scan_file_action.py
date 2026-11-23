#!/usr/bin/env python3
"""Scan an xhx-agent SFT jsonl for File Action Protocol data-quality issues.

Three questions:
  Q1: does every system prompt contain the File Action Protocol?
  Q2: is every file-writing tool call preceded by a <file_action> (same assistant msg)?
  Q3: is every <file_action> followed by a tool call (same assistant msg)?  [key symptom]

Output: a JSON summary to stdout.
"""
import json, sys

PROTO_MARKERS = ["文件操作预播报协议", "File Action Protocol"]
FA_OPEN = "<file_action>"
FA_CLOSE = "</file_action>"
# Tools that unambiguously write files per the protocol's intent.
STRICT_WRITE_TOOLS = {"write_file"}
# Tools that MAY write files (shell/code) — reported separately, not asserted.
MAYBE_WRITE_TOOLS = {"execute_code", "execute_shell_command"}

def main(path):
    agg = {
        "path": path,
        "records": 0,
        "main_records": 0,
        "subtask_records": 0,
        "malformed_lines": 0,
        # Q1
        "sys_msgs_total": 0,
        "sys_with_proto": 0,
        "sys_without_proto": 0,
        "sys_without_proto_examples": [],   # (case_id, agent, line)
        "records_no_system_msg": 0,
        # assistant / file_action
        "assistant_msgs": 0,
        "assistant_with_fa": 0,             # >=1 <file_action> in content
        "fa_blocks_total": 0,               # total <file_action> open tags
        "fa_open_close_mismatch_msgs": 0,   # malformed (open != close) messages
        # Q3: file_action -> tool_call
        "fa_msg_with_toolcalls": 0,
        "fa_msg_without_toolcalls": 0,          # KEY SYMPTOM A
        "fa_no_tc_is_last_msg": 0,              # file_action then trajectory ends
        "fa_no_tc_not_last_msg": 0,
        "fa_no_tc_examples": [],               # (case_id, agent, line, msg_idx, is_last)
        # per-tool coverage (Q2)
        "tool_call_total": 0,
        "toolname_counts": {},                 # tool -> total calls
        "toolname_in_fa_msg": {},              # tool -> calls where msg had file_action
        # Symptom B: strict write tool without file_action
        "write_file_calls": 0,
        "write_file_without_fa": 0,
        "write_file_without_fa_examples": [],  # (case_id, agent, line, msg_idx)
        # multi-toolcall messages with file_action (protocol says fa maps to ONE next call)
        "fa_msg_multi_toolcalls": 0,
    }

    def bump(d, k):
        d[k] = d.get(k, 0) + 1

    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                agg["malformed_lines"] += 1
                continue
            agg["records"] += 1
            is_subtask = ("subtask_id" in rec) or (rec.get("agent") == "subtask")
            if is_subtask:
                agg["subtask_records"] += 1
            else:
                agg["main_records"] += 1
            case_id = rec.get("case_id", "?")
            agent = rec.get("agent", "?")
            msgs = rec.get("messages", []) or []

            # Q1: system prompt protocol presence
            sys_msgs = [m for m in msgs if m.get("role") == "system"]
            if not sys_msgs:
                agg["records_no_system_msg"] += 1
            for sm in sys_msgs:
                agg["sys_msgs_total"] += 1
                c = sm.get("content") or ""
                if any(mk in c for mk in PROTO_MARKERS):
                    agg["sys_with_proto"] += 1
                else:
                    agg["sys_without_proto"] += 1
                    if len(agg["sys_without_proto_examples"]) < 20:
                        agg["sys_without_proto_examples"].append([case_id, agent, lineno])

            last_idx = len(msgs) - 1
            for j, m in enumerate(msgs):
                if m.get("role") != "assistant":
                    continue
                agg["assistant_msgs"] += 1
                content = m.get("content") or ""
                tcs = m.get("tool_calls") or []
                n_open = content.count(FA_OPEN)
                n_close = content.count(FA_CLOSE)
                has_fa = n_open > 0
                has_tc = len(tcs) > 0

                if has_tc:
                    agg["tool_call_total"] += len(tcs)
                    for tc in tcs:
                        fn = (tc.get("function") or {})
                        name = fn.get("name", "?")
                        bump(agg["toolname_counts"], name)
                        if has_fa:
                            bump(agg["toolname_in_fa_msg"], name)
                        if name in STRICT_WRITE_TOOLS:
                            agg["write_file_calls"] += 1
                            if not has_fa:
                                agg["write_file_without_fa"] += 1
                                if len(agg["write_file_without_fa_examples"]) < 20:
                                    agg["write_file_without_fa_examples"].append(
                                        [case_id, agent, lineno, j])

                if has_fa:
                    agg["assistant_with_fa"] += 1
                    agg["fa_blocks_total"] += n_open
                    if n_open != n_close:
                        agg["fa_open_close_mismatch_msgs"] += 1
                    if has_tc:
                        agg["fa_msg_with_toolcalls"] += 1
                        if len(tcs) > 1:
                            agg["fa_msg_multi_toolcalls"] += 1
                    else:
                        agg["fa_msg_without_toolcalls"] += 1
                        is_last = (j == last_idx)
                        if is_last:
                            agg["fa_no_tc_is_last_msg"] += 1
                        else:
                            agg["fa_no_tc_not_last_msg"] += 1
                        if len(agg["fa_no_tc_examples"]) < 30:
                            agg["fa_no_tc_examples"].append([case_id, agent, lineno, j, is_last])

    print(json.dumps(agg, ensure_ascii=False))

if __name__ == "__main__":
    main(sys.argv[1])
