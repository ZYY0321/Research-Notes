import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed_path = os.path.expanduser("~/Desktop/e31-newapps/e31-seed-ps-print.png")
        os.makedirs(os.path.dirname(seed_path), exist_ok=True)
        width, height = 64, 64
        color = (128, 128, 128)
        def png_chunk(chunk_type, data):
            chunk_data = chunk_type + data
            crc = zlib.crc32(chunk_data) & 0xffffffff
            return struct.pack(">I", len(data)) + chunk_data + struct.pack(">I", crc)
        ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        raw_data = b''
        for y in range(height):
            raw_data += b'\x00'
            for x in range(width):
                raw_data += bytes(color)
        idat = zlib.compress(raw_data)
        png = b'\x89PNG\r\n\x1a\n'
        png += png_chunk(b'IHDR', ihdr)
        png += png_chunk(b'IDAT', idat)
        png += png_chunk(b'IEND', b'')
        with open(seed_path, 'wb') as f:
            f.write(png)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(2)
        return {"status": "completed", "state": {}}
