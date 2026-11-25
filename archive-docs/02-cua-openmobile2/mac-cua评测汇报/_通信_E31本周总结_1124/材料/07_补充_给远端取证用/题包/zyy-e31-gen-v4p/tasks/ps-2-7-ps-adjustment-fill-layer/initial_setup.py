import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        out_dir = os.path.expanduser('~/e31-newapps/out')
        seed_dir = os.path.expanduser('~/e31-newapps/seed')
        os.makedirs(out_dir, exist_ok=True)
        os.makedirs(seed_dir, exist_ok=True)
        target = os.path.join(out_dir, 'ps-2-7-ps-adjustment-fill-layer.psd')
        if os.path.lexists(target):
            os.remove(target)
        seed = os.path.join(seed_dir, 'ps-2-7-adjustment-seed.png')
        width, height = 48, 32

        def chunk(tag, data):
            return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

        ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        rows = b''
        for y in range(height):
            row = b'\x00'
            for x in range(width):
                row += bytes([70 + (x * 2) % 90, 120, 180 - (y * 3) % 90])
            rows += row
        idat = zlib.compress(rows)
        png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')
        with open(seed, 'wb') as f:
            f.write(png)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed}}
