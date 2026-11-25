import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = "~/Desktop/e31-newapps/ps-2-23-ps-print-hard-proof-2-seed.png"


def _png_bytes(width, height, rgb):
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class Setup(BaseSetup):
    def run(self, context):
        seed = os.path.expanduser(SEED)
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        os.makedirs(os.path.expanduser("~/Desktop/e31-newapps/out"), exist_ok=True)
        with open(seed, "wb") as f:
            f.write(_png_bytes(32, 32, (200, 80, 40)))
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "err": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed}}
