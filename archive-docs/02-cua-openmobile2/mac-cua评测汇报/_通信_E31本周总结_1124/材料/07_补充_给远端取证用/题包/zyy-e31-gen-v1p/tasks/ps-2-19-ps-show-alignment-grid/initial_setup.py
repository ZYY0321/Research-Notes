import os, sys, subprocess, time, zlib, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

class Setup(BaseSetup):
    def run(self, context):
        base = os.path.expanduser("~/Desktop/e31-newapps")
        out_dir = os.path.join(base, "out")
        os.makedirs(out_dir, exist_ok=True)
        shot = os.path.join(out_dir, "ps-2-19-ps-show-alignment-grid.png")
        if os.path.lexists(shot):
            os.remove(shot)
        seed = os.path.join(base, "ps-2-19-seed.png")
        width, height = 48, 32
        row = b"\x00" + bytes((90, 140, 200)) * width
        raw = row * height
        def chunk(tag, data):
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
        ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
        with open(seed, "wb") as f:
            f.write(png)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed}}
