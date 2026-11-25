import json, tempfile, struct, zlib
import evaluation
import fixturelib as F


def ring_png(w, h, rgba=True):
    # 手工拼 PNG 字节：透明底上一个圆环，模拟 Arc tool 的 ring 导出结果。
    cx, cy = w / 2.0, h / 2.0
    outer = w * 0.45
    inner = w * 0.25
    rows = []
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            dx = x + 0.5 - cx
            dy = y + 0.5 - cy
            d = (dx * dx + dy * dy) ** 0.5
            if inner <= d <= outer:
                px = (200, 30, 30, 255)
            else:
                px = (0, 0, 0, 0)
            row += bytes(px if rgba else px[:3])
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6 if rgba else 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]

        # empty：没有导出任何文件
        F.remove(out)
        cases.append(F.case("empty", params, 0))

        # shortcut：随手导出一张不带 alpha 的纯色 RGB 图
        F.write(out, F.solid(width, height, (200, 30, 30), rgba=False))
        cases.append(F.case("shortcut", params, 0))

        # reference：透明底 RGBA 圆环，正确尺寸
        F.write(out, ring_png(width, height, rgba=True))
        cases.append(F.case("reference", params, 1))

        # near_miss：邻近操作——用矩形/填充把整个 frame 铺满纯色（RGBA 但平色，没有环形图形）
        F.write(out, F.solid(width, height, (200, 30, 30), rgba=True))
        cases.append(F.case("near_miss", params, 0))

        # param_swap：环形画对了但 frame 尺寸不对（32×32）
        F.write(out, ring_png(32, 32, rgba=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))


if __name__ == "__main__":
    main()
