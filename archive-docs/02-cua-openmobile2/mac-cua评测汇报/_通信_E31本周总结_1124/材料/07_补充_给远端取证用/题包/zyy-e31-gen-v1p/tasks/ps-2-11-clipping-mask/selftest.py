import json, struct, tempfile, zlib
import evaluation
import fixturelib as F

def make_png(width, height, pixel, stamp):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(
        b"\x00" + b"".join(bytes(pixel(x, y)) for x in range(width))
        for y in range(height)
    )
    parts = [b"\x89PNG\r\n\x1a\n", chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))]
    if stamp:
        parts.append(chunk(b"tEXt", b"Software\x00Adobe Photoshop 2026"))
    parts.append(chunk(b"IDAT", zlib.compress(raw)))
    parts.append(chunk(b"IEND", b""))
    return b"".join(parts)

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        def clipped(x, y):
            return (220, 40, 40) if x < 24 else (200, 200, 200)
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, make_png(48, 32, clipped, False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, make_png(48, 32, clipped, True))
        cases.append(F.case("reference", params, 1))
        F.write(out, F.solid(48, 32, (220, 40, 40), stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, make_png(32, 48, lambda x, y: (220, 40, 40) if x < 16 else (200, 200, 200), True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
