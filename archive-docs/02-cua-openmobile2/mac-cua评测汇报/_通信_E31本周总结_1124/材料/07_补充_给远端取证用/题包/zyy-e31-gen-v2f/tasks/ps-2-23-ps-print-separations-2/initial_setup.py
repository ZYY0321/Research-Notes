import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)


def _seed_png(width, height):
    raw = b''
    for y in range(height):
        row = bytearray(b'\x00')
        for x in range(width):
            row += bytes(((x * 5) % 256, (y * 7) % 256, 90))
        raw += bytes(row)
    return (b'\x89PNG\r\n\x1a\n'
            + _chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + _chunk(b'IDAT', zlib.compress(raw))
            + _chunk(b'IEND', b''))


class Setup(BaseSetup):
    def run(self, context):
        seed = os.path.expanduser('~/Desktop/e31-newapps/ps-2-23-ps-print-separations-2-seed.png')
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        with open(seed, 'wb') as fh:
            fh.write(_seed_png(48, 32))
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed}}
