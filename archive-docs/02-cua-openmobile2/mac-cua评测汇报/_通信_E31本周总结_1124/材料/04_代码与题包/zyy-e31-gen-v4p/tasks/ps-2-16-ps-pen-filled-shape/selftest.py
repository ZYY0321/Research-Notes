import json, tempfile, struct, zlib
import evaluation
import fixturelib as F


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def shape_png(width, height, bg, fg, stamp):
    rows = []
    for y in range(height):
        row = bytearray(b"\x00")
        for x in range(width):
            if 14 <= x < 34 and 14 <= y < 34:
                row += bytes(fg)
            else:
                row += bytes(bg)
        rows.append(bytes(row))
    raw = b"".join(rows)
    out = b"\x89PNG\r\n\x1a\n"
    out += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    if stamp:
        out += _chunk(b"tEXt", b"Software\x00Adobe Photoshop 2026")
    out += _chunk(b"IDAT", zlib.compress(raw))
    out += _chunk(b"IEND", b"")
    return out


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        fill = tuple(params["samples"][0]["rgb"])
        bg = tuple(params["samples"][1]["rgb"])
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, shape_png(width, height, bg, fill, stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, shape_png(width, height, bg, fill, stamp=True))
        cases.append(F.case("reference", params, 1))
        F.write(out, F.solid(width, height, fill, stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, shape_png(width, height, fill, bg, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))


if __name__ == "__main__":
    main()
