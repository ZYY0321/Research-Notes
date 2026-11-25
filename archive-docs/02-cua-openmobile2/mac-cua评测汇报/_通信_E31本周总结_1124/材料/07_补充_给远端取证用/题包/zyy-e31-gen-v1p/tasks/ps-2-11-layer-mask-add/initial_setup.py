import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + zlib.crc32(tag + data).to_bytes(4, 'big')


def _solid_png(width, height, rgb):
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    row = b'\x00' + bytes(rgb) * width
    raw = row * height
    return b''.join([
        b'\x89PNG\r\n\x1a\n',
        _chunk(b'IHDR', ihdr),
        _chunk(b'IDAT', zlib.compress(raw)),
        _chunk(b'IEND', b''),
    ])


class Setup(BaseSetup):
    def run(self, context):
        base = os.path.expanduser('~/Desktop/e31-newapps')
        os.makedirs(os.path.join(base, 'out'), exist_ok=True)
        for path in ['~/Desktop/e31-newapps/out/ps-2-11-layer-mask-add.png']:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        seed = os.path.join(base, 'ps-2-11-layer-mask-add-seed.png')
        with open(seed, 'wb') as f:
            f.write(_solid_png(48, 32, (220, 40, 40)))
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed}}
