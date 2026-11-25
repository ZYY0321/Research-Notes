import json, tempfile, zlib, struct
import evaluation
import fixturelib as F

RED = (200, 40, 40)
BLUE = (40, 60, 200)
GREEN = (30, 160, 70)


def make_png(width, height, left_color, right_color, stamp):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    rows = b''
    for y in range(height):
        rows += b'\x00'
        for x in range(width):
            color = left_color if x < width // 2 else right_color
            rows += bytes(color)
    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    if stamp:
        out += chunk(b'tEXt', b'Software\x00Adobe Photoshop 2026')
    out += chunk(b'IDAT', zlib.compress(rows))
    out += chunk(b'IEND', b'')
    return out


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, make_png(width, height, GREEN, BLUE, False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, make_png(width, height, GREEN, BLUE, True))
        cases.append(F.case("reference", params, 1))
        F.write(out, make_png(width, height, GREEN, GREEN, True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, make_png(width, height, RED, GREEN, True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
