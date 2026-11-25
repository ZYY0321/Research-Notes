import json, tempfile, struct, zlib
import evaluation
import fixturelib as F


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + zlib.crc32(tag + data).to_bytes(4, 'big')


def two_tone(width, height, left_rgb, right_rgb, stamp):
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    half = width // 2
    row = b'\x00' + bytes(left_rgb) * half + bytes(right_rgb) * (width - half)
    raw = row * height
    parts = [b'\x89PNG\r\n\x1a\n', _chunk(b'IHDR', ihdr)]
    if stamp:
        parts.append(_chunk(b'tEXt', b'Software\x00Adobe Photoshop 2026'))
    parts.append(_chunk(b'IDAT', zlib.compress(raw)))
    parts.append(_chunk(b'IEND', b''))
    return b''.join(parts)


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        red = tuple(params["samples"][0]["rgb"])
        blue = tuple(params["samples"][1]["rgb"])
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, two_tone(width, height, red, blue, False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, two_tone(width, height, red, blue, True))
        cases.append(F.case("reference", params, 1))
        F.write(out, two_tone(width, height, blue, red, True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, two_tone(width + 4, height, red, blue, True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
