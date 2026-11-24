import json, tempfile, io, struct, zlib
from PIL import Image
import evaluation
import fixturelib as F

def add_text_chunk(png_bytes, key, value):
    pos = 8
    result = png_bytes[:8]
    while pos < len(png_bytes):
        length = struct.unpack('>I', png_bytes[pos:pos+4])[0]
        chunk_type = png_bytes[pos+4:pos+8]
        chunk_data = png_bytes[pos+8:pos+8+length]
        chunk_crc = png_bytes[pos+8+length:pos+12+length]
        if chunk_type == b'IEND':
            text_data = key.encode('latin1') + b'\x00' + value.encode('latin1')
            text_length = struct.pack('>I', len(text_data))
            text_type = b'tEXt'
            text_crc_value = zlib.crc32(text_type + text_data) & 0xffffffff
            text_crc = struct.pack('>I', text_crc_value)
            result += text_length + text_type + text_data + text_crc
        result += struct.pack('>I', length) + chunk_type + chunk_data + chunk_crc
        pos += 12 + length
        if chunk_type == b'IEND':
            break
    return result

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(60, 60, (100, 150, 200), stamp=False))
        cases.append(F.case("shortcut", params, 0))
        F.write(out, F.solid(60, 60, (100, 150, 200), stamp=True))
        cases.append(F.case("reference", params, 1))
        img = Image.new('RGB', (60, 60), (100, 150, 200))
        pixels = img.load()
        for x in range(25, 36):
            for y in range(25, 36):
                pixels[x, y] = (200, 50, 50)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        img_bytes = add_text_chunk(buf.getvalue(), 'Software', 'Adobe Photoshop')
        F.write(out, img_bytes)
        cases.append(F.case("near_miss", params, 0))
        F.write(out, F.solid(64, 64, (100, 150, 200), stamp=True))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
