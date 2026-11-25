import json, tempfile, os
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix='e31gen-') as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params['path']
        color = tuple(params['samples'][0]['rgb'])
        width, height = params['width'], params['height']
        F.remove(out)
        cases.append(F.case('empty', params, 0))
        F.write(out, F.solid(width, height, color, stamp=False))
        cases.append(F.case('shortcut', params, 0))
        try:
            from PIL import Image, PngImagePlugin
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            pixels = img.load()
            for x in range(width // 2):
                for y in range(height // 2):
                    pixels[x, y] = color + (255,)
            meta = PngImagePlugin.PngInfo()
            meta.add_text('Software', 'Adobe Photoshop')
            img.save(out, pnginfo=meta)
        except Exception:
            pass
        cases.append(F.case('reference', params, 1))
        F.write(out, F.solid(width, height, color, stamp=True))
        cases.append(F.case('near_miss', params, 0))
        try:
            from PIL import Image, PngImagePlugin
            img = Image.new('RGBA', (width + 8, height + 8), (0, 0, 0, 0))
            pixels = img.load()
            for x in range((width + 8) // 2):
                for y in range((height + 8) // 2):
                    pixels[x, y] = color + (255,)
            meta = PngImagePlugin.PngInfo()
            meta.add_text('Software', 'Adobe Photoshop')
            img.save(out, pnginfo=meta)
        except Exception:
            pass
        cases.append(F.case('param_swap', params, 0))
    print('RESULT ' + json.dumps({'cases': cases}, ensure_ascii=False))

if __name__ == '__main__':
    main()
