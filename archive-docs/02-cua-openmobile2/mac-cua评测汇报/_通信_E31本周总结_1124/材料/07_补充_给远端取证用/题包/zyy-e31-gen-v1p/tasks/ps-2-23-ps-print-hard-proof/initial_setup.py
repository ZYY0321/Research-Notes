import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser("~/Desktop/e31-newapps/seed/ps-2-23-seed.png")

def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

def _make_seed_png(path):
    width, height = 48, 32
    rows = []
    for y in range(height):
        row = bytearray(b"\x00")
        for x in range(width):
            row += bytes(((40 + x * 4) % 256, (160 - y * 3) % 256, 90))
        rows.append(bytes(row))
    raw = b"".join(rows)
    body = b"\x89PNG\r\n\x1a\n"
    body += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    body += _chunk(b"IDAT", zlib.compress(raw))
    body += _chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(body)

class Setup(BaseSetup):
    def run(self, context):
        for path in []:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        _make_seed_png(SEED)
        os.makedirs(os.path.expanduser("~/Desktop/e31-newapps/out"), exist_ok=True)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": SEED}}
