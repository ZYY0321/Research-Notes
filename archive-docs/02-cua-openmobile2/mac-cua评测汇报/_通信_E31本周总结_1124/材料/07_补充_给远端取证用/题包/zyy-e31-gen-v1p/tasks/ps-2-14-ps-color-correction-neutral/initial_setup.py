import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

OUT = '~/Desktop/e31-newapps/out/ps-2-14-ps-color-correction-neutral.png'
SEED = '~/Desktop/e31-newapps/seed/ps-2-14-ps-color-correction-neutral-seed.png'


def write_png(path, width, height, rgb):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b''
    row = b'\x00' + bytes(rgb) * width
    for _ in range(height):
        raw += row
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as handle:
        handle.write(png)


class Setup(BaseSetup):
    def run(self, context):
        out = os.path.expanduser(OUT)
        if os.path.lexists(out):
            os.remove(out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        seed = os.path.expanduser(SEED)
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        write_png(seed, 48, 32, (128, 128, 178))
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026', seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed}}
