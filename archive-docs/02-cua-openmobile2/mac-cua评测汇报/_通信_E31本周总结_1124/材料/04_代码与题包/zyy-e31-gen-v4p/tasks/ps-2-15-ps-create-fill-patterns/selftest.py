import json, struct, zlib, tempfile
import evaluation
import fixturelib as F

RED = (180, 40, 40)
BLUE = (40, 60, 180)


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)


def checker(width, height, color_a, color_b, tile, stamp):
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            color = color_a if ((x // tile + y // tile) % 2 == 0) else color_b
            rows.extend(color)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
    if stamp:
        png += _chunk(b"tEXt", b"Software\x00Adobe Photoshop")
    png += _chunk(b"IDAT", zlib.compress(bytes(rows))) + _chunk(b"IEND", b"")
    return png


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, checker(width, height, RED, BLUE, 8, False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, checker(width, height, RED, BLUE, 8, True))
        cases.append(F.case("reference", params, 1))
        F.write(out, F.solid(width, height, RED, stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, checker(width, height, BLUE, RED, 8, True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
