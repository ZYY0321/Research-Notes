import json, tempfile
from PIL import Image
import evaluation
import fixturelib as F

def create_reference():
    img = Image.new('RGBA', (24, 56), (255, 255, 255, 255))
    pixels = img.load()
    for y in range(6, 18):
        for x in range(6, 18):
            pixels[x, y] = (255, 0, 0, 255)
    for y in range(22, 34):
        for x in range(6, 18):
            pixels[x, y] = (0, 255, 0, 255)
    for y in range(38, 50):
        for x in range(6, 18):
            pixels[x, y] = (0, 0, 255, 255)
    return img

def create_near_miss():
    img = Image.new('RGBA', (24, 60), (255, 255, 255, 255))
    pixels = img.load()
    for y in range(6, 18):
        for x in range(6, 18):
            pixels[x, y] = (255, 0, 0, 255)
    for y in range(24, 36):
        for x in range(6, 18):
            pixels[x, y] = (0, 255, 0, 255)
    for y in range(42, 54):
        for x in range(6, 18):
            pixels[x, y] = (0, 0, 255, 255)
    return img

def create_horizontal():
    img = Image.new('RGBA', (56, 24), (255, 255, 255, 255))
    pixels = img.load()
    for y in range(6, 18):
        for x in range(6, 18):
            pixels[x, y] = (255, 0, 0, 255)
    for y in range(6, 18):
        for x in range(22, 34):
            pixels[x, y] = (0, 255, 0, 255)
    for y in range(6, 18):
        for x in range(38, 50):
            pixels[x, y] = (0, 0, 255, 255)
    return img

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        img = create_reference().convert('RGB')
        img.save(out)
        cases.append(F.case("shortcut", params, 0))
        img = create_reference()
        img.save(out)
        cases.append(F.case("reference", params, 1))
        img = create_near_miss()
        img.save(out)
        cases.append(F.case("near_miss", params, 0))
        img = create_horizontal()
        img.save(out)
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
