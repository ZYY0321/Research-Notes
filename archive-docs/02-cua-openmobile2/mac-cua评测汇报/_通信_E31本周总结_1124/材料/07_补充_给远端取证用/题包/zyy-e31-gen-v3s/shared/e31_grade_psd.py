"""Stdlib readers for PSD, PDF, plist, and droplet files.

Does not import Pillow. Does not launch apps, osascript, or read a mailbox
unless the caller passes that path. Selftests pass a temporary path.
"""
from __future__ import annotations

import os
import plistlib
import re
import sqlite3
import struct

import e31_grade

LARGE_KEYS = {
    b"LMsk", b"Lr16", b"Lr32", b"Layr", b"Mt16", b"Mt32", b"Mtrn", b"Alph",
    b"FMsk", b"lnk2", b"FEid", b"FXid", b"PxSD", b"lnkE", b"cinf",
}
ADJUSTMENT_KEYS = {
    b"brit", b"levl", b"curv", b"expA", b"vibA", b"hue2", b"blnc", b"blwh",
    b"phfl", b"mixr", b"clrL", b"nvrt", b"post", b"thrs", b"grdm", b"selc",
    b"SoCo", b"GdFl", b"PtFl",
}
EFFECT_KEYS = {b"lfx2", b"lrFX", b"lfxs", b"lmfx"}
SMART_KEYS = {b"SoLd", b"SoLE", b"plLd", b"PlLd"}
ARTBOARD_KEYS = {b"artb", b"artd", b"abdd"}
BASE_CHANNELS = {0: 1, 1: 1, 2: 1, 3: 3, 4: 4, 7: 1, 8: 1, 9: 3}
KINDS = {
    "psd_adjustment",
    "psd_drop_shadow",
    "psd_smart_object",
    "psd_layer_comp",
    "psd_artboard",
    "psd_duotone",
    "psd_saved_selection",
    "psd_frame_animation",
    "psd_resource_text",
    "pdf_annot",
    "droplet_app",
    "plist_flag",
    "account_description",
    "sample_text",
}
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PDF_ANNOT = re.compile(br"/Subtype\s*/(Ink|Stamp)\b")
_SAMPLE_FRAME = re.compile(r"\(in [^)\n]+\)")


def _u32(data, off):
    return struct.unpack(">I", data[off:off + 4])[0]


def _pad_even(size):
    return size + (size % 2)


def parse_psd(data):
    if len(data) < 26 or data[:4] != b"8BPS":
        raise ValueError("not psd")
    if struct.unpack(">H", data[4:6])[0] != 1:
        raise ValueError("not psd version 1")
    channels, height, width, depth, mode = struct.unpack(">HIIHH", data[12:26])
    off = 26
    if off + 4 > len(data):
        raise ValueError("truncated")
    color_len = _u32(data, off)
    color = data[off + 4:off + 4 + color_len]
    if len(color) != color_len:
        raise ValueError("truncated color")
    off += 4 + color_len
    if off + 4 > len(data):
        raise ValueError("truncated")
    res_len = _u32(data, off)
    off += 4 + res_len
    if off + 4 > len(data):
        raise ValueError("truncated")
    section_len = _u32(data, off)
    section = data[off + 4:off + 4 + section_len]
    if len(section) != section_len:
        raise ValueError("truncated layers")
    layers = _parse_layers(section) if section_len else []
    resources = {}
    for rid, payload in e31_grade._psd_resources(data) or ():
        resources.setdefault(rid, []).append(payload)
    return {
        "channels": channels,
        "height": height,
        "width": width,
        "depth": depth,
        "mode": mode,
        "color": color,
        "layers": layers,
        "resources": resources,
    }


def _parse_layers(section):
    if len(section) < 4:
        return []
    info_len = _u32(section, 0)
    if info_len < 2 or 4 + info_len > len(section):
        return []
    info = section[4:4 + info_len]
    count = abs(struct.unpack(">h", info[:2])[0])
    cursor = 2
    layers = []
    for _ in range(count):
        if cursor + 18 > len(info):
            raise ValueError("layer header")
        cursor += 16
        nch = struct.unpack(">H", info[cursor:cursor + 2])[0]
        cursor += 2 + nch * 6
        if info[cursor:cursor + 4] != b"8BIM":
            raise ValueError("blend sig")
        cursor += 12
        extra_len = _u32(info, cursor)
        cursor += 4
        extra_end = cursor + extra_len
        if extra_end > len(info):
            raise ValueError("layer extra")
        layers.append(_read_blocks(info, cursor, extra_end))
        cursor = extra_end
    return layers


def _read_blocks(info, cursor, extra_end):
    blocks = {}
    if cursor + 4 > extra_end:
        return blocks
    mask_size = _u32(info, cursor)
    cursor += 4 + mask_size
    if cursor + 4 > extra_end:
        return blocks
    blend_size = _u32(info, cursor)
    cursor += 4 + blend_size
    if cursor >= extra_end:
        return blocks
    name_len = info[cursor]
    cursor += 1 + name_len
    cursor += (4 - ((1 + name_len) % 4)) % 4
    while cursor + 12 <= extra_end:
        sig = info[cursor:cursor + 4]
        if sig not in (b"8BIM", b"8B64"):
            break
        key = info[cursor + 4:cursor + 8]
        if key in LARGE_KEYS:
            if cursor + 16 > extra_end:
                break
            length = struct.unpack(">Q", info[cursor + 8:cursor + 16])[0]
            cursor += 16
        else:
            length = _u32(info, cursor + 8)
            cursor += 12
        if length < 0 or cursor + length > extra_end:
            break
        blocks.setdefault(key, []).append(info[cursor:cursor + length])
        cursor += length
        if length % 2 and cursor < extra_end:
            cursor += 1
    return blocks


def _utf16_counted(text):
    return struct.pack(">I", len(text)) + text.encode("utf-16-be")


def version_info(reader):
    return struct.pack(">I", 1) + b"\x01" + _utf16_counted(reader) + _utf16_counted(reader)


def _resource(rid, payload):
    pad = b"\x00" if len(payload) % 2 else b""
    return b"8BIM" + struct.pack(">H", rid) + b"\x00\x00" + struct.pack(">I", len(payload)) + payload + pad


def _tagged(key, data):
    pad = b"\x00" if len(data) % 2 else b""
    return b"8BIM" + key + struct.pack(">I", len(data)) + data + pad


def _layer_record(blocks, name="Layer 1"):
    raw_name = name.encode("ascii")
    field = bytes([len(raw_name)]) + raw_name
    field += b"\x00" * ((4 - (len(field) % 4)) % 4)
    extra = struct.pack(">I", 0) + struct.pack(">I", 0) + field
    for key, data in blocks:
        extra += _tagged(key, data)
    rect = struct.pack(">iiii", 0, 0, 0, 0)
    blend = b"8BIM" + b"norm" + bytes((255, 0, 0, 0))
    return rect + struct.pack(">H", 0) + blend + struct.pack(">I", len(extra)) + extra


def build_psd(mode=3, channels=None, color=b"", resources=None, layers=None, sign="2026", width=1, height=1, depth=8):
    """Minimal PSD for fixtures. sign is '2026', 'stock', or 'none'."""
    if channels is None:
        channels = BASE_CHANNELS.get(mode, 3)
    resources = dict(resources or {})
    if sign == "2026":
        resources[1057] = version_info("Adobe Photoshop 2026")
    elif sign == "stock":
        resources[1057] = version_info("Adobe Photoshop CC 2014")
    blob = b"".join(_resource(rid, payload) for rid, payload in sorted(resources.items()))
    if layers:
        records = b"".join(_layer_record(blocks) for blocks in layers)
        info = struct.pack(">h", len(layers)) + records
        section = struct.pack(">I", len(info)) + info + struct.pack(">I", 0)
        layer_mask = struct.pack(">I", len(section)) + section
    else:
        layer_mask = struct.pack(">I", 0)
    header = b"8BPS" + struct.pack(">H", 1) + b"\x00" * 6 + struct.pack(">HIIHH", channels, height, width, depth, mode)
    image = struct.pack(">H", 0) + bytes(channels * height * width)
    return header + struct.pack(">I", len(color)) + color + struct.pack(">I", len(blob)) + blob + layer_mask + image


def _paths(params):
    if params.get("path"):
        return [e31_grade.expand(params["path"])]
    return [e31_grade.expand(item) for item in (params.get("paths") or []) if isinstance(item, str)]


def _read(params):
    paths = _paths(params)
    path = paths[0] if paths else ""
    if not path or not os.path.isfile(path):
        return path, None, e31_grade.result(False, reason="missing", path=path)
    with open(path, "rb") as handle:
        return path, handle.read(), None


def _signed_doc(params):
    path, data, missing = _read(params)
    if missing:
        return path, None, missing
    if not data.startswith(b"8BPS"):
        return path, None, e31_grade.result(False, reason="not-psd", path=path)
    if params.get("require_app_signature", True) and not e31_grade.psd_has_app_signature(data):
        return path, None, e31_grade.result(False, reason="no_app_signature", path=path, app_signature=False)
    try:
        return path, parse_psd(data), None
    except Exception as exc:
        return path, None, e31_grade.result(False, reason="psd-parse", error=type(exc).__name__, path=path)


def _feature(params, predicate):
    path, doc, rejected = _signed_doc(params)
    if rejected:
        return rejected
    ok = bool(predicate(doc))
    return e31_grade.result(ok, reason="ok" if ok else "feature-missing", path=path, app_signature=True)


def _any_key(doc, keys):
    return any(keys.intersection(layer) for layer in doc["layers"])


def _payloads(doc, keys):
    found = []
    for layer in doc["layers"]:
        for key in keys:
            found.extend(layer.get(key, []))
    return found


def has_adjustment(doc):
    return _any_key(doc, ADJUSTMENT_KEYS)


def has_drop_shadow(doc):
    for payload in _payloads(doc, EFFECT_KEYS):
        if b"DrSh" in payload or b"dsdw" in payload:
            return True
    return False


def has_smart_object(doc):
    return _any_key(doc, SMART_KEYS)


def has_layer_comp(doc):
    return any(len(payload) >= 8 for payload in doc["resources"].get(1065, []))


def has_artboard(doc):
    return _any_key(doc, ARTBOARD_KEYS)


def has_duotone(doc):
    return doc["mode"] == 8 and len(doc["color"]) > 0


def has_saved_selection(doc):
    base = BASE_CHANNELS.get(doc["mode"], 3)
    named = doc["resources"].get(1045) or doc["resources"].get(1006)
    return doc["channels"] > base and any(named or ())


def has_frame_animation(doc):
    for payload in _payloads(doc, {b"shmd"}):
        if b"8BIMmlst" in payload or b"8B64mlst" in payload:
            return True
    return False


def has_resource_text(doc, resource_id, token):
    needle = token.lower().encode("ascii")
    return any(needle in payload.lower() for payload in doc["resources"].get(int(resource_id), []))


def grade_pdf_annot(params):
    path, data, missing = _read(params)
    if missing:
        return missing
    if not data.startswith(b"%PDF"):
        return e31_grade.result(False, reason="not-pdf", path=path)
    if not _PDF_ANNOT.search(data):
        return e31_grade.result(False, reason="no-signature-annot", path=path)
    return e31_grade.result(True, reason="ok", path=path)


def grade_droplet(params):
    path = _paths(params)[0] if _paths(params) else ""
    if not path or not os.path.lexists(path):
        return e31_grade.result(False, reason="missing", path=path)
    if not os.path.isdir(path) or os.path.islink(path):
        return e31_grade.result(False, reason="not-bundle", path=path)
    plist_path = os.path.join(path, "Contents", "Info.plist")
    if not os.path.isfile(plist_path):
        return e31_grade.result(False, reason="no-plist", path=path)
    try:
        info = plistlib.loads(open(plist_path, "rb").read())
    except Exception as exc:
        return e31_grade.result(False, reason="plist", error=type(exc).__name__, path=path)
    if not isinstance(info, dict) or info.get("CFBundlePackageType") != "APPL":
        return e31_grade.result(False, reason="not-app", path=path)
    text = " ".join(str(value) for value in info.values() if isinstance(value, str))
    if info.get("CFBundleSignature") != "8BIM" and "photoshop" not in text.lower():
        return e31_grade.result(False, reason="not-photoshop", path=path)
    executable = info.get("CFBundleExecutable")
    macos = os.path.join(path, "Contents", "MacOS")
    names = os.listdir(macos) if os.path.isdir(macos) else []
    if not isinstance(executable, str) or not executable or not any(os.path.isfile(os.path.join(macos, name)) for name in names):
        return e31_grade.result(False, reason="no-executable", path=path)
    return e31_grade.result(True, reason="ok", path=path)


def _plist_values(obj, found):
    if isinstance(obj, str):
        found.append(obj)
    elif isinstance(obj, dict):
        for value in obj.values():
            _plist_values(value, found)
    elif isinstance(obj, list):
        for value in obj:
            _plist_values(value, found)


def grade_plist_flag(params):
    key = params.get("key")
    expect = params.get("expect")
    paths = [item for item in _paths(params) if os.path.basename(item).endswith(".plist")]
    if not key or not paths:
        return e31_grade.result(False, reason="missing", key=key)
    saw = False
    for path in paths:
        if not os.path.isfile(path):
            continue
        try:
            obj = plistlib.loads(open(path, "rb").read())
        except Exception:
            continue
        if not isinstance(obj, dict) or key not in obj:
            continue
        saw = True
        value = obj[key]
        if isinstance(value, bool) and value is expect:
            return e31_grade.result(True, reason="ok", path=path, key=key, value=value)
        if isinstance(value, int) and not isinstance(value, bool) and bool(value) is bool(expect):
            return e31_grade.result(True, reason="ok", path=path, key=key, value=bool(value))
    if not saw:
        return e31_grade.result(False, reason="plist-missing", key=key)
    return e31_grade.result(False, reason="plist-mismatch", key=key)


def _account_file_ok(path):
    name = os.path.basename(path)
    return (name.startswith("Accounts") and name.endswith((".sqlite", ".plist"))) or name == "com.apple.mail.plist"


def _sqlite_has_description(path, text):
    uri = "file:" + os.path.abspath(path) + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            if not _IDENT.match(table):
                continue
            columns = [row[1] for row in conn.execute('PRAGMA table_info("%s")' % table)]
            if any(not _IDENT.match(name) for name in columns):
                continue
            desc_cols = [name for name in columns if "DESCRIPTION" in name.upper() or name.upper().endswith("ACCOUNTNAME")]
            bundle_cols = [name for name in columns if "BUNDLE" in name.upper()]
            bundle = '"%s"' % bundle_cols[0] if bundle_cols else None
            for column in desc_cols:
                selected = '"%s"' % column
                query = "SELECT %s" % selected
                if bundle:
                    query += ", " + bundle
                query += ' FROM "%s" WHERE %s = ?' % (table, selected)
                for row in conn.execute(query, (text,)):
                    if bundle and row[1] not in (None, "") and "mail" not in str(row[1]).lower():
                        continue
                    return True
        return False
    finally:
        conn.close()


def grade_account_description(params):
    text = params.get("text") or ""
    paths = [item for item in _paths(params) if _account_file_ok(item)]
    existing = [item for item in paths if os.path.isfile(item) and os.path.getsize(item) <= 32 * 1024 * 1024]
    if not text or not existing:
        return e31_grade.result(False, reason="missing")
    for path in existing:
        try:
            obj = plistlib.loads(open(path, "rb").read())
        except Exception:
            obj = None
        if obj is not None:
            values = []
            _plist_values(obj, values)
            if text in values:
                return e31_grade.result(True, reason="ok", path=path, via="plist")
            continue
        try:
            with open(path, "rb") as handle:
                header = handle.read(16)
        except OSError:
            continue
        if header.startswith(b"SQLite format 3") and _sqlite_has_description(path, text):
            return e31_grade.result(True, reason="ok", path=path, via="sqlite")
    return e31_grade.result(False, reason="description-mismatch")


def grade_sample_text(params):
    path, data, missing = _read(params)
    if missing:
        return missing
    if data.startswith(b"\x89PNG") or data.startswith(b"8BPS") or data.startswith(b"%PDF"):
        return e31_grade.result(False, reason="not-text", path=path)
    text = data.decode("utf-8", "replace")
    sample = "Sampling process" in text and "Call graph:" in text and "Binary Images:" in text
    spindump = "Spindump" in text and "Process:" in text and "Binary Images:" in text
    frames = len(_SAMPLE_FRAME.findall(text))
    if (sample or spindump) and frames >= 3:
        return e31_grade.result(True, reason="ok", path=path, frames=frames)
    return e31_grade.result(False, reason="not-sample", path=path, frames=frames)


def grade(params):
    kind = params.get("kind")
    if kind == "psd_adjustment":
        return _feature(params, has_adjustment)
    if kind == "psd_drop_shadow":
        return _feature(params, has_drop_shadow)
    if kind == "psd_smart_object":
        return _feature(params, has_smart_object)
    if kind == "psd_layer_comp":
        return _feature(params, has_layer_comp)
    if kind == "psd_artboard":
        return _feature(params, has_artboard)
    if kind == "psd_duotone":
        return _feature(params, has_duotone)
    if kind == "psd_saved_selection":
        return _feature(params, has_saved_selection)
    if kind == "psd_frame_animation":
        return _feature(params, has_frame_animation)
    if kind == "psd_resource_text":
        resource_id = params.get("resource_id")
        token = params.get("token") or ""
        return _feature(params, lambda doc: has_resource_text(doc, resource_id, token))
    if kind == "pdf_annot":
        return grade_pdf_annot(params)
    if kind == "droplet_app":
        return grade_droplet(params)
    if kind == "plist_flag":
        return grade_plist_flag(params)
    if kind == "account_description":
        return grade_account_description(params)
    if kind == "sample_text":
        return grade_sample_text(params)
    return e31_grade.result(False, reason="unknown-kind", kind=kind)
