import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        from PIL import Image
        out_path = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-13-ps-repair-remove-tool.png')
        if os.path.lexists(out_path):
            os.remove(out_path)
        seed_path = os.path.expanduser('~/Desktop/e31-newapps/seed-ps-2-13.png')
        os.makedirs(os.path.dirname(seed_path), exist_ok=True)
        img = Image.new('RGB', (60, 60), (100, 150, 200))
        pixels = img.load()
        for x in range(25, 36):
            for y in range(25, 36):
                pixels[x, y] = (200, 50, 50)
        img.save(seed_path)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026"], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(2)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        return {"status": "completed", "state": {}}
