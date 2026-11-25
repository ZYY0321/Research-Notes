import os, sys, subprocess, time, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser('~/Desktop/e31-newapps/seed/ps-2-8-artboard-add-to-doc-seed.psd')
OUT = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-8-artboard-add-to-doc.psd')


def write_seed_psd(path):
    width = 16
    height = 16
    header = b'8BPS'
    header += struct.pack('>H', 1)
    header += b'\x00' * 6
    header += struct.pack('>H', 3)
    header += struct.pack('>I', height)
    header += struct.pack('>I', width)
    header += struct.pack('>H', 8)
    header += struct.pack('>H', 3)
    body = struct.pack('>I', 0)  # color mode data
    body += struct.pack('>I', 0)  # image resources
    body += struct.pack('>I', 0)  # layer and mask info
    pixels = width * height
    image = struct.pack('>H', 0)
    image += bytes([200]) * pixels
    image += bytes([120]) * pixels
    image += bytes([60]) * pixels
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(header + body + image)


class Setup(BaseSetup):
    def run(self, context):
        for path in [OUT]:
            if os.path.lexists(path):
                os.remove(path)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        write_seed_psd(SEED)
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026', SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": SEED}}
