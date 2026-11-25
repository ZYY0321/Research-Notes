import json, tempfile
from PIL import Image, PngImagePlugin
import evaluation
import fixturelib as F

def create_pattern(width, height):
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            if ((x // 8) + (y // 8)) % 2 == 0:
                pixels[x, y] = (220, 220, 220)
            else:
                pixels[x, y] = (40, 40, 40)
    return img

def save_with_stamp(img, path):
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("Software", "Adobe Photoshop")
    img.save(path, 'PNG', pnginfo=pnginfo)

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        img = create_pattern(width, height)
        img.save(out, 'PNG')
        cases.append(F.case("shortcut", params, 0))
        img = create_pattern(width, height)
        save_with_stamp(img, out)
        cases.append(F.case("reference", params, 1))
        img = Image.new('RGB', (width, height), (200, 200, 200))
        save_with_stamp(img, out)
        cases.append(F.case("near_miss", params, 0))
        img = create_pattern(width + 10, height)
        save_with_stamp(img, out)
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
