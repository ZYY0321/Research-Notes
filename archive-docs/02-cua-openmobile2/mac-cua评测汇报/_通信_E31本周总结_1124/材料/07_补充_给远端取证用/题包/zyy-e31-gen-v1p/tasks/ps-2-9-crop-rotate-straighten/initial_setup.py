import os, sys, subprocess, time, math, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser('~/Desktop/e31-newapps/ps-2-9-crop-rotate-straighten-seed.png')
OUT = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-9-crop-rotate-straighten.png')


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def _seed_bytes():
    c = math.cos(math.radians(15.0))
    s = math.sin(math.radians(15.0))
    rows = []
    for y in range(64):
        row = bytearray(b'\x00')
        for x in range(64):
            dx = x - 31.5
            dy = y - 31.5
            px = dx * c + dy * s + 23.5
            py = -dx * s + dy * c + 23.5
            if 0 <= px < 48 and 0 <= py < 48:
                rgb = (200, 40, 40) if px < 24 else (40, 80, 200)
            else:
                rgb = (128, 128, 128)
            row += bytes(rgb)
        rows.append(bytes(row))
    body = _chunk(b'IHDR', struct.pack('>IIBBBBB', 64, 64, 8, 2, 0, 0, 0))
    body += _chunk(b'IDAT', zlib.compress(b''.join(rows)))
    body += _chunk(b'IEND', b'')
    return b'\x89PNG\r\n\x1a\n' + body


class Setup(BaseSetup):
    def run(self, context):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        if os.path.lexists(OUT):
            os.remove(OUT)
        with open(SEED, 'wb') as fh:
            fh.write(_seed_bytes())
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026', SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
