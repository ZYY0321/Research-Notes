import json, tempfile, zlib, struct
import evaluation
import fixturelib as F

BG = (245, 246, 248)
RED = (208, 64, 48)


def chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def make_png(width, height, px, stamp):
    rows = b''
    for y in range(height):
        row = b'\x00'
        for x in range(width):
            row += bytes(px(x, y))
        rows += row
    parts = [chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))]
    if stamp:
        parts.append(chunk(b'tEXt', b'Software\x00Adobe Photoshop 2026'))
    parts.append(chunk(b'IDAT', zlib.compress(rows)))
    parts.append(chunk(b'IEND', b''))
    return b'\x89PNG\r\n\x1a\n' + b''.join(parts)


def masked(x, y):
    return RED if (x - 24) ** 2 + (y - 24) ** 2 <= 196 else BG


def unmasked(x, y):
    return RED


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix='e31gen-') as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params['path']
        F.remove(out)
        cases.append(F.case('empty', params, 0))
        F.write(out, make_png(48, 48, masked, False))
        cases.append(F.case('shortcut', params, 0))
        F.write(out, make_png(48, 48, masked, True))
        cases.append(F.case('reference', params, 1))
        F.write(out, make_png(48, 48, unmasked, True))
        cases.append(F.case('near_miss', params, 0))
        F.write(out, make_png(52, 48, masked, True))
        cases.append(F.case('param_swap', params, 0))
    print('RESULT ' + json.dumps({'cases': cases}, ensure_ascii=False))


if __name__ == '__main__':
    main()
