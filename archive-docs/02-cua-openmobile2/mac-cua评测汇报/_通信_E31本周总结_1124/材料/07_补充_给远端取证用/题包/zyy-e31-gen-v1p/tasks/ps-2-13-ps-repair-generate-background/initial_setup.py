import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED_PATH = "~/Desktop/e31-newapps/seed/ps-2-13-ps-repair-generate-background-seed.png"
OUT_PATH = "~/Desktop/e31-newapps/out/ps-2-13-ps-repair-generate-background.png"


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _seed_bytes():
    width = height = 48
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            if 16 <= x < 32 and 16 <= y < 32:
                raw.extend((200, 60, 60, 255))
            else:
                raw.extend((0, 0, 0, 0))
    data = b"\x89PNG\r\n\x1a\n"
    data += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    data += _chunk(b"IDAT", zlib.compress(bytes(raw)))
    data += _chunk(b"IEND", b"")
    return data


class Setup(BaseSetup):
    def run(self, context):
        seed = os.path.expanduser(SEED_PATH)
        out = os.path.expanduser(OUT_PATH)
        for path in [out]:
            if os.path.lexists(path):
                os.remove(path)
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(seed, "wb") as handle:
            handle.write(_seed_bytes())
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
