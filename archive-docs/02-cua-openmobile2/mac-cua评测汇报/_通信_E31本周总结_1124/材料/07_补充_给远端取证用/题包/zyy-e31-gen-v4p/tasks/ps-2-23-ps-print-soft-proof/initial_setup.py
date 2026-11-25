import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _png_chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _make_seed_png(width, height):
    raw = b""
    for y in range(height):
        row = bytearray()
        for x in range(width):
            row += bytes(((x * 5) % 256, (y * 7) % 256, 120))
        raw += b"\x00" + bytes(row)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _png_chunk(b"IHDR", ihdr)
            + _png_chunk(b"IDAT", zlib.compress(raw))
            + _png_chunk(b"IEND", b""))


class Setup(BaseSetup):
    def run(self, context):
        seed = os.path.expanduser("~/e31-newapps/seed/ps-2-23-ps-print-soft-proof.png")
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        with open(seed, "wb") as handle:
            handle.write(_make_seed_png(48, 32))
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(2)
        return {"status": "completed", "state": {"seed": seed}}
