import base64, os, subprocess, sys, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED_PNG = os.path.expanduser("~/Desktop/e31-newapps/seed/poster.png")
SEED_TXT = os.path.expanduser("~/Desktop/e31-newapps/seed/attach-note.txt")
SEED_PNG_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAyAAAAJYCAIAAAAVFBUnAAAI0klEQVR42u3WMQ0AAAgEsfeEJzzhFhOEqUkV3HSpHgAADkUCAACDBQBgsAAADBYAAAYLAMBgAQAYLAAADBYAgMECADBYAAAYLAAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAwWAAABgsAwGABABgsAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQBgsAAADBYAgMECADBYAAAYLAAAgwUAYLAAADBYAAAGCwDAYAEAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAGCwAAAwWAAABgsAwGABAGCwAAAMFgCAwQIAwGABABgsAACDBQBgsAAAMFgAAAYLAMBgAQBgsAAADBYAgMECAMBgAQAYLAAAgwUAgMECADBYAAAGCwDAYAEAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAIDBAgAwWAAABgsAAIMFAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAACDBQBgsAAADBYAAAYLAMBgAQAYLAAAgwUAgMECADBYAAAGCwAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAIMFAIDBAgAwWAAABgsAAIMFAGCwAAAMFgAABgsAwGABABgsAAAMFgCAwQIAMFgAAAYLAACDBQBgsAAADBYAAAYLAMBgAQAYLAAADBYAgMECADBYAAAYLAAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAwWAAABgsAwGABABgsAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQAYLBUAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAwWAAABgsAwGABAGCwAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQBgsAAADBYAgMECAMBgAQAYLAAAgwUAYLAAADBYAAAGCwDAYAEAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAIDBAgAwWAAABgsAwGABAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAMBgqQAAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAIDBAgAwWAAABgsAAIMFAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAACDBQBgsAAADBYAAAYLAMBgAQAYLAAAgwUAgMECADBYAAAGCwAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAAwWAIDBAgAwWAAABgsAAIMFAGCwAAAMFgAABgsAwGABABgsAAAMFgCAwQIAMFgAAAZLAgAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAMFgAABgsAwGABABgsAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQAYLAAADBYAgMECADBYAAAYLAAAgwUAYLAAADBYAAAGCwDAYAEAYLAAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAwWAAABgsAwGABAGCwAAAMFgCAwQIAwGABABgsAACDBQBgsAAAMFgAAAYLAMBgAQBgsAAADBYAgMECAMBgAQAYLAAAgwUAYLAAADBYAAAGCwDAYAEAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAIDBAgAwWAAABgsAwGABAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAACDBQBgsAAADBYAgMECAMBgAQAYLAAAgwUAgMECADBYAAAGCwAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAIMFAIDBAgAwWAAABgsAAIMFAGCwAAAMFgAABgsAwGABABgsAACDBQCAwQIAMFgAAAYLAACDBQBgsAAADBYAAAYLAMBgAQAYLAAADBYAgMECADBYAAAGCwAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAMFgAABgsAwGABABgsAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQAYLAAADBYAgMECADBYAAAYLAAAgwUAYLAAADBYAAAGCwDAYAEAGCwVAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQBgsAAADBYAgMECADBYAAAYLAAAgwUAYLAAADBYAAAGCwDAYAEAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAGCwAAAwWAAABgsAwGABAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAMBgAQBgsAAADBYAgMECAMBgAQAYLAAAgwUAgMECADBYAAAGCwDAYKkAAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAACDBQBgsAAADBYAgMECAMBgAQAYLAAAgwUAgMECADBYAAAGCwAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAIMFAIDBAgAwWAAABgsAAIMFAGCwAAAMFgAABgsAwGABABgsAAAMFgCAwQIAMFgAAAYLAACDBQBgsAAADBYAAAYLAMBgAQAYLAAADBYAgMECADBYAAAGSwIAAIMFAGCwAAAMFgAABgsAwGABABgsAAAMFgCAwQIAMFgAABgsAACDBQBgsAAADBYAAAYLAMBgAQAYLAAADBYAgMECADBYAAAYLAAAgwUAYLAAADBYAAAGCwDAYAEAGCwAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAwWAAABgsAwGABAGCwAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQBgsAAADBYAgMECAMBgAQAYLAAAgwUAYLAAADBYAAAGCwDAYAEAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAGCwAAAwWAAABgsAwGABAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAMBgAQBgsAAADBYAgMECAMBgAQAYLAAAgwUAgMECAPizsIW5UHdhWEEAAAAASUVORK5CYII='
OPEN_CANDIDATES = ['Adobe Photoshop 2026', '/Applications/Adobe Photoshop 2026/Adobe Photoshop 2026.app', 'Photoshop']
OPEN_FILE = '~/Desktop/e31-newapps/seed/poster.png'
CLEAR_PATHS = ['~/Desktop/e31-newapps/out/ps-merged.psd']
BASELINE_PATH = None
BASELINE_SCRIPT = None
MARK_SPECS = []


def write_seeds():
    os.makedirs(os.path.dirname(SEED_PNG), exist_ok=True)
    with open(SEED_PNG, "wb") as handle:
        handle.write(base64.b64decode(SEED_PNG_B64))
    with open(SEED_TXT, "w", encoding="utf-8") as handle:
        handle.write("E31-ATTACH\n")


def clear_outputs():
    for rel in CLEAR_PATHS:
        path = os.path.expanduser(rel)
        if os.path.lexists(path):
            os.remove(path)


def open_app():
    target = os.path.expanduser(OPEN_FILE) if OPEN_FILE else None
    errors = []
    for name in OPEN_CANDIDATES:
        cmd = ["open", "-a", name]
        if target:
            cmd.append(target)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            return name, errors
        errors.append({"name": name, "code": proc.returncode, "stderr": (proc.stderr or "")[:400]})
    return None, errors


def write_marks():
    import secrets
    import string
    alphabet = string.ascii_uppercase + string.digits
    written = {}
    for spec in MARK_SPECS:
        path = os.path.expanduser(spec["path"])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        token = spec["prefix"] + "".join(secrets.choice(alphabet) for _ in range(6))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(token + "\n")
        written[spec["path"]] = token
    return written


def write_flag_baseline():
    if not BASELINE_SCRIPT:
        return
    path = os.path.expanduser(BASELINE_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = "unknown\n"
    try:
        proc = subprocess.run(["osascript", "-"], input=BASELINE_SCRIPT, capture_output=True, text=True, timeout=40)
        text = (proc.stdout or "").strip()
        if proc.returncode == 0 and text.startswith("flagged="):
            body = text + "\n"
    except Exception:
        body = "unknown\n"
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)


class Setup(BaseSetup):
    def run(self, context):
        write_seeds()
        clear_outputs()
        marks = write_marks()
        opened, errors = open_app()
        if opened is None:
            sys.stderr.write("open failed\n")
            return {"status": "failed", "state": {"errors": errors, "marks": marks}}
        time.sleep(2)
        write_flag_baseline()
        return {"status": "completed", "state": {"opened": opened, "marks": marks}}
