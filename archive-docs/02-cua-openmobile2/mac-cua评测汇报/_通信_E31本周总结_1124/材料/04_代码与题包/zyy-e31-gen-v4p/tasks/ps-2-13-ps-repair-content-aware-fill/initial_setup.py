import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

W, H = 48, 32
BG = (96, 140, 190)
OBJ = (230, 70, 40)
RECT = (18, 10, 29, 21)


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _seed_png():
    rows = []
    for y in range(H):
        row = bytearray(b"\x00")
        for x in range(W):
            if RECT[0] <= x <= RECT[2] and RECT[1] <= y <= RECT[3]:
                row.extend(OBJ)
            else:
                row.extend(BG)
        rows.append(bytes(row))
    raw = b"".join(rows)
    out = b"\x89PNG\r\n\x1a\n"
    out += _chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    out += _chunk(b"IDAT", zlib.compress(raw))
    out += _chunk(b"IEND", b"")
    return out


class Setup(BaseSetup):
    def run(self, context):
        out_path = os.path.expanduser("~/e31-newapps/out/ps-2-13-ps-repair-content-aware-fill.png")
        if os.path.lexists(out_path):
            os.remove(out_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        seed_dir = os.path.expanduser("~/e31-newapps/seed")
        os.makedirs(seed_dir, exist_ok=True)
        seed_path = os.path.join(seed_dir, "ps-2-13-ps-repair-content-aware-fill-seed.png")
        with open(seed_path, "wb") as f:
            f.write(_seed_png())
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed_path], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed_path}}
