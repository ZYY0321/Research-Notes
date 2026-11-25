import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser('~/Desktop/e31-newapps/seed/ps-2-23-ps-print-duotone-inks.png')


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def _make_seed(path):
    width, height = 48, 48
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            row.append((x * 5 + y * 3) % 256)
        rows.append(bytes(row))
    raw = b''.join(rows)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 0, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', ihdr) + _chunk(b'IDAT', zlib.compress(raw)) + _chunk(b'IEND', b'')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(png)


class Setup(BaseSetup):
    def run(self, context):
        out = os.path.expanduser('~/Desktop/e31-newapps/out/ps-2-23-ps-print-duotone-inks.psd')
        if os.path.lexists(out):
            os.remove(out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        _make_seed(SEED)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": SEED}}
