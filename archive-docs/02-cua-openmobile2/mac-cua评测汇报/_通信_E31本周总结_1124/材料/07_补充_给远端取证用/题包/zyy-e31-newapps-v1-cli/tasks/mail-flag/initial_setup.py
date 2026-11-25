import base64, os, subprocess, sys, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED_PNG = os.path.expanduser("~/Desktop/e31-newapps/seed/poster.png")
SEED_TXT = os.path.expanduser("~/Desktop/e31-newapps/seed/attach-note.txt")
SEED_PNG_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAyAAAAJYCAIAAAAVFBUnAAAI0klEQVR42u3WMQ0AAAgEsfeEJzzhFhOEqUkV3HSpHgAADkUCAACDBQBgsAAADBYAAAYLAMBgAQAYLAAADBYAgMECADBYAAAYLAAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAwWAAABgsAwGABABgsAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQBgsAAADBYAgMECADBYAAAYLAAAgwUAYLAAADBYAAAGCwDAYAEAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAGCwAAAwWAAABgsAwGABAGCwAAAMFgCAwQIAwGABABgsAACDBQBgsAAAMFgAAAYLAMBgAQBgsAAADBYAgMECAMBgAQAYLAAAgwUAgMECADBYAAAGCwDAYAEAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAIDBAgAwWAAABgsAAIMFAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAACDBQBgsAAADBYAAAYLAMBgAQAYLAAAgwUAgMECADBYAAAGCwAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAIMFAIDBAgAwWAAABgsAAIMFAGCwAAAMFgAABgsAwGABABgsAAAMFgCAwQIAMFgAAAYLAACDBQBgsAAADBYAAAYLAMBgAQAYLAAADBYAgMECADBYAAAYLAAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAwWAAABgsAwGABABgsAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQAYLBUAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAwWAAABgsAwGABAGCwAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQBgsAAADBYAgMECAMBgAQAYLAAAgwUAYLAAADBYAAAGCwDAYAEAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAIDBAgAwWAAABgsAwGABAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAMBgqQAAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAIDBAgAwWAAABgsAAIMFAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAACDBQBgsAAADBYAAAYLAMBgAQAYLAAAgwUAgMECADBYAAAGCwAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAAwWAIDBAgAwWAAABgsAAIMFAGCwAAAMFgAABgsAwGABABgsAAAMFgCAwQIAMFgAAAZLAgAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAMFgAABgsAwGABABgsAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQAYLAAADBYAgMECADBYAAAYLAAAgwUAYLAAADBYAAAGCwDAYAEAYLAAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAwWAAABgsAwGABAGCwAAAMFgCAwQIAwGABABgsAACDBQBgsAAAMFgAAAYLAMBgAQBgsAAADBYAgMECAMBgAQAYLAAAgwUAYLAAADBYAAAGCwDAYAEAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAIDBAgAwWAAABgsAwGABAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAACDBQBgsAAADBYAgMECAMBgAQAYLAAAgwUAgMECADBYAAAGCwAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAIMFAIDBAgAwWAAABgsAAIMFAGCwAAAMFgAABgsAwGABABgsAACDBQCAwQIAMFgAAAYLAACDBQBgsAAADBYAAAYLAMBgAQAYLAAADBYAgMECADBYAAAGCwAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAMFgAABgsAwGABABgsAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQAYLAAADBYAgMECADBYAAAYLAAAgwUAYLAAADBYAAAGCwDAYAEAGCwVAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQBgsAAADBYAgMECADBYAAAYLAAAgwUAYLAAADBYAAAGCwDAYAEAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAGCwAAAwWAAABgsAwGABAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAMBgAQBgsAAADBYAgMECAMBgAQAYLAAAgwUAgMECADBYAAAGCwDAYKkAAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAACDBQBgsAAADBYAgMECAMBgAQAYLAAAgwUAgMECADBYAAAGCwAAgwUAYLAAAAwWAAAGCwDAYAEAGCwAAIMFAIDBAgAwWAAABgsAAIMFAGCwAAAMFgAABgsAwGABABgsAAAMFgCAwQIAMFgAAAYLAACDBQBgsAAADBYAAAYLAMBgAQAYLAAADBYAgMECADBYAAAGSwIAAIMFAGCwAAAMFgAABgsAwGABABgsAAAMFgCAwQIAMFgAABgsAACDBQBgsAAADBYAAAYLAMBgAQAYLAAADBYAgMECADBYAAAYLAAAgwUAYLAAADBYAAAGCwDAYAEAGCwAAAwWAIDBAgAwWAAAGCwAAIMFAGCwAAAwWAAABgsAwGABAGCwAAAMFgCAwQIAMFgAABgsAACDBQBgsAAAMFgAAAYLAMBgAQBgsAAADBYAgMECAMBgAQAYLAAAgwUAYLAAADBYAAAGCwDAYAEAYLAAAAwWAIDBAgDAYAEAGCwAAIMFAGCwAAAwWAAABgsAwGABAGCwAAAMFgCAwQIAwGABABgsAACDBQCAwQIAMFgAAAYLAMBgAQBgsAAADBYAgMECAMBgAQAYLAAAgwUAgMECAPizsIW5UHdhWEEAAAAASUVORK5CYII='
OPEN_CANDIDATES = ['Mail']
OPEN_FILE = None
CLEAR_PATHS = ['~/Desktop/e31-newapps/out/mail-flag-skip.txt']
BASELINE_PATH = '~/Desktop/e31-newapps/state/mail-flag-before.txt'
BASELINE_SCRIPT = 'tell application "Mail"\n    set flaggedCount to 0\n    set inboxCount to 0\n    set inboxNames to {"INBOX", "收件箱"}\n    repeat with acc in accounts\n        repeat with n in inboxNames\n            try\n                set mb to mailbox (n as string) of acc\n                set inboxCount to inboxCount + (count of messages of mb)\n                set flaggedCount to flaggedCount + (count of (messages of mb whose flagged status is true))\n            end try\n        end repeat\n    end repeat\n    return "flagged=" & flaggedCount & linefeed & "inbox=" & inboxCount\nend tell\n'
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


def reseed_inbox():
    creds = os.environ.get("E31_MAIL_CREDS") or ""
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_mailcom.py")
    if not creds or not os.path.isfile(creds) or not os.path.isfile(script):
        return
    marker = os.path.join("/tmp", "e31-mail-marker.txt")
    proc = subprocess.run(
        [sys.executable, script, "--creds", creds, "--reset", "--scenario", "mixed-inbox", "--marker-file", marker],
        capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        sys.stderr.write("mail reseed failed\n")
def clear_e31_mail():
    script = """
tell application "Mail"
    set draftNames to {"Drafts", "草稿", "草稿箱"}
    set sentNames to {"Sent", "已发送", "发件箱", "Sent Messages"}
    repeat with acct in accounts
        repeat with mb in mailboxes of acct
            set n to name of mb as string
            set ids to {}
            if draftNames contains n then
                repeat with m in messages of mb
                    set end of ids to id of m
                end repeat
            else if sentNames contains n then
                repeat with m in messages of mb
                    set blob to subject of m as string
                    try
                        set blob to blob & (content of m as string)
                    end try
                    if blob contains "E31" then set end of ids to id of m
                end repeat
            end if
            repeat with mid in ids
                delete (first message of mb whose id is mid)
            end repeat
        end repeat
    end repeat
end tell
"""
    try:
        proc = subprocess.run(["osascript", "-"], input=script, capture_output=True, text=True, timeout=90)
        if proc.returncode != 0:
            sys.stderr.write("mail clear failed\n")
    except Exception:
        sys.stderr.write("mail clear failed\n")


class Setup(BaseSetup):
    def run(self, context):
        reseed_inbox()
        write_seeds()
        clear_outputs()
        marks = write_marks()
        opened, errors = open_app()
        if opened is None:
            sys.stderr.write("open failed\n")
            return {"status": "failed", "state": {"errors": errors, "marks": marks}}
        time.sleep(2)
        clear_e31_mail()
        write_flag_baseline()
        return {"status": "completed", "state": {"opened": opened, "marks": marks}}
