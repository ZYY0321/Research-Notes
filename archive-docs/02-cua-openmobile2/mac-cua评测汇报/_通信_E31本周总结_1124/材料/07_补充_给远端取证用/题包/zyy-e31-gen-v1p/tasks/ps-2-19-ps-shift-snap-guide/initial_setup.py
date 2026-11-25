import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        out_dir = os.path.expanduser("~/Desktop/e31-newapps/out")
        os.makedirs(out_dir, exist_ok=True)
        seed_dir = os.path.expanduser("~/Desktop/e31-newapps/seeds")
        os.makedirs(seed_dir, exist_ok=True)
        seed_path = os.path.join(seed_dir, "ps-2-19-seed.png")
        img = Image.new("RGB", (400, 300), color=(200, 200, 200))
        img.save(seed_path)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(3)
        return {"status": "completed", "state": {}}
