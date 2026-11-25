import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser('~/Desktop/e31-newapps/ps-2-13-red-eye-seed.png')
OUT = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-13-ps-repair-red-eye.png')


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def _seed_png():
    w = h = 64
    rows = []
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            c = (92, 132, 180)
            if 10 <= x < 54 and 8 <= y < 58:
                c = (226, 178, 148)
            for cx in (20, 44):
                d = (x - cx) ** 2 + (y - 26) ** 2
                if d <= 25:
                    c = (245, 245, 245)
                if d <= 4:
                    c = (204, 36, 36)
            if 24 <= x < 40 and 46 <= y < 48:
                c = (150, 90, 80)
            row += bytes(c)
        rows.append(bytes(row))
    raw = b''.join(rows)
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', ihdr) + _chunk(b'IDAT', zlib.compress(raw)) + _chunk(b'IEND', b'')


class Setup(BaseSetup):
    def run(self, context):
        for path in [OUT]:
            if os.path.lexists(path):
                os.remove(path)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        os.makedirs(os.path.dirname(SEED), exist_ok=True)
        with open(SEED, 'wb') as f:
            f.write(_seed_png())
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026', SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
