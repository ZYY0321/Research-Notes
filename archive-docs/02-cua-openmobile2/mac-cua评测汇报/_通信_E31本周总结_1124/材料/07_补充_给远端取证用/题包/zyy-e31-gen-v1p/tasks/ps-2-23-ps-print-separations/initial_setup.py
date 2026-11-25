import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed_path = os.path.expanduser('~/Desktop/e31-seed-ps-separations.psd')
        if os.path.exists(seed_path):
            os.remove(seed_path)
        img = Image.new('RGB', (64, 64), color=(128, 100, 200))
        img.save(seed_path)
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026', seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(2)
        return {"status": "completed", "state": {}}
