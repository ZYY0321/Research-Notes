"""Tightened stdlib graders, 2026-11-24.

Drop-in copy of the shared E31 grader. Function names and PARAMS keys stay the
same. This copy rejects files that only look finished: flat or fully transparent
images, sample-point dots on an empty field, magic bytes with a garbage body,
drafts already listed in the setup baseline, and an unsealed empty-inbox skip.

Mail baseline file (setup writes this before the task, grader only reads it):
  ~/Desktop/e31-newapps/state/draft-baseline.txt
  lines: optional "# e31-draft-baseline v1", then the same dump as grading
  (ID=, SUBJECT=, BODY=, TO=, ATTACH=, ----). One setup line:
  e31_grade.write_draft_baseline(draft_dump_text)

Flag seal file, copied from the setup baseline and not the file the task edits:
  ~/Desktop/e31-newapps/state/mail-flag-seal.txt
  lines flagged=N and inbox=M. One setup line:
  e31_grade.write_flag_seal(baseline_text)

Does not import task_api. Does not open apps. osascript runs only when a live
grade is asked for and the params dict has no canned dump or flagged_now.
"""
from __future__ import annotations

import hashlib
import os
import re
import struct
import subprocess
import time
import zlib
from html.parser import HTMLParser

DRAFT_BASELINE_PATH = "~/Desktop/e31-newapps/state/draft-baseline.txt"
FLAG_SEAL_PATH = "~/Desktop/e31-newapps/state/mail-flag-seal.txt"

SEED_RGB = (0x33, 0x66, 0x99)


def result(ok, **details):
    return {"status": "graded", "score": 1 if ok else 0, "details": details}


def expand(path):
    return os.path.expanduser(os.fspath(path))


def _chunk(tag, data):
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def encode_png(width, height, rgb):
    if len(rgb) != width * height * 3:
        raise ValueError("rgb length")
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        raw.extend(rgb[y * stride:(y + 1) * stride])
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b"")


def solid_rgb(width, height, color):
    return bytes(color) * (width * height)


def _paeth(left, up, up_left):
    estimate = left + up - up_left
    pa, pb, pc = abs(estimate - left), abs(estimate - up), abs(estimate - up_left)
    if pa <= pb and pa <= pc:
        return left
    if pb <= pc:
        return up
    return up_left


def png_chunks_ok(data):
    """Magic, chunk CRCs, IHDR first, at least one IDAT, IEND last, no tail."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    off = 8
    seen_ihdr = False
    seen_idat = False
    first = True
    while off + 8 <= len(data):
        length = struct.unpack(">I", data[off:off + 4])[0]
        tag = data[off + 4:off + 8]
        start = off + 8
        end = start + length
        if end + 4 > len(data):
            return False
        chunk = data[start:end]
        crc = struct.unpack(">I", data[end:end + 4])[0]
        if (zlib.crc32(tag + chunk) & 0xFFFFFFFF) != crc:
            return False
        if first and tag != b"IHDR":
            return False
        first = False
        if tag == b"IHDR":
            if seen_ihdr or length < 13:
                return False
            seen_ihdr = True
        elif tag == b"IDAT":
            seen_idat = True
        elif tag == b"IEND":
            return length == 0 and seen_idat and end + 4 == len(data)
        off = end + 4
    return False


def decode_png_full(data):
    """Return width, height, color type, and 8-bit pixels (RGB or RGBA)."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not png")
    off = 8
    ihdr = None
    idat = bytearray()
    while off + 8 <= len(data):
        length = struct.unpack(">I", data[off:off + 4])[0]
        tag = data[off + 4:off + 8]
        start = off + 8
        end = start + length
        if end + 4 > len(data):
            raise ValueError("truncated chunk")
        chunk = data[start:end]
        off = end + 4
        if tag == b"IHDR":
            ihdr = chunk
        elif tag == b"IDAT":
            idat.extend(chunk)
        elif tag == b"IEND":
            break
    if ihdr is None or len(ihdr) < 13:
        raise ValueError("missing ihdr")
    width, height, depth, color, comp, _filt, inter = struct.unpack(">IIBBBBB", ihdr[:13])
    if depth != 8 or color not in (2, 6) or comp != 0 or inter != 0:
        raise ValueError("unsupported png")
    channels = 3 if color == 2 else 4
    raw = zlib.decompress(bytes(idat))
    stride = width * channels
    expect = height * (stride + 1)
    if len(raw) < expect:
        raise ValueError("short idat")
    out = bytearray(width * height * channels)
    prev = bytearray(stride)
    cursor = 0
    for y in range(height):
        filt = raw[cursor]
        cursor += 1
        scan = bytearray(raw[cursor:cursor + stride])
        cursor += stride
        if filt == 1:
            for x in range(stride):
                left = scan[x - channels] if x >= channels else 0
                scan[x] = (scan[x] + left) & 255
        elif filt == 2:
            for x in range(stride):
                scan[x] = (scan[x] + prev[x]) & 255
        elif filt == 3:
            for x in range(stride):
                left = scan[x - channels] if x >= channels else 0
                scan[x] = (scan[x] + ((left + prev[x]) // 2)) & 255
        elif filt == 4:
            for x in range(stride):
                left = scan[x - channels] if x >= channels else 0
                up = prev[x]
                up_left = prev[x - channels] if x >= channels else 0
                scan[x] = (scan[x] + _paeth(left, up, up_left)) & 255
        elif filt != 0:
            raise ValueError("bad filter")
        prev = scan
        dest = y * width * channels
        out[dest:dest + stride] = scan
    return width, height, color, bytes(out)


def decode_png(data):
    width, height, color, pixels = decode_png_full(data)
    if color == 2:
        return width, height, pixels
    out = bytearray(width * height * 3)
    for index in range(width * height):
        src = index * 4
        dest = index * 3
        out[dest:dest + 3] = pixels[src:src + 3]
    return width, height, bytes(out)


def jpeg_size(data):
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ValueError("not jpeg")
    index = 2
    while index + 3 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        while index < len(data) and data[index] == 0xFF:
            index += 1
        if index >= len(data):
            break
        marker = data[index]
        index += 1
        if marker in (0xD8, 0xD9) or marker == 0x01 or 0xD0 <= marker <= 0xD7:
            continue
        if index + 2 > len(data):
            break
        seglen = struct.unpack(">H", data[index:index + 2])[0]
        if marker in (0xC0, 0xC1, 0xC2) and index + 7 <= len(data):
            height, width = struct.unpack(">HH", data[index + 3:index + 7])
            return width, height
        index += seglen
    raise ValueError("no sof")


def psd_layer_count(data):
    if len(data) < 26 or data[:4] != b"8BPS":
        raise ValueError("not psd")
    if struct.unpack(">H", data[4:6])[0] != 1:
        raise ValueError("not psd version 1")
    off = 26
    for _section in range(2):
        if off + 4 > len(data):
            raise ValueError("truncated")
        length = struct.unpack(">I", data[off:off + 4])[0]
        off += 4 + length
    if off + 4 > len(data):
        raise ValueError("truncated")
    layer_mask_len = struct.unpack(">I", data[off:off + 4])[0]
    off += 4
    if layer_mask_len == 0:
        return 0
    if off + 6 > len(data):
        raise ValueError("truncated layer info")
    info_len = struct.unpack(">I", data[off:off + 4])[0]
    off += 4
    if info_len < 2:
        return 0
    return abs(struct.unpack(">h", data[off:off + 2])[0])


def psd_contains(data, text):
    if not data.startswith(b"8BPS") or not text:
        return False
    blobs = (text.encode("utf-8"), text.encode("utf-16-be"), text.encode("utf-16-le"))
    return any(blob in data for blob in blobs)


def _read(path):
    path = expand(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "rb") as handle:
        return path, handle.read()


def _pixel(rgb, width, x, y):
    index = (y * width + x) * 3
    return rgb[index:index + 3]


# r3 psd-tools wrote a stock sample, not a Photoshop 2026 save.
# Version resource 1057 reader is "Adobe Photoshop CC 2014".
# XMP CreatorTool is "Adobe Photoshop CC 2014 (2014.2.2 x001 x003)  (Macintosh)".
PSD_STOCK_READER = "Adobe Photoshop CC 2014"
PSD_STOCK_XMP = "2014.2.2 x001 x003"
_PS_PHRASE = b"Adobe Photoshop"
_PS_VERSION = re.compile(r"Adobe Photoshop[^\n]{0,80}(20[2-9]\d|\d{2}\.\d)")


def _png_text_blobs(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return []
    blobs = []
    off = 8
    while off + 8 <= len(data):
        length = struct.unpack(">I", data[off:off + 4])[0]
        tag = data[off + 4:off + 8]
        start = off + 8
        end = start + length
        if end + 4 > len(data):
            break
        chunk = data[start:end]
        off = end + 4
        if tag == b"tEXt":
            blobs.append(chunk.split(b"\x00", 1)[-1])
        elif tag == b"zTXt":
            blobs.append(chunk)
            nul = chunk.find(b"\x00")
            if nul >= 0 and nul + 2 <= len(chunk):
                try:
                    blobs.append(zlib.decompress(chunk[nul + 2:]))
                except zlib.error:
                    pass
        elif tag == b"iTXt":
            blobs.append(chunk)
            nul = chunk.find(b"\x00")
            if nul >= 0 and nul + 3 <= len(chunk) and chunk[nul + 1] == 1:
                rest = chunk[nul + 3:]
                for _ in range(2):
                    cut = rest.find(b"\x00")
                    if cut < 0:
                        rest = b""
                        break
                    rest = rest[cut + 1:]
                if rest:
                    try:
                        blobs.append(zlib.decompress(rest))
                    except zlib.error:
                        pass
        elif tag == b"IEND":
            break
    return blobs


def _phrase_in(blob):
    return _PS_PHRASE in blob or _PS_PHRASE.decode("ascii").encode("utf-16-be") in blob


def png_has_app_signature(data):
    return any(_phrase_in(blob) for blob in _png_text_blobs(data))


def _jpeg_segments(data):
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return
    index = 2
    while index + 3 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        while index < len(data) and data[index] == 0xFF:
            index += 1
        if index >= len(data):
            break
        marker = data[index]
        index += 1
        if marker == 0xD9:
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD7 or marker == 0xD8:
            continue
        if index + 2 > len(data):
            break
        seglen = struct.unpack(">H", data[index:index + 2])[0]
        if seglen < 2 or index + seglen > len(data):
            break
        yield marker, data[index + 2:index + seglen]
        index += seglen


def jpeg_has_app_signature(data):
    for marker, payload in _jpeg_segments(data):
        if marker == 0xED and (payload.startswith(b"Photoshop 3.0\x00") or _phrase_in(payload)):
            return True
        if marker == 0xE1 and _phrase_in(payload):
            return True
    return False


def _psd_resources(data):
    if len(data) < 30 or data[:4] != b"8BPS":
        return
    off = 26
    if off + 4 > len(data):
        return
    color_len = struct.unpack(">I", data[off:off + 4])[0]
    off += 4 + color_len
    if off + 4 > len(data):
        return
    res_len = struct.unpack(">I", data[off:off + 4])[0]
    pos = off + 4
    end = min(len(data), pos + res_len)
    while pos + 12 <= end:
        sig = data[pos:pos + 4]
        if sig not in (b"8BIM", b"8B64"):
            break
        rid = struct.unpack(">H", data[pos + 4:pos + 6])[0]
        name_len = data[pos + 6]
        cursor = pos + 7 + name_len
        if (cursor - pos) % 2 == 1:
            cursor += 1
        if cursor + 4 > end:
            break
        size = struct.unpack(">I", data[cursor:cursor + 4])[0]
        payload_end = cursor + 4 + size
        if payload_end > end:
            break
        yield rid, data[cursor + 4:payload_end]
        cursor = payload_end + (size % 2)
        pos = cursor


def _psd_unicode(payload, cursor):
    if cursor + 4 > len(payload):
        return "", cursor
    count = struct.unpack(">I", payload[cursor:cursor + 4])[0]
    raw = payload[cursor + 4:cursor + 4 + count * 2]
    return raw.decode("utf-16-be", "replace"), cursor + 4 + count * 2


def psd_version_info(data):
    writer = reader = ""
    xmp = ""
    for rid, payload in _psd_resources(data) or ():
        if rid == 1057 and len(payload) >= 5:
            cursor = 5
            writer, cursor = _psd_unicode(payload, cursor)
            reader, _cursor = _psd_unicode(payload, cursor)
        elif rid == 1060:
            xmp = payload.decode("utf-8", "replace")
    return writer, reader, xmp


def psd_has_app_signature(data):
    writer, reader, xmp = psd_version_info(data)
    if "Adobe Photoshop" not in writer and "Adobe Photoshop" not in reader:
        return False
    if reader.strip() == PSD_STOCK_READER or PSD_STOCK_XMP in xmp:
        return False
    if _PS_VERSION.search(reader) or _PS_VERSION.search(xmp):
        return True
    return False


def _ext_ok(path, suffixes):
    return os.path.splitext(path)[1].lower() in suffixes


def _signature_required(params):
    """Photoshop exports must carry a signature even if a task forgot the flag.

    Figma paths are left alone: their written checks do not ask for an Adobe
    signature, and a real Figma export does not contain one.
    """
    if params.get("require_app_signature"):
        return True
    note = params.get("grade_note") or ""
    # "不核 Photoshop 署名" is an explicit opt-out, not a requirement.
    if "不核" in note and "署名" in note:
        note_requires = False
    else:
        note_requires = "Photoshop" in note and ("署名" in note or "由 Photoshop" in note)
    if note_requires:
        return True
    name = os.path.basename(str(params.get("path") or "")).lower()
    if params.get("kind") in ("png", "jpeg", "psd", "png_rgba") and name.startswith("ps-"):
        return True
    return False


def _rgb_view(color, pixels):
    if color == 2:
        return pixels
    out = bytearray((len(pixels) // 4) * 3)
    dest = 0
    for index in range(0, len(pixels), 4):
        out[dest:dest + 3] = pixels[index:index + 3]
        dest += 3
    return bytes(out)


def _png_content_problems(width, height, color, pixels, params):
    """Reject a blank field. A real picture still has more than the sample dots."""
    problems = []
    channels = 3 if color == 2 else 4
    total = width * height
    if channels <= 0 or len(pixels) < total * channels:
        problems.append("flat")
        return problems
    samples = params.get("samples") or []
    sample_at = set()
    for sample in samples:
        try:
            sample_at.add((int(sample["x"]), int(sample["y"])))
        except (TypeError, ValueError, KeyError):
            continue
    seen = {}
    outside = {}
    outside_n = 0
    max_alpha = 0
    for index in range(total):
        start = index * channels
        key = pixels[start:start + channels]
        seen[key] = seen.get(key, 0) + 1
        if channels == 4 and key[3] > max_alpha:
            max_alpha = key[3]
        x = index % width
        y = index // width
        if (x, y) not in sample_at:
            outside[key] = outside.get(key, 0) + 1
            outside_n += 1
    if color == 6 and max_alpha == 0:
        problems.append("transparent")
    if len(seen) <= 1:
        problems.append("flat")
    if samples and outside_n > 0 and outside:
        minority = outside_n - max(outside.values())
        if minority < 2:
            problems.append("sample-dots")
    return problems


def jpeg_well_formed(data):
    """SOI, a real scan after SOS, and EOI. A SOF size header alone is not enough."""
    if len(data) < 16 or not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
        return False
    try:
        jpeg_size(data)
    except Exception:
        return False
    sos = data.find(b"\xff\xda")
    if sos < 0 or sos + 4 >= len(data):
        return False
    seglen = struct.unpack(">H", data[sos + 2:sos + 4])[0]
    if seglen < 2 or sos + 2 + seglen >= len(data):
        return False
    scan_at = sos + 2 + seglen
    eoi = len(data) - 2
    return eoi - scan_at >= 4


def psd_layout(data):
    """Header plus color, resource, layer, and a non-empty image-data section.

    Returns None for an 8BPS prefix with no image. layer_len 0 is allowed when
    the merged image data is actually there (a flattened Photoshop file).
    """
    if len(data) < 26 or data[:4] != b"8BPS":
        return None
    if struct.unpack(">H", data[4:6])[0] != 1:
        return None
    channels = struct.unpack(">H", data[12:14])[0]
    height = struct.unpack(">I", data[14:18])[0]
    width = struct.unpack(">I", data[18:22])[0]
    depth = struct.unpack(">H", data[22:24])[0]
    mode = struct.unpack(">H", data[24:26])[0]
    if not (1 <= channels <= 56 and width > 0 and height > 0):
        return None
    if depth not in (1, 8, 16, 32) or mode not in (0, 1, 2, 3, 4, 7, 8, 9):
        return None
    off = 26
    for _section in range(2):
        if off + 4 > len(data):
            return None
        length = struct.unpack(">I", data[off:off + 4])[0]
        off += 4
        if length > len(data) - off:
            return None
        off += length
    if off + 4 > len(data):
        return None
    layer_len = struct.unpack(">I", data[off:off + 4])[0]
    layer_at = off + 4
    if layer_len > len(data) - layer_at:
        return None
    image_off = layer_at + layer_len
    if image_off + 3 > len(data):
        return None
    compression = struct.unpack(">H", data[image_off:image_off + 2])[0]
    if compression not in (0, 1, 2, 3):
        return None
    return {
        "width": width,
        "height": height,
        "channels": channels,
        "depth": depth,
        "layer_at": layer_at,
        "layer_len": layer_len,
        "image_off": image_off,
    }


def psd_layer_contains(data, text, layout=None):
    """Needle must sit in the layer-and-mask section, not after the file."""
    if not text:
        return False
    if layout is None:
        layout = psd_layout(data)
    if not layout or layout["layer_len"] <= 0:
        return False
    blob = data[layout["layer_at"]:layout["layer_at"] + layout["layer_len"]]
    needles = (text.encode("utf-8"), text.encode("utf-16-be"), text.encode("utf-16-le"))
    return any(needle and needle in blob for needle in needles)


def tiff_well_formed(data):
    """Classic little-endian TIFF: II*\\0, version 42, and an IFD that fits."""
    if len(data) < 14 or not data.startswith(b"II*\x00"):
        return False
    version = struct.unpack_from("<H", data, 4)[0]
    offset = struct.unpack_from("<I", data, 6)[0]
    if version != 42 or offset < 8 or offset + 6 > len(data):
        return False
    count = struct.unpack_from("<H", data, offset)[0]
    if count > 256:
        return False
    return offset + 2 + count * 12 + 4 <= len(data)


def text_phrases(value):
    """A string is one phrase. A list is several phrases. Never walk characters."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    return [str(item) for item in value]


def _unsigned(params, path, data):
    if not _signature_required(params):
        return None
    kind = params.get("kind")
    if kind == "png":
        ok = png_has_app_signature(data)
    elif kind == "jpeg":
        ok = jpeg_has_app_signature(data)
    elif kind == "psd":
        ok = psd_has_app_signature(data)
    else:
        ok = False
    if ok:
        return None
    return result(False, reason="no_app_signature", path=path, app_signature=False)


def grade_png(params):
    try:
        path, data = _read(params["path"])
    except Exception as exc:
        return result(False, reason="png", error=type(exc).__name__, path=expand(params["path"]))
    if not _ext_ok(path, {".png"}):
        return result(False, reason="extension", path=path)
    if not png_chunks_ok(data):
        return result(False, reason="png-structure", path=path)
    rejected = _unsigned(params, path, data)
    if rejected:
        return rejected
    try:
        width, height, color, pixels = decode_png_full(data)
        rgb = _rgb_view(color, pixels)
    except Exception as exc:
        return result(False, reason="png", error=type(exc).__name__, path=path)
    problems = []
    if params.get("width") is not None and width != params["width"]:
        problems.append("width")
    if params.get("height") is not None and height != params["height"]:
        problems.append("height")
    if params.get("min_width") is not None and width < params["min_width"]:
        problems.append("min_width")
    if params.get("min_height") is not None and height < params["min_height"]:
        problems.append("min_height")
    problems.extend(_png_content_problems(width, height, color, pixels, params))
    keep = params.get("keep")
    if keep:
        try:
            _kpath, keep_data = _read(keep["path"])
            keep_w, keep_h, _keep_rgb = decode_png(keep_data)
            if keep.get("width") is not None and keep_w != keep["width"]:
                problems.append("keep.width")
            if keep.get("height") is not None and keep_h != keep["height"]:
                problems.append("keep.height")
        except Exception as exc:
            problems.append("keep:" + type(exc).__name__)
    for sample in params.get("samples") or []:
        x, y = sample["x"], sample["y"]
        if not (0 <= x < width and 0 <= y < height):
            problems.append("sample-bounds")
            continue
        got = _pixel(rgb, width, x, y)
        tol = sample.get("tol", 0)
        expect = bytes(sample["rgb"])
        if any(abs(a - b) > tol for a, b in zip(got, expect)):
            problems.append("sample@%s,%s" % (x, y))
    differ = params.get("differ_from")
    mean_abs = None
    if differ:
        try:
            _dpath, other = _read(differ["path"])
            _ow, _oh, other_rgb = decode_png(other)
            if len(other_rgb) != len(rgb):
                problems.append("differ-size")
            else:
                mean_abs = sum(abs(a - b) for a, b in zip(rgb, other_rgb)) / len(rgb)
                if mean_abs < differ.get("min_mean_abs", 1):
                    problems.append("differ")
        except Exception as exc:
            problems.append("differ:" + type(exc).__name__)
    details = dict(path=path, width=width, height=height, problems=problems, mean_abs=mean_abs,
                   quality_checked=False)
    if _signature_required(params):
        details["app_signature"] = True
    return result(not problems, reason="ok" if not problems else "png-mismatch", **details)


def grade_jpeg(params):
    try:
        path, data = _read(params["path"])
    except Exception as exc:
        return result(False, reason="jpeg", error=type(exc).__name__, path=expand(params["path"]))
    if not _ext_ok(path, {".jpg", ".jpeg"}):
        return result(False, reason="extension", path=path)
    if not jpeg_well_formed(data):
        return result(False, reason="jpeg-structure", path=path)
    rejected = _unsigned(params, path, data)
    if rejected:
        return rejected
    try:
        width, height = jpeg_size(data)
    except Exception as exc:
        return result(False, reason="jpeg", error=type(exc).__name__, path=path)
    problems = []
    if params.get("width") is not None and width != params["width"]:
        problems.append("width")
    if params.get("height") is not None and height != params["height"]:
        problems.append("height")
    details = dict(path=path, width=width, height=height, problems=problems, quality_checked=False)
    if _signature_required(params):
        details["app_signature"] = True
    return result(not problems, reason="ok" if not problems else "jpeg-mismatch", **details)


def _psd_needle(params, problems):
    if params.get("contains_file"):
        try:
            lines = open(expand(params["contains_file"]), encoding="utf-8").read().splitlines()
        except OSError:
            problems.append("contains_file")
            return None
        needle = lines[0].strip() if lines else ""
        if not needle:
            problems.append("contains_file")
            return None
        return needle
    return params.get("contains") or None


def grade_psd(params):
    try:
        path, data = _read(params["path"])
    except Exception as exc:
        return result(False, reason="psd", error=type(exc).__name__, path=expand(params["path"]))
    if not _ext_ok(path, {".psd"}):
        return result(False, reason="extension", path=path)
    layout = psd_layout(data)
    if layout is None:
        return result(False, reason="psd-structure", path=path)
    rejected = _unsigned(params, path, data)
    if rejected:
        return rejected
    problems = []
    count = None
    needle = _psd_needle(params, problems)
    if needle and not psd_layer_contains(data, needle, layout):
        problems.append("contains")
    if params.get("layer_count_in") is not None:
        try:
            count = psd_layer_count(data)
            if count not in params["layer_count_in"]:
                problems.append("layer_count")
        except Exception as exc:
            problems.append("layer_count:" + type(exc).__name__)
    details = dict(path=path, problems=problems, layer_count=count, width=layout["width"], height=layout["height"])
    if _signature_required(params):
        details["app_signature"] = True
    return result(not problems, reason="ok" if not problems else "psd-mismatch", **details)


def grade_text(params):
    path = expand(params["path"])
    try:
        text = open(path, encoding="utf-8").read()
    except Exception as exc:
        return result(False, reason="text", error=type(exc).__name__, path=path)
    missing = [item for item in text_phrases(params.get("contains")) if item not in text]
    exact = params.get("exact")
    if exact is not None and text.strip() != exact:
        missing.append("exact")
    return result(not missing, reason="ok" if not missing else "text-mismatch", path=path, missing=missing)


def parse_draft_dump(text):
    records = []
    current = {}
    for line in (text or "").splitlines():
        if line.strip() == "----":
            if current:
                records.append(current)
            current = {}
            continue
        for key in ("ID", "SUBJECT", "BODY", "TO", "ATTACH"):
            prefix = key + "="
            if line.startswith(prefix):
                current[key] = line[len(prefix):]
                break
    if current:
        records.append(current)
    return records


class _HtmlText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        if data:
            self.parts.append(data)


def visible_text(value):
    if not value or "<" not in value or ">" not in value:
        return value or ""
    parser = _HtmlText()
    try:
        parser.feed(value)
        parser.close()
    except Exception:
        return value
    text = "".join(parser.parts)
    return text if text.strip() else value


def _draft_fp(record):
    raw = "\n".join((
        record.get("SUBJECT") or "",
        record.get("BODY") or "",
        record.get("TO") or "",
        record.get("ATTACH") or "",
    ))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_draft_baseline(params):
    """Records written before the task. Missing file means no known old drafts."""
    if params and "draft_baseline" in params:
        return parse_draft_dump(params.get("draft_baseline") or "")
    path = expand(params["draft_baseline_path"]) if params and params.get("draft_baseline_path") else expand(DRAFT_BASELINE_PATH)
    if not os.path.isfile(path):
        return []
    try:
        return parse_draft_dump(open(path, encoding="utf-8").read())
    except OSError:
        return []


def _prior_index(records):
    ids = set()
    subjects = set()
    fps = set()
    for record in records:
        ident = (record.get("ID") or "").strip()
        if ident:
            ids.add(ident)
        subject = record.get("SUBJECT") or ""
        if subject:
            subjects.add(subject)
        fps.add(_draft_fp(record))
    return {"ids": ids, "subjects": subjects, "fps": fps}


def _draft_is_prior(record, prior):
    ident = (record.get("ID") or "").strip()
    if ident:
        return ident in prior["ids"]
    subject = record.get("SUBJECT") or ""
    if subject and subject in prior["subjects"]:
        return True
    return _draft_fp(record) in prior["fps"]


def write_draft_baseline(text, path=None):
    """Setup calls this once, with the pre-task draft dump. Does not read Mail."""
    path = expand(path or DRAFT_BASELINE_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = text or ""
    if not body.lstrip().startswith("#"):
        body = "# e31-draft-baseline v1\n" + body
    if body and not body.endswith("\n"):
        body += "\n"
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)
    return path


def write_flag_seal(text, path=None):
    """Setup copies the flag baseline here. The task file is the one an agent can edit."""
    path = expand(path or FLAG_SEAL_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = text or ""
    if body and not body.endswith("\n"):
        body += "\n"
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)
    return path


def match_drafts(text, params):
    prior = _prior_index(load_draft_baseline(params))
    for record in parse_draft_dump(text):
        if _draft_is_prior(record, prior):
            continue
        if params.get("subject") and record.get("SUBJECT") != params["subject"]:
            continue
        body = visible_text(record.get("BODY", ""))
        if params.get("body_contains") and params["body_contains"] not in body:
            continue
        if params.get("to_contains") and params["to_contains"] not in record.get("TO", ""):
            continue
        if params.get("attachment_contains") and params["attachment_contains"] not in record.get("ATTACH", ""):
            continue
        return True
    return False


DRAFT_SCRIPT = r'''
on flatten(t)
    set AppleScript's text item delimiters to {return, linefeed}
    set parts to text items of (t as string)
    set AppleScript's text item delimiters to " "
    set joined to parts as string
    set AppleScript's text item delimiters to ""
    return joined
end flatten

on dumpBox(boxRef)
    tell application "Mail"
        set blob to ""
        try
            set msgList to messages of boxRef
        on error
            return ""
        end try
        repeat with m in msgList
            set subj to ""
            set bodyText to ""
            set recText to ""
            set attText to ""
            try
                set subj to my flatten(subject of m)
            end try
            try
                set bodyText to my flatten(content of m)
            end try
            if bodyText is "" then
                try
                    set bodyText to my flatten(source of m)
                end try
            end if
            try
                repeat with r in (to recipients of m)
                    set recText to recText & (address of r as string) & ","
                end repeat
            end try
            try
                repeat with a in (mail attachments of m)
                    set attText to attText & (name of a as string) & ","
                end repeat
            end try
            set idText to ""
            try
                set idText to (id of m) as string
            end try
            set blob to blob & "ID=" & idText & linefeed & "SUBJECT=" & subj & linefeed & "BODY=" & bodyText & linefeed & "TO=" & recText & linefeed & "ATTACH=" & attText & linefeed & "----" & linefeed
        end repeat
        return blob
    end tell
end dumpBox

on remember(seenText, marker)
    if marker is "" then
        return seenText
    end if
    if seenText contains ("|" & marker & "|") then
        return seenText
    end if
    return seenText & marker & "|"
end remember

on seenAlready(seenText, marker)
    if marker is "" then
        return false
    end if
    return seenText contains ("|" & marker & "|")
end seenAlready

set blob to ""
set seenText to "|"
tell application "Mail"
    set nameList to {"Drafts", "草稿", "草稿箱"}
    repeat with acc in accounts
        set candidates to {}
        repeat with n in nameList
            try
                set end of candidates to mailbox (n as string) of acc
            end try
        end repeat
        try
            repeat with mb in mailboxes of acc
                set n to name of mb as string
                if n contains "Draft" or n contains "draft" or n contains "草稿" then
                    set end of candidates to mb
                end if
            end repeat
        end try
        repeat with mb in candidates
            set marker to ""
            try
                set marker to (id of mb) as string
            end try
            if marker is "" then
                try
                    set marker to (name of mb) as string
                end try
            end if
            if not my seenAlready(seenText, marker) then
                set seenText to my remember(seenText, marker)
                set blob to blob & my dumpBox(mb)
            end if
        end repeat
    end repeat
    repeat with n in nameList
        try
            set blob to blob & my dumpBox(mailbox (n as string))
        end try
    end repeat
end tell
return blob
'''

FLAG_NOW_SCRIPT = r'''
tell application "Mail"
    set flaggedCount to 0
    set inboxNames to {"INBOX", "收件箱"}
    repeat with acc in accounts
        repeat with n in inboxNames
            try
                set mb to mailbox (n as string) of acc
                set flaggedCount to flaggedCount + (count of (messages of mb whose flagged status is true))
            end try
        end repeat
    end repeat
    return flaggedCount as string
end tell
'''


def run_osascript(script, timeout=45):
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


def _parse_flag_pair(text):
    flagged = inbox = None
    try:
        for line in (text or "").splitlines():
            line = line.strip()
            if line.startswith("flagged="):
                flagged = int(line.split("=", 1)[1])
            elif line.startswith("inbox="):
                inbox = int(line.split("=", 1)[1])
    except ValueError:
        return None
    if flagged is None or inbox is None:
        return None
    return flagged, inbox


def grade_flag_logic(skip_text, baseline_text, flagged_now, seal_text=None):
    base = (baseline_text or "").strip()
    skip = (skip_text or "").strip()
    if base in ("", "unknown"):
        return False, "baseline_unknown"
    pair = _parse_flag_pair(base)
    if pair is None:
        return False, "baseline_bad"
    flagged0, inbox0 = pair
    seal = _parse_flag_pair(seal_text) if seal_text else None
    if inbox0 == 0:
        if skip == "no-message" and seal == (flagged0, 0):
            return True, "skipped_empty_inbox"
        if skip == "no-message":
            return False, "empty_inbox_unsealed"
        return False, "empty_inbox_needs_skip_file"
    if seal and seal != (flagged0, inbox0):
        return False, "baseline_rewritten"
    if skip:
        return False, "skip_file_but_inbox_not_empty"
    if flagged_now is None:
        return False, "flagged_now_missing"
    if flagged_now > flagged0:
        return True, "flagged_increased"
    return False, "flag_not_increased"


def grade_mail_draft(params):
    if "dump" in params:
        text = params.get("dump") or ""
        records = len(parse_draft_dump(text))
        ok = match_drafts(text, params)
        return result(ok, reason="ok" if ok else "draft-missing", records=records, reads=1)
    deadline = time.time() + float(params.get("wait_seconds", 60))
    reads = 0
    last_text = ""
    last_err = None
    while True:
        reads += 1
        text, err = run_osascript(DRAFT_SCRIPT, timeout=15)
        if err:
            last_err = err
            text = ""
        else:
            last_err = None
            text = text or ""
        last_text = text
        records = len(parse_draft_dump(text))
        if not err and match_drafts(text, params):
            return result(True, reason="ok", records=records, reads=reads)
        if time.time() >= deadline:
            break
        time.sleep(5)
    if last_err and not last_text:
        return result(False, reason="applescript", error=last_err, records=0, reads=reads)
    records = len(parse_draft_dump(last_text))
    return result(False, reason="draft-missing", records=records, reads=reads)


def grade_mail_flag(params):
    skip_path = expand(params["skip_path"])
    base_path = expand(params["baseline_path"])
    skip_text = ""
    if os.path.isfile(skip_path):
        try:
            skip_text = open(skip_path, encoding="utf-8").read()
        except OSError as exc:
            return result(False, reason="skip-file", error=type(exc).__name__)
    try:
        baseline = open(base_path, encoding="utf-8").read()
    except OSError as exc:
        return result(False, reason="baseline-missing", error=type(exc).__name__, path=base_path)
    if "flagged_now" in params:
        flagged_now = params["flagged_now"]
    else:
        text, err = run_osascript(FLAG_NOW_SCRIPT)
        if err:
            return result(False, reason="applescript", error=err)
        try:
            flagged_now = int((text or "").strip())
        except ValueError:
            return result(False, reason="flagged_now_bad", raw=(text or "")[:80])
    if "flag_seal" in params:
        seal_text = params.get("flag_seal") or ""
    else:
        seal_path = expand(params["flag_seal_path"]) if params.get("flag_seal_path") else expand(FLAG_SEAL_PATH)
        seal_text = None
        if os.path.isfile(seal_path):
            try:
                seal_text = open(seal_path, encoding="utf-8").read()
            except OSError as exc:
                return result(False, reason="flag-seal", error=type(exc).__name__, path=seal_path)
    ok, why = grade_flag_logic(skip_text, baseline, flagged_now, seal_text)
    return result(ok, reason=why, flagged_now=flagged_now)


def grade_manual(params):
    return result(False, reason="gradeable_false", note=params.get("note", ""))


def grade(params):
    kind = params.get("kind")
    if kind == "all":
        parts = [grade(check) for check in params.get("checks") or []]
        ok = bool(parts) and all(part["score"] == 1 for part in parts)
        reasons = [part["details"].get("reason") for part in parts]
        if not ok and "no_app_signature" in reasons:
            reason = "no_app_signature"
        else:
            reason = "ok" if ok else "all"
        out = result(ok, reason=reason, parts=[part["details"] for part in parts])
    elif kind == "png":
        out = grade_png(params)
    elif kind == "jpeg":
        out = grade_jpeg(params)
    elif kind == "psd":
        out = grade_psd(params)
    elif kind == "text":
        out = grade_text(params)
    elif kind == "mail_draft":
        out = grade_mail_draft(params)
    elif kind == "mail_flag":
        out = grade_mail_flag(params)
    elif kind == "manual":
        out = grade_manual(params)
    else:
        out = result(False, reason="unknown-kind", kind=kind)
    note = params.get("grade_note")
    if note and kind != "all":
        out["details"]["grade_note"] = note
    elif note and kind == "all":
        out["details"]["grade_note"] = note
    return out
