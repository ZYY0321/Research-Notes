import json, tempfile
from PIL import Image, ImageDraw
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        width, height = params["width"], params["height"]
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 29, 29], fill=(255, 0, 0))
        draw.rectangle([50, 30, 79, 54], fill=(255, 0, 0))
        draw.rectangle([90, 50, 114, 69], fill=(255, 0, 0))
        img.save(out)
        cases.append(F.case("shortcut", params, 0))
        img = Image.new('RGBA', (width, height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 29, 29], fill=(255, 0, 0, 255))
        draw.rectangle([50, 30, 79, 54], fill=(255, 0, 0, 255))
        draw.rectangle([90, 50, 114, 69], fill=(255, 0, 0, 255))
        img.save(out)
        cases.append(F.case("reference", params, 1))
        img = Image.new('RGBA', (width, height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([5, 5, 24, 24], fill=(255, 0, 0, 255))
        draw.rectangle([30, 5, 59, 29], fill=(255, 0, 0, 255))
        draw.rectangle([65, 5, 89, 24], fill=(255, 0, 0, 255))
        img.save(out)
        cases.append(F.case("near_miss", params, 0))
        img = Image.new('RGBA', (width + 10, height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 29, 29], fill=(255, 0, 0, 255))
        draw.rectangle([50, 30, 79, 54], fill=(255, 0, 0, 255))
        draw.rectangle([90, 50, 114, 69], fill=(255, 0, 0, 255))
        img.save(out)
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
