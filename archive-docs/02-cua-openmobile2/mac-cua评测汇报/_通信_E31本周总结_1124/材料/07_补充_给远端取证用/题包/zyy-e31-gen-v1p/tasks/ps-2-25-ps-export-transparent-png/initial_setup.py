import os, sys, subprocess, time
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        output_path = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-25-ps-export-transparent-png.png')
        if os.path.lexists(output_path):
            os.remove(output_path)
        try:
            from PIL import Image
            seed_path = os.path.expanduser('~/Desktop/ps-2-25-seed.png')
            img = Image.new('RGBA', (48, 48), (0, 0, 0, 0))
            pixels = img.load()
            for x in range(24):
                for y in range(24):
                    pixels[x, y] = (200, 50, 50, 255)
            img.save(seed_path)
            proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed_path], capture_output=True, text=True)
            if proc.returncode != 0:
                return {'status': 'failed', 'state': {'code': proc.returncode}}
            time.sleep(2)
            return {'status': 'completed', 'state': {}}
        except ImportError:
            return {'status': 'failed', 'state': {'error': 'PIL not available'}}
