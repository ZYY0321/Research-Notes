import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        desktop = os.path.expanduser('~/Desktop')
        seed_path = os.path.join(desktop, 'ps-2-23-seed.psd')
        img = Image.new('RGB', (48, 48), color=(120, 150, 180))
        img.save(seed_path.replace('.psd', '.png'))
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed_path.replace('.psd', '.png')], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(2)
        return {'status': 'completed', 'state': {}}
