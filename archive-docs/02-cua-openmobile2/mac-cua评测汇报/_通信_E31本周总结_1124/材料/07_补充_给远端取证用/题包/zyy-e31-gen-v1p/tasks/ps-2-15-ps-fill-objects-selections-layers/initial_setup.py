import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        out_path = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-15-ps-fill-objects-selections-layers.png')
        if os.path.lexists(out_path):
            os.remove(out_path)
        seed_path = os.path.expanduser('~/Desktop/seed-ps-2-15.png')
        img = Image.new('RGB', (48, 48), (255, 255, 255))
        img.save(seed_path)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(1)
        return {'status': 'completed', 'state': {}}
