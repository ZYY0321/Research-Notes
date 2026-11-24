import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser('~/e31-newapps/ps-2-13-ps-repair-clone-stamp-seed.png')
OUT = os.path.expanduser('~/e31-newapps/out/ps-2-13-ps-repair-clone-stamp.png')


def build_seed_png():
    width = height = 48
    background = (86, 124, 70)
    pattern = (190, 40, 40)
    raw = b''
    for y in range(height):
        row = bytearray(b'\x00')
        for x in range(width):
            if 28 <= x < 40 and 28 <= y < 40:
                row += bytes(pattern)
            else:
                row += bytes(background)
        raw += bytes(row)

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


class Setup(BaseSetup):
    def run(self, context):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        if os.path.lexists(OUT):
            os.remove(OUT)
        with open(SEED, 'wb') as f:
            f.write(build_seed_png())
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": SEED}}
