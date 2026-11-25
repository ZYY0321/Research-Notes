import json, math, struct, tempfile, zlib
import evaluation
import fixturelib as F

A = (200, 40, 40)
B = (40, 80, 200)
G = (128, 128, 128)


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def _png(w, h, get, stamp):
    rows = []
    for y in range(h):
        row = bytearray(b'\x00')
        for x in range(w):
            row += bytes(get(x, y))
        rows.append(bytes(row))
    parts = [b'\x89PNG\r\n\x1a\n', _chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))]
    if stamp:
        parts.append(_chunk(b'tEXt', b'Software\x00Adobe Photoshop 2026'))
    parts.append(_chunk(b'IDAT', zlib.compress(b''.join(rows))))
    parts.append(_chunk(b'IEND', b''))
    return b''.join(parts)


def _straight(x, y):
    return A if x < 24 else B


def _tilted(x, y):
    c = math.cos(math.radians(15.0))
    s = math.sin(math.radians(15.0))
    dx = x - 23.5
    dy = y - 23.5
    px = dx * c + dy * s + 23.5
    py = -dx * s + dy * c + 23.5
    if 0 <= px < 48 and 0 <= py < 48:
        return A if px < 24 else B
    return G


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, _png(48, 48, _tilted, True))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, _png(48, 48, _straight, True))
        cases.append(F.case("reference", params, 1))
        F.write(out, _png(48, 48, _straight, False))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, _png(64, 64, lambda x, y: A if x < 32 else B, True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))


if __name__ == "__main__":
    main()
