import json, tempfile, struct, zlib
import evaluation
import fixturelib as F

RED = (220, 30, 30)
BG = (235, 235, 235)
RECT_A = (4, 4, 28, 20)
RECT_B = (20, 12, 44, 28)


def in_rect(x, y, r):
    return r[0] <= x < r[2] and r[1] <= y < r[3]


def make_png(width, height, pixel_fn, rgba=True):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    color_type = 6 if rgba else 2
    raw = b""
    for y in range(height):
        row = bytearray(b"\x00")
        for x in range(width):
            r, g, b = pixel_fn(x, y)
            row += bytes((r, g, b))
            if rgba:
                row += b"\xff"
        raw += bytes(row)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def union_px(x, y):
    return RED if (in_rect(x, y, RECT_A) or in_rect(x, y, RECT_B)) else BG


def single_px(x, y):
    return RED if in_rect(x, y, RECT_A) else BG


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, RED, rgba=True))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, make_png(width, height, union_px, rgba=True))
        cases.append(F.case("reference", params, 1))
        F.write(out, make_png(width, height, single_px, rgba=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, make_png(height, width, union_px, rgba=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))


if __name__ == "__main__":
    main()
