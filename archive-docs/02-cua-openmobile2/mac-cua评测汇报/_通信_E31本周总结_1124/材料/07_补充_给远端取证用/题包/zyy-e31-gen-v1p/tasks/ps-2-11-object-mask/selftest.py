import json, os, copy, struct, zlib, tempfile
import evaluation
import fixturelib as F

OBJECT = (178, 34, 34, 255)
CLEAR = (255, 255, 255, 0)
BACK = (235, 235, 235, 255)


def _chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def _stamp_chunks(data):
    keep = []
    offset = 8
    while offset + 12 <= len(data):
        (length,) = struct.unpack(">I", data[offset:offset + 4])
        kind = data[offset + 4:offset + 8]
        if kind not in (b"IHDR", b"PLTE", b"IDAT", b"IEND"):
            keep.append(data[offset:offset + 12 + length])
        if kind == b"IEND":
            break
        offset += 12 + length
    if not keep:
        keep = [_chunk(b"tEXt", b"Software\x00Adobe Photoshop")]
    return keep


def _rgba(width, height, pixel, extra):
    rows = []
    for y in range(height):
        row = bytearray(b"\x00")
        for x in range(width):
            row += bytes(pixel(x, y))
        rows.append(bytes(row))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + b"".join(extra)
            + _chunk(b"IDAT", zlib.compress(b"".join(rows)))
            + _chunk(b"IEND", b""))


def _masked(x, y):
    return OBJECT if 12 <= x < 36 and 8 <= y < 24 else CLEAR


def _inverted(x, y):
    return CLEAR if 12 <= x < 36 and 8 <= y < 24 else BACK


def _masked_swapped(x, y):
    return OBJECT if 8 <= x < 24 and 12 <= y < 36 else CLEAR


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = copy.deepcopy(evaluation.PARAMS)
        for check in params["checks"]:
            check["path"] = os.path.join(directory, os.path.basename(check["path"]))
        psd_path = params["checks"][0]["path"]
        png_path = params["checks"][1]["path"]
        width = params["checks"][1]["width"]
        height = params["checks"][1]["height"]
        stamp = _stamp_chunks(F.solid(8, 8, (10, 20, 30), stamp=True))
        psd_bytes = b"8BPS" + b"\x00" * 60
        F.remove(psd_path)
        F.remove(png_path)
        cases.append(F.case("empty", params, 0))
        F.write(psd_path, psd_bytes)
        F.write(png_path, _rgba(width, height, _masked, []))
        cases.append(F.case("shortcut", params, 0))
        F.write(png_path, _rgba(width, height, _masked, stamp))
        cases.append(F.case("reference", params, 1))
        F.write(png_path, _rgba(width, height, _inverted, stamp))
        cases.append(F.case("near_miss", params, 0))
        F.write(png_path, _rgba(height, width, _masked_swapped, stamp))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))


if __name__ == "__main__":
    main()
