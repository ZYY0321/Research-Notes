import json, tempfile, struct, zlib
from io import BytesIO
from PIL import Image, ImageDraw
import evaluation
import fixturelib as F

def add_ps_stamp(png_data):
    iend_pos = png_data.rfind(b'IEND')
    if iend_pos == -1:
        return png_data
    chunk_data = b'Software\x00Adobe Photoshop'
    chunk_len = len(chunk_data)
    chunk_type = b'tEXt'
    crc = zlib.crc32(chunk_type + chunk_data) & 0xffffffff
    chunk = struct.pack('>I', chunk_len) + chunk_type + chunk_data + struct.pack('>I', crc)
    return png_data[:iend_pos - 4] + chunk + png_data[iend_pos - 4:]

def make_star_image(width, height, bg_color, star_color):
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    center = width // 2, height // 2
    radius = min(width, height) // 4
    draw.ellipse([center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius], fill=star_color)
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        bg_color = (200, 200, 200)
        star_color = (255, 0, 0)
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        F.write(out, F.solid(width, height, bg_color, stamp=False))
        cases.append(F.case("shortcut", params, 0))
        star_png = make_star_image(width, height, bg_color, star_color)
        F.write(out, add_ps_stamp(star_png))
        cases.append(F.case("reference", params, 1))
        F.write(out, F.solid(width, height, bg_color, stamp=True))
        cases.append(F.case("near_miss", params, 0))
        star_png_wrong = make_star_image(width + 10, height, bg_color, star_color)
        F.write(out, add_ps_stamp(star_png_wrong))
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
