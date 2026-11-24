import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser("~/e31-newapps/seed/ps-2-25-seed.png")
OUT = os.path.expanduser("~/e31-newapps/out/ps-2-25-ps-quick-export-png.png")
W, H = 48, 32
RGB = (34, 120, 200)


def write_png(path, width, height, rgb):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    body = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(body)


class Setup(BaseSetup):
    def run(self, context):
        for path in [OUT]:
            if os.path.lexists(path):
                os.remove(path)
        os.makedirs(os.path.dirname(SEED), exist_ok=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        write_png(SEED, W, H, RGB)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "err": proc.stderr[-300:]}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": SEED}}
