#!/usr/bin/env python3
"""Empty run scores 0 and a terminal shortcut scores 0. Does not launch apps."""
from __future__ import annotations

import ast
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "shared"), str(ROOT)]

import build_nologin as build
import nologin_grade as grade
import nologin_seed as seed

FAILURES = []
CTX = {
    "marker": "E31-AB12CD",
    "today": "2026-11-22",
    "tomorrow": "2026-11-23",
    "seed": "SEED-ZX90Q1",
    "photo": "e31-photo-E31-AB12CD.png",
}


def check(name, cond, detail=""):
    if cond:
        print("OK  ", name)
        return
    FAILURES.append(name)
    print("FAIL", name, detail)


def forbid_osascript(*_args, **_kwargs):
    raise AssertionError("selftest must not call osascript")


def fill(value, ctx):
    if not isinstance(value, str):
        return value
    for key, item in ctx.items():
        value = value.replace("{" + key + "}", item)
    return value


def textedit_rtf(body, bold=False):
    payload = body.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\\n")
    bold_on = "\\b " if bold else ""
    bold_off = "\\b0 " if bold else ""
    return (
        "{\\rtf1\\ansi\\ansicpg936\\cocoartf2870\n"
        "\\cocoatextscaling0\\cocoaplatform0{\\fonttbl\\f0\\fswiss\\fcharset0 Helvetica;}\n"
        "{\\colortbl;\\red255\\green255\\blue255;}\n"
        "{\\*\\expandedcolortbl;;}\n"
        "\\margl1440\\margr1440\\vieww11520\\viewh8400\\viewkind0\n"
        "\\pard\\tx560\\pardirnatural\\partightenfactor0\n"
        "\\f0\\fs24 " + bold_on + "\\cf0 " + payload + bold_off + "}"
    ).encode("latin1")


def textutil_rtf(body):
    payload = body.replace("\n", "\\\n")
    return (
        "{\\rtf1\\ansi\\ansicpg936\\cocoartf2870\n"
        "\\cocoatextscaling0\\cocoaplatform0{\\fonttbl\\f0\\fswiss\\fcharset0 Helvetica-Light;}\n"
        "{\\colortbl;\\red255\\green255\\blue255;}\n"
        "{\\*\\expandedcolortbl;;}\n"
        "\\pard\\tx560\\pardirnatural\\partightenfactor0\n"
        "\\f0\\fs24 \\cf0 " + payload + "\n}"
    ).encode("latin1")


def rewrite(value, root):
    if isinstance(value, str) and value.startswith("~/Desktop/e31-nologin"):
        relative = value[len("~/Desktop/e31-nologin"):].lstrip("/")
        return str(root / relative)
    if isinstance(value, dict):
        return {key: rewrite(item, root) for key, item in value.items()}
    if isinstance(value, list):
        return [rewrite(item, root) for item in value]
    return value


def plant(params, ctx):
    for key, text in (
        ("marker_file", ctx["marker"] + "\n"),
        ("today_file", ctx["today"] + "\n"),
        ("seed_token_file", ctx["seed"] + "\n"),
        ("photo_file", ctx["photo"] + "\n"),
    ):
        if params.get(key):
            seed.write_text(params[key], text)
    for check in params.get("checks") or []:
        plant(check, ctx)


def write_keep(spec, params, ctx):
    kind = spec.get("keep_file")
    path = params.get("keep_path")
    if not kind or not path:
        return
    if kind == "pdf":
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Path(path).write_bytes(seed.pdf_bytes(ctx["seed"]))
    else:
        seed.write_text(path, kind)


def dump_of(record, ctx):
    lines = []
    for key, value in record.items():
        lines.append("%s=%s" % (key, fill(str(value), ctx)))
    lines.append("----")
    return "\n".join(lines) + "\n"


def annotate(data, marker, mode, angle=None):
    if mode == "freetext":
        extra = (
            "\n6 0 obj << /Type /Annot /Subtype /FreeText /Rect [72 640 400 700] "
            "/Contents (%s) /DA (/Helv 14 Tf 0 0 1 rg) "
            "/RC (<?xml version=\"1.0\"?><body xmlns=\"http://www.w3.org/1999/xhtml\"><p>%s</p></body>) >> endobj\n"
            "/Annots [6 0 R]\n" % (marker, marker)
        )
    elif mode == "sticky":
        extra = (
            "\n6 0 obj << /Type /Annot /Subtype /Text /Name /Comment /Contents (%s) >> endobj\n"
            "/Annots [6 0 R]\n" % marker
        )
    elif mode == "highlight":
        extra = (
            "\n6 0 obj << /Type /Annot /Subtype /Highlight /QuadPoints [72 700 200 700 72 680 200 680] "
            "/Contents (%s) >> endobj\n/Annots [6 0 R]\n" % marker
        )
    elif mode == "rotate":
        needle = b"/Type /Page"
        return data.replace(needle, needle + (" /Rotate %s" % angle).encode("ascii"), 1)
    elif mode == "crop":
        needle = b"/MediaBox [0 0 612 792]"
        return data.replace(needle, needle + b" /CropBox [0 396 612 792]", 1)
    else:
        raise ValueError(mode)
    return data.replace(b"%%EOF", extra.encode("ascii") + b"%%EOF")


def stage_one(spec, root, mode, ctx):
    params = rewrite(json.loads(json.dumps(spec["params"])), root)
    plant(params, ctx)
    write_keep(spec, params, ctx)
    fixture = spec["fixture"]
    if fixture == "rtf":
        path = Path(params["path"])
        body = fill(spec.get("good_text") or "", ctx)
        if mode == "empty":
            if spec.get("empty") == "plain":
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(seed.plain_rtf(spec.get("seed_text") or ""))
        elif mode == "shortcut":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(textutil_rtf(body))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(textedit_rtf(body, bold=bool(spec.get("bold"))))
    elif fixture == "pdf":
        path = Path(params["path"])
        original = seed.pdf_bytes(ctx["seed"])
        if mode == "shortcut":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(original)
        elif mode == "good":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(annotate(original, ctx["marker"], params["mode"], params.get("angle")))
    elif fixture == "alias":
        path = Path(params["path"])
        target = params["target_name"]
        if mode == "shortcut":
            path.parent.mkdir(parents=True, exist_ok=True)
            dummy = path.parent / target
            dummy.write_text("target\n", encoding="utf-8")
            if path.is_symlink() or path.exists():
                path.unlink()
            path.symlink_to(dummy)
        elif mode == "good":
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.is_symlink() or path.exists():
                path.unlink()
            path.write_bytes(b"book\x00\x00\x00\x00mark" + b"\x00" * 16 + target.encode("ascii"))
    elif fixture == "view":
        path = Path(params["path"])
        code = params["view"].encode("ascii")
        if mode == "shortcut":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(code.decode("ascii") + "\n", encoding="utf-8")
        elif mode == "good":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"\x00\x00\x00\x01Bud1" + b"\x00" * 8 + b"vstl" + b"type" + code)
    elif fixture == "app":
        side = root / "shell-out.txt"
        if mode == "empty":
            params["dump"] = ""
        elif mode == "shortcut":
            side.write_text(ctx["marker"] + "\n", encoding="utf-8")
            params["dump"] = "exported by shell\n" + ctx["marker"] + "\n"
        else:
            params["dump"] = dump_of(spec["good_record"], ctx)
    else:
        raise ValueError(fixture)
    return params


def stage(spec, root, mode, ctx):
    if spec["fixture"] == "multi":
        checks = [stage_one(part, root, mode, ctx) for part in spec["checks"]]
        return {"kind": "all", "checks": checks, "grade_note": spec["grade_note"]}
    return stage_one(spec, root, mode, ctx)


def expect_zero(task_id, mode, scored):
    check(
        task_id + "_" + mode + "0",
        scored["score"] == 0 and scored["status"] == "graded",
        scored,
    )


def main():
    grade.run_osascript = forbid_osascript
    limit = int(os.environ.get("NOLOGIN_LIMIT", "0") or "0") or None
    specs = build.build(limit)
    suite = json.loads((ROOT / "suite.json").read_text(encoding="utf-8"))
    allowed = {"schema_version", "tasks", "smoke", "metadata"}
    check("suite_keys", set(suite) <= allowed, sorted(set(suite) - allowed))
    check("suite_count", len(suite["tasks"]) == len(specs), len(suite["tasks"]))
    check("smoke_known", set(suite["smoke"]) <= {item["id"] for item in specs})

    needles = ("pass" + "word", "pass" + "wd", "token" + "hub", "api_" + "key")
    secret_hits = []
    for path in list(ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".json", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if any(needle in text for needle in needles):
            secret_hits.append(str(path))
    check("no_secrets", not secret_hits, secret_hits)

    sample = (
        "{\\rtf1\\ansi\\ansicpg936\\cocoartf2870\n"
        "\\f0\\fs24 \\cf0 \\'c7\\'eb\\'b0\\'d1 TOKEN \\'bb\\'bb\\'b3\\'c9\\'b1\\'ea\\'bc\\'c7\n"
        "\\f1 \\\n"
        "E31-AB12CD}"
    ).encode("latin1")
    decoded = grade.rtf_text(sample)
    check("rtf_gbk", "请把" in decoded and "TOKEN" in decoded and "换成标记" in decoded and "E31-AB12CD" in decoded, decoded)

    ids = []
    for spec in specs:
        ids.append(spec["id"])
        task_path = ROOT / "tasks" / spec["id"] / "task.json"
        task = json.loads(task_path.read_text(encoding="utf-8"))
        check(spec["id"] + "_id", task["id"] == spec["id"])
        check(spec["id"] + "_login", task["metadata"]["needs_login"] is False)
        check(spec["id"] + "_instruction", len(task["instruction"]) > 40 and "命令行优先" not in task["instruction"] and "CLI" not in task["instruction"])
        ast.parse((task_path.parent / "initial_setup.py").read_text(encoding="utf-8"))
        ast.parse((task_path.parent / "evaluation.py").read_text(encoding="utf-8"))
        setup_text = (task_path.parent / "initial_setup.py").read_text(encoding="utf-8")
        check(spec["id"] + "_no_osa", "osascript" not in setup_text)
        with tempfile.TemporaryDirectory(prefix="nologin-") as directory:
            root = Path(directory)
            for mode in ("empty", "shortcut", "good"):
                scored = grade.grade(stage(spec, root, mode, dict(CTX)))
                if mode == "good":
                    check(spec["id"] + "_good1", scored["score"] == 1, scored)
                else:
                    expect_zero(spec["id"], mode, scored)
            if spec["fixture"] == "app" or spec["fixture"] == "multi":
                side = root / "shell-out.txt"
                if spec["fixture"] == "app":
                    check(spec["id"] + "_sidefile", side.is_file() and CTX["marker"] in side.read_text(encoding="utf-8"))

    check("ids_unique", len(ids) == len(set(ids)))
    check("at_least_25" if limit == 25 else "count", len(ids) == (limit or len(build.SPECS)), len(ids))

    print("---")
    if FAILURES:
        print(len(FAILURES), "failures")
        for name in FAILURES:
            print(" -", name)
        return 1
    print("all ok", len(ids))
    return 0


if __name__ == "__main__":
    sys.exit(main())
