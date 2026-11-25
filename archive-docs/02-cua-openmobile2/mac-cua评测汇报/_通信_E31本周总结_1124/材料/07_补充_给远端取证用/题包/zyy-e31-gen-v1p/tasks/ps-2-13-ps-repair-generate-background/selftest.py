import json, struct, tempfile, zlib
import evaluation
import fixturelib as F

SUBJECT = (200, 60, 60, 255)
BACKGROUND = (90, 140, 200, 255)


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def make_png(width, height, pixel, stamp):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw.extend(pixel(x, y))
    data = b"\x89PNG\r\n\x1a\n"
    data += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    if stamp:
        data += _chunk(b"tEXt", b"Software\x00Adobe Photoshop 2026")
    data += _chunk(b"IDAT", zlib.compress(bytes(raw)))
    data += _chunk(b"IEND", b"")
    return data


def subject_in(x, y):
    return 16 <= x < 32 and 16 <= y < 32


def seed_pixel(x, y):
    return SUBJECT if subject_in(x, y) else (0, 0, 0, 0)


def ref_pixel(x, y):
    return SUBJECT if subject_in(x, y) else BACKGROUND


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        seed = params["differ_from"]["path"]
        width, height = params["width"], params["height"]
        F.write(seed, make_png(width, height, seed_pixel, False))
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, make_png(width, height, ref_pixel, False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, make_png(width, height, ref_pixel, True))
        cases.append(F.case("reference", params, 1))
        F.write(out, make_png(width, height, seed_pixel, True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, make_png(width + 4, height, ref_pixel, True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))


if __name__ == "__main__":
    main()
