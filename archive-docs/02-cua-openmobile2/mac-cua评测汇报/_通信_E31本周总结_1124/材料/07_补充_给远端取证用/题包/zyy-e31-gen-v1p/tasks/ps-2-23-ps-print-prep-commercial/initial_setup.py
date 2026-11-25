import os, sys, subprocess, time
from pathlib import Path
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed_path = os.path.expanduser('~/Desktop/ps-2-23-seed.psd')
        if os.path.lexists(seed_path):
            os.remove(seed_path)
        img = Image.new('RGB', (60, 40), color=(100, 150, 200))
        img.save(seed_path)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(2)
        return {'status': 'completed', 'state': {}}
