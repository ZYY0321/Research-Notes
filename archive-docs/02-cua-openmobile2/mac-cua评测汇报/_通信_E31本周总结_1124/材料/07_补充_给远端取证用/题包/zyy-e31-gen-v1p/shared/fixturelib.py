"""Host-side fixture builders for the machine gate.

No subprocess, no osascript, no GUI. Selftests import this module; the guest task does not.
"""
from __future__ import annotations

import os
from pathlib import Path

import e31_grade
import e31_grade_ext

PATH_KEYS = {"path", "baseline_path", "skip_path", "contains_file"}


def retarget(params, root):
    """Point every grader path at a file name inside root. Does not touch the real Desktop."""
    root = Path(root)

    def one(value):
        return str(root / Path(os.path.expanduser(value)).name)

    def walk(obj):
        if isinstance(obj, dict):
            return {key: one(val) if key in PATH_KEYS and isinstance(val, str) else walk(val) for key, val in obj.items()}
        if isinstance(obj, list):
            return [walk(item) for item in obj]
        return obj

    return walk(params)


def write(path, data):
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if isinstance(data, (bytes, bytearray)) else "w"
    with open(path, mode) as handle:
        handle.write(data)


def remove(path):
    path = os.path.expanduser(path)
    if os.path.lexists(path):
        os.remove(path)


def _maybe_stamp(data, stamp):
    if stamp:
        return e31_grade_ext.stamp_png_text(data, "Software", "Adobe Photoshop")
    return data


def solid(width, height, rgb, stamp=False, rgba=False, alpha=255):
    if rgba:
        pixel = bytes((rgb[0], rgb[1], rgb[2], alpha))
        data = e31_grade_ext.encode_png_rgba(width, height, pixel * (width * height))
    else:
        data = e31_grade.encode_png(width, height, e31_grade.solid_rgb(width, height, tuple(rgb)))
    return _maybe_stamp(data, stamp)


def two_color(width, height, left, right, stamp=False, rgba=False, alpha=255):
    if rgba:
        buf = bytearray()
        for _y in range(height):
            for x in range(width):
                color = left if x < max(width // 2, 1) else right
                buf.extend((color[0], color[1], color[2], alpha))
        data = e31_grade_ext.encode_png_rgba(width, height, bytes(buf))
    else:
        buf = bytearray()
        for _y in range(height):
            for x in range(width):
                buf.extend(left if x < max(width // 2, 1) else right)
        data = e31_grade.encode_png(width, height, bytes(buf))
    return _maybe_stamp(data, stamp)


def case(name, params, expect):
    got = e31_grade_ext.grade(params)
    score = got["score"]
    reason = (got.get("details") or {}).get("reason")
    return {"class": name, "score": score, "expect": expect, "ok": score == expect, "reason": reason}
