import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser('~/e31-newapps/seed/ps-2-13-ps-repair-patch-seed.png')
OUT = os.path.expanduser('~/e31-newapps/out/ps-2-13-ps-repair-patch.png')
BG = (96, 144, 192)
FLAW = (168, 64, 48)


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def _seed_png(width, height):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            if 18 <= x <= 29 and 10 <= y <= 21:
                raw.extend(FLAW)
            else:
                raw.extend(BG)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    body = _chunk(b'IHDR', ihdr) + _chunk(b'IDAT', zlib.compress(bytes(raw))) + _chunk(b'IEND', b'')
    return b'\x89PNG\r\n\x1a\n' + body


class Setup(BaseSetup):
    def run(self, context):
        os.makedirs(os.path.dirname(SEED), exist_ok=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        if os.path.lexists(OUT):
            os.remove(OUT)
        with open(SEED, 'wb') as handle:
            handle.write(_seed_png(48, 32))
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026', SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
