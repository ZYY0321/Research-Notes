"""Fetch a shared-cluster run task by task (facts + agent events only, no recordings) into a run-like directory.

python3 fetch_run_tasks.py <client_dir> <run_id> <task_package_dir> <out_run_dir> [--model M --strategy S --effort E]
The server's whole-run download packs every recording into one archive and times out for large runs; this reads
GET /api/v1/runs/{run}/tasks/{task} and the paginated GET /api/v1/runs/{run}/logs?kind=agent instead.
Output layout matches a downloaded run closely enough for extract.py: run.json, tasks/<id>/<attempt>/{task.json,
result.json, grading/score.json, agent/events.jsonl}. Sessions (policy-rejected commands) are not available this way.
"""
import argparse
import json
import os
import shutil
import ssl
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path


def client(client_dir):
    c = json.load(open(Path(client_dir) / ".state/access/client.json"))["clusters"]["office"]
    ctx = ssl.create_default_context()
    cert = c["certificate"]
    if not os.path.exists(str(cert)):
        f = tempfile.NamedTemporaryFile("w", suffix=".crt", delete=False)
        f.write(cert)
        f.close()
        cert = f.name
    ctx.load_verify_locations(cafile=cert)
    ctx.check_hostname = False

    def get(path, retries=4):
        for i in range(retries):
            try:
                req = urllib.request.Request(c["url"] + path, headers={"Authorization": "Bearer " + c["token"]})
                with urllib.request.urlopen(req, context=ctx, timeout=120) as r:
                    return json.loads(r.read())
            except Exception:  # noqa: BLE001
                if i == retries - 1:
                    raise
                time.sleep(5 * (i + 1))
    return get


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("client_dir")
    ap.add_argument("run_id")
    ap.add_argument("task_dir")
    ap.add_argument("out")
    ap.add_argument("--model", default="")
    ap.add_argument("--strategy", default="sky")
    ap.add_argument("--effort", default="")
    ap.add_argument("--ids", default="", help="file with task ids to fetch (default: all)")
    a = ap.parse_args()
    get = client(a.client_dir)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    run = get("/api/v1/runs/" + a.run_id)
    agent = run.get("agent") or {}
    (out / "run.json").write_text(json.dumps({
        "run_id": a.run_id, "source": "fetch_run_tasks.py (facts + agent events only)",
        "agent": {"model": agent.get("model", a.model), "gui_strategy": agent.get("gui_strategy", a.strategy),
                  "reasoning_effort": agent.get("reasoning_effort", a.effort)}}, ensure_ascii=False))
    tasks = [t.get("id") for t in run.get("tasks", [])]
    if a.ids:
        keep = set(Path(a.ids).read_text().split())
        tasks = [t for t in tasks if t in keep]
    done = 0
    for tid in tasks:
        facts = get("/api/v1/runs/%s/tasks/%s" % (a.run_id, urllib.parse.quote(tid)))
        attempt = facts.get("attempt")
        if not attempt:
            continue
        adir = out / "tasks" / tid / attempt
        if (adir / ".complete").exists():
            done += 1
            continue
        (adir / "agent").mkdir(parents=True, exist_ok=True)
        (adir / "grading").mkdir(parents=True, exist_ok=True)
        src = Path(a.task_dir) / "tasks" / tid / "task.json"
        if src.exists():
            shutil.copy(src, adir / "task.json")
        else:
            (adir / "task.json").write_text(json.dumps({"id": tid, "instruction": ""}))
        assess = facts.get("assessment") or {}
        errors = [e if isinstance(e, dict) else {"message": str(e)} for e in
                  ((assess.get("agent_execution") or {}).get("errors") or [])]
        (adir / "result.json").write_text(json.dumps({
            "stage": facts.get("stage"), "agent": {"status": facts.get("agent_status")}, "grade": facts.get("grade"),
            "materials": assess.get("materials"), "errors": errors,
            "trajectory": {"status": "valid" if assess.get("sample_accepted") else "unknown"},
            "budget": {"spent": {"agent": 0}}}, ensure_ascii=False))
        grade = facts.get("grade") or {}
        (adir / "grading" / "score.json").write_text(json.dumps({"status": grade.get("status"), "score": grade.get("score")}))
        offset, chunks = 0, []
        while True:
            lg = get("/api/v1/runs/%s/logs?task=%s&kind=agent&offset=%d&attempt=%s"
                     % (a.run_id, urllib.parse.quote(tid), offset, attempt))
            if not lg.get("text"):
                break
            chunks.append(lg["text"])
            if lg["offset"] <= offset:
                break
            offset = lg["offset"]
        (adir / "agent" / "events.jsonl").write_text("".join(chunks))
        (adir / ".complete").write_text("")
        done += 1
        if done % 20 == 0:
            print("fetched", done, "/", len(tasks), flush=True)
    print("fetched", done, "of", len(tasks), "tasks ->", out)


if __name__ == "__main__":
    main()
