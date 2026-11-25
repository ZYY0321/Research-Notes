import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        seed = os.path.expanduser("~/Desktop/e31-newapps/seed/ps-2-10-ps-elliptical-marquee-seed.png")
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        width, height = 48, 32
        def chunk(tag, data):
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
        raw = b""
        for y in range(height):
            row = b"\x00"
            for x in range(width):
                row += bytes((200, 120 + (y % 60), 60))
            raw += row
        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(raw))
        png += chunk(b"IEND", b"")
        with open(seed, "wb") as f:
            f.write(png)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
