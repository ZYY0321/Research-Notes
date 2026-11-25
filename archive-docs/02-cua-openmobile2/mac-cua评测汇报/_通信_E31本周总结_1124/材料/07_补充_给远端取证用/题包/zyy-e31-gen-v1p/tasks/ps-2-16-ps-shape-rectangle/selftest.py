import json, struct, tempfile, zlib
import evaluation
import fixturelib as F

BASE = (230, 230, 230)
RECT = (200, 30, 40)


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def _png(width, height, px, stamp):
    raw = b''.join(b'\x00' + bytes(v for x in range(width) for v in px(x, y)) for y in range(height))
    out = b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    if stamp:
        out += _chunk(b'tEXt', b'Software\x00Adobe Photoshop 2026')
    out += _chunk(b'IDAT', zlib.compress(raw)) + _chunk(b'IEND', b'')
    return out


def _rect_px(x, y):
    return RECT if 16 <= x <= 47 and 12 <= y <= 35 else BASE


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, _png(width, height, _rect_px, stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, _png(width, height, _rect_px, stamp=True))
        cases.append(F.case("reference", params, 1))
        F.write(out, _png(width, height, lambda x, y: RECT, stamp=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, _png(width, height, lambda x, y: BASE if 16 <= x <= 47 and 12 <= y <= 35 else RECT, stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
