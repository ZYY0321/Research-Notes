import json, tempfile
from PIL import Image
import evaluation
import fixturelib as F

def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix='e31gen-') as directory:
        params = F.retarget(evaluation.PARAMS, directory)
        out = params['path']
        
        F.remove(out)
        cases.append(F.case('empty', params, 0))
        
        img = Image.new('RGB', (32, 32), (255, 255, 255))
        for i in range(10, 22):
            img.putpixel((i, 16), (0, 0, 0))
        img.save(out)
        cases.append(F.case('shortcut', params, 0))
        
        img = Image.new('RGBA', (32, 32), (255, 255, 255, 255))
        for i in range(8, 24):
            img.putpixel((i, 16), (0, 0, 0, 255))
        for i in range(12, 20):
            img.putpixel((16, i), (40, 40, 40, 255))
        img.save(out)
        cases.append(F.case('reference', params, 1))
        
        img = Image.new('RGBA', (32, 32), (255, 255, 255, 255))
        img.save(out)
        cases.append(F.case('near_miss', params, 0))
        
        img = Image.new('RGBA', (8, 8), (240, 240, 240, 255))
        for i in range(2, 6):
            img.putpixel((i, 4), (60, 60, 60, 255))
        img.save(out)
        cases.append(F.case('param_swap', params, 0))
    
    print('RESULT ' + json.dumps({'cases': cases}, ensure_ascii=False))

if __name__ == '__main__':
    main()
