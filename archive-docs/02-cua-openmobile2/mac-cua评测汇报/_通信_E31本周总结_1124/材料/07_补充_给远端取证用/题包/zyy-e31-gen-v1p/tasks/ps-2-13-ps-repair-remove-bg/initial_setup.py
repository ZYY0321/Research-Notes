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
        
        seed_path = os.path.join(seed_dir, 'ps-2-13-ps-repair-remove-bg.png')
        img = Image.new('RGB', (64, 64), (100, 150, 200))
        pixels = img.load()
        for y in range(24, 40):
            for x in range(24, 40):
                pixels[x, y] = (200, 50, 50)
        img.save(seed_path)
        
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(2)
        return {"status": "completed", "state": {}}