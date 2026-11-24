import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser("~/e31-newapps/seed/ps-2-18-sharpen-seed.png")
OUT = os.path.expanduser("~/e31-newapps/out/ps-2-18-sharpen.png")


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _seed_png(width, height):
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            base = 220 if ((x // 8 + y // 8) % 2) else 40
            rows.extend((base, (x * 5) % 256, (y * 5) % 256))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(bytes(rows))) + _chunk(b"IEND", b"")


class Setup(BaseSetup):
    def run(self, context):
        for path in [OUT]:
            if os.path.lexists(path):
                os.remove(path)
        os.makedirs(os.path.dirname(SEED), exist_ok=True)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(SEED, "wb") as handle:
            handle.write(_seed_png(48, 48))
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(2)
        return {"status": "completed", "state": {"seed": SEED}}
