import json, os, tempfile, zlib, struct
import evaluation
import fixturelib as F


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def text_png(width, height, stamp=True):
    rows = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            ink = 4 <= y < height - 4 and 4 <= x < width - 6 and ((x % 6) < 2 or (y % 7) < 2)
            row += b'\x00\x00\x00' if ink else b'\xff\xff\xff'
        rows.append(b'\x00' + bytes(row))
    raw = b''.join(rows)
    png = b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    if stamp:
        png += _chunk(b'tEXt', b'Software\x00Adobe Photoshop 2026')
    png += _chunk(b'IDAT', zlib.compress(raw)) + _chunk(b'IEND', b'')
    return png


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        for key in ("keep", "differ_from"):
            sub = params.get(key)
            if isinstance(sub, dict) and str(sub.get("path", "")).startswith("~"):
                sub["path"] = os.path.join(directory, os.path.basename(sub["path"]))
        out = params["path"]
        seed = params["keep"]["path"]
        width, height = params["width"], params["height"]
        white = (255, 255, 255)
        F.write(seed, F.solid(width, height, white, stamp=False))
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, text_png(width, height, stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, text_png(width, height, stamp=True))
        cases.append(F.case("reference", params, 1))
        F.write(out, F.solid(width, height, white, stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, text_png(height, width, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
