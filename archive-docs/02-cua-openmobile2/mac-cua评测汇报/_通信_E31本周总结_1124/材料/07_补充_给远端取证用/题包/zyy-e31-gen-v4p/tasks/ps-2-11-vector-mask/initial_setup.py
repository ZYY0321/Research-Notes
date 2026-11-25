import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _chunk(tag, data):
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)


def _solid_png(width, height, rgb):
    row = b'\x00' + bytes(rgb) * width
    raw = row * height
    parts = [_chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)),
             _chunk(b'IDAT', zlib.compress(raw)),
             _chunk(b'IEND', b'')]
    return b'\x89PNG\r\n\x1a\n' + b''.join(parts)


class Setup(BaseSetup):
    def run(self, context):
        base = os.path.expanduser('~/e31-newapps')
        out_dir = os.path.join(base, 'out')
        os.makedirs(out_dir, exist_ok=True)
        for path in ['~/e31-newapps/out/ps-2-11-vector-mask.png',
                     '~/e31-newapps/out/ps-2-11-vector-mask.psd']:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        seed = os.path.join(base, 'ps-2-11-vector-mask-seed.png')
        with open(seed, 'wb') as handle:
            handle.write(_solid_png(48, 48, (245, 246, 248)))
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed}}
