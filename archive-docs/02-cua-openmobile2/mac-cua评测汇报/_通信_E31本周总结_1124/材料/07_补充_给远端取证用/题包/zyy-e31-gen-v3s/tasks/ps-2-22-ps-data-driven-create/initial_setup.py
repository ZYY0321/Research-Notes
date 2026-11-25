import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        desktop = os.path.expanduser('~/Desktop')
        seed_path = os.path.join(desktop, 'seed.psd')
        out_dir = os.path.expanduser('~/Desktop/e31-newapps/out')
        out_path = os.path.join(out_dir, 'ps-2-22-ps-data-driven-create.psd')
        for path in [out_path]:
            if os.path.lexists(path):
                os.remove(path)
        os.makedirs(out_dir, exist_ok=True)
        img = Image.new('RGB', (64, 64), color=(240, 240, 240))
        img.save(seed_path, 'PSD')
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(1)
        return {'status': 'completed', 'state': {}}
