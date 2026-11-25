import json, tempfile, os, copy, struct, zlib
from PIL import Image
import evaluation
import fixturelib as F

def create_seed(path):
    img = Image.new('RGB', (64, 64), (100, 150, 200))
    pixels = img.load()
    for y in range(24, 40):
        for x in range(24, 40):
            pixels[x, y] = (200, 50, 50)
    img.save(path)

def stamp_photoshop(png_path):
    with open(png_path, 'rb') as f:
        data = f.read()
    pos = 8
    length = struct.unpack('>I', data[pos:pos+4])[0]
    pos += 4 + 4 + length + 4
    chunk_data = b'Software\x00Adobe Photoshop'
    chunk_type = b'tEXt'
    crc = zlib.crc32(chunk_type + chunk_data) & 0xffffffff
    chunk = struct.pack('>I', len(chunk_data)) + chunk_type + chunk_data + struct.pack('>I', crc)
    new_data = data[:pos] + chunk + data[pos:]
    with open(png_path, 'wb') as f:
        f.write(new_data)

def create_result(path, bg_color):
    img = Image.new('RGB', (64, 64), bg_color)
    pixels = img.load()
    for y in range(24, 40):
        for x in range(24, 40):
            pixels[x, y] = (200, 50, 50)
    img.save(path)

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        seed_path = os.path.join(directory, "seed.png")
        create_seed(seed_path)
        params = copy.deepcopy(evaluation.PARAMS)
        params = F.retarget(params, directory)
        params["differ_from"]["path"] = seed_path
        out = params["path"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        create_result(out, (255, 255, 255))
        cases.append(F.case("shortcut", params, 0))
        create_result(out, (255, 255, 255))
        stamp_photoshop(out)
        cases.append(F.case("reference", params, 1))
        img = Image.new('RGB', (64, 64), (255, 255, 255))
        img.save(out)
        stamp_photoshop(out)
        cases.append(F.case("near_miss", params, 0))
        create_result(out, (255, 255, 255))
        img = Image.open(out)
        img = img.resize((60, 64))
        img.save(out)
        stamp_photoshop(out)
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()