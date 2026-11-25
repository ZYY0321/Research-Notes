import os, sys, subprocess, time
from PIL import Image
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        for path in [
            '~/Desktop/e31-newapps/out/ps-2-9-crop-nondestructive-restore-cropped.png',
            '~/Desktop/e31-newapps/out/ps-2-9-crop-nondestructive-restore-restored.png'
        ]:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        seed_path = os.path.expanduser('~/Desktop/e31-newapps/seed-ps-2-9.png')
        os.makedirs(os.path.dirname(seed_path), exist_ok=True)
        img = Image.new('RGB', (64, 64), color=(80, 120, 160))
        img.save(seed_path)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(2)
        return {'status': 'completed', 'state': {}}
