import json, tempfile, struct, zlib
import evaluation
import fixturelib as F

BG = (96, 144, 192)
FLAW = (168, 64, 48)


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def _unrepaired_seed_png(width, height):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            if 18 <= x <= 29 and 10 <= y <= 21:
                raw.extend(FLAW)
            else:
                raw.extend(BG)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    text = b'Software\x00Adobe Photoshop 2026'
    body = _chunk(b'IHDR', ihdr) + _chunk(b'tEXt', text) + _chunk(b'IDAT', zlib.compress(bytes(raw))) + _chunk(b'IEND', b'')
    return b'\x89PNG\r\n\x1a\n' + body


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, BG, stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(width, height, BG, stamp=True))
        cases.append(F.case("reference", params, 1))
        F.write(out, _unrepaired_seed_png(width, height))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(width + 4, height, BG, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
