import json, struct, tempfile, zlib
import evaluation
import fixturelib as F

def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

def _png_rgba(width, height, pixel):
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.extend(pixel(x, y))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(rows))) + _chunk(b"IEND", b""))

def _ring(width, height, color, inner, outer):
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0
    def pixel(x, y):
        r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        if inner <= r <= outer:
            return (color[0], color[1], color[2], 255)
        return (0, 0, 0, 0)
    return _png_rgba(width, height, pixel)

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        fill = (235, 90, 30)
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, fill, rgba=True))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, _ring(width, height, fill, 12.0, 24.0))
        cases.append(F.case("reference", params, 1))
        F.write(out, _ring(width, height, fill, 0.0, 24.0))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, _ring(width, height, (30, 90, 235), 12.0, 24.0))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
