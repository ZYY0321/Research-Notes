import json, tempfile, struct, zlib
import evaluation
import fixturelib as F

BG = (96, 140, 190)
RECT = (18, 10, 29, 21)


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _png(width, height, px, stamp):
    rows = []
    for y in range(height):
        row = bytearray(b"\x00")
        for x in range(width):
            row.extend(px(x, y))
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

        F.remove(out)
        cases.append(F.case("empty", params, 0))

        F.write(out, F.solid(width, height, BG, stamp=False))
        cases.append(F.case("shortcut", params, 0))

        F.write(out, F.solid(width, height, BG, stamp=True))
        cases.append(F.case("reference", params, 1))

        def near_px(x, y):
            if RECT[0] <= x <= RECT[2] and RECT[1] <= y <= RECT[3]:
                return (0, 0, 0)
            return BG
        F.write(out, _png(width, height, near_px, True))
        cases.append(F.case("near_miss", params, 0))

        F.write(out, F.solid(width + 8, height, BG, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
