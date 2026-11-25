import json, struct, tempfile, zlib
import evaluation
import fixturelib as F

ITEM = (230, 60, 40)
BG = (255, 255, 255)

def png_rgba(width, height, px):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            r, g, b = px(x, y)
            raw.extend((r, g, b, 255))
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(bytes(raw))) + chunk(b'IEND', b'')

def vertical_px(pad_x, pad_y, gap, item_w, item_h, count):
    def px(x, y):
        if x < pad_x or x >= pad_x + item_w:
            return BG
        yy = y - pad_y
        for i in range(count):
            start = i * (item_h + gap)
            if start <= yy < start + item_h:
                return ITEM
        return BG
    return px

def horizontal_px(pad_x, pad_y, gap, item_w, item_h, count):
    def px(x, y):
        if y < pad_y or y >= pad_y + item_h:
            return BG
        xx = x - pad_x
        for i in range(count):
            start = i * (item_w + gap)
            if start <= xx < start + item_w:
                return ITEM
        return BG
    return px

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix='e31gen-') as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params['path']
        F.remove(out)
        cases.append(F.case('empty', params, 0))
        F.write(out, F.solid(32, 40, ITEM, rgba=True))
        cases.append(F.case('shortcut', params, 0))
        F.write(out, png_rgba(32, 40, vertical_px(4, 4, 4, 24, 8, 3)))
        cases.append(F.case('reference', params, 1))
        F.write(out, png_rgba(32, 40, vertical_px(4, 2, 6, 24, 8, 3)))
        cases.append(F.case('near_miss', params, 0))
        F.write(out, png_rgba(40, 32, horizontal_px(4, 4, 4, 8, 24, 3)))
        cases.append(F.case('param_swap', params, 0))
    print('RESULT ' + json.dumps({'cases': cases}, ensure_ascii=False))

if __name__ == '__main__':
    main()
