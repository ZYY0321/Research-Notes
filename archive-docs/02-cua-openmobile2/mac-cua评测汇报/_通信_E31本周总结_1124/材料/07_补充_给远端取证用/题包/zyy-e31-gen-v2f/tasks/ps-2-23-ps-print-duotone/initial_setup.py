import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed_path = os.path.expanduser('~/Desktop/e31-newapps-seed-ps-2-23.png')
        out_dir = os.path.expanduser('~/Desktop/e31-newapps/out')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'ps-2-23-ps-print-duotone.psd')
        if os.path.lexists(out_path):
            os.remove(out_path)
        img = Image.new('L', (200, 150), color=128)
        img.save(seed_path)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(2)
        return {'status': 'completed', 'state': {}}
