import os, sys, subprocess, time, struct
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]
from task_api import BaseSetup

SEED = "~/e31-newapps/ps-2-25-ps-save-as-format-seed.psd"
OUT = "~/e31-newapps/out/ps-2-25-ps-save-as-format.tif"


def make_psd(width=16, height=16, rgb=(30, 90, 160)):
    data = b"8BPS" + struct.pack(">H", 1) + b"\x00" * 6
    data += struct.pack(">HIIHH", 3, height, width, 8, 3)
    data += struct.pack(">I", 0)  # color mode data
    data += struct.pack(">I", 0)  # image resources
    data += struct.pack(">I", 0)  # layer and mask info
    data += struct.pack(">H", 0)  # raw compression
    for value in rgb:
        data += bytes([value]) * (width * height)
    return data


class Setup(BaseSetup):
    def run(self, context):
        out = os.path.expanduser(OUT)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if os.path.lexists(out):
            os.remove(out)
        seed = os.path.expanduser(SEED)
        os.makedirs(os.path.dirname(seed), exist_ok=True)
        with open(seed, "wb") as fh:
            fh.write(make_psd())
        proc = subprocess.run(["open", "-a", "Adobe Photoshop 2026", seed], capture_output=True, text=True)
        if proc.returncode != 0:
            return {"status": "failed", "state": {"code": proc.returncode}}
        time.sleep(1)
        return {"status": "completed", "state": {}}
