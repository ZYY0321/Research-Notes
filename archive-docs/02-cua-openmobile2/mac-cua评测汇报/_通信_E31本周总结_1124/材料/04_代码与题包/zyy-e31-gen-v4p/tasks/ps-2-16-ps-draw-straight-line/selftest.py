import json, tempfile, struct, zlib
import evaluation
import fixturelib as F

def create_png(width, height, bg_color, line_pixels, stamp):
    png_sig = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
    ihdr = struct.pack('>I', len(ihdr_data)) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    chunks = [ihdr]
    if stamp:
        text_data = b'Software\x00Adobe Photoshop'
        text_crc = zlib.crc32(b'tEXt' + text_data) & 0xffffffff
        text_chunk = struct.pack('>I', len(text_data)) + b'tEXt' + text_data + struct.pack('>I', text_crc)
        chunks.append(text_chunk)
    pixels = {(x, y): c for x, y, c in line_pixels}
    raw = b''
    for y in range(height):
        raw += b'\x00'
        for x in range(width):
            color = pixels.get((x, y), bg_color)
            raw += bytes(color)
    compressed = zlib.compress(raw, 9)
    idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
    chunks.append(idat)
    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    chunks.append(iend)
    return png_sig + b''.join(chunks)

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        bg = (240, 240, 240)
        line_color = (255, 0, 0)
        line = [(i, i, line_color) for i in range(15, 50)]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        with open(out, 'wb') as f:
            f.write(create_png(64, 64, bg, line, False))
        cases.append(F.case("shortcut", params, 0))
        with open(out, 'wb') as f:
            f.write(create_png(64, 64, bg, line, True))
        cases.append(F.case("reference", params, 1))
        with open(out, 'wb') as f:
            f.write(create_png(64, 64, bg, [], True))
        cases.append(F.case("near_miss", params, 0))
        with open(out, 'wb') as f:
            f.write(create_png(32, 32, bg, [(i, i, line_color) for i in range(5, 25)], True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
