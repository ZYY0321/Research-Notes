import os, sys, subprocess, time, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = "~/Desktop/e31-newapps/seeds/ps-2-8-frame-from-shape-text-seed.psd"
OUT = "~/Desktop/e31-newapps/out/ps-2-8-frame-from-shape-text.psd"

class Setup(BaseSetup):
    def run(self, context):
        out = os.path.expanduser(OUT)
        if os.path.lexists(out):
            os.remove(out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        seed = os.path.expanduser(SEED)
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        width = height = 32
        channels = 3
        header = b"8BPS" + struct.pack(">H", 1) + b"\x00" * 6 + struct.pack(">HIIHH", channels, height, width, 8, 3)
        body = struct.pack(">I", 0) + struct.pack(">I", 0) + struct.pack(">I", 0) + struct.pack(">H", 0) + bytes([180]) * (channels * height * width)
        with open(seed, "wb") as f:
            f.write(header + body)
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {"seed": seed}}
