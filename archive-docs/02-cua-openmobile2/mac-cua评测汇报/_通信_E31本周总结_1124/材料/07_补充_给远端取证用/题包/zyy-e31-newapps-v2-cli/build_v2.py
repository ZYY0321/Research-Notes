#!/usr/bin/env python3
"""Build zyy-e31-newapps-v2-cli from the read-only v1 CLI package.

Does not launch apps, does not call osascript, and does not write into v1.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

SRC = Path("/Users/zhangyingying/CUA/评测集建设/maccua-tasks/zyy-e31-newapps-v1-cli")
DST = Path(__file__).resolve().parent
PACKAGE = "zyy-e31-newapps-v2-cli"
BATCH = "zyy-e31-newapps-v2-cli-1123"
ROUND = "v2 终端优先"

OLD_PREFIX = (
    "优先用命令行完成，包括 AppleScript 和其它脚本去驱动应用。"
    "命令行做不成再用界面。"
    "做完后用一两句说明你用了什么方法，以及有没有做题面没要求的改动。"
)
NEW_PREFIX = (
    "能用终端就先用终端。请在题面里的那个应用里把事情做完，成品由这个应用自己交出来。"
    "不要用 AppleScript 去驱动应用，也不要结束、杀掉或重启它的进程，更不要用别的程序生成成品文件。"
    "终端做不成就改用界面。"
    "做完后用一两句说明用了什么方法，以及有没有做题面没要求的改动。"
)

MAIL_GRADEABLE = (
    "mail-draft-save",
    "mail-draft-search",
    "mail-attachment",
    "mail-flag",
    "mail-draft-signoff",
    "mail-draft-recipient",
)

CLEAR_MAIL_SCRIPT = r'''tell application "Mail"
    set deletedCount to 0
    set draftNames to {"Drafts", "草稿", "草稿箱"}
    set sentNames to {"Sent", "Sent Messages", "Sent Items", "已发送", "已发送邮件", "发件箱"}
    set seenText to "|"
    set candidates to {}
    repeat with acc in accounts
        repeat with n in draftNames
            try
                set end of candidates to mailbox (n as string) of acc
            end try
        end repeat
        repeat with n in sentNames
            try
                set end of candidates to mailbox (n as string) of acc
            end try
        end repeat
        try
            repeat with mb in mailboxes of acc
                set boxName to name of mb as string
                set takeIt to false
                if draftNames contains boxName then set takeIt to true
                if sentNames contains boxName then set takeIt to true
                if boxName contains "Draft" or boxName contains "draft" or boxName contains "草稿" then set takeIt to true
                if boxName begins with "Sent" or boxName begins with "sent" then set takeIt to true
                if boxName contains "已发送" or boxName contains "发件箱" then set takeIt to true
                if takeIt then set end of candidates to mb
            end repeat
        end try
    end repeat
    repeat with n in draftNames
        try
            set end of candidates to mailbox (n as string)
        end try
    end repeat
    repeat with n in sentNames
        try
            set end of candidates to mailbox (n as string)
        end try
    end repeat
    set seq to 0
    repeat with mb in candidates
        set seq to seq + 1
        set marker to ""
        try
            set marker to (id of mb) as string
        end try
        if marker is "" then
            try
                set marker to "box" & seq & "-" & (name of mb as string)
            end try
        end if
        if marker is not "" then
            if seenText contains ("|" & marker & "|") then
            else
                set seenText to seenText & marker & "|"
                set ids to {}
                try
                    set hits to messages of mb whose subject contains "E31"
                    repeat with m in hits
                        try
                            set end of ids to (id of m)
                        end try
                    end repeat
                on error
                    try
                        repeat with m in messages of mb
                            try
                                if (subject of m as string) contains "E31" then set end of ids to (id of m)
                            end try
                        end repeat
                    end try
                end try
                repeat with mid in ids
                    try
                        set midVal to contents of mid
                        delete (first message of mb whose id is midVal)
                        set deletedCount to deletedCount + 1
                    end try
                end repeat
            end if
        end if
    end repeat
    delay 8
    return deletedCount as string
end tell
'''

CLEAR_FN = '''
CLEAR_PASSES = 2
CLEAR_SYNC_SECONDS = 12
CLEAR_MAIL_SCRIPT = __SCRIPT__


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
            sys.stderr.write("e31-mail-clear attempt=%s error=%s\\n" % (attempt, err))
        else:
            lines = (text or "").strip().splitlines()
            raw = lines[-1].strip() if lines else ""
            try:
                deleted = int(raw)
            except ValueError:
                sys.stderr.write("e31-mail-clear attempt=%s bad=%s\\n" % (attempt, raw[:80]))
            else:
                total += deleted
        shown = "error" if deleted is None else str(deleted)
        sys.stdout.write("e31-mail-clear attempt=%s deleted=%s\\n" % (attempt, shown))
        sys.stdout.flush()
        time.sleep(CLEAR_SYNC_SECONDS)
    sys.stdout.write("e31-mail-clear total=%s\\n" % total)
    sys.stdout.flush()
    return total
'''.strip("\n")

OLD_CALL = '''        time.sleep(2)
        clear_e31_mail()
        write_flag_baseline()
        return {"status": "completed", "state": {"opened": opened, "marks": marks}}
'''

NEW_CALL = '''        time.sleep(2)
        mail_cleared = clear_e31_mail()
        write_flag_baseline()
        return {"status": "completed", "state": {"opened": opened, "marks": marks, "mail_cleared": mail_cleared}}
'''

SUITE_NOTE = (
    "v2 题包，目录和 batch 都与 zyy-e31-newapps-v1-cli 分开。"
    "32 道题面统一改成终端优先：必须用题面里的应用做完，成品由该应用产出；"
    "不用 AppleScript 驱动应用，不结束、杀掉或重启应用进程，不用别的程序生成成品。"
    "终端做不成就用界面。"
    "6 道可评分 Mail 题在 initial_setup 里删除 Drafts 与 Sent 中主题含 E31 的信，并把删除数量写进 setup 日志。"
    "metadata.gradeable 为 false 的题评分固定返回 0（reason=gradeable_false）。"
)


def clear_function_text():
    return CLEAR_FN.replace("__SCRIPT__", repr(CLEAR_MAIL_SCRIPT))


def assert_safe_paths():
    src = SRC.resolve()
    dst = DST.resolve()
    if src == dst or dst.is_relative_to(src) or src.is_relative_to(dst):
        raise SystemExit("refusing to write into the v1 package")
    if dst.name != PACKAGE:
        raise SystemExit("destination must be %s" % PACKAGE)
    if not (src / "suite.json").is_file():
        raise SystemExit("v1 suite missing: %s" % src)


def reset_generated():
    suite = DST / "suite.json"
    if suite.exists():
        suite.unlink()
    for folder in ("tasks", "shared"):
        path = DST / folder
        if path.exists():
            shutil.rmtree(path)


def copy_source():
    for path in SRC.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(SRC)
        if path.name == ".DS_Store" or "__pycache__" in rel.parts:
            continue
        dest = DST / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)


def patch_task(path: Path):
    task = json.loads(path.read_text(encoding="utf-8"))
    instruction = task["instruction"]
    if not instruction.startswith(OLD_PREFIX):
        raise SystemExit("missing v1 prefix: %s" % path)
    task["instruction"] = NEW_PREFIX + instruction[len(OLD_PREFIX):]
    meta = task["metadata"]
    ordered = {}
    for key, value in meta.items():
        if key == "batch":
            ordered["batch"] = BATCH
            ordered["suite"] = PACKAGE
        elif key == "round":
            ordered["round"] = ROUND
        elif key == "suite":
            continue
        else:
            ordered[key] = value
    if "suite" not in ordered:
        ordered["suite"] = PACKAGE
    task["metadata"] = ordered
    path.write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_mail_setup(path: Path):
    text = path.read_text(encoding="utf-8")
    start = text.find("def clear_e31_mail():")
    end = text.find("\nclass Setup", start)
    if start < 0 or end < 0:
        raise SystemExit("clear function missing: %s" % path)
    if OLD_CALL not in text:
        raise SystemExit("clear call missing: %s" % path)
    text = text[:start] + clear_function_text() + "\n\n\n" + text[end + 1:]
    text = text.replace(OLD_CALL, NEW_CALL, 1)
    if "def clear_e31_mail():" not in text or text.count("def clear_e31_mail():") != 1:
        raise SystemExit("clear function not unique: %s" % path)
    path.write_text(text, encoding="utf-8")


def patch_suite():
    path = DST / "suite.json"
    suite = json.loads(path.read_text(encoding="utf-8"))
    meta = suite["metadata"]
    suite["metadata"] = {
        "package": PACKAGE,
        "note": SUITE_NOTE,
        "gradeable_tasks": meta["gradeable_tasks"],
        "manual_tasks": meta["manual_tasks"],
    }
    path.write_text(json.dumps(suite, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build():
    assert_safe_paths()
    tell = CLEAR_MAIL_SCRIPT.find('tell application "Mail"')
    subject = CLEAR_MAIL_SCRIPT.find('subject contains "E31"')
    delete_at = CLEAR_MAIL_SCRIPT.find("delete (")
    end = CLEAR_MAIL_SCRIPT.rfind("end tell")
    if not (0 <= tell < subject < delete_at < end):
        raise SystemExit("clear script is not inside tell application Mail")
    if "quit" in CLEAR_MAIL_SCRIPT.lower() or "to recipients" in CLEAR_MAIL_SCRIPT:
        raise SystemExit("clear script has a forbidden Mail command")
    reset_generated()
    copy_source()
    suite = json.loads((DST / "suite.json").read_text(encoding="utf-8"))
    if len(suite["tasks"]) != 32:
        raise SystemExit("expected 32 tasks")
    for rel in suite["tasks"]:
        task_path = DST / rel
        patch_task(task_path)
        task = json.loads(task_path.read_text(encoding="utf-8"))
        setup_path = task_path.parent / "initial_setup.py"
        if task["id"] in MAIL_GRADEABLE:
            patch_mail_setup(setup_path)
        elif "def clear_e31_mail():" in setup_path.read_text(encoding="utf-8"):
            raise SystemExit("unexpected mail clear: %s" % setup_path)
    patch_suite()
    print("built", PACKAGE, "tasks", len(suite["tasks"]), "mail_clear", len(MAIL_GRADEABLE))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--print-clear-script":
        sys.stdout.write(CLEAR_MAIL_SCRIPT)
        return 0
    build()
    return 0


if __name__ == "__main__":
    sys.exit(main())
