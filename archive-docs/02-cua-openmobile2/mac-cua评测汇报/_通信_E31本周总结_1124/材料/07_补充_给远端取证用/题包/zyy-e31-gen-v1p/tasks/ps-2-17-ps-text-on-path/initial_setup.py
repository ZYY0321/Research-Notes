import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser('~/Desktop/e31-newapps/ps-2-17-seed.png')
OUT = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-17-ps-text-on-path.png')


def _png(width, height, rgb):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    row = b'\x00' + bytes(rgb) * width
    body = zlib.compress(row * height)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', body) + chunk(b'IEND', b'')


class Setup(BaseSetup):
    def run(self, context):
        for path in [OUT]:
            if os.path.lexists(path):
                os.remove(path)
        os.makedirs(os.path.dirname(SEED), exist_ok=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(SEED, 'wb') as fh:
            fh.write(_png(64, 64, (245, 245, 245)))
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026', SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
