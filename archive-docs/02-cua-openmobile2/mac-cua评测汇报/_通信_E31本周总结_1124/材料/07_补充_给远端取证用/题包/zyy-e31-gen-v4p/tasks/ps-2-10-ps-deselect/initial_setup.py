import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = os.path.expanduser("~/e31-newapps/ps-2-10-ps-deselect-seed.png")


def _png_bytes(width, height, rgb):
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


class Setup(BaseSetup):
    def run(self, context):
        os.makedirs(os.path.dirname(SEED), exist_ok=True)
        with open(SEED, "wb") as handle:
            handle.write(_png_bytes(48, 32, (70, 130, 180)))
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", SEED], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": SEED}}
