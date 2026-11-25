import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = '~/Desktop/e31-newapps/seed/ps-2-25-ps-save-copy-seed.png'
OUT = '~/Desktop/e31-newapps/out/ps-2-25-ps-save-copy.png'


def _png_bytes(width, height, rgb):
    def chunk(tag, data):
        body = tag + data
        return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xffffffff)
    raw = b''.join(b'\x00' + bytes(rgb) * width for _ in range(height))
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw))
            + chunk(b'IEND', b''))


class Setup(BaseSetup):
    def run(self, context):
        seed = os.path.expanduser(SEED)
        out = os.path.expanduser(OUT)
        for path in [out]:
            if os.path.lexists(path):
                os.remove(path)
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(seed, 'wb') as handle:
            handle.write(_png_bytes(48, 32, (30, 120, 200)))
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026', seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
