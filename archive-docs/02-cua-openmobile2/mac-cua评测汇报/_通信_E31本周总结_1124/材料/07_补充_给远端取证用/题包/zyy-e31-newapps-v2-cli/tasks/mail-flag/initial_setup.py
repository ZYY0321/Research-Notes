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
CLEAR_PASSES = 2
CLEAR_SYNC_SECONDS = 12
CLEAR_MAIL_SCRIPT = 'tell application "Mail"\n    set deletedCount to 0\n    set draftNames to {"Drafts", "草稿", "草稿箱"}\n    set sentNames to {"Sent", "Sent Messages", "Sent Items", "已发送", "已发送邮件", "发件箱"}\n    set seenText to "|"\n    set candidates to {}\n    repeat with acc in accounts\n        repeat with n in draftNames\n            try\n                set end of candidates to mailbox (n as string) of acc\n            end try\n        end repeat\n        repeat with n in sentNames\n            try\n                set end of candidates to mailbox (n as string) of acc\n            end try\n        end repeat\n        try\n            repeat with mb in mailboxes of acc\n                set boxName to name of mb as string\n                set takeIt to false\n                if draftNames contains boxName then set takeIt to true\n                if sentNames contains boxName then set takeIt to true\n                if boxName contains "Draft" or boxName contains "draft" or boxName contains "草稿" then set takeIt to true\n                if boxName begins with "Sent" or boxName begins with "sent" then set takeIt to true\n                if boxName contains "已发送" or boxName contains "发件箱" then set takeIt to true\n                if takeIt then set end of candidates to mb\n            end repeat\n        end try\n    end repeat\n    repeat with n in draftNames\n        try\n            set end of candidates to mailbox (n as string)\n        end try\n    end repeat\n    repeat with n in sentNames\n        try\n            set end of candidates to mailbox (n as string)\n        end try\n    end repeat\n    set seq to 0\n    repeat with mb in candidates\n        set seq to seq + 1\n        set marker to ""\n        try\n            set marker to (id of mb) as string\n        end try\n        if marker is "" then\n            try\n                set marker to "box" & seq & "-" & (name of mb as string)\n            end try\n        end if\n        if marker is not "" then\n            if seenText contains ("|" & marker & "|") then\n            else\n                set seenText to seenText & marker & "|"\n                set ids to {}\n                try\n                    set hits to messages of mb whose subject contains "E31"\n                    repeat with m in hits\n                        try\n                            set end of ids to (id of m)\n                        end try\n                    end repeat\n                on error\n                    try\n                        repeat with m in messages of mb\n                            try\n                                if (subject of m as string) contains "E31" then set end of ids to (id of m)\n                            end try\n                        end repeat\n                    end try\n                end try\n                repeat with mid in ids\n                    try\n                        set midVal to contents of mid\n                        delete (first message of mb whose id is midVal)\n                        set deletedCount to deletedCount + 1\n                    end try\n                end repeat\n            end if\n        end if\n    end repeat\n    delay 8\n    return deletedCount as string\nend tell\n'


def run_osascript(script, timeout=60):
    try:
        proc = subprocess.run(
            ["osascript", "-"],
            input=script,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:
        return None, type(exc).__name__
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "osascript_failed").strip()
        return None, err[:300]
    return proc.stdout, None


def clear_e31_mail():
    total = 0
    for attempt in range(1, CLEAR_PASSES + 1):
        text, err = run_osascript(CLEAR_MAIL_SCRIPT, timeout=60)
        deleted = None
        if err:
            sys.stderr.write("e31-mail-clear attempt=%s error=%s\n" % (attempt, err))
        else:
            lines = (text or "").strip().splitlines()
            raw = lines[-1].strip() if lines else ""
            try:
                deleted = int(raw)
            except ValueError:
                sys.stderr.write("e31-mail-clear attempt=%s bad=%s\n" % (attempt, raw[:80]))
            else:
                total += deleted
        shown = "error" if deleted is None else str(deleted)
        sys.stdout.write("e31-mail-clear attempt=%s deleted=%s\n" % (attempt, shown))
        sys.stdout.flush()
        time.sleep(CLEAR_SYNC_SECONDS)
    sys.stdout.write("e31-mail-clear total=%s\n" % total)
    sys.stdout.flush()
    return total


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
        mail_cleared = clear_e31_mail()
        write_flag_baseline()
        return {"status": "completed", "state": {"opened": opened, "marks": marks, "mail_cleared": mail_cleared}}
