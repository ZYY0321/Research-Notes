import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = "~/Desktop/e31-newapps/ps-2-15-seed.png"
OUT = "~/Desktop/e31-newapps/out/ps-2-15-ps-brushes-presets.png"


def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _white_png(width, height):
    row = b"\x00" + b"\xff" * (width * 3)
    raw = row * height
    out = b"\x89PNG\r\n\x1a\n"
    out += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    out += _chunk(b"IDAT", zlib.compress(raw))
    out += _chunk(b"IEND", b"")
    return out


class Setup(BaseSetup):
    def run(self, context):
        for path in [OUT]:
            expanded = os.path.expanduser(path)
            if os.path.lexists(expanded):
                os.remove(expanded)
        out_dir = os.path.dirname(os.path.expanduser(OUT))
        os.makedirs(out_dir, exist_ok=True)
        seed = os.path.expanduser(SEED)
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        with open(seed, "wb") as handle:
            handle.write(_white_png(64, 64))
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
