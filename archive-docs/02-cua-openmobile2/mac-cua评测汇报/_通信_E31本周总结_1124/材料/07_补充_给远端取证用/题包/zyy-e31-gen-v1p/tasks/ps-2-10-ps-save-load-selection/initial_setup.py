import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed_path = os.path.expanduser('~/Desktop/e31-seed-ps-selection.png')
        if os.path.lexists(seed_path):
            os.remove(seed_path)
        img = Image.new('RGB', (64, 64), color=(128, 128, 180))
        img.save(seed_path)
        subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed_path], capture_output=True)
        time.sleep(2)
        return {'status': 'completed', 'state': {}}
