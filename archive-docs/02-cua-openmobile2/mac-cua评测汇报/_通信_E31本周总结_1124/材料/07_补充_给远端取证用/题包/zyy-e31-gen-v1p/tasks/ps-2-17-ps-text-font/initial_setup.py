import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

OUT = '~/Desktop/e31-newapps/out/ps-2-17-ps-text-font.png'
SEED = '~/Desktop/e31-newapps/seed/ps-2-17-ps-text-font-seed.png'


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def _white_png(width, height):
    raw = b''.join(b'\x00' + b'\xff' * (width * 3) for _ in range(height))
    return (b'\x89PNG\r\n\x1a\n'
            + _chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + _chunk(b'IDAT', zlib.compress(raw))
            + _chunk(b'IEND', b''))


class Setup(BaseSetup):
    def run(self, context):
        out = os.path.expanduser(OUT)
        seed = os.path.expanduser(SEED)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        if os.path.lexists(out):
            os.remove(out)
        with open(seed, 'wb') as handle:
            handle.write(_white_png(48, 24))
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
