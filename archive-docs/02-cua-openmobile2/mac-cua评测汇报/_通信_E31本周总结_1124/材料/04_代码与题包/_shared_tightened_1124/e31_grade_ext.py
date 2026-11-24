"""Extra file checks, tightened 2026-11-24.

Same PARAMS as the package copy. Prefix checks now require a real body
(TIFF IFD, PDF trailer, SVG close tag, or a Photoshop PSD image section),
not the magic bytes plus leftover text.

Does not call osascript or open apps.
Import e31_grade from this same directory.
"""
from __future__ import annotations

import struct
import zlib

import e31_grade


def png_ihdr(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not png")
    if data[12:16] != b"IHDR":
        raise ValueError("ihdr")
    length = struct.unpack(">I", data[8:12])[0]
    chunk = data[16:16 + length]
    if len(chunk) < 13:
        raise ValueError("short ihdr")
    return struct.unpack(">IIBBBBB", chunk[:13])


def encode_png_rgba(width, height, rgba):
    if len(rgba) != width * height * 4:
        raise ValueError("rgba length")
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)
        raw.extend(rgba[y * stride:(y + 1) * stride])
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + e31_grade._chunk(b"IHDR", ihdr)
        + e31_grade._chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + e31_grade._chunk(b"IEND", b"")
    )


def stamp_png_text(data, keyword, text):
    """Insert a tEXt chunk before IEND. The text, not the keyword, is what the signature check reads."""
    if b"IEND" not in data:
        raise ValueError("no iend")
    payload = keyword.encode("latin-1") + b"\x00" + text.encode("latin-1")
    chunk = e31_grade._chunk(b"tEXt", payload)
    pos = data.rfind(b"IEND")
    return data[:pos - 4] + chunk + data[pos - 4:]


def _prefix_bytes(value):
    if isinstance(value, str):
        return value.encode("latin-1")
    return bytes(value)


def _prefix_suffixes(prefix):
    if prefix.startswith(b"8BPS"):
        return {".psd"}
    if prefix.startswith(b"II*") or prefix.startswith(b"MM"):
        return {".tif", ".tiff"}
    if prefix.startswith(b"%PDF"):
        return {".pdf"}
    if prefix.startswith(b"<svg") or prefix.startswith(b"<?xml"):
        return {".svg"}
    return None


def prefix_body_ok(prefix, data):
    if prefix.startswith(b"8BPS"):
        return e31_grade.psd_layout(data) is not None
    if prefix.startswith(b"II*"):
        return e31_grade.tiff_well_formed(data)
    if prefix.startswith(b"%PDF"):
        return (
            len(data) >= 64
            and b"%%EOF" in data
            and (b"trailer" in data or b"startxref" in data)
        )
    if prefix.startswith(b"<svg"):
        return len(data) >= len(prefix) + 16 and b">" in data and b"</svg>" in data
    return len(data) >= len(prefix) + 8


def grade_prefix(params):
    path = e31_grade.expand(params["path"])
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except Exception as exc:
        return e31_grade.result(False, reason="prefix", error=type(exc).__name__, path=path)
    prefix = _prefix_bytes(params.get("prefix", ""))
    if not prefix or not data.startswith(prefix):
        return e31_grade.result(False, reason="prefix-mismatch", path=path)
    suffixes = _prefix_suffixes(prefix)
    if suffixes and not e31_grade._ext_ok(path, suffixes):
        return e31_grade.result(False, reason="extension", path=path)
    if not prefix_body_ok(prefix, data):
        return e31_grade.result(False, reason="prefix-structure", path=path, size=len(data))
    return e31_grade.result(True, reason="ok", path=path, size=len(data))


def _check_color_type(params):
    if params.get("kind") != "png" or params.get("color_type") is None:
        return None
    try:
        path, data = e31_grade._read(params["path"])
    except Exception as exc:
        return e31_grade.result(False, reason="png", error=type(exc).__name__, path=e31_grade.expand(params["path"]))
    try:
        color_type = png_ihdr(data)[3]
    except Exception as exc:
        return e31_grade.result(False, reason="png", error=type(exc).__name__, path=path)
    if color_type != params["color_type"]:
        return e31_grade.result(False, reason="color-type", color_type=color_type, expect=params["color_type"], path=path)
    return None


def grade(params):
    kind = params.get("kind")
    note = params.get("grade_note")
    if kind == "all":
        parts = [grade(check) for check in params.get("checks") or []]
        ok = bool(parts) and all(part["score"] == 1 for part in parts)
        reasons = [part["details"].get("reason") for part in parts]
        if not ok and "no_app_signature" in reasons:
            reason = "no_app_signature"
        elif not ok and "color-type" in reasons:
            reason = "color-type"
        else:
            reason = "ok" if ok else "all"
        out = e31_grade.result(ok, reason=reason, parts=[part["details"] for part in parts])
    elif kind == "png_rgba":
        forwarded = dict(params)
        forwarded["kind"] = "png"
        forwarded["color_type"] = 6
        out = grade(forwarded)
    elif kind == "prefix":
        out = grade_prefix(params)
    else:
        rejected = _check_color_type(params)
        out = rejected if rejected is not None else e31_grade.grade(params)
    if note and "grade_note" not in out.get("details", {}):
        out["details"]["grade_note"] = note
    return out
