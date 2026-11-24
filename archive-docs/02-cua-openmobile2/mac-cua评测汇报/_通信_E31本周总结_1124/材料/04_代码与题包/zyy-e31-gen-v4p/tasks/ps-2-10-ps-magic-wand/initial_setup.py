import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = "~/e31-newapps/ps-2-10-ps-magic-wand-seed.png"

class Setup(BaseSetup):
    def run(self, context):
        seed = os.path.expanduser(SEED)
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        width = 64
        height = 64
        rows = bytearray()
        for y in range(height):
            rows.append(0)
            for x in range(width):
                if x < width // 2:
                    rows.extend((200, 40, 40))
                else:
                    rows.extend((40, 80, 200))
        def chunk(tag, data):
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(rows))) + chunk(b"IEND", b"")
        with open(seed, "wb") as handle:
            handle.write(png)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed}}
