"""Best-effort read-only observations after a capture failure; never a valid sample."""

import json
import time
from pathlib import Path

from PIL import Image
from truncator.common.storage import digest, save, read


def validate_failure_evidence(attempt):
    """Verify the diagnostic archive independently from normal sample validation."""
    attempt = Path(attempt)
    summary = read(attempt / "failure.json")["diagnostics"]
    if summary.get("path") != "failure-evidence/evidence.json" or summary.get("sample_eligible") is not False:
        raise ValueError("Invalid failure diagnostic reference")
    manifest = attempt / summary["path"]
    if digest(manifest.read_bytes()) != summary["sha256"]:
        raise ValueError("Failure diagnostic manifest changed")
    record = read(manifest)
    if record.get("purpose") != "failure-diagnostic" or record.get("sample_eligible") is not False:
        raise ValueError("Failure diagnostic cannot be an eligible sample")
    names = {"tree-before.json", "snapshot.jpeg", "tree-after.json"}
    if set(record["files"]) - names or (record["status"] == "complete" and set(record["files"]) != names):
        raise ValueError("Unexpected failure diagnostic files")
    for name, checksum in record["files"].items():
        if digest((manifest.parent / name).read_bytes()) != checksum:
            raise ValueError("Failure diagnostic file changed: " + name)
    return record


def observe_failure(attempt, hdc):
    folder = Path(attempt) / "failure-evidence"
    folder.mkdir(exist_ok=False)
    remote = "/data/local/tmp/truncator-failure-" + digest(str(folder))[:12]
    result = {"purpose": "failure-diagnostic", "sample_eligible": False,
              "pairing": "sequential-observations-without-target-validation",
              "started_at": time.time(), "steps": [], "errors": {}, "files": {}}
    trees = {}

    def step(name, operation):
        item = {"name": name, "started_at": time.time()}
        result["steps"].append(item)
        try:
            operation()
            item["status"] = "observed"
        except Exception as error:
            item["status"] = "failed"
            result["errors"][name] = str(error)
        item["finished_at"] = time.time()
        save(folder / "evidence.json", result)

    def tree(name):
        path = remote + "-" + name + ".json"
        output = hdc("shell", "uitest", "dumpLayout", "-p", path)
        if "DumpLayout saved" not in output:
            raise RuntimeError("Diagnostic dumpLayout did not save a tree")
        value = json.loads(hdc("shell", "cat", path))
        save(folder / (name + ".json"), value)
        trees[name] = value

    step("tree-before", lambda: tree("tree-before"))
    step("snapshot", lambda: hdc("shell", "snapshot_display", "-f", remote + ".jpeg"))
    # Read the tree immediately after the screenshot, before host transfer.
    step("tree-after", lambda: tree("tree-after"))

    def receive():
        hdc("file", "recv", remote + ".jpeg", str(folder / "snapshot.jpeg"))
        with Image.open(folder / "snapshot.jpeg") as image:
            image.load()
            result["image_size_px"] = list(image.size)

    if not result["errors"].get("snapshot"):
        step("image-transfer", receive)
    result["trees_equal"] = (trees["tree-before"] == trees["tree-after"]
                             if len(trees) == 2 else None)
    result["files"] = {p.name: digest(p.read_bytes()) for p in folder.iterdir()
                       if p.is_file() and p.name != "evidence.json"}
    result["finished_at"] = time.time()
    result["status"] = "complete" if len(trees) == 2 and "image_size_px" in result else "partial"
    save(folder / "evidence.json", result)
    return {"status": result["status"], "path": "failure-evidence/evidence.json",
            "sha256": digest((folder / "evidence.json").read_bytes()), "sample_eligible": False}
