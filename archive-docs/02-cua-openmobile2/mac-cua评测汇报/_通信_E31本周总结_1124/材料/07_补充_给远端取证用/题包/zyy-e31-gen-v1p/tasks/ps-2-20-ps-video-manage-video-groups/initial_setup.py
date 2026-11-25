import os, sys, subprocess, time, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed_path = os.path.expanduser('~/Desktop/ps-2-20-ps-video-manage-video-groups-seed.psd')
        out_path = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-20-ps-video-manage-video-groups.psd')
        
        for path in [out_path]:
            if os.path.lexists(path):
                os.remove(path)
        
        os.makedirs(os.path.dirname(seed_path), exist_ok=True)
        with open(seed_path, 'wb') as f:
            f.write(b'8BPS')
            f.write(struct.pack('>H', 1))
            f.write(b'\x00' * 6)
            f.write(struct.pack('>H', 3))
            f.write(struct.pack('>I', 64))
            f.write(struct.pack('>I', 64))
            f.write(struct.pack('>H', 8))
            f.write(struct.pack('>H', 3))
            f.write(struct.pack('>I', 0))
            f.write(struct.pack('>I', 0))
            f.write(struct.pack('>I', 0))
            f.write(struct.pack('>H', 0))
            f.write(b'\x00' * (64 * 64 * 3))
        
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026'], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(1)
        return {'status': 'completed', 'state': {}}
