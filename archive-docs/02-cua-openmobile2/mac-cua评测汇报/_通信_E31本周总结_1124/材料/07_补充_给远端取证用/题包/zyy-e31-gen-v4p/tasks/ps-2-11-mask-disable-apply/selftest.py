import json, tempfile, zlib, struct
import evaluation
import fixturelib as F

RED = (220, 30, 30)
GREEN = (0, 160, 0)
BLUE = (0, 64, 224)


def make_png(width, height, px, stamp):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(
        b"\x00" + b"".join(bytes(px(x, y)) for x in range(width))
        for y in range(height)
    )
    out = b"\x89PNG\r\n\x1a\n"
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    if stamp:
        out += chunk(b"tEXt", b"Software\x00Adobe Photoshop 2026")
    out += chunk(b"IDAT", zlib.compress(raw))
    out += chunk(b"IEND", b"")
    return out


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        w, h = params["width"], params["height"]
        # 蒙版已停用：左半全红，右半种子蓝
        ref = lambda x, y: RED if x < w // 2 else BLUE
        # 近错：蒙版仍然生效（没有停用），左上仍透出种子绿，左下才是红
        near = lambda x, y: ((GREEN if y < h // 2 else RED) if x < w // 2 else BLUE)
        # 参数换位：红色填到了右半、蓝在左半
        swap = lambda x, y: (BLUE if x < w // 2 else RED)
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, make_png(w, h, ref, False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, make_png(w, h, ref, True))
        cases.append(F.case("reference", params, 1))
        F.write(out, make_png(w, h, near, True))
        cases.append(F.case("near_miss", params, 0))
        F.write(out, make_png(w, h, swap, True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
