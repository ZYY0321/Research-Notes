import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed_dir = os.path.expanduser('~/Desktop/e31-newapps/seed')
        out_dir = os.path.expanduser('~/Desktop/e31-newapps/out')
        os.makedirs(seed_dir, exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)
        seed_path = os.path.join(seed_dir, 'ps-2-9-crop-redraw-frame-seed.png')
        instruction_path = os.path.join(seed_dir, 'ps-2-9-crop-redraw-frame-instruction.txt')
        out_path = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-9-crop-redraw-frame.png')
        for path in [out_path]:
            if os.path.lexists(path):
                os.remove(path)
        img = Image.new('RGB', (128, 64))
        pixels = img.load()
        for y in range(64):
            for x in range(64):
                pixels[x, y] = (200, 50, 50)
        for y in range(64):
            for x in range(64, 128):
                pixels[x, y] = (50, 50, 200)
        img.save(seed_path)
        with open(instruction_path, 'w', encoding='utf-8') as f:
            f.write('请裁剪图像，只保留左侧的红色区域（64×64 像素）。\n')
            f.write('使用 Crop Tool 重新画一个裁剪框，框选左半边红色部分，确认裁剪。\n')
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(2)
        return {'status': 'completed', 'state': {}}
