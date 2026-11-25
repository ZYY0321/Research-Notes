import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser("~/Desktop/e31-newapps/seed/ps-2-18-neural-filter-seed.png")
OUT = os.path.expanduser("~/Desktop/e31-newapps/out/ps-2-18-neural-filter.png")


def _chunk(tag, data):
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def _seed_png(width, height):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw += bytes((min(255, 60 + x * 3), min(255, 40 + y * 4), 90))
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(bytes(raw)))
            + _chunk(b"IEND", b""))


class Setup(BaseSetup):
    def run(self, context):
        if os.path.lexists(OUT):
            os.remove(OUT)
        os.makedirs(os.path.dirname(SEED), exist_ok=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(SEED, "wb") as f:
            f.write(_seed_png(48, 32))
        proc = subprocess.run(["open", "-a", 'Adobe Photoshop 2026', SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
