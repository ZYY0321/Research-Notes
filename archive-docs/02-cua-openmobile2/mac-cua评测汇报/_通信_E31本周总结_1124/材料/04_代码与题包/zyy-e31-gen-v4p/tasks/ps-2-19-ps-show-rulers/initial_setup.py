import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser("~/e31-newapps/seed/ps-2-19-seed.png")
OUT = os.path.expanduser("~/e31-newapps/out/ps-2-19-ps-show-rulers.png")


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _write_seed(path):
    width, height = 48, 32
    rows = []
    for y in range(height):
        row = bytearray(b"\x00")
        for x in range(width):
            row += bytes(((40 + x * 3) % 256, (160 - y * 2) % 256, 200))
        rows.append(bytes(row))
    raw = b"".join(rows)
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
           + _chunk(b"IDAT", zlib.compress(raw))
           + _chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(png)


class Setup(BaseSetup):
    def run(self, context):
        for path in [OUT]:
            if os.path.lexists(path):
                os.remove(path)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        _write_seed(SEED)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026"], capture_output=True, text=True)
            if proc.returncode != 0:
                return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": SEED}}
