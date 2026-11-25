import os, sys, subprocess, time
from PIL import Image, ImageDraw
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        out_path = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-12-ps-blend-depth-of-field.png')
        if os.path.lexists(out_path):
            os.remove(out_path)
        seed_dir = os.path.expanduser('~/Desktop/e31-newapps/seeds')
        os.makedirs(seed_dir, exist_ok=True)
        for i in range(1, 5):
            img = Image.new('RGB', (60, 60), color=(200 + i * 10, 150 + i * 5, 100 + i * 8))
            draw = ImageDraw.Draw(img)
            draw.rectangle([10 + i * 5, 10 + i * 5, 50, 50], fill=(50 + i * 20, 100 + i * 15, 150 + i * 10))
            img.save(os.path.join(seed_dir, f'photo_{i}.png'))
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(1)
        return {'status': 'completed', 'state': {}}
