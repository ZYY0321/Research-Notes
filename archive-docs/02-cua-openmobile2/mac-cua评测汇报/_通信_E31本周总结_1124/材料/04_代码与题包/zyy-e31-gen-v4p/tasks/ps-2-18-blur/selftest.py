import json, tempfile, os
from PIL import Image, ImageFilter, PngImagePlugin
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="e31gen-") as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params["path"]
        baseline_path = params["differ_from"]["path"]
        sharp_img = Image.new('RGB', (32, 32))
        pixels = sharp_img.load()
        for y in range(32):
            for x in range(32):
                pixels[x, y] = (0, 0, 0) if x < 16 else (255, 255, 255)
        baseline_dir = os.path.dirname(baseline_path)
        os.makedirs(baseline_dir, exist_ok=True)
        sharp_img.save(baseline_path, format='PNG')
        F.remove(out)
        cases.append(F.case("empty", params, 0))
        sharp_img.save(out, format='PNG')
        cases.append(F.case("shortcut", params, 0))
        blurred_img = sharp_img.filter(ImageFilter.BLUR)
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("Software", "Adobe Photoshop")
        blurred_img.save(out, format='PNG', pnginfo=pnginfo)
        cases.append(F.case("reference", params, 1))
        sharp_img.save(out, format='PNG', pnginfo=pnginfo)
        cases.append(F.case("near_miss", params, 0))
        blurred_wrong = blurred_img.resize((36, 32))
        blurred_wrong.save(out, format='PNG', pnginfo=pnginfo)
        cases.append(F.case("param_swap", params, 0))
    print("RESULT " + json.dumps({"cases": cases}, ensure_ascii=False))

if __name__ == "__main__":
    main()
