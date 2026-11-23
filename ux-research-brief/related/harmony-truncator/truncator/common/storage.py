from pathlib import Path
import hashlib
import json
import os
import time
import uuid


def digest(value):
    return hashlib.sha256(
        value.encode("utf-8") if isinstance(value, str) else value
    ).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.replace(temporary, path)


def event(run, stage, **fields):
    with (Path(run) / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(
            json.dumps(
                {"time": time.time(), "stage": stage, **fields}, ensure_ascii=False
            )
            + "\n"
        )


def contained(root, relative):
    root = Path(root).resolve()
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Path escapes project: " + str(relative))
    return target
