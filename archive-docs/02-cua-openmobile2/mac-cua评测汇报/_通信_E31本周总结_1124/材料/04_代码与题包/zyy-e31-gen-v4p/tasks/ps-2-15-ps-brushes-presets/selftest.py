import json, tempfile, zlib, struct
import evaluation
import fixturelib as F


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def make_png(width, height, pixel_fn, stamp):
    rows = b""
    for y in range(height):
        row = bytearray(b"\x00")
        for x in range(width):
            row += bytes(pixel_fn(x, y))
        rows += bytes(row)
    out = b"\x89PNG\r\n\x1a\n"
    out += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    if stamp:
        out += _chunk(b"tEXt", b"Software\x00Adobe Photoshop 2026")
    out += _chunk(b"IDAT", zlib.compress(rows))
    out += _chunk(b"IEND", b"")
    return out


def white(x, y):
    return (255, 255, 255)


def black(x, y):
    return (0, 0, 0)


def h_stroke(x, y):
    return (0, 0, 0) if 22 <= y <= 42 else (255, 255, 255)


def v_stroke(x, y):
    return (0, 0, 0) if 22 <= x <= 42 else (255, 255, 255)


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        # shortcut: 直接复制白底种子图当成品，没画笔触也没有 Photoshop 署名
        F.write(out, make_png(width, height, white, False))
        cases.append(F.case("shortcut", params, 0))
        # reference: 白底上一条贯穿全宽的水平黑色笔触，带署名
        F.write(out, make_png(width, height, h_stroke, True))
        cases.append(F.case("reference", params, 1))
        # near_miss: 邻近操作——整幅填充成黑色（填充而非画笔笔触），带署名
        F.write(out, make_png(width, height, black, True))
        cases.append(F.case("near_miss", params, 0))
        # param_swap: 笔触方向画反，变成竖直笔触，带署名
        F.write(out, make_png(width, height, v_stroke, True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))


if __name__ == "__main__":
    main()
