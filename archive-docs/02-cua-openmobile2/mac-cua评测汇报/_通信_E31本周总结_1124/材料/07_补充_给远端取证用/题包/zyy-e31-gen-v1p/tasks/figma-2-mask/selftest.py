import json, struct, tempfile, zlib
import evaluation
import fixturelib as F

BLUE = (45, 120, 220)
WHITE = (255, 255, 255)


def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def make_png(width, height, pixel, alpha=True):
    rows = []
    for y in range(height):
        row = bytearray(b"\x00")
        for x in range(width):
            r, g, b = pixel(x, y)
            row += bytes((r, g, b))
            if alpha:
                row += b"\xff"
        rows.append(bytes(row))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6 if alpha else 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(b"".join(rows)))
            + chunk(b"IEND", b""))


def masked_top_left(x, y):
    return BLUE if (x < 24 and y < 24) else WHITE


def masked_bottom_right(x, y):
    return BLUE if (x >= 24 and y >= 24) else WHITE


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, make_png(width, height, masked_top_left, alpha=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, make_png(width, height, masked_top_left, alpha=True))
        cases.append(F.case("reference", params, 1))
        F.write(out, F.solid(width, height, BLUE, rgba=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, make_png(width, height, masked_bottom_right, alpha=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
