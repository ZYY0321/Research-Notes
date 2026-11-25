import os, sys, subprocess, time, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        out_dir = os.path.expanduser('~/Desktop/e31-newapps/out')
        os.makedirs(out_dir, exist_ok=True)
        
        psd_path = os.path.join(out_dir, 'ps-2-20-ps-video-use-keyframes.psd')
        if os.path.exists(psd_path):
            os.remove(psd_path)
        
        with open(psd_path, 'wb') as f:
            width, height = 800, 600
            f.write(b'8BPS')
            f.write(struct.pack('>H', 1))
            f.write(b'\x00' * 6)
            f.write(struct.pack('>H', 3))
            f.write(struct.pack('>I', height))
            f.write(struct.pack('>I', width))
            f.write(struct.pack('>H', 8))
            f.write(struct.pack('>H', 3))
            f.write(struct.pack('>I', 0))
            f.write(struct.pack('>I', 0))
            f.write(struct.pack('>I', 0))
            f.write(struct.pack('>H', 0))
            for _ in range(3):
                f.write(b'\xff' * (width * height))
        
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', psd_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(2)
        return {'status': 'completed', 'state': {}}
