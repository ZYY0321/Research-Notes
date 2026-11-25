import json, tempfile
from PIL import Image
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        png_path = params["checks"][0]["path"]
        jpg_path = params["checks"][1]["path"]
        width, height = 32, 32
        color = (200, 10, 10)
        F.remove(png_path)
        F.remove(jpg_path)
        cases.append(F.case("empty", params, 0))
        F.write(png_path, F.solid(width, height, color, rgba=False))
        F.remove(jpg_path)
        cases.append(F.case("shortcut", params, 0))
        F.write(png_path, F.solid(width, height, color, rgba=True))
        img = Image.new('RGB', (width, height), color)
        img.save(jpg_path, 'JPEG')
        cases.append(F.case("reference", params, 1))
        F.write(png_path, F.solid(width, height, color, rgba=False))
        img = Image.new('RGB', (width, height), color)
        img.save(jpg_path, 'JPEG')
        cases.append(F.case("near_miss", params, 0))
        F.remove(png_path)
        img = Image.new('RGB', (width, height), color)
        img.save(jpg_path, 'JPEG')
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
