import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = "~/e31-newapps/seed/ps-2-11-object-mask-seed.png"
OUTS = [
    "~/e31-newapps/out/ps-2-11-object-mask.psd",
    "~/e31-newapps/out/ps-2-11-object-mask.png",
]


def _chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def _seed_png():
    width, height = 48, 32
    rows = []
    for y in range(height):
        row = bytearray(b"\x00")
        for x in range(width):
            if 12 <= x < 36 and 8 <= y < 24:
                row += bytes((178, 34, 34))
            else:
                row += bytes((235, 235, 235))
        rows.append(bytes(row))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(b"".join(rows)))
            + _chunk(b"IEND", b""))


class Setup(BaseSetup):
    def run(self, context):
        seed = os.path.expanduser(SEED)
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        os.makedirs(os.path.expanduser("~/e31-newapps/out"), exist_ok=True)
        with open(seed, "wb") as fh:
            fh.write(_seed_png())
        for path in OUTS:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(2)
        return {"status": "completed", "state": {}}
