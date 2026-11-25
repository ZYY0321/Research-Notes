import os, sys, subprocess, time, struct, zlib
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup


def _png(width, height, rgb):
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = b"\x00" + bytes(rgb) * width
    raw = row * height
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


class Setup(BaseSetup):
    def run(self, context):
        out_dir = os.path.expanduser("~/e31-newapps/out")
        os.makedirs(out_dir, exist_ok=True)
        target = os.path.join(out_dir, "ps-2-20-ps-video-create-animation-frames.psd")
        if os.path.lexists(target):
            os.remove(target)
        seed = os.path.expanduser("~/e31-newapps/ps-2-20-seed.png")
        with open(seed, "wb") as handle:
            handle.write(_png(16, 16, (200, 80, 40)))
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode, "stderr": proc.stderr}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed}}
