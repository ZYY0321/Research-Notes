import json, struct, tempfile, zlib
import evaluation
import fixturelib as F

RED = (208, 2, 27)
WHITE = (255, 255, 255)

def build_png(width, height, pixel_fn):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            r, g, b = pixel_fn(x, y)
            raw += bytes((r, g, b, 255))
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(raw))) + chunk(b"IEND", b"")

def stroke_at(center):
    def fn(x, y):
        cy = center + (1 if x % 9 < 3 else 0)
        if 4 <= x <= 43 and cy - 1 <= y <= cy + 1:
            return RED
        return WHITE
    return fn

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, WHITE, rgba=True))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, build_png(width, height, stroke_at(16)))
        cases.append(F.case("reference", params, 1))
        F.write(out, build_png(width, height, stroke_at(5)))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, build_png(width + 4, height, stroke_at(16)))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
