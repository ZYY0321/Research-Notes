import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        out_dir = os.path.expanduser('~/e31-newapps/out')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'ps-2-18-quick-action.png')
        if os.path.lexists(out_path):
            os.remove(out_path)
        seed_path = os.path.expanduser('~/e31-newapps/ps-2-18-quick-action-seed.png')
        width, height = 48, 32
        def pixel(x, y):
            if 16 <= x < 32 and 10 <= y < 22:
                return (230, 80, 60)
            return (40, 120, 200)
        rows = []
        for y in range(height):
            row = bytearray(b'\x00')
            for x in range(width):
                row.extend(pixel(x, y))
            rows.append(bytes(row))
        raw = b''.join(rows)
        def chunk(tag, data):
            return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
        with open(seed_path, 'wb') as f:
            f.write(png)
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026', seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
