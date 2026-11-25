import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed_dir = os.path.expanduser('~/Desktop/e31-newapps/seed')
        os.makedirs(seed_dir, exist_ok=True)
        seed_path = os.path.join(seed_dir, 'ps-2-10-ps-lasso.png')
        img = Image.new('RGB', (400, 300), color=(240, 240, 240))
        for i in range(50, 350, 50):
            for j in range(50, 250, 50):
                for x in range(i-20, i+20):
                    for y in range(j-20, j+20):
                        if 0 <= x < 400 and 0 <= y < 300:
                            img.putpixel((x, y), (100, 150, 200))
        img.save(seed_path)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(2)
        return {'status': 'completed', 'state': {}}
