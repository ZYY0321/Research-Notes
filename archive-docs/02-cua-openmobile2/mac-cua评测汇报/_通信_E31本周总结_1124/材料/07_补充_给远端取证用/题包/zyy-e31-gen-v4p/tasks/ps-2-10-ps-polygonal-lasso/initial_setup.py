import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _chunk(tag, data):
    block = tag + data
    return struct.pack(">I", len(data)) + block + struct.pack(">I", zlib.crc32(block) & 0xFFFFFFFF)


def _seed_png(width, height):
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.append((40 + 4 * x) % 256)
            rows.append((90 + 3 * y) % 256)
            rows.append((160 + 2 * (x + y)) % 256)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    body = _chunk(b"IHDR", header) + _chunk(b"IDAT", zlib.compress(bytes(rows))) + _chunk(b"IEND", b"")
    return b"\x89PNG\r\n\x1a\n" + body


class Setup(BaseSetup):
    def run(self, context):
        seed = os.path.expanduser("~/e31-newapps/ps-2-10-ps-polygonal-lasso-seed.png")
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        out_dir = os.path.expanduser("~/e31-newapps/out")
        os.makedirs(out_dir, exist_ok=True)
        target = os.path.join(out_dir, "ps-2-10-ps-polygonal-lasso.psd")
        if os.path.lexists(target):
            os.remove(target)
        with open(seed, "wb") as fh:
            fh.write(_seed_png(48, 32))
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed}}
