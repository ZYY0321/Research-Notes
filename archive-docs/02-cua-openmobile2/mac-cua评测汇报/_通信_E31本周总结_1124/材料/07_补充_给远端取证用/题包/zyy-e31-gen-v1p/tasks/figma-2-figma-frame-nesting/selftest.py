import json, struct, tempfile, zlib
import evaluation
import fixturelib as F


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def make_png(width, height, bg, rects):
    rows = []
    for y in range(height):
        row = bytearray(b"\x00")
        for x in range(width):
            color = bg
            for (x0, y0, x1, y1, col) in rects:
                if x0 <= x < x1 and y0 <= y < y1:
                    color = col
            row += bytes([color[0], color[1], color[2], 255])
        rows.append(bytes(row))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(b"".join(rows))
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b""))


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        parent = (30, 60, 200)
        child = (240, 180, 20)
        child_rect = (28, 8, 44, 24, child)
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, parent, rgba=True))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, make_png(width, height, parent, [child_rect]))
        cases.append(F.case("reference", params, 1))
        F.write(out, make_png(width, height, child, [(28, 8, 44, 24, parent)]))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, make_png(width + 4, height, parent, [child_rect]))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))


if __name__ == "__main__":
    main()
