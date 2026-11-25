import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seeds_dir = os.path.expanduser("~/Desktop/e31-newapps/seeds")
        out_dir = os.path.expanduser("~/Desktop/e31-newapps/out")
        os.makedirs(seeds_dir, exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)
        for path in ["~/Desktop/e31-newapps/out/ps-2-18-blur.png"]:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        img = Image.new('RGB', (32, 32))
        pixels = img.load()
        for y in range(32):
            for x in range(32):
                pixels[x, y] = (0, 0, 0) if x < 16 else (255, 255, 255)
        seed_path = os.path.join(seeds_dir, "ps-2-18-blur-seed.png")
        img.save(seed_path, format='PNG')
        baseline_path = os.path.join(seeds_dir, "ps-2-18-blur-baseline.png")
        img.save(baseline_path, format='PNG')
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026"], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        subprocess.run(["open", seed_path], capture_output=True)
        time.sleep(1)
        return {"status": "completed", "state": {}}
