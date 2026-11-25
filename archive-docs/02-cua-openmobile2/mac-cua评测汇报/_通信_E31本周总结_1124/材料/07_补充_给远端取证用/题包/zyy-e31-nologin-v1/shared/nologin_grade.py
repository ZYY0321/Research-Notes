"""Graders for zyy-e31-nologin-v1.

File checks look at app-native bytes. App-state checks read a canned dump in
selftest, and otherwise ask the app through osascript. A desktop text file is
not an app state.
"""
from __future__ import annotations

import datetime
import os
import re
import subprocess
import zlib

CODEPAGES = {936: "gbk", 950: "big5", 932: "shift_jis", 65001: "utf-8", 1252: "cp1252"}
RTF_DEST = {
    "fonttbl", "colortbl", "stylesheet", "info", "pict", "object", "datastore",
    "themedata", "expandedcolortbl", "rsidtbl", "generator",
}


def result(ok, **details):
    return {"status": "graded", "score": 1 if ok else 0, "details": details}


def expand(path):
    return os.path.expanduser(os.fspath(path))


def read_first(path):
    with open(expand(path), encoding="utf-8") as handle:
        line = handle.readline()
    return line.strip()


def next_day(iso):
    year, month, day = (int(part) for part in iso.split("-"))
    return (datetime.date(year, month, day) + datetime.timedelta(days=1)).isoformat()


def subst(value, ctx):
    if not isinstance(value, str):
        return value
    for key, item in ctx.items():
        value = value.replace("{" + key + "}", item)
    return value


def rtf_text(data):
    raw = data.decode("latin1", "replace")
    found = re.search(r"\\ansicpg(\d+)", raw)
    encoding = CODEPAGES.get(int(found.group(1)) if found else 1252, "latin1")
    out = []
    pending = bytearray()
    skip = [False]
    uc = 1
    index = 0
    length = len(raw)

    def flush():
        if pending and not skip[-1]:
            out.append(pending.decode(encoding, "replace"))
        pending.clear()

    def add(text):
        flush()
        if text and not skip[-1]:
            out.append(text)

    while index < length:
        char = raw[index]
        if char == "{":
            flush()
            skip.append(skip[-1])
            index += 1
            if raw.startswith("\\*", index):
                skip[-1] = True
            continue
        if char == "}":
            flush()
            if len(skip) > 1:
                skip.pop()
            index += 1
            continue
        if char == "\\":
            if index + 1 < length and raw[index + 1] in "\\{}":
                add(raw[index + 1])
                index += 2
                continue
            if index + 1 < length and raw[index + 1] in "\n\r":
                add("\n")
                index += 2
                if index < length and raw[index - 1] == "\r" and raw[index] == "\n":
                    index += 1
                continue
            if raw.startswith("\\'", index) and index + 4 <= length:
                try:
                    pending.append(int(raw[index + 2:index + 4], 16))
                except ValueError:
                    pass
                index += 4
                continue
            flush()
            cursor = index + 1
            if cursor < length and raw[cursor] == "*":
                cursor += 1
            start = cursor
            while cursor < length and raw[cursor].isalpha():
                cursor += 1
            word = raw[start:cursor]
            arg_at = cursor
            sign = ""
            if arg_at < length and raw[arg_at] == "-":
                sign = "-"
                arg_at += 1
            digits = arg_at
            while digits < length and raw[digits].isdigit():
                digits += 1
            arg = (sign + raw[arg_at:digits]) if digits > arg_at else ""
            if digits < length and raw[digits] == " ":
                digits += 1
            if word in RTF_DEST:
                skip[-1] = True
            if word == "uc" and arg:
                try:
                    uc = int(arg)
                except ValueError:
                    pass
            if word == "u" and arg and not skip[-1]:
                try:
                    code = int(arg)
                    if code < 0:
                        code += 65536
                    out.append(chr(code))
                except ValueError:
                    pass
                skipped = 0
                while skipped < max(uc, 0) and digits < length:
                    if raw.startswith("\\'", digits):
                        digits += 4
                        skipped += 1
                    elif raw[digits] in "\\{}\r\n":
                        break
                    else:
                        digits += 1
                        skipped += 1
                index = digits
                continue
            if word in ("par", "line") and not skip[-1]:
                out.append("\n")
            index = digits
            continue
        if char in "\r\n":
            index += 1
            continue
        add(char)
        index += 1
    flush()
    return "".join(out)


def textedit_signature(data):
    return (
        data.startswith(b"{\\rtf1")
        and b"\\cocoartf" in data
        and b"\\viewkind0" in data
        and b"\\margl1440" in data
    )


def marker_is_bold(data, marker):
    text = data.decode("latin1", "replace")
    at = text.find(marker)
    if at < 0:
        return False
    toggles = list(re.finditer(r"\\b0(?![0-9])|\\b(?![a-zA-Z0-9])", text[:at]))
    if not toggles:
        return False
    return toggles[-1].group(0) == "\\b"


def load_file(path):
    path = expand(path)
    if not os.path.isfile(path) or os.path.islink(path):
        raise FileNotFoundError(path)
    with open(path, "rb") as handle:
        return path, handle.read()


def problem_result(problems, **details):
    return result(not problems, reason="ok" if not problems else "mismatch", problems=problems, **details)


def check_keep(params, ctx):
    if not params.get("keep_path"):
        return None
    try:
        _path, data = load_file(params["keep_path"])
    except OSError:
        return "keep-missing"
    text = data.decode("utf-8", "replace")
    if params.get("keep_contains"):
        needle = subst(params["keep_contains"], ctx).encode("utf-8")
        if needle not in data and subst(params["keep_contains"], ctx) not in text:
            return "keep-contains"
    if params.get("keep_lacks"):
        needle = subst(params["keep_lacks"], ctx)
        if needle and (needle.encode("utf-8") in data or needle in text):
            return "keep-lacks"
    return None


def grade_textedit(params, ctx):
    problems = []
    try:
        path, data = load_file(params["path"])
    except OSError as exc:
        return result(False, reason="missing", error=type(exc).__name__, path=expand(params["path"]))
    if not textedit_signature(data):
        problems.append("signature")
    text = rtf_text(data).strip()
    exact = params.get("exact")
    if exact is not None and text != subst(exact, ctx):
        problems.append("exact")
    needles = [subst(item, ctx) for item in params.get("contains") or []]
    for needle in needles:
        if needle not in text:
            problems.append("contains")
    if params.get("order"):
        cursor = 0
        for needle in needles:
            found = text.find(needle, cursor)
            if found < 0:
                problems.append("order")
                break
            cursor = found + len(needle)
    for item in params.get("forbids") or []:
        if subst(item, ctx) in text:
            problems.append("forbids")
    if params.get("bold"):
        bold_of = subst(params.get("bold_text") or ctx["marker"], ctx)
        if not marker_is_bold(data, bold_of):
            problems.append("bold")
    kept = check_keep(params, ctx)
    if kept:
        problems.append(kept)
    return problem_result(problems, path=path, text=text[:240])


def inflate_streams(data):
    found = []
    index = 0
    while True:
        start = data.find(b"stream", index)
        if start < 0:
            break
        cursor = start + 6
        if data[cursor:cursor + 2] == b"\r\n":
            cursor += 2
        elif cursor < len(data) and data[cursor:cursor + 1] == b"\n":
            cursor += 1
        end = data.find(b"endstream", cursor)
        if end < 0:
            break
        chunk = data[cursor:end].strip(b"\r\n")
        try:
            found.append(zlib.decompress(chunk))
        except zlib.error:
            pass
        index = end + 9
    return found


def has_blob(data, blob):
    if blob in data:
        return True
    return any(blob in part for part in inflate_streams(data))


def is_pdf(data):
    return data.startswith(b"%PDF-") and b"%%EOF" in data and b"/Page" in data


def boxes(data, name):
    pattern = rb"/" + name.encode("ascii") + rb"\s*\[\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s*\]"
    return [tuple(float(item) for item in match.groups()) for match in re.finditer(pattern, data)]


def grade_preview(params, ctx):
    problems = []
    try:
        path, data = load_file(params["path"])
    except OSError as exc:
        return result(False, reason="missing", error=type(exc).__name__, path=expand(params["path"]))
    if not is_pdf(data):
        problems.append("pdf")
        return problem_result(problems, path=path)
    token = ctx.get("seed") or ""
    if token and not has_blob(data, token.encode("ascii")):
        problems.append("seed-token")
    mode = params.get("mode")
    marker = ctx["marker"]
    if mode == "freetext":
        if b"/Subtype /FreeText" not in data and b"/Subtype/FreeText" not in data:
            problems.append("freetext")
        if marker.encode("ascii") not in data:
            problems.append("marker")
        if b"/RC" not in data and b"1999/xhtml" not in data:
            problems.append("rc")
        if b"/DA" not in data and b"/DS" not in data:
            problems.append("da")
        if b"/Annots" not in data:
            problems.append("annots")
    elif mode == "sticky":
        if not re.search(br"/Subtype\s*/Text(?![A-Za-z])", data):
            problems.append("sticky")
        if b"/Comment" not in data:
            problems.append("comment")
        if ("(%s)" % marker).encode("ascii") not in data and marker.encode("ascii") not in data:
            problems.append("marker")
        if b"/Annots" not in data:
            problems.append("annots")
    elif mode == "highlight":
        if b"/Highlight" not in data or b"/QuadPoints" not in data:
            problems.append("highlight")
        if b"/Annots" not in data:
            problems.append("annots")
    elif mode == "rotate":
        angle = str(params.get("angle", 90)).encode("ascii")
        if not re.search(br"/Rotate\s+" + angle + br"(?!\d)", data):
            problems.append("rotate")
    elif mode == "crop":
        medias = boxes(data, "MediaBox")
        crops = boxes(data, "CropBox")
        if not any(box[3] - box[1] >= 700 and box[2] - box[0] >= 500 for box in medias):
            problems.append("mediabox")
        if not any(300 <= box[3] - box[1] <= 460 and box[2] - box[0] >= 500 and box[3] >= 740 for box in crops):
            problems.append("cropbox")
    else:
        problems.append("mode")
    kept = check_keep(params, ctx)
    if kept:
        problems.append(kept)
    return problem_result(problems, path=path, mode=mode)


def grade_alias(params, ctx):
    path = expand(params["path"])
    if os.path.islink(path) or not os.path.isfile(path):
        return result(False, reason="missing" if not os.path.lexists(path) else "symlink", path=path)
    with open(path, "rb") as handle:
        data = handle.read()
    target = subst(params["target_name"], ctx).encode("utf-8")
    problems = []
    if not data.startswith(b"book\x00\x00\x00\x00"):
        problems.append("bookmark")
    if target not in data and target.decode().encode("utf-16-be") not in data:
        problems.append("target")
    return problem_result(problems, path=path)


def grade_view(params, ctx):
    del ctx
    try:
        path, data = load_file(params["path"])
    except OSError as exc:
        return result(False, reason="missing", error=type(exc).__name__, path=expand(params["path"]))
    code = params["view"].encode("ascii")
    if not data.startswith(b"\x00\x00\x00\x01Bud1"):
        return result(False, reason="not-dsstore", path=path)
    start = 0
    while True:
        at = data.find(b"vstl", start)
        if at < 0:
            return result(False, reason="view", path=path, view=params["view"])
        if code in data[at:at + 24]:
            return result(True, reason="ok", path=path, view=params["view"])
        start = at + 4


def parse_records(text):
    records = []
    current = {}
    for line in (text or "").splitlines():
        if line.strip() == "----":
            if current:
                records.append(current)
            current = {}
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            current[key.strip()] = value
    if current:
        records.append(current)
    return records


def record_ok(record, wheres, ctx):
    for clause in wheres:
        value = record.get(clause["field"], "")
        if "eq" in clause and value != subst(clause["eq"], ctx):
            return False
        if "has" in clause and subst(clause["has"], ctx) not in value:
            return False
        if "prefix" in clause and not value.startswith(subst(clause["prefix"], ctx)):
            return False
        if "gte" in clause or "lte" in clause:
            try:
                number = int(str(value).strip())
            except ValueError:
                return False
            if "gte" in clause and number < clause["gte"]:
                return False
            if "lte" in clause and number > clause["lte"]:
                return False
    return bool(wheres)


def run_osascript(script, timeout=90):
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


NOTES_SCRIPT = r'''
on flatten(t)
    set AppleScript's text item delimiters to {return, linefeed}
    set parts to text items of (t as string)
    set AppleScript's text item delimiters to " "
    return parts as string
end flatten

on emitNote(n)
    set nm to ""
    set tx to ""
    set bd to ""
    set fol to ""
    set att to ""
    try
        set nm to my flatten(name of n)
    end try
    try
        set tx to my flatten(plaintext of n)
    end try
    try
        set bd to my flatten(body of n)
    end try
    try
        set fol to my flatten(name of container of n)
    end try
    try
        repeat with a in (attachments of n)
            try
                set att to att & (name of a as string) & ","
            end try
        end repeat
    end try
    if nm contains "E31" or tx contains "E31" or fol contains "E31" or att contains "E31" or bd contains "E31" then
        return "KIND=note" & linefeed & "NAME=" & nm & linefeed & "PLAIN=" & tx & linefeed & "BODY=" & bd & linefeed & "FOLDER=" & fol & linefeed & "ATTACH=" & att & linefeed & "----" & linefeed
    end if
    return ""
end emitNote

set blob to ""
tell application "Notes"
    set allNotes to notes
    set total to count of allNotes
    if total > 500 then set total to 500
    repeat with i from 1 to total
        set blob to blob & my emitNote(item i of allNotes)
    end repeat
end tell
return blob
'''

REMINDERS_SCRIPT = r'''
on flatten(t)
    set AppleScript's text item delimiters to {return, linefeed}
    set parts to text items of (t as string)
    set AppleScript's text item delimiters to " "
    return parts as string
end flatten

on pad(n)
    if n < 10 then return "0" & (n as string)
    return n as string
end pad

on iso(d)
    if d is missing value then return ""
    set y to year of d as integer
    set m to month of d as integer
    set da to day of d as integer
    set hh to hours of d as integer
    set mm to minutes of d as integer
    return (y as string) & "-" & my pad(m) & "-" & my pad(da) & "T" & my pad(hh) & ":" & my pad(mm)
end iso

set blob to ""
tell application "Reminders"
    set allItems to reminders
    set total to count of allItems
    if total > 500 then set total to 500
    repeat with i from 1 to total
        set r to item i of allItems
        set nm to ""
        set bd to ""
        set lst to ""
        set doneText to "false"
        set flagText to "false"
        set dueText to ""
        set pri to "0"
        try
            set nm to my flatten(name of r)
        end try
        try
            set bd to my flatten(body of r)
        end try
        try
            set lst to my flatten(name of container of r)
        end try
        if nm contains "E31" or bd contains "E31" or lst contains "E31" then
            try
                if completed of r then set doneText to "true"
            end try
            try
                if flagged of r then set flagText to "true"
            end try
            try
                set pri to priority of r as string
            end try
            try
                set dueText to my iso(due date of r)
            end try
            set blob to blob & "KIND=reminder" & linefeed & "NAME=" & nm & linefeed & "BODY=" & bd & linefeed & "LIST=" & lst & linefeed & "COMPLETED=" & doneText & linefeed & "FLAGGED=" & flagText & linefeed & "PRIORITY=" & pri & linefeed & "DUE=" & dueText & linefeed & "----" & linefeed
        end if
    end repeat
end tell
return blob
'''

CALENDAR_SCRIPT = r'''
on flatten(t)
    set AppleScript's text item delimiters to {return, linefeed}
    set parts to text items of (t as string)
    set AppleScript's text item delimiters to " "
    return parts as string
end flatten

on pad(n)
    if n < 10 then return "0" & (n as string)
    return n as string
end pad

on iso(d)
    if d is missing value then return ""
    set y to year of d as integer
    set m to month of d as integer
    set da to day of d as integer
    set hh to hours of d as integer
    set mm to minutes of d as integer
    return (y as string) & "-" & my pad(m) & "-" & my pad(da) & "T" & my pad(hh) & ":" & my pad(mm)
end iso

set blob to ""
tell application "Calendar"
    repeat with cal in calendars
        set evs to {}
        try
            set evs to (events of cal whose summary contains "E31")
        end try
        repeat with ev in evs
            set sm to ""
            set loc to ""
            set desc to ""
            set st to ""
            set en to ""
            set allDay to "false"
            set alarmText to ""
            try
                set sm to my flatten(summary of ev)
            end try
            try
                set loc to my flatten(location of ev)
            end try
            try
                set desc to my flatten(description of ev)
            end try
            try
                set st to my iso(start date of ev)
            end try
            try
                set en to my iso(end date of ev)
            end try
            try
                if allday event of ev then set allDay to "true"
            end try
            try
                set alarmText to (trigger interval of first display alarm of ev) as string
            end try
            set blob to blob & "KIND=event" & linefeed & "SUMMARY=" & sm & linefeed & "LOCATION=" & loc & linefeed & "DESCRIPTION=" & desc & linefeed & "START=" & st & linefeed & "END=" & en & linefeed & "ALLDAY=" & allDay & linefeed & "ALARM=" & alarmText & linefeed & "----" & linefeed
        end repeat
    end repeat
end tell
return blob
'''

PHOTOS_SCRIPT = r'''
on flatten(t)
    set AppleScript's text item delimiters to {return, linefeed}
    set parts to text items of (t as string)
    set AppleScript's text item delimiters to " "
    return parts as string
end flatten

set blob to ""
tell application "Photos"
    try
        repeat with a in albums
            try
                set nm to my flatten(name of a)
                if nm contains "E31" then
                    set blob to blob & "KIND=album" & linefeed & "NAME=" & nm & linefeed & "----" & linefeed
                end if
            end try
        end repeat
    end try
    try
        repeat with f in folders
            try
                set nm to my flatten(name of f)
                if nm contains "E31" then
                    set blob to blob & "KIND=folder" & linefeed & "NAME=" & nm & linefeed & "----" & linefeed
                end if
            end try
        end repeat
    end try
    set hits to {}
    try
        set hits to (media items whose filename contains "E31")
    end try
    repeat with m in hits
        set nm to ""
        set fn to ""
        set fav to "false"
        try
            set nm to my flatten(name of m)
        end try
        try
            set fn to my flatten(filename of m)
        end try
        try
            if favorite of m then set fav to "true"
        end try
        set blob to blob & "KIND=item" & linefeed & "NAME=" & nm & linefeed & "FILENAME=" & fn & linefeed & "FAVORITE=" & fav & linefeed & "----" & linefeed
    end repeat
end tell
return blob
'''

SHORTCUTS_SCRIPT = r'''
on flatten(t)
    set AppleScript's text item delimiters to {return, linefeed}
    set parts to text items of (t as string)
    set AppleScript's text item delimiters to " "
    return parts as string
end flatten

set blob to ""
tell application "Shortcuts"
    try
        repeat with f in folders
            try
                set nm to my flatten(name of f)
                if nm contains "E31" then
                    set blob to blob & "KIND=folder" & linefeed & "NAME=" & nm & linefeed & "----" & linefeed
                end if
            end try
        end repeat
    end try
    set allItems to shortcuts
    set total to count of allItems
    if total > 500 then set total to 500
    repeat with i from 1 to total
        set s to item i of allItems
        set nm to ""
        set fol to ""
        set acts to "0"
        set acc to "false"
        try
            set nm to my flatten(name of s)
        end try
        try
            set fol to my flatten(name of folder of s)
        end try
        if nm contains "E31" or fol contains "E31" then
            try
                set acts to action count of s as string
            end try
            try
                if accepts input of s then set acc to "true"
            end try
            set blob to blob & "KIND=shortcut" & linefeed & "NAME=" & nm & linefeed & "FOLDER=" & fol & linefeed & "ACTIONS=" & acts & linefeed & "ACCEPTS=" & acc & linefeed & "----" & linefeed
        end if
    end repeat
end tell
return blob
'''

SCRIPTS = {
    "notes": NOTES_SCRIPT,
    "reminders": REMINDERS_SCRIPT,
    "calendar": CALENDAR_SCRIPT,
    "photos": PHOTOS_SCRIPT,
    "shortcuts": SHORTCUTS_SCRIPT,
}


def context_from(params):
    ctx = {"marker": "", "today": "", "tomorrow": "", "seed": "", "photo": ""}
    if params.get("marker") is not None:
        ctx["marker"] = params["marker"]
    elif params.get("marker_file"):
        try:
            ctx["marker"] = read_first(params["marker_file"])
        except OSError:
            ctx["marker"] = ""
    if params.get("today") is not None:
        ctx["today"] = params["today"]
    elif params.get("today_file"):
        try:
            ctx["today"] = read_first(params["today_file"])
        except OSError:
            ctx["today"] = ""
    if ctx["today"]:
        try:
            ctx["tomorrow"] = next_day(ctx["today"])
        except ValueError:
            ctx["tomorrow"] = ""
    if params.get("seed_token") is not None:
        ctx["seed"] = params["seed_token"]
    elif params.get("seed_token_file"):
        try:
            ctx["seed"] = read_first(params["seed_token_file"])
        except OSError:
            ctx["seed"] = ""
    if params.get("photo") is not None:
        ctx["photo"] = params["photo"]
    elif params.get("photo_file"):
        try:
            ctx["photo"] = read_first(params["photo_file"])
        except OSError:
            ctx["photo"] = ""
    return ctx


def grade_app(params, ctx):
    if not ctx.get("marker"):
        return result(False, reason="marker-missing")
    if "dump" in params:
        text, err = params.get("dump") or "", None
    else:
        script = SCRIPTS.get(params.get("app"))
        if not script:
            return result(False, reason="unknown-app", app=params.get("app"))
        text, err = run_osascript(script)
    if err:
        return result(False, reason="applescript", error=err)
    wheres = params.get("where") or []
    matched = [record for record in parse_records(text) if record_ok(record, wheres, ctx)]
    return result(bool(matched), reason="ok" if matched else "app-state", records=len(parse_records(text)), app=params.get("app"))


def grade(params):
    ctx = context_from(params)
    kind = params.get("kind")
    if kind == "all":
        parts = [grade(check) for check in params.get("checks") or []]
        ok = bool(parts) and all(part["score"] == 1 for part in parts)
        out = result(ok, reason="ok" if ok else "all", parts=[part["details"] for part in parts])
    elif kind == "textedit_rtf":
        if params.get("exact") or params.get("contains") or params.get("bold"):
            if not ctx.get("marker") and ("{marker}" in str(params.get("exact")) or any("{marker}" in str(item) for item in params.get("contains") or [])):
                return result(False, reason="marker-missing")
        out = grade_textedit(params, ctx)
    elif kind == "preview_pdf":
        if not ctx.get("marker") and params.get("mode") in ("freetext", "sticky"):
            return result(False, reason="marker-missing")
        out = grade_preview(params, ctx)
    elif kind == "finder_alias":
        out = grade_alias(params, ctx)
    elif kind == "finder_view":
        out = grade_view(params, ctx)
    elif kind == "app_state":
        out = grade_app(params, ctx)
    else:
        out = result(False, reason="unknown-kind", kind=kind)
    note = params.get("grade_note")
    if note:
        out["details"]["grade_note"] = note
    return out
