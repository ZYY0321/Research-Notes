import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        out_dir = os.path.expanduser('~/Desktop/e31-newapps/out')
        os.makedirs(out_dir, exist_ok=True)
        for path in ['~/Desktop/e31-newapps/out/ps-2-18-stylize.png']:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        seed = os.path.expanduser('~/Desktop/e31-newapps/ps-2-18-stylize-seed.png')
        w = h = 48
        raw = b''
        for y in range(h):
            row = bytearray(b'\x00')
            for x in range(w):
                row += bytes(((x * 5) % 256, (y * 5) % 256, ((x + y) * 3) % 256))
            raw += bytes(row)
        def chunk(tag, data):
            return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        png = (b'\x89PNG\r\n\x1a\n'
               + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
               + chunk(b'IDAT', zlib.compress(raw))
               + chunk(b'IEND', b''))
        with open(seed, 'wb') as f:
            f.write(png)
        proc = subprocess.run(['open', '-a', 'Adobe Photoshop 2026', seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
