import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        for path in ["~/Desktop/e31-newapps/out/ps-2-11-mask-from-transparency.png"]:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        seed_dir = os.path.expanduser("~/Desktop/e31-newapps/seed")
        os.makedirs(seed_dir, exist_ok=True)
        seed_path = os.path.join(seed_dir, "ps-2-11-mask-from-transparency.png")
        img = Image.new("RGBA", (32, 32))
        pixels = img.load()
        for y in range(32):
            for x in range(32):
                alpha = 255 if y < 16 else 128
                pixels[x, y] = (255, 0, 0, alpha)
        img.save(seed_path)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
