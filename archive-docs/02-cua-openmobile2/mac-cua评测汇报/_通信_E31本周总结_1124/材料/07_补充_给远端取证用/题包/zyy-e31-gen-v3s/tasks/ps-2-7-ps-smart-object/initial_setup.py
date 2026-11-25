import os, sys, subprocess, time, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        out_dir = os.path.expanduser('~/Desktop/e31-newapps/out')
        os.makedirs(out_dir, exist_ok=True)
        target = os.path.join(out_dir, 'ps-2-7-ps-smart-object.psd')
        if os.path.lexists(target):
            os.remove(target)
        seed = os.path.expanduser('~/Desktop/e31-seed-ps-2-7.psd')
        width, height, channels = 8, 8, 3
        header = b'8BPS' + struct.pack('>H', 1) + b'\x00' * 6
        header += struct.pack('>H', channels)
        header += struct.pack('>I', height) + struct.pack('>I', width)
        header += struct.pack('>H', 8) + struct.pack('>H', 3)
        sections = struct.pack('>I', 0) * 3
        plane = width * height
        pixels = struct.pack('>H', 0) + bytes([180]) * plane + bytes([60]) * plane + bytes([200]) * plane
        with open(seed, 'wb') as handle:
            handle.write(header + sections + pixels)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {'status': 'failed', 'state': {'code': proc.returncode}}
        time.sleep(1)
        return {'status': 'completed', 'state': {}}
