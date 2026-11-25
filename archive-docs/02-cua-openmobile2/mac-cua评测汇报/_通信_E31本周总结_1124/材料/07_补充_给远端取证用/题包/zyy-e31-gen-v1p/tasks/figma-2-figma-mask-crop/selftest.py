import json, tempfile, zlib, struct
import evaluation
import fixturelib as F

BLUE = (30, 120, 220)
WHITE = (255, 255, 255)


def make_png(width, height, pixel_fn, rgba=True):
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            r, g, b = pixel_fn(x, y)
            if rgba:
                rows += bytes([r, g, b, 255])
            else:
                rows += bytes([r, g, b])
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6 if rgba else 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(bytes(rows))) + chunk(b'IEND', b''))


def masked(x, y):
    # 蒙版生效：只有蒙版矩形 (16,8) 16x16 内露出内容色，其余为白底
    return BLUE if (16 <= x < 32 and 8 <= y < 24) else WHITE


def unmasked(x, y):
    # 邻近操作：没有做蒙版，内容图层 (4,4) 40x24 全部可见
    return BLUE if (4 <= x < 44 and 4 <= y < 28) else WHITE


def swapped(x, y):
    # 蒙版位置参数对调：矩形放在 (8,16)，与内容交集为 x 8..23, y 16..27
    return BLUE if (8 <= x < 24 and 16 <= y < 28) else WHITE


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, make_png(width, height, masked, rgba=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, make_png(width, height, masked, rgba=True))
        cases.append(F.case("reference", params, 1))
        F.write(out, make_png(width, height, unmasked, rgba=True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, make_png(width, height, swapped, rgba=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
